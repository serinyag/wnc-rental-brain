"""Atomic mailbox page ingestion into existing staging case/observation services.

The mailbox advisory lock spans read and commit. Checkpoint and all local effects
commit together. A crash rolls back the whole page; replay is provider-ID based.
No outbound adapter or reasoning provider is invoked here.
"""
import json
import hashlib

def tombstone(value):
    return "sha256:"+hashlib.sha256(str(value).encode()).hexdigest()
from datetime import datetime, timezone
from .inbound_email import evidence_hash, timing_evidence_body
from .observation_types import InboundSourceRecordInput, CaseAssociationInput, CaseAssociationResult, StructuredObservationCandidate, StructuredObservationIngestionRequest
from .observations import ingest_structured_observations
from .inquiry_intake import apply_inquiry_intake
from .date_normalization import timing_components
from .test_console_service import TestConsoleService, TestConsoleConfig
from .supabase_observation_repository import SupabaseObservationRepository
from tools.runtime_environment import AppRuntimeConfig, AppEnvironment
from tools.phase_05_chunking.generate_pilot import _wrap_supabase_json_query, _drain_cursor_results


def connection_runner(connection):
    def run(sql, *, expect_json):
        cursor = connection.execute(_wrap_supabase_json_query(sql) if expect_json else sql)
        value = json.loads(cursor.fetchone()[0] or '[]') if expect_json else None
        _drain_cursor_results(cursor)
        return {'rows': value} if expect_json else None
    return run


def sync_page(connection, adapter, *, before_checkpoint=None):
    """One bounded page only. Caller must supply an idle, staging connection."""
    config = adapter.config
    config.validate()
    if not config.enabled: raise ValueError('inbound_gate_disabled')
    now = datetime.now(timezone.utc).isoformat()
    with connection.transaction():
        connection.execute("select pg_advisory_xact_lock(hashtextextended(%s,0))", ('outlook-inbound:' + config.mailbox.casefold(),))
        mailbox = config.mailbox.casefold()
        if config.environment=='production':
            config.production_contract.verify_database_marker(connection_runner(connection))
        checkpoint = connection.execute('select cursor,version,initial_since from public.outlook_inbound_checkpoints where mailbox=%s for update', (mailbox,)).fetchone()
        cursor = checkpoint[0] if checkpoint else adapter.initial_cursor()
        if checkpoint and checkpoint[2].isoformat() != datetime.fromisoformat(config.since.replace('Z','+00:00')).isoformat():
            raise ValueError('checkpoint_window_changed_requires_review')
        records, next_cursor, status = adapter.read_page(cursor)
        runner = connection_runner(connection)
        repository = SupabaseObservationRepository(query_runner=runner)
        service = TestConsoleService(query_runner=runner, config=TestConsoleConfig(runtime=AppRuntimeConfig(app_env=AppEnvironment(config.environment),production=config.production_contract), allow_real_providers=False))
        results, removed, duplicates = [], [], 0
        for raw in records:
            if not isinstance(raw, dict) or not isinstance(raw.get('id'),str) or not raw['id']: raise ValueError('missing_provider_identity')
            if '@removed' in raw:
                removed.append(raw['id']); continue  # Loss from Inbox is not business deletion.
            existing = connection.execute('select source_record_id,rental_case_id,association_status from public.outlook_inbound_messages where mailbox=%s and message_id in (%s,%s)',(mailbox,raw['id'],tombstone(raw['id']))).fetchone()
            if existing:
                duplicates += 1
                results.append({'source_id':existing[0], 'case_id':existing[1], 'association_status':existing[2], 'duplicate':True})
                continue
            # Delta supplies metadata only. Never fetch unrelated mailbox bodies.
            sender = raw.get('from', {}).get('emailAddress', {}).get('address', '').casefold()
            sender_role = config.production_contract.manifest['outlook']['sender_roles'].get(sender,'unknown') if config.environment=='production' else 'client'
            recipients = [r.get('emailAddress', {}).get('address', '').casefold() for r in raw.get('toRecipients', [])]
            conversation = raw.get('conversationId')
            bound = connection.execute('select rental_case_id from public.outlook_inbound_conversations where mailbox=%s and conversation_id in (%s,%s)', (mailbox,conversation,tombstone(conversation))).fetchone()
            synthetic_subject = config.environment=='production' or config.new_enquiry_subject in str(raw.get('subject',''))
            if sender not in config.allowed_senders or mailbox not in recipients or not (bound or synthetic_subject):
                results.append({'source_id':None,'case_id':None,'association_status':'out_of_scope','duplicate':False})
                continue
            if 'body' not in raw:
                message_id = raw['id']
                raw = adapter.read_message(message_id)
                if raw.get('id') != message_id or raw.get('conversationId') != conversation:
                    raise ValueError('inbound_message_identity_changed')
                if raw.get('from', {}).get('emailAddress', {}).get('address', '').casefold() != sender:
                    raise ValueError('inbound_sender_changed')
            env = adapter.envelope(raw)
            if datetime.fromisoformat(env.received_at.replace('Z','+00:00')) < datetime.fromisoformat(config.since.replace('Z','+00:00')):
                raise ValueError('provider_returned_before_authorized_window')
            bound = connection.execute('select rental_case_id from public.outlook_inbound_conversations where mailbox=%s and conversation_id in (%s,%s)',(mailbox,env.provider_conversation_id,tombstone(env.provider_conversation_id))).fetchone()
            case_id = None
            # Synthetic admission is explicit and separate from conversation routing.
            admitted = env.from_address in config.allowed_senders and mailbox in env.to_addresses
            if not admitted:
                association, basis = 'out_of_scope', 'sender_or_recipient_not_in_synthetic_scope'
            elif bound:
                if config.environment=='production' and not connection.execute('select is_active from public.rental_cases where id=%s',(bound[0],)).fetchone()[0]:
                    raise ValueError('inactive_case_requires_association_review')
                case_id, association, basis = bound[0], 'resolved', 'exact_provider_conversation'
            elif sender_role=='client' and (config.environment=='production' or env.subject == config.new_enquiry_subject) and not env.reply_references:
                # Reuse the application's normal synthetic staging creation path,
                # never the test-only source injection path. It starts revision 0,
                # custom_scope/unknown; it does not infer business facts.
                report = service.create_test_case(label=('Production Outlook enquiry' if config.environment=='production' else 'Real Outlook inbound synthetic enquiry'), client_label=None,
                    contact_email=env.from_address, event_reference='outlook-inbound:' + env.identity)
                if not report.success: raise ValueError('case_creation_failed')
                reference = next(line.split(': ',1)[1] for line in report.lines if line.startswith('RentalCase: '))
                case_id = connection.execute('select id from public.rental_cases where case_reference_code=%s',(reference,)).fetchone()[0]
                connection.execute('insert into public.outlook_inbound_conversations(mailbox,conversation_id,rental_case_id) values(%s,%s,%s)',(mailbox,env.provider_conversation_id,case_id))
                association, basis = 'resolved', ('explicit_pilot_sender_new_enquiry_admission' if config.environment=='production' else 'explicit_synthetic_new_enquiry_admission')
            else:
                association, basis = 'needs_review', 'unbound_conversation_no_safe_new_enquiry_admission'
            candidates = ()
            timing_body = timing_evidence_body(env)
            timing = timing_components(timing_body) if case_id and sender_role=='client' else None
            if timing:
                candidates = (StructuredObservationCandidate(reported_field_code='active_event_window', observation_type='fact_candidate',
                    claim_kind='new_information', candidate_value_payload=timing,
                    source_evidence_reference='outlook_message:' + env.provider_message_id, asserted_by_party_type='client',
                    asserted_by_reference=env.from_address, source_excerpt=timing_body[:500], extraction_confidence=1.0),)
            source = InboundSourceRecordInput(source_system_code='email',source_record_type='message',occurred_at=env.received_at,
                received_at=env.received_at,dedupe_key='outlook:' + env.identity,source_hash='sha256:' + evidence_hash(raw),
                external_source_id=env.provider_message_id,conversation_reference=env.provider_conversation_id,
                sender_actor_type=sender_role,sender_actor_reference=env.from_address,source_location_reference='outlook-inbox:' + mailbox,
                evidence_excerpt=env.normalized_body[:500] or env.subject or '(empty email)')
            if candidates:
                ingested = ingest_structured_observations(request=StructuredObservationIngestionRequest(source_record=source,
                    case_association=CaseAssociationInput(rental_case_id=case_id),observations=candidates), repository=repository,now=lambda:now)
                sid = ingested.source_record.inbound_source_record_id
            else:
                record = repository.create_source_record(source_record_input=source,
                    case_association=CaseAssociationResult(status='resolved' if case_id else 'case_association_required',
                        rental_case_id=case_id, association_basis=basis),created_at=now)
                sid = record.inbound_source_record_id
            connection.execute('''insert into public.outlook_inbound_messages(mailbox,message_id,conversation_id,source_record_id,rental_case_id,
                association_status,association_basis,raw_provider_payload,envelope,source_hash) values(%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s)''',
                (mailbox,env.provider_message_id,env.provider_conversation_id,sid,case_id,association,basis,json.dumps(raw),json.dumps(env.payload()),evidence_hash(raw)))
            if case_id:
                repository.create_workflow_event(rental_case_id=case_id,event_type_code='outlook_inbound_evidence_recorded',source_type='outlook_inbound',
                    source_reference='inbound_source_record:' + str(sid),actor_type='system',actor_reference='outlook_inbound',occurred_at=env.received_at,
                    event_identity_key='outlook-inbound:' + env.identity,structured_payload={'inbound_source_record_id':sid,'provider_message_id':env.provider_message_id,
                        'conversation_id':env.provider_conversation_id,'source_hash':evidence_hash(raw),'association_basis':basis,
                        'source_label':'Real Outlook Inbox', 'sender':env.from_address, 'subject':env.subject,
                        'body':env.normalized_body, 'external_test_reference':None})
                intake = apply_inquiry_intake(repository,rental_case_id=case_id,actor_reference='outlook_inbound',actor_type='system',now=lambda:now)
                if intake.failure_codes: raise ValueError('governed_intake_failed')
            results.append({'source_id':sid,'case_id':case_id,'association_status':association,'duplicate':False})
        if before_checkpoint: before_checkpoint()  # Fault injection in provider-free tests only.
        version = (checkpoint[1] if checkpoint else 0) + 1
        connection.execute('''insert into public.outlook_inbound_checkpoints(mailbox,cursor,initial_since,version,status,last_successful_sync_at)
            values(%s,%s,%s,%s,%s,%s) on conflict(mailbox) do update set cursor=excluded.cursor,version=excluded.version,
            status=excluded.status,last_successful_sync_at=excluded.last_successful_sync_at''',(mailbox,next_cursor,config.since,version,status,now))
        connection.execute('insert into public.outlook_inbound_sync_events(mailbox,checkpoint_version,record_count,duplicate_count,removed_message_ids) values(%s,%s,%s,%s,%s::jsonb)',(mailbox,version,len(records),duplicates,json.dumps(removed)))
    return {'results':results,'checkpoint_version':version,'checkpoint_status':status,'outbound_calls':0}


def reprocess_quarantined_reply(connection, config, message_id):
    """Append corrected timing evidence through existing governance, no new source.

    Explicit staging remediation only; preserves the original quarantined
    observation, provider payload, checkpoint and all message identities.
    """
    from .inbound_email import InboundEmailEnvelope
    from .observations import _ingest_one_candidate
    config.validate()
    if not config.enabled: raise ValueError('inbound_gate_disabled')
    with connection.transaction():
        mailbox=config.mailbox.casefold()
        connection.execute('select pg_advisory_xact_lock(hashtextextended(%s,0))',('outlook-inbound:'+mailbox,))
        row=connection.execute('''select m.source_record_id,m.rental_case_id,m.envelope,m.raw_provider_payload,m.source_hash
            from public.outlook_inbound_messages m join public.outlook_inbound_conversations c
            on c.mailbox=m.mailbox and c.conversation_id=m.conversation_id and c.rental_case_id=m.rental_case_id
            where m.mailbox=%s and m.message_id=%s and m.association_status='resolved' ''',(mailbox,message_id)).fetchone()
        if not row: raise ValueError('reply_reprocessing_binding_missing')
        sid,cid,payload,raw,stored_hash=row
        if evidence_hash(raw)!=stored_hash: raise ValueError('reply_reprocessing_evidence_changed')
        env=InboundEmailEnvelope(**payload)
        if env.from_address not in config.allowed_senders or mailbox not in env.to_addresses:
            raise ValueError('reply_reprocessing_scope_forbidden')
        body=timing_evidence_body(env)
        if body==env.normalized_body: raise ValueError('reply_reprocessing_boundary_missing')
        runner=connection_runner(connection);repository=SupabaseObservationRepository(query_runner=runner)
        existing=repository.list_observations_for_source(sid)
        if not any(o.status=='quarantined' and o.candidate_value_payload=={'normalization_error':'multiple_calendar_dates_require_clarification'} for o in existing):
            raise ValueError('reply_reprocessing_quarantine_missing')
        timing=timing_components(body)
        if not timing or 'normalization_error' in timing: raise ValueError('reply_reprocessing_still_ambiguous')
        source=next(s for s in repository.list_source_records_for_case(cid) if s.inbound_source_record_id==sid)
        now=datetime.now(timezone.utc).isoformat()
        candidate=StructuredObservationCandidate(reported_field_code='active_event_window',observation_type='fact_candidate',
            claim_kind='new_information',candidate_value_payload=timing,source_evidence_reference='outlook_message:'+message_id,
            asserted_by_party_type='client',asserted_by_reference=env.from_address,source_excerpt=body[:500],extraction_confidence=1.0)
        result=_ingest_one_candidate(candidate=candidate,source_record=source,
            case_association=CaseAssociationResult(status='resolved',rental_case_id=cid,association_basis='exact_provider_conversation'),
            case_snapshot=repository.load_case_snapshot(cid),repository=repository,created_at=now)
        if result.observation.status!='validated': raise ValueError('reply_reprocessing_not_validated')
        intake=apply_inquiry_intake(repository,rental_case_id=cid,actor_reference='outlook_inbound_reply_reprocessing',actor_type='system',now=lambda:now)
        if intake.failure_codes: raise ValueError('governed_intake_failed')
        return {'case_id':cid,'source_id':sid,'observation_id':result.observation.inbound_observation_id,
                'original_quarantine_preserved':True,'provider_calls':0}
