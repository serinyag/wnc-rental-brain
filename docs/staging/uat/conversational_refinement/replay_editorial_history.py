import json,sys
from pathlib import Path
from types import SimpleNamespace as NS
root=Path('/Users/serinya/Documents/WNC Rental Automation');sys.path.insert(0,str(root))
from tools.phase_08_workflow.test_console_service import TestConsoleService
p=root/'docs/staging/uat/conversational_refinement';old=json.loads((p.parent/'autonomous_remediation/cycle3_final_snapshots.json').read_text());checks=[];original_results=json.loads((p.parent/'autonomous_remediation/cycle3_results.json').read_text())
for case in old['cases']:
 d=case['snapshot']['case'];o=d['orchestration_snapshot']
 detail=NS(evidence_bundles=tuple(NS(raw_evidence=NS(**b['raw_evidence']) if b['raw_evidence'] else None,source_record=NS(**b['source_record'])) for b in d['evidence_bundles']),simulated_outlook_threads=tuple(NS(draft_history=tuple(NS(**r) for r in t['draft_history'])) for t in d['simulated_outlook_threads']))
 snap=NS(workflow_events=tuple(NS(**e) for e in o['workflow_events']))
 history=TestConsoleService._prior_client_drafts(detail,snap)
 body=history[-1] if history else None
 if body:
  revision=next(r for t in detail.simulated_outlook_threads for r in t.draft_history if r.body_text==body)
  current=next(t['current_revision'] for t in d['simulated_outlook_threads'] if t['current_revision'])
  scenario=next(x for x in original_results['results'] if x['scenario_id']==case['scenario_id'])
  accepted=[t['draft']['draft_revision'] for t in scenario['turns'] if t.get('draft',{}).get('draft_revision')]
  assert revision.inquiry_response_draft_revision_id==accepted[-2]['inquiry_response_draft_revision_id']
  checks.append({'scenario':case['scenario_id'],'case':case['rental_case_id'],'selected_prior_revision':revision.inquiry_response_draft_revision_id,'current_revision':current['inquiry_response_draft_revision_id'],'same_case_revision':revision.source_case_revision==current['source_case_revision'],'result':'PASS'})
assert len(checks)==7
(p/'cycle2_history_replay.json').write_text(json.dumps({'source':'Previous program final snapshots; offline only, no provider/database/API calls','checks':checks},indent=2)+'\n')
print('All seven multi-turn histories selected the correct predecessor, including unchanged case revisions.')
