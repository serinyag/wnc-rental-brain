"""Single-use synthetic transport fixture for the authorized Case 586 journey.

No case truth is written here. The self-addressed reply must arrive through the
normal Inbox ingestion path. A durable start event precedes any Graph mutation;
even a crash or ambiguous create/send outcome permanently blocks replay.
"""
import json
from urllib.parse import quote
from .outlook_adapter import OutlookExecutionAdapter, UrllibOutlookTransport, _graph_json_headers
from .outlook_inbound_runtime import configuration, enabled, validate_staging_database
from tools.phase_05_search.semantic_common import load_env_value

BODY = ('STAGING SYNTHETIC CLIENT EVIDENCE — Case 586 only.\n\n'
        'Thanks. We would prefer theatre-style seated seating for our existing 24 guests '
        'in the Studio. All other details of our synthetic enquiry remain unchanged.\n\n'
        'Synthetic client')
MAILBOX = 'serinya@whennaturecalls.nl'
SOURCE = 3105
KEY = 'case586:synthetic-layout-reply:v1'


def validate_message(message, conversation, *, draft=False):
    recipients = [r.get('emailAddress', {}).get('address', '').casefold() for r in message.get('toRecipients', [])]
    if (message.get('conversationId') != conversation or recipients != [MAILBOX]
            or message.get('ccRecipients') or message.get('bccRecipients')
            or 'SYNTHETIC TEST' not in message.get('subject', '')
            or (draft and (message.get('isDraft') is not True or message.get('body', {}).get('content') != BODY))):
        raise ValueError('synthetic_reply_provider_binding_mismatch')
    if not draft and message.get('from', {}).get('emailAddress', {}).get('address', '').casefold() != MAILBOX:
        raise ValueError('synthetic_reply_source_sender_mismatch')


def run():
    import psycopg
    config, auth = configuration()
    if config.mailbox.casefold() != MAILBOX or not enabled('STAGING_ALLOW_REAL_OUTLOOK_SEND'):
        raise ValueError('synthetic_reply_gate_closed')
    dsn = load_env_value('DATABASE_URL') or ''
    validate_staging_database(dsn)
    with psycopg.connect(dsn, autocommit=True) as conn:
        with conn.transaction():
            conn.execute("select pg_advisory_xact_lock(hashtextextended(%s,0))", (KEY,))
            prior = conn.execute('select structured_payload from public.workflow_events where rental_case_id=586 and event_identity_key=%s', (KEY,)).fetchone()
            if prior:
                return {'replay_blocked': True, 'prior': prior[0], 'provider_calls': 0}
            row = conn.execute('''select m.message_id,m.conversation_id,c.case_revision from public.outlook_inbound_messages m
                join public.rental_cases c on c.id=m.rental_case_id where m.source_record_id=%s and m.rental_case_id=586
                and m.mailbox=%s and m.association_status='resolved' ''', (SOURCE, MAILBOX)).fetchone()
            if not row or row[2] != 5:
                raise ValueError('synthetic_reply_case_binding_mismatch')
            source, conversation, revision = row
            conn.execute('''insert into public.workflow_events(rental_case_id,event_type_code,source_type,source_reference,
                actor_type,actor_reference,occurred_at,recorded_at,event_identity_key,structured_payload)
                values(586,'synthetic_client_transport_started','staging_fixture',%s,'operator','authorized_synthetic_journey',
                now(),now(),%s,%s::jsonb)''', ('inbound_source_record:3105', KEY,
                json.dumps({'source':source,'conversation':conversation,'case_revision':revision,'body':BODY,'retry_allowed':False})))
        adapter = OutlookExecutionAdapter(auth, UrllibOutlookTransport(), send_enabled=True)
        token = adapter._acquire_access_token()
        if token.result is not None or not token.access_token:
            raise ValueError('synthetic_reply_token_failed_no_retry')
        base = auth.graph_base_url + '/users/' + quote(MAILBOX, safe='') + '/messages/'
        headers = _graph_json_headers(token.access_token)
        headers['Prefer'] += ', outlook.body-content-type="text"'
        def request(method, suffix, payload=None):
            status, raw, _ = adapter.transport.request(method=method,url=base+suffix,headers=headers,
                body=None if payload is None else json.dumps(payload).encode(),timeout_seconds=auth.timeout_seconds)
            if not 200 <= status < 300:
                raise ValueError('synthetic_reply_provider_error_no_retry:' + str(status))
            return json.loads(raw) if raw else {}
        original = request('GET', quote(source, safe='') + '?$select=id,conversationId,from,toRecipients,ccRecipients,bccRecipients,subject')
        validate_message(original, conversation)
        draft = request('POST', quote(source, safe='')+'/createReply', {'message':{'body':{'contentType':'Text','content':BODY},
            'toRecipients':[{'emailAddress':{'address':MAILBOX}}],'ccRecipients':[],'bccRecipients':[]}})
        mid = draft.get('id')
        if not mid: raise ValueError('synthetic_reply_missing_draft_no_retry')
        current = request('GET', quote(mid,safe='')+'?$select=id,conversationId,toRecipients,ccRecipients,bccRecipients,subject,isDraft,body')
        validate_message(current, conversation, draft=True)
        result = adapter._send_draft(access_token=token.access_token,message_id=mid,external_reference='outlook:message:'+mid)
        if result is not None:
            raise ValueError('synthetic_reply_send_not_confirmed_no_retry')
        proof = {'draft_id':mid,'conversation_id':conversation,'source_record_id':SOURCE,'send_accepted':True,'final_client_send':False}
        conn.execute('''insert into public.workflow_events(rental_case_id,event_type_code,source_type,source_reference,
            actor_type,actor_reference,occurred_at,recorded_at,event_identity_key,structured_payload)
            values(586,'synthetic_client_transport_accepted','staging_fixture',%s,'operator','authorized_synthetic_journey',now(),now(),%s,%s::jsonb)''',
            ('outlook_message:'+mid,KEY+':accepted',json.dumps(proof)))
        return proof
