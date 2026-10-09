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
