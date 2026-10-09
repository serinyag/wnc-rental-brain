"""Read-only, in-memory boundary proof using current case; no provider/state edits."""
from common import *
from dataclasses import replace,asdict
from tools.phase_08_workflow.context_aware_drafting import derive_resolution_items,with_workflow_actions
from tools.phase_08_workflow.observation_registry import OBSERVATION_FIELD_DEFINITIONS
from tools.phase_08_workflow.governed_client_response import build_draft_contract
with connect() as c:
 c.execute('set transaction read only')
 s=service(c);d=s.load_case_detail(586);snap=d.orchestration_snapshot
 items=derive_resolution_items(snap,observed_fields=s._build_observed_field_candidates(d.evidence_bundles))
 completed=tuple(replace(a,structured_payload={**a.structured_payload,'resolution_status':'RESOLVED'}) for a in snap.workflow_actions if a.structured_payload.get('resolution_item_key'))
 hypothetical=with_workflow_actions(items,completed)
 assert hypothetical and all(x.resolution_status!='RESOLVED' for x in hypothetical)
 fields={f.field_code:f.canonical_target_reference for f in OBSERVATION_FIELD_DEFINITIONS}
 assert not any(f in fields for f in ('venue_availability','venue_availability_confirmation','technical_setup_confirmation','operational_resolution'))
 # Verify closed component lineages without executing any component tests/providers.
 baselines=json.loads((ROOT/'docs/staging/outlook_reconciled_closure/raw_after.json').read_text());baselines['585']=json.loads((ROOT/'docs/staging/outlook_inbound/protected_asana_before.json').read_text())
 for cid,tables in baselines.items():
  for table,expected in tables.items():
   actual=c.execute(f"select coalesce(json_agg(row_to_json(r) order by r.id),'[]') from public.{table} r where rental_case_id=%s",(int(cid),)).fetchone()[0]
   assert actual==expected,(cid,table)
 messages=c.execute('select message_id,conversation_id,source_record_id,source_hash from public.outlook_inbound_messages order by retrieved_at').fetchall()
 sources=c.execute('select count(*) from public.inbound_source_records where resolved_rental_case_id=586').fetchone()[0]
 assert len(messages)==sources==2
 result={'case_revision':snap.rental_case.case_revision,'actual_resolution_items':[x.to_payload() for x in items],
 'hypothetical_resolved_actions_still_pending':[x.to_payload() for x in hypothetical],
 'observation_registry_fields':fields,'workflow_actions':[asdict(a) for a in snap.workflow_actions],
 'current_facts':[asdict(f) for f in snap.rental_case_facts],
 'inbound_bindings':messages,'inbound_source_count':sources,'protected_cases_unchanged':[424,584,585],
 'decision':'Governed operational resolution admission and consumption are missing; no provider mutation performed.'}
save('resolution_boundary_audit',result)
print(json.dumps({'case_revision':result['case_revision'],'actions':[(a.workflow_action_id,a.structured_payload.get('summary')) for a in snap.workflow_actions],'proof':result['hypothetical_resolved_actions_still_pending']},indent=2))
