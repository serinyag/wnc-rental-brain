"""Actual isolated PostgreSQL production-mode integration; no live provider."""
import io,json,os,time
from dataclasses import replace
from datetime import datetime,timezone,timedelta
from pathlib import Path
from uuid import uuid4
from unittest.mock import patch
from types import SimpleNamespace
import psycopg,pytest
from tools.production_runtime.test_production import production,signed_operator
from tools.production_runtime.auth import CURRENT
from tools.production_runtime.alerts import atomic_json
from tools.production_readiness.migration_rehearsal import sql,cmd,database_seed
from tools.phase_08_workflow.outlook_inbound_service import connection_runner,sync_page
from tools.phase_08_workflow.outlook_inbound import OutlookInboundConfig,OutlookInboundAdapter
from tools.phase_08_workflow.tests.test_outlook_inbound import message
from tools.phase_08_workflow.test_console_service import TestConsoleService,TestConsoleConfig
from tools.phase_08_workflow.test_console import build_test_console_app
from tools.phase_08_workflow.governed_client_response import DeterministicFakeClientResponseProvider
from tools.runtime_environment import AppRuntimeConfig,AppEnvironment
ROOT=Path(__file__).resolve().parents[2]

@pytest.fixture
def database(production):
    c,p,_=production;name='wnc_readiness_prod_'+uuid4().hex[:8]
    sql('postgres','create database '+name+' template template0;')
    try:
        sql(name,'create schema extensions;')
        for file in sorted((ROOT/'supabase/migrations').glob('*.sql')):sql(name,'begin;'+file.read_text()+'\ncommit;')
        sql(name,'begin;'+database_seed()+'\ncommit;')
        with psycopg.connect('postgresql://postgres:postgres@127.0.0.1:54322/'+name,autocommit=True) as conn:
            conn.execute('insert into public.runtime_environment_identity(deployment_id,environment) values(%s,%s)',(c.manifest['deployment_id'],'production'))
            yield conn,c,p,name
    finally:sql('postgres','drop database '+name+';')

def service(conn,c):
    runtime=AppRuntimeConfig(app_env=AppEnvironment.PRODUCTION,app_env_explicit=True,database_url=os.environ['DATABASE_URL'],production=c)
    return TestConsoleService(query_runner=connection_runner(conn),config=TestConsoleConfig(runtime=runtime,allow_real_providers=True),client_response_provider=DeterministicFakeClientResponseProvider(),contextual_guidance_search=SimpleNamespace(search=lambda **kwargs:()))

class Graph:
    def __init__(self,config,records):self.config,self.records,self.calls=config,records,[]
    def request(self,**kwargs):
        self.calls.append(kwargs)
        assert kwargs['method']=='GET'
        return 200,json.dumps({'value':self.records,'@odata.deltaLink':OutlookInboundAdapter(self.config,self,'fake').delta_path+'?$deltatoken=test'}),{}


def test_production_startup_intake_authority_approval_gates(database,monkeypatch):
    from tools.phase_08_workflow.operational_resolution import obligation,submit,current_resolutions
    from tools.phase_08_workflow.tests.test_provider_safety import make_asana_action
    conn,c,p,name=database
    svc=service(conn,c)
    from tools.production_runtime.config import knowledge_fingerprint
    c.manifest['baseline']['corpus_hash']=knowledge_fingerprint(svc.query_runner)
    # Real production build contract checks host/DB identity/config and DB marker;
    # only DB transport and model implementation are isolated test dependencies.
    # Synthetic P5/P6 availability is injected; live startup checks actual health.
    from http import HTTPStatus
    svc.get_health_report=lambda:SimpleNamespace(overall_status='ok',http_status=HTTPStatus.OK)
    app=build_test_console_app(config=svc.config,service=svc)
    assert app.contract is c
    verifier,key,claims=signed_operator(c,p);app.verifier=verifier
    import jwt
    token=jwt.encode(claims,key,algorithm='RS256');status=[]
    payload=app({'REQUEST_METHOD':'GET','PATH_INFO':'/api/operator/whoami','HTTP_AUTHORIZATION':'Bearer '+token},lambda s,h:status.append(s))
    assert status==['200 OK'] and p.actor in b''.join(payload).decode()
    assert all(not c.lane(k) for k in ('outlook_inbound','outlook_send','asana_mutations'))
    cfg=OutlookInboundConfig('rental@example.test','rental@example.test','2026-10-09T00:00:00Z',('client@example.test',),'',True,'production',10,c)
    record=message('prod-message','prod-conversation');record['toRecipients']=[{'emailAddress':{'address':cfg.mailbox}}];record['subject']='Ordinary venue enquiry'
    g=Graph(cfg,[record]);adapter=OutlookInboundAdapter(cfg,g,'fake')
    with pytest.raises(ValueError,match='gate_disabled'):adapter.read_page()
    assert not g.calls
    controls=c.controls();controls['lanes']['outlook_inbound']=True;controls['lease_expires']=time.time()+120;atomic_json(c.controls_path,controls)
    identity=CURRENT.set(p)
    try:
        first=sync_page(conn,adapter);cid=first['results'][0]['case_id'];assert cid
        replay=sync_page(conn,adapter);assert replay['results'][0]['duplicate']
        registered=conn.execute("select structured_payload,actor_reference from public.workflow_events where rental_case_id=%s and event_type_code='production_case_registered'",(cid,)).fetchone()
        assert registered[0]['test_case'] is False and registered[1]==p.actor
        observation=svc.inject_structured_test_observation(rental_case_id=cid,field_code='requested_rental_scope',
            observation_type='fact_candidate',claim_kind='new_information',value_text='studio_space',
            source_excerpt='Client requests Studio',sender_reference=None,external_test_reference='provider-message:prod-message:scope')
        assert observation.success
        assert svc.run_inquiry_intake(rental_case_id=cid).success
        snap=svc.orchestration_repository.load_case_snapshot(cid)
        assert snap.rental_case.rental_type_code=='studio_space'
        # Independent fixture builds a typed obligation from canonical event facts.
        base=make_asana_action(c.manifest['asana']['project_gid'])
        case=snap.rental_case;assert case.active_event_start
        action=svc.orchestration_repository.create_workflow_action(replace(base,rental_case_id=cid,
            action_type='CREATE_INTERNAL_TASK_ITEM',structured_payload={'resolution_owner':'WNC_INTERNAL','resolution_status':'REQUIRED',
             'resolution_item_key':f'availability:{case.active_event_start}:{case.active_event_end}'},idempotency_key='prod-resolution-'+str(uuid4())))
        contract=obligation(svc.orchestration_repository.load_case_snapshot(cid),action,environment='production')
        request={'workflow_action_id':action.workflow_action_id,'expected_case_revision':case.case_revision,'contract':contract,
         'outcomes':{case.rental_type_code:'AVAILABLE'},'evidence_reference':'operator-check:calendar-1','evidence_text':'Operator verified exact interval.',
         'occurred_at':(datetime.now(timezone.utc)-timedelta(seconds=1)).isoformat(),'idempotency_key':str(uuid4()),'synthetic':False}
        accepted=submit(svc.orchestration_repository,rental_case_id=cid,submission=request,actor=p.actor,environment='production')
        assert accepted['case_revision']==case.case_revision+1
        assert current_resolutions(svc.orchestration_repository.load_case_snapshot(cid))[0]['synthetic'] is False
        with pytest.raises(ValueError):submit(svc.orchestration_repository,rental_case_id=cid,submission={**request,'synthetic':True},actor=p.actor,environment='production')
        with pytest.raises(Exception):svc.execute_action(rental_case_id=cid,workflow_action_id=action.workflow_action_id,execution_mode='success')
        class FixtureProvider:
            def generate_client_response(self,contract):
                from tools.phase_08_workflow.governed_client_response import ClientResponseDraft
                from tools.phase_08_workflow.operational_resolution import client_results
                assertions=' '.join(x['assertion'] for x in client_results(svc.orchestration_repository.load_case_snapshot(cid)))
                questions=' '.join(q for _,q in contract.open_client_questions)
                return ClientResponseDraft('Studio enquiry','Hi,\n\nThanks for your enquiry. '+assertions+' '+questions,
                    question_ids=tuple(i for i,_ in contract.open_client_questions))
        svc.client_response_provider=FixtureProvider()
        try:generated=svc.generate_governed_client_response_draft(rental_case_id=cid)
        except Exception as e:raise AssertionError(getattr(e,'validation_codes',str(e))) from e
        assert generated.success
        draft=next(d for d in svc._list_draft_revisions(cid) if d.is_current)
        approved=svc.approve_request(rental_case_id=cid,approval_request_id=draft.approval_request_id)
        assert approved.success
        before=conn.execute('select count(*) from public.workflow_execution_attempts').fetchone()[0]
        with patch('urllib.request.urlopen',side_effect=AssertionError('Provider forbidden')):
            result=svc.execute_action(rental_case_id=cid,workflow_action_id=draft.workflow_action_id,execution_mode='real')
            assert not result.success
        assert conn.execute('select count(*) from public.workflow_execution_attempts').fetchone()[0]==before
        assert conn.execute("select decided_by_reference from public.rental_case_approval_requests where id=%s",(draft.approval_request_id,)).fetchone()[0]==p.actor
        # Explicitly close fake intake lane before closure and restore proof.
        controls['lanes']['outlook_inbound']=False;atomic_json(c.controls_path,controls)
        assert all(not c.lane(k) for k in controls['lanes'])
    finally:CURRENT.reset(identity)

def test_privacy_closed_case_hold_redaction_and_replay(database):
    from tools.production_runtime.auth import Principal
    from tools.production_runtime.privacy import anonymize_case
    conn,c,p,name=database;svc=service(conn,c)
    identity=CURRENT.set(p)
    try:
        assert svc.create_test_case(label='Private event title',client_label='Private Client',contact_email='client@example.test',event_reference='evidence-1').success
        cid=conn.execute('select max(id) from public.rental_cases').fetchone()[0]
    finally:CURRENT.reset(identity)
    admin=Principal(p.tenant,p.oid,frozenset({'ADMIN'}));identity=CURRENT.set(admin)
    try:
        with pytest.raises(Exception,match='case_lifecycle_hold'):
            anonymize_case(c,conn,case_id=cid,request_reference='privacy-request:1')
        # Age an isolated fixture; no production table/trigger is changed.
        conn.execute('alter table public.rental_cases disable trigger trg_rental_cases_touch_updated_at')
        conn.execute("update public.rental_cases set is_active=false,updated_at=now()-interval '40 days' where id=%s",(cid,))
        conn.execute('alter table public.rental_cases enable trigger trg_rental_cases_touch_updated_at')
        from tools.production_runtime.privacy import set_hold
        set_hold(c,conn,case_id=cid,reason_reference='legal-review:1',enabled=True)
        with pytest.raises(Exception,match='case_lifecycle_hold'):
            anonymize_case(c,conn,case_id=cid,request_reference='privacy-request:1')
        set_hold(c,conn,case_id=cid,reason_reference='legal-review:released',enabled=False)
        receipt=anonymize_case(c,conn,case_id=cid,request_reference='privacy-request:1')
        assert anonymize_case(c,conn,case_id=cid,request_reference='privacy-request:1')==receipt
        assert conn.execute('select structured_payload from public.workflow_events where rental_case_id=%s',(cid,)).fetchone()[0]=={'redacted':True}
        assert conn.execute('select actor_reference from public.case_data_lifecycle_events where rental_case_id=%s',(cid,)).fetchone()[0]==admin.actor
        assert conn.execute("select exists(select 1 from pg_auth_members where roleid='wnc_lifecycle_executor'::regrole and member='postgres'::regrole and (set_option or inherit_option))").fetchone()[0] is False
    finally:CURRENT.reset(identity)


def test_encrypted_dump_restore_app_compatibility(database,tmp_path):
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from tools.production_runtime.recovery import protect,recover
    conn,c,p,name=database;svc=service(conn,c);identity=CURRENT.set(p)
    try:assert svc.create_test_case(label='Restore fixture',client_label='Fixture',contact_email='client@example.test',event_reference='restore-source').success
    finally:CURRENT.reset(identity)
    dump=cmd(['pg_dump','-U','postgres','-d',name,'-Fc'])
    key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    pub=key.public_key().public_bytes(serialization.Encoding.PEM,serialization.PublicFormat.SubjectPublicKeyInfo)
    private=key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption())
    archive=protect(dump,pub,deployment_id=c.manifest['deployment_id'],ledger_hash='fixture-current',destination=tmp_path)
    restored=name+'_restore';sql('postgres','create database '+restored+' template template0;')
    try:
        # Preserve function owner isolation on restore; never use --no-owner here.
        sql('postgres','grant wnc_lifecycle_executor to postgres;')
        sql(restored,'grant create on schema public to wnc_lifecycle_executor;')
        cmd(['pg_restore','-U','postgres','-d',restored,'--exit-on-error'],recover(archive,private,expected_deployment=c.manifest['deployment_id']))
        with psycopg.connect('postgresql://postgres:postgres@127.0.0.1:54322/'+restored,autocommit=True) as restored_conn:
            c.verify_database_marker(connection_runner(restored_conn))
            recovered_service=service(restored_conn,c)
            assert len(recovered_service.list_test_cases())==1
            assert restored_conn.execute("select pg_get_userbyid(proowner) from pg_proc where oid='public.anonymize_closed_rental_case(bigint,text,text,text,integer)'::regprocedure").fetchone()[0]=='wnc_lifecycle_executor'
    finally:
        sql('postgres','revoke wnc_lifecycle_executor from postgres;')
        sql('postgres','drop database '+restored+';')

def test_monitor_and_external_evidence_are_safe(database):
    from .monitoring import check
    conn,c,p,_=database;identity=CURRENT.set(p)
    try:
        c.manifest['outlook']['allowed_senders'].append('supplier@example.test')
        c.manifest['outlook']['sender_roles']['supplier@example.test']='external_supplier'
        cfg=OutlookInboundConfig('rental@example.test','rental@example.test','2026-10-09T00:00:00Z',('supplier@example.test',),'',True,'production',10,c)
        record=message('external-message','external-unbound');record['from']={'emailAddress':{'address':'supplier@example.test'}};record['toRecipients']=[{'emailAddress':{'address':cfg.mailbox}}]
        controls=c.controls();controls['lanes']['outlook_inbound']=True;controls['lease_expires']=time.time()+60;atomic_json(c.controls_path,controls)
        result=sync_page(conn,OutlookInboundAdapter(cfg,Graph(cfg,[record]),'fake'))
        assert result['results'][0]['association_status']=='needs_review'
        assert conn.execute('select count(*) from public.rental_cases').fetchone()[0]==0
        assert conn.execute('select sender_actor_type from public.inbound_source_records').fetchone()[0]=='external_supplier'
        metrics=check(c,conn);assert metrics['association_review']==1
        assert any(json.loads(f.read_text())['code']=='ASSOCIATION_REVIEW' for f in Path(c.manifest['alerting']['spool_path']).glob('*.json'))
        controls['lanes']['outlook_inbound']=False;atomic_json(c.controls_path,controls)
    finally:CURRENT.reset(identity)

def test_retired_history_erasure_does_not_touch_active_authority(database):
    from tools.production_runtime.privacy import anonymize_history
    from tools.production_runtime.auth import Principal
    conn,c,p,_=database;identity=CURRENT.set(Principal(p.tenant,p.oid,frozenset({'ADMIN'})))
    try:
        cid=conn.execute("insert into public.historical_cases(case_code,canonical_title,updated_at) values('HC-999999','Private historic client',now()-interval '40 days') returning id").fetchone()[0]
        level=conn.execute('select min(id) from public.knowledge_confidentiality_levels').fetchone()[0]
        conn.execute("""insert into public.historical_case_versions(historical_case_id,version_number,governance_status,precedent_availability,precedent_type,evidence_strength,historical_event_status,temporal_precision,curated_narrative,confidentiality_level_id,contains_historical_value_only_content,updated_at)
          values(%s,1,'draft','held','limited_precedent','limited','completed','unknown','Private narrative',%s,false,now()-interval '40 days')""",(cid,level))
        with pytest.raises(Exception,match='historical_lifecycle_hold'):
            anonymize_history(c,conn,historical_case_id=cid,request_reference='history:1',source_disposition_reference='no-linked-files')
        # Isolated fixture aging, never a production trigger operation.
        conn.execute('alter table public.historical_case_versions disable trigger user')
        conn.execute("update public.historical_case_versions set governance_status='retired',updated_at=now()-interval '40 days' where historical_case_id=%s",(cid,))
        conn.execute('alter table public.historical_case_versions enable trigger user')
        before=conn.execute('select count(*) from public.rule_catalogue').fetchone()[0]
        receipt=anonymize_history(c,conn,historical_case_id=cid,request_reference='history:1',source_disposition_reference='no-linked-files')
        assert anonymize_history(c,conn,historical_case_id=cid,request_reference='history:1',source_disposition_reference='no-linked-files')==receipt
        assert conn.execute('select curated_narrative from public.historical_case_versions where historical_case_id=%s',(cid,)).fetchone()[0]=='[redacted]'
        assert conn.execute('select count(*) from public.rule_catalogue').fetchone()[0]==before
    finally:CURRENT.reset(identity)

def test_inbound_erasure_retains_hashed_replay_tombstone(database):
    from tools.production_runtime.privacy import anonymize_case
    from tools.production_runtime.auth import Principal
    conn,c,p,_=database;identity=CURRENT.set(p)
    cfg=OutlookInboundConfig('rental@example.test','rental@example.test','2026-10-09T00:00:00Z',('client@example.test',),'',True,'production',10,c)
    record=message('erase-message','erase-conversation');record['toRecipients']=[{'emailAddress':{'address':cfg.mailbox}}]
    controls=c.controls();controls['lanes']['outlook_inbound']=True;controls['lease_expires']=time.time()+120;atomic_json(c.controls_path,controls)
    adapter=OutlookInboundAdapter(cfg,Graph(cfg,[record]),'fake')
    try:
        first=sync_page(conn,adapter);cid=first['results'][0]['case_id']
        conn.execute("update public.workflow_actions set status='cancelled' where rental_case_id=%s",(cid,))
        conn.execute("update public.rental_case_approval_requests set status='rejected' where rental_case_id=%s",(cid,))
        conn.execute('alter table public.rental_cases disable trigger trg_rental_cases_touch_updated_at')
        conn.execute("update public.rental_cases set is_active=false,updated_at=now()-interval '40 days' where id=%s",(cid,))
        conn.execute('alter table public.rental_cases enable trigger trg_rental_cases_touch_updated_at')
        CURRENT.set(Principal(p.tenant,p.oid,frozenset({'ADMIN'})))
        anonymize_case(c,conn,case_id=cid,request_reference='erase-client:1')
        CURRENT.set(p)
        assert sync_page(conn,adapter)['results'][0]['duplicate']
        row=conn.execute('select message_id,raw_provider_payload from public.outlook_inbound_messages').fetchone()
        assert row[0].startswith('sha256:') and row[1]=={'redacted':True}
    finally:
        controls['lanes']['outlook_inbound']=False;atomic_json(c.controls_path,controls);CURRENT.reset(identity)
