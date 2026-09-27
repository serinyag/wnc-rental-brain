import json,statistics,sys,hashlib
from pathlib import Path
from collections import Counter
p=Path('/Users/serinya/Documents/WNC Rental Automation/docs/staging/uat/autonomous_remediation');slug=sys.argv[1]
d=json.loads((p/f'{slug}_results.json').read_text());reviews=json.loads((p/f'{slug}_reviews.json').read_text());base=json.loads((p/'baseline_assessment.json').read_text());names=list(base['assessments'][0]['scores']);checks=list(base['assessments'][0]['checks'])
audit=json.loads((p/f'{slug}_database_audit.json').read_text());actions=next(b['evidence'] for b in audit if b['kind']=='actions');counts=Counter((a['rental_case_id'],a['structured_payload'].get('resolution_item_key')) for a in actions if a['structured_payload'].get('resolution_item_key') and a['status'] not in {'superseded','cancelled','failed'})
records=[]
for s in d['results']:
 for t in s['turns']:
  r=t.get('draft',{}).get('draft_revision')
  if not r:continue
  a=reviews[f"{s['scenario_id']}/{t['turn_number']}"];grade,values,flags,note=a
  c={name:name in flags for name in checks};c['em_dash']='—' in (r['subject']+r['body_text']);c['stale_draft']=not r['is_current'] or r['source_case_revision']!=t['after_generation']['case_revision'];c['duplicate_internal_work_action']=any(n>1 for (case,key),n in counts.items() if case==s['rental_case_id'])
  records.append({'scenario_id':s['scenario_id'],'turn':t['turn_number'],'content_hash':r['content_hash'],'subject_body_sha256':hashlib.sha256((r['subject']+'\n'+r['body_text']).encode()).hexdigest(),'grade':grade,'scores':dict(zip(names,values)),'checks':c,'reason':note,'clearly_reduces_operator_work':grade in {'A','B'}})
metrics={'scenarios_attempted':len(d['results']),'turns_attempted':sum(len(s['turns']) for s in d['results']),'persisted_drafts':len(records),'turn_coverage_percent':round(100*len(records)/21,2),'grades':dict(Counter(r['grade'] for r in records)),'A_plus_B_percent':round(100*sum(r['grade'] in {'A','B'} for r in records)/len(records),2),'scores':{k:round(statistics.mean(r['scores'][k] for r in records),2) for k in names},'clearly_reduces_operator_work_percent':round(100*sum(r['clearly_reduces_operator_work'] for r in records)/len(records),2),'checks_count':{k:sum(r['checks'][k] for r in records) for k in checks}}
(p/f'{slug}_assessment.json').write_text(json.dumps({'method':base['method'],'metrics':metrics,'assessments':records},indent=2,ensure_ascii=False)+'\n');print(json.dumps(metrics,indent=2))
