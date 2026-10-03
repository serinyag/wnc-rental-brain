from dataclasses import replace, asdict
from types import SimpleNamespace
import json
import pytest
from unittest.mock import patch
from tools.phase_08_workflow.tests.test_editorial_content_planner import contract, guide, followup
from tools.phase_08_workflow.editorial_content_planner import EditorialRole as Role, EditorialContentItem, EditorialContentPlan, digest
from tools.phase_08_workflow.required_realization import validate_required_realization, requirements
from tools.phase_08_workflow.governed_client_response import (
 ClientResponseDraft, DraftValidationResult, generate_with_required_realization,
 validate_client_response_draft, OpenAIClientResponseProvider, DraftCorrection)


def audio_contract():
 return contract('Can we play background music?',contextual_guidance=(guide('audio_playback',status='supported'),))


def check(c,body):
 return validate_required_realization(c.editorial_plan,body)


@pytest.mark.parametrize('body,expected',[
 ('Background music is available.',True),('You can play background music in the Studio.',True),
 ('Light background music is no problem.',True),('Background music works in the Studio.',True),
 ('WNC can accommodate light background music.',True),
 ("I've noted the background music.",False),("I'll check whether background music is possible.",False),
 ('Background music is part of the plan.',False),('Music has been requested.',False),
 ("We'll see whether music is possible.",False),
 ('Music is part of the setup. I will check what fee adjustment may be possible.',False),
 ('Music is unavailable. Projection is possible.',False),
])
def test_audio_assertion_required(body,expected):assert check(audio_contract(),body)[0]['realized']==expected


class Provider:
 def __init__(self,*bodies):self.bodies=iter(bodies);self.calls=[]
 def generate_client_response(self,c):
  self.calls.append(('initial',c,None));return ClientResponseDraft('Subject',next(self.bodies))
 def correct_client_response(self,c,correction):
  self.calls.append(('correction',c,correction));return ClientResponseDraft('Subject',next(self.bodies))


def generate(provider,c=None,validator=None):
 c=c or audio_contract()
 return generate_with_required_realization(provider=provider,contract=c,safety_validator=validator or
  (lambda d:validate_client_response_draft(contract=c,draft=d,current_case_revision=c.source_case_revision,current_context_hash=c.context_hash)))


def test_safe_omission_gets_exactly_one_correction_same_contract_and_plan():
 c=audio_contract();before=asdict(c);p=Provider("I've noted the music.",'Background music is available.')
 r=generate(p,c)
 assert r.validation.is_valid and len(p.calls)==2 and r.audit['corrective_retry_count']==1
 assert p.calls[0][1] is c and p.calls[1][1] is c and asdict(c)==before
 correction=p.calls[1][2]
 assert correction.contract_identity==digest(before)
 assert [v['semantic_key'] for v in correction.unmet_items]==['fact:audio_playback']
 assert r.audit['initial_candidate_hash']!=r.audit['corrected_candidate_hash']
 assert r.audit['attempts'][0]['failed_realization_item_ids']==['fact:audio_playback']
 assert all(v['realized'] for v in r.audit['final_realization_results'])
 assert 'Background music is available.' not in correction.to_payload()['instruction']


def test_success_needs_no_retry():
 p=Provider('Background music is available.');r=generate(p)
 assert r.validation.is_valid and len(p.calls)==1 and r.audit['corrective_retry_count']==0


def test_second_omission_rejected_without_third_attempt():
 p=Provider('Music is part of the plan.',"I've noted the music.")
 r=generate(p)
 assert not r.validation.is_valid and len(p.calls)==2
 assert r.validation.failure_codes==('required_semantic_items_not_realized',)


@pytest.mark.parametrize('body',[
 'The booking fee is EUR 99.', 'Your booking is confirmed.', 'Hello — music noted.',
])
def test_safety_failure_never_retries(body):
 p=Provider(body);r=generate(p)
 assert not r.validation.is_valid and len(p.calls)==1
 assert r.audit['corrective_retry_count']==0 and r.audit['final_realization_results']==[]


def test_second_candidate_safety_failure_stops():
 p=Provider('Music noted.','Your booking is confirmed. Background music is available.')
 r=generate(p)
 assert not r.validation.is_valid and len(p.calls)==2
 assert 'unsupported_availability_or_confirmation' in r.validation.failure_codes


@pytest.mark.parametrize('attempt',[1,2])
def test_stale_revision_context_or_recipient_from_boundary_never_persists(attempt):
 p=Provider('Music noted.','Background music is available.');calls=[]
 def safety(d):
  calls.append(d)
  return DraftValidationResult(len(calls)!=attempt,('stale_draft_contract',) if len(calls)==attempt else ())
 r=generate(p,validator=safety)
 assert not r.validation.is_valid and len(p.calls)==attempt


def test_nested_contract_mutation_cannot_reach_correction():
 c=audio_contract()
 class Mutating(Provider):
  def generate_client_response(self,c):
   c.contextual_guidance[0].semantic_values['status']='not_supported'
   return super().generate_client_response(c)
 p=Mutating('Music noted.');r=generate(p,c)
 assert not r.validation.is_valid and r.validation.failure_codes==('draft_contract_mutated',)
 assert len(p.calls)==1


def item_plan(value,topic='next_step',role=Role.MUST_COMMUNICATE):
 i=EditorialContentItem('test',topic,'source','test','current_governed',value,role,'test')
 return EditorialContentPlan('test',(),(i,),3,'test')


@pytest.mark.parametrize('role',[Role.ACKNOWLEDGE,Role.HELPFUL_NOW,Role.DEFER,Role.INTERNAL_ONLY,Role.ALREADY_COMMUNICATED])
def test_nonrequired_roles_do_not_become_hard_obligations(role):
 assert requirements(item_plan({'client_fact':{'background_music_playback':True}},'audio_playback',role))==()


@pytest.mark.parametrize('topic,value,good,bad',[
 ('commercial',{'booking_fee':'EUR 75 excl. VAT','vat':'21%'},'The booking fee is EUR 75 excl. VAT, with VAT at 21%.','I will check the fee. The caterer charges EUR 75.'),
 ('commercial',{'booking_fee':'EUR 75 excl. VAT','vat':'21%'},'The booking fee is EUR 75 excluding VAT. VAT is 21%.','The booking fee is EUR 75.'),
 ('microphones',{'status':'not_supported'},'Microphones are not available from WNC.','Microphones noted. Projectors are not available.'),
 ('commercial_next_step',{'request':'booking fee adjustment','status':'check_required'},"I'll check what adjustment can be arranged for the fee.",'The adjustment is noted.'),
 ('next_step',{'action':'check','subjects':['requested facilitator availability and format']},"I'll check the facilitator availability and format.",'The facilitator is noted.'),
 ('next_step',{'action':'check','subjects':['loading route','venue handover']},"I'll check the loading route and venue handover.","I'll check the loading route."),
 ('client_information',{'question':'What day, start time and finish time would you like?'},'What day, start time and finish time would you like?','What day and start time would you like?'),
 ('client_information',{'question':'How many guests are expected?'},'How many people will attend?','I have noted the guests. What date would you like?'),
 ('projection_display',{'status':'conditional','check_required':['practical projection setup']},"I'll check the practical projector setup.",'I have noted the slides.'),
])
def test_typed_required_answers(topic,value,good,bad):
 p=item_plan(value,topic,Role.MUST_ASK if topic=='client_information' else Role.MUST_COMMUNICATE)
 assert validate_required_realization(p,good)[0]['realized']
 assert not validate_required_realization(p,bad)[0]['realized']


def test_unknown_required_shape_fails_closed():
 p=item_plan({'unexpected_fact':True},'unknown')
 assert not validate_required_realization(p,'Thanks for your request.')[0]['realized']


def test_valid_audio_realization_suppresses_turns_two_three_unless_reopened():
 c=audio_contract();p=Provider('Music noted.','Background music is available.')
 r=generate(p,c)
 second=followup(c,'We now expect 24 people.',r.draft.body)
 assert next(i for i in second.editorial_plan.items if i.topic=='audio_playback').role==Role.ALREADY_COMMUNICATED
 assert not any(v.get('topic')=='audio_playback' for v in second.to_provider_payload()['must_say'])
 third=replace(second,latest_client_message='21 January from 17:00 to 21:00',prior_client_messages=(c.latest_client_message,second.latest_client_message))
 assert next(i for i in third.editorial_plan.items if i.topic=='audio_playback').role==Role.ALREADY_COMMUNICATED
 assert not any(v.get('topic')=='audio_playback' for v in third.to_provider_payload()['must_say'])
 reopened=replace(third,latest_client_message='Can we play background music?')
 assert next(i for i in reopened.editorial_plan.items if i.topic=='audio_playback').role==Role.MUST_COMMUNICATE


def test_transport_correction_keeps_exact_payload_model_intent_and_no_tools():
 requests=[]
 def transport(payload,url,headers,timeout,ssl_context):
  requests.append(payload)
  body='Music noted.' if len(requests)==1 else 'Background music is available.'
  return {'id':'response','status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':json.dumps({'subject':'Subject','body':body,'question_ids':[]})}]}]},{}
 p=OpenAIClientResponseProvider(api_key='test',model_code='unchanged',transport=transport)
 r=generate(p)
 assert r.validation.is_valid and len(requests)==2
 assert requests[0]['input']==requests[1]['input'][:2]
 assert requests[0]['model']==requests[1]['model']=='unchanged'
 assert all('tools' not in p for p in requests)
 correction=json.loads(requests[1]['input'][2]['content'])
 assert correction['unmet_items'][0]['semantic_key']=='fact:audio_playback'
 assert correction['correction_reason']=='required_semantic_items_not_realized'


def make_service(monkeypatch,bodies):
 from tools.phase_08_workflow.tests.test_test_console_service import _GovernedClientResponseLifecycleService
 from tools.phase_08_workflow.tests.test_inquiry_intake import make_case
 from tools.phase_08_workflow.tests.test_test_console_service import WorkflowOrchestrationCaseSnapshot
 service=_GovernedClientResponseLifecycleService(snapshot=WorkflowOrchestrationCaseSnapshot(rental_case=make_case()),calls=[])
 service._require_case_snapshot=lambda cid:service.snapshot
 service._current_client_policy_guidance=lambda *args: (guide('audio_playback',status='supported'),)
 c=replace(audio_contract(),source_case_revision=service.snapshot.rental_case.case_revision);monkeypatch.setattr('tools.phase_08_workflow.test_console_service.build_draft_contract',lambda **kw:c)
 provider=Provider(*bodies);service.client_response_provider=provider
 events=[];service._create_console_event=lambda **kw:events.append(kw)
 return service,provider,events


def test_only_accepted_candidate_persists_and_gets_approval(monkeypatch):
 service,p,events=make_service(monkeypatch,['Music noted.','Background music is available.'])
 persisted=[]
 original=service._create_draft_revision
 def persist(**kw):
  assert len(p.calls)==2 and 'approval_created' not in service.calls
  persisted.append(kw);return original(**kw)
 service._create_draft_revision=persist
 r=service.generate_governed_client_response_draft(rental_case_id=1)
 assert r.success and len(persisted)==1 and len(events)==1
 assert persisted[0]['content'].body_text_override=='Background music is available.'
 assert service.calls.count('approval_created')==1
 assert events[0]['structured_payload']['generation_audit']['corrective_retry_count']==1
 assert [x['semantic_key'] for x in events[0]['structured_payload']['communicated_editorial_items']]==['fact:audio_playback']


def test_two_omissions_leave_no_current_revision_or_approval(monkeypatch):
 from tools.phase_08_workflow.test_console_service import TestConsoleError
 service,p,events=make_service(monkeypatch,['Music noted.','Music is part of the plan.'])
 with pytest.raises(TestConsoleError):service.generate_governed_client_response_draft(rental_case_id=1)
 assert 'draft_persisted' not in service.calls and 'approval_created' not in service.calls
 assert len(events)==1 and events[0]['event_type_code']=='governed_client_response_draft_rejected'
 assert len(events[0]['structured_payload']['generation_audit']['attempts'])==2


def test_recipient_change_is_safety_failure_no_correction(monkeypatch):
 from tools.phase_08_workflow.test_console_service import TestConsoleError
 service,p,events=make_service(monkeypatch,['Music noted.'])
 original=service._load_test_case_metadata;count=[]
 def metadata(cid):
  count.append(cid);v=original(cid)
  return replace(v,contact_email='changed@example.test') if len(count)>1 else v
 service._load_test_case_metadata=metadata
 with pytest.raises(TestConsoleError):service.generate_governed_client_response_draft(rental_case_id=1)
 assert len(p.calls)==1 and 'draft_persisted' not in service.calls
 assert events[0]['structured_payload']['validation_codes']==['stale_draft_contract']


def test_provider_failure_on_correction_preserves_first_candidate_hash_and_no_persistence(monkeypatch):
 from tools.phase_08_workflow.test_console_service import TestConsoleError
 service,p,events=make_service(monkeypatch,['Music noted.'])
 def timeout(*args):raise TimeoutError()
 p.correct_client_response=timeout
 with pytest.raises(TestConsoleError) as error:service.generate_governed_client_response_draft(rental_case_id=1)
 assert error.value.diagnostics['generation_audit']['initial_candidate_hash']
 assert error.value.diagnostics['generation_audit']['failed_provider_attempt']==2
 assert 'draft_persisted' not in service.calls and 'approval_created' not in service.calls
 assert events[0]['event_type_code']=='governed_client_response_generation_failed'


def test_same_accepted_content_reuses_existing_exact_revision(monkeypatch):
 from tools.phase_08_workflow.outlook_action_contract import CONTRACT_VERSION
 service,p,events=make_service(monkeypatch,['Music noted.','Background music is available.','Music noted.','Background music is available.'])
 assert service.generate_governed_client_response_draft(rental_case_id=1).success
 service._ensure_governed_client_response_action=lambda *args,**kw:SimpleNamespace(workflow_action_id=1,structured_payload={'contract_version':CONTRACT_VERSION,'draft_revision_id':101})
 assert service.generate_governed_client_response_draft(rental_case_id=1).success
 assert service.calls.count('draft_persisted')==1 and service.calls.count('approval_created')==1
 assert len(events)==2 and events[-1]['event_type_code']=='governed_client_response_draft_reused'


def test_new_inbound_event_during_generation_stops_correction(monkeypatch):
 from tools.phase_08_workflow.test_console_service import TestConsoleError
 service,p,events=make_service(monkeypatch,['Music noted.'])
 service._require_case_snapshot=lambda cid:replace(service.snapshot,workflow_events=(SimpleNamespace(workflow_event_id=123),))
 with pytest.raises(TestConsoleError):service.generate_governed_client_response_draft(rental_case_id=1)
 assert len(p.calls)==1 and 'draft_persisted' not in service.calls
 assert events[0]['structured_payload']['validation_codes']==['stale_draft_contract']
