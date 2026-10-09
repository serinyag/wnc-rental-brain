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
        for migration in ('20260907000100_phase_08_governed_client_response_action_type.sql','20260913000100_phase_08_outlook_canonical_plan_identity.sql','20261003000100_phase_08_human_delivery_reconciliation.sql','20261003000200_phase_08_asana_projection_fences.sql','20261009000100_phase_08_outlook_inbound.sql'):
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
