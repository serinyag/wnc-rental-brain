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


def receipt():
    """Read-only exact approved Case 586 send/Inbox correlation after gate closure.

    No ingestion, retry, approval mutation or inferred receipt. Both provider
    copies must match the immutable approved content and Internet message ID.
    """
    import psycopg
    from urllib.parse import urlencode
    from .outlook_adapter import OutlookAdapterConfig
    from .outlook_inbound_runtime import ReadOnlyGraphTransport
    if (load_env_value('APP_ENV') != 'staging' or enabled('STAGING_ALLOW_REAL_OUTLOOK_SEND')
            or not enabled('STAGING_ALLOW_REAL_OUTLOOK') or not enabled('WORKFLOW_TEST_CONSOLE_ALLOW_REAL_PROVIDERS')):
        raise ValueError('receipt_read_scope_forbidden')
    dsn=load_env_value('DATABASE_URL') or ''; validate_staging_database(dsn)
    with psycopg.connect(dsn) as conn:
        conn.execute('set transaction read only')
        row=conn.execute('''select t.external_reference,r.subject,r.body_text,r.recipient_email,t.started_at
            from public.workflow_execution_attempts t
            join public.inquiry_response_draft_revisions r on r.workflow_action_id=t.workflow_action_id
            join public.rental_case_approval_requests a on a.id=r.approval_request_id
            where t.rental_case_id=586 and t.workflow_action_id=1640 and t.id=29
            and r.id=387 and r.is_current and a.id=466 and a.status='approved'
            and t.failure_code='adapter_outcome_ambiguous' and t.retry_eligible=false''').fetchone()
        if not row or row[3].casefold()!=MAILBOX or not row[0].startswith('outlook:message:'):
            raise ValueError('receipt_read_exact_lineage_missing')
    external,subject,body,recipient,started=row
    auth=OutlookAdapterConfig.from_env()
    if (auth.sender_mailbox.casefold()!=MAILBOX or auth.graph_base_url!='https://graph.microsoft.com/v1.0'
            or auth.authority_base_url!='https://login.microsoftonline.com'):
        raise ValueError('receipt_read_provider_scope_forbidden')
    transport=ReadOnlyGraphTransport();adapter=OutlookExecutionAdapter(auth,transport,send_enabled=False)
    token=adapter._acquire_access_token()
    if token.result is not None or not token.access_token:raise ValueError('receipt_read_auth_failed')
    headers=_graph_json_headers(token.access_token);headers['Prefer']+=', outlook.body-content-type="text"'
    base=auth.graph_base_url+'/users/'+quote(MAILBOX,safe='')
    def get(suffix):
        code,raw,_=transport.request(method='GET',url=base+suffix,headers=headers,body=None,timeout_seconds=auth.timeout_seconds)
        if code!=200:raise ValueError('receipt_read_provider_failed:'+str(code))
        return json.loads(raw)
    mid=external.removeprefix('outlook:message:')
    fields='id,internetMessageId,isDraft,sentDateTime,receivedDateTime,from,toRecipients,ccRecipients,bccRecipients,subject,body,conversationId'
    sent=get('/messages/'+quote(mid,safe='')+'?'+urlencode({'$select':fields}))
    def exact(m):
        return (m.get('isDraft') is False and m.get('subject')==subject
            and [r['emailAddress']['address'].casefold() for r in m.get('toRecipients',[])]==[MAILBOX]
            and not m.get('ccRecipients') and not m.get('bccRecipients')
            and m.get('body',{}).get('content','').replace('\r\n','\n').strip()==body.replace('\r\n','\n').strip())
    if sent.get('id')!=mid or not exact(sent) or not sent.get('internetMessageId') or not sent.get('sentDateTime'):
        raise ValueError('receipt_read_sent_copy_inconclusive')
    iid=sent['internetMessageId'].replace("'","''")
    inbox=get('/mailFolders/inbox/messages?'+urlencode({'$select':fields,'$top':2,'$filter':"internetMessageId eq '"+iid+"'"}))
    copies=inbox.get('value',[])
    if len(copies)!=1 or inbox.get('@odata.nextLink') or not exact(copies[0]) or not copies[0].get('receivedDateTime'):
        raise ValueError('receipt_read_inbox_copy_inconclusive')
    received=copies[0]
    from datetime import datetime
    if datetime.fromisoformat(received['receivedDateTime'].replace('Z','+00:00')) < started:
        raise ValueError('receipt_predates_exact_attempt')
    if received['internetMessageId']!=sent['internetMessageId'] or sent.get('conversationId')!=received.get('conversationId'):
        raise ValueError('receipt_read_message_correlation_mismatch')
    return {'provider_reads':2,'provider_mutations':0,'case_id':586,'action_id':1640,'attempt_id':29,
        'revision_id':387,'approval_id':466,'recipient':recipient,'subject':subject,'exact_content_match':True,
        'sent_message_id':mid,'inbox_message_id':received['id'],'internet_message_id':sent['internetMessageId'],
        'sent_at':sent['sentDateTime'],'received_at':received['receivedDateTime'],
        'conversation_id':sent.get('conversationId'),'receipt_verified':True}
