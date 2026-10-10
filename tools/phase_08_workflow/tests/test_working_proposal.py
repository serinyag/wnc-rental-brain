from dataclasses import replace
from unittest.mock import patch

import pytest

from tools.phase_08_workflow.working_proposal import build_rental_working_proposal, TEMPLATES
from tools.phase_08_workflow.asana_projection import build_projection, prepare_projection, NUANCED_VERSION
from tools.phase_08_workflow.observation_contracts import RentalCaseFact
from tools.phase_08_workflow.observation_registry import get_field_definition
from tools.phase_08_workflow.tests.test_asana_projection import synthetic_repo, harness, execute, update_case, work_action, NOW
from tools.phase_08_workflow.live_proposal import render_live_proposal


def add_fact(repo, field, value, revision=0):
    repo.rental_case_facts[1].append(RentalCaseFact(100+len(repo.rental_case_facts[1]),1,field,'timing',value,
        'synthetic_email:validated',revision,NOW,NOW))


def nuanced(repo):
    return prepare_projection(repo,rental_case_id=1,workspace_gid='111',project_gid='222',now=NOW,version=NUANCED_VERSION)


@pytest.fixture(autouse=True)
def no_provider():
    with patch('urllib.request.urlopen',side_effect=AssertionError('Provider calls forbidden')):
        yield


def test_simple_studio_uses_existing_template_without_production_or_hospitality_checklist():
    repo=synthetic_repo();repo.workflow_actions[1]=[work_action(1,'venue','Check studio availability')]
    result=build_rental_working_proposal(repo.load_case_snapshot(1))
    assert result['template']['path'].endswith('Studio Rental Proposal Template.docx')
    assert not result['template_review_required']
    assert not {'production_days','load_in','catering_requirements'} & {r['key'] for r in result['details']}
    assert [s['key'] for s in result['next_steps']]==['item:venue']
    plan=build_projection(repo.load_case_snapshot(1),workspace_gid='111',project_gid='222',version=NUANCED_VERSION)
    assert [w['name'] for w in plan['work'] if w.get('kind')=='department']==['Admin']
    assert all(r['status']=='TBC' for r in result['details'])


@pytest.mark.parametrize('scope,filename',list(TEMPLATES.items()))
def test_every_existing_template_is_selected_from_explicit_scope(scope,filename):
    repo=synthetic_repo();add_fact(repo,'requested_rental_scope',scope)
    result=build_rental_working_proposal(repo.load_case_snapshot(1))
    assert result['template']['path'].endswith(filename)
    assert len(result['template']['sha256'])==64 and len(result['sections'])==7


def test_production_service_scope_keeps_venue_and_supplier_work_distinct():
    repo=synthetic_repo();add_fact(repo,'production_scope','full_production')
    add_fact(repo,'production_schedule',{'dates':['2026-11-11'],'day_count':1,'timezone':'Europe/Amsterdam'})
    add_fact(repo,'load_in_schedule',{'date':'2026-11-11','start':'09:00','timezone':'Europe/Amsterdam'})
    add_fact(repo,'technical_requirements',['microphones'])
    result=build_rental_working_proposal(repo.load_case_snapshot(1))
    assert result['template']['scope']=='full_production'
    details={r['key']:r for r in result['details']}
    assert details['requested_rental_scope']['value']=='studio_space'
    assert details['load_in_schedule']['status']=='TBC' and details['load_out_schedule']['value'] is None
    assert details['production_schedule']['source_reference']=='synthetic_email:validated'
    assert 'group:EXTERNAL_PARTY:supplier-logistics' in {s['key'] for s in result['next_steps']}


def test_unsupported_scope_requires_review_and_an_unusual_detail_is_preserved():
    repo=synthetic_repo();add_fact(repo,'requested_rental_scope','unknown_new_scope');add_fact(repo,'special_access','Freight lift required')
    result=build_rental_working_proposal(repo.load_case_snapshot(1))
    assert result['template']['scope']=='custom_scope' and result['template_review_required']
    assert next(r for r in result['details'] if r['key']=='special_access')['status']=='TBC'


def test_followup_updates_values_adds_relevant_work_and_replays_without_duplicates():
    repo,provider,adapter=harness();first=nuanced(repo);assert execute(repo,adapter,first).action_status_after=='succeeded'
    before=repo.execution_attempts[1][-1].response_snapshot['bindings']
    update_case(repo);add_fact(repo,'catering_arrangement','wnc_vendor',1)
    repo.create_workflow_action(replace(work_action(30,'catering','Confirm catering supplier','EXTERNAL_PARTY'),source_case_revision=1,idempotency_key='catering:1'))
    updated=build_rental_working_proposal(repo.load_case_snapshot(1))
    assert next(r for r in updated['details'] if r['key']=='guest_count')['value']==30
    a=nuanced(repo);assert execute(repo,adapter,a).action_status_after=='succeeded'
    after=repo.execution_attempts[1][-1].response_snapshot['bindings']
    assert all(after[k]['gid']==v['gid'] for k,v in before.items())
    assert after['item:catering']['parent_key']=='department:experience'
    mutations=len(provider.mutations);assert execute(repo,adapter,nuanced(repo)).already_succeeded_idempotently
    assert len(provider.mutations)==mutations


def test_optional_none_is_not_a_false_positive_confirmation_and_html_is_safe():
    repo=synthetic_repo();add_fact(repo,'catering_arrangement','none');add_fact(repo,'event_day_contact',{'name':'<script>oops</script>'})
    model=build_rental_working_proposal(repo.load_case_snapshot(1))
    assert next(r for r in model['details'] if r['key']=='catering_arrangement')['status']=='Not applicable'
    assert model['verified_operational_outcomes']==[] and not model['document_sync_enabled']
    page=render_live_proposal(repo.load_case_snapshot(1))
    assert '<script>' not in page and 'Studio Rental: Working Proposal' in page and 'Confirmed / Still TBC' in page


def test_agent_observation_boundary_requires_validation_for_each_new_detail():
    for field in ('production_scope','event_schedule','production_schedule','load_in_schedule','load_out_schedule'):
        definition=get_field_definition(field)
        assert definition.client_input_allowed and definition.human_validation_required
        assert definition.default_review_posture=='human_only'


def test_a_specific_open_question_activates_only_its_missing_detail():
    from tools.phase_08_workflow.contracts import OpenQuestion
    repo=synthetic_repo();snapshot=repo.load_case_snapshot(1)
    question=OpenQuestion(1,1,'load_out_schedule_confirmation','timing','What is the load out window?',
        'readiness','open',NOW,requested_from_role='client')
    snapshot=replace(snapshot,open_questions=(question,))
    model=build_rental_working_proposal(snapshot)
    details={r['key']:r for r in model['details']}
    assert details['load_out_schedule']['value'] is None and details['load_out_schedule']['status']=='TBC'
    assert 'technical_requirements' not in details
    assert any(s['key']=='question:1' for s in model['next_steps'])


def test_complex_proposal_remains_readable_when_asana_needs_operator_review():
    repo=synthetic_repo()
    for i in range(50,80):
        repo.create_workflow_action(replace(work_action(i,'special:'+str(i),'Review supplier '+str(i)),idempotency_key='special:'+str(i)))
    assert len(build_rental_working_proposal(repo.load_case_snapshot(1))['next_steps'])>25
    assert 'Review supplier 79' in render_live_proposal(repo.load_case_snapshot(1))
    with pytest.raises(ValueError,match='too much work'):
        nuanced(repo)


def test_nuanced_layout_preserves_the_ambiguity_fence():
    repo,provider,adapter=harness();original=provider.send_json;count=0
    def send(**kwargs):
        nonlocal count
        if kwargs['method']!='GET':
            count+=1
            if count==2:provider.next_failure='timeout_after_accept'
        return original(**kwargs)
    provider.send_json=send
    result=execute(repo,adapter,nuanced(repo))
    assert result.action_status_after=='failed' and not result.retry_eligible
    mutations=len(provider.mutations);update_case(repo)
    assert execute(repo,adapter,nuanced(repo)).failure_codes==('adapter_outcome_ambiguous',)
    assert len(provider.mutations)==mutations


def test_opaque_governed_technical_blocker_is_grouped_under_logistics():
    repo=synthetic_repo()
    repo.workflow_actions[1]=[work_action(1,'blocker:2388','Confirm event-specific technical setup'),work_action(2,'availability:window','Confirm Studio availability')]
    plan=build_projection(repo.load_case_snapshot(1),workspace_gid='111',project_gid='222',version=NUANCED_VERSION)
    work={w['key']:w for w in plan['work']}
    assert work['item:blocker:2388']['parent_key']=='department:logistics'
    assert work['item:availability:window']['parent_key']=='department:admin'
    assert {w['name'] for w in plan['work'] if w.get('kind')=='department'}=={'Admin','Logistics'}
