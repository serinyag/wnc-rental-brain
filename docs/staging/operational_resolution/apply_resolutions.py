"""Two explicitly authorized synthetic operational results via authenticated API."""
from staging import *
c=client()
before=json.loads((OUT/'before.json').read_text())
for aid,outcomes in ((1634,{'studio_space':'AVAILABLE'}),(1633,{'projection_display':'FEASIBLE'})):
    name='resolution_'+str(aid)
    recovering = (OUT/(name+'_started.json')).exists()
    assert not recovering or '--resume-verified-empty' in sys.argv, 'Inspect persisted evidence before attempting recovery'
    detail=c.request('GET','/api/operator/cases/586')['case']
    rev=detail['orchestration_snapshot']['rental_case']['case_revision']
    expected=3 if aid==1634 else 4
    assert rev==expected,(rev,expected)
    submission=dict(workflow_action_id=aid,expected_case_revision=rev,contract=before['contracts'][str(aid)],
        outcomes=outcomes,evidence_reference=f'staging:case586:authorized-synthetic-operator:{aid}:v1',
        evidence_text='staging synthetic operator evidence: '+(
            'Studio is AVAILABLE for 12 November 2026 14:00–18:00 Europe/Amsterdam only. This does not confirm a booking, capacity, catering, fees or any other date.' if aid==1634 else
            'The specifically requested projection_display setup is FEASIBLE for the Studio team workshop on 12 November 2026 14:00–18:00 Europe/Amsterdam only. No microphone, technician, fee waiver or wider AV approval is confirmed.'),
        occurred_at=(datetime.now(timezone.utc)-timedelta(seconds=2)).isoformat(),
        idempotency_key=f'case586-synthetic-operational-{aid}-v1',synthetic=True)
    if recovering:
        with connect() as conn:
            conn.execute('set transaction read only')
            assert conn.execute("select count(*) from public.workflow_events where rental_case_id=586 and event_type_code='operational_resolution_accepted'").fetchone()[0] == (0 if aid==1634 else 1)
        submission=json.loads((OUT/(name+'_started.json')).read_text())
    else:
        save(name+'_started',submission)
    result=c.request('POST','/api/operator/cases/586/operational-resolutions',submission)
    save(name,result)
    assert result['case_revision']==expected+1 and not result['replayed'],result
    replay=c.request('POST','/api/operator/cases/586/operational-resolutions',submission)
    save(name+'_replay',replay)
    assert replay=={**result,'replayed':True}
    print(json.dumps({'action':aid,'result':result,'replay':replay},indent=2))
