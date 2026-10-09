"""Operator extraction of explicit original client claims; existing source/governance."""
from common import *
from datetime import datetime,timezone
from tools.phase_08_workflow.observations import _ingest_one_candidate
from tools.phase_08_workflow.observation_types import StructuredObservationCandidate,CaseAssociationResult
from tools.phase_08_workflow.inquiry_intake import apply_inquiry_intake
from tools.phase_08_workflow.context_aware_drafting import derive_resolution_items
from unittest.mock import patch
assert not (OUT/'original_claims_intake.json').exists()
with connect() as c,patch('urllib.request.urlopen',side_effect=AssertionError('No providers during intake')):
 s=service(c);r=s.observation_repository
 source=next(x for x in r.list_source_records_for_case(586) if x.inbound_source_record_id==3104)
 raw=c.execute('select envelope from public.outlook_inbound_messages where source_record_id=3104 and rental_case_id=586').fetchone()[0]
 assert 'Studio team workshop for 24 guests' in raw['normalized_body'] and 'external caterer' in raw['normalized_body'] and 'basic projection' in raw['normalized_body']
 now=datetime.now(timezone.utc).isoformat();results=[]
 for field,value in [('guest_count',24),('requested_rental_scope','studio_space'),('event_type','team_workshop'),('catering_arrangement','client_external_caterer'),('technical_requirements',['projection_display'])]:
  o=_ingest_one_candidate(candidate=StructuredObservationCandidate(reported_field_code=field,observation_type='fact_candidate',claim_kind='new_information',candidate_value_payload=value,source_evidence_reference='outlook_message:'+raw['provider_message_id'],asserted_by_party_type='client',asserted_by_reference=raw['from_address'],source_excerpt=raw['normalized_body'][:500],extraction_confidence=1.0),source_record=source,case_association=CaseAssociationResult(status='resolved',rental_case_id=586,association_basis='exact_provider_conversation'),case_snapshot=r.load_case_snapshot(586),repository=r,created_at=now)
  assert o.observation.status=='validated';results.append({'field':field,'observation_id':o.observation.inbound_observation_id,'disposition':o.effect.disposition_code})
 intake=apply_inquiry_intake(r,rental_case_id=586,actor_type='operator',actor_reference='synthetic_integration:operator_extraction_of_source_3104',now=lambda:now)
 assert not intake.failure_codes
 detail=s.load_case_detail(586)
 result={'observations':results,'case_revision':detail.orchestration_snapshot.rental_case.case_revision,'intake':str(intake),'resolution_items':[x.to_payload() for x in derive_resolution_items(detail.orchestration_snapshot,observed_fields=s._build_observed_field_candidates(detail.evidence_bundles))]}
save('original_claims_intake',result);print(json.dumps(result,indent=2))
