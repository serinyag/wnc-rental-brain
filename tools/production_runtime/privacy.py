"""Data inventory and governed lifecycle requests; no implicit retention policy.

Raw case evidence remains immutable while operational or needed for reconciliation.
A lifecycle plan explicitly enumerates content and preserved audit obligations.
"""
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json,uuid
from .auth import CURRENT
from .alerts import atomic_json,emit
CATEGORIES={
 'raw_inbound':('outlook_inbound_messages.raw_provider_payload','workflow_events.structured_payload'),
 'normalized_email':('outlook_inbound_messages.envelope','inbound_source_records.evidence_excerpt'),
 'contact_identity':('inbound_source_records.sender_actor_reference','rental_cases.primary_contact_ref'),
 'case_facts':('rental_case_facts.value_payload',),
 'observations':('inbound_observations.candidate_value_payload','inbound_observations.source_excerpt'),
 'provider_identifiers':('outlook_inbound_messages.message_id','outlook_inbound_conversations.conversation_id'),
 'drafts':('inquiry_response_draft_revisions.body_text','inquiry_response_draft_revisions.recipient_email'),
 'approvals':('rental_case_approval_requests',),
 'attempts':('workflow_execution_attempts',),
 'audit':('workflow_events',),
 'historical':('public.historical_case_versions',),
 'logs':('alert_outbox','host_logs'),
}

def validate_policy(policy):
    if not policy.get('approved_by') or not policy.get('policy_version'):raise ValueError('privacy_policy_unapproved')
    if policy.get('mode')=='split_closure_v1':
        if (policy['policy_version']!='WNC_PILOT_RETENTION_20261009' or
            policy.get('raw_body_days_after_closure')!=180 or policy.get('structured_calendar_years_after_closure')!=2 or
            policy.get('technical_log_days')!=90 or policy.get('accounting_documents')!='excluded'):
            raise ValueError('production_retention_policy_mismatch')
        return policy
    if set(policy.get('retention_days',{}))!=set(CATEGORIES):raise ValueError('privacy_category_policy_incomplete')
    if any(type(x) is not int or x<1 for x in policy['retention_days'].values()):raise ValueError('invalid_retention_duration')
    bundle=set(CATEGORIES)-{"historical","logs"}
    if len({policy["retention_days"][k] for k in bundle})!=1:raise ValueError("linked_case_categories_require_one_explicit_bundle_duration")
    return policy

def journal(contract,receipt):
    from . import state_store
    if state_store.enabled(contract):
        state_store.lifecycle_receipt(contract,receipt)
    else:
        atomic_json(Path(contract.manifest['alerting']['lifecycle_spool_path'])/(str(uuid.uuid4())+'.json'),receipt)

def lifecycle_plan(contract,*,case_id,category,request_reference,legal_hold,case_active,unresolved_attempts):
    p=CURRENT.get()
    if p is None:raise PermissionError('named_operator_required')
    p.require('ADMIN')
    validate_policy(contract.manifest['privacy'])
    if category not in CATEGORIES or not request_reference.strip():raise ValueError('lifecycle_request_invalid')
    plan={'id':str(uuid.uuid4()),'actor':p.actor,'case_id':case_id,'category':category,
          'request_reference':request_reference,'policy_version':contract.manifest['privacy']['policy_version'],
          'at':datetime.now(timezone.utc).isoformat(),'targets':CATEGORIES[category],
          'disposition':'held' if legal_hold or case_active or unresolved_attempts else 'eligible_for_review',
          'preserve':['case_id','event sequence','approval/attempt binding','integrity hashes','lifecycle receipt']}
    journal(contract,plan)
    emit(contract,'PRIVACY_ACTION',case_id=case_id,actor=p.actor)
    return plan

def redact_diagnostic(value):
    """Only bounded known metadata survives; unknown keys/content are dropped."""
    allowed={'failure_code','stage','status','case_id','workflow_action_id','attempt_id','duration_ms'}
    return {k:v for k,v in value.items() if k in allowed and
            (type(v) in (int,float,bool) or (isinstance(v,str) and len(v)<100 and all(c.isalnum() or c in '_-' for c in v)))}

def anonymize_case(contract,connection,*,case_id,request_reference):
    """Explicit admin action under an approved policy; DB rechecks terminal holds."""
    p=CURRENT.get()
    if p is None:raise PermissionError('named_operator_required')
    p.require('ADMIN')
    policy=validate_policy(contract.manifest['privacy'])
    if not request_reference:raise ValueError('lifecycle_request_reference_required')
    # One case bundle is anonymized only after every content category has expired;
    # individual early category erasure would break linked integrity/audit semantics.
    from tools.phase_08_workflow.outlook_inbound_service import connection_runner
    contract.verify_database_marker(connection_runner(connection))
    with connection.transaction():
        if policy.get('mode')=='split_closure_v1':
            value=connection.execute('select public.anonymize_case_at_calendar_expiry(%s,%s,%s,%s)',
                (case_id,p.actor,policy['policy_version'],request_reference)).fetchone()[0]
        else:
            days=max(policy['retention_days'].values())
            value=connection.execute('select public.anonymize_closed_rental_case(%s,%s,%s,%s,%s)',
                (case_id,p.actor,policy['policy_version'],request_reference,days)).fetchone()[0]
    emit(contract,'PRIVACY_ACTION',case_id=case_id,actor=p.actor)
    return str(value)


def expire_delivered_alerts(contract,*,now=None):
    """Only acknowledged content-free alerts expire; pending alerts never age away."""
    import time
    p=CURRENT.get()
    if p is None:raise PermissionError('named_operator_required')
    p.require('ADMIN')
    policy=validate_policy(contract.manifest['privacy'])
    days=policy['technical_log_days'] if policy.get('mode')=='split_closure_v1' else policy['retention_days']['logs']
    cutoff=(now or time.time())-days*86400
    from . import state_store
    if state_store.enabled(contract):
        return state_store.expire_accepted_alerts(contract,cutoff=cutoff,actor=p.actor,policy=policy['policy_version'])
    files=[f for f in Path(contract.manifest['alerting']['spool_path']).glob('*.delivered') if f.stat().st_mtime<cutoff]
    receipt={'actor':p.actor,'policy_version':policy['policy_version'],'expired_alerts':[f.stem for f in files]}
    journal(contract,receipt)
    for f in files:f.unlink()
    return receipt

def set_hold(contract,connection,*,case_id,reason_reference,enabled):
    """Named ADMIN only; durable receipt precedes a hold release."""
    p=CURRENT.get()
    if p is None:raise PermissionError('named_operator_required')
    p.require('ADMIN')
    if not reason_reference or type(enabled) is not bool:raise ValueError('hold_reason_required')
    from tools.phase_08_workflow.outlook_inbound_service import connection_runner
    contract.verify_database_marker(connection_runner(connection))
    receipt={'actor':p.actor,'case_id':case_id,'reason_reference':reason_reference,'hold_enabled':enabled,'at':datetime.now(timezone.utc).isoformat()}
    journal(contract,receipt)
    with connection.transaction():
        connection.execute('select id from public.rental_cases where id=%s for update',(case_id,))
        if enabled:
            connection.execute('insert into public.case_data_lifecycle_holds(rental_case_id,actor_reference,reason_reference) values(%s,%s,%s) on conflict(rental_case_id) do update set actor_reference=excluded.actor_reference,reason_reference=excluded.reason_reference,recorded_at=now()', (case_id,p.actor,reason_reference))
        else:connection.execute('delete from public.case_data_lifecycle_holds where rental_case_id=%s',(case_id,))
    return receipt

def anonymize_history(contract,connection,*,historical_case_id,request_reference,source_disposition_reference):
    """Erase retired database content; linked source disposition is separately attested.

    Shared active source material is a hold, never implicitly deleted. Owner must
    provide its approved redacted replacement or verified external erasure receipt.
    """
    p=CURRENT.get()
    if p is None:raise PermissionError('named_operator_required')
    p.require('ADMIN');policy=validate_policy(contract.manifest['privacy'])
    if policy.get('mode')=='split_closure_v1':
        raise ValueError('reference_corpus_disposition_requires_separate_source_review')
    from tools.phase_08_workflow.outlook_inbound_service import connection_runner
    contract.verify_database_marker(connection_runner(connection))
    with connection.transaction():
        result=connection.execute('select public.anonymize_retired_historical_case(%s,%s,%s,%s,%s,%s)',
            (historical_case_id,p.actor,policy['policy_version'],request_reference,source_disposition_reference,policy['retention_days']['historical'])).fetchone()[0]
    return str(result)

def expire_raw_bodies(contract,connection,*,case_id):
    p=CURRENT.get()
    if p is None:raise PermissionError('named_operator_required')
    p.require('ADMIN')
    policy=validate_policy(contract.manifest['privacy'])
    if policy.get('mode')!='split_closure_v1':raise ValueError('split_retention_policy_required')
    from tools.phase_08_workflow.outlook_inbound_service import connection_runner
    contract.verify_database_marker(connection_runner(connection))
    with connection.transaction():
        digest=connection.execute('select public.purge_closed_case_raw_bodies(%s,%s,%s)',
            (case_id,p.actor,policy['policy_version'])).fetchone()[0]
    journal(contract,{'actor':p.actor,'case_id':case_id,'disposition':'raw_body_expired','content_digest':digest,'policy_version':policy['policy_version']})
    return digest
