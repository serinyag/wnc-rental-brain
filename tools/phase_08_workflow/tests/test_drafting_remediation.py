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
    assert 'availability' not in result[0].client_safe_guidance
    assert 'Do not confirm venue availability or booking.' in contract().forbidden_claims


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


def test_conditional_projection_retains_current_equipment_conditions():
    from tools.phase_08_workflow.test_console_service import TestConsoleService
    service=object.__new__(TestConsoleService)
    service._build_observed_field_candidates=lambda bundles: ()
    service._capacity_authority_issue=lambda *args,**kwargs: None
    service._technical_authority_issue=lambda **kwargs: SimpleNamespace(source_snapshot={'triggered_requirements':[
        {'semantic_state_code':'known_conditional','observed_requirement':'projection_display','issue_code':'projection_conditional',
         'source_snapshot':{'support_status':'requires_confirmation','conditions_summary':'A projector exists; compatibility and screenless setup must be checked.'}},
        {'semantic_state_code':'unknown_internal','observed_requirement':'hologram','issue_code':'hologram_unknown','source_snapshot':{}},
    ]})
    result=service._current_client_policy_guidance(SimpleNamespace(evidence_bundles=()),snapshot())
    assert len(result)==1
    assert 'projector exists' in result[0].client_safe_guidance
    assert 'must be checked' in result[0].client_safe_guidance
    assert 'hologram' not in str(result)


def test_followup_topics_retain_current_observed_requests_without_becoming_facts():
    from tools.phase_08_workflow.context_aware_drafting import detect_guidance_topics
    fields=(SimpleNamespace(field_code='catering_arrangement',value_payload='external',stale_observation=False),
            SimpleNamespace(field_code='technical_requirements',value_payload=['projection_display'],stale_observation=False),
            SimpleNamespace(field_code='facilitator_arrangement',value_payload='wnc_provided',stale_observation=True))
    topics=detect_guidance_topics(snapshot(),'The date is 21 January.',observed_fields=fields)
    assert topics==('catering_kitchen','external_supplier_setup','technical_capabilities')
    assert not any("catering" in fact or "projection" in fact for fact in contract().confirmed_case_facts)


def test_current_thread_changes_contract_hash_and_stays_separate_from_authority():
    from tools.phase_08_workflow.test_console_service import TestConsoleService
    detail=SimpleNamespace(evidence_bundles=tuple(SimpleNamespace(raw_evidence=SimpleNamespace(body=b),source_record=SimpleNamespace(sender_actor_type='client'))
        for b in ('Latest timing','Guest update','Original catering question')))
    detail.evidence_bundles += (SimpleNamespace(raw_evidence=SimpleNamespace(body='Confidential operator note'),source_record=SimpleNamespace(sender_actor_type='operator')), )
    prior=TestConsoleService._prior_client_messages(detail)
    assert prior==('Original catering question','Guest update')
    c=contract(prior_client_messages=prior)
    assert c.context_hash!=contract().context_hash
    assert c.prior_client_messages==prior
    assert 'prior_client_messages' not in c.to_provider_payload()
    assert 'Original catering question' not in str(c.to_provider_payload())
    assert c.allowed_client_assertions==contract().allowed_client_assertions


def test_facilitator_request_does_not_retrieve_class_cancellation_fee_as_process():
    guidance=retrieve_contextual_guidance(search=_Search(({
        'document_code':'CF-003','authority_classification':'authoritative',
        'body_text':'Cancellation of a scheduled class: EUR 45.',
    },)),topics=('facilitator_process',),rental_type_code=None)
    assert guidance==()


def test_rejected_text_audit_is_synthetic_staging_only_and_never_creates_draft():
    import pytest
    from tools.phase_08_workflow.test_console_service import TestConsoleService, TestConsoleError
    for staging,email,retained in ((True,'avery@example.test',True),(True,'avery@example.com',False),(False,'avery@example.test',False)):
        service=object.__new__(TestConsoleService)
        service.config=SimpleNamespace(runtime=SimpleNamespace(is_staging=staging))
        service.now=lambda: '2026-09-27T12:00:00Z'
        state=snapshot(workflow_actions=())
        detail=SimpleNamespace(metadata=SimpleNamespace(client_label='Avery',contact_email=email),
            evidence_bundles=(),orchestration_snapshot=state,
            working_proposal=SimpleNamespace(commercial_snapshot=(),feasibility_snapshot=()))
        service.load_case_detail=lambda case_id: detail
        service._require_case_snapshot=lambda case_id: state
        service._current_client_policy_guidance=lambda *args: ()
        service.contextual_guidance_search=_Search(())
        rejected=ClientResponseDraft('Subject','Hello — unsafe style')
        service._client_response_provider_for_request=lambda **kwargs: SimpleNamespace(generate_client_response=lambda contract: rejected)
        events=[]
        service._create_console_event=lambda **kwargs: events.append(kwargs)
        with pytest.raises(TestConsoleError,match='no draft was created'):
            service.generate_governed_client_response_draft(rental_case_id=8)
        assert len(events)==1 and events[0]['event_type_code']=='governed_client_response_draft_rejected'
        payload=events[0]['structured_payload']
        assert ('rejected_body' in payload)==retained
        if retained:
            assert payload['rejected_subject']==rejected.subject and payload['rejected_body']==rejected.body
        assert 'em_dash_not_allowed' in payload['validation_codes']


def test_logistics_requests_create_stable_internal_checks_without_contact_claims():
    fields=(SimpleNamespace(field_code='layout_requirements',value_payload={'notes':'handover, loading-route and supplier arrival guidance'},stale_observation=False),)
    items=derive_resolution_items(snapshot(),observed_fields=fields)
    assert len(items)==3
    assert items==derive_resolution_items(snapshot(),observed_fields=fields)
    assert all(i.resolution_owner=='WNC_INTERNAL' and i.blocking and i.client_visibility=='INTERNAL_ONLY' for i in items)
    assert len({i.proposition_key for i in items})==3
    c=contract(resolution_items=items)
    assert c.to_provider_payload()['external_pending']==[]
    assert 'Confirm the supplier loading route' not in str(c.to_provider_payload())


def test_timing_question_asks_only_missing_times_when_day_and_month_known():
    q=SimpleNamespace(open_question_id=7,human_question_text='What date and time is requested?',
        question_type='requested_event_timing',status='open',requested_from_role='client')
    c=build_draft_contract(snapshot=snapshot(open_questions=(q,)),recipient_label='Lena',latest_client_message='19 November')
    assert c.open_client_questions[0][1] == 'What start time and finish time would you like?'
    def validate(body):
        return validate_client_response_draft(contract=c,draft=ClientResponseDraft('Date',body,(7,)),
            current_case_revision=2,current_context_hash=c.context_hash)
    assert validate('What start and end times do you need on 19 November?').is_valid
    assert 'missing_client_question_component' not in codes(contract(),'What start time would you prefer?')


def test_timing_projection_does_not_reask_an_explicit_client_year():
    q=SimpleNamespace(open_question_id=7,human_question_text='What date and time is requested?',
        question_type='requested_event_timing',status='open',requested_from_role='client')
    for message in ('19 November 2026','November 19, 2026','2026-11-19','The year is 2026'):
        c=build_draft_contract(snapshot=snapshot(open_questions=(q,)),recipient_label='Lena',latest_client_message=message)
        assert 'including year' not in c.open_client_questions[0][1]


def test_supplier_acknowledgement_keeps_what_must_be_acknowledged():
    guidance=retrieve_contextual_guidance(search=_Search(({
        'document_code':'SERV-004','authority_classification':'authoritative',
        'body_text':'Supplier ID: TEMPLATE\nVenue-rule acknowledgement: Required before delivery\nInternal notes: Not client prose',
    },)),topics=('external_supplier_setup',),rental_type_code=None)
    assert 'Venue-rule acknowledgement: Required before delivery' in guidance[0].client_safe_guidance
    assert 'Internal notes' not in guidance[0].client_safe_guidance


def test_unresolved_supplier_windows_cannot_be_authorized_from_requested_times():
    fields=(SimpleNamespace(field_code='layout_requirements',value_payload={'notes':'Suppliers will arrive during setup'},stale_observation=False),)
    items=derive_resolution_items(snapshot(),observed_fields=fields)
    assert any(i.proposition_key.startswith('logistics:supplier_arrival:') for i in items)
    c=contract(resolution_items=items)
    for body in ('Suppliers may arrive from 13:30.', 'Please use 14:00 as the estimated unloading time.', 'Setup can begin at 14:00.'):
        assert 'unresolved_access_window_claim' in codes(c,body)
    assert 'unresolved_access_window_claim' not in codes(c,'Setup begins at the confirmed rental start. I will check the supplier access details for you.')


def test_decision_blocker_does_not_create_a_second_internal_approval_task():
    decision=SimpleNamespace(case_decision_id=58,status='proposed',decision_type='booking_fee_override')
    b=blocker(1747,'case_decision_approval_required','Approval must be approved')
    b.origin_entity_type='case_decision';b.origin_entity_reference='case_decision:58'
    items=derive_resolution_items(snapshot(case_decisions=(decision,),blockers=(b,)))
    assert len(items)==1 and items[0].resolution_owner=='GOVERNED_DECISION'


def test_internal_work_reuses_active_action_and_replaces_superseded_binding():
    from tools.phase_08_workflow.test_console_service import TestConsoleService
    from tools.phase_08_workflow.context_aware_drafting import with_workflow_actions
    b=blocker(3,'confirmation_required','Check setup')
    item=derive_resolution_items(snapshot(blockers=(b,)))[0]
    prior=SimpleNamespace(workflow_action_id=4,status='superseded',structured_payload={'resolution_item_key':item.proposition_key})
    assert with_workflow_actions((item,),(prior,))[0].workflow_action_id is None
    service=object.__new__(TestConsoleService);service.now=lambda:'2026-09-27T12:00:00Z'
    created=[];service.orchestration_repository=SimpleNamespace(create_workflow_action=lambda action:created.append(action))
    s=snapshot(workflow_actions=(prior,))
    service._ensure_resolution_workflow_actions(s,(item,))
    assert len(created)==1 and ':revision:2' in created[0].idempotency_key
    active=replace(created[0],workflow_action_id=5)
    s.workflow_actions=(prior,active)
    service._ensure_resolution_workflow_actions(s,(item,))
    assert len(created)==1
    assert with_workflow_actions((item,),s.workflow_actions)[0].workflow_action_id==5
