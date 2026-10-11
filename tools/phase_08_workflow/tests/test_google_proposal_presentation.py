"""Human presentation never upgrades a request to WNC authority."""
from dataclasses import replace
from unittest.mock import patch
from tools.phase_08_workflow.tests.test_google_proposal import harness, prepare, execute, native
from tools.phase_08_workflow.tests.test_working_proposal import add_fact
from tools.phase_08_workflow.google_proposal import render_template, binding


def production():
    repo, provider, adapter = harness()
    repo.rental_cases[1] = replace(repo.rental_cases[1], active_event_start='2026-11-13T09:00:00+00:00',
        active_event_end='2026-11-13T13:00:00+00:00', client_account_ref=None)
    for key, value in {'production_scope': 'production_coordination',
        'layout_requirements': {'configuration_type': 'seated', 'style': 'theatre'},
        'technical_requirements': ['projection_display'],
        'load_in_schedule': {'date': '2026-11-13', 'time': '09:00', 'status': 'requested_tbc', 'timezone': 'Europe/Amsterdam'},
        'load_out_schedule': {'date': '2026-11-13', 'time': '15:00', 'status': 'requested_tbc', 'timezone': 'Europe/Amsterdam'}}.items():
        add_fact(repo, key, value)
    return repo, provider, adapter


def test_production_requests_read_normally_unknowns_are_separate():
    repo, _, adapter = production()
    plan = prepare(repo, adapter).structured_payload['projection']
    _, lines = render_template(plan); text = '\n'.join(lines)
    for expected in ('13 November 2026', 'Time: 10:00–14:00', 'Guests: 24',
                     'Room setup: Theatre-style seating', 'Load-in: Requested from 09:00',
                     'Load-out: Requested until 15:00', 'Client: To be confirmed', 'Still to Confirm'):
        assert expected in text
    for forbidden in ('(TBC)', 'Europe/Amsterdam', 'CET', 'requested tbc', 'Configuration type', ' · ', 'TBC where applicable'):
        assert forbidden not in text
    assert 'Confirmed So Far' not in lines and 'Team & Responsibilities' not in lines
    assert '• Primary contact' in text and '• Final production coordination scope' in text
    assert 'does not constitute a confirmed booking' in text


def test_confirmations_preserve_polarity_subject_and_window():
    repo, _, adapter = production()
    results = [{'assertion': 'The Studio is unavailable for 13 November 2026 from 10:00 to 14:00 (Europe/Amsterdam).', 'outcome': 'UNAVAILABLE'},
               {'assertion': 'The requested projection setup is not feasible for 13 November 2026 from 10:00 to 14:00 (Europe/Amsterdam).', 'outcome': 'NOT_FEASIBLE'}]
    with patch('tools.phase_08_workflow.operational_resolution.client_results', return_value=results):
        plan = prepare(repo, adapter).structured_payload['projection']
    assert 'unavailable' in plan['sections']['Confirmed / Still TBC']
    assert 'not feasible' in plan['sections']['Confirmed / Still TBC']
    assert 'Technical feasibility' in plan['sections']['Working Timeline']
    assert '13 November 2026 from 10:00 to 14:00' in plan['sections']['Confirmed / Still TBC']


def test_timezone_conversion_and_multiday_scope_survive_human_formatting():
    repo, _, adapter = production()
    repo.rental_cases[1] = replace(repo.rental_cases[1], active_event_start='2026-07-13T08:00:00+00:00',
        active_event_end='2026-07-14T12:00:00+00:00')
    plan = prepare(repo, adapter).structured_payload['projection']
    assert '13 July 2026–14 July 2026' in plan['sections']['Event Overview']
    assert '10:00' in plan['sections']['Event Overview'] and '14:00' in plan['sections']['Event Overview']
    assert '13 November 2026' in plan['sections']['Current Scope'] # Different-day load-in is not silently dropped.


def test_legacy_layout_refines_same_bound_document_and_replay_writes_nothing():
    repo, provider, adapter = production()
    assert execute(repo, adapter).action_status_after == 'succeeded'
    before = binding(repo.load_case_snapshot(1))
    # Model a previously certified compact legacy layout with its exact fingerprint.
    from tools.phase_08_workflow.google_proposal_adapter import fingerprint
    doc = native(['Legacy title', 'Legacy scope'], revision='revision_2')
    provider.documents['doc_001'] = doc
    repo.execution_attempts[1][-1].response_snapshot['binding']['document_fingerprint'] = fingerprint(doc)
    repo.rental_cases[1] = replace(repo.rental_cases[1], case_revision=1)
    action = prepare(repo, adapter)
    assert execute(repo, adapter, action).action_status_after == 'succeeded'
    after = binding(repo.load_case_snapshot(1))
    assert all(before[k] == after[k] for k in ('document_id', 'file_id', 'provider_identity', 'proposal_identity', 'folder_id', 'template'))
    assert adapter.observe(action=action)['status'] == 'MATCHES_PROJECTION'
    assert execute(repo, adapter, action).already_succeeded_idempotently
    assert provider.mutations == [('create', 'doc_001'), ('update', 'doc_001')]


def test_one_feasible_subject_does_not_confirm_other_requested_equipment():
    repo, _, adapter = production(); add_fact(repo, 'technical_requirements', ['projection_display', 'microphones'])
    result = {'assertion': 'The requested projection setup is feasible for 13 November 2026 from 10:00 to 14:00 (Europe/Amsterdam).',
        'subject': 'projection_display', 'outcome': 'FEASIBLE'}
    with patch('tools.phase_08_workflow.operational_resolution.client_results', return_value=[result]):
        plan = prepare(repo, adapter).structured_payload['projection']
    assert 'Technical feasibility' in plan['sections']['Working Timeline']
    assert 'microphones is feasible' not in plan['sections']['Confirmed / Still TBC']


def test_metadata_only_unknown_is_unresolved_and_confirmed_lifecycle_is_preserved():
    repo, _, adapter = production(); add_fact(repo, 'event_day_contact', {'status': 'unknown'})
    repo.rental_cases[1] = replace(repo.rental_cases[1], lifecycle_state='confirmed_pre_event')
    plan = prepare(repo, adapter).structured_payload['projection']
    _, lines = render_template(plan)
    assert 'Team & Responsibilities' not in lines
    assert 'Event day contact' in plan['sections']['Working Timeline']
    assert 'Booking confirmation is recorded separately.' in lines[-1]
    assert repo.rental_cases[1].lifecycle_state == 'confirmed_pre_event'
