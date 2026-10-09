-- Explicit content erasure for fully retired historical cases, never active knowledge.
-- Linked source files must already have a data-owner erasure/retention disposition.
create table public.historical_data_lifecycle_events (
 id uuid primary key default gen_random_uuid(), historical_case_id bigint not null unique references public.historical_cases(id),
 actor_reference text not null, policy_version text not null, request_reference text not null,
 source_disposition_reference text not null, recorded_at timestamptz not null default now()
);
alter table public.historical_data_lifecycle_events enable row level security;
revoke all on public.historical_data_lifecycle_events from public,anon,authenticated;
grant select on public.historical_data_lifecycle_events to service_role;
grant select,insert on public.historical_data_lifecycle_events to wnc_lifecycle_executor;
create policy lifecycle_receipt on public.historical_data_lifecycle_events for all to wnc_lifecycle_executor using(true) with check(true);
grant update on public.historical_cases to wnc_lifecycle_executor;
create policy lifecycle_redaction on public.historical_cases for all to wnc_lifecycle_executor using(true) with check(true);
grant update on public.historical_case_versions to wnc_lifecycle_executor;
create policy lifecycle_redaction on public.historical_case_versions for all to wnc_lifecycle_executor using(true) with check(true);
grant update on public.historical_case_aliases to wnc_lifecycle_executor;
create policy lifecycle_redaction on public.historical_case_aliases for all to wnc_lifecycle_executor using(true) with check(true);
grant update on public.historical_case_version_decisions to wnc_lifecycle_executor;
create policy lifecycle_redaction on public.historical_case_version_decisions for all to wnc_lifecycle_executor using(true) with check(true);
grant update on public.historical_case_version_lessons to wnc_lifecycle_executor;
create policy lifecycle_redaction on public.historical_case_version_lessons for all to wnc_lifecycle_executor using(true) with check(true);
grant update on public.historical_case_version_responsibilities to wnc_lifecycle_executor;
create policy lifecycle_redaction on public.historical_case_version_responsibilities for all to wnc_lifecycle_executor using(true) with check(true);
grant update on public.historical_case_version_source_objects to wnc_lifecycle_executor;
create policy lifecycle_redaction on public.historical_case_version_source_objects for all to wnc_lifecycle_executor using(true) with check(true);
grant update on public.historical_case_version_knowledge_document_versions to wnc_lifecycle_executor;
create policy lifecycle_redaction on public.historical_case_version_knowledge_document_versions for all to wnc_lifecycle_executor using(true) with check(true);
grant update on public.historical_case_version_knowledge_documents to wnc_lifecycle_executor;
create policy lifecycle_redaction on public.historical_case_version_knowledge_documents for all to wnc_lifecycle_executor using(true) with check(true);
grant update on public.historical_case_version_logical_rules to wnc_lifecycle_executor;
create policy lifecycle_redaction on public.historical_case_version_logical_rules for all to wnc_lifecycle_executor using(true) with check(true);
grant update on public.historical_case_version_rule_versions to wnc_lifecycle_executor;
create policy lifecycle_redaction on public.historical_case_version_rule_versions for all to wnc_lifecycle_executor using(true) with check(true);
grant select,delete on private.historical_case_search_units,private.historical_case_embeddings,private.historical_case_unit_sources to wnc_lifecycle_executor;
grant select,update on private.historical_case_version_processing to wnc_lifecycle_executor;
do $$ declare name text; body text; begin
 foreach name in array array['private.enforce_historical_case_version_lifecycle()',
 'private.enforce_historical_case_version_statement_editability()',
 'private.enforce_historical_case_version_source_object_editability()',
 'private.enforce_hcv_authority_connectivity_editability()'] loop
 select pg_get_functiondef(name::regprocedure) into body;
 body:=regexp_replace(body,'\mbegin\M','begin IF current_user = ''wnc_lifecycle_executor'' THEN RETURN NEW; END IF;','i');
 execute body;
 end loop;
end $$;
create function public.anonymize_retired_historical_case(p_case bigint,p_actor text,p_policy text,p_request text,p_sources text,p_days integer)
returns uuid language plpgsql security definer set search_path=pg_catalog,public,private,extensions as $$
declare ids bigint[]; receipt uuid;
begin
 if p_actor is null or p_actor !~ '^entra:[0-9a-f-]{36}:[0-9a-f-]{36}$' or coalesce(p_policy,'')='' or coalesce(p_request,'')='' or coalesce(p_sources,'')='' or p_days is null or p_days<1
 then raise exception 'approved_historical_lifecycle_required'; end if;
 perform id from public.historical_cases where id=p_case for update;
 if not found then raise exception 'historical_case_missing'; end if;
 select id into receipt from public.historical_data_lifecycle_events where historical_case_id=p_case;
 if found then return receipt; end if;
 if exists(select 1 from public.historical_cases where id=p_case and updated_at>now()-make_interval(days=>p_days))
 or exists(select 1 from public.historical_case_versions where historical_case_id=p_case and
    (governance_status<>'retired' or updated_at>now()-make_interval(days=>p_days)))
 then raise exception 'historical_lifecycle_hold'; end if;
 select array_agg(id) into ids from public.historical_case_versions where historical_case_id=p_case;
 delete from private.historical_case_search_units where historical_case_id=p_case;
 update private.historical_case_version_processing set last_error_message=null where historical_case_version_id=any(ids);
 update public.historical_cases set canonical_title='[redacted]' where id=p_case;
 update public.historical_case_versions set curated_narrative='[redacted]',temporal_note=null,personal_information_notes=null where historical_case_id=p_case;
 update public.historical_case_aliases set alias_text='redacted-'||id::text where historical_case_id=p_case;
 update public.historical_case_version_decisions set decision_statement='[redacted]',historical_context=null where historical_case_version_id=any(ids);
 update public.historical_case_version_lessons set lesson_statement='[redacted]' where historical_case_version_id=any(ids);
 update public.historical_case_version_responsibilities set responsibility_statement='[redacted]' where historical_case_version_id=any(ids);
 update public.historical_case_version_source_objects set source_locator='redacted-'||id::text,relationship_notes=null where historical_case_version_id=any(ids);
 update public.historical_case_version_knowledge_document_versions set relationship_note=null where historical_case_version_id=any(ids);
 update public.historical_case_version_knowledge_documents set relationship_note=null where historical_case_version_id=any(ids);
 update public.historical_case_version_logical_rules set relationship_note=null where historical_case_version_id=any(ids);
 update public.historical_case_version_rule_versions set relationship_note=null where historical_case_version_id=any(ids);
 insert into public.historical_data_lifecycle_events(historical_case_id,actor_reference,policy_version,request_reference,source_disposition_reference)
 values(p_case,p_actor,p_policy,p_request,p_sources) returning id into receipt;
 return receipt;
end $$;
do $$ begin execute format('grant wnc_lifecycle_executor to %I',current_user); end $$;
grant create on schema public to wnc_lifecycle_executor;
alter function public.anonymize_retired_historical_case(bigint,text,text,text,text,integer) owner to wnc_lifecycle_executor;
revoke all on function public.anonymize_retired_historical_case(bigint,text,text,text,text,integer) from public,anon,authenticated;
grant execute on function public.anonymize_retired_historical_case(bigint,text,text,text,text,integer) to service_role;
revoke create on schema public from wnc_lifecycle_executor;
do $$ begin execute format('revoke wnc_lifecycle_executor from %I',current_user); end $$;
