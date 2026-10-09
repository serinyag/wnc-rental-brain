-- Native evidence journal + current case fact, committed under the case lock.
-- Only the trusted application role may invoke this authority gate.
create or replace function public.accept_operational_resolution(
 p_case bigint, p_action bigint, p_revision integer, p_action_hash text,
 p_field text, p_evidence jsonb
) returns jsonb language plpgsql set search_path = public as $$
declare
 c public.rental_cases%rowtype; a public.workflow_actions%rowtype;
 old public.rental_case_facts%rowtype; prior public.workflow_events%rowtype;
 v_id bigint; v_fact bigint; v_revision integer; v_payload jsonb; v_outcomes jsonb;
 v_key text := 'operational_resolution:' || (p_evidence->>'idempotency_key');
 v_contract jsonb := p_evidence->'contract';
begin
 select * into c from public.rental_cases where id=p_case for update;
 if not found then raise exception 'case_not_found'; end if;
 select * into prior from public.workflow_events where rental_case_id=p_case and event_identity_key=v_key;
 if found then
   if prior.structured_payload->'submission' <> p_evidence then raise exception 'resolution_replay_payload_conflict'; end if;
   return prior.structured_payload->'result' || '{"replayed":true}'::jsonb;
 end if;
 if c.case_revision <> p_revision then raise exception 'stale_case_revision'; end if;
 select * into a from public.workflow_actions where id=p_action and rental_case_id=p_case for update;
 if not found or a.semantic_subject_hash <> p_action_hash or a.action_type <> 'CREATE_INTERNAL_TASK_ITEM'
   or a.status in ('cancelled','failed')
   or a.structured_payload->>'resolution_owner' <> 'WNC_INTERNAL'
   or a.structured_payload->>'resolution_item_key' is distinct from v_contract->>'resolution_item_key'
   then raise exception 'resolution_action_mismatch'; end if;
 if p_evidence->>'version' is distinct from 'operational_resolution_v1'
   or p_evidence->>'authority_class' is distinct from 'WNC_INTERNAL_OPERATOR'
   or p_evidence->>'provenance' is distinct from 'staging synthetic operator evidence'
   or p_evidence->'synthetic' is distinct from 'true'::jsonb
   or coalesce(p_evidence->>'actor','') = '' or coalesce(p_evidence->>'evidence_text','') = ''
   or coalesce(p_evidence->>'evidence_reference','') = ''
   or (v_contract->>'workflow_action_id')::bigint <> p_action
   or (v_contract->'scope'->>'rental_case_id')::bigint <> p_case
   or v_contract->'scope'->>'venue' is distinct from c.rental_type_code
   or (v_contract->'scope'->>'start')::timestamptz is distinct from c.active_event_start
   or (v_contract->'scope'->>'end')::timestamptz is distinct from c.active_event_end
   or p_field not like 'operational_resolution:%'
   then raise exception 'invalid_resolution_authority_or_scope'; end if;
 if v_contract->>'kind' not in ('AVAILABILITY_CONFIRMATION','TECHNICAL_CAPABILITY_CONFIRMATION','CAPACITY_LAYOUT_CONFIRMATION')
    or jsonb_typeof(p_evidence->'outcomes') <> 'object' or p_evidence->'outcomes' = '{}'::jsonb
    then raise exception 'invalid_resolution_kind'; end if;
 if exists(select 1 from jsonb_each_text(p_evidence->'outcomes') x where
     not (v_contract->'subjects' ? x.key) or
     (v_contract->>'kind'='AVAILABILITY_CONFIRMATION' and x.value not in ('AVAILABLE','UNAVAILABLE')) or
     (v_contract->>'kind' in ('TECHNICAL_CAPABILITY_CONFIRMATION','CAPACITY_LAYOUT_CONFIRMATION') and x.value not in ('FEASIBLE','NOT_FEASIBLE')))
    then raise exception 'invalid_resolution_outcome'; end if;
 if v_contract->>'kind'='CAPACITY_LAYOUT_CONFIRMATION' and (
   p_case <> 586 or c.rental_type_code <> 'studio_space'
   or v_contract->'subjects' is distinct from '["capacity_layout"]'::jsonb
   or v_contract->'inputs'->>'configuration_type' is distinct from 'seated'
   or v_contract->'inputs'->'guest_count' is distinct from '24'::jsonb
   or not exists(select 1 from public.rental_case_facts f where f.rental_case_id=p_case
       and f.field_code='guest_count' and f.value_payload=v_contract->'inputs'->'guest_count')
   or not exists(select 1 from public.rental_case_facts f where f.rental_case_id=p_case
       and f.field_code='layout_requirements' and f.value_payload=v_contract->'inputs'->'layout_requirements'
       and f.value_payload->>'configuration_type'='seated'))
   then raise exception 'capacity_input_binding_mismatch'; end if;
 -- One current authority state per operational kind and event scope, even if
 -- reconciliation replaced the WorkflowAction. This also reads v1 legacy keys.
 if (select count(*) from public.rental_case_facts where rental_case_id=p_case
     and field_code like 'operational_resolution:%'
     and value_payload->'contract'->>'kind'=v_contract->>'kind'
     and value_payload->'contract'->'scope'=v_contract->'scope') > 1
   then raise exception 'conflicting_current_operational_authority'; end if;
 select * into old from public.rental_case_facts where rental_case_id=p_case
   and field_code like 'operational_resolution:%'
   and value_payload->'contract'->>'kind'=v_contract->>'kind'
   and value_payload->'contract'->'scope'=v_contract->'scope' for update;
 if found and coalesce((p_evidence->>'supersedes_event_id')::bigint,0) <> (old.value_payload->>'event_id')::bigint
   then raise exception 'conflicting_resolution_requires_explicit_correction'; end if;
 if old.id is null and p_evidence->>'supersedes_event_id' is not null
   then raise exception 'correction_target_not_current'; end if;
 if old.id is not null then p_field := old.field_code; end if;
 -- Corrections state the complete new result. Omitted components become pending.
 v_outcomes := p_evidence->'outcomes';
 v_revision := c.case_revision + 1;
 v_payload := p_evidence || jsonb_build_object('accepted_case_revision',v_revision);
 v_id := nextval(pg_get_serial_sequence('public.workflow_events','id'));
 insert into public.rental_case_facts(rental_case_id,field_code,domain_code,value_payload,source_reference,established_case_revision)
 values(p_case,p_field,'operations',v_payload || jsonb_build_object('event_id',v_id),'workflow_event:'||v_id,v_revision)
 on conflict(rental_case_id,field_code) do update set value_payload=excluded.value_payload,
   source_reference=excluded.source_reference,established_case_revision=excluded.established_case_revision returning id into v_fact;
 update public.rental_cases set case_revision=v_revision where id=p_case;
 -- A fact establishes resolution; the inverse inference is never permitted.
 update public.workflow_actions set structured_payload=structured_payload || jsonb_build_object(
   'resolution_status',case when (select count(*) from jsonb_object_keys(v_outcomes))=jsonb_array_length(v_contract->'subjects')
      then 'resolved' else 'REQUIRED' end,'governed_resolution_event_id',v_id) where id=p_action;
 insert into public.workflow_events(id,rental_case_id,event_type_code,source_type,source_reference,
    actor_type,actor_reference,occurred_at,recorded_at,event_identity_key,structured_payload,origin_metadata)
 values(v_id,p_case,'operational_resolution_accepted','operator_resolution',p_evidence->>'evidence_reference',
    'wnc_operator',p_evidence->>'actor',(p_evidence->>'occurred_at')::timestamptz,clock_timestamp(),v_key,
    jsonb_build_object('submission',p_evidence,'resolution',v_payload,'result',jsonb_build_object('event_id',v_id,'fact_id',v_fact,'case_revision',v_revision,'replayed',false)),
    jsonb_build_object('authority_contract','operational_resolution_v1','synthetic',true));
 return jsonb_build_object('event_id',v_id,'fact_id',v_fact,'case_revision',v_revision,'replayed',false);
end $$;
revoke all on function public.accept_operational_resolution(bigint,bigint,integer,text,text,jsonb) from public, anon, authenticated;
grant execute on function public.accept_operational_resolution(bigint,bigint,integer,text,text,jsonb) to service_role;
