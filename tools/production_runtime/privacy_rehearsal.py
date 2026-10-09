"""Exercise actual retention guards and raw-body erasure on a disposable DB."""
import json
from pathlib import Path
from .schema_rehearsal import sql
from .schema_provisioning import bootstrap_sql
from .schema_isolation import ROLES

ROOT=Path(__file__).resolve().parents[2]
DATABASE='wnc_privacy_split_rehearsal'
ACTOR='entra:7c9d7d19-2b22-4da3-975a-1fba6f29c366:40f4954d-5bbd-4d49-9ab2-527309f6deb2'

def main():
    def run(statement):return sql(statement,DATABASE)
    if DATABASE in sql('select datname from pg_database;','postgres').splitlines():raise RuntimeError('disposable_target_exists')
    sql('create database '+DATABASE+';','postgres')
    created=False
    result={'cloud_changes':0,'provider_calls':0,'production_cases_created':0}
    try:
        run('create schema extensions;')
        bootstrap,_=bootstrap_sql('b0fa5fbf-779f-4d1f-8e8f-2a3276fa4f06')
        run('begin;'+bootstrap+'create role wnc_staging_runtime nologin;commit;');created=True
        run((ROOT/'tools/production_runtime/privacy_lifecycle.sql').read_text())
        run("insert into rental_production.rental_types(rental_type_code,display_name,description) values('studio','Synthetic studio','Disposable retention rehearsal');")
        run("insert into rental_production.rental_cases(id,case_reference_code,lifecycle_state,rental_type_code) values(90001,'RC-90001','inquiry_active','studio');")
        run("insert into rental_production.inbound_source_records(id,source_system_code,source_record_type,dedupe_key,source_hash,external_source_id,conversation_reference,resolved_rental_case_id,association_status,occurred_at,evidence_excerpt) values(90001,'email','message','synthetic-source','synthetic-hash','synthetic-message','synthetic-conversation',90001,'resolved',now(),'Synthetic raw excerpt');")
        run("insert into rental_production.outlook_inbound_messages(mailbox,message_id,conversation_id,source_record_id,rental_case_id,association_status,association_basis,raw_provider_payload,envelope,source_hash) values('synthetic@invalid.test','synthetic-message','synthetic-conversation',90001,90001,'resolved','synthetic','{\"body\":{\"content\":\"Synthetic body\"},\"id\":\"synthetic-message\"}','{\"raw_body\":\"Synthetic body\",\"normalized_body\":\"Synthetic body\",\"subject\":\"Synthetic subject\"}','synthetic-hash');")
        run("insert into rental_production.workflow_events(rental_case_id,event_type_code,source_type,source_reference,actor_type,actor_reference,occurred_at,event_identity_key,structured_payload) values(90001,'outlook_inbound_evidence_recorded','synthetic','synthetic-source','system','synthetic',now(),'synthetic-event','{\"body\":\"Synthetic body\",\"source_hash\":\"synthetic-hash\"}');")
        run('grant wnc_production_runtime to postgres;')
        call=f"set role wnc_production_runtime;select rental_production.purge_closed_case_raw_bodies(90001,'{ACTOR}','WNC_PILOT_RETENTION_20261009');"
        def held(statement):
            try:run(statement)
            except RuntimeError as error:
                assert 'case_lifecycle_hold' in str(error)
            else:raise AssertionError('retention_hold_not_enforced')
        held(call)
        run("update rental_production.rental_cases set is_active=false,lifecycle_state='closed' where id=90001;")
        assert run('select count(*) from rental_production.runtime_case_closures;')=='1'
        held(call)
        run("update rental_production.runtime_case_closures set closed_at=now()-interval '181 days' where rental_case_id=90001;")
        run(f"insert into rental_production.case_data_lifecycle_holds values(90001,'{ACTOR}','synthetic legal hold',now());")
        held(call)
        run('delete from rental_production.case_data_lifecycle_holds where rental_case_id=90001;')
        digest=run(call);assert len(digest)==64
        assert run(call)==digest
        assert run("select (not raw_provider_payload ? 'body') and (not envelope ? 'raw_body') and (not envelope ? 'normalized_body') and message_id='synthetic-message' and source_hash='synthetic-hash' from rental_production.outlook_inbound_messages;")=='t'
        assert run("select (not structured_payload ? 'body') and structured_payload->>'source_hash'='synthetic-hash' from rental_production.workflow_events;")=='t'
        held(f"set role wnc_production_runtime;select rental_production.anonymize_case_at_calendar_expiry(90001,'{ACTOR}','WNC_PILOT_RETENTION_20261009','synthetic-expiry');")
        assert run("select timestamptz '2024-02-29 12:00:00+00'+interval '2 years'=timestamptz '2026-02-28 12:00:00+00';")=='t'
        run('update rental_production.rental_cases set is_active=true where id=90001;')
        assert run('select count(*) from rental_production.runtime_case_closures;')=='0'
        run("update rental_production.rental_cases set is_active=false,lifecycle_state='closed',updated_at=now()-interval '3 years' where id=90001;")
        run("update rental_production.runtime_case_closures set closed_at=now()-interval '2 years'-interval '1 day' where rental_case_id=90001;")
        receipt=run(f"set role wnc_production_runtime;select rental_production.anonymize_case_at_calendar_expiry(90001,'{ACTOR}','WNC_PILOT_RETENTION_20261009','synthetic-expiry');")
        assert len(receipt)==36
        assert run(f"set role wnc_production_runtime;select rental_production.anonymize_case_at_calendar_expiry(90001,'{ACTOR}','WNC_PILOT_RETENTION_20261009','synthetic-expiry');")==receipt
        try:run(f"set role wnc_production_runtime;select rental_production.anonymize_closed_rental_case(90001,'{ACTOR}','any-policy','bypass',1);")
        except RuntimeError as error:assert 'permission denied' in str(error)
        else:raise AssertionError('legacy_duration_bypass_available')
        result.update(status='passed',active_recent_and_legal_hold_guards=True,raw_expiry_preserves_identity_and_structured_evidence=True,replay_same_digest=True,calendar_year_expiry=True,reopening_clears_closure_clock=True)
    finally:
        sql('drop database '+DATABASE+';','postgres')
        if created:
            sql('drop role wnc_staging_runtime;','postgres')
            for role in reversed(list(ROLES.values())):sql('drop role '+role+';','postgres')
        result['disposable_target_removed']=True
        (ROOT/'docs/production_provisioning/privacy_split_rehearsal.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))

if __name__=='__main__':main()
