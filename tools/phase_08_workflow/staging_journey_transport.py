"""Fixed, one-shot internal email fixtures for the authorized Google campaign.

Only staging Case 587 journals fixture receipts; real Inbox admission creates the
journey cases. No business facts, customers or production resources are changed.
A durable start receipt permanently prevents a blind retry after any outcome.
"""
import json
from urllib.parse import quote
from .outlook_adapter import OutlookExecutionAdapter, UrllibOutlookTransport, _graph_json_headers
from .outlook_inbound_runtime import configuration, enabled, validate_staging_database
from tools.phase_05_search.semantic_common import load_env_value

MAILBOX = 'serinya@whennaturecalls.nl'
BODIES = {
 'A': 'STAGING SYNTHETIC CLIENT REQUEST — Google integrated journey A only.\nWe request the Studio for a team workshop for 12 guests on 12 November 2026, 10:00–14:00 Europe/Amsterdam. Theatre-style seated setup. Please check room availability and advise on next steps. No booking or commercial commitment.',
 'B': 'STAGING SYNTHETIC CLIENT REQUEST — Google integrated journey B only.\nWe request the Studio with production coordination for a team workshop for 24 guests on 13 November 2026, 10:00–14:00 Europe/Amsterdam. Theatre-style seated setup and projection display requested. Load-in 09:00 and load-out 15:00 are requested and TBC. Please check availability, technical requirements and production responsibilities. No booking or commercial commitment.',
 'C-followup': 'STAGING SYNTHETIC CLIENT FOLLOW-UP — Google integrated journey C only.\nPlease change our existing Studio request to 24 guests on 15 November 2026, 11:00–16:00 Europe/Amsterdam. Theatre-style seated setup remains requested. Projection display is now requested and TBC. Please recheck availability and technical setup. No booking or commercial commitment.',
 'C': 'STAGING SYNTHETIC CLIENT REQUEST — Google integrated journey C only.\nWe request the Studio for a team workshop for 18 guests on 14 November 2026, 10:00–14:00 Europe/Amsterdam. Theatre-style seated setup. Date, count and scope may change later. Please check availability and advise on next steps. No booking or commercial commitment.',
}

def run(scenario):
 import psycopg
 if scenario not in BODIES: raise ValueError('synthetic_scenario_invalid')
 if load_env_value('APP_ENV')!='staging':raise ValueError('synthetic_staging_only')
 config,auth=configuration()
 if (config.environment!='staging' or config.mailbox.casefold()!=MAILBOX
     or config.allowed_mailbox.casefold()!=MAILBOX or MAILBOX not in config.allowed_senders
     or not all(enabled(k) for k in ('STAGING_ALLOW_REAL_OUTLOOK','STAGING_ALLOW_REAL_OUTLOOK_SEND','WORKFLOW_TEST_CONSOLE_ALLOW_REAL_PROVIDERS'))):
  raise ValueError('synthetic_journey_scope_or_gate_closed')
 dsn=load_env_value('DATABASE_URL') or '';validate_staging_database(dsn)
 key='google-cert-20261010:inbound-fixture:'+scenario
 body=BODIES[scenario]
 with psycopg.connect(dsn,autocommit=True,connect_timeout=15) as conn:
  with conn.transaction():
   conn.execute('select pg_advisory_xact_lock(hashtextextended(%s,0))',(key,))
   if conn.execute('select 1 from public.workflow_events where rental_case_id=587 and event_identity_key=%s',(key,)).fetchone():
    return {'replay_blocked':True,'provider_calls':0}
   row=conn.execute("select case_reference_code from public.rental_cases where id=587 for update").fetchone()
   if not row or row[0]!='RC-20261010150641817':raise ValueError('synthetic_controller_binding_invalid')
   reply_source=None
   if scenario=='C-followup':
    sources=conn.execute("select message_id,conversation_id,envelope from public.outlook_inbound_messages where rental_case_id=588 and association_status='resolved'").fetchall()
    sources=[r for r in sources if 'Google integrated journey C only.' in r[2].get('normalized_body','') and 'CLIENT REQUEST' in r[2].get('normalized_body','')]
    if len(sources)!=1 or sources[0][2].get('from_address','').casefold()!=MAILBOX:raise ValueError('synthetic_followup_binding_invalid')
    reply_source=sources[0]
   conn.execute("""insert into public.workflow_events(rental_case_id,event_type_code,source_type,source_reference,actor_type,actor_reference,occurred_at,recorded_at,event_identity_key,structured_payload)
    values(587,'synthetic_client_transport_started','staging_fixture',%s,'operator','authorized_google_staging_campaign',now(),now(),%s,%s::jsonb)""",
    (key,key,json.dumps({'scenario':scenario,'subject':config.new_enquiry_subject,'body':body,'recipient':MAILBOX,'retry_allowed':False})))
  adapter=OutlookExecutionAdapter(auth,UrllibOutlookTransport(),send_enabled=True)
  token=adapter._acquire_access_token()
  if token.result is not None or not token.access_token:raise ValueError('synthetic_auth_failed_no_retry')
  base=auth.graph_base_url+'/users/'+quote(MAILBOX,safe='')+'/messages'
  headers=_graph_json_headers(token.access_token);headers['Prefer']+=', outlook.body-content-type="text"'
  payload={'subject':config.new_enquiry_subject,'body':{'contentType':'Text','content':body},'toRecipients':[{'emailAddress':{'address':MAILBOX}}],'ccRecipients':[],'bccRecipients':[]}
  destination=base
  request_payload=payload
  if reply_source:
   destination=base+'/'+quote(reply_source[0],safe='')+'/createReply'
   request_payload={'message':{k:v for k,v in payload.items() if k!='subject'}}
  status,raw,_=adapter.transport.request(method='POST',url=destination,headers=headers,body=json.dumps(request_payload).encode(),timeout_seconds=auth.timeout_seconds)
  if not 200<=status<300:raise ValueError('synthetic_create_unknown_no_retry')
  draft=json.loads(raw);mid=draft.get('id')
  if not mid or draft.get('isDraft') is not True:raise ValueError('synthetic_create_shape_unknown_no_retry')
  status,raw,_=adapter.transport.request(method='GET',url=base+'/'+quote(mid,safe='')+'?$select=id,isDraft,subject,body,toRecipients,ccRecipients,bccRecipients,conversationId',headers=headers,body=None,timeout_seconds=auth.timeout_seconds)
  if status!=200:raise ValueError('synthetic_verify_unknown_no_retry')
  message=json.loads(raw)
  if (message.get('isDraft') is not True or message.get('subject') not in {payload['subject'],'RE: '+payload['subject'],'Re: '+payload['subject']} or message.get('body',{}).get('content')!=body
      or [r['emailAddress']['address'].casefold() for r in message.get('toRecipients',[])]!=[MAILBOX]
      or message.get('ccRecipients') or message.get('bccRecipients')):raise ValueError('synthetic_exact_content_binding_invalid')
  if reply_source and message.get('conversationId')!=reply_source[1]:raise ValueError('synthetic_followup_conversation_invalid')
  result=adapter._send_draft(access_token=token.access_token,message_id=mid,external_reference='outlook:message:'+mid)
  if result is not None:raise ValueError('synthetic_send_unknown_no_retry')
  proof={'scenario':scenario,'draft_id':mid,'conversation_id':message['conversationId'],'send_accepted':True,'final_client_send':False,'recipient':MAILBOX}
  conn.execute("""insert into public.workflow_events(rental_case_id,event_type_code,source_type,source_reference,actor_type,actor_reference,occurred_at,recorded_at,event_identity_key,structured_payload)
    values(587,'synthetic_client_transport_accepted','staging_fixture',%s,'operator','authorized_google_staging_campaign',now(),now(),%s,%s::jsonb)""",(key,key+':accepted',json.dumps(proof)))
  return proof
