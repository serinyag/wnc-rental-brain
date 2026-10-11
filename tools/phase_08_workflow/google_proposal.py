"""Client-safe, outbound proposal projection. The action journal owns identity.

Provider edits never establish facts. Requested details are distinct from WNC confirmations.
The source Word template supplies the layout; its example prices/statuses do not.
"""
from __future__ import annotations

import io
import json
from datetime import datetime, timezone
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from .asana_projection import digest
from .contracts import WorkflowAction
from .working_proposal import ROOT, SECTIONS, build_rental_working_proposal

ADAPTER = 'google_proposal'
VERSION = 'google_proposal_v1'
MANUAL_EDIT_POLICY = 'PROPOSAL_DOC_CANONICAL_PROJECTION_WITH_MANUAL_DRIFT_REVIEW'
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
# Explicit public-field boundary, rather than serializing the internal view.
PUBLIC_FIELDS = {
    'requested_rental_scope', 'event_start', 'event_end', 'event_type', 'guest_count',
    'primary_contact', 'event_schedule', 'production_scope', 'production_schedule',
    'load_in_schedule', 'load_out_schedule', 'event_day_contact', 'event_days',
    'production_days', 'production_dates', 'production_start', 'production_end',
    'load_in', 'load_out', 'build_up', 'breakdown', 'layout_requirements',
    'technical_requirements', 'catering_requirements', 'drink_package',
    'catering_arrangement', 'facilitator_arrangement', 'staffing_requirements',
    'wnc_responsibilities', 'client_responsibilities',
}


def attempts(snapshot):
    return sorted((a for a in snapshot.execution_attempts if a.adapter_code == ADAPTER),
                  key=lambda a: a.execution_attempt_id)


def binding(snapshot):
    result = None
    for attempt in attempts(snapshot):
        if isinstance(attempt.response_snapshot, dict) and attempt.response_snapshot.get('binding'):
            result = attempt.response_snapshot['binding']
        recovered = reconciled_attempts(snapshot).get(attempt.execution_attempt_id)
        if recovered:
            result = recovered['binding']
    return result


def reconciled_attempts(snapshot):
    """Separate evidence records preserve the original failed attempt unchanged."""
    result = {}
    for event in snapshot.workflow_events:
        if event.event_type_code != 'google_proposal_reconciled': continue
        p = event.structured_payload
        a = next((a for a in attempts(snapshot) if a.execution_attempt_id == p.get('execution_attempt_id')), None)
        original = a.response_snapshot.get('binding') if a and isinstance(a.response_snapshot, dict) else None
        b = p.get('binding')
        if (a and a.status == 'failed' and original and isinstance(b, dict)
                and p.get('workflow_action_id') == a.workflow_action_id
                and p.get('status') == 'MATCHES_PROJECTION' and p.get('provider_mutations') == 0
                and p.get('business_truth_changed') is False
                and all(b.get(k) == original.get(k) for k in (
                    'rental_case_id','document_id','file_id','folder_id','provider_identity','proposal_identity'))
                and b.get('document_fingerprint') and b.get('projection_hash')):
            result[a.execution_attempt_id] = p
    return result


def unresolved_attempts(snapshot):
    recovered = reconciled_attempts(snapshot)
    return [a for a in attempts(snapshot) if a.status == 'started' or
            (a.status != 'succeeded' and not a.retry_eligible and a.execution_attempt_id not in recovered)]


def identity(snapshot):
    return digest({'case_uuid': snapshot.rental_case.rental_case_uuid, 'purpose': VERSION})


def display(value):
    """Human labels only; presentation never establishes confirmation."""
    if value is None or isinstance(value, str) and value in ('unknown', 'under_consideration'):
        return 'To be confirmed'
    if isinstance(value, dict):
        if value.get('style'):
            style = display(value['style'])
            return style.capitalize() + '-style seating' if value.get('configuration_type') == 'seated' else style.capitalize()
        dates = value.get('dates', [value['date']] if value.get('date') else [])
        parts = [display(d) for d in dates]
        time = value.get('time') or value.get('start')
        if time: parts.append(str(time) + ('–' + str(value['end']) if value.get('end') else ''))
        if parts: return ', '.join(parts)
        return '; '.join(k.replace('_', ' ').capitalize()+': '+display(v) for k,v in sorted(value.items())
            if k not in {'status', 'timezone', 'configuration_type', 'source_reference', 'evidence_reference', 'reason', 'authority_basis', 'internal_notes'}) or 'To be confirmed'
    if isinstance(value, list):
        return ', '.join(display(v) for v in value) or 'To be confirmed'
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value)
            if parsed.tzinfo:
                from zoneinfo import ZoneInfo
                parsed = parsed.astimezone(ZoneInfo('Europe/Amsterdam'))
                return f'{parsed.day} {parsed:%B %Y}, {parsed:%H:%M}'
            if len(value) == 10: return f'{parsed.day} {parsed:%B %Y}'
        except ValueError: pass
        return {'studio_space': 'Studio', 'entire_venue': 'Entire venue',
            'projection_display': 'Projection', 'production_coordination': 'Production coordination',
            'full_production': 'Full production', 'audio_playback': 'Audio playback'}.get(value,
            value.replace('_', ' ').replace('\r', ' ').replace('\n', ' '))
    return str(value)


def _local(value):
    from zoneinfo import ZoneInfo
    try:
        parsed = datetime.fromisoformat(value)
        return parsed.astimezone(ZoneInfo('Europe/Amsterdam')) if parsed.tzinfo else None
    except (ValueError, TypeError): return None


def _confirmation(result):
    # Keep every governed assertion's subject, polarity and exact window.
    return result['assertion'].replace(' (Europe/Amsterdam)', '')


def approved_prices(snapshot):
    """Only approved active commercial decisions; no facts or proposed amounts.

    Existing decision payloads remain intact. No VAT, currency, totals or quote
    validity are inferred from the exemplary Word template.
    """
    approvals = {a.approval_request_id: a for a in snapshot.approval_requests}
    lines = []
    for decision in snapshot.case_decisions:
        approval = approvals.get(decision.approval_request_id)
        if (decision.status == 'active' and decision.domain_code == 'commercial'
                and decision.evidence_reference and approval and approval.status == 'approved'
                and approval.target_entity_type == 'case_decision'
                and approval.target_entity_id == decision.case_decision_id
                and approval.rental_case_id == snapshot.rental_case.rental_case_id
                and decision.effective_value_payload is not None):
            payload = decision.effective_value_payload
            if isinstance(payload, dict):
                # Approval provenance/reasons stay internal even when approved.
                payload = {k: v for k, v in payload.items() if k in {
                    'booking_fee', 'amount', 'currency', 'vat_rate', 'discount', 'discount_percent',
                    'rental_fee', 'production_fee', 'total', 'fee', 'rate', 'unit', 'quantity'}}
                if not payload: continue
            elif not isinstance(payload, (int, float)) or isinstance(payload, bool):
                continue
            lines.append(decision.scope_description + ': ' + display(payload))
    return sorted(lines)


def build_projection(snapshot, *, folder_id, provider_identity):
    model = build_rental_working_proposal(snapshot)
    if model['template_review_required']:
        raise ValueError('proposal_template_review_required')
    existing = binding(snapshot)
    # Layout identity persists even if a follow-up changes rental scope.
    template = existing['template'] if existing else model['template']
    rows = {r['key']: r for r in model['details'] if r['key'] in PUBLIC_FIELDS}
    known = {k: r for k, r in rows.items() if r['value'] is not None
             and r['value'] not in ('unknown', 'under_consideration', 'none')
             and r['value'] != ['none'] and display(r['value']) != 'To be confirmed'}
    unresolved_labels = {'event_schedule': 'Remaining event-day schedule details',
        'production_schedule': 'Production schedule', 'load_in_schedule': 'Load-in timing',
        'load_out_schedule': 'Load-out timing', 'event_start': 'Event date and start time',
        'event_end': 'Event end time'}
    unresolved = [unresolved_labels.get(k, r['label']) for k, r in rows.items() if k not in known and r['status'] != 'Not applicable']
    start, end = (_local(rows[k]['value']) for k in ('event_start', 'event_end'))
    event = []
    if start:
        date = f'{start.day} {start:%B %Y}'
        if end and end.date() != start.date(): date += f'–{end.day} {end:%B %Y}'
        event.append('Date: ' + date)
        event.append('Time: ' + (f'{start:%H:%M}–{end:%H:%M}' if end and end.date() == start.date()
            else display(rows['event_start']['value']) + (' – ' + display(rows['event_end']['value']) if end else '')))
    labels = {'guest_count': 'Guests', 'event_type': 'Event format', 'requested_rental_scope': 'Space', 'layout_requirements': 'Room setup'}
    for key, label in labels.items():
        if key in known: event.append(label + ': ' + display(known[key]['value']))
    technical, team = [], []
    for key, row in known.items():
        if key in labels or key in {'event_start', 'event_end'}: continue
        label, value = row['label'], display(row['value'])
        if key == 'production_scope':
            label, value = 'Production coordination' if row['value'] == 'production_coordination' else 'Production scope', 'Requested, scope to be confirmed'
            unresolved.append('Final production coordination scope' if row['value'] == 'production_coordination' else 'Final production scope')
        elif key in {'load_in_schedule', 'load_in', 'load_out_schedule', 'load_out'}:
            label = 'Load-in' if 'in' in key else 'Load-out'
            raw = row['value']
            time = (raw.get('time') or raw.get('start')) if isinstance(raw, dict) else None
            value = 'Requested ' + ('from ' if label == 'Load-in' else 'until ') + (str(time) if time else value)
            if isinstance(raw, dict) and raw.get('date') and (not start or raw['date'] != start.date().isoformat()):
                value += ' on ' + display(raw['date'])
            if isinstance(raw, dict) and raw.get('timezone') not in {None, 'Europe/Amsterdam'}:
                value += ' (' + str(raw['timezone']) + ')' 
            unresolved.append(label + ' timing')
        if row['section'] == 'Team & Responsibilities': team.append(label + ': ' + value)
        elif key in {'primary_contact', 'event_schedule', 'event_days'}: event.append(label + ': ' + value)
        else: technical.append(label + ': ' + value)
    from .operational_resolution import client_results
    governed_results = client_results(snapshot)
    confirmations = [_confirmation(result) for result in governed_results]
    if 'technical_requirements' in known:
        requested_technical = known['technical_requirements']['value']
        requested_technical = requested_technical if isinstance(requested_technical, list) else [requested_technical]
        feasible_subjects = {r.get('subject') for r in governed_results if r['outcome'] == 'FEASIBLE'}
        if not all(isinstance(subject, str) and subject in feasible_subjects for subject in requested_technical):
            unresolved.append('Technical feasibility')
    prices = approved_prices(snapshot)
    if not prices: unresolved.append('Pricing and applicable fees')
    sections = {
        'Event Overview': '\n'.join(event) or 'Event details are still to confirm.',
        'Current Scope': '\n'.join(technical),
        'Financial Summary': '\n'.join(prices) or 'To be confirmed',
        'Confirmed / Still TBC': '\n'.join('• ' + text for text in confirmations),
        'Working Timeline': '\n'.join('• ' + text for text in dict.fromkeys(unresolved)),
        'Team & Responsibilities': '\n'.join(team),
        'Next Steps': "We'll confirm the remaining operational details and pricing before the proposal is finalized." if unresolved else
            'Review the current scope and confirmed details before finalizing the proposal.',
    }
    headings = {'Event Overview': 'Event Details', 'Current Scope': 'Production & Technical' if technical else 'Requested Details',
        'Financial Summary': 'Pricing', 'Confirmed / Still TBC': 'Confirmed So Far' if confirmations else 'Confirmation Status',
        'Working Timeline': 'Still to Confirm', 'Team & Responsibilities': 'Team & Responsibilities' if team else 'Working Proposal Status',
        'Next Steps': 'Next Steps'}
    subtitle = display(known['event_type']['value']).capitalize() if 'event_type' in known else 'Rental event'
    if start: subtitle += f' | {start.day} {start:%B %Y}'
    case = snapshot.rental_case
    status_note = 'Working proposal: this document reflects the current event scope and confirmed details.'
    status_note += (' Booking confirmation is recorded separately.' if case.lifecycle_state in {
        'confirmed_pre_event', 'event_ready', 'event_in_progress', 'close_out_in_progress'} else
        ' It does not constitute a confirmed booking.')
    value = {'version': VERSION, 'rental_case_id': case.rental_case_id,
        'proposal_identity': identity(snapshot), 'source_case_revision': case.case_revision,
        'folder_id': folder_id, 'provider_identity': provider_identity, 'template': template,
        'title': 'Working Proposal\n' + subtitle, 'client': display(case.client_account_ref),
        'sections': sections, 'headings': headings,
        'status_note': status_note, 'manual_edit_policy': MANUAL_EDIT_POLICY}
    # Content hash ignores unrelated revisions, while the execution envelope is
    # still bound to the exact current case revision.
    value['projection_hash'] = digest({k: v for k, v in value.items() if k != 'source_case_revision'})
    return value


def render_template(plan):
    """Render human sections using the bound source's page setup and styles.

    This changes presentation only. Native updates retain the existing strict
    layout/fingerprint review fence; incompatible existing layouts fail closed.
    """
    path = ROOT / plan['template']['path']
    raw = path.read_bytes()
    from hashlib import sha256
    if sha256(raw).hexdigest() != plan['template']['sha256']:
        raise ValueError('proposal_template_changed')
    with ZipFile(io.BytesIO(raw)) as archive:
        tree = ET.fromstring(archive.read('word/document.xml'))
        body = tree.find(W+'body')
        setup = body.find(W+'sectPr')
        for child in list(body): body.remove(child)
        def paragraph(text, style=None):
            p = ET.Element(W+'p')
            properties = ET.SubElement(p, W+'pPr')
            if style: ET.SubElement(properties, W+'pStyle', {W+'val': style})
            ET.SubElement(properties, W+'spacing', {W+'before': '160' if style == 'Heading1' else '0', W+'after': '70'})
            if style in {'Heading1', 'Title', 'Subtitle'}: ET.SubElement(properties, W+'keepNext')
            _replace_paragraph(p, text)
            rp = ET.Element(W+'rPr')
            p.find(W+'r').insert(0, rp)
            ET.SubElement(rp, W+'rFonts', {W+'ascii': 'Arial', W+'hAnsi': 'Arial'})
            ET.SubElement(rp, W+'color', {W+'val': '000000'})
            ET.SubElement(rp, W+'sz', {W+'val': '44' if style == 'Title' else '28' if style == 'Heading1' else '24' if style == 'Subtitle' else '21'})
            return p
        for index, line in enumerate(plan['title'].splitlines()):
            body.append(paragraph(line, 'Title' if index == 0 else 'Subtitle'))
        body.append(paragraph('Client: ' + plan['client']))
        order = ('Event Overview', 'Current Scope', 'Team & Responsibilities',
                 'Confirmed / Still TBC', 'Working Timeline', 'Financial Summary', 'Next Steps')
        for name in order:
            content = plan['sections'].get(name, '')
            if not content: continue
            body.append(paragraph(plan.get('headings', {}).get(name, name), 'Heading1'))
            lines = content.splitlines()
            for line in lines: body.append(paragraph(line))
        body.append(paragraph(plan.get('status_note', ''), 'Normal'))
        if setup is not None: body.append(setup)
        paragraphs = [''.join(n.text or '' for n in p.iter(W+'t')) for p in tree.iter(W+'p')]
        output = io.BytesIO()
        with ZipFile(output, 'w') as target:
            for entry in archive.infolist():
                target.writestr(entry, ET.tostring(tree, encoding='utf-8', xml_declaration=True)
                    if entry.filename == 'word/document.xml' else archive.read(entry.filename))
    return output.getvalue(), paragraphs


def _replace_paragraph(paragraph, text):
    if paragraph.tag != W+'p':
        raise ValueError('unsupported_template_element')
    for child in list(paragraph):
        if child.tag != W+'pPr': paragraph.remove(child)
    properties = paragraph.find(W+'pPr')
    if properties is not None:
        for border in properties.findall(W+'pBdr'): properties.remove(border)
    run = ET.SubElement(paragraph, W+'r')
    node = ET.SubElement(run, W+'t', {'{http://www.w3.org/XML/1998/namespace}space': 'preserve'})
    node.text = text


def prepare_projection(repository, *, rental_case_id, folder_id, provider_identity, now=None):
    snapshot = repository.load_case_snapshot(rental_case_id)
    value = build_projection(snapshot, folder_id=folder_id, provider_identity=provider_identity)
    timestamp = now or datetime.now(timezone.utc).isoformat()
    return repository.create_workflow_action(WorkflowAction(
        workflow_action_id=1, workflow_action_uuid='pending', rental_case_id=rental_case_id,
        action_type='CREATE_INTERNAL_TASK_ITEM', action_category='coordination', target_adapter_code=ADAPTER,
        reason_entity_type='rental_case', reason_entity_id=rental_case_id, approval_posture='automatic_allowed',
        status='ready_to_execute', semantic_subject_hash=digest(value), source_case_revision=snapshot.rental_case.case_revision,
        idempotency_key=f'{VERSION}:{rental_case_id}:{digest(value)}', structured_payload={
            'task_kind': VERSION, 'summary': 'Synchronize rental proposal',
            'reason': 'Project governed proposal without importing provider truth', 'projection': value},
        created_at=timestamp, updated_at=timestamp))


def validate_projection(action, snapshot, config):
    value = build_projection(snapshot, folder_id=config.folder_id, provider_identity=config.provider_identity)
    if (action.target_adapter_code != ADAPTER or action.action_type != 'CREATE_INTERNAL_TASK_ITEM'
            or action.source_case_revision != snapshot.rental_case.case_revision
            or action.structured_payload.get('task_kind') != VERSION
            or action.structured_payload.get('projection') != value
            or action.semantic_subject_hash != digest(value)
            or action.idempotency_key != f'{VERSION}:{action.rental_case_id}:{digest(value)}'):
        raise ValueError('proposal_stale_or_invalid')
    return value


def proposal_send_block(snapshot):
    """Opt-in required proposal actions must be current and successfully synced."""
    actions = [a for a in snapshot.workflow_actions if a.target_adapter_code == ADAPTER]
    if not actions: return None  # Existing certified cases retain their contract.
    if unresolved_attempts(snapshot):
        return 'proposal_requires_reconciliation'
    latest = max(actions, key=lambda a: a.workflow_action_id)
    b = binding(snapshot)
    recovered_actions = {p['workflow_action_id'] for p in reconciled_attempts(snapshot).values()}
    if (latest.status != 'succeeded' and latest.workflow_action_id not in recovered_actions or not b or b.get('source_case_revision') != snapshot.rental_case.case_revision):
        return 'proposal_not_current'
    observations = [e for e in snapshot.workflow_events if e.event_type_code in {'google_proposal_observed','google_proposal_reconciled'}]
    if observations and observations[-1].structured_payload.get('status') != 'MATCHES_PROJECTION':
        return 'proposal_requires_review'
    return None
