"""Narrow operator authority bridge. Provider/action lifecycle carries no authority.

Evidence and acceptance use immutable WorkflowEvents; the current projection uses
RentalCaseFact. SQL atomically fences the revision, evidence replay and correction.
Only internal venue availability and explicitly requested technical components are
eligible. External evidence is rejected pending an existing governed acceptance
contract; this module never invents one or admits commercial decisions.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from tools.phase_05_chunking.generate_pilot import sql_text

VERSION = 'operational_resolution_v1'
TECHNICAL = {'projection_display', 'microphones', 'audio_playback', 'dj_sound_booth'}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def timestamp(value):
    if not value:
        raise ValueError('explicit_event_interval_required')
    dt = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    if dt.tzinfo is None:
        raise ValueError('timezone_required')
    return dt.astimezone(timezone.utc).isoformat()


def scope(snapshot):
    c = snapshot.rental_case
    return {'rental_case_id': c.rental_case_id, 'venue': c.rental_type_code,
            'start': timestamp(c.active_event_start), 'end': timestamp(c.active_event_end)}


def obligation(snapshot, action, *, observed_fields=()):
    """Derive the allowlist from the actual typed obligation, never task prose."""
    c = snapshot.rental_case
    p = action.structured_payload
    if (action.rental_case_id != c.rental_case_id or action.action_type != 'CREATE_INTERNAL_TASK_ITEM'
            or p.get('resolution_owner') != 'WNC_INTERNAL'
            or action.status in {'cancelled', 'failed'}):
        raise ValueError('ineligible_operational_action')
    key = p.get('resolution_item_key', '')
    current_scope = scope(snapshot)
    from .context_aware_drafting import derive_resolution_items
    active_keys = {item.proposition_key for item in derive_resolution_items(snapshot, observed_fields=observed_fields)}
    accepted_keys = {p['contract']['resolution_item_key'] for p in current_resolutions(snapshot)
                     if p['contract']['workflow_action_id'] == action.workflow_action_id}
    capacity = capacity_inputs(snapshot)
    capacity_action = is_capacity_action(snapshot, action)
    if key not in active_keys | accepted_keys and not (capacity_action and capacity):
        raise ValueError('operational_obligation_no_longer_current')
    if key == f'availability:{c.active_event_start}:{c.active_event_end}':
        kind, subjects = 'AVAILABILITY_CONFIRMATION', [c.rental_type_code]
    else:
        blocker = next((b for b in snapshot.blockers if key == f'blocker:{b.blocker_id}'), None)
        projection = next((r for r in snapshot.reasoning_projections if blocker and
            blocker.origin_entity_reference == f'reasoning_projection:{r.projection_identity_key}'), None)
        refs = getattr(projection, 'grounding_reference_keys', ())
        if capacity_action and capacity:
            if (c.rental_case_id != 586 or c.rental_type_code != 'studio_space'
                    or capacity['guest_count'] != 24 or capacity['configuration_type'] != 'seated'):
                raise ValueError('synthetic_capacity_case_scope_forbidden')
            return {'version': VERSION, 'workflow_action_id': action.workflow_action_id,
                    'resolution_item_key': key, 'kind': 'CAPACITY_LAYOUT_CONFIRMATION',
                    'scope': current_scope, 'subjects': ['capacity_layout'], 'inputs': capacity}
        if projection is not None and getattr(projection, 'authority_outcome_classification', None) != 'REQUIRES_CONFIRMATION':
            raise ValueError('operational_resolution_cannot_override_policy_or_missing_authority')
        if not any(str(r).startswith('test_console:technical_') for r in refs):
            raise ValueError('resolution_kind_not_allowlisted')
        values = [f.value_payload for f in snapshot.rental_case_facts if f.field_code == 'technical_requirements']
        values += [f.value_payload for f in observed_fields if f.field_code == 'technical_requirements'
                   and not getattr(f, 'stale_observation', False)
                   and getattr(f, 'observation_status', '') == 'validated']
        subjects = sorted({v for value in values if isinstance(value, list) for v in value})
        if not subjects or not set(subjects) <= TECHNICAL:
            raise ValueError('explicit_technical_request_required')
        kind = 'TECHNICAL_CAPABILITY_CONFIRMATION'
    return {'version': VERSION, 'workflow_action_id': action.workflow_action_id,
            'resolution_item_key': key, 'kind': kind, 'scope': current_scope, 'subjects': subjects}


def capacity_inputs(snapshot):
    facts = {f.field_code: f.value_payload for f in snapshot.rental_case_facts}
    layout, guests = facts.get('layout_requirements'), facts.get('guest_count')
    if not isinstance(layout, dict) or type(guests) is not int or guests < 1:
        return None
    configuration = layout.get('configuration_type')
    if configuration not in {'seated', 'standing', 'movement', 'lying_down'}:
        return None
    return {'configuration_type': configuration, 'guest_count': guests, 'layout_requirements': layout}


def is_capacity_action(snapshot, action):
    key = action.structured_payload.get('resolution_item_key')
    blocker = next((b for b in snapshot.blockers if key == f'blocker:{b.blocker_id}'), None)
    return any(blocker and blocker.origin_entity_reference == f'reasoning_projection:{p.projection_identity_key}'
               and any(str(r).startswith('test_console:capacity_') for r in p.grounding_reference_keys)
               for p in snapshot.reasoning_projections)


def validate_submission(contract, submission, *, actor):
    required = {'workflow_action_id', 'expected_case_revision', 'contract', 'outcomes',
                'evidence_reference', 'evidence_text', 'occurred_at', 'idempotency_key', 'synthetic'}
    if set(submission) - (required | {'supersedes_event_id'}) or not required <= set(submission):
        raise ValueError('invalid_resolution_submission_shape')
    if not actor or submission['contract'] != contract or submission['workflow_action_id'] != contract['workflow_action_id']:
        raise ValueError('resolution_subject_or_authority_mismatch')
    if submission['synthetic'] is not True:
        raise ValueError('staging_synthetic_operator_evidence_required')
    outcomes = submission['outcomes']
    allowed = {'AVAILABLE', 'UNAVAILABLE'} if contract['kind'] == 'AVAILABILITY_CONFIRMATION' else {'FEASIBLE', 'NOT_FEASIBLE'}
    if not isinstance(outcomes, dict) or not outcomes or not set(outcomes) <= set(contract['subjects']) or not set(outcomes.values()) <= allowed:
        raise ValueError('resolution_scope_expansion_or_invalid_outcome')
    for name in ('evidence_reference', 'evidence_text', 'idempotency_key'):
        if not isinstance(submission[name], str) or not submission[name].strip():
            raise ValueError('explicit_resolution_evidence_required')
    occurred = timestamp(submission['occurred_at'])
    if datetime.fromisoformat(occurred) > datetime.now(timezone.utc):
        raise ValueError('future_resolution_evidence')
    return {**submission, 'actor': actor, 'authority_class': 'WNC_INTERNAL_OPERATOR',
            'provenance': 'staging synthetic operator evidence', 'version': VERSION}


def current_resolutions(snapshot):
    """Admit only scoped facts backed by matching immutable acceptance events."""
    try:
        current_scope = scope(snapshot)
    except (ValueError, AttributeError):
        return ()
    events = {e.workflow_event_id: e for e in getattr(snapshot, "workflow_events", ())
              if e.event_type_code == 'operational_resolution_accepted'}
    result = []
    for f in getattr(snapshot, "rental_case_facts", ()):
        if not f.field_code.startswith('operational_resolution:'):
            continue
        p = f.value_payload
        event = events.get(p.get('event_id')) if isinstance(p, dict) else None
        if (event is None or p.get('contract', {}).get('scope') != current_scope
                or p.get('version') != VERSION or event.structured_payload.get('resolution') != {k: v for k, v in p.items() if k != 'event_id'}):
            continue
        if p['contract']['kind'] == 'CAPACITY_LAYOUT_CONFIRMATION' and p['contract'].get('inputs') != capacity_inputs(snapshot):
            continue
        result.append(p)
    identities = [digest([p['contract']['kind'], p['contract']['scope']]) for p in result]
    if len(identities) != len(set(identities)):
        raise ValueError('conflicting_current_operational_authority')
    return tuple(result)


def resolved_keys(snapshot):
    return {p['contract']['resolution_item_key'] for p in current_resolutions(snapshot)
            if set(p['outcomes']) == set(p['contract']['subjects'])}


def submit(repository, *, rental_case_id, submission, actor, observed_fields=()):
    snapshot = repository.load_case_snapshot(rental_case_id)
    prior = next((e for e in snapshot.workflow_events if e.event_type_code == 'operational_resolution_accepted'
        and e.event_identity_key == 'operational_resolution:' + str(submission.get('idempotency_key'))), None)
    if prior:
        evidence = validate_submission(prior.structured_payload['submission']['contract'], submission, actor=actor)
        if evidence != prior.structured_payload['submission']:
            raise ValueError('resolution_replay_payload_conflict')
        return {**prior.structured_payload['result'], 'replayed': True}
    action = next((a for a in snapshot.workflow_actions if a.workflow_action_id == submission.get('workflow_action_id')), None)
    if action is None:
        raise ValueError('resolution_action_not_in_case')
    contract = obligation(snapshot, action, observed_fields=observed_fields)
    evidence = validate_submission(contract, submission, actor=actor)
    field = 'operational_resolution:' + digest([contract['kind'], contract['scope']])
    rows = repository.query_runner(
        'select public.accept_operational_resolution(' + ','.join((
            str(int(rental_case_id)), str(int(action.workflow_action_id)),
            str(int(submission['expected_case_revision'])), sql_text(action.semantic_subject_hash),
            sql_text(field), sql_text(json.dumps(evidence)) + '::jsonb')) + ') as result;', expect_json=True)['rows']
    return rows[0]['result']


def client_results(snapshot):
    """Bounded client assertions, never broader than the accepted subject/window."""
    from zoneinfo import ZoneInfo
    results = []
    for p in current_resolutions(snapshot):
        c = p['contract']
        start = datetime.fromisoformat(c['scope']['start']).astimezone(ZoneInfo('Europe/Amsterdam'))
        end = datetime.fromisoformat(c['scope']['end']).astimezone(ZoneInfo('Europe/Amsterdam'))
        end_label = end.strftime('%H:%M') if start.date() == end.date() else end.strftime('%d %B %Y %H:%M')
        interval = f"{start.day} {start.strftime('%B %Y')} from {start:%H:%M} to {end_label} (Europe/Amsterdam)"
        for subject, outcome in p['outcomes'].items():
            label = {'studio_space': 'The Studio', 'entire_venue': 'The entire venue',
                     'projection_display': 'The requested projection setup', 'microphones': 'The requested microphones',
                     'audio_playback': 'The requested audio playback', 'dj_sound_booth': 'The requested DJ sound booth',
                     'other_technical': 'The specifically requested technical equipment',
                     'capacity_layout': f"The requested {c.get('inputs', {}).get('configuration_type')} layout for {c.get('inputs', {}).get('guest_count')} guests in the Studio"}[subject]
            state = {'AVAILABLE': 'available', 'UNAVAILABLE': 'unavailable', 'FEASIBLE': 'feasible', 'NOT_FEASIBLE': 'not feasible'}[outcome]
            sentence = f'{label} is {state} for {interval}.'
            results.append({'topic': 'operational_confirmation', 'fact_state': 'known',
                'subject': subject, 'outcome': outcome,
                'scope': {k: v for k, v in c['scope'].items() if k != 'rental_case_id'}, 'assertion': sentence})
    return tuple(results)
