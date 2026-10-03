"""Offline audit of fresh provider-free case snapshots and saved request logs."""
import json,sys
from pathlib import Path
from collections import Counter
p=Path(__file__).resolve().parent;slug=sys.argv[1]
load=lambda name:json.loads((p/name).read_text())
state=load(f'{slug}_final_snapshots.json');rows=[];rejections=[]
for entry in state['cases']:
 c=entry['snapshot']['case'];o=c['orchestration_snapshot'];case=o['rental_case']
 assert not o['execution_attempts']
 counts=Counter(a['structured_payload'].get('resolution_item_key') for a in o['workflow_actions'] if a['status'] not in ['superseded','cancelled','failed'] and a['structured_payload'].get('resolution_item_key'))
 assert all(n==1 for n in counts.values())
 for t in c['simulated_outlook_threads']:
  r=t['current_revision']
  if r is None:continue
  assert r['is_current'] and r['source_case_revision']==case['case_revision']
  assert t['current_display_status']=='needs_approval' and not t['can_simulate_send']
  assert t['workflow_action_status']=='awaiting_approval'
  rows.append({'scenario_id':entry['scenario_id'],'case_id':case['rental_case_id'],'revision_id':r['inquiry_response_draft_revision_id'],'source_case_revision_matches':True,'display_status':t['current_display_status'],'send_available':False,'blocking_operator_annotations':t['approval_blocked_by_operator_annotations'],'duplicate_active_resolution_actions':0,'execution_attempts':0})
 for event in o.get('workflow_events',[]):
  if event['event_type_code']=='governed_client_response_draft_rejected':rejections.append(event)
for run in [slug]:
 if not (p/f'{run}_results.json').exists():continue
 result=load(f'{run}_results.json')
 for x in result['request_log']:
  assert '/approve' not in x['path'] and '/execute' not in x['path']
 for case in result['results']:assert not case.get('final_execution_attempts')
assert state['health']['environment']=='staging' and state['health']['status']=='ok'
assert state['health']['providers']=={'outlook':'configured_draft_only','asana':'configured_but_disabled'}
(p/f'{slug}_integrity_audit.json').write_text(json.dumps({'health':state['health'],'current_drafts':rows,'rejected_candidates':rejections,'approval_and_execution_routes_called':0},indent=2)+'\n')
print(len(rows),'current revisions pass freshness, approval, disabled-send and duplicate checks; rejected candidates',len(rejections))
