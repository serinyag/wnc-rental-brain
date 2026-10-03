"""Provider-free acceptance boundaries for the targeted editorial closure."""
from dataclasses import replace
from types import SimpleNamespace
import json
import pytest
from tools.phase_08_workflow.tests.test_editorial_content_planner import contract, guide, selected, followup
from tools.phase_08_workflow.tests.test_governed_client_response import make_snapshot
from tools.phase_08_workflow.editorial_content_planner import mentioned, pricing_context, EditorialRole
from tools.phase_08_workflow.context_aware_drafting import ContextualGuidance, detect_guidance_topics
from tools.phase_08_workflow.governed_client_response import ClientResponseDraft, validate_client_response_draft


@pytest.mark.parametrize('body,valid', [
    ('A WNC projector is available. Microphones need to come from an external supplier.', True),
    ('Microphones are available.', False),
    ('Microphones and a projector are available.', False),
    ('A projector and microphones are available.', False),
    ('WNC can provide the microphones.', False),
    ('WNC does not provide microphones.', True),
    ('Microphones are not provided, so please arrange them through an external supplier.', True),
    ('Microphones are not available, but a WNC projector is available.', True),
    ('A projector is available and microphones are not available.', True),
    ('Microphones are not available. They are available after all.', False),
    ('Microphones are available, but not included.', False),
    ('Microphones are available from an external supplier.', True),
    ('Microphones are not available and WNC can provide microphones.', False),
])
def test_known_no_scope(body, valid):
    c = contract('A projector and microphones', snapshot=make_snapshot(reasoning_projections=(SimpleNamespace(degraded_retrieval_summary={'semantic_state_code': 'known_no'}),)),
                 contextual_guidance=(guide('microphones', status='not_supported'), guide('projection_display', status='conditional')))
    result = validate_client_response_draft(contract=c, draft=ClientResponseDraft('Equipment', body),
        current_case_revision=c.source_case_revision, current_context_hash=c.context_hash)
    assert ('known_no_contradiction' not in result.failure_codes) == valid


@pytest.mark.parametrize('body,valid', [
    ('A projector is available. A DJ setup is not supported.', True),
    ('A DJ booth is available.', False),
    ('We can provide a DJ setup.', False),
])
def test_second_governed_topic(body, valid):
    c = contract(snapshot=make_snapshot(reasoning_projections=(SimpleNamespace(degraded_retrieval_summary={'semantic_state_code': 'known_no'}),)),
                 contextual_guidance=(guide('dj_sound_booth', status='not_supported'),))
    r = validate_client_response_draft(contract=c, draft=ClientResponseDraft('Equipment', body),
        current_case_revision=c.source_case_revision, current_context_hash=c.context_hash)
    assert ('known_no_contradiction' not in r.failure_codes) == valid


@pytest.mark.parametrize('text,topic,match', [
    ('Could you adjust the fee?', 'dj_sound_booth', False),
    ('A booking fee adjustment', 'dj_sound_booth', False),
    ('Does the usual pricing sound realistic?', 'audio_playback', False),
    ('The pricing sounds realistic', 'audio_playback', False),
    ('Background sound system', 'audio_playback', True),
    ('DJ setup', 'dj_sound_booth', True),
])
def test_topic_alias_boundaries(text, topic, match):
    assert mentioned(topic, text) == match
    if not match:
        assert topic not in contract(text).editorial_plan.primary_client_need
        assert 'technical_capabilities' not in detect_guidance_topics(make_snapshot(), text)


def test_acknowledged_dj_is_not_reopened_by_adjust():
    c = contract('We know a DJ setup is not available, which is fine. Could you adjust the booking fee?',
                 contextual_guidance=(guide('dj_sound_booth', status='not_supported'),))
    assert 'fact:dj_sound_booth' not in selected(c)


@pytest.mark.parametrize('text,requested,budget', [
    ('What does it cost?', True, 'absent'),
    ('What are your prices?', True, 'absent'),
    ('Could you send over an idea of what is possible and what it costs?', True, 'absent'),
    ('Our budget is tight. Does the usual pricing sound realistic?', True, 'general_constraint'),
    ('Our budget is tight.', False, 'general_constraint'),
    ('We have around EUR 1200', False, 'explicit_amount'),
    ('Does your usual pricing sound realistic for us?', True, 'absent'),
])
def test_pricing_and_budget_are_independent(text, requested, budget):
    assert pricing_context(text) == {'overall_pricing_requested': requested, 'budget_context': budget}
    if requested:
        value = selected(contract(text))['commercial.overall_pricing'].value
        assert value['budget_context'] == budget
        assert ('budget' in value['action']) == (budget != 'absent')


def test_audio_projection_is_a_fact_without_status_label():
    c = contract('Can we play background music?', contextual_guidance=(guide('audio_playback', status='supported', capability='audio playback'),))
    assert selected(c)['fact:audio_playback'].value == {'client_fact': {'background_music_playback': True}}
    assert c.contextual_guidance[0].semantic_values['status'] == 'supported'


def test_optional_hologram_delta_is_explicit():
    c = contract('The hologram is optional, so please do not hold up the rest of the planning for it. Normal projection covers the essentials.',
                 prior_client_messages=('Can we use a hologram?',))
    value = selected(c)['latest_client_detail'].value
    assert value == {'kind': 'client_preference_change', 'item': 'hologram', 'optional': True,
                     'should_not_delay': ['projection planning', 'event planning']}
    assert 'dependency' not in json.dumps(c.to_provider_payload())


def test_aerial_rig_uses_concrete_safety_checks():
    c = contract('Can we bring a custom aerial rig?', contextual_guidance=(guide('other_technical', status='conditional', check_required=['custom technical feasibility']),))
    value = selected(c)['fact:other_technical'].value
    assert value['subject'] == 'custom aerial rig'
    assert value['questions'] == ['can it be installed safely', 'can it be operated safely']
    assert value['report_back'] is True
    assert 'feasibility' not in json.dumps(c.to_provider_payload())


def test_accepted_compound_draft_suppresses_technical_and_catering_on_logistics_followup():
    c = contract('Can we use the projector and microphones, and prepare food in the kitchen?', contextual_guidance=(
        guide('projection_display', status='conditional', check_required=['compatibility'], available_equipment='WNC projector'),
        guide('microphones', status='not_supported', supplier_requirement='external supplier'),
        ContextualGuidance('catering_kitchen', 'The kitchen is best suited to ready-made food, warming and plating, not large-scale food production.', 'SERV-003')))
    body = 'A WNC projector is available. I will check the projection setup. Microphones need an external supplier. The kitchen is suited to warming and plating.'
    f = followup(c, 'What are the florist handover requirements, caterer loading route and arrival timing?', body)
    for topic in ('projection_display', 'microphones', 'catering_kitchen'):
        assert 'fact:' + topic not in selected(f)
        assert next(i for i in f.editorial_plan.items if i.semantic_key == 'fact:' + topic).role == EditorialRole.ALREADY_COMMUNICATED
