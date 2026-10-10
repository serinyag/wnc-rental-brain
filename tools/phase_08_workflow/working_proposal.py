"""Rental-specific working proposal derived from persisted case evidence.

This projection is provider-free. Template placeholders and client requests are
never confirmation evidence. It does not create supplier or financial commitments.
"""
from hashlib import sha256
from pathlib import Path
from xml.etree import ElementTree
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = {
    'studio_space': 'Studio Rental Proposal Template.docx',
    'entire_venue': 'Entire Venue Proposal Template.docx',
    'production_coordination': 'Production Coordination Proposal Template.docx',
    'full_production': 'Full Production Proposal Template.docx',
    'custom_scope': 'Custom Scope Proposal Template.docx',
}
SECTIONS = ('Event Overview', 'Current Scope', 'Financial Summary',
            'Confirmed / Still TBC', 'Working Timeline', 'Team & Responsibilities', 'Next Steps')
# Missing optional detail is requested only when the rental's recorded scope needs it.
DETAILS = (
    ('event_type', 'Event format', 'Event Overview', 'base'),
    ('guest_count', 'Guests', 'Event Overview', 'base'),
    ('primary_contact', 'Primary contact', 'Event Overview', 'base'),
    ('event_schedule', 'Event days and schedule', 'Event Overview', 'base'),
    ('production_schedule', 'Production days and schedule', 'Working Timeline', 'production'),
    ('load_in_schedule', 'Load in window', 'Working Timeline', 'delivery'),
    ('load_out_schedule', 'Load out window', 'Working Timeline', 'delivery'),
    ('catering_arrangement', 'Catering arrangement', 'Current Scope', 'optional'),
    ('facilitator_arrangement', 'Facilitator arrangement', 'Current Scope', 'optional'),
    ('event_day_contact', 'Event day contact', 'Team & Responsibilities', 'optional'),
    ('event_days', 'Event days', 'Event Overview', 'optional'),
    ('production_days', 'Production days', 'Working Timeline', 'optional'),
    ('production_dates', 'Production dates', 'Working Timeline', 'optional'),
    ('production_start', 'Production start', 'Working Timeline', 'optional'),
    ('production_end', 'Production end', 'Working Timeline', 'optional'),
    ('load_in', 'Load in', 'Working Timeline', 'optional'),
    ('load_out', 'Load out', 'Working Timeline', 'optional'),
    ('build_up', 'Build up', 'Working Timeline', 'optional'),
    ('breakdown', 'Breakdown', 'Working Timeline', 'optional'),
    ('layout_requirements', 'Room layout', 'Current Scope', 'optional'),
    ('technical_requirements', 'Technical requirements', 'Current Scope', 'optional'),
    ('catering_requirements', 'Catering', 'Current Scope', 'optional'),
    ('drink_package', 'Drink package', 'Current Scope', 'optional'),
    ('staffing_requirements', 'Staffing', 'Team & Responsibilities', 'optional'),
    ('supplier_requirements', 'External suppliers', 'Current Scope', 'optional'),
    ('wnc_responsibilities', 'WNC responsibilities', 'Team & Responsibilities', 'optional'),
    ('client_responsibilities', 'Client responsibilities', 'Team & Responsibilities', 'optional'),
    ('financial_summary', 'Recorded commercial details', 'Financial Summary', 'optional'),
)


def _template(scope):
    path = ROOT / 'sources/phase-01-03/Checklists + Templates/Proposal Templates' / TEMPLATES[scope]
    raw = path.read_bytes()
    with ZipFile(path) as archive:
        root = ElementTree.fromstring(archive.read('word/document.xml'))
    text = '\n'.join(n.text or '' for n in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'))
    if not all(section in text for section in SECTIONS):
        raise ValueError('working_proposal_template_contract_changed_review_required')
    return {'scope': scope, 'path': str(path.relative_to(ROOT)), 'sha256': sha256(raw).hexdigest(),
            'title': text.splitlines()[0]}


def build_rental_working_proposal(snapshot):
    from .asana_projection import _build_flat_projection
    from .operational_resolution import current_resolutions
    case = snapshot.rental_case
    # Prefer the latest persisted value; ordering never turns an observation into approval.
    facts = {f.field_code: f for f in sorted(snapshot.rental_case_facts,
        key=lambda f: (f.established_case_revision, f.rental_case_fact_id))
        if not f.field_code.startswith('operational_resolution:')}
    requested = facts.get('requested_rental_scope')
    scope = requested.value_payload if requested else case.rental_type_code
    venue_scope = scope
    production_scope = facts.get('production_scope')
    if production_scope and production_scope.value_payload not in ('none', 'venue_only'):
        scope = production_scope.value_payload
    needs_review = not isinstance(scope, str) or scope not in TEMPLATES
    if needs_review: scope = 'custom_scope'
    template = _template(scope)
    from .observation_registry import OBSERVATION_FIELD_DEFINITIONS
    open_types = {q.question_type for q in snapshot.open_questions
                  if q.status in {'open', 'answered_pending_validation'}}
    requirement_types = {r.requirement_type for r in snapshot.requirements
                         if r.status in {'required', 'unresolved', 'in_progress'}}
    requested_fields = {d.field_code for d in OBSERVATION_FIELD_DEFINITIONS
                        if open_types.intersection(d.related_open_question_types)
                        or requirement_types.intersection(d.related_requirement_types)}
    production = scope in {'production_coordination', 'full_production'}
    delivery = production or bool(requested_fields.intersection({'load_in_schedule', 'load_out_schedule'})) or any(f in facts for f in ('load_in', 'load_out', 'load_in_schedule', 'load_out_schedule', 'production_schedule', 'supplier_details', 'supplier_requirements'))
    rows = []
    def row(code, label, section, value=None, fact=None):
        rows.append({'key': code, 'label': label, 'section': section,
            'value': fact.value_payload if fact else value,
            'status': 'Not applicable' if fact and (fact.value_payload == 'none' or fact.value_payload == ['none']) else 'TBC',
            'source_reference': fact.source_reference if fact else None,
            'source_case_revision': fact.established_case_revision if fact else None})
    row('requested_rental_scope', 'Rental scope', 'Current Scope', venue_scope, requested)
    row('event_start', 'Event start', 'Event Overview', case.active_event_start)
    row('event_end', 'Event end', 'Event Overview', case.active_event_end)
    for code, label, section, relevance in DETAILS:
        fact = facts.get(code)
        if fact or code in requested_fields or relevance == 'base' or relevance == 'production' and production or relevance == 'delivery' and delivery:
            row(code, label, section, fact=fact)
    included = {r['key'] for r in rows}
    # Retain other governed client details instead of dropping an unusual request.
    for code, fact in facts.items():
        if code not in included:
            row(code, code.replace('_', ' ').title(), 'Current Scope', fact=fact)
    for code in sorted(requested_fields - {r['key'] for r in rows}):
        row(code, code.replace('_', ' ').title(), 'Current Scope')
    work = _build_flat_projection(snapshot, workspace_gid='projection', project_gid='projection', enforce_limits=False)
    next_steps = [{'key': w['key'], 'summary': w['name'], 'owner': w['owner'],
                   'members': w['members']} for w in work['work'] if not w['completed']]
    questions = [{'key': 'question:'+str(q.open_question_id), 'summary': q.human_question_text,
                  'owner': q.requested_from_role or 'CLIENT'}
                 for q in snapshot.open_questions if q.status in {'open', 'answered_pending_validation'}]
    reviews = [{'key': 'requirement:'+str(r.requirement_id), 'summary': r.requirement_type.replace('_', ' '),
                'owner': r.owner_role or 'WNC_INTERNAL'} for r in snapshot.requirements if r.status in {'required', 'unresolved', 'in_progress'}]
    changes = [{'key': 'change:'+str(c.proposed_case_change_id), 'summary': c.change_kind.replace('_', ' '),
                'owner': 'GOVERNED_DECISION'} for c in snapshot.proposed_changes if c.status in {'proposed', 'under_review'}]
    decisions = [{'key': 'decision:'+str(d.case_decision_id), 'summary': d.scope_description,
                  'owner': 'GOVERNED_DECISION'} for d in snapshot.case_decisions
                 if d.status in {'proposed', 'pending_approval'}]
    verified = [{'key': p['contract']['resolution_item_key'], 'kind': p['contract']['kind'],
                 'outcomes': p['outcomes'], 'event_id': p['event_id']}
                for p in current_resolutions(snapshot)]
    artifact = next((a for a in snapshot.artifacts if a.artifact_reference_id == case.current_proposal_artifact_id), None)
    return {'version': 'rental_working_proposal_v1', 'rental_case_id': case.rental_case_id,
            'case_revision': case.case_revision, 'template': template, 'template_review_required': needs_review,
            'sections': list(SECTIONS), 'details': rows, 'verified_operational_outcomes': verified,
            'next_steps': next_steps + questions + reviews + changes + decisions,
            'artifact_current': bool(artifact and artifact.derived_from_case_revision == case.case_revision
                                     and artifact.freshness_status == 'current'),
            'document_sync_enabled': False}
