"""Fail-closed production boundary around existing operator surfaces."""
import json, re, time, os, fcntl, html
from pathlib import Path
from .auth import CURRENT, EntraVerifier
from .alerts import emit, atomic_json
from .config import LANES

class ProductionOperatorApp:
    def __init__(self,app,contract,*,verifier=None):
        self.app,self.contract=app,contract
        self.verifier=verifier or EntraVerifier(contract)
    def reply(self,start,status,payload):
        data=json.dumps(payload).encode();start(status,[('Content-Type','application/json'),('Cache-Control','no-store')]);return [data]
    def __call__(self,environ,start):
        path=environ.get('PATH_INFO','');method=environ.get('REQUEST_METHOD','GET')
        token=None
        try:
            if path=='/healthz' and method=='GET':
                from .config import verify_knowledge
                verify_knowledge(self.contract,self.app.service.query_runner)
                report=self.app.service.get_health_report()
                from .config import read_json
                heartbeat=read_json(str(Path(self.contract.manifest['alerting']['spool_path'])/'heartbeat.state'))
                healthy=report.http_status.value==200 and 0 <= time.time()-heartbeat.get('at',0) < 150
                return self.reply(start,'200 OK' if healthy else '503 Service Unavailable',
                                  {'status':'ok' if healthy else 'unavailable','environment':'production'})
            header=('Bearer '+environ['HTTP_X_FORWARDED_ACCESS_TOKEN']) if environ.get('HTTP_X_FORWARDED_ACCESS_TOKEN') else environ.get('HTTP_AUTHORIZATION','')
            if not header.startswith('Bearer '):raise PermissionError('named_operator_required')
            principal=self.verifier.verify(header[7:]);token=CURRENT.set(principal)
            self.contract.validate_database(os.environ.get('DATABASE_URL',''))
            if hasattr(self.app,'service'):
                self.contract.verify_database_marker(self.app.service.query_runner)
            if method not in ('GET','HEAD'):
                # Browser proxy requests must preserve Origin; bearer API calls explicitly opt in.
                if environ.get('HTTP_ORIGIN')!=self.contract.manifest['application_origin']:
                    if environ.get('HTTP_ORIGIN') or environ.get('HTTP_X_WNC_API')!='1':raise PermissionError('request_origin_denied')
            if path=='/api/operator/whoami' and method=='GET':
                identity={'actor':principal.actor,'roles':sorted(principal.roles)}
                if 'text/html' in environ.get('HTTP_ACCEPT',''):
                    labels={'OPERATOR':'Operator','APPROVER':'Approver','DECISION_AUTHORITY':'Decision Authority','ADMIN':'Admin'}
                    body=('<!doctype html><meta charset="utf-8"><title>Production access</title>'
                          '<h1>Production access</h1><p>Verified actor: <code>'+html.escape(identity['actor'])+'</code></p>'
                          '<h2>Capabilities</h2><ul>'+''.join('<li>'+html.escape(labels[r])+'</li>' for r in identity['roles'])+
                          '</ul><p><a href="/">Return to rental console</a></p>').encode()
                    start('200 OK',[('Content-Type','text/html; charset=utf-8'),('Cache-Control','no-store'),
                                    ('X-Content-Type-Options','nosniff'),('Referrer-Policy','no-referrer')])
                    return [body]
                return self.reply(start,'200 OK',identity)
            if path=='/api/operator/access/revoke' and method=='POST':
                principal.require('ADMIN')
                n=int(environ.get('CONTENT_LENGTH','0'))
                if not 0<n<2048:raise ValueError('invalid_revocation_request')
                body=json.loads(environ['wsgi.input'].read(n))
                if set(body)!={'object_id'}:raise ValueError('invalid_revocation_request')
                from . import state_store
                if not state_store.enabled(self.contract):raise ValueError('durable_registry_required')
                receipt=state_store.revoke_operator(self.contract,body['object_id'],actor=principal.actor)
                return self.reply(start,'200 OK',receipt)
            privacy_match=re.fullmatch(r'/api/operator/cases/(\d+)/privacy/(raw-expiry|anonymize|hold)',path)
            if privacy_match and method=='POST':
                principal.require('ADMIN')
                n=int(environ.get('CONTENT_LENGTH','0'))
                if not 0<n<4096:raise ValueError('invalid_lifecycle_request')
                body=json.loads(environ['wsgi.input'].read(n))
                cid=int(privacy_match[1]);operation=privacy_match[2]
                from .database import connect
                from .privacy import expire_raw_bodies,anonymize_case,set_hold
                with connect(os.environ['DATABASE_URL'],autocommit=True,connect_timeout=5) as conn:
                    if operation=='raw-expiry' and set(body)=={'review_confirmed'} and body['review_confirmed'] is True:
                        receipt=expire_raw_bodies(self.contract,conn,case_id=cid)
                    elif operation=='anonymize' and set(body)=={'request_reference','review_confirmed'} and body['review_confirmed'] is True:
                        receipt=anonymize_case(self.contract,conn,case_id=cid,request_reference=body['request_reference'])
                    elif operation=='hold' and set(body)=={'reason_reference','enabled'}:
                        receipt=set_hold(self.contract,conn,case_id=cid,reason_reference=body['reason_reference'],enabled=body['enabled'])
                    else:raise ValueError('explicit_lifecycle_review_required')
                return self.reply(start,'200 OK',{'receipt':receipt})
            if path=='/api/operator/provider-gates' and method=='POST':
                principal.require('ADMIN')
                n=int(environ.get('CONTENT_LENGTH','0'))
                if not 0<n<2048:raise ValueError('invalid_control_request')
                body=json.loads(environ['wsgi.input'].read(n))
                if set(body)!={'disable'} or body['disable'] not in (*LANES,'all'):raise PermissionError('only_emergency_disable_supported')
                from . import state_store
                if state_store.enabled(self.contract):
                    c=state_store.disable(self.contract,None if body['disable']=='all' else body['disable'])
                else:
                    with open(self.contract.controls_path+'.lock','a') as lock:
                        fcntl.flock(lock,fcntl.LOCK_EX)
                        c=self.contract.controls()
                        for lane in LANES:
                            if body['disable'] in (lane,'all'):c['lanes'][lane]=False
                        c['changed_by']=principal.actor;c['changed_at']=time.time()
                        atomic_json(self.contract.controls_path,c)
                emit(self.contract,'LANE_CHANGED',actor=principal.actor)
                return self.reply(start,'200 OK',{'lanes':c['lanes']})
            if path.startswith('/clock/') or any(x in path for x in ('synthetic','final-receipt','raw-evidence','task-surface-actions')):
                raise PermissionError('production_fixture_path_forbidden')
            if method in ('GET','HEAD'):
                if not (path in ('/','/cases','/api/operator/cases','/api/operator/outlook-inbound/review') or
                        re.fullmatch(r'/(?:api/operator/)?cases/\d+(?:/live-proposal|/mailbox/(?:revalidation-read|drafts/\d+/outlook-read|actions/\d+/outlook-send-readiness))?',path)):
                    raise PermissionError('unapproved_production_read_path')
                if not principal.roles & {'OPERATOR','APPROVER','DECISION_AUTHORITY'}:raise PermissionError('case_read_denied')
            else:
                if re.search(r'/approvals/\d+/(approve|reject)$',path):principal.require('APPROVER')
                elif re.search(r'/actions/\d+/confirm-delivery$',path):principal.require('APPROVER')
                elif (path=='/operator/inbox-sync' or re.fullmatch(r'/(?:api/operator/)?cases/\d+/(inquiry-intake|inquiry-waiting|reconcile|operational-resolutions|asana-projection|structured-observations|mailbox)',path)
                      or re.fullmatch(r'/api/operator/outlook-inbound/(sync|preflight)',path)
                      or re.fullmatch(r'/(?:api/operator/)?cases/\d+/(?:mailbox/)?(?:actions|drafts)/\d+/(execute|generate|edit|observe-asana|outlook-reconcile|outlook-apply)',path)
                      or re.fullmatch(r'/api/operator/cases/\d+/mailbox/generate',path)):
                    principal.require('OPERATOR')
                else:raise PermissionError('unapproved_production_path')
            if path=='/operator/inbox-sync' and method=='POST':
                from tools.phase_08_workflow.outlook_inbound_runtime import synchronize
                synchronize()
                return self.app._respond_html(start,self.app._render_index())
            match=re.fullmatch(r'/cases/(\d+)/(operational-resolutions|asana-projection)',path)
            if match and method=='POST':
                cid=int(match[1])
                if match[2]=='operational-resolutions':
                    from .operator_ui import submit_form
                    submit_form(self.app.service,cid,self.app._parse_form(environ))
                else:self.app.service.prepare_asana_rental_projection(rental_case_id=cid)
                return self.app._respond_html(start,self.app._render_case_detail(cid))
            def observed_start(status,headers,*args):
                if int(status[:3])>=400:
                    code=('INBOUND_FAILURE' if 'outlook-inbound' in path else 'AUTHORITY_FAILURE' if 'operational-resolutions' in path
                          else 'ASANA_FAILURE' if 'asana' in path else 'OUTLOOK_FAILURE' if 'mailbox' in path or 'execute' in path else 'APPLICATION_FAILURE')
                    emit(self.contract,code,actor=principal.actor)
                return start(status,headers+[('Cache-Control','no-store'),('X-Content-Type-Options','nosniff'),('Referrer-Policy','no-referrer')],*args)
            return self.app(environ,observed_start)
        except Exception as error:
            # No token, body, provider response, arbitrary path or exception text in alerts/responses.
            denied=isinstance(error,PermissionError)
            try:emit(self.contract,'AUTH_DENIED' if denied else 'APPLICATION_FAILURE')
            except Exception:pass
            return self.reply(start,'403 Forbidden' if denied else '503 Service Unavailable',{'error':'access_denied' if denied else 'operation_unavailable'})
        finally:
            if token is not None:CURRENT.reset(token)
