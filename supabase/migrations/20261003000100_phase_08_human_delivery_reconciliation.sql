-- Human delivery evidence is separate from immutable automated execution evidence.
-- Reuse workflow_events and its unique case/identity constraint; no parallel ledger.
alter table public.inquiry_response_draft_revisions
  drop constraint if exists inquiry_response_draft_revisions_draft_status_check;
alter table public.inquiry_response_draft_revisions
  add constraint inquiry_response_draft_revisions_draft_status_check check (
    draft_status in ('draft','needs_approval','approved','rejected','simulated_sent',
                     'send_failed','send_outcome_uncertain','human_confirmed_delivered'));

create or replace function public.reconcile_outlook_human_delivery(
  p_case_id bigint, p_action_id bigint, p_revision_id bigint, p_approval_id bigint,
  p_attempt_id bigint, p_expected_payload jsonb, p_recipient text, p_subject text,
  p_evidence_note text, p_actor_reference text
) returns jsonb language plpgsql security invoker set search_path = public, pg_temp as $$
declare
  a public.workflow_actions%rowtype;
  d public.inquiry_response_draft_revisions%rowtype;
  ap public.rental_case_approval_requests%rowtype;
  t public.workflow_execution_attempts%rowtype;
  e public.workflow_events%rowtype;
  identity_key text := 'outlook_human_confirmed_delivery:' || p_action_id || ':' || p_attempt_id;
  target text := 'workflow_action:' || p_action_id || ':draft_revision:' || p_revision_id;
  evidence jsonb;
  stamp timestamptz := clock_timestamp();
begin
  -- Lock the case/action first, matching the execution path's serialization scope.
  perform 1 from public.rental_cases where id=p_case_id for update;
  select * into strict a from public.workflow_actions where id=p_action_id and rental_case_id=p_case_id for update;
  select * into strict d from public.inquiry_response_draft_revisions where id=p_revision_id and rental_case_id=p_case_id for update;
  select * into strict ap from public.rental_case_approval_requests where id=p_approval_id and rental_case_id=p_case_id for update;
  select * into strict t from public.workflow_execution_attempts where id=p_attempt_id and rental_case_id=p_case_id for update;
  if p_evidence_note is null or btrim(p_evidence_note)='' or p_actor_reference is null or btrim(p_actor_reference)='' then
    raise exception 'human_delivery_evidence_required';
  end if;
  if a.action_type <> 'SEND_INQUIRY_RESPONSE' or a.target_adapter_code <> 'outlook'
     or a.structured_payload is distinct from p_expected_payload
     or d.workflow_action_id <> a.id or not d.is_current or d.approval_request_id is distinct from ap.id
     or ap.status <> 'approved' or ap.target_entity_type <> 'workflow_action'
     or ap.target_entity_id is distinct from a.id or ap.target_entity_reference is distinct from target
     or a.structured_payload->>'approval_target' is distinct from target
     or a.structured_payload->>'draft_revision_id' is distinct from d.id::text
     or a.structured_payload->>'draft_content_hash' is distinct from d.content_hash
     or a.structured_payload->>'context_hash' is distinct from d.context_hash
     or a.structured_payload->>'recipient_email' is distinct from d.recipient_email
     or a.structured_payload->>'subject' is distinct from d.subject
     or a.structured_payload->>'body' is distinct from d.body_text
     or d.recipient_email is distinct from p_recipient or d.subject is distinct from p_subject
     or t.workflow_action_id <> a.id or t.status <> 'failed'
     or t.failure_code is distinct from 'adapter_outcome_ambiguous' or t.retry_eligible
     or t.response_snapshot->>'stage' is distinct from 'verify_sent_message'
     or t.response_snapshot->>'reason' is distinct from 'send_verification_inconclusive'
     or (select count(*) from public.workflow_execution_attempts where workflow_action_id=a.id) <> 1
     or exists(select 1 from public.inquiry_response_draft_revisions where supersedes_draft_revision_id=d.id)
  then raise exception 'human_delivery_lineage_mismatch'; end if;
  evidence := jsonb_build_object(
    'workflow_action_id',a.id,'draft_revision_id',d.id,'approval_request_id',ap.id,
    'execution_attempt_id',t.id,'reconciliation_source','human_operator_confirmation',
    'confirmation','recipient_received_intended_message','recipient',p_recipient,'subject',p_subject,
    'resend_performed',false,'provider_call_performed',false,
    'delivery_outcome','human_confirmed_delivered','evidence_note',p_evidence_note,
    'content_hash',d.content_hash,'context_hash',d.context_hash,
    'governed_context_hash',a.structured_payload->>'governed_context_hash',
    'original_execution_attempt',to_jsonb(t));
  select * into e from public.workflow_events where rental_case_id=p_case_id and event_identity_key=identity_key;
  if found then
    if e.event_type_code <> 'outlook_delivery_human_confirmed' or e.structured_payload is distinct from evidence
       or a.status <> 'succeeded' or d.draft_status <> 'human_confirmed_delivered' then
      raise exception 'human_delivery_reconciliation_conflict';
    end if;
    return jsonb_build_object('workflow_event_id',e.id,'already_reconciled',true,'delivery_outcome','human_confirmed_delivered');
  end if;
  if a.status <> 'failed' or d.draft_status <> 'send_outcome_uncertain' then
    raise exception 'human_delivery_terminal_state_mismatch';
  end if;
  insert into public.workflow_events(rental_case_id,event_type_code,source_type,source_reference,
    actor_type,actor_reference,occurred_at,recorded_at,structured_payload,event_identity_key,origin_metadata)
  values(p_case_id,'outlook_delivery_human_confirmed','operator_confirmation','execution_attempt:'||t.id,
    'operator',p_actor_reference,stamp,stamp,evidence,identity_key,'{"phase":"8","mechanism":"human_delivery_reconciliation_v1"}'::jsonb)
  returning * into e;
  update public.workflow_actions set status='succeeded',updated_at=stamp where id=a.id;
  -- Retain automated delivery metadata, including its ambiguity code and timestamp.
  -- Actual receipt time is unknown; the event timestamps when confirmation was recorded.
  update public.inquiry_response_draft_revisions set draft_status='human_confirmed_delivered',updated_at=stamp where id=d.id;
  return jsonb_build_object('workflow_event_id',e.id,'already_reconciled',false,'delivery_outcome','human_confirmed_delivered');
end $$;
revoke all on function public.reconcile_outlook_human_delivery(bigint,bigint,bigint,bigint,bigint,jsonb,text,text,text,text) from public;
grant execute on function public.reconcile_outlook_human_delivery(bigint,bigint,bigint,bigint,bigint,jsonb,text,text,text,text) to service_role;
