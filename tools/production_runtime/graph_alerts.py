"""Fixed-recipient administrative alerts, separate from rental-send execution."""
import json
import os
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
import certifi
from .network import open_provider

TENANT='7c9d7d19-2b22-4da3-975a-1fba6f29c366'
CLIENT='fadc2e8e-14a0-496d-b95f-2815a2755ca3'
MAILBOX='booking@whennaturecalls.nl'
RECIPIENT='serinya@gjemmestad.com'


class AlertOutcomeAmbiguous(RuntimeError):pass


def request(method,url,headers,data):
    req=urllib.request.Request(url,data=data,headers=headers,method=method)
    try:
        with open_provider(req,timeout=10,context=ssl.create_default_context(cafile=certifi.where())) as response:
            return response.status,response.read(65537)
    except urllib.error.HTTPError as error:
        return error.code,b''
    except Exception:
        raise AlertOutcomeAmbiguous('administrative_alert_transport_outcome_unknown') from None


class GraphAlerts:
    def __init__(self,contract,*,secret=None,requester=request):
        self.contract=contract;self.request=requester
        outlook=contract.manifest['outlook'];alert=contract.manifest['alerting']
        if (outlook['tenant_id']!=TENANT or outlook['client_id']!=CLIENT
            or outlook['mailbox'].casefold()!=MAILBOX or alert.get('recipient')!=RECIPIENT
            or alert.get('transport')!='graph_mail_alert_v1'):
            raise ValueError('administrative_alert_identity_or_recipient_forbidden')
        self.secret=secret or os.environ.get('PRODUCTION_MICROSOFT_CLIENT_SECRET')
        if not self.secret:raise ValueError('administrative_alert_credential_missing')
        self.token=None;self.expires_at=0

    def access_token(self):
        if self.token and time.time()<self.expires_at-60:return self.token
        fields={'client_id':CLIENT,'client_secret':self.secret,'grant_type':'client_credentials',
                'scope':'https://graph.microsoft.com/.default'}
        status,body=self.request('POST','https://login.microsoftonline.com/'+TENANT+'/oauth2/v2.0/token',
            {'Content-Type':'application/x-www-form-urlencoded'},urllib.parse.urlencode(fields).encode())
        if status!=200:raise ValueError('administrative_alert_token_failed')
        try:
            payload=json.loads(body);token=payload['access_token']
            if not isinstance(token,str) or len(token)<10 or type(payload['expires_in']) is not int or not 60<=payload['expires_in']<=86400:
                raise ValueError()
        except Exception:raise ValueError('administrative_alert_token_shape_invalid') from None
        self.token=token;self.expires_at=time.time()+payload['expires_in'];return token

    def send(self,event,key):
        from .alerts import CODES
        if (set(event)!={'deployment_id','code','timestamp','case_id','actor'}
            or event['deployment_id']!=self.contract.manifest['deployment_id'] or event['code'] not in CODES
            or len(key)!=64 or any(c not in '0123456789abcdef' for c in key)):
            raise ValueError('administrative_alert_event_invalid')
        subject=('SAFE SYNTHETIC WNC production alert verification' if event['code']=='SYNTHETIC_VERIFICATION'
                 else 'WNC production alert: '+event['code'])+' ['+key[:16]+']'
        content='Administrative WNC Rental Brain alert.\nCode: '+event['code']+'\nDeployment: '+event['deployment_id']+'\nEvent: '+key+'\nNo customer message body or rental facts are included.'
        payload={'message':{'subject':subject,'body':{'contentType':'Text','content':content},
            'toRecipients':[{'emailAddress':{'address':RECIPIENT}}]},'saveToSentItems':True}
        status,_=self.request('POST','https://graph.microsoft.com/v1.0/users/'+urllib.parse.quote(MAILBOX,safe='')+'/sendMail',
            {'Content-Type':'application/json','Authorization':'Bearer '+self.access_token()},json.dumps(payload).encode())
        if status>=500:raise AlertOutcomeAmbiguous('administrative_alert_provider_outcome_unknown')
        if status!=202:raise ValueError('administrative_alert_provider_rejected')
        return {'status':'provider_accepted','http_status':202,'recipient':RECIPIENT,
                'subject':subject,'receipt_confirmed':False}
