"""Automatic refresh of explicitly enrolled, already-bound staging projections.

Supabase remains authoritative. Provider gates, journal leases, strict validation,
manual drift checks and ambiguity fences apply exactly as for operator execution.
No unbound rental or production deployment is enrolled implicitly.
"""
import logging
from threading import Event, Thread

LOG = logging.getLogger(__name__)


def synchronize(service, rental_case_id):
    from .asana_projection import OPERATOR_VERSION, projection_attempts, prior_bindings
    from .google_proposal import binding, unresolved_attempts
    runtime = service.config.runtime
    if not runtime.is_staging or not service.config.allow_real_providers:
        return {'status': 'gates_disabled', 'executed': []}
    snap = service._require_case_snapshot(rental_case_id)
    enrolled = any(a.target_adapter_code == 'asana_projection' and a.status == 'succeeded'
                   and a.structured_payload.get('projection', {}).get('layout_version') == OPERATOR_VERSION
                   for a in snap.workflow_actions)
    if not enrolled or not binding(snap) or not prior_bindings(snap).get('master'):
        return {'status': 'not_enrolled', 'executed': []}
    if unresolved_attempts(snap) or any(a.status == 'started' or a.status != 'succeeded' and not a.retry_eligible
                                      for a in projection_attempts(snap)):
        return {'status': 'reconciliation_required', 'executed': []}
    executed = []
    for gate, prepare in [(runtime.staging_allow_real_google, service.prepare_google_proposal),
                           (runtime.staging_allow_real_asana, service.prepare_asana_rental_projection)]:
        if not gate:
            return {'status': 'gates_disabled', 'executed': executed}
        prepared = prepare(rental_case_id=rental_case_id)
        aid = prepared['workflow_action_id']
        action = service._require_case_snapshot(rental_case_id).find_workflow_action(aid)
        if action.status == 'succeeded':
            continue
        result = service.execute_action(rental_case_id=rental_case_id, workflow_action_id=aid, execution_mode='real')
        confirmed = service._require_case_snapshot(rental_case_id).find_workflow_action(aid).status == 'succeeded'
        executed.append({'workflow_action_id': aid, 'success': confirmed, 'failure_codes': result.failure_codes})
        if not confirmed:
            return {'status': 'review_required', 'executed': executed}
    return {'status': 'synchronized', 'executed': executed}


def start_worker(service):
    """Free hosted worker; polls canonical enrollment, not provider content.

    Gate closure prevents startup and every sync rechecks both adapter gates.
    Failures are logged; ambiguous actions are never retried by the next poll.
    """
    r = service.config.runtime
    if not (r.is_staging and service.config.allow_real_providers and
            r.staging_allow_real_google and r.staging_allow_real_asana):
        return None
    stop = Event()
    def run():
        from .asana_projection import OPERATOR_VERSION
        while not stop.wait(15):
            try:
                rows = service.query_runner("select distinct rental_case_id from public.workflow_actions "
                    "where target_adapter_code='asana_projection' and status='succeeded' "
                    "and structured_payload->'projection'->>'layout_version'='" + OPERATOR_VERSION + "'", expect_json=True)['rows']
                for row in rows:
                    result = synchronize(service, int(row['rental_case_id']))
                    if result['status'] not in {'synchronized', 'not_enrolled', 'gates_disabled'}:
                        LOG.warning('automatic_projection_sync case=%s status=%s', row['rental_case_id'], result['status'])
            except Exception:
                # No secrets or raw transport exceptions in operational logs.
                LOG.warning('automatic_projection_sync needs review')
    Thread(target=run, name='wnc-staging-projection-sync', daemon=True).start()
    return stop
