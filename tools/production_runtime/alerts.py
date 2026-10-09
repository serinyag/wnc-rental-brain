"""Durable content-free alert outbox; delivery never includes request bodies/tokens."""
import hashlib, json, os, tempfile, time, urllib.request
from pathlib import Path
CODES=frozenset({'AUTH_DENIED','SCOPE_DENIED','INBOUND_FAILURE','CHECKPOINT_FAILURE','QUARANTINE',
 'ASSOCIATION_REVIEW','INBOUND_BACKLOG','STUCK_WORK','AUTHORITY_FAILURE','STALE_DRAFT',
 'OUTLOOK_FAILURE','PROVIDER_AMBIGUITY','RECONCILIATION_REQUIRED','ASANA_FAILURE',
 'MONITOR_READY','ASANA_MISMATCH','UNEXPECTED_RECIPIENT','APPLICATION_FAILURE','LANE_CHANGED','PRIVACY_ACTION','SYNTHETIC_VERIFICATION'})

def atomic_json(path,payload):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    fd,tmp=tempfile.mkstemp(dir=path.parent,prefix='.wnc-')
    try:
        with os.fdopen(fd,'w') as f:
            json.dump(payload,f,sort_keys=True);f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
        directory=os.open(path.parent,os.O_RDONLY)
        try:os.fsync(directory)
        finally:os.close(directory)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def emit(contract,code,*,case_id=None,actor=None):
    if code not in CODES:raise ValueError('unknown_alert_code')
    event={'deployment_id':contract.manifest['deployment_id'],'code':code,'timestamp':int(time.time()),
           'case_id':case_id if type(case_id) is int else None,'actor':actor}
    key=hashlib.sha256(json.dumps(event,sort_keys=True).encode()).hexdigest()
    from . import state_store
    if state_store.enabled(contract):
        state_store.emit_alert(contract,key,event)
        return key
    path=Path(contract.manifest['alerting']['spool_path'])/(key+'.json')
    atomic_json(path,event)
    return key

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):raise ValueError('alert_redirect_forbidden')

def dispatch(contract,*,opener=None,limit=25,sender=None):
    """Bounded worker; durable Graph alerts fence unknown outcomes before retry."""
    from .config import ProductionContract
    if not isinstance(contract,ProductionContract):raise ValueError('validated_contract_required')
    if type(limit) is not int or not 1<=limit<=25:raise ValueError('alert_dispatch_limit_invalid')
    from . import state_store
    if state_store.enabled(contract):
        from .graph_alerts import GraphAlerts,AlertOutcomeAmbiguous
        if state_store.unresolved_alerts(contract):
            state_store.disable(contract)
            raise ValueError('administrative_alert_reconciliation_required')
        sender=sender or GraphAlerts(contract)
        sent=0
        for key,event in state_store.pending_alerts(contract,limit):
            if not state_store.claim_alert(contract,key):continue
            try:receipt=sender.send(event,key)
            except AlertOutcomeAmbiguous:
                state_store.alert_receipt(contract,key,'ambiguous',{'status':'reconciliation_required'})
                state_store.disable(contract)
                raise
            except Exception:
                state_store.alert_receipt(contract,key,'failed',{'status':'delivery_failed'})
                state_store.disable(contract)
                raise
            state_store.alert_receipt(contract,key,'accepted',receipt);sent+=1
        state_store.heartbeat(contract,sent)
        atomic_json(Path(contract.manifest['alerting']['spool_path'])/'heartbeat.state',{'at':time.time(),'sent':sent})
        return sent
    opener=opener or urllib.request.build_opener(NoRedirect())
    sent=0
    for p in sorted(Path(contract.manifest['alerting']['spool_path']).glob('*.json'))[:limit]:
        event=json.loads(p.read_text())
        if event['deployment_id']!=contract.manifest['deployment_id']:raise ValueError('alert_scope_mismatch')
        request=urllib.request.Request(contract.manifest['alerting']['destination'],json.dumps(event).encode(),
            {'Content-Type':'application/json','Authorization':'Bearer '+os.environ['PRODUCTION_ALERT_TOKEN'],
             'Idempotency-Key':p.stem},method='POST')
        with opener.open(request,timeout=5) as response:
            if response.status not in (200,201,202,204):raise ValueError('alert_delivery_failed')
        p.rename(p.with_suffix('.delivered'));sent+=1
    atomic_json(Path(contract.manifest['alerting']['spool_path'])/'heartbeat.state',{'at':time.time(),'sent':sent})
    return sent
