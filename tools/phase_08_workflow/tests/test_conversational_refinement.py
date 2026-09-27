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
    followup=contract(commercial_snapshot=(('Booking fee','EUR 75'),),prior_client_draft='The old fee was EUR 50. We contacted the facilitator.')
    assert followup.context_hash != current.context_hash
    assert followup.allowed_client_assertions == current.allowed_client_assertions
    assert followup.to_provider_payload()['external_pending'] == []
    assert 'commercial_assertion_not_allowed' in codes(followup, 'The fee is EUR 50.')


def test_current_revision_is_excluded_from_editorial_history_and_old_case_revision_selected():
    def revision(case_rev,body,created):
        return SimpleNamespace(source_case_revision=case_rev,body_text=body,created_at=created)
    old=revision(1,'Earlier explanation',1);latest=revision(2,'Latest earlier explanation',2)
    current=revision(3,'Current draft',3)
    detail=SimpleNamespace(simulated_outlook_threads=(SimpleNamespace(draft_history=(current,old,latest)),))
    snap=SimpleNamespace(rental_case=SimpleNamespace(case_revision=3))
    assert TestConsoleService._prior_client_draft(detail,snap)=='Latest earlier explanation'
    detail.simulated_outlook_threads[0].draft_history+=(revision(3,'Regenerated current draft',4),)
    assert TestConsoleService._prior_client_draft(detail,snap)=='Latest earlier explanation'


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
