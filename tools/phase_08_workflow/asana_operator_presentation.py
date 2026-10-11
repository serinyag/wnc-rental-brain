"""Human Asana copy only; semantic work, authority and provider identities stay intact."""
from datetime import datetime
from html import escape
from zoneinfo import ZoneInfo

from .operational_resolution import current_resolutions
from .requested_detail_presentation import event_timing, technical_details, TECHNICAL_LABELS

VENUES = {'studio_space': 'Studio', 'entire_venue': 'Whole space', 'custom_scope': 'Custom scope'}
LABELS = {**TECHNICAL_LABELS, 'livestream_recording': 'Livestream recording',
          'internet_connectivity': 'Internet connection'}


def _human(value):
    if isinstance(value, list):
        return ', '.join(_human(v) for v in value)
    if isinstance(value, dict):
        return '; '.join(k.replace('_', ' ').capitalize() + ': ' + _human(v)
                        for k, v in value.items() if k not in {'status', 'timezone', 'source_reference', 'evidence_reference'})
    return str(value).replace('_', ' ')


def _clean(summary):
    import re
    summary = re.sub(r'^(?:WNC internal check:|WNC governed decision review:|Confirm:)\s*', '', summary, flags=re.I)
    if 'proposed change must be accepted' in summary.lower():
        return 'Review the requested event change'
    if 'current governed policy does not support' in summary.lower():
        return 'Review what WNC can support for this request'
    return summary[0].upper() + summary[1:] if summary else 'Review the request'


def present(snapshot, plan, *, proposal=None):
    """Mutate only display fields on an already grouped semantic projection."""
    c = snapshot.rental_case
    facts = {f.field_code: f.value_payload for f in sorted(snapshot.rental_case_facts,
             key=lambda f: (f.established_case_revision, f.rental_case_fact_id))}
    metadata = next((e.structured_payload for e in snapshot.workflow_events
                     if e.event_type_code == 'test_console_case_registered'), {})
    client = metadata.get('client_label') or c.client_account_ref
    event = _human(facts.get('event_type', 'Rental inquiry')).capitalize()
    venue = VENUES.get(facts.get('requested_rental_scope', c.rental_type_code),
                       _human(facts.get('requested_rental_scope', c.rental_type_code)))
    start = datetime.fromisoformat(c.active_event_start.replace('Z', '+00:00')).astimezone(ZoneInfo('Europe/Amsterdam')) if c.active_event_start else None
    end = datetime.fromisoformat(c.active_event_end.replace('Z', '+00:00')).astimezone(ZoneInfo('Europe/Amsterdam')) if c.active_event_end else None
    schedule = facts.get('event_schedule', {})
    date = start or (datetime.fromisoformat(schedule['date']) if isinstance(schedule, dict) and schedule.get('date') else None)
    day = f'{date.day} {date:%B %Y}' if date else 'Date to be confirmed'
    title_day = day
    if not date and isinstance(schedule, dict) and isinstance(schedule.get('dates'), list):
        title_day = ' OR '.join(f'{d.day} {d:%B %Y}' for d in (datetime.fromisoformat(x) for x in schedule['dates']))
    plan['master']['name'] = f'{client or event} | {title_day}'
    outcomes = {subject: outcome for p in current_resolutions(snapshot) for subject, outcome in p['outcomes'].items()}
    availability = outcomes.get(facts.get('requested_rental_scope', c.rental_type_code))
    details = technical_details(facts.get('technical_request_details'))
    subjects = [s for s in facts.get('technical_requirements', []) if s != 'none']
    technical_rows = []
    for subject in subjects:
        state = {'FEASIBLE': 'Confirmed for the requested setup', 'NOT_FEASIBLE': 'Not available for the requested setup'}.get(outcomes.get(subject), 'To be checked')
        label = LABELS.get(subject, _human(subject).capitalize())
        request = details.get(subject)
        if subject == 'internet_connectivity' and request:
            technical_rows.append(f'Internet request: {request[0].upper() + request[1:]} requested. ' +
                                  ('This cannot yet be confirmed from current WNC information.' if subject not in outcomes else state + '.'))
        else:
            technical_rows.append(f'{label}: {state}' + (f' ({request})' if request else ''))
    steps = []
    for item in plan['work']:
        if item.get('kind') == 'department':
            item['notes'] = {'Admin': 'Availability, event details and booking arrangements.',
                             'Logistics': 'Room setup, production and technical arrangements.',
                             'Experience': 'Hospitality and event experience arrangements.',
                             'Post-event': 'Follow-up after the event.'}[item['name']]
            continue
        text = ' '.join(m['summary'] for m in item['members']).lower()
        keys = [m['key'] for m in item['members']]
        if any(k.startswith('availability:') or k == 'venue' for k in keys):
            interval = f'{start:%H:%M}–{end:%H:%M}' if start and end and start.date() == end.date() else ''
            if start and end and start.date() != end.date():
                interval = f'{start:%H:%M} to {end.day} {end:%b, %H:%M}'
            short_day = f'{date.day} {date:%b}' if date else 'date TBC'
            item['name'] = f'Check {venue} availability | {short_day}' + (f', {interval}' if interval else '')
            item['notes'] = f'Confirm whether {venue} is available for the requested rental window.\n\nRequested: {day}' + (f', {interval}' if interval else '')
        elif subjects and (any(k == 'technical_specifications' for k in keys) or any(s in text for s in ('technical', 'av setup', 'projector', 'microphone'))):
            item['name'] = ('Check livestream + internet setup' if {'livestream_recording', 'internet_connectivity'} <= set(subjects)
                            else 'Check ' + ' + '.join(LABELS.get(s, _human(s)).lower() for s in subjects) + ' setup')
            requests = [details.get(s) or LABELS.get(s, _human(s)) for s in subjects]
            checks = [('What livestream setup WNC can provide' if s == 'livestream_recording' else
                       'What internet/upload capacity WNC can commit to' if s == 'internet_connectivity' else
                       f'Whether WNC can provide the requested {LABELS.get(s, _human(s)).lower()}')
                      for s in subjects if s not in outcomes]
            item['notes'] = 'Client requested\n' + '\n'.join('- ' + r[0].upper() + r[1:] for r in requests)
            if checks:
                item['notes'] += '\n\nConfirm\n' + '\n'.join('- ' + x for x in checks)
            confirmed = [row for s, row in zip(subjects, technical_rows) if s in outcomes]
            if confirmed:
                item['notes'] += '\n\nRecorded outcomes\n' + '\n'.join('- ' + x for x in confirmed)
        else:
            item['name'] = _clean(item['name'])
            item['notes'] = '\n'.join('- ' + _clean(m['summary']) + (' (previous request)' if m['retired'] else ' (completed)' if m['resolved'] else '') for m in item['members'])
        if item['name'] == 'Review the requested event change':
            item['notes'] = 'Review the changed details against the booking arrangements before confirming them to the client.'
        if item['members'] and all(m['retired'] for m in item['members']):
            item['name'] = 'Previous check: ' + _clean(item['members'][0]['summary'])
            item['notes'] = 'This check belongs to an earlier request and is no longer active.'
        elif item['completed']:
            item['notes'] += '\n\nThis check is complete; see the current brief for confirmed details.'
        if not item['completed']:
            steps.append(item['name'])
    status = ('Closed / cancelled' if plan['master']['completed'] else 'Internal checks in progress' if steps else
              'Client details needed' if not client else 'Awaiting client response' if c.lifecycle_state == 'proposal_pending_client' else 'Review the next client response')
    sections = [f'Current status: {status}']
    # These sections require explicit lifecycle facts; artifact existence is not
    # proof of payment, signature or a scheduled visit.
    for field, label, states in [
        ('payment_status', 'Payment status', {'paid': 'Paid', 'not_paid': 'Not paid', 'deposit_received': 'Deposit received'}),
        ('agreement_status', 'Agreement status', {'signed': 'Signed', 'sent': 'Sent, awaiting signature', 'not_sent': 'Not yet sent'})]:
        if facts.get(field) in states:
            sections.append(label + ': ' + states[facts[field]])
    tour = facts.get('tour_schedule')
    if isinstance(tour, dict) and tour.get('status') in {'scheduled', 'confirmed'} and tour.get('date') and (tour.get('time') or tour.get('start')):
        from .asana_projection import _requested_schedule
        sections.append('Tour\nScheduled: ' + _requested_schedule(tour, None))
    timing = []
    if date:
        timing.append(f'Event date: {date:%A}, {day}')
    rows, missing = event_timing(c.active_event_start, c.active_event_end, schedule)
    if start and end:
        time = f'{start:%H:%M}–{end:%H:%M}' if start.date() == end.date() else f'{start:%H:%M} to {end.day} {end:%B %Y, %H:%M}'
        timing.append('Requested rental time: ' + time)
    else:
        timing.extend(r for r in rows if not r.startswith('Date:'))
    if facts.get('guest_count') is not None:
        timing.append('Number of guests: ' + str(facts['guest_count']))
    timing.append('Availability: ' + {'AVAILABLE': 'Confirmed for the requested window', 'UNAVAILABLE': 'Unavailable for the requested window'}.get(availability, 'To be confirmed'))
    sections.append('Date and timing\n' + '\n'.join(timing))
    scope = [event, venue + ' requested'] + [LABELS.get(s, _human(s)) + ' requested' for s in subjects]
    for field, label in [('production_scope', 'Production'), ('catering_arrangement', 'Catering'), ('layout_requirements', 'Room layout')]:
        if facts.get(field) not in (None, 'none', 'venue_only'):
            value = facts[field]
            if field == 'layout_requirements' and isinstance(value, dict):
                layout = value.get('style') or value.get('configuration_type')
                scope.append(str(layout).capitalize() + ' layout requested' if layout else 'Room layout requested')
            else:
                scope.append(label + ': ' + _human(value) + ' requested')
    sections.append('Current event scope\n' + '\n'.join('- ' + x for x in scope))
    from .asana_projection import _requested_schedule
    for field, label in [('production_schedule', 'Production schedule'), ('load_in_schedule', 'Load-in'), ('load_out_schedule', 'Load-out')]:
        if facts.get(field):
            technical_rows.append(label + ' requested: ' + _requested_schedule(facts[field], c.active_event_start, schedule.get('date') if isinstance(schedule, dict) else None))
    if technical_rows:
        sections.append('Technical / production\n' + '\n'.join(technical_rows))
    clarify = ([] if client else ['Client / company name']) + [x + ': Still to confirm' for x in missing]
    clarify += [q.human_question_text for q in snapshot.open_questions if q.status == 'open' and q.requested_from_role in {None, 'client', 'CLIENT'}]
    if clarify:
        sections.append('Still to clarify\n' + '\n'.join('- ' + _clean(x) for x in dict.fromkeys(clarify)))
    if steps:
        steps += ['Prepare the client response once the checks are complete']
    else:
        steps = ['Review the working proposal and prepare the next client response']
    sections.append('Recommended next steps\n' + '\n'.join(f'{i}. {x}' for i, x in enumerate(dict.fromkeys(steps), 1)))
    if proposal:
        sections.append('Rental proposal\nOpen working proposal')
    notes = '\n\n'.join(sections)
    plan['master']['notes'] = notes
    html = escape(notes)
    if proposal:
        html = html.replace('Open working proposal', '<a href="https://docs.google.com/document/d/' + escape(proposal['document_id'], quote=True) + '/edit">Open working proposal</a>')
    plan['master']['html_notes'] = '<body>' + html + '</body>'
    plan['presentation_version'] = 'asana_operator_presentation_v1'
