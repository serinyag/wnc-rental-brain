"""Regressions for observed client-projection, policy selection and validation defects."""
from dataclasses import replace
from types import SimpleNamespace
from tools.phase_08_workflow.tests.test_context_aware_drafting import snapshot, blocker, _Search
from tools.phase_08_workflow.context_aware_drafting import derive_resolution_items, retrieve_contextual_guidance
from tools.phase_08_workflow.governed_client_response import build_draft_contract, ClientResponseDraft, validate_client_response_draft


def contract(**kwargs):
    return build_draft_contract(snapshot=snapshot(),recipient_label='Avery',latest_client_message=None,**kwargs)


def codes(c,body,subject='Inquiry'):
    return validate_client_response_draft(contract=c,draft=ClientResponseDraft(subject,body),current_case_revision=2,current_context_hash=c.context_hash).failure_codes


def test_euro_normalization_does_not_allow_different_or_ambiguous_amounts():
    c=contract(commercial_snapshot=(("Booking fee","EUR 75 excluding VAT"),))
    for value in ('EUR 75','€75','EUR 75.00','€75,00'):
        assert not codes(c,f'The current fee is {value}.')
    for value in ('EUR 75000','EUR 75,000','€75.01','€50','EUR 7.5'):
        assert 'commercial_assertion_not_allowed' in codes(c,f'The current fee is {value}.')
    assert 'commercial_assertion_not_allowed' in codes(c,'Thanks.','Fee EUR 50')


def test_negation_is_narrow_and_does_not_hide_another_confirmation():
    c=contract()
    assert not codes(c,'The venue is not confirmed.')
    assert not codes(c,'The date is not yet available.')
    for body in ('The venue is confirmed.','The venue is not confirmed. Your booking is confirmed.',
                 'The date is available.', 'Your booking has been confirmed.'):
        assert 'unsupported_availability_or_confirmation' in codes(c,body)


def test_private_workflow_and_unknown_facts_do_not_reach_model():
    s=snapshot(blockers=(blocker(1,'availability_confirmation','Secret internal check'),),
               rental_case_facts=(SimpleNamespace(field_code='internal_margin',value_payload=99),))
    c=build_draft_contract(snapshot=s,recipient_label='Avery',latest_client_message=None)
    payload=c.to_provider_payload()
    assert 'Secret internal check' not in str(payload)
    assert 'internal_margin' not in str(payload)
    assert 'pending_internal_confirmations' not in payload
    assert c.operator_annotations[0].blocking
    assert 'Do not write a signature' in payload['signature_policy']


def test_supplier_guidance_omits_internal_notes_and_unrelated_prices():
    guidance=retrieve_contextual_guidance(search=_Search(({
        'document_code':'SERV-003','authority_classification':'authoritative',
        'body_text':'Rule: Use the current kitchen guidance.\nClient responsibility: Share equipment needs.\nInternal notes: Confidential margin.\nService fee: EUR 999',
    },)),topics=('catering_kitchen',),rental_type_code=None)
    assert guidance[0].client_safe_guidance=='Use the current kitchen guidance. Share equipment needs.'


def test_uncontacted_task_does_not_authorize_curly_apostrophe_contact_claim():
    s=snapshot(blockers=(blocker(1,'facilitator_confirmation','Contact facilitator'),))
    c=build_draft_contract(snapshot=s,recipient_label='Avery',latest_client_message=None)
    assert 'external_contact_not_recorded' in codes(c,'We’ve reached out to the facilitator.')
    assert 'system_sender_not_allowed' in codes(c,'Best regards,\nWNC Rental Brain')
    assert 'internal_uncertainty_exposed' in codes(c,'We are reviewing whether this works.')


def test_inquiry_availability_work_is_stable_and_not_client_prose():
    s=snapshot(rental_case=SimpleNamespace(rental_case_id=8,case_revision=2,rental_type_code='studio_space',
        lifecycle_state='inquiry_active',active_event_start='2027-01-01T10:00:00Z',active_event_end='2027-01-01T13:00:00Z'))
    items=derive_resolution_items(s)
    assert items==derive_resolution_items(s)
    assert len(items)==1 and items[0].resolution_owner=='WNC_INTERNAL' and items[0].blocking
    c=build_draft_contract(snapshot=s,recipient_label='Avery',latest_client_message=None)
    assert items[0].message not in str(c.to_provider_payload())


def test_phase4_known_equipment_answer_survives_unrelated_unknown_request():
    from tools.phase_08_workflow.test_console_service import TestConsoleService
    service=object.__new__(TestConsoleService)
    service._build_observed_field_candidates=lambda bundles: ()
    service._capacity_authority_issue=lambda *args,**kwargs: None
    service._technical_authority_issue=lambda **kwargs: SimpleNamespace(source_snapshot={'triggered_requirements':[
        {'semantic_state_code':'known_yes','observed_requirement':'projection_display','issue_code':'projection_supported',
         'source_snapshot':{'support_status':'available_on_request','requires_confirmation':False}},
        {'semantic_state_code':'unknown_internal','observed_requirement':'hologram','issue_code':'hologram_unknown','source_snapshot':{}},
    ]})
    result=service._current_client_policy_guidance(SimpleNamespace(evidence_bundles=()),snapshot())
    assert len(result)==1
    assert 'projection display' in result[0].client_safe_guidance
    assert 'available on request' in result[0].client_safe_guidance
    assert 'hologram' not in str(result)


def test_phase4_capacity_answer_does_not_confirm_date():
    from tools.phase_08_workflow.test_console_service import TestConsoleService
    service=object.__new__(TestConsoleService)
    service._build_observed_field_candidates=lambda bundles: ()
    service._capacity_authority_issue=lambda *args,**kwargs: SimpleNamespace(semantic_state_code='known_no',
        issue_code='capacity_entire_venue_restriction',source_snapshot={'published_max_guests':50})
    service._current_guest_count=lambda case: 65
    service._technical_authority_issue=lambda **kwargs: None
    result=service._current_client_policy_guidance(SimpleNamespace(evidence_bundles=()),snapshot())
    assert '65 guests are outside' in result[0].client_safe_guidance
    assert 'maximum is 50' in result[0].client_safe_guidance
    assert 'does not establish date availability' in result[0].client_safe_guidance


def test_generic_facilitator_blocker_uses_persisted_proposition_for_ownership():
    b=blocker(3,'confirmation_required','Structured confirmation is required')
    b.origin_entity_reference='reasoning_projection:projection-7'
    s=snapshot(blockers=(b,),reasoning_projections=(SimpleNamespace(projection_identity_key='projection-7',
        grounding_reference_keys=('test_console:facilitator_wnc_provided_confirmation',)),))
    item=derive_resolution_items(s)[0]
    assert item.resolution_owner=='EXTERNAL_PARTY'
    assert item.resolution_status=='CONTACT_REQUIRED'
    assert item.message.startswith('Contact facilitator')
    assert item.client_visibility=='INTERNAL_ONLY'
