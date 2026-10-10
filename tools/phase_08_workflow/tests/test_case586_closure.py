"""Provider-free regression coverage for the bounded synthetic journey bridge."""
from types import SimpleNamespace as NS
from unittest.mock import patch
import pytest
from tools.phase_08_workflow.staging_layout_reply import BODY, MAILBOX, validate_message, run
from tools.phase_08_workflow.operational_resolution import capacity_inputs, current_resolutions


def message():
    return {'conversationId':'bound','subject':'Re: SYNTHETIC TEST — test','isDraft':True,
        'toRecipients':[{'emailAddress':{'address':MAILBOX}}], 'ccRecipients':[], 'bccRecipients':[],
        'body':{'content':BODY},'from':{'emailAddress':{'address':MAILBOX}}}


def test_exact_reply_binding():
    validate_message(message(),'bound')
    validate_message(message(),'bound',draft=True)


@pytest.mark.parametrize('field,value', [('conversationId','other'),('subject','ordinary'),
    ('toRecipients',[{'emailAddress':{'address':'other@example.com'}}]),
    ('ccRecipients',[{'emailAddress':{'address':'other@example.com'}}]),
    ('bccRecipients',[{'emailAddress':{'address':'other@example.com'}}]),
    ('isDraft',False),('body',{'content':'different body'})])
def test_reply_rejects_scope_or_content_drift(field,value):
    m=message();m[field]=value
    with pytest.raises(ValueError): validate_message(m,'bound',draft=True)


def test_reply_rejects_untrusted_source_sender():
    m=message();m['from']={'emailAddress':{'address':'other@example.com'}}
    with pytest.raises(ValueError):validate_message(m,'bound')


def test_disabled_gate_never_reaches_graph():
    with patch('tools.phase_08_workflow.staging_layout_reply.configuration',return_value=(NS(mailbox=MAILBOX),None)),patch(
        'tools.phase_08_workflow.staging_layout_reply.enabled',return_value=False),patch(
        'urllib.request.urlopen',side_effect=AssertionError('No Graph')):
        with pytest.raises(ValueError,match='gate_closed'):run()


@pytest.mark.parametrize('guests,layout',[(True,{'configuration_type':'seated'}),(24,None),(24,{'configuration_type':'unknown'}),(0,{'configuration_type':'seated'})])
def test_capacity_requires_explicit_canonical_inputs(guests,layout):
    s=NS(rental_case_facts=[NS(field_code='guest_count',value_payload=guests),NS(field_code='layout_requirements',value_payload=layout)])
    assert capacity_inputs(s) is None


def test_capacity_retains_complete_layout_provenance():
    layout={'configuration_type':'seated','style':'theatre'}
    s=NS(rental_case_facts=[NS(field_code='guest_count',value_payload=24),NS(field_code='layout_requirements',value_payload=layout)])
    assert capacity_inputs(s)=={'guest_count':24,'configuration_type':'seated','layout_requirements':layout}


def test_capacity_resolution_expires_when_guest_or_layout_changes():
    from copy import deepcopy
    from tools.phase_08_workflow.operational_resolution import scope, VERSION
    s=NS(rental_case=NS(rental_case_id=586,rental_type_code='studio_space',
        active_event_start='2026-11-12T13:00:00+00:00',active_event_end='2026-11-12T17:00:00+00:00'),
        rental_case_facts=[NS(field_code='guest_count',value_payload=24),
        NS(field_code='layout_requirements',value_payload={'configuration_type':'seated','style':'theatre'})])
    accepted={'version':VERSION,'contract':{'kind':'CAPACITY_LAYOUT_CONFIRMATION','scope':scope(s),
        'inputs':capacity_inputs(s),'subjects':['capacity_layout']},'outcomes':{'capacity_layout':'FEASIBLE'}}
    s.workflow_events=[NS(workflow_event_id=1,event_type_code='operational_resolution_accepted',structured_payload={'resolution':deepcopy(accepted)})]
    s.rental_case_facts.append(NS(field_code='operational_resolution:test',value_payload={**accepted,'event_id':1}))
    assert len(current_resolutions(s))==1
    s.rental_case_facts[0].value_payload=25
    assert not current_resolutions(s)
    s.rental_case_facts[0].value_payload=24
    s.rental_case_facts[1].value_payload={'configuration_type':'seated','style':'boardroom'}
    assert not current_resolutions(s)


@pytest.mark.parametrize('environment,send_gate',[('production',False),('staging',True)])
def test_receipt_verification_rejects_production_or_open_send_gate(environment,send_gate):
    from tools.phase_08_workflow.staging_layout_reply import receipt
    with patch('tools.phase_08_workflow.staging_layout_reply.load_env_value',return_value=environment),patch(
        'tools.phase_08_workflow.staging_layout_reply.enabled',side_effect=lambda key:send_gate if key=='STAGING_ALLOW_REAL_OUTLOOK_SEND' else True),patch(
        'urllib.request.urlopen',side_effect=AssertionError('No provider')):
        with pytest.raises(ValueError,match='receipt_read_scope_forbidden'):receipt()


@pytest.mark.parametrize('scenario',[None,'A','B','C'])
@pytest.mark.parametrize('mismatch',[None,'recipient','body','message_id','old_receipt','duplicate'])
def test_receipt_requires_exact_received_copy_and_never_mutates(mismatch,scenario):
    from datetime import datetime,timezone
    from tools.phase_08_workflow.staging_layout_reply import receipt
    from tools.phase_08_workflow.outlook_adapter import OutlookAdapterConfig
    class Connection:
        def __enter__(self):return self
        def __exit__(self,*a):pass
        def execute(self,*a):return self
        def fetchone(self):return ('outlook:message:sent-id','Approved subject','Approved body',MAILBOX,datetime(2026,10,9,11,tzinfo=timezone.utc))
        def fetchall(self):return [self.fetchone()+(51,1682,388,467)]
    sent={'id':'sent-id','internetMessageId':'<exact@example.test>','isDraft':False,'sentDateTime':'2026-10-09T11:00:01Z',
        'subject':'Approved subject','body':{'content':'Approved body'},'toRecipients':[{'emailAddress':{'address':MAILBOX}}],
        'conversationId':'final-conversation'}
    received={**sent,'id':'received-id','receivedDateTime':'2026-10-09T11:00:02Z'}
    if mismatch=='recipient':received['toRecipients']=[{'emailAddress':{'address':'wrong@example.test'}}]
    if mismatch=='body':received['body']={'content':'Changed'}
    if mismatch=='message_id':received['internetMessageId']='<other@example.test>'
    if mismatch=='old_receipt':received['receivedDateTime']='2026-10-09T10:59:00Z'
    calls=[]
    class Transport:
        def request(self,**kw):
            import json
            assert kw['method']=='GET' and kw['body'] is None
            calls.append(kw['url'])
            return 200,json.dumps(sent if len(calls)==1 else {'value':[received]*(2 if mismatch=='duplicate' else 1)}),{}
    env={'APP_ENV':'staging','DATABASE_URL':'postgresql://postgres:password@db.mspcopnsbounmdpivkvq.supabase.co/postgres'}
    with patch('tools.phase_08_workflow.staging_layout_reply.load_env_value',side_effect=env.get),patch(
        'tools.phase_08_workflow.staging_layout_reply.enabled',side_effect=lambda k:k!='STAGING_ALLOW_REAL_OUTLOOK_SEND'),patch(
        'psycopg.connect',return_value=Connection()),patch(
        'tools.phase_08_workflow.outlook_adapter.OutlookAdapterConfig.from_env',return_value=OutlookAdapterConfig('tenant','client','secret',MAILBOX)),patch(
        'tools.phase_08_workflow.outlook_adapter.OutlookExecutionAdapter._acquire_access_token',return_value=NS(result=None,access_token='fake')),patch(
        'tools.phase_08_workflow.outlook_inbound_runtime.ReadOnlyGraphTransport',return_value=Transport()):
        if mismatch:
            with pytest.raises(ValueError):receipt(scenario)
        else:
            result=receipt(scenario);assert result['receipt_verified'] and result['provider_mutations']==0
    assert len(calls)==2


@pytest.mark.parametrize('scenario',['D','A/anything','586'])
def test_journey_receipt_rejects_unapproved_lineage_before_provider(scenario):
    from tools.phase_08_workflow.staging_layout_reply import receipt
    with patch('tools.phase_08_workflow.staging_layout_reply.load_env_value',side_effect=AssertionError('No config access')):
        with pytest.raises(ValueError,match='receipt_synthetic_scenario_invalid'):receipt(scenario)


@pytest.mark.parametrize('scenario',['A','B','C'])
def test_journey_receipt_never_reads_production(scenario):
    from tools.phase_08_workflow.staging_layout_reply import receipt
    with patch('tools.phase_08_workflow.staging_layout_reply.load_env_value',return_value='production'),patch('psycopg.connect',side_effect=AssertionError('No database access')):
        with pytest.raises(ValueError,match='receipt_read_scope_forbidden'):receipt(scenario)
