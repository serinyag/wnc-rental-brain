"""Content-free production monitoring from DB outcomes and alert outbox."""
from tools.production_readiness.monitor import QUERIES,report
from .alerts import emit
EXTRA={
 'stale_approvals':"select count(*) from public.rental_case_approval_requests r join public.workflow_actions a on r.target_entity_type='workflow_action' and a.id=r.target_entity_id join public.rental_cases c on c.id=a.rental_case_id where r.status in ('open','approved') and a.source_case_revision<>c.case_revision and a.status not in ('succeeded','cancelled','superseded')",
 'blocked_work':"select count(*) from public.rental_case_blockers where status='open'",
 'inbound_backlog':"select count(*) from public.outlook_inbound_checkpoints where status='paging' and last_successful_sync_at<now()-interval '15 minutes'",
 'asana_failures':"select count(*) from public.workflow_execution_attempts where adapter_code in ('asana_projection','asana','task_surface') and status in ('failed','timeout') and created_at>now()-interval '1 hour'",
 'outlook_failures':"select count(*) from public.workflow_execution_attempts where adapter_code in ('email','outlook') and status in ('failed','timeout') and created_at>now()-interval '1 hour'",
}
CODES={'stale_approvals':'STALE_DRAFT','failed_attempts':'OUTLOOK_FAILURE','ambiguous_attempts':'PROVIDER_AMBIGUITY','association_review':'ASSOCIATION_REVIEW',
 'quarantined_observations':'QUARANTINE','stuck_actions':'STUCK_WORK','stale_drafts':'STALE_DRAFT',
 'checkpoint_stale':'INBOUND_BACKLOG','blocked_work':'STUCK_WORK','inbound_backlog':'INBOUND_BACKLOG',
 'asana_failures':'ASANA_FAILURE','outlook_failures':'OUTLOOK_FAILURE'}

def check(contract,connection):
    from tools.phase_08_workflow.outlook_inbound_service import connection_runner
    with connection.transaction():
        connection.execute('set transaction read only')
        connection.execute("set local statement_timeout='5s'")
        contract.verify_database_marker(connection_runner(connection))
        metrics={k:connection.execute(query).fetchone()[0] for k,query in (QUERIES|EXTRA).items()}
    for name,count in metrics.items():
        if count and (name!='checkpoint_stale' or contract.lane('outlook_inbound')):emit(contract,CODES[name])
    if metrics.get('ambiguous_attempts'):emit(contract,'RECONCILIATION_REQUIRED')
    return metrics

def run_once():
    import os
    from .database import connect
    from .config import ProductionContract
    from .alerts import dispatch
    contract=ProductionContract.from_env()
    try:
        with connect(os.environ['DATABASE_URL'],autocommit=True,connect_timeout=5) as conn:metrics=check(contract,conn)
    except Exception:
        emit(contract,'APPLICATION_FAILURE');raise RuntimeError('monitoring_database_unavailable') from None
    delivered=dispatch(contract)
    from . import state_store
    if state_store.enabled(contract):state_store.heartbeat(contract,len(metrics))
    return {'signals':len(metrics),'alerts_delivered':delivered}
if __name__=='__main__':
    import json
    print(json.dumps(run_once()))
