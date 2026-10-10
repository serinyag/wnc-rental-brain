"""Client-safe, outbound proposal projection. The action journal owns identity.

Provider edits never establish facts. Unknown and requested values remain TBC.
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
    return result


def identity(snapshot):
    return digest({'case_uuid': snapshot.rental_case.rental_case_uuid, 'purpose': VERSION})


def display(value):
    if value is None or value == 'unknown' or value == 'under_consideration':
        return 'TBC'
    if isinstance(value, dict):
        return '; '.join(k.replace('_', ' ').capitalize()+': '+display(v) for k,v in sorted(value.items())
                         if k not in {'source_reference', 'evidence_reference', 'reason', 'authority_basis', 'internal_notes'}) or 'TBC'
    if isinstance(value, list):
        return ', '.join(display(v) for v in value) or 'TBC'
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value)
            if parsed.tzinfo:
                from zoneinfo import ZoneInfo
                return parsed.astimezone(ZoneInfo('Europe/Amsterdam')).strftime('%d %B %Y at %H:%M %Z')
        except ValueError: pass
        return value.replace('_', ' ').replace('\r', ' ').replace('\n', ' ')
    return str(value)


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
    sections = {name: [] for name in SECTIONS}
    for row in model['details']:
        if row['key'] in PUBLIC_FIELDS:
            value = display(row['value'])
            status = 'Not applicable' if row['status'] == 'Not applicable' else 'TBC'
            sections[row['section']].append(f"{row['label']}: {value}" + (f' ({status})' if value != 'TBC' else ''))
    sections['Financial Summary'] = approved_prices(snapshot) or ['Pricing and applicable fees: TBC']
    # Only typed, accepted operational evidence may be described as verified.
    from .operational_resolution import client_results
    sections['Confirmed / Still TBC'].extend(result['assertion'] for result in client_results(snapshot))
    sections['Confirmed / Still TBC'].append('Other requested details remain TBC. No booking confirmation is inferred.')
    sections['Next Steps'] = [q.human_question_text for q in snapshot.open_questions
        if q.status == 'open' and q.requested_from_role in {None, 'client', 'CLIENT'}]
    sections['Next Steps'].append('Review the requested details and confirm the remaining TBC items.')
    content = {name: ' · '.join(lines) if lines else 'TBC where applicable' for name, lines in sections.items()}
    case = snapshot.rental_case
    value = {'version': VERSION, 'rental_case_id': case.rental_case_id,
        'proposal_identity': identity(snapshot), 'source_case_revision': case.case_revision,
        'folder_id': folder_id, 'provider_identity': provider_identity, 'template': template,
        'title': model['template']['title'], 'client': display(case.client_account_ref),
        'sections': content, 'manual_edit_policy': MANUAL_EDIT_POLICY}
    # Content hash ignores unrelated revisions, while the execution envelope is
    # still bound to the exact current case revision.
    value['projection_hash'] = digest({k: v for k, v in value.items() if k != 'source_case_revision'})
    return value


def render_template(plan):
    """Retain the actual template's headings, table styles and page setup.

    Replace example content with one managed paragraph per section. Fixed
    paragraph layout allows revision-guarded in-place updates of native Docs.
    """
    path = ROOT / plan['template']['path']
    raw = path.read_bytes()
    from hashlib import sha256
    if sha256(raw).hexdigest() != plan['template']['sha256']:
        raise ValueError('proposal_template_changed')
    with ZipFile(io.BytesIO(raw)) as archive:
        tree = ET.fromstring(archive.read('word/document.xml'))
        body = tree.find(W+'body')
        current = None
        placed = set()
        for child in list(body):
            text = ''.join(n.text or '' for n in child.iter(W+'t'))
            heading = next((name for name in SECTIONS if text.startswith(tuple(f'{i}. {name}' for i in range(1, 8)))), None)
            if heading and child.tag == W+'p':
                current = heading
                _replace_paragraph(child, f'{SECTIONS.index(heading)+1}. {heading}')
                continue
            if child.tag == W+'sectPr':
                continue
            if current:
                if current in placed:
                    body.remove(child)
                    continue
                if child.tag == W+'tbl':
                    # Keep a styled table with one row; suppress every example.
                    rows = child.findall(W+'tr')
                    for row in rows[1:]: child.remove(row)
                    cells = rows[0].findall(W+'tc')
                    first = cells[0]
                    # The managed section uses the full styled table width;
                    # retain the source table's page geometry, not narrow cells.
                    properties = first.find(W+'tcPr')
                    if properties is None: properties = ET.SubElement(first, W+'tcPr')
                    span = ET.SubElement(properties, W+'gridSpan', {W+'val': str(len(cells))})
                    widths = [cell.find(W+'tcPr/'+W+'tcW') for cell in cells]
                    if all(width is not None for width in widths):
                        width = properties.find(W+'tcW')
                        width.set(W+'w', str(sum(int(n.get(W+'w', '0')) for n in widths)))
                    for cell in cells[1:]: rows[0].remove(cell)
                    for i, cell in enumerate([first]):
                        paragraphs = cell.findall(W+'p')
                        for extra in paragraphs[1:]: cell.remove(extra)
                        _replace_paragraph(paragraphs[0], plan['sections'][current] if i == 0 else '')
                else:
                    _replace_paragraph(child, plan['sections'][current])
                placed.add(current)
            elif child.tag == W+'p':
                # Match the required Google Docs sanitizer deterministically in
                # the hosted path, without altering retained source templates.
                props = child.find(W+'pPr')
                if props is not None:
                    for border in props.findall(W+'pBdr'): props.remove(border)
                _replace_paragraph(child, plan['title'] if text.endswith('Working Proposal') else
                    'Client: '+plan['client'] if text.startswith('Client:') else '')
        if placed != set(SECTIONS):
            raise ValueError('proposal_template_layout_unsupported')
        if list(body)[-2].tag == W+'tbl':
            body.insert(len(body)-1, ET.Element(W+'p'))
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
    if any(a.status == 'started' or (a.status != 'succeeded' and not a.retry_eligible) for a in attempts(snapshot)):
        return 'proposal_requires_reconciliation'
    latest = max(actions, key=lambda a: a.workflow_action_id)
    b = binding(snapshot)
    if (latest.status != 'succeeded' or not b or b.get('source_case_revision') != snapshot.rental_case.case_revision):
        return 'proposal_not_current'
    observations = [e for e in snapshot.workflow_events if e.event_type_code == 'google_proposal_observed']
    if observations and observations[-1].structured_payload.get('status') != 'MATCHES_PROJECTION':
        return 'proposal_requires_review'
    return None
