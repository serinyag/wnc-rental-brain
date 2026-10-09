-- Explicit, audited anonymization of inactive terminal cases only. No automatic policy.
create table public.case_data_lifecycle_events (
 id uuid primary key, rental_case_id bigint not null references public.rental_cases(id),
 actor_reference text not null, policy_version text not null, request_reference text not null,
 recorded_at timestamptz not null default now(), content_digest text not null,
 disposition text not null check(disposition='anonymized'),
 unique(rental_case_id)
);
alter table public.case_data_lifecycle_events enable row level security;
revoke all on public.case_data_lifecycle_events from public,anon,authenticated;
grant select on public.case_data_lifecycle_events to service_role;
create table public.case_data_lifecycle_holds (
 rental_case_id bigint primary key references public.rental_cases(id),
 actor_reference text not null, reason_reference text not null, recorded_at timestamptz not null default now()
);
alter table public.case_data_lifecycle_holds enable row level security;
revoke all on public.case_data_lifecycle_holds from public,anon,authenticated;
grant select,insert,delete on public.case_data_lifecycle_holds to service_role;
-- This role cannot log in and is never granted to the application. Only the
-- narrowly scoped SECURITY DEFINER routine below runs with this identity.
do $$ begin
 if not exists(select 1 from pg_roles where rolname='wnc_lifecycle_executor') then
  create role wnc_lifecycle_executor nologin noinherit;
 end if;
end $$;
do $$ begin execute format('grant wnc_lifecycle_executor to %I',current_user); end $$;
grant create on schema public to wnc_lifecycle_executor;
grant usage on schema public,private,extensions to wnc_lifecycle_executor;
grant select on all tables in schema public to wnc_lifecycle_executor;
grant update on public.rental_case_blockers,public.rental_case_open_questions,public.rental_case_follow_ups,public.rental_case_reasoning_projections,public.outlook_inbound_conversations,public.outlook_inbound_messages,public.inbound_source_records,public.inbound_observations,
 public.rental_case_facts,public.inquiry_response_draft_revisions,public.workflow_events,
 public.workflow_actions,public.workflow_execution_attempts,public.rental_cases,public.rental_case_approval_requests,
 public.rental_case_decisions,public.rental_case_proposed_changes to wnc_lifecycle_executor;
grant insert on public.case_data_lifecycle_events to wnc_lifecycle_executor;
-- Only the function owner role can take the explicit lifecycle exception.
-- Ordinary service/owner writes continue through original immutability checks.
do $$ declare name text; body text; begin
 foreach name in array array['public.reject_outlook_inbound_evidence_mutation()',
  'private.guard_inquiry_response_draft_revision_write()',
  'private.workflow_execution_attempt_update_guard()', 'private.guard_asana_projection_action()',
  'private.workflow_append_only_guard()'] loop
  select pg_get_functiondef(name::regprocedure) into body;
  body := regexp_replace(body, '\mbegin\M',
   'begin IF current_user = ''wnc_lifecycle_executor'' THEN RETURN NEW; END IF;', 'i');
  execute body;
 end loop;
end $$;
-- RLS applies even to the dedicated function role; only its constrained body
-- is callable by the runtime role. No direct membership is granted.
do $$ declare t text; begin
 foreach t in array array['rental_case_blockers','rental_case_open_questions','rental_case_follow_ups','rental_case_reasoning_projections','outlook_inbound_conversations','outlook_inbound_messages','inbound_source_records','inbound_observations',
 'rental_case_facts','inquiry_response_draft_revisions','workflow_events','workflow_actions',
 'workflow_execution_attempts','rental_cases','case_data_lifecycle_events','rental_case_approval_requests',
 'rental_case_decisions','rental_case_proposed_changes','case_data_lifecycle_holds'] loop
  execute format('create policy wnc_lifecycle_executor_access on public.%I for all to wnc_lifecycle_executor using(true) with check(true)',t);
 end loop;
end $$;
create function public.anonymize_closed_rental_case(p_case bigint,p_actor text,p_policy text,p_request text,p_days integer)
returns uuid language plpgsql security definer set search_path=pg_catalog,public,private,extensions as $$
declare c public.rental_cases%rowtype; receipt uuid; fingerprint text;
begin
 if p_actor is null or p_days is null or p_actor !~ '^entra:[0-9a-f-]{36}:[0-9a-f-]{36}$' or coalesce(p_policy,'')='' or coalesce(p_request,'')='' or p_days<1
 then raise exception 'approved_lifecycle_authority_required'; end if;
 select id into receipt from public.case_data_lifecycle_events where rental_case_id=p_case;
 if found then return receipt; end if;
 select * into strict c from public.rental_cases where id=p_case for update;
 if exists(select 1 from public.case_data_lifecycle_holds where rental_case_id=p_case) or c.is_active or c.updated_at>now()-make_interval(days=>p_days)
  or exists(select 1 from public.workflow_actions where rental_case_id=p_case and status not in ('succeeded','cancelled','superseded'))
  or exists(select 1 from public.workflow_execution_attempts where rental_case_id=p_case and (status='started' or (status<>'succeeded' and not retry_eligible)))
  or exists(select 1 from public.rental_case_approval_requests where rental_case_id=p_case and status='open')
 then raise exception 'case_lifecycle_hold'; end if;
 select encode(digest(coalesce(string_agg(row_to_json(e)::text,E'\n' order by e.id),''),'sha256'),'hex') into fingerprint
 from public.workflow_events e where rental_case_id=p_case;
 update public.outlook_inbound_conversations set conversation_id='sha256:'||encode(digest(conversation_id,'sha256'),'hex') where rental_case_id=p_case;
 update public.outlook_inbound_messages set message_id='sha256:'||encode(digest(message_id,'sha256'),'hex'),conversation_id='sha256:'||encode(digest(conversation_id,'sha256'),'hex'),raw_provider_payload='{"redacted":true}',envelope='{"redacted":true}' where rental_case_id=p_case;
 update public.inbound_source_records set dedupe_key='sha256:'||encode(digest(dedupe_key,'sha256'),'hex'),external_source_id='sha256:'||encode(digest(external_source_id,'sha256'),'hex'),conversation_reference='sha256:'||encode(digest(conversation_reference,'sha256'),'hex'),case_reference_hint=null,source_location_reference='[redacted]',evidence_excerpt='[redacted]',sender_actor_reference='[redacted]' where resolved_rental_case_id=p_case;
 update public.inbound_observations set observation_identity_key='sha256:'||encode(digest(observation_identity_key,'sha256'),'hex'),source_evidence_reference='redacted:'||id::text,source_excerpt='[redacted]',candidate_value_payload='{"redacted":true}',asserted_by_reference='[redacted]' where rental_case_id=p_case;
 update public.rental_case_facts set source_reference='redacted:'||id::text,value_payload='{"redacted":true}' where rental_case_id=p_case;
 update public.inquiry_response_draft_revisions set subject='[redacted]',salutation='[redacted]',intro_text='[redacted]',
  question_lines='["[redacted]"]',closing_text='[redacted]',signoff_text='[redacted]',body_text='[redacted]',context_payload='{"redacted":true}',
  sender_email='redacted@invalid.test',delivery_external_reference='[redacted]',recipient_email='redacted@invalid.test',recipient_label='[redacted]',sender_label='[redacted]',sender_display_name='[redacted]'
  where rental_case_id=p_case;
 update public.workflow_events set event_identity_key='sha256:'||encode(digest(event_identity_key,'sha256'),'hex'),origin_metadata='{}',source_reference='redacted:'||id::text,structured_payload='{"redacted":true}' where rental_case_id=p_case;
 update public.workflow_actions set structured_payload='{"redacted":true}' where rental_case_id=p_case;
 update public.workflow_execution_attempts set external_reference='[redacted]',response_snapshot='{"redacted":true}' where rental_case_id=p_case;
 update public.rental_case_approval_requests set evidence_reference_keys='{}',reason_text='[redacted]',decision_notes='[redacted]',decision_payload='{"redacted":true}' where rental_case_id=p_case;
 update public.rental_case_decisions set proposed_value_payload='{"redacted":true}',effective_value_payload='{"redacted":true}',scope_description='[redacted]' where rental_case_id=p_case;
 update public.rental_case_proposed_changes set prior_value_payload='{"redacted":true}',proposed_value_payload='{"redacted":true}',final_value_payload='{"redacted":true}' where rental_case_id=p_case;
 update public.rental_case_blockers set resolution_condition_text='[redacted]',resolution_reference=null where rental_case_id=p_case;
 update public.rental_case_open_questions set human_question_text='[redacted]',proposed_answer_payload=null,source_reference='[redacted]' where rental_case_id=p_case;
 update public.rental_case_follow_ups set context_payload='{}',waiting_for_reference=null where rental_case_id=p_case;
 update public.rental_case_reasoning_projections set degraded_retrieval_summary='{}',grounding_reference_keys='{}' where rental_case_id=p_case;
 update public.rental_cases set client_account_ref=null,primary_contact_ref=null,service_level_or_type='[redacted]' where id=p_case;
 receipt=gen_random_uuid();
 insert into public.case_data_lifecycle_events(id,rental_case_id,actor_reference,policy_version,request_reference,content_digest,disposition)
 values(receipt,p_case,p_actor,p_policy,p_request,fingerprint,'anonymized');
 return receipt;
end $$;
alter function public.anonymize_closed_rental_case(bigint,text,text,text,integer) owner to wnc_lifecycle_executor;
revoke all on function public.anonymize_closed_rental_case(bigint,text,text,text,integer) from public,anon,authenticated;
grant execute on function public.anonymize_closed_rental_case(bigint,text,text,text,integer) to service_role;

revoke create on schema public from wnc_lifecycle_executor;
do $$ begin execute format('revoke wnc_lifecycle_executor from %I',current_user); end $$;
