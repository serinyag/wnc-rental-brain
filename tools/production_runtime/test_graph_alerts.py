import copy,json
import pytest
from dataclasses import replace
from .test_production import production
from .graph_alerts import GraphAlerts,CLIENT,TENANT,MAILBOX,RECIPIENT,AlertOutcomeAmbiguous


def configured(production):
    c,_,_=production;m=copy.deepcopy(c.manifest)
    m['outlook'].update(client_id=CLIENT,tenant_id=TENANT,mailbox=MAILBOX)
    m['alerting'].update(transport='graph_mail_alert_v1',recipient=RECIPIENT)
    return replace(c,manifest=m)


def test_alert_recipient_is_fixed_and_content_is_minimal(production):
    c=configured(production);calls=[]
    def request(method,url,headers,data):
        calls.append((method,url,headers,data))
        if '/token' in url:return 200,json.dumps({'access_token':'fake-access-token','expires_in':3600}).encode()
        return 202,b''
    alert=GraphAlerts(c,secret='fake-secret',requester=request)
    event={'deployment_id':c.manifest['deployment_id'],'code':'SYNTHETIC_VERIFICATION',
           'timestamp':100,'case_id':None,'actor':None}
    receipt=alert.send(event,'0'*64)
    mail=json.loads(calls[1][3])
    assert mail['message']['toRecipients']==[{'emailAddress':{'address':RECIPIENT}}]
    assert 'SAFE SYNTHETIC' in mail['message']['subject']
    assert 'case_id' not in mail['message']['body']['content']
    assert receipt['http_status']==202 and receipt['receipt_confirmed'] is False
    assert all(method=='POST' for method,_,_,_ in calls)


def test_wrong_scope_rejected_before_any_request(production):
    c=configured(production);c.manifest['alerting']['recipient']='other@example.test'
    with pytest.raises(ValueError):
        GraphAlerts(c,secret='fake',requester=lambda *_:pytest.fail('network reached'))


def test_ambiguous_http_outcome_is_not_retried(production):
    c=configured(production);calls=[]
    def request(method,url,headers,data):
        calls.append(url)
        if '/token' in url:return 200,b'{"access_token":"fake-access-token","expires_in":3600}'
        return 503,b''
    alert=GraphAlerts(c,secret='fake-secret',requester=request)
    with pytest.raises(AlertOutcomeAmbiguous):alert.send(
        {'deployment_id':c.manifest['deployment_id'],'code':'SYNTHETIC_VERIFICATION',
         'timestamp':100,'case_id':None,'actor':None},'0'*64)
    assert len(calls)==2
