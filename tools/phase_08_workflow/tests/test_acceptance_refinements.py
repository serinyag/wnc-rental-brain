from dataclasses import replace
from unittest.mock import patch
import pytest
from tools.phase_08_workflow.tests.test_google_proposal import harness, prepare, execute, binding
from tools.phase_08_workflow.tests.test_working_proposal import add_fact
from tools.phase_08_workflow.asana_projection import build_projection
from tools.phase_08_workflow.google_proposal import build_projection as google
from tools.phase_08_workflow.requested_detail_presentation import event_timing, technical_details
from tools.phase_08_workflow.observation_registry import get_field_definition
from tools.phase_08_workflow.observations import _value_matches_definition
from tools.phase_08_workflow.editorial_content_planner import EditorialContentItem, EditorialRole
from tools.phase_08_workflow.required_realization import requirements, realized

@pytest.mark.parametrize('schedule,known,missing', [
 ({'date':'2026-11-26','start':'10:00'},'Start time: 10:00','Event end time'),
 ({'date':'2026-11-26','end':'14:00'},'End time: 14:00','Event start time'),
 ({'date':'2026-11-26'},'Date: 26 November 2026','Event start time'),
 ({'date':'2026-11-26','approximate':'around lunchtime'},'Approximate timing requested: around lunchtime','Event end time'),
])
def test_partial_schedule_preserves_only_explicit_components(schedule,known,missing):
 repo,_,adapter=harness();repo.rental_cases[1]=replace(repo.rental_cases[1],active_event_start=None,active_event_end=None)
 add_fact(repo,'event_schedule',schedule)
 snap=repo.load_case_snapshot(1);plan=google(snap,folder_id='folder',provider_identity='test')
 assert known in plan['sections']['Event Overview']
 assert missing in plan['sections']['Working Timeline']
 asana=build_projection(snap,workspace_gid='1',project_gid='2')
 assert known in asana['master']['notes']
 assert 'Europe/Amsterdam' not in asana['master']['notes']
 assert not plan['sections']['Confirmed / Still TBC']
 if schedule.get('date'): assert 'Event date' not in plan['sections']['Working Timeline']
 if schedule.get('start'): assert 'Event start time' not in plan['sections']['Working Timeline']

def test_component_confirmation_does_not_confirm_other_equipment_or_specification():
 repo,_,adapter=harness();add_fact(repo,'technical_requirements',['projection_display','microphones'])
 add_fact(repo,'technical_request_details',{'projection_display':'Client laptop and HDMI adapter'})
 result={'subject':'projection_display','outcome':'FEASIBLE','assertion':'The requested projection setup is feasible for 13 November 2026 from 10:00 to 14:00.'}
 with patch('tools.phase_08_workflow.operational_resolution.client_results',return_value=[result]):
  plan=prepare(repo,adapter).structured_payload['projection']
 assert 'Projection: Requested' in plan['sections']['Current Scope']
 assert 'Microphones: Requested' in plan['sections']['Current Scope']
 assert 'Microphones feasibility' in plan['sections']['Working Timeline']
 assert 'Projection specification: Client laptop and HDMI adapter' in plan['sections']['Working Timeline']
 assert 'microphones' not in plan['sections']['Confirmed / Still TBC']

def test_detail_boundary_rejects_objects_unknown_subjects_and_confirmation_flags():
 definition=get_field_definition('technical_request_details')
 assert definition.human_validation_required and definition.default_review_posture=='human_only'
 assert _value_matches_definition({'internet_connectivity':'Dedicated 500 Mbps upload'},definition)
 for bad in ({'internet_connectivity':{'confirmed':True}},{'confirmed':'yes'},{'microphones':'one\ntwo'},{}):
  assert not _value_matches_definition(bad,definition)

def test_generic_reply_cannot_satisfy_specific_performance_check():
 item=EditorialContentItem('spec:internet','technical_specification','validated_client_request','spec:internet','client_request',
  {'action':'check','specification':'guaranteed dedicated 500 Mbps upload'},EditorialRole.MUST_COMMUNICATE,'client_request')
 plan=type('Plan',(),{'items':[item]})()
 req=requirements(plan)[0]
 assert not realized(req,"We'll check technical setup and get back to you.")
 assert realized(req,"We'll check your requested guaranteed dedicated 500 Mbps upload. It is not yet confirmed.")

def test_partial_to_full_followup_updates_same_doc_and_replay_without_mutation():
 repo,provider,adapter=harness();repo.rental_cases[1]=replace(repo.rental_cases[1],active_event_start=None,active_event_end=None)
 add_fact(repo,'event_schedule',{'date':'2026-11-26','start':'10:00'})
 assert execute(repo,adapter).action_status_after=='succeeded'
 before=binding(repo.load_case_snapshot(1))
 repo.rental_cases[1]=replace(repo.rental_cases[1],case_revision=1,active_event_start='2026-11-26T09:00:00+00:00',active_event_end='2026-11-26T13:00:00+00:00')
 assert execute(repo,adapter).action_status_after=='succeeded'
 after=binding(repo.load_case_snapshot(1));assert before['document_id']==after['document_id']
 plan=prepare(repo,adapter).structured_payload['projection']
 assert 'Time: 10:00–14:00' in plan['sections']['Event Overview']
 assert 'Event end time' not in plan['sections']['Working Timeline']
 mutations=len(provider.mutations);assert execute(repo,adapter).already_succeeded_idempotently
 assert len(provider.mutations)==mutations

def test_supplied_finish_time_followup_realizes_pending_change_and_availability():
 from tools.phase_08_workflow.tests.test_editorial_content_planner import contract
 from tools.phase_08_workflow.governed_client_response import DeterministicFakeClientResponseProvider
 from tools.phase_08_workflow.context_aware_drafting import ResolutionItem
 from tools.phase_08_workflow.required_realization import validate_required_realization
 c=replace(contract('Our requested finish time is now 14:00. Please check availability.'),
  change_or_reschedule_state=('event schedule',),open_client_questions=(),
  confirmed_case_facts=('Requested active event start: 2026-11-26T09:00:00+00:00','Requested active event end: 2026-11-26T13:00:00+00:00'),
  resolution_items=(ResolutionItem('availability:start:end','Check availability','WNC_INTERNAL','REQUIRED','INTERNAL_ONLY',True),),contextual_guidance=())
 d=DeterministicFakeClientResponseProvider().generate_client_response(c)
 assert all(row['realized'] for row in validate_required_realization(c.editorial_plan,d.body))
 assert '14:00' in d.body and 'availability' in d.body
 assert '?' not in d.body

def test_partial_event_schedule_keeps_requested_access_and_shared_date_once():
 repo,_,_=harness();repo.rental_cases[1]=replace(repo.rental_cases[1],active_event_start=None,active_event_end=None)
 add_fact(repo,'event_schedule',{'date':'2026-11-26','start':'10:00'})
 add_fact(repo,'load_in_schedule',{'date':'2026-11-26','start':'09:00','timezone':'Europe/Amsterdam','status':'requested_tbc'})
 add_fact(repo,'load_out_schedule',{'date':'2026-11-27','time':'15:00'})
 snap=repo.load_case_snapshot(1)
 g=google(snap,folder_id='test',provider_identity='test');a=build_projection(snap,workspace_gid='1',project_gid='2')
 assert 'Load-in: Requested from 09:00' in g['sections']['Current Scope']
 assert '26 November 2026' not in g['sections']['Current Scope']
 assert '27 November 2026' in g['sections']['Current Scope']
 assert 'Load-in requested: 09:00' in a['master']['notes']
 assert 'on 26 November 2026' not in a['master']['notes']
 assert 'on 27 November 2026' in a['master']['notes']
 assert 'Load-in timing' in g['sections']['Working Timeline']
 assert not g['sections']['Confirmed / Still TBC']
