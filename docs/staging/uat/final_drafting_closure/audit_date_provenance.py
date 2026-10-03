"""Provider-free provenance and client-question audit of the frozen run."""
from pathlib import Path
import json,re,sys
root=Path('/Users/serinya/Documents/WNC Rental Automation');sys.path.insert(0,str(root))
from tools.phase_08_workflow.date_normalization import resolve_calendar_date,timing_components
p=Path(__file__).resolve().parent
state=json.loads((p/'acceptance_final_snapshots.json').read_text());rows=[]
for case in state['cases']:
 for bundle in case['snapshot']['case']['evidence_bundles']:
  source=bundle['source_record']
  for observation in bundle['observations']:
   value=observation['candidate_value_payload']
   if observation['reported_field_code']!='active_event_window' or not isinstance(value,dict):continue
   provenance=value.get('date_provenance');assert provenance,observation
   assert provenance['reference_timestamp']==source['received_at'] or provenance.get('timing_update_source_reference')
   if value.get('resolved_date'):
    day,month=value['day'],value['month'];year=provenance['explicit_client_year']
    resolved,expected=resolve_calendar_date(day=day,month=month,year=year,reference_timestamp=provenance['reference_timestamp'])
    assert str(resolved)==value['resolved_date']
    assert provenance['year_source']==expected['year_source']
    if year is None:assert 'year' not in value
   rows.append({'scenario_id':case['scenario_id'],'observation_id':observation['inbound_observation_id'],
                'status':observation['status'],'value':value,'source_received_at':source['received_at'],'provenance_validation':'PASS'})
r=json.loads((p/'acceptance_results.json').read_text());questions=[]
for case in r['results']:
 for turn in case['turns']:
  d=turn.get('draft',{}).get('draft_revision')
  if not d:continue
  body=d['body_text']
  asks_year=bool(re.search(r'\b(?:which|what)\s+year\b|including (?:the )?year|\byear\b[^.!?\n]{0,40}\?',body,re.I))
  questions.append({'turn':f"{case['scenario_id']}/{turn['turn_number']}",'asks_client_for_year':asks_year})
assert rows and not any(q['asks_client_for_year'] for q in questions)
(p/'acceptance_date_provenance.json').write_text(json.dumps({'provider_calls':0,'observations':rows,'draft_question_checks':questions},indent=2)+'\n')
print(len(rows),'timing observations pass provenance checks;',len(questions),'drafts do not ask for year.')
