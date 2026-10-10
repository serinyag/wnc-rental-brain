"""Durable controls and named-operator revocation for the free shared deployment."""
import os
import hashlib
from contextlib import contextmanager
import psycopg
from psycopg.types.json import Jsonb
from .database import CA


def enabled(contract):
    return contract.manifest['database'].get('state_backend')=='postgres_v1'


def connection(contract):
    dsn=os.environ.get('DATABASE_URL','')
    contract.validate_database(dsn)
    try:
        return psycopg.connect(dsn,sslrootcert=str(CA),connect_timeout=5)
    except Exception:
        raise ValueError('production_state_store_unavailable') from None


def controls(contract):
    try:
        with connection(contract) as c:
            row=c.execute('select lanes,lease_expires from rental_production.runtime_provider_controls where deployment_id=%s',
                          (contract.manifest['deployment_id'],)).fetchone()
        if row is None:raise ValueError('production_controls_missing')
        return {'deployment_id':contract.manifest['deployment_id'],'lanes':row[0],'lease_expires':float(row[1])}
    except Exception:
        raise ValueError('production_controls_unavailable') from None


def disable(contract,lane=None):
    from .config import LANES
    if lane is not None and lane not in LANES:raise ValueError('unknown_provider_lane')
    with connection(contract) as c:
        if lane is None:
            c.execute('update rental_production.runtime_provider_controls set lanes=%s,lease_expires=0 where deployment_id=%s',
                      (Jsonb({k:False for k in LANES}),contract.manifest['deployment_id']))
        else:
            c.execute("update rental_production.runtime_provider_controls set lanes=jsonb_set(lanes,%s,'false'::jsonb) where deployment_id=%s",
                      ([lane],contract.manifest['deployment_id']))
    return controls(contract)


def operators(contract):
    try:
        with connection(contract) as c:
            rows=c.execute('select object_id::text,enabled,name,roles from rental_production.runtime_operator_registry where deployment_id=%s',
                           (contract.manifest['deployment_id'],)).fetchall()
        return {'deployment_id':contract.manifest['deployment_id'],'operators':{
            oid:{'enabled':active,'name':name,'roles':roles} for oid,active,name,roles in rows}}
    except Exception:
        raise ValueError('production_operator_registry_unavailable') from None


def emit_alert(contract,key,event):
    if event['deployment_id']!=contract.manifest['deployment_id']:
        raise ValueError('alert_deployment_mismatch')
    with connection(contract) as c:
        c.execute('insert into rental_production.runtime_alert_outbox(event_id,deployment_id,payload) values(%s,%s,%s) on conflict(event_id) do nothing',
                  (key,event['deployment_id'],Jsonb(event)))


def pending_alerts(contract,limit):
    with connection(contract) as c:
        rows=c.execute("select event_id,payload from rental_production.runtime_alert_outbox where deployment_id=%s and status='pending' order by created_at,event_id limit %s",
                       (contract.manifest['deployment_id'],limit)).fetchall()
    return rows


@contextmanager
def alert_dispatch_lock(contract):
    """Session ownership spans claim, provider call and durable receipt.

    A competing deployment does not mistake the owner's active claim for an
    abandoned send. A lost owner still leaves its claim fenced for reconciliation.
    """
    key=int.from_bytes(hashlib.sha256(('wnc-alerts:'+contract.manifest['deployment_id']).encode()).digest()[:8],signed=True)
    with connection(contract) as c:
        acquired=c.execute('select pg_try_advisory_lock(%s)',(key,)).fetchone()[0]
        try:yield acquired
        finally:
            if acquired:c.execute('select pg_advisory_unlock(%s)',(key,))


def claim_alert(contract,key):
    with connection(contract) as c:
        row=c.execute("update rental_production.runtime_alert_outbox set status='sending' where event_id=%s and deployment_id=%s and status='pending' returning event_id",
                      (key,contract.manifest['deployment_id'])).fetchone()
    return row is not None


def unresolved_alerts(contract):
    with connection(contract) as c:
        return c.execute("select count(*) from rental_production.runtime_alert_outbox where deployment_id=%s and status in ('sending','ambiguous')",
                         (contract.manifest['deployment_id'],)).fetchone()[0]


def alert_receipt(contract,key,status,receipt):
    if status not in ('accepted','ambiguous','failed'):raise ValueError('invalid_alert_receipt_status')
    with connection(contract) as c:
        c.execute('update rental_production.runtime_alert_outbox set status=%s,receipt=%s,accepted_at=case when %s=\'accepted\' then now() else null end where event_id=%s and deployment_id=%s',
                  (status,Jsonb(receipt),status,key,contract.manifest['deployment_id']))


def heartbeat(contract,signals):
    with connection(contract) as c:
        c.execute('insert into rental_production.runtime_monitor_heartbeat values(%s,now(),%s) on conflict(deployment_id) do update set observed_at=excluded.observed_at,signals=excluded.signals',
                  (contract.manifest['deployment_id'],signals))


def lifecycle_receipt(contract,receipt):
    from uuid import uuid4
    with connection(contract) as c:
        c.execute('insert into rental_production.runtime_lifecycle_journal(id,deployment_id,payload) values(%s,%s,%s)',
            (uuid4(),contract.manifest['deployment_id'],Jsonb(receipt)))


def revoke_operator(contract,object_id,*,actor):
    from uuid import UUID,uuid4
    object_id=str(UUID(object_id))
    from .config import LANES
    with connection(contract) as c:
        row=c.execute('update rental_production.runtime_operator_registry set enabled=false where deployment_id=%s and object_id=%s returning object_id',
            (contract.manifest['deployment_id'],object_id)).fetchone()
        if row is None:raise ValueError('named_operator_not_registered')
        c.execute('update rental_production.runtime_provider_controls set lanes=%s,lease_expires=0 where deployment_id=%s',
            (Jsonb({k:False for k in LANES}),contract.manifest['deployment_id']))
        c.execute('insert into rental_production.runtime_lifecycle_journal(id,deployment_id,payload) values(%s,%s,%s)',
            (uuid4(),contract.manifest['deployment_id'],Jsonb({'actor':actor,'revoked_object_id':object_id,'disposition':'operator_revoked'})))
    return {'object_id':object_id,'enabled':False,'provider_gates':'all_off'}


def expire_accepted_alerts(contract,*,cutoff,actor,policy):
    """Erase acknowledged diagnostic detail; preserve content-free replay keys."""
    from uuid import uuid4
    with connection(contract) as c:
        rows=c.execute("update rental_production.runtime_alert_outbox set payload='{}',receipt='{\"status\":\"expired\"}' where deployment_id=%s and status='accepted' and accepted_at<to_timestamp(%s) and payload<>'{}'::jsonb returning event_id",
            (contract.manifest['deployment_id'],cutoff)).fetchall()
        receipt={'actor':actor,'policy_version':policy,'expired_alerts':[r[0] for r in rows]}
        c.execute('insert into rental_production.runtime_lifecycle_journal(id,deployment_id,payload) values(%s,%s,%s)',
            (uuid4(),contract.manifest['deployment_id'],Jsonb(receipt)))
    return receipt
