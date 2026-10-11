"""Display-only scenarios: preserve semantic plans, source truth and authority."""
from copy import deepcopy
from dataclasses import replace
from unittest.mock import patch

import pytest

from tools.phase_08_workflow.asana_projection import build_projection, NUANCED_VERSION
from tools.phase_08_workflow.asana_operator_presentation import present
from tools.phase_08_workflow.tests.test_asana_projection import synthetic_repo, work_action
from tools.phase_08_workflow.tests.test_working_proposal import add_fact


def render(repo, outcomes=()):
    snapshot = repo.load_case_snapshot(1)
    plan = build_projection(snapshot, workspace_gid='111', project_gid='222', version=NUANCED_VERSION)
    original = deepcopy(plan)
    with patch('tools.phase_08_workflow.asana_operator_presentation.current_resolutions', return_value=outcomes):
        present(snapshot, plan, proposal={'document_id':'existing_document'})
    assert [(w['key'],w['members'],w['owner'],w['parent_key'],w['completed']) for w in plan['work']] == [
        (w['key'],w['members'],w['owner'],w['parent_key'],w['completed']) for w in original['work']]
    assert plan['marker'] == original['marker']
    visible = plan['master']['name'] + plan['master']['notes'] + ''.join(w['name']+w['notes'] for w in plan['work'])
    for forbidden in ['WNC internal check:', 'WNC governed decision review:', 'WNC reference:', 'Record the outcome', 'No verified conversation', 'Europe/Amsterdam', 'Operational work for this rental.']:
        assert forbidden not in visible
    assert 'Open working proposal' in plan['master']['notes']
    assert 'href="https://docs.google.com/document/d/existing_document/edit"' in plan['master']['html_notes']
    return plan


def simple():
    repo = synthetic_repo()
    repo.workflow_actions[1] = [work_action(1,'venue','Confirm studio availability')]
    return repo


def test_simple_rental_conditional_sections_and_full_title():
    plan = render(simple())
    assert plan['master']['name'] == 'SYNTHETIC TEST — WNC Operations | 12 November 2026'
    assert 'Requested rental time: 14:00–18:00' in plan['master']['notes']
    for absent in ['Technical / production', 'Tour', 'Payment', 'Agreement', 'Pricing', 'Outlook']:
        assert absent not in plan['master']['notes']
    assert plan['work'][1]['name'] == 'Check Studio availability | 12 Nov, 14:00–18:00'


def technical():
    repo = simple()
    add_fact(repo,'technical_requirements',['livestream_recording','internet_connectivity'])
    add_fact(repo,'technical_request_details',{'internet_connectivity':'guaranteed dedicated 500 Mbps upload'})
    repo.create_workflow_action(work_action(2,'technical_specifications','Check technical equipment'))
    return repo


def test_technical_request_is_never_a_promise():
    plan = render(technical())
    assert 'cannot yet be confirmed from current WNC information' in plan['master']['notes']
    task = next(w for w in plan['work'] if w['key']=='item:technical_specifications')
    assert task['name'] == 'Check livestream + internet setup'
    assert 'What internet/upload capacity WNC can commit to' in task['notes']


def test_missing_client_uses_event_and_real_missing_detail():
    repo = simple(); repo.rental_cases[1] = replace(repo.rental_cases[1],client_account_ref=None)
    plan = render(repo)
    assert plan['master']['name'] == 'Team workshop | 12 November 2026'
    assert 'Client / company name' in plan['master']['notes']
    assert 'Client not yet identified' not in plan['master']['notes']


def test_changed_window_count_scope_does_not_inherit_old_confirmation():
    repo = simple()
    repo.rental_cases[1] = replace(repo.rental_cases[1],active_event_start='2026-11-28T11:00:00+01:00',active_event_end='2026-11-28T15:00:00+01:00')
    add_fact(repo,'guest_count',30,revision=1); add_fact(repo,'requested_rental_scope','entire_venue',revision=1)
    plan = render(repo)
    assert '28 November 2026' in plan['master']['name']
    assert 'Number of guests: 30' in plan['master']['notes']
    assert 'Whole space requested' in plan['master']['notes']
    assert 'Availability: To be confirmed' in plan['master']['notes']


def test_partial_technical_keeps_unconfirmed_subjects_open():
    repo = simple();add_fact(repo,'technical_requirements',['projection_display','microphones'])
    repo.create_workflow_action(work_action(2,'technical_specifications','Check technical equipment'))
    plan = render(repo,[{'outcomes':{'projection_display':'FEASIBLE'}}])
    assert 'Projection: Confirmed for the requested setup' in plan['master']['notes']
    assert 'Microphones: To be checked' in plan['master']['notes']
    task = next(w for w in plan['work'] if w['key']=='item:technical_specifications')
    assert 'requested microphones' in task['notes']
    assert 'Whether WNC can provide the requested projection' not in task['notes']


def test_rendering_does_not_modify_canonical_or_proposal_architecture():
    repo=technical();snapshot=deepcopy(repo.load_case_snapshot(1))
    from tools.phase_08_workflow.working_proposal import build_rental_working_proposal
    before=build_rental_working_proposal(snapshot)
    render(repo)
    assert snapshot == repo.load_case_snapshot(1)
    assert build_rental_working_proposal(repo.load_case_snapshot(1)) == before


def test_scheduled_tour_requires_explicit_scheduled_evidence():
    repo=simple();add_fact(repo,'tour_schedule',{'date':'2026-11-10','start':'15:00','status':'requested_tbc'})
    assert 'Tour\n' not in render(repo)['master']['notes']
    add_fact(repo,'tour_schedule',{'date':'2026-11-10','start':'15:00','status':'scheduled'},revision=1)
    assert 'Tour\nScheduled: 15:00 on 10 November 2026' in render(repo)['master']['notes']


def test_payment_agreement_not_inferred_from_other_facts():
    repo=simple();add_fact(repo,'payment_status','deposit_received');add_fact(repo,'agreement_status','sent')
    notes=render(repo)['master']['notes']
    assert 'Payment status: Deposit received' in notes
    assert 'Agreement status: Sent, awaiting signature' in notes
