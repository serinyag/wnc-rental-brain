"""Content-free, read-only operator snapshot. No provider calls or notifications.

collect(connection) must receive an already identity-validated database connection.
This module deliberately has no credential discovery or production connection CLI.
"""
QUERIES = {
 'failed_attempts': "select count(*) from public.workflow_execution_attempts where status in ('failed','timeout') and created_at > now()-interval '24 hours'",
 'ambiguous_attempts': "select count(*) from public.workflow_execution_attempts where failure_code='adapter_outcome_ambiguous'",
 'association_review': "select count(*) from public.outlook_inbound_messages where association_status='needs_review'",
 'quarantined_observations': "select count(*) from public.inbound_observations where status='quarantined'",
 'stuck_actions': "select count(*) from public.workflow_actions where status='executing' and updated_at < now()-interval '10 minutes'",
 'stale_drafts': "select count(*) from public.inquiry_response_draft_revisions d join public.rental_cases c on c.id=d.rental_case_id where d.is_current and d.source_case_revision<>c.case_revision and d.draft_status in ('draft','needs_approval','approved')",
 'checkpoint_stale': "select count(*) from public.outlook_inbound_checkpoints where last_successful_sync_at is null or last_successful_sync_at < now()-interval '15 minutes'",
}

def collect(connection):
    # Dedicated connection required: nested transaction cannot change read mode.
    if connection.info.transaction_status.value != 0:
        raise ValueError('monitor_requires_idle_dedicated_connection')
    with connection.transaction():
        connection.execute('set transaction read only')
        connection.execute("set local statement_timeout='5s'")
        return {name:connection.execute(sql).fetchone()[0] for name,sql in QUERIES.items()}

def report(metrics, *, health_ok, inbound_expected=False):
    """Reject unknown/missing signals instead of reporting false healthy status."""
    alerts=[]
    if health_ok is not True: alerts.append({'code':'HEALTH_UNAVAILABLE','severity':'stop'})
    for name in QUERIES:
        value=metrics.get(name)
        if type(value) is not int or value<0:
            alerts.append({'code':'MONITOR_SIGNAL_MISSING','signal':name,'severity':'stop'})
        elif value and (name!='checkpoint_stale' or inbound_expected):
            alerts.append({'code':name.upper(),'count':value,'severity':'review'})
    return {'status':'attention' if alerts else 'ok','alerts':alerts,
            'delivery':'operator_stdout_only','production_alert_routing_verified':False}
