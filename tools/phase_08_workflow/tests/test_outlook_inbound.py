import copy
import json
import os
from dataclasses import replace
from pathlib import Path
from urllib.parse import urlparse
from unittest.mock import patch
import pytest
from tools.phase_08_workflow.outlook_inbound import OutlookInboundAdapter, OutlookInboundConfig
from tools.phase_08_workflow.inbound_email import normalize_body
from tools.phase_08_workflow.outlook_inbound_service import sync_page

CONFIG=OutlookInboundConfig('staging@example.test','staging@example.test','2026-10-09T00:00:00Z',('client@example.test',),'SYNTHETIC TEST — rental enquiry',True)
ROOT=Path(__file__).resolve().parents[3]


def message(mid='m1',cid='c1',body='We would like 12 November 2026, 14:00 to 18:00.'):
    return dict(id=mid,conversationId=cid,internetMessageId='<'+mid+'@test>',receivedDateTime='2026-10-09T10:00:00Z',
        **{'from':{'emailAddress':{'address':'client@example.test'}}},toRecipients=[{'emailAddress':{'address':CONFIG.mailbox}}],ccRecipients=[],
        subject=CONFIG.new_enquiry_subject,body={'contentType':'text','content':body},hasAttachments=False,internetMessageHeaders=[],isDraft=False)


class Graph:
    def __init__(self,records): self.records,self.calls=records,[]
    def request(self,**kwargs):
        self.calls.append(kwargs)
        if '/attachments?' in kwargs['url']: return 200,json.dumps({'value':[{'id':'a1','name':'plan.pdf','size':12,'contentType':'application/pdf','isInline':False}]}),{}
        return 200,json.dumps({'value':self.records,'@odata.deltaLink':OutlookInboundAdapter(CONFIG,self,'fake').delta_path+'?$deltatoken=next'}),{}


def adapter(records): return OutlookInboundAdapter(CONFIG,Graph(records),'fake')


@pytest.fixture
def db():
    import psycopg
    dsn=os.environ.get('WNC_TEST_POSTGRES_DSN')
    if not dsn: pytest.skip('Explicit local PostgreSQL required')
    assert urlparse(dsn).hostname in ('127.0.0.1','localhost','::1')
    with psycopg.connect(dsn) as conn, conn.transaction(force_rollback=True), patch('urllib.request.urlopen',side_effect=AssertionError('Provider HTTP forbidden')):
        for migration in ('20260907000100_phase_08_governed_client_response_action_type.sql','20260913000100_phase_08_outlook_canonical_plan_identity.sql','20261003000100_phase_08_human_delivery_reconciliation.sql','20261003000200_phase_08_asana_projection_fences.sql','20261009000300_phase_08_outlook_inbound.sql'):
            conn.execute((ROOT/'supabase/migrations'/migration).read_text())
        yield conn


def test_normalization_preserves_raw_and_links():
    raw='<p>24 guests &amp; catering.</p><p>See <a href="https://example.test/menu">menu</a>.</p><script>unsafe()</script>'
    m=message();m['body']={'contentType':'html','content':raw}; e=adapter([]).envelope(m)
    assert e.raw_body==raw and '24 guests & catering.' in e.normalized_body and 'https://example.test/menu' in e.normalized_body
    assert 'unsafe' not in e.normalized_body


@pytest.mark.parametrize('url',['https://evil.test/v1.0/x','https://graph.microsoft.com/v1.0/users/production@example.test/mailFolders/inbox/messages/delta','http://graph.microsoft.com/v1.0/x'])
def test_cursor_scope_rejected_before_request(url):
    a=adapter([])
    with pytest.raises(ValueError):a.read_page(url)
    assert not a.transport.calls


@pytest.mark.parametrize('changes',[{'environment':'production'},{'mailbox':'production@example.test'},{'page_size':100}])
def test_scope_rejected(changes):
    with pytest.raises(ValueError):OutlookInboundAdapter(replace(CONFIG,**changes),Graph([]),'fake')


def test_gate_independent_and_disabled():
    a=OutlookInboundAdapter(replace(CONFIG,enabled=False),Graph([]),'fake')
    with pytest.raises(ValueError,match='gate_disabled'):a.read_page()
    assert not a.transport.calls


def test_read_page_and_immutable_header():
    a=adapter([message()]);records,cursor,status=a.read_page();assert len(records)==1 and status=='ready'
    assert 'ImmutableId' in a.transport.calls[0]['headers']['Prefer'] and a.transport.calls[0]['method']=='GET'
    e=a.envelope(records[0]); assert e.internet_message_id=='<m1@test>' and e.provider_conversation_id=='c1'


def test_new_case_replay_and_restart(db):
    a=adapter([message()]);one=sync_page(db,a); case=one['results'][0]['case_id'];sid=one['results'][0]['source_id']
    assert case and sid
    count=db.execute('select count(*) from public.inbound_observations where rental_case_id=%s',(case,)).fetchone()[0]
    two=sync_page(db,adapter([message()]));assert two['results'][0]=={'source_id':sid,'case_id':case,'association_status':'resolved','duplicate':True}
    assert db.execute('select count(*) from public.inbound_observations where rental_case_id=%s',(case,)).fetchone()[0]==count
    assert db.execute('select count(*) from public.outlook_inbound_conversations').fetchone()[0]==1
    assert two['checkpoint_version']==2


def test_followup_same_case_governed_revision(db):
    first=sync_page(db,adapter([message(body='We would like 12 November 2026.')]))['results'][0]
    cid=first['case_id'];before=db.execute('select case_revision from public.rental_cases where id=%s',(cid,)).fetchone()[0]
    m=message('m2',body='The time is 14:00 to 18:00.');m['subject']='Re: '+m['subject'];m['internetMessageHeaders']=[{'name':'In-Reply-To','value':'<m1@test>'}]
    result=sync_page(db,adapter([m]))['results'][0]
    assert result['case_id']==cid and result['source_id']!=first['source_id']
    assert db.execute('select case_revision from public.rental_cases where id=%s',(cid,)).fetchone()[0]>before
    assert db.execute('select count(*) from public.outlook_inbound_conversations').fetchone()[0]==1


@pytest.mark.parametrize('kind',['similar_subject','unknown_reply','same_sender','non_rental'])
def test_unbound_does_not_guess(db,kind):
    sync_page(db,adapter([message()]))
    m=message('m2','different');m['subject']='Re: '+m['subject'] if kind!='non_rental' else 'Newsletter'
    if kind=='unknown_reply':m['internetMessageHeaders']=[{'name':'References','value':'<unknown@test>'}]
    r=sync_page(db,adapter([m]))['results'][0]; assert r['case_id'] is None and r['association_status']==('out_of_scope' if kind=='non_rental' else 'needs_review')
    assert db.execute('select count(*) from public.outlook_inbound_conversations').fetchone()[0]==1


def test_two_explicit_new_conversations_remain_distinct(db):
    a=sync_page(db,adapter([message()]))['results'][0];b=sync_page(db,adapter([message('m2','c2')]))['results'][0]
    assert a['case_id']!=b['case_id']


def test_atomic_failure_does_not_advance_or_leave_case(db):
    before=db.execute('select count(*) from public.rental_cases').fetchone()[0]
    def fail():raise RuntimeError('crash_before_checkpoint')
    with pytest.raises(RuntimeError):sync_page(db,adapter([message()]),before_checkpoint=fail)
    assert db.execute('select count(*) from public.outlook_inbound_checkpoints').fetchone()[0]==0
    assert db.execute('select count(*) from public.outlook_inbound_messages').fetchone()[0]==0
    assert db.execute('select count(*) from public.rental_cases').fetchone()[0]==before
    assert sync_page(db,adapter([message()]))['results'][0]['case_id']


def test_raw_immutable_and_received_date_provenance(db):
    r=sync_page(db,adapter([message()]))['results'][0]
    raw,env=db.execute('select raw_provider_payload,envelope from public.outlook_inbound_messages').fetchone()
    assert raw==message() and env['received_at']==message()['receivedDateTime']
    with pytest.raises(Exception,match='evidence_immutable'), db.transaction():db.execute("update public.outlook_inbound_messages set raw_provider_payload='{}'")
    source=db.execute('select received_at,external_source_id,conversation_reference from public.inbound_source_records where id=%s',(r['source_id'],)).fetchone()
    assert source[0].isoformat().startswith('2026-10-09T10:00:00') and source[1:]==('m1','c1')


def test_attachments_not_fetched_and_no_outbound(db):
    m=message();m['hasAttachments']=True;a=adapter([m]);sync_page(db,a)
    assert len(a.transport.calls)==2 and all(c['method']=='GET' for c in a.transport.calls)
    assert db.execute("select envelope->'has_attachments' from public.outlook_inbound_messages").fetchone()[0] is True


def test_removed_item_is_audit_only(db):
    sync_page(db,adapter([message()]));r=sync_page(db,adapter([{'id':'m1','@removed':{'reason':'deleted'}}]))
    assert not r['results'] and db.execute('select count(*) from public.outlook_inbound_messages').fetchone()[0]==1


def test_local_end_to_end_uses_existing_reasoning_and_draft_preparation(db):
    from tools.phase_08_workflow.outlook_inbound_service import connection_runner
    from tools.phase_08_workflow.test_console_service import TestConsoleService,TestConsoleConfig
    from tools.runtime_environment import AppRuntimeConfig,AppEnvironment
    r=sync_page(db,adapter([message()]))['results'][0];cid=r['case_id']
    service=TestConsoleService(query_runner=connection_runner(db),config=TestConsoleConfig(runtime=AppRuntimeConfig(app_env=AppEnvironment.STAGING),allow_real_providers=False))
    detail=service.load_case_detail(cid)
    assert any(b.raw_evidence and b.raw_evidence.body==message()['body']['content'] for b in detail.evidence_bundles)
    report=service.run_reconciliation(rental_case_id=cid)
    assert report.success
    report=service.run_inquiry_waiting(rental_case_id=cid)
    assert report.success
    draft=service.generate_governed_client_response_draft(rental_case_id=cid,use_deterministic_fixture=True)
    assert draft.success
    from tools.phase_08_workflow.asana_projection import prepare_projection
    projection=prepare_projection(service.orchestration_repository,rental_case_id=cid,workspace_gid='111',project_gid='222',now=service.now())
    assert projection.structured_payload['projection']['master']['name']
    assert db.execute('select count(*) from public.workflow_execution_attempts where rental_case_id=%s',(cid,)).fetchone()[0]==0


@pytest.mark.parametrize('mutation',[
    lambda m:m.update(conversationId=''),
    lambda m:m.update(receivedDateTime='invalid'),
    lambda m:m.update(isDraft=True),
    lambda m:m.update(body={'contentType':'unknown','content':'x'}),
])
def test_bad_provider_shape_rolls_back(db,mutation):
    m=message();mutation(m)
    with pytest.raises((ValueError,KeyError)):sync_page(db,adapter([m]))
    assert db.execute('select count(*) from public.outlook_inbound_checkpoints').fetchone()[0]==0


def test_failure_after_success_leaves_original_checkpoint(db):
    sync_page(db,adapter([message()]));before=db.execute('select cursor,version from public.outlook_inbound_checkpoints').fetchone()
    def crash():raise RuntimeError('crash')
    with pytest.raises(RuntimeError):sync_page(db,adapter([message('m2')]),before_checkpoint=crash)
    assert db.execute('select cursor,version from public.outlook_inbound_checkpoints').fetchone()==before
    assert db.execute('select count(*) from public.outlook_inbound_messages').fetchone()[0]==1
    r=sync_page(db,adapter([message('m2')]))['results'][0];assert not r['duplicate']


def test_transport_forbids_mutations_and_wrong_hosts():
    from tools.phase_08_workflow.outlook_inbound_runtime import ReadOnlyGraphTransport
    for method,url in [('POST','https://graph.microsoft.com/v1.0/users/test/sendMail'),('GET','https://evil.test/x'),('GET','http://graph.microsoft.com/x')]:
        with pytest.raises(ValueError):ReadOnlyGraphTransport().request(method=method,url=url,headers={},body=None,timeout_seconds=1)


def test_provider_time_drives_missing_year(db):
    m=message(body='12 November, 14:00 to 18:00');sync_page(db,adapter([m]))
    rows=db.execute("select o.candidate_value_payload from public.inbound_observations o join public.outlook_inbound_messages m on m.source_record_id=o.inbound_source_record_id").fetchall()
    assert rows and rows[0][0]['resolved_date']=='2026-11-12'
    assert 'date_provenance' in rows[0][0]


def test_sender_outside_scope_cannot_start_client_work(db):
    m=message();m['from']['emailAddress']['address']='other@example.test'
    r=sync_page(db,adapter([m]))['results'][0];assert r['case_id'] is None and r['association_status']=='out_of_scope'


def test_failed_or_uncertain_graph_read_never_advances(db):
    a=adapter([]);a.transport.request=lambda **kw:(410,'{}',{})
    with pytest.raises(ValueError,match='410'):sync_page(db,a)
    assert db.execute('select count(*) from public.outlook_inbound_checkpoints').fetchone()[0]==0


def test_runtime_authorization_precedes_token_and_database():
    from tools.phase_08_workflow import outlook_inbound_runtime as runtime
    with patch.object(runtime,'load_env_value',side_effect=lambda key:'staging' if key=='APP_ENV' else None), patch.object(runtime,'ReadOnlyGraphTransport') as transport:
        with pytest.raises(ValueError,match='not_authorized'):runtime.preflight()
        with pytest.raises(ValueError,match='not_authorized'):runtime.synchronize()
        transport.assert_not_called()


def test_provider_page_missing_checkpoint_rolls_back(db):
    a=adapter([]);a.transport.request=lambda **kw:(200,json.dumps({'value':[message()]}),{})
    with pytest.raises(ValueError,match='checkpoint_uncertain'):sync_page(db,a)
    assert db.execute('select count(*) from public.outlook_inbound_messages').fetchone()[0]==0


def test_database_rejects_cross_case_binding(db):
    sync_page(db,adapter([message()]));row=db.execute('select source_record_id from public.outlook_inbound_messages').fetchone()
    with pytest.raises(Exception,match='binding_conflict'),db.transaction():
        db.execute("""insert into public.outlook_inbound_messages(mailbox,message_id,conversation_id,source_record_id,association_status,association_basis,raw_provider_payload,envelope,source_hash)
            values('other@example.test','wrong','wrong',%s,'needs_review','test','{}','{}','test')""",(row[0],))


def test_metadata_delta_fetches_only_admitted_body(db):
    wanted=message();other=message('unrelated','other');other['from']['emailAddress']['address']='outside@example.test'
    records=[{k:v for k,v in m.items() if k!='body'} for m in (wanted,other)]
    a=adapter(records);original=a.transport.request
    def request(**kw):
        if '/messages/m1?' in kw['url']:
            a.transport.calls.append(kw);return 200,json.dumps(wanted),{}
        return original(**kw)
    a.transport.request=request
    result=sync_page(db,a)
    assert result['results'][0]['case_id'] and result['results'][1]['association_status']=='out_of_scope'
    assert len(a.transport.calls)==2 and all('/messages/unrelated' not in c['url'] for c in a.transport.calls)
    assert db.execute('select count(*) from public.outlook_inbound_messages').fetchone()[0]==1


def test_cursor_rejection_reports_path_without_tokens():
    a=adapter([])
    with pytest.raises(ValueError) as caught:
        a.validate_cursor('https://graph.microsoft.com/v1.0/users/unexpected/mailFolders/inbox/messages/delta?$deltatoken=SECRET-CURSOR')
    details=caught.value.diagnostics
    assert details['returned_path'].startswith('/v1.0/users/unexpected/')
    assert details['cursor_values_redacted'] and 'SECRET-CURSOR' not in json.dumps(details)
    assert not a.transport.calls


@pytest.mark.parametrize('link_key', ['@odata.nextLink', '@odata.deltaLink'])
@pytest.mark.parametrize('odata_path', [False, True])
def test_provider_cursor_alias_and_opaque_state_round_trip(link_key, odata_path):
    a=adapter([])
    path=a.delta_path.replace('/mailFolders/inbox', "/mailFolders('inbox')") if odata_path else a.delta_path
    cursor=path.replace('%40','@')+'?'+('$skiptoken' if link_key.endswith('nextLink') else '$deltatoken')+'=opaque%2B%2F%3D&state=a%252Fb'
    a.transport.request=lambda **kw:(a.transport.calls.append(kw) or (200,json.dumps({'value':[],link_key:cursor}),{}))
    _,returned,status=a.read_page()
    assert returned==cursor and status==('paging' if link_key.endswith('nextLink') else 'ready')
    a.read_page(returned)
    assert a.transport.calls[-1]['url']==cursor


@pytest.mark.parametrize('path', [
    "/v1.0/users/other@example.test/mailFolders('inbox')/messages/delta",
    "/v1.0/users/staging@example.test/mailFolders('sentitems')/messages/delta",
    "/v1.0/users/staging@example.test/mailFolders/inbox/messages",
    "/v1.0/users/staging@example.test/mailFolders('inbox')/messages/delta/extra",
    "/v1.0/users/staging@example.test/mailFolders('inbox')/../messages/delta",
    "/v1.0/users/staging@example.test/mailFolders('inbox')/messages/%252e%252e/delta",
    "/beta/users/staging@example.test/mailFolders('inbox')/messages/delta",
    "/v1.0/me/mailFolders('inbox')/messages/delta",
])
def test_odata_cursor_other_scope_rejected_without_fetch(path):
    a=adapter([])
    with pytest.raises(ValueError,match='cursor_scope_forbidden'):
        a.read_page('https://graph.microsoft.com'+path+'?$deltatoken=opaque')
    assert not a.transport.calls


@pytest.mark.parametrize('origin', ['http://graph.microsoft.com','https://graph.microsoft.com.evil.test',
    'https://graph.microsoft.com:444','https://user@graph.microsoft.com'])
def test_odata_cursor_wrong_origin_rejected(origin):
    a=adapter([])
    path="/v1.0/users/staging@example.test/mailFolders('inbox')/messages/delta"
    with pytest.raises(ValueError,match='cursor_scope_forbidden'):a.read_page(origin+path+'?$deltatoken=opaque')
    assert not a.transport.calls


def test_preflight_replays_cursor_without_ingestion():
    from tools.phase_08_workflow import outlook_inbound_runtime as runtime
    a=adapter([]);original=a.transport.request
    def request(**kw):
        if '/mailFolders/inbox?' in kw['url']:
            a.transport.calls.append(kw);return 200,json.dumps({'id':'verified-inbox'}),{}
        return original(**kw)
    a.transport.request=request
    with patch.object(runtime,'build_adapter',return_value=a),patch.object(runtime,'sync_page') as ingest:
        r=runtime.preflight()
        ingest.assert_not_called()
    assert r['cursor_replay_valid'] and r['delta_pages_read']==2 and r['ingested']==0 and not r['checkpoint_persisted']
    assert len(a.transport.calls)==3 and all(c['method']=='GET' for c in a.transport.calls)


@pytest.mark.parametrize('dsn',[
    'postgresql://postgres:fake@db.mspcopnsbounmdpivkvq.supabase.co:5432/postgres',
    'postgresql://postgres.mspcopnsbounmdpivkvq:fake@aws-0-eu-central-1.pooler.supabase.com:5432/postgres',
])
def test_staging_database_accepts_verified_direct_and_pooler(dsn):
    from tools.phase_08_workflow.outlook_inbound_runtime import validate_staging_database
    validate_staging_database(dsn)


@pytest.mark.parametrize('dsn',[
    'postgresql://postgres.otherproject:fake@aws-0-eu-central-1.pooler.supabase.com:5432/postgres',
    'postgresql://postgres:fake@aws-0-eu-central-1.pooler.supabase.com:5432/postgres',
    'postgresql://postgres.mspcopnsbounmdpivkvq:fake@evil.test:5432/postgres',
    'postgresql://postgres:fake@db.otherproject.supabase.co:5432/postgres',
    'postgresql://postgres:fake@db.mspcopnsbounmdpivkvq.supabase.co:5432/other',
    'postgresql://postgres:fake@db.mspcopnsbounmdpivkvq.supabase.co:5432/postgres?host=evil.test',
    'postgresql://postgres.mspcopnsbounmdpivkvq:fake@aws-0-eu-central-1.pooler.supabase.com:6543/postgres',
])
def test_staging_database_rejects_routing_changes_before_provider(dsn):
    from tools.phase_08_workflow import outlook_inbound_runtime as runtime
    with patch.object(runtime,'configuration'),patch.object(runtime,'load_env_value',return_value=dsn),patch.object(runtime,'build_adapter') as build:
        with pytest.raises(ValueError,match='database_scope_forbidden'):runtime.synchronize()
        build.assert_not_called()


def outlook_reply():
    m=message('m2',body='unused');m['subject']='Re: '+m['subject']
    m['internetMessageHeaders']=[{'name':'In-Reply-To','value':'<m1@test>'}]
    m['body']={'contentType':'html','content':'<p>Please use 14:00 to 18:00 on 12 November 2026.</p><div id="divRplyFwdMsg">From: client<br>Sent: Friday, October 9, 2026</div><p>Original enquiry for 12 November 2026.</p>'}
    return m


def test_outlook_quoted_reply_excludes_header_date_only_for_timing(db):
    first=sync_page(db,adapter([message(body='12 November 2026')]))['results'][0]
    a=adapter([outlook_reply()]);r=sync_page(db,a)['results'][0]
    assert r['case_id']==first['case_id']
    obs=db.execute('select candidate_value_payload,status from public.inbound_observations where inbound_source_record_id=%s',(r['source_id'],)).fetchone()
    assert obs[1]=='validated' and obs[0]['start_time']=='14:00' and obs[0]['finish_time']=='18:00'
    raw,env=db.execute('select raw_provider_payload,envelope from public.outlook_inbound_messages where source_record_id=%s',(r['source_id'],)).fetchone()
    assert raw==outlook_reply() and 'October 9' in env['normalized_body']


def test_reply_boundary_requires_reply_headers_and_single_marker():
    from tools.phase_08_workflow.inbound_email import timing_evidence_body
    m=outlook_reply();m['internetMessageHeaders']=[];e=adapter([]).envelope(m)
    assert timing_evidence_body(e)==e.normalized_body
    m=outlook_reply();m['body']['content']+='<div id="divRplyFwdMsg">second</div>';e=adapter([]).envelope(m)
    assert timing_evidence_body(e)==e.normalized_body


def test_quarantined_reply_reprocessing_is_append_only_and_idempotent(db):
    from tools.phase_08_workflow.outlook_inbound_service import reprocess_quarantined_reply
    first=sync_page(db,adapter([message(body='12 November 2026')]))['results'][0]
    with patch('tools.phase_08_workflow.outlook_inbound_service.timing_evidence_body',side_effect=lambda e:e.normalized_body):
        reply=sync_page(db,adapter([outlook_reply()]))['results'][0]
    before=db.execute('select row_to_json(m) from public.outlook_inbound_messages m order by message_id').fetchall()
    checkpoint=db.execute('select * from public.outlook_inbound_checkpoints').fetchall()
    revision=db.execute('select case_revision from public.rental_cases where id=%s',(first['case_id'],)).fetchone()[0]
    result=reprocess_quarantined_reply(db,CONFIG,'m2')
    after_revision=db.execute('select case_revision from public.rental_cases where id=%s',(first['case_id'],)).fetchone()[0]
    assert after_revision>revision and result['source_id']==reply['source_id']
    assert db.execute('select status from public.inbound_observations where inbound_source_record_id=%s order by id',(reply['source_id'],)).fetchall()==[('quarantined',),('validated',)]
    assert reprocess_quarantined_reply(db,CONFIG,'m2')==result
    assert db.execute('select case_revision from public.rental_cases where id=%s',(first['case_id'],)).fetchone()[0]==after_revision
    assert db.execute('select row_to_json(m) from public.outlook_inbound_messages m order by message_id').fetchall()==before
    assert db.execute('select * from public.outlook_inbound_checkpoints').fetchall()==checkpoint
    assert db.execute('select count(*) from public.inbound_source_records where id=any(%s)',([first['source_id'],reply['source_id']],)).fetchone()[0]==2
    with pytest.raises(ValueError,match='binding_missing'):reprocess_quarantined_reply(db,CONFIG,'unknown')
    with pytest.raises(ValueError,match='gate_disabled'):reprocess_quarantined_reply(db,replace(CONFIG,enabled=False),'m2')


def test_authored_reply_with_two_event_dates_remains_quarantined(db):
    sync_page(db,adapter([message(body='12 November 2026')]))
    m=outlook_reply();m['body']['content']=m['body']['content'].replace('Please use','13 November 2026 or please use')
    r=sync_page(db,adapter([m]))['results'][0]
    assert db.execute('select status from public.inbound_observations where inbound_source_record_id=%s',(r['source_id'],)).fetchone()[0]=='quarantined'
