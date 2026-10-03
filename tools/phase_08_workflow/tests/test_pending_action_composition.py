from dataclasses import replace, fields
from pathlib import Path
import json
import pytest
from tools.phase_08_workflow.editorial_content_planner import EditorialContentItem, EditorialContentPlan, EditorialRole as Role
from tools.phase_08_workflow.pending_action_composition import pending_action_groups, must_say_projection
from tools.phase_08_workflow.required_realization import validate_required_realization, requirements
from tools.phase_08_workflow.governed_client_response import _provider_system_prompt
from tools.phase_08_workflow.tests.test_required_realization import Provider, generate
from tools.phase_08_workflow.tests.test_editorial_content_planner import contract

MESSAGE = 'Our group has grown to 30 and we now need the entire venue from 15:00 to 20:00 on 13 November instead.'
CHANGES = ('guest count', 'requested rental scope', 'requested reschedule is awaiting review')
COMPLETE = "I'll check the revised request, including the group size, full-venue hire and new date and time, then come back to you."


def changed_contract():
    return replace(contract(MESSAGE), change_or_reschedule_state=CHANGES)


def test_three_checks_one_projection_originals_unchanged():
    c = changed_contract(); plan = c.editorial_plan; before = plan.to_payload()
    groups = pending_action_groups(plan, MESSAGE)
    assert len(groups) == 1 and len(groups[0].items) == 3
    assert len({i.semantic_key for i in groups[0].items}) == 3
    assert tuple(i.value['requested_change'] for i in groups[0].items) == CHANGES
    projected = c.to_provider_payload()['must_say']
    assert len(projected) == 1 and projected[0]['subjects'] == list(CHANGES)
    assert projected[0]['report_back'] is True
    assert json.dumps(projected).count('report_back') == 1
    assert plan.to_payload() == before
    assert len(requirements(plan)) == 3
    assert all(r['realized'] for r in validate_required_realization(plan, COMPLETE))


@pytest.mark.parametrize('omitted,subjects', [
    (0, 'full-venue hire and new date and time'),
    (1, 'group size and new date and time'),
    (2, 'group size and full-venue hire'),
])
def test_each_omitted_subject_fails_its_own_original(omitted, subjects):
    results = validate_required_realization(changed_contract().editorial_plan, f"I'll check the {subjects} and come back to you.")
    assert [r['realized'] for r in results] == [i != omitted for i in range(3)]


def test_vague_check_does_not_realize_three_originals():
    assert not any(r['realized'] for r in validate_required_realization(changed_contract().editorial_plan, "I'll check your updated request and come back to you."))


def item(key, topic, value, reason='immediate_wnc_owned_next_step', role=Role.MUST_COMMUNICATE):
    return EditorialContentItem(key, topic, 'governed_case', key, 'current_governed', value, role, reason)


def plan(*items):
    return EditorialContentPlan('COMPLETE_INQUIRY_RESPONSE', (), items, 4, 'test')


@pytest.mark.parametrize('extra', [
    item('fact', 'audio_playback', {'fact_state': 'known', 'client_fact': {'background_music_playback': True}}),
    item('restriction', 'microphones', {'status': 'not_supported'}),
    item('question', 'client_information', {'question': 'What day?', 'open_question_id': 1}, role=Role.MUST_ASK),
    item('external', 'next_step', {'action': 'check', 'subjects': ['loading route'], 'status': 'check_required', 'owner': 'EXTERNAL_PARTY'}),
    item('decision', 'commercial_next_step', {'action': 'check', 'request': 'booking fee adjustment', 'status': 'check_required'}),
])
def test_materially_different_items_remain_outside_group(extra):
    original = changed_contract().editorial_plan
    p = replace(original, items=original.items + (extra,))
    assert all(extra not in group.items for group in pending_action_groups(p, MESSAGE + ' Loading route?'))
    if extra.role == Role.MUST_COMMUNICATE:
        assert extra.writing_value() in must_say_projection(p, MESSAGE)


def test_current_price_and_adjustment_remain_separate():
    p = plan(item('price', 'commercial', {'booking_fee': 'EUR 75 excl. VAT'}),
             item('adjustment', 'commercial_next_step', {'action': 'check', 'request': 'booking fee adjustment', 'status': 'check_required'}))
    assert not pending_action_groups(p, 'Could you adjust the fee?')
    assert len(must_say_projection(p, 'Could you adjust the fee?')) == 2


def test_supplier_logistics_share_group_and_each_witness():
    subjects = ('venue handover', 'supplier arrival timing', 'loading route')
    p = plan(*(item(s, 'next_step', {'action': 'check', 'subjects': [s], 'status': 'check_required'}) for s in subjects))
    message = 'Please check venue handover, supplier arrival timing and loading route.'
    groups = pending_action_groups(p, message)
    assert len(groups) == 1 and groups[0].subjects == subjects
    assert all(r['realized'] for r in validate_required_realization(p, "I'll check handover, supplier arrival and the loading route, then report back."))
    assert [r['realized'] for r in validate_required_realization(p, "I'll check handover and supplier arrival.")] == [True, True, False]


def test_historical_or_unmentioned_checks_not_grouped():
    p = changed_contract().editorial_plan
    assert not pending_action_groups(p, 'Thanks, noted.')
    historical = replace(p, items=tuple(replace(i, value={**i.value, 'turn': 'previous'}) for i in p.items))
    assert not pending_action_groups(historical, MESSAGE)


def test_one_narrow_composition_instruction():
    prompt = _provider_system_prompt()
    assert prompt.count('one report-back promise for the group') == 1
    assert COMPLETE not in prompt


def test_retry_same_original_obligations_and_unchanged_bound():
    c = changed_contract(); provider = Provider("I'll check the group size and full-venue hire.", COMPLETE)
    result = generate(provider, c)
    assert result.validation.is_valid and result.audit['corrective_retry_count'] == 1
    assert len(provider.calls) == 2
    assert provider.calls[0][1] is provider.calls[1][1]
    assert [i['required_meaning']['requested_change'] for i in provider.calls[1][2].unmet_items] == [CHANGES[2]]
    assert len(result.audit['final_realization_results']) == 3
    assert all(r['realized'] for r in result.audit['final_realization_results'])


def test_frozen_uat_006_turn_2_plan_payload():
    root = Path(__file__).resolve().parents[3]
    audits = json.loads((root / 'docs/staging/uat/required_realization/full_planner_audit.json').read_text())
    captured = next(a for a in audits if a.get('draft_revision_id') == 371)
    original = captured['editorial_content_plan']; names = {f.name for f in fields(EditorialContentItem)}
    items = tuple(EditorialContentItem(**{k: v for k, v in i.items() if k in names})
                  for role in Role for i in original[role.value.lower()])
    p = EditorialContentPlan(original['response_intent'], tuple(original['primary_client_need']), items, original['substantive_budget'], original['editorial_rationale'])
    payload = must_say_projection(p, captured['client_generation_payload']['latest_client_message'])
    assert len(payload) == 1 and payload[0]['subjects'] == list(CHANGES)
    assert len(requirements(p)) == 3
    assert all(r['realized'] for r in validate_required_realization(p, COMPLETE))
    assert {r['fingerprint'] for r in validate_required_realization(p, COMPLETE)} == {i['fingerprint'] for i in original['must_communicate']}
