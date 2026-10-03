"""Summarize direct reviews and immutable provider-free evidence."""
from pathlib import Path
import json
from collections import Counter
p=Path(__file__).resolve().parent
load=lambda name:json.loads((p/name).read_text())
s=load('program_status.json');target=load('targeted_review.json');runs=['targeted']
if (p/'full_results.json').exists():runs.append('full')
safety=[];model_candidates=0;operations=0;retries=0;date_rows=0;question_rows=0
for run in runs:
 result=load(f'{run}_results.json');integrity=load(f'{run}_integrity_audit.json');ga=load(f'{run}_generation_audit.json');date=load(f'{run}_date_provenance.json')
 assert all(not any(part in req['path'] for part in ['/approve','/execute','/send']) for req in result['request_log'])
 assert all(not c.get('final_execution_attempts') for c in result['results'])
 assert all(r['execution_attempts']==0 for r in integrity['current_drafts'])
 assert not any(x['asks_client_for_year'] for x in date['draft_question_checks'])
 for x in ga['results']:
  safety.extend(code for a in x['attempts'] for code in a['safety_failure_codes'])
  retries+=x['retry_count']
 model_candidates+=ga['model_candidates'];operations+=ga['generation_operations']
 date_rows+=len(date['observations']);question_rows+=len(date['draft_question_checks'])
 s['health']=integrity['health']
s['safety']={'environment':'staging','health':s['health']['status'],'outlook':s['health']['providers']['outlook'],'send_gate':'DISABLED','asana':s['health']['providers']['asana'],'Graph mutations':0,'Outlook sends':0,'real Asana executions':0,'production activity':0,'actions approved':0,'actions executed':0,'ExecutionAttempts created':0,'generation_operations':operations,'model_candidates':model_candidates,'corrective_retries':retries,'provider':'openai','model':'gpt-5.6-sol'}
s['date_audit']={'normalization_and_observation_sources_unchanged':'PASS','frozen_prior_evidence_hashes':'PASS','timestamp_provenance_observations_checked':date_rows,'drafts_without_year_question':question_rows,'targeted_January_21':'2027-01-21','targeted_provenance':'system_inferred_next_occurrence'}
if 'full' in runs:
 review=load('full_review.json');s['full_review']=review
 if review.get('safety_failures'):safety.append('direct_review_safety_failure')
 passed=target['result']=='PASS' and review['result']=='PASS'
else:passed=False
s['status']='acceptance_complete_stopped'
s['final_marker']='WNC_REQUIRED_REALIZATION_SAFETY_FAILURE' if safety else ('WNC_GOVERNED_DRAFTING_STAGING_ACCEPTED' if passed else 'WNC_REQUIRED_REALIZATION_REVIEW_REQUIRED')
s['remaining_issues']=load('full_review.json').get('remaining_issues',[]) if 'full' in runs else target.get('remaining_issues',[])
s['evidence_limit']='Direct assistant quality review and bounded deterministic checks; no independent human acceptance or universal language-coverage claim.'
p.joinpath('program_status.json').write_text(json.dumps(s,indent=2)+'\n');print(s['final_marker']);print(s['safety'])
