import copy, hashlib, io, json, os, time
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import patch
import jwt, pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from tools.production_runtime.config import ProductionContract, ProductionConfigurationError, LANES
from tools.production_runtime.auth import EntraVerifier, Principal, CURRENT
from tools.production_runtime.privacy import CATEGORIES
from tools.production_runtime.alerts import atomic_json
ROOT=Path(__file__).resolve().parents[2]

@pytest.fixture
def production(tmp_path,monkeypatch):
    tenant,client,oid=str(uuid4()),str(uuid4()),str(uuid4())
    m={'environment':'production','deployment_id':str(uuid4()),'render_service_id':'srv-fake-production',
       'application_origin':'https://pilot.example.test',
       'database':{'project_ref':'abcdefghijklmnopqrst','pooler_host':'aws-0-eu-central-1.pooler.supabase.com'},
       'outlook':{'tenant_id':tenant,'client_id':str(uuid4()),'staging_client_id':str(uuid4()),'mailbox':'rental@example.test',
                  'exchange_scope':'one-mailbox','allowed_recipients':['client@example.test'],'allowed_senders':['client@example.test'],'sender_roles':{'client@example.test':'client'},'since':'2026-10-09T00:00:00Z'},
       'asana':{'workspace_gid':'100000000001','project_gid':'100000000002'},
       'auth':{'tenant_id':tenant,'audience':str(uuid4()),'authorized_client_ids':[client]},
       'alerting':{'owner':'test-on-call','destination':'https://alerts.example.test/incoming','spool_path':str(tmp_path/'alerts'),'lifecycle_spool_path':str(tmp_path/'privacy')},
       'baseline':{'corpus_hash':'0'*64,'version':'test-baseline','files':{'pyproject.toml':hashlib.sha256((ROOT/'pyproject.toml').read_bytes()).hexdigest()}},
       'model':{'provider':'openai','model':'gpt-5.6-sol','timeout_seconds':60},
       'privacy':{'approved_by':'test-policy-owner','policy_version':'test-only','retention_days':{k:30 for k in CATEGORIES}},
       'backup':{'owner':'test-restore-owner'}}
    control=tmp_path/'controls.json';operators=tmp_path/'operators.json';manifest=tmp_path/'manifest.json'
    atomic_json(control,{'deployment_id':m['deployment_id'],'lanes':{k:False for k in LANES},'lease_expires':0})
    atomic_json(operators,{'deployment_id':m['deployment_id'],'operators':{oid:{'enabled':True,'name':'Test Operator','roles':['OPERATOR','APPROVER']}}})
    atomic_json(manifest,m)
    values={'APP_ENV':'production','RENDER_SERVICE_ID':m['render_service_id'],
       'DATABASE_URL':'postgresql://postgres:fake@db.abcdefghijklmnopqrst.supabase.co:5432/postgres?sslmode=verify-full',
       'WNC_PRODUCTION_MANIFEST':str(manifest),'WNC_PRODUCTION_CONTROLS':str(control),'WNC_PRODUCTION_OPERATORS':str(operators)}
    for key in ['PRODUCTION_MICROSOFT_CLIENT_SECRET','PRODUCTION_ASANA_ACCESS_TOKEN','PRODUCTION_OPENAI_API_KEY','PRODUCTION_ALERT_TOKEN']:values[key]='fake-never-used'
    for key,value in values.items():monkeypatch.setenv(key,value)
    contract=ProductionContract.from_env();contract.validate(os.environ,initial=True)
    return contract,Principal(tenant,oid,frozenset({'OPERATOR','APPROVER'})),values

@pytest.mark.parametrize('field',['project','mailbox','service','asana'])
def test_staging_identity_refused(production,field):
    from tools.production_runtime.config import STAGING
    c,p,env=production;m=copy.deepcopy(c.manifest)
    if field=='project':m['database']['project_ref']=STAGING['project']
    if field=='mailbox':m['outlook']['mailbox']=STAGING['mailbox']
    if field=='service':m['render_service_id']=STAGING['service']
    if field=='asana':m['asana']['project_gid']=STAGING['asana_project']
    with pytest.raises(ProductionConfigurationError):replace(c,manifest=m).validate(env)

@pytest.mark.parametrize('key',['DATABASE_URL','PRODUCTION_MICROSOFT_CLIENT_SECRET','RENDER_SERVICE_ID'])
def test_missing_configuration_refused(production,key):
    c,p,env=production
    with pytest.raises(ProductionConfigurationError):c.validate({k:v for k,v in env.items() if k!=key})

def test_graph_alert_transport_uses_scoped_mail_identity(production):
    from tools.production_runtime.graph_alerts import TENANT,CLIENT,MAILBOX,RECIPIENT
    c,_,env=production;m=copy.deepcopy(c.manifest)
    m['outlook'].update(tenant_id=TENANT,client_id=CLIENT,mailbox=MAILBOX)
    m['alerting'].update(transport='graph_mail_alert_v1',recipient=RECIPIENT,
        destination='https://graph.microsoft.com/v1.0/users/booking%40whennaturecalls.nl/sendMail')
    scoped=replace(c,manifest=m)
    scoped.validate({k:v for k,v in env.items() if k!='PRODUCTION_ALERT_TOKEN'})
    m['alerting']['recipient']='other@example.test'
    with pytest.raises(ProductionConfigurationError):scoped.validate(env)

@pytest.mark.parametrize('limit',[0,26,-1,True])
def test_alert_dispatch_requires_bounded_batch(production,limit):
    from tools.production_runtime.alerts import dispatch
    with pytest.raises(ValueError,match='alert_dispatch_limit_invalid'):
        dispatch(production[0],limit=limit)

def test_lane_defaults_expiry_and_disable(production):
    c,_,_=production
    assert all(not c.lane(x) for x in LANES)
    controls=c.controls();controls['lanes']['outlook_send']=True;controls['lease_expires']=time.time()+60
    atomic_json(c.controls_path,controls)
    assert c.lane('outlook_send') and not c.lane('asana_mutations')
    with pytest.raises(ProductionConfigurationError):c.validate(os.environ,initial=True)
    controls['lease_expires']=time.time()-1;atomic_json(c.controls_path,controls)
    assert not c.lane('outlook_send')

def test_inert_configuration_admits_no_customer_scope(production):
    c,_,env=production;m=copy.deepcopy(c.manifest)
    m['outlook'].update(allowed_recipients=[],allowed_senders=[],sender_roles={})
    scoped=replace(c,manifest=m);scoped.validate(env)
    controls=c.controls();controls['lanes']['outlook_inbound']=True;controls['lease_expires']=time.time()+60
    atomic_json(c.controls_path,controls)
    with pytest.raises(ProductionConfigurationError,match='production_pilot_participant_scope_missing'):
        scoped.validate(env)

def signed_operator(c,p):
    key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    claims={'iss':'https://login.microsoftonline.com/'+p.tenant+'/v2.0','aud':c.manifest['auth']['audience'],
            'tid':p.tenant,'oid':p.oid,'scp':'access_as_user','azp':c.manifest['auth']['authorized_client_ids'][0],
            'roles':['OPERATOR','APPROVER'],'exp':int(time.time())+300,'iat':int(time.time()),'nbf':int(time.time())-1}
    verifier=EntraVerifier(c)
    verifier.keys=SimpleNamespace(get_signing_key_from_jwt=lambda token:SimpleNamespace(key=key.public_key()))
    return verifier,key,claims

def test_auth_signature_claims_roles_revocation(production):
    c,p,_=production;v,key,claims=signed_operator(c,p)
    token=jwt.encode(claims,key,algorithm='RS256')
    assert v.verify(token).actor==p.actor
    for change in [{'aud':str(uuid4())},{'tid':str(uuid4())},{'idtyp':'app'},{'scp':'wrong'},{'azp':str(uuid4())},{'oid':str(uuid4())},{'exp':1}]:
        with pytest.raises(Exception):v.verify(jwt.encode({**claims,**change},key,algorithm='RS256'))
    with pytest.raises(Exception):v.verify(jwt.encode(claims,rsa.generate_private_key(public_exponent=65537,key_size=2048),algorithm='RS256'))
    registry=json.loads(Path(c.operators_path).read_text());registry['operators'][p.oid]['enabled']=False;atomic_json(c.operators_path,registry)
    with pytest.raises(PermissionError):v.verify(token)

def test_durable_registry_revokes_existing_token_and_fails_closed(production,monkeypatch):
    from tools.production_runtime import state_store
    c,p,_=production;v,key,claims=signed_operator(c,p)
    token=jwt.encode(claims,key,algorithm='RS256')
    registry=c.operator_registry()
    monkeypatch.setattr(state_store,'enabled',lambda _:True)
    monkeypatch.setattr(state_store,'operators',lambda _:registry)
    assert v.verify(token).actor==p.actor
    registry['operators'][p.oid]['enabled']=False
    with pytest.raises(PermissionError):v.verify(token)
    def unavailable(_):raise ValueError('production_operator_registry_unavailable')
    monkeypatch.setattr(state_store,'operators',unavailable)
    with pytest.raises(ValueError):v.verify(token)

@pytest.mark.parametrize('path',['/api/operator/access/revoke','/api/operator/cases/1/privacy/raw-expiry'])
def test_operator_cannot_revoke_or_erase(production,path):
    from tools.production_runtime.middleware import ProductionOperatorApp
    c,p,_=production;v,key,claims=signed_operator(c,p)
    token=jwt.encode(claims,key,algorithm='RS256');responses=[]
    app=ProductionOperatorApp(lambda *_:pytest.fail('must not reach application'),c,verifier=v)
    data=b'{"review_confirmed":true}'
    result=app({'PATH_INFO':path,'REQUEST_METHOD':'POST','HTTP_AUTHORIZATION':'Bearer '+token,
        'HTTP_ORIGIN':c.manifest['application_origin'],'CONTENT_LENGTH':str(len(data)),'wsgi.input':io.BytesIO(data)},
        lambda status,*_:responses.append(status))
    assert responses==['403 Forbidden'] and json.loads(result[0])=={'error':'access_denied'}


@pytest.mark.parametrize('accept',['text/html','application/json'])
def test_whoami_is_readable_without_exposing_credentials(production,accept):
    from tools.production_runtime.middleware import ProductionOperatorApp
    c,p,_=production;v,key,claims=signed_operator(c,p)
    token=jwt.encode(claims,key,algorithm='RS256');responses=[]
    app=ProductionOperatorApp(lambda *_:pytest.fail('must not reach application'),c,verifier=v)
    body=b''.join(app({'PATH_INFO':'/api/operator/whoami','REQUEST_METHOD':'GET',
        'HTTP_AUTHORIZATION':'Bearer '+token,'HTTP_ACCEPT':accept},
        lambda status,headers:responses.append((status,dict(headers))))).decode()
    assert responses[0][0]=='200 OK' and responses[0][1]['Cache-Control']=='no-store'
    assert p.actor in body and token not in body
    if accept=='text/html':
        assert '<li>Operator</li>' in body and '<li>Approver</li>' in body
        assert responses[0][1]['Content-Type'].startswith('text/html')
    else:
        assert json.loads(body)=={'actor':p.actor,'roles':sorted(p.roles)}


def test_middleware_roles_origin_and_gate_shutdown(production):
    from tools.production_runtime.middleware import ProductionOperatorApp
    c,p,_=production;v,key,claims=signed_operator(c,p);calls=[]
    def downstream(env,start):calls.append(CURRENT.get().actor);start('200 OK',[]);return [b'ok']
    app=ProductionOperatorApp(downstream,c,verifier=v)
    def request(path,roles,origin=None,body=b'{}'):
        token=jwt.encode({**claims,'roles':roles},key,algorithm='RS256')
        env={'PATH_INFO':path,'REQUEST_METHOD':'POST','HTTP_AUTHORIZATION':'Bearer '+token,'CONTENT_LENGTH':str(len(body)),'wsgi.input':io.BytesIO(body)}
        if origin:env['HTTP_ORIGIN']=origin
        status=[];app(env,lambda s,h:status.append(s));return status[0]
    assert request('/api/operator/cases/1/approvals/2/approve',['OPERATOR'],c.manifest['application_origin']).startswith('403')
    assert request('/api/operator/cases/1/approvals/2/approve',['APPROVER'],'https://evil.test').startswith('403')
    assert request('/api/operator/cases/1/approvals/2/approve',['APPROVER'],c.manifest['application_origin']).startswith('200')
    assert calls==[p.actor] and CURRENT.get() is None


def test_alert_delivery_and_backup_crypto(production,tmp_path):
    from tools.production_runtime.alerts import emit,dispatch
    from tools.production_runtime.recovery import protect,recover,retention_plan
    from cryptography.hazmat.primitives import serialization
    c,p,_=production;emit(c,'CHECKPOINT_FAILURE',actor=p.actor)
    class Response:
        status=202
        def __enter__(self):return self
        def __exit__(self,*args):pass
    calls=[]
    class Opener:
        def open(self,req,timeout):calls.append(json.loads(req.data));return Response()
    assert dispatch(c,opener=Opener())==1 and calls[0]['code']=='CHECKPOINT_FAILURE'
    key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    public=key.public_key().public_bytes(serialization.Encoding.PEM,serialization.PublicFormat.SubjectPublicKeyInfo)
    private=key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption())
    path=protect(b'private-database',public,deployment_id=c.manifest['deployment_id'],ledger_hash='test',destination=tmp_path)
    assert b'private-database' not in path.read_bytes()
    assert recover(path,private,expected_deployment=c.manifest['deployment_id'])==b'private-database'
    with pytest.raises(ValueError):recover(path,private,expected_deployment='wrong')
    with pytest.raises(ValueError):retention_plan(tmp_path,approved_policy={})

def test_permission_probes_are_bounded_gets(production):
    from .permissions import verify_outlook,verify_asana
    c,_,_=production
    class Graph:
        calls=[]
        def request(self,**k):
            self.calls.append(k);assert k['method']=='GET'
            return (403,'{}',{}) if 'negative' in k['url'] else (200,'{"id":"inbox"}',{})
    graph=Graph();out=verify_outlook(c,graph,'fake',known_existing_forbidden_mailbox='negative@example.test')
    assert out['mailbox_read_verified'] and out['negative_scope_verified'] and len(graph.calls)==2
    class Asana:
        def send_json(self,**k):
            assert k['method']=='GET' and c.manifest['asana']['project_gid'] in k['url']
            return 200,json.dumps({'data':{'gid':c.manifest['asana']['project_gid'],'workspace':{'gid':c.manifest['asana']['workspace_gid']}}}),{}
    assert verify_asana(c,Asana(),'fake')['project_read_verified']

def test_admin_has_no_business_authority_and_disable_is_independent(production):
    from .middleware import ProductionOperatorApp
    c,p,_=production;v,key,claims=signed_operator(c,p)
    registry=json.loads(Path(c.operators_path).read_text());registry['operators'][p.oid]['roles']=['ADMIN'];atomic_json(c.operators_path,registry)
    app=ProductionOperatorApp(lambda e,s: (_ for _ in ()).throw(AssertionError('Business path entered')),c,verifier=v)
    claims['roles']=['ADMIN'];token=jwt.encode(claims,key,algorithm='RS256')
    controls=c.controls();controls['lanes']={k:True for k in LANES};controls['lease_expires']=time.time()+60;atomic_json(c.controls_path,controls)
    body=b'{"disable":"outlook_send"}';status=[]
    env={'REQUEST_METHOD':'POST','PATH_INFO':'/api/operator/provider-gates','HTTP_AUTHORIZATION':'Bearer '+token,'HTTP_X_WNC_API':'1','CONTENT_LENGTH':str(len(body)),'wsgi.input':io.BytesIO(body)}
    app(env,lambda s,h:status.append(s));assert status==['200 OK']
    assert not c.lane('outlook_send') and c.lane('outlook_inbound') and c.lane('asana_mutations')
    env['PATH_INFO']='/api/operator/cases/1/approvals/1/approve';status=[]
    app(env,lambda s,h:status.append(s));assert status==['403 Forbidden']

def test_staging_factory_rejects_production_destinations():
    from .config import validate_staging_target
    with pytest.raises(ValueError):validate_staging_target(provider='outlook',config=SimpleNamespace(sender_mailbox='production@example.test'))
    with pytest.raises(ValueError):validate_staging_target(provider='asana',config=SimpleNamespace(default_project_gid='999'))

def test_provider_redirect_and_unknown_host_refused():
    import urllib.request
    from tools.production_runtime.network import open_provider,NoProviderRedirect
    with pytest.raises(ValueError,match='provider_host_forbidden'):
        open_provider(urllib.request.Request('https://evil.example.test/'),timeout=1,context=None)
    with pytest.raises(ValueError,match='provider_redirect_forbidden'):
        NoProviderRedirect().redirect_request(None,None,None,None,None,None)
