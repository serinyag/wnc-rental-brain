"""Staging-only entry points. Independent preflight and ingestion authorization."""
import json
import ssl
import urllib.request
import urllib.error
from datetime import datetime, timezone
from dataclasses import replace
from urllib.parse import urlparse
import certifi
from tools.phase_05_search.semantic_common import load_env_value
from .outlook_adapter import OutlookAdapterConfig, OutlookExecutionAdapter
from .outlook_inbound import OutlookInboundConfig, OutlookInboundAdapter
from .outlook_inbound_service import sync_page


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('inbound_redirect_forbidden')


class ReadOnlyGraphTransport:
    def request(self, *, method, url, headers, body, timeout_seconds):
        parts = urlparse(url)
        token = method == 'POST' and parts.netloc == 'login.microsoftonline.com' and parts.path.endswith('/oauth2/v2.0/token')
        read = method == 'GET' and parts.netloc == 'graph.microsoft.com'
        if parts.scheme != 'https' or not (token or read): raise ValueError('inbound_transport_operation_forbidden')
        opener = urllib.request.build_opener(_NoRedirect(), urllib.request.HTTPSHandler(context=ssl.create_default_context(cafile=certifi.where())))
        try:
            with opener.open(urllib.request.Request(url,body,headers,method=method),timeout=timeout_seconds) as response:
                data=response.read(2_000_001)
                if len(data)>2_000_000: raise ValueError('inbound_response_bound_exceeded')
                return response.status,data.decode(),dict(response.headers)
        except urllib.error.HTTPError as exc:
            return exc.code,'{}',{}  # Never expose provider response bodies in errors.


def enabled(name): return (load_env_value(name) or '').lower() == 'true'


def configuration(*, preflight=False):
    env = load_env_value('APP_ENV')
    gate = 'STAGING_ALLOW_OUTLOOK_INBOUND_PREFLIGHT' if preflight else 'STAGING_ALLOW_REAL_OUTLOOK_INBOUND'
    if env != 'staging' or not enabled(gate): raise ValueError('inbound_operation_not_authorized')
    mailbox=load_env_value('OUTLOOK_SENDER_MAILBOX') or ''
    config=OutlookInboundConfig(mailbox,load_env_value('OUTLOOK_INBOUND_ALLOWED_MAILBOX') or '',
        load_env_value('OUTLOOK_INBOUND_SINCE') or '',
        tuple(x.strip().casefold() for x in (load_env_value('OUTLOOK_INBOUND_ALLOWED_SENDERS') or '').split(',') if x.strip()),
        load_env_value('OUTLOOK_INBOUND_NEW_ENQUIRY_SUBJECT') or '',True,env)
    config.validate()
    auth=OutlookAdapterConfig.from_env()
    if auth.graph_base_url!='https://graph.microsoft.com/v1.0' or auth.authority_base_url!='https://login.microsoftonline.com' or auth.read_availability_failure_code():
        raise ValueError('inbound_credentials_or_host_invalid')
    return config,auth


def build_adapter(*, preflight=False):
    config,auth=configuration(preflight=preflight)
    transport=ReadOnlyGraphTransport()
    token=OutlookExecutionAdapter(auth,transport,send_enabled=False)._acquire_access_token()
    if token.result is not None or not token.access_token: raise ValueError('inbound_token_failed')
    return OutlookInboundAdapter(config,transport,token.access_token)


def preflight():
    adapter=build_adapter(preflight=True)
    folder=adapter._get(adapter.base+'/mailFolders/inbox?$select=id,displayName')
    if not folder.get('id'): raise ValueError('inbox_identity_missing')
    # Initialize no durable checkpoint and return no message contents. The narrow
    # query starts now; the later authorized ingestion window remains separate.
    adapter.config=replace(adapter.config,since=datetime.now(timezone.utc).isoformat())
    records,cursor,status=adapter.read_page()
    # A second bounded read proves that the provider-returned opaque cursor
    # is usable, without writing a checkpoint or ingesting either page.
    replay_records,_,replay_status=adapter.read_page(cursor)
    for record in records + replay_records:
        if '@removed' not in record and not all(record.get(k) for k in ('id','conversationId','receivedDateTime')):
            raise ValueError('inbound_preflight_metadata_shape_invalid')
    return {'mailbox':adapter.config.mailbox,'folder':'inbox','folder_id':folder['id'],
        'read_only':True,'ingested':0,'bounded_records':len(records),'response_shape_valid':True,
        'checkpoint_persisted':False,'provider_scope_negative_test':'application guard only; no unauthorized mailbox accessed',
        'status':status,'cursor_replay_valid':True,'replay_status':replay_status,
        'replay_bounded_records':len(replay_records),'delta_pages_read':2}


def synchronize():
    import psycopg
    # Check both runtime and database destination before token or Graph access.
    configuration()
    dsn=load_env_value('DATABASE_URL') or ''
    host=urlparse(dsn).hostname
    if host!='db.mspcopnsbounmdpivkvq.supabase.co': raise ValueError('inbound_staging_database_scope_forbidden')
    adapter=build_adapter()
    with psycopg.connect(dsn,autocommit=True,connect_timeout=15) as connection:
        return sync_page(connection,adapter)
