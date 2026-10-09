from journey import *
mode=sys.argv[1]
if mode=='prepare':
 r=call('asana_final_candidate','/api/operator/cases/586/asana-projection')
 p=r['projection'];assert p['rental_case_id']==586 and p['case_revision']==7
 assert len(p['work'])==3 and all(w['completed'] for w in p['work'])
 assert 'Requested venue / scope: studio space' in p['master']['notes']
 assert {w['key'] for w in p['work']}=={'item:blocker:2384','item:blocker:2385','item:availability:2026-11-12 13:00:00+00:2026-11-12 17:00:00+00'}
elif mode=='execute':
 r=json.loads((OUT/'asana_final_candidate.json').read_text());aid=r['workflow_action_id']
 assert client().get_health()['providers']=={'asana':'configured','outlook':'configured_draft_only'}
 with connect() as c:
  c.execute('set transaction read only');protected(c)
  assert not c.execute('select 1 from public.workflow_execution_attempts where workflow_action_id=%s',(aid,)).fetchone()
 response=call('asana_execution',f'/api/operator/cases/586/actions/{aid}/execute',{'execution_mode':'real'})
 assert response['ok'],'Stop on provider uncertainty; never retry.'
elif mode=='verify':
 aid=json.loads((OUT/'asana_final_candidate.json').read_text())['workflow_action_id']
 observed=call('asana_observation',f'/api/operator/cases/586/actions/{aid}/observe-asana')
 assert observed['status']=='matches_projection'
 replay=call('asana_replay',f'/api/operator/cases/586/actions/{aid}/execute',{'execution_mode':'real'})
 assert replay['report']['failure_codes']==['action_already_succeeded']
 with connect() as c:
  c.execute('set transaction read only')
  attempts=c.execute('select id,status,response_snapshot from public.workflow_execution_attempts where workflow_action_id=%s',(aid,)).fetchall()
  assert len(attempts)==1 and attempts[0][1]=='succeeded'
  bindings=attempts[0][2]['bindings']
  old=c.execute('select response_snapshot from public.workflow_execution_attempts where id=27 and rental_case_id=586').fetchone()[0]['bindings']
  assert {k:v['gid'] for k,v in bindings.items()}=={k:v['gid'] for k,v in old.items()}
  save('asana_binding_proof',{'attempt_id':attempts[0][0],'bindings':bindings,'prior_bindings':old,'stable':True})
