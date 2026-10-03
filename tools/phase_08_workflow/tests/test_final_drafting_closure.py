from dataclasses import replace
from types import SimpleNamespace
import pytest
from tools.phase_08_workflow.editorial_content_planner import is_pending_check_action, audio_fact_realized, EditorialRole
from tools.phase_08_workflow.tests.test_editorial_content_planner import contract, guide, selected, followup
from tools.phase_08_workflow.context_aware_drafting import ResolutionItem
from tools.phase_08_workflow.date_normalization import resolve_calendar_date, timing_components, normalize_timing, missing_timing_question
from tools.phase_08_workflow.tests.test_inquiry_intake import make_repo, make_case
from tools.phase_08_workflow.observation_types import InboundSourceRecordInput, StructuredObservationCandidate, StructuredObservationIngestionRequest, CaseAssociationInput
from tools.phase_08_workflow.observations import ingest_structured_observations
from tools.phase_08_workflow.inquiry_intake import apply_inquiry_intake


@pytest.mark.parametrize('value,expected', [
 ({'action':'check','subject':'custom aerial rig','questions':['can it be installed safely'],'report_back':True},True),
 ({'action':'check','status':'check_required','subjects':['venue availability']},True),
 ({'background_music_playback':True},False),
 ({'client_fact':{'background_music_playback':True},'fact_state':'known','action_required':False},False),
 ({'status':'conditional','check_required':['practical projection setup']},True),
 ({'action':'check'},False),
])
def test_pending_check_shapes(value,expected):assert is_pending_check_action(value)==expected


def test_rig_check_suppresses_unrequested_availability_but_explicit_question_wins():
 c=contract('Can you include a custom aerial rig?',contextual_guidance=(guide('other_technical',status='conditional'),),
            resolution_items=(ResolutionItem('availability:event','Check availability','WNC_INTERNAL','REQUIRED','INTERNAL_ONLY',True),))
 assert set(selected(c))=={'latest_client_detail','fact:other_technical'}
 assert next(i for i in c.editorial_plan.items if i.semantic_key=='next_step.availability').role==EditorialRole.DEFER
 assert c.editorial_plan.to_payload()['client_visible_pending_state']==[selected(c)['fact:other_technical'].writing_value()]
 explicit=replace(c,latest_client_message='Can you include a custom aerial rig, and is the venue available?')
 assert selected(explicit)['next_step'].value['subjects']==['requested date and venue availability']


@pytest.mark.parametrize('body,expected', [
 ('Background music is available.',True),('Background music is no problem.',True),
 ('You can play background music in the Studio.',True),('Light background music works in the Studio.',True),
 ('Music is fine. I will check the projection setup.',True),
 ('I’ll check the music setup.',False),('We’ll see what is possible.',False),
 ('I’ll check whether audio can work.',False),('Music is part of the request.',False),
 ('Music is part of the setup. I’ll check what fee adjustment may be possible.',False),
 ('Music is part of the setup and a fee adjustment is possible.',False),
 ('Music is part of the setup; a fee adjustment is available.',False),
 ('I will check whether music is available.',False),('Music is not available.',False),
 ('Music may be possible.',False),('If background music is available, we can use it.',False),
 ('I will check projection, and background music is available.',True),
])
def test_audio_realization_scoped(body,expected):assert audio_fact_realized(body)==expected


def test_audio_projection_are_distinct_and_only_valid_audio_realization_suppresses_followup():
 c=contract('Can we use slides and background music?',contextual_guidance=(guide('audio_playback',status='supported'),guide('projection_display',status='conditional')))
 audio=selected(c)['fact:audio_playback'];proj=selected(c)['fact:projection_display']
 assert audio.value=={'client_fact':{'background_music_playback':True},'fact_state':'known','action_required':False}
 assert not is_pending_check_action(audio.value) and is_pending_check_action(proj.value)
 good=followup(c,'We now expect 24 people.','You can play background music in the Studio. I will check projection.')
 bad=followup(c,'We now expect 24 people.','I will check music and projection. A fee adjustment may be possible.')
 assert next(i for i in good.editorial_plan.items if i.topic=='audio_playback').role==EditorialRole.ALREADY_COMMUNICATED
 assert selected(bad)['fact:audio_playback'].role==EditorialRole.MUST_COMMUNICATE


@pytest.mark.parametrize('day,month,year,anchor,expected,source', [
 (19,11,None,'2026-10-03T08:00:00Z','2026-11-19','system_inferred_next_occurrence'),
 (3,12,None,'2026-10-03T08:00:00Z','2026-12-03','system_inferred_next_occurrence'),
 (21,1,None,'2026-10-03T08:00:00Z','2027-01-21','system_inferred_next_occurrence'),
 (7,2,None,'2026-10-03T08:00:00Z','2027-02-07','system_inferred_next_occurrence'),
 (2,10,None,'2026-10-03T08:00:00Z','2027-10-02','system_inferred_next_occurrence'),
 (21,1,2026,'2026-10-03T08:00:00Z','2026-01-21','client_explicit'),
 (29,2,None,'2026-10-03T08:00:00Z','2028-02-29','system_inferred_next_occurrence'),
 (29,2,None,'2099-10-03T08:00:00Z','2104-02-29','system_inferred_next_occurrence'),
 (31,12,None,'2026-12-31T23:30:00Z','2027-12-31','system_inferred_next_occurrence'),
 (1,1,None,'2026-12-31T23:30:00Z','2027-01-01','system_inferred_next_occurrence'),
 (19,11,None,'2026-11-19T23:30:00Z','2027-11-19','system_inferred_next_occurrence'),
])
def test_date_boundaries(day,month,year,anchor,expected,source):
 d,p=resolve_calendar_date(day=day,month=month,year=year,reference_timestamp=anchor)
 assert str(d)==expected and p['year_source']==source and p['explicit_client_year']==year


def test_invalid_explicit_leap_date_and_naive_anchor_never_infer():
 with pytest.raises(ValueError):resolve_calendar_date(day=29,month=2,year=2027,reference_timestamp='2026-10-03T08:00:00Z')
 with pytest.raises(ValueError):resolve_calendar_date(day=19,month=11,year=None,reference_timestamp='2026-10-03T08:00:00')


@pytest.mark.parametrize('body,expected', [
 ('19 November, timing still TBC','What start time and finish time would you like?'),
 ('Sometime in November','What day, start time and finish time would you like?'),
 ('19 November from 17:00','What finish time would you like?'),
 ('19 November until 21:00','What start time would you like?'),
 ('Sometime this autumn','What date, start time and finish time would you like?'),
])
def test_question_only_missing_components(body,expected):
 assert missing_timing_question((body,))==expected
 assert 'year' not in expected


def ingest(repo,key,body,anchor='2026-10-03T08:00:00Z'):
 return ingest_structured_observations(request=StructuredObservationIngestionRequest(
  source_record=InboundSourceRecordInput(source_system_code='email',source_record_type='message',occurred_at=anchor,
   received_at=anchor,dedupe_key=key,source_hash=key,sender_actor_type='client',evidence_excerpt=body),
  case_association=CaseAssociationInput(rental_case_id=1),
  observations=(StructuredObservationCandidate(reported_field_code='active_event_window',observation_type='fact_candidate',
   claim_kind='new_information',candidate_value_payload=timing_components(body),source_evidence_reference=key,asserted_by_party_type='client',source_excerpt=body),)),repository=repo,now=lambda:anchor)


def test_inferred_date_persisted_before_intake_and_complete_schedule_closes_question():
 repo=make_repo(rental_cases=(make_case(),));apply_inquiry_intake(repository=repo,rental_case_id=1,actor_reference='test',actor_type='operator')
 result=ingest(repo,'jan','21 January from 17:00 to 21:00')
 value=result.observation_results[0].observation.candidate_value_payload
 assert value['resolved_date']=='2027-01-21' and value['active_event_start']=='2027-01-21T16:00:00+00:00'
 assert value['date_provenance']['year_source']=='system_inferred_next_occurrence'
 assert value['date_provenance']['explicit_client_year'] is None and 'year' not in value
 assert repo.rental_cases[1].active_event_start is None
 apply_inquiry_intake(repository=repo,rental_case_id=1,actor_reference='test',actor_type='operator')
 assert repo.rental_cases[1].active_event_start.startswith('2027-01-21')
 assert not any(q.question_type=='requested_event_timing' and q.status=='open' for q in repo.open_questions[1])


def test_later_explicit_correction_supersedes_inference_through_normal_reschedule():
 repo=make_repo(rental_cases=(make_case(),));first=ingest(repo,'first','21 January from 17:00 to 21:00')
 apply_inquiry_intake(repository=repo,rental_case_id=1,actor_reference='test',actor_type='operator')
 second=ingest(repo,'second','21 January 2028 from 17:00 to 21:00',anchor='2026-10-04T08:00:00Z')
 value=second.observation_results[0].observation.candidate_value_payload
 assert value['date_provenance']['year_source']=='client_explicit' and value['resolved_date']=='2028-01-21'
 assert first.observation_results[0].observation.candidate_value_payload['date_provenance']['year_source']=='system_inferred_next_occurrence'
 assert repo.reschedule_requests[1][-1].requested_date_payload['active_event_start'].startswith('2028-01-21')
 assert repo.rental_cases[1].active_event_start.startswith('2027-01-21')  # No bypass of governed change approval.


def test_partial_date_and_later_times_keep_original_year_provenance():
 repo=make_repo(rental_cases=(make_case(),));ingest(repo,'first','19 November, timing TBC')
 r=ingest(repo,'times','From 17:00 to 21:00',anchor='2026-10-04T09:00:00Z')
 v=r.observation_results[0].observation.candidate_value_payload
 assert v['active_event_start'].startswith('2026-11-19') and 'year' not in v
 assert v['date_provenance']['year_source']=='system_inferred_next_occurrence'
 assert v['date_provenance']['reference_timestamp']=='2026-10-03T08:00:00Z'


@pytest.mark.parametrize('text', ['29 March 2026 from 02:30 to 04:00','25 October 2026 from 02:30 to 04:00',
 '19 November 2026, the year is 2027','31 November from 10:00 to 14:00'])
def test_ambiguous_invalid_dates_and_dst_do_not_become_schedules(text):
 repo=make_repo(rental_cases=(make_case(),));r=ingest(repo,text,text)
 o=r.observation_results[0].observation
 assert o.status=='quarantined' and 'active_event_start' not in o.candidate_value_payload
 assert repo.rental_cases[1].active_event_start is None


def test_raw_evidence_uses_received_timestamp_and_persists_provenance_before_intake():
 from tools.phase_08_workflow.test_console_service import TestConsoleService
 repo=make_repo(rental_cases=(make_case(),));events=[]
 service=SimpleNamespace(observation_repository=repo,now=lambda:'2030-01-01T00:00:00Z',
  _load_test_case_metadata=lambda cid:SimpleNamespace(event_reference='TEST-1'),
  _create_console_event=lambda **kwargs:events.append(kwargs))
 TestConsoleService.inject_raw_test_evidence(service,rental_case_id=1,source_label='test',sender='client@example.test',
  subject='Gathering',body='21 January from 17:00 to 21:00',received_at='2026-10-03T08:00:00Z',external_test_reference='raw-date')
 observations=repo.list_observations_for_case(1)
 assert len(observations)==1
 value=observations[0].candidate_value_payload
 assert value['resolved_date']=='2027-01-21'
 assert value['date_provenance']['reference_timestamp']=='2026-10-03T08:00:00Z'
 assert value['date_provenance']['year_source']=='system_inferred_next_occurrence'
 assert events[0]['structured_payload']['body']=='21 January from 17:00 to 21:00'
 apply_inquiry_intake(repository=repo,rental_case_id=1,actor_reference='test',actor_type='operator')
 assert repo.rental_cases[1].active_event_start.startswith('2027-01-21')


def test_year_only_explicit_correction_keeps_prior_day_month_and_changes_provenance():
 repo=make_repo(rental_cases=(make_case(),));ingest(repo,'first','21 January from 17:00 to 21:00')
 r=ingest(repo,'correction','The year is 2028',anchor='2026-10-04T08:00:00Z')
 value=r.observation_results[0].observation.candidate_value_payload
 assert value['resolved_date']=='2028-01-21' and value['date_provenance']['year_source']=='client_explicit'
