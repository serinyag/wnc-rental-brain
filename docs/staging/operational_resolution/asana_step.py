"""One bounded canonical Case586 projection operation; never automatic retries."""
from staging import *
mode=sys.argv[1];c=client()
if mode.startswith('prepare_'):
    name=mode.removeprefix('prepare_')
    response=c.request('POST','/api/operator/cases/586/asana-projection',{})
    save(name+'_candidate',response)
    print(json.dumps(response,indent=2))
elif mode.startswith('execute_'):
    name=mode.removeprefix('execute_')
    candidate=json.loads((OUT/(name+'_candidate.json')).read_text());aid=candidate['workflow_action_id']
    health=c.get_health()
    assert health['environment']=='staging' and health['providers']=={'asana':'configured','outlook':'configured_draft_only'}
    assert health['application']['metrics']['outlook_inbound_gate']=='disabled'
    with connect() as conn:
        conn.execute('set transaction read only');protected(conn)
        actual=conn.execute('select structured_payload,status from public.workflow_actions where id=%s and rental_case_id=586',(aid,)).fetchone()
        assert actual[0]['projection']==candidate['projection'] and actual[1]=='ready_to_execute'
        assert not conn.execute('select 1 from public.workflow_execution_attempts where workflow_action_id=%s',(aid,)).fetchone()
    save(name+'_execution_started',{'action':aid,'case':586,'at':datetime.now(timezone.utc).isoformat()})
    response=c.execute_action(rental_case_id=586,workflow_action_id=aid,execution_mode='real')
    save(name+'_execution',response)
    print(json.dumps({'ok':response.get('ok'),'report':response.get('report')},indent=2))
    assert response['ok'], 'STOP: inspect provider outcome; do not retry'
elif mode.startswith('verify_'):
    name=mode.removeprefix('verify_')
    aid=json.loads((OUT/(name+'_candidate.json')).read_text())['workflow_action_id']
    observed=c.request('POST',f'/api/operator/cases/586/actions/{aid}/observe-asana',{})
    save(name+'_observation',observed)
    assert observed['status']=='matches_projection',observed
    replay=c.execute_action(rental_case_id=586,workflow_action_id=aid,execution_mode='real')
    save(name+'_replay',replay)
    assert replay['ok'] or replay['report']['failure_codes']==['action_already_succeeded']
    with connect() as conn:
        attempts=conn.execute('select id,status from public.workflow_execution_attempts where workflow_action_id=%s',(aid,)).fetchall()
        assert len(attempts)==1 and attempts[0][1]=='succeeded',attempts
    print(json.dumps({'observation':observed['status'],'attempts':attempts,'replay':replay.get('report')},indent=2))
