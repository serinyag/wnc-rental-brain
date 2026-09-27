"""Boundaries for editorial continuity, prospective checks and response diagnostics."""
import hashlib
import json
from types import SimpleNamespace
import pytest
from tools.phase_08_workflow.tests.test_drafting_remediation import contract, codes
from tools.phase_08_workflow.context_aware_drafting import ContextualGuidance, guidance_editorial_priority
from tools.phase_08_workflow.operator_harness import OperatorHarnessClient, OperatorHarnessConfig, OperatorHarnessError
from tools.phase_08_workflow.test_console_service import TestConsoleService


@pytest.mark.parametrize('body', [
    "I'll check whether the venue is available on that date.",
    "I’ll check whether the venue is available for exclusive use.",
    "We will check if your booking has been confirmed.",
    "I'll check if the date is available.",
])
def test_prospective_embedded_proposition_is_not_a_confirmation(body):
    assert 'unsupported_availability_or_confirmation' not in codes(contract(), body)


@pytest.mark.parametrize('body', [
    'The venue is available.',
    "I'll check whether the venue is available, and it is.",
    "I'll check whether the venue is available. It is confirmed.",
    "We will check if the venue is available; yes, it is.",
    "I've checked whether the venue is available, and it is.",
    "I'll check whether the venue is available. Your booking is confirmed.",
    "I'll check whether the venue is available and the date is confirmed.",
    "I'll check the fee. The venue is confirmed.",
    "I’ll check whether the venue is available; your booking has been confirmed.",
])
def test_prospective_check_never_masks_an_independent_confirmation(body):
    assert 'unsupported_availability_or_confirmation' in codes(contract(), body)


def test_prior_draft_changes_editorial_context_never_current_assertions():
    current=contract(commercial_snapshot=(('Booking fee','EUR 75'),))
    followup=contract(commercial_snapshot=(('Booking fee','EUR 75'),),prior_client_drafts=('The old fee was EUR 50. We contacted the facilitator.',))
    assert followup.context_hash != current.context_hash
    assert followup.allowed_client_assertions == current.allowed_client_assertions
    assert followup.to_provider_payload()['external_pending'] == []
    assert 'commercial_assertion_not_allowed' in codes(followup, 'The fee is EUR 50.')


def test_editorial_history_tracks_client_turn_even_without_case_revision_change():
    def revision(rid, body):
        return SimpleNamespace(inquiry_response_draft_revision_id=rid,source_case_revision=2,body_text=body)
    def event(eid,rid,kind='governed_client_response_draft_generated'):
        return SimpleNamespace(workflow_event_id=eid,event_type_code=kind,structured_payload={'draft_revision_id':rid})
    prior=revision(1,'Earlier explanation');edited=revision(2,'Operator-edited earlier explanation')
    current=revision(3,'Current turn draft')
    incoming=SimpleNamespace(raw_evidence=SimpleNamespace(workflow_event_id=20),source_record=SimpleNamespace(sender_actor_type='client'))
    operator_note=SimpleNamespace(raw_evidence=SimpleNamespace(workflow_event_id=30),source_record=SimpleNamespace(sender_actor_type='operator'))
    earlier=SimpleNamespace(raw_evidence=SimpleNamespace(workflow_event_id=5),source_record=SimpleNamespace(sender_actor_type='client'))
    detail=SimpleNamespace(evidence_bundles=(operator_note,incoming,earlier),simulated_outlook_threads=(SimpleNamespace(draft_history=(current,prior,edited)),))
    snap=SimpleNamespace(rental_case=SimpleNamespace(case_revision=2),workflow_events=(event(10,1),event(12,2,'inquiry_response_draft_edited'),event(25,3)))
    assert TestConsoleService._prior_client_drafts(detail,snap)==('Operator-edited earlier explanation',)
    # Regenerating the same turn cannot make a draft its own editorial input.
    detail.simulated_outlook_threads[0].draft_history+=(revision(4,'Regeneration'),)
    snap.workflow_events+=(event(35,4),)
    assert TestConsoleService._prior_client_drafts(detail,snap)==('Operator-edited earlier explanation',)
    # A subsequent incoming message advances editorial history even though case
    # truth and the case revision remain unchanged.
    newer=SimpleNamespace(raw_evidence=SimpleNamespace(workflow_event_id=40),source_record=SimpleNamespace(sender_actor_type='client'))
    detail.evidence_bundles=(newer,operator_note,incoming,earlier)
    assert TestConsoleService._prior_client_drafts(detail,snap)==('Operator-edited earlier explanation','Regeneration')


def test_no_editorial_history_without_a_prior_recorded_draft_event():
    incoming=SimpleNamespace(raw_evidence=SimpleNamespace(workflow_event_id=20),source_record=SimpleNamespace(sender_actor_type='client'))
    revision=SimpleNamespace(inquiry_response_draft_revision_id=1,source_case_revision=1,body_text='Unproven chronology')
    detail=SimpleNamespace(evidence_bundles=(incoming,),simulated_outlook_threads=(SimpleNamespace(draft_history=(revision,)),))
    assert TestConsoleService._prior_client_drafts(detail,SimpleNamespace(workflow_events=())) == ()


def test_editorial_priority_never_removes_governed_guidance():
    from dataclasses import replace
    guide=ContextualGuidance('capacity','The requested guests are outside the current capacity rules.','phase4:test')
    assert guidance_editorial_priority(guide,'The date changed.')=='prevents_likely_problem'
    kitchen=ContextualGuidance('catering_kitchen','Governed kitchen constraint.','SERV-003')
    c=replace(contract(),latest_client_message='What time can the supplier unload?',contextual_guidance=(kitchen,))
    projected=c.to_provider_payload()['contextual_guidance'][0]
    assert projected['client_safe_guidance']==kitchen.client_safe_guidance
    assert projected['editorial_priority'].startswith('background_only')
    assert guidance_editorial_priority(kitchen,'We are bringing a buffet.')=='directly_relevant_to_latest_message'


@pytest.mark.parametrize('body,content_type', [('', 'application/json'), ('Private client name <html>','text/html'),('{"ok": tru','application/json'),('{"ok": true}\ntrailing','application/json')])
def test_malformed_response_is_an_error_with_diagnostics_but_no_body_content(body,content_type):
    class Response:
        headers={'Content-Type':content_type,'Content-Length':str(len(body.encode()))}
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def read(self):return body.encode()
    client=OperatorHarnessClient(OperatorHarnessConfig('https://example.test',None,None),opener=lambda *args,**kwargs:Response())
    with pytest.raises(OperatorHarnessError) as error:client.get_health()
    data=error.value.error_payload['diagnostics']
    assert data['content_type']==content_type
    assert data['body_length_bytes']==len(body.encode())
    assert data['body_sha256']==hashlib.sha256(body.encode()).hexdigest()
    assert isinstance(data['json_error_offset'],int)
    assert data['json_error']
    if body:
        assert body not in json.dumps(data)


def test_editorial_history_is_bounded_to_three_earlier_client_turns():
    bundles=tuple(SimpleNamespace(raw_evidence=SimpleNamespace(workflow_event_id=n),source_record=SimpleNamespace(sender_actor_type='client')) for n in (41,31,21,11,1))
    revisions=tuple(SimpleNamespace(inquiry_response_draft_revision_id=n,body_text=f'Answer {n}') for n in (5,15,25,35,45))
    events=tuple(SimpleNamespace(workflow_event_id=n,event_type_code='governed_client_response_draft_generated',structured_payload={'draft_revision_id':n}) for n in (5,15,25,35,45))
    detail=SimpleNamespace(evidence_bundles=bundles,simulated_outlook_threads=(SimpleNamespace(draft_history=revisions),))
    assert TestConsoleService._prior_client_drafts(detail,SimpleNamespace(workflow_events=events))==('Answer 15','Answer 25','Answer 35')
