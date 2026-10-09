"""Existing Phase 7 assemblers and Phase 8 consumer, pinned staging DB I/O."""
from common import *
from dataclasses import asdict
from unittest.mock import patch
from tools.phase_07_reasoning.context_assembler import build_context_package
from tools.phase_07_reasoning.phase4_adapter import execute_phase4_plan
from tools.phase_07_reasoning.phase5_wrapper import execute_phase5_plan
from tools.phase_07_reasoning.phase6_adapter import execute_phase6_plan
from tools.phase_08_workflow.phase7_workflow_consumer import consume_phase7_context
from tools.phase_08_workflow.phase7_consumption_repository import SupabasePhase7ConsumptionRepository
from tools.phase_08_workflow.context_aware_drafting import derive_resolution_items
query='Current Studio space capacity and projection display requirements for a team workshop for 24 guests, 12 November 2026 14:00 to 18:00 Europe/Amsterdam, with an external caterer. What operational checks and supplier guidance apply? Relevant historical precedent is context only; current authority takes priority.'
assert not (OUT/'reasoning_initial.json').exists()
with connect() as c:
 runner=connection_runner(c)
 def rows(sql):return runner(sql,expect_json=True)['rows']
 # Database adapters use the same existing query interfaces, pinned to staging.
 with patch('tools.phase_06_search.historical_retrieval.run_supabase_query',runner),patch('tools.phase_05_search.search_hybrid.run_supabase_query',runner):
  context=build_context_package(query,
   phase4_executor=lambda plan,**kw:execute_phase4_plan(plan,query_runner=rows,**kw),
   phase5_executor=lambda plan,**kw:execute_phase5_plan(plan,query_runner=rows,**kw),
   phase6_executor=execute_phase6_plan)
 s=service(c);rev=s._require_case_snapshot(586).rental_case.case_revision
 result=consume_phase7_context(rental_case_id=586,expected_case_revision=rev,reasoning_purpose='feasibility_review',context_package=context,repository=SupabasePhase7ConsumptionRepository(query_runner=runner))
 assert not result.failure_codes,result
 reconciled=s.run_reconciliation(rental_case_id=586);assert reconciled.success,reconciled
 detail=s.load_case_detail(586);items=derive_resolution_items(detail.orchestration_snapshot,observed_fields=s._build_observed_field_candidates(detail.evidence_bundles))
 s._ensure_resolution_workflow_actions(detail.orchestration_snapshot,items)
 output={'context':asdict(context),'consumption':asdict(result),'reconciliation':asdict(reconciled),'resolution_items':[x.to_payload() for x in items]}
save('reasoning_initial',output)
print(json.dumps({'layers':[{'id':r.layer_id,'state':r.execution_state,'count':r.result_count} for r in context.layer_execution],'consumption':str(result),'resolutions':[x.to_payload() for x in items]},indent=2))
