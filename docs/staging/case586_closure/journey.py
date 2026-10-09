"""Authorized Case 586 closure steps. Each mutation has an exclusive local receipt.

Provider mutations are executed only by the authenticated staging application.
The local database client is pinned to staging and calls existing governance APIs.
"""
import sys,json
from pathlib import Path
from dataclasses import asdict
from datetime import datetime,timezone,timedelta
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'docs/staging/operational_resolution'))
from staging import connect,service,client,protected
OUT=Path(__file__).parent

def save(name,data):
 with (OUT/(name+'.json')).open('x') as f:json.dump(data,f,indent=2,default=str)

def call(name,path,payload=None):
 save(name+'_started',{'path':path,'at':datetime.now(timezone.utc).isoformat()})
 result=client().request('POST',path,{} if payload is None else payload)
 save(name,result);print(json.dumps(result.get('report',result),indent=2)[:5000]);return result

if __name__=='__main__':
 mode=sys.argv[1]
 if mode=='reply':
  h=client().get_health();assert h['environment']=='staging' and h['application']['metrics']['outlook_inbound_gate']=='enabled'
  call('synthetic_reply','/api/operator/cases/586/synthetic-layout-reply')
 elif mode.startswith('sync'):
  call(mode,'/api/operator/outlook-inbound/sync')
 elif mode=='layout':
  from tools.phase_08_workflow.staging_layout_reply import BODY
  from tools.phase_08_workflow.observations import _ingest_one_candidate
  from tools.phase_08_workflow.observation_types import StructuredObservationCandidate,CaseAssociationResult
  from tools.phase_08_workflow.orchestration_runtime import apply_case_fact_mutation
  from tools.phase_08_workflow.orchestration_types import CaseFactMutationRequest
  save('layout_started',{'at':datetime.now(timezone.utc).isoformat()})
  with connect() as c:
   protected(c);s=service(c);r=s.observation_repository
   rows=c.execute("select source_record_id,envelope,source_hash from public.outlook_inbound_messages where rental_case_id=586 and envelope->>'normalized_body' like %s",('%'+BODY.split('\n')[0]+'%',)).fetchall()
   assert len(rows)==1,rows
   sid,env,source_hash=rows[0];assert BODY in env['normalized_body']
   source=next(x for x in r.list_source_records_for_case(586) if x.inbound_source_record_id==sid)
   assert s._require_case_snapshot(586).rental_case.case_revision==5
   now=datetime.now(timezone.utc).isoformat();value={'configuration_type':'seated','style':'theatre'}
   candidate=StructuredObservationCandidate(reported_field_code='layout_requirements',observation_type='fact_candidate',claim_kind='new_information',
    candidate_value_payload=value,source_evidence_reference='outlook_message:'+env['provider_message_id'],asserted_by_party_type='client',
    asserted_by_reference=env['from_address'],source_excerpt=BODY,extraction_confidence=1.0)
   o=_ingest_one_candidate(candidate=candidate,source_record=source,case_association=CaseAssociationResult(status='resolved',rental_case_id=586,
    association_basis='exact_provider_conversation'),case_snapshot=r.load_case_snapshot(586),repository=r,created_at=now)
   assert o.observation.status=='validated'
   # Explicit operator validation of the client's preference, never capacity truth.
   result=apply_case_fact_mutation(s.orchestration_repository,CaseFactMutationRequest(rental_case_id=586,expected_case_revision=5,
    field_code='layout_requirements',domain_code='layout',new_value_payload=value,
    source_reference='inbound_observation:'+str(o.observation.inbound_observation_id),
    resolution_basis='Authorized synthetic operator validation of explicit client layout preference from immutable Outlook evidence; not capacity confirmation.',
    actor_reference='authorized_case586_synthetic_operator',actor_type='operator'))
   assert result and result.new_case_revision==6
   data={'source_record_id':sid,'provider_message_id':env['provider_message_id'],'conversation_id':env['provider_conversation_id'],
    'source_hash':source_hash,'observation':asdict(o.observation),'effect':asdict(o.effect),'fact_mutation':asdict(result),'value':value}
  save('layout',data);print(json.dumps(data,indent=2))
 elif mode=='capacity':
  from tools.phase_08_workflow.operational_resolution import obligation
  with connect() as c:
   c.execute('set transaction read only');s=service(c);d=s.load_case_detail(586);snap=d.orchestration_snapshot
   assert snap.rental_case.case_revision==6
   action=next(a for a in snap.workflow_actions if a.workflow_action_id==1632)
   contract=obligation(snap,action,observed_fields=s._build_observed_field_candidates(d.evidence_bundles))
   row=c.execute("select capacity_evaluation_status,within_capacity from api.evaluate_capacity('studio_space',null,'seated',24,current_date)").fetchone()
   assert row and row[1] is True,row
  submission={'workflow_action_id':1632,'expected_case_revision':6,'contract':contract,'outcomes':{'capacity_layout':'FEASIBLE'},
   'evidence_reference':'synthetic:case586:operator:seated24:practical-check:v1',
   'evidence_text':'STAGING SYNTHETIC WNC OPERATOR EVIDENCE — Case 586 only. Independently checked the theatre-style seated configuration for 24 guests in the Studio on 12 November 2026 14:00–18:00 Europe/Amsterdam. Published seated maximum 40 (CAPACITY_STUDIO_SEATED); synthetic practical check confirms 24 chairs, clear access routes and projection sightlines for this workshop. Layout is feasible. No booking, commercial commitment, fee decision or policy exception.',
   'occurred_at':(datetime.now(timezone.utc)-timedelta(seconds=1)).isoformat(),'idempotency_key':'case586:capacity-layout:seated24:v1','synthetic':True}
  save('capacity_submission',submission);result=call('capacity','/api/operator/cases/586/operational-resolutions',submission)
  replay=call('capacity_replay','/api/operator/cases/586/operational-resolutions',submission)
  assert replay.get('replayed') or replay.get('result',{}).get('replayed'),replay
