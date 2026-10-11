"""Exact WNC field identities audited from Rentals 2026; outbound projection only."""
import re

WORKSPACE = '1208455784737302'
RENT = '1212662125912127'
ROOM = '1212669866280539'
EVENT = '1212669866280544'
CONTACT = '1212669866280551'
ADDONS = '1212669866280553'
FIELDS = (RENT, ROOM, EVENT, CONTACT, ADDONS)
ROOMS = {'studio_space': '1212669866280540', 'entire_venue': '1212669866280542'}
EVENTS = {'pr': '1212669866280545', 'personal_private': '1212669866280546',
          'corporate_networking': '1212669866280547', 'workshop': '1212669866280548',
          'team_workshop': '1212669866280548', 'photo_shoot': '1212669866280549'}
CATERING = '1212669866280554'
DRINKS = '1212669866280555'
TECH = '1212669866280556'


def project(snapshot):
    facts = {f.field_code: f.value_payload for f in sorted(snapshot.rental_case_facts,
             key=lambda f: (f.established_case_revision, f.rental_case_fact_id))}
    # Explicit governed primary contact overrides the verified conversation POC.
    primary = facts.get('primary_contact')
    email = primary.get('email') if isinstance(primary, dict) else None
    if primary is None:
        metadata = next((e.structured_payload for e in snapshot.workflow_events
                         if e.event_type_code == 'test_console_case_registered'), {})
        email = metadata.get('contact_email')
    email = email.strip().lower() if isinstance(email, str) and re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email.strip()) else None
    addons = []
    arrangement = facts.get('catering_arrangement')
    if arrangement in {'client_external_caterer', 'wnc_vendor', 'wnc_coordinated'}:
        addons.append(CATERING)
    if arrangement == 'drinks_refreshments_only':
        addons.append(DRINKS)
    if any(t != 'none' for t in facts.get('technical_requirements', [])):
        addons.append(TECH)
    event = str(facts.get('event_type', '')).strip().lower().replace(' ', '_')
    return {ROOM: ROOMS.get(facts.get('requested_rental_scope', snapshot.rental_case.rental_type_code)),
            EVENT: EVENTS.get(event), CONTACT: email, ADDONS: addons}


def values(record):
    result = {}
    for field in record.get('custom_fields', []):
        gid = field.get('gid')
        if gid == RENT:
            result[gid] = field.get('display_value') or field.get('text_value')
        elif gid in {ROOM, EVENT}:
            result[gid] = (field.get('enum_value') or {}).get('gid')
        elif gid == CONTACT:
            result[gid] = field.get('text_value') or None
        elif gid == ADDONS:
            result[gid] = sorted(x['gid'] for x in field.get('multi_enum_values', []))
    return result


def verify_definitions(project_record, expected):
    fields = {s['custom_field']['gid']: s['custom_field'] for s in project_record.get('custom_field_settings', [])}
    if not set(FIELDS) <= set(fields) or fields[RENT].get('id_prefix') != 'RENT':
        raise ValueError('Existing WNC field settings required; no field creation permitted')
    for gid, subtype in [(ROOM, 'enum'), (EVENT, 'enum'), (CONTACT, 'text'), (ADDONS, 'multi_enum')]:
        if fields[gid].get('resource_subtype') != subtype:
            raise ValueError('Existing WNC field type drift')
        selected = expected.get(gid)
        if subtype != 'text' and selected:
            selected = selected if isinstance(selected, list) else [selected]
            options = {o['gid'] for o in fields[gid].get('enum_options', []) if o.get('enabled')}
            if not set(selected) <= options:
                raise ValueError('Existing WNC option missing or disabled')
