from dataclasses import replace
from types import SimpleNamespace
import json
import pytest
from tools.phase_08_workflow.editorial_content_planner import EditorialRole as Role, communicated_items
from tools.phase_08_workflow.context_aware_drafting import ContextualGuidance
from tools.phase_08_workflow.governed_client_response import build_draft_contract
from tools.phase_08_workflow.tests.test_governed_client_response import make_snapshot, client_question
from tools.phase_08_workflow.test_console_service import TestConsoleService as Console


def guide(topic, **value):
    return ContextualGuidance('technical_capabilities', 'RAW POLICY MUST STAY LOCAL', 'phase4:' + topic,
                              {'topic': topic, **value})


def contract(message='', **kwargs):
    snap=kwargs.pop('snapshot',make_snapshot())
    return build_draft_contract(snapshot=snap,recipient_label='Taylor',latest_client_message=message,**kwargs)


def selected(c):
    return {i.semantic_key:i for i in c.editorial_plan.items if i.included}


def followup(c, message, body, **kwargs):
    return contract(message,prior_client_messages=(c.latest_client_message,),prior_client_drafts=(body,),
        prior_editorial_items=tuple(communicated_items(c.editorial_plan,body)),contextual_guidance=c.contextual_guidance,**kwargs)


def test_roles_have_typed_auditable_identity_and_no_excluded_values_cross_boundary():
    c=contract('What time can we unload?',contextual_guidance=(ContextualGuidance('catering_kitchen','UNNEEDED POLICY','SERV-003'),))
    plan=c.editorial_plan
    assert plan == c.editorial_plan
    assert 'UNNEEDED POLICY' not in json.dumps(c.to_provider_payload())
    item=next(i for i in plan.items if i.source_reference=='SERV-003')
    assert item.role==Role.DEFER and not item.included
    assert item.fingerprint and item.semantic_key and item.reason
    assert item.value['source_text']=='UNNEEDED POLICY'


def test_audio_answer_does_not_repeat_but_conditional_projection_next_step_survives():
    c=contract('Can we use music and projection?',contextual_guidance=(guide('audio_playback',status='supported'),guide('projection_display',status='conditional',check_required=['compatibility'])))
    f=followup(c,'The hologram is optional. Normal projection and light music cover the essentials.', 'Music is fine. I will check the projection setup.')
    assert 'fact:audio_playback' not in selected(f)
    assert next(i for i in f.editorial_plan.items if i.topic=='audio_playback').role==Role.ALREADY_COMMUNICATED
    assert selected(f)['fact:projection_display'].role==Role.MUST_COMMUNICATE
    assert 'RAW POLICY' not in json.dumps(f.to_provider_payload())
    assert not any('supplier access' in str(i.value) for i in f.editorial_plan.items if i.included)


def test_explicit_repeat_question_and_changed_answer_override_novelty():
    c=contract('Is music possible?',contextual_guidance=(guide('audio_playback',status='supported'),))
    f=followup(c,'Can we play music?', 'Music is fine.')
    assert selected(f)['fact:audio_playback'].reason=='explicit_current_turn_question_requires_answer_again'
    changed=replace(f,contextual_guidance=(guide('audio_playback',status='not_supported'),))
    assert selected(changed)['fact:audio_playback'].prior_turn_status=='changed_since_prior_draft'


def test_planned_but_unspoken_fact_never_counts_as_communicated():
    c=contract('Could we play music?',contextual_guidance=(guide('audio_playback',status='supported'),))
    assert not communicated_items(c.editorial_plan,'Thanks, I will get back to you.')
    f=followup(c,'Can we play music?', 'Thanks, I will get back to you.')
    assert 'fact:audio_playback' in selected(f)


def test_missing_timing_beats_unrequested_kitchen_rules():
    kitchen=ContextualGuidance('catering_kitchen','The kitchen is best suited to ready-made food, warming and plating, not large-scale food production.','SERV-003')
    c=contract('A supper club with an external caterer. What do you need from us to check the date?',
        snapshot=make_snapshot(open_questions=(client_question(),)),contextual_guidance=(kitchen,))
    assert 'fact:catering_kitchen' not in selected(c)
    assert selected(c)['question:9'].role==Role.MUST_ASK
    assert 'large-scale' not in json.dumps(c.to_provider_payload())


def test_direct_kitchen_question_keeps_material_constraint_without_secondary_rules():
    kitchen=ContextualGuidance('catering_kitchen','The kitchen is best suited to ready-made food, warming and plating, not large-scale food production. Share equipment needs.','SERV-003')
    c=contract('What food can our caterer prepare?',contextual_guidance=(kitchen,))
    assert selected(c)['fact:catering_kitchen'].value['limitation']=='not large-scale food production'
    assert 'equipment needs' not in json.dumps(c.to_provider_payload())


def test_newly_available_fee_answers_earlier_question_and_unrelated_known_fee_is_deferred():
    first=contract('What is the booking fee?',commercial_snapshot=())
    final=followup(first,'The gathering is on 21 January, 17:00 to 21:00.', 'I will check the fee.',commercial_snapshot=(('Booking fee baseline','EUR 75 excl. VAT'),('VAT','21%'),('Effective booking fee','EUR 75 excl. VAT')))
    assert selected(final)['commercial.current'].value=={'booking_fee':'EUR 75 excl. VAT','vat':'21%'}
    unrelated=contract('Can we bring an aerial rig? Our budget is substantial.',commercial_snapshot=(('Booking fee','EUR 75'),))
    assert 'commercial.current' not in selected(unrelated)


def test_fee_already_answered_not_repeated_but_changed_fee_is_included():
    first=contract('What is the fee?',commercial_snapshot=(('Booking fee','EUR 75'),))
    final=followup(first,'The arrival time changed.', 'The booking fee is EUR 75.',commercial_snapshot=(('Booking fee','EUR 75'),))
    assert 'commercial.current' not in selected(final)
    changed=replace(final,allowed_client_assertions=('Booking fee: EUR 50',))
    assert selected(changed)['commercial.current'].prior_turn_status=='changed_since_prior_draft'


def test_compound_material_answers_and_all_open_questions_survive_budget():
    guides=tuple(guide(t,status='conditional',check_required=['review']) for t in ('audio_playback','projection_display','microphones','other_technical'))
    questions=tuple(client_question(n) for n in range(10,14))
    c=contract('Can we use music, slides, microphones and a hologram?',snapshot=make_snapshot(open_questions=questions),contextual_guidance=guides)
    assert len(c.editorial_plan.role_items(Role.MUST_ASK))==4
    assert all('fact:'+t in selected(c) for t in ('audio_playback','projection_display','microphones','other_technical'))
    assert c.editorial_plan.substantive_budget>=8
    assert c.editorial_plan.budget_reason=='compound_material_answers_and_client_questions'


def test_internal_resolution_is_auditable_but_never_written():
    from tools.phase_08_workflow.context_aware_drafting import ResolutionItem
    c=contract('What is the next step?',resolution_items=(ResolutionItem('private:1','PRIVATE COST DISCUSSION','WNC_INTERNAL','REQUIRED','INTERNAL_ONLY',True),))
    assert any(i.role==Role.INTERNAL_ONLY for i in c.editorial_plan.items)
    assert 'PRIVATE COST DISCUSSION' not in json.dumps(c.to_provider_payload())


def test_prior_metadata_is_hash_bound_and_latest_turn_cannot_feed_itself():
    def bundle(n):return SimpleNamespace(raw_evidence=SimpleNamespace(workflow_event_id=n),source_record=SimpleNamespace(sender_actor_type='client'))
    def event(n,key,kind='governed_client_response_draft_generated'):
        return SimpleNamespace(workflow_event_id=n,event_type_code=kind,structured_payload={'communicated_editorial_items':[{'semantic_key':key,'fingerprint':key}]})
    detail=SimpleNamespace(evidence_bundles=(bundle(20),bundle(1)))
    snap=SimpleNamespace(workflow_events=(event(10,'earlier'),event(30,'same-turn')))
    assert Console._prior_editorial_items(detail,snap)==({'semantic_key':'earlier','fingerprint':'earlier'},)
    snap.workflow_events+=(SimpleNamespace(workflow_event_id=15,event_type_code='inquiry_response_draft_edited',structured_payload={}),)
    assert Console._prior_editorial_items(detail,snap)==()
    assert contract('new').context_hash!=contract('new',prior_editorial_items=({'semantic_key':'a','fingerprint':'b'},)).context_hash
    assert contract('new').context_hash!=contract('changed').context_hash


def test_no_em_dash_and_other_existing_validators_still_apply():
    from tools.phase_08_workflow.governed_client_response import ClientResponseDraft,validate_client_response_draft
    c=contract('Can we book?')
    v=validate_client_response_draft(contract=c,draft=ClientResponseDraft('Confirmed','Your booking is confirmed — thanks.'),current_case_revision=c.source_case_revision,current_context_hash=c.context_hash)
    assert 'em_dash_not_allowed' in v.failure_codes
    assert 'unsupported_availability_or_confirmation' in v.failure_codes


def test_secondary_projection_conditions_are_deferred_unless_specifically_requested():
    g=guide('projection_display',status='conditional',available_equipment='WNC projector',check_required=['compatibility','adapters','files','screenless setup suitability'])
    c=contract('Normal projection is enough.',contextual_guidance=(g,))
    assert selected(c)['fact:projection_display'].value['check_required']==['practical projection setup']
    assert not any(i.topic=='projection_detail' for i in selected(c).values())
    assert 'screenless' not in json.dumps(c.to_provider_payload())
    specific=replace(c,latest_client_message='Which adapters and file formats are needed for projection?')
    assert selected(specific)['condition:projection:adapters'].role==Role.MUST_COMMUNICATE
    assert selected(specific)['condition:projection:files'].role==Role.MUST_COMMUNICATE


def test_setup_request_does_not_bundle_loading_or_handover_and_dj_setup_is_not_logistics():
    c=contract('Our caterer needs 45 minutes for setup.')
    assert selected(c)['next_step'].value['subjects']==['supplier setup access']
    dj=contract('We will bring a caterer. We know a DJ setup is not available, which is fine.')
    assert not any('supplier' in str(i.value) for i in selected(dj).values())


def test_overall_price_question_is_retained_independently_of_fee_and_adjustment():
    c=contract('What is the fee, and does the overall pricing fit our budget?',commercial_snapshot=(('Booking fee','EUR 75'),),
       snapshot=make_snapshot(case_decisions=(SimpleNamespace(status='proposed',decision_type='booking_fee_override'),)))
    assert 'commercial.current' in selected(c)
    assert 'commercial.overall_pricing' in selected(c)
    assert selected(c)['decision:booking fee override'].value['request']=='booking fee adjustment'
    assert 'override' not in json.dumps(c.to_provider_payload())


def test_client_acknowledged_restriction_stays_deferred_on_later_turn():
    c=contract('Timing is now known.',prior_client_messages=('We know a DJ setup is not available, which is fine.',),
        contextual_guidance=(guide('dj_sound_booth',status='not_supported',supplier_requirement='external supplier'),))
    assert 'fact:dj_sound_booth' not in selected(c)
    assert any(i.reason=='client_already_acknowledges_restriction' for i in c.editorial_plan.items)
    new_question=replace(c,latest_client_message='Can a DJ setup be provided now?')
    assert selected(new_question)['fact:dj_sound_booth'].value['status']=='not_supported'


def test_can_in_a_statement_is_not_a_new_explicit_question():
    from tools.phase_08_workflow.editorial_content_planner import asked_again
    assert not asked_again('supplier_access','The florist can arrive after handover.')
    assert asked_again('supplier_access','Can the florist arrive before handover?')


def test_client_question_normalization_retains_identity_and_information_need():
    q=client_question();q.human_question_text='Which space or rental scope is the client requesting?'
    c=contract('An offsite',snapshot=make_snapshot(open_questions=(q,)))
    assert c.to_provider_payload()['open_client_questions']==[{'topic':'client_information','open_question_id':9,'question':'Which space would you like?'}]
    assert c.open_client_questions[0][1]==q.human_question_text


def test_free_operational_fixture_keeps_projection_conditional_and_omits_deferred_policy():
    from tools.phase_08_workflow.governed_client_response import DeterministicFakeClientResponseProvider, validate_client_response_draft
    from tools.phase_08_workflow.required_realization import validate_required_realization
    c=contract('Can we use a projector?',contextual_guidance=(
        guide('projection_display',capability='projection display',status='conditional',available_equipment='WNC projector',check_required=['practical projection setup']),
        ContextualGuidance('external_supplier_setup','Supplier removes packaging','SERV-004')))
    draft=DeterministicFakeClientResponseProvider().generate_client_response(c)
    assert 'practical projection setup' in draft.body and "We'll check" in draft.body
    assert 'Supplier removes packaging' not in draft.body
    assert all(r['realized'] for r in validate_required_realization(c.editorial_plan,draft.body))
    assert validate_client_response_draft(contract=c,draft=draft,current_case_revision=4,current_context_hash=c.context_hash).is_valid
