from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import patch
import pytest

from tools.phase_08_workflow.automatic_projection_sync import synchronize, start_worker
from tools.phase_08_workflow.tests.test_google_proposal import harness as google_harness, prepare as google_prepare, execute as google_execute
from tools.phase_08_workflow.tests.test_asana_projection import harness as asana_harness, execute
from tools.phase_08_workflow.tests.test_asana_operator_adapter import operator, rich_transport
from tools.phase_08_workflow.tests.test_working_proposal import add_fact
from tools.phase_08_workflow.asana_projection import prior_bindings
from tools.phase_08_workflow.google_proposal import binding


def service_fixture():
    repo,provider,google=google_harness()
    _,transport,asana=asana_harness(repo);rich_transport(transport)
    assert google_execute(repo,google).action_status_after=='succeeded'
    assert execute(repo,asana,operator(repo)).action_status_after=='succeeded'
    runtime=replace(asana.runtime,staging_allow_real_google=True)
    def run(*,rental_case_id,workflow_action_id,execution_mode):
        action=repo.load_case_snapshot(1).find_workflow_action(workflow_action_id)
        result=(google_execute(repo,google,action) if action.target_adapter_code=='google_proposal' else execute(repo,asana,action))
        return SimpleNamespace(success=not result.failure_codes,failure_codes=result.failure_codes)
    service=SimpleNamespace(config=SimpleNamespace(runtime=runtime,allow_real_providers=True),
        _require_case_snapshot=repo.load_case_snapshot,
        prepare_google_proposal=lambda **kw:{'workflow_action_id':google_prepare(repo,google).workflow_action_id},
        prepare_asana_rental_projection=lambda **kw:{'workflow_action_id':operator(repo).workflow_action_id},
        execute_action=run)
    return service,repo,provider,transport,google,asana


@pytest.mark.parametrize('field,value',[('guest_count',30),('requested_rental_scope','entire_venue'),('catering_arrangement','client_external_caterer')])
def test_governed_change_automatically_updates_same_document_and_master_once(field,value):
    s,repo,g,a,google,asana=service_fixture()
    before=repo.load_case_snapshot(1);gid=prior_bindings(before)['master']['gid'];doc=binding(before)['document_id']
    repo.rental_cases[1]=replace(repo.rental_cases[1],case_revision=1);add_fact(repo,field,value,1)
    assert synchronize(s,1)['status']=='synchronized'
    after=repo.load_case_snapshot(1)
    assert prior_bindings(after)['master']['gid']==gid and binding(after)['document_id']==doc
    assert len(g.documents)==1
    counts=(len(g.mutations),len(a.mutations),len(after.execution_attempts))
    assert synchronize(s,1)['executed']==[]
    assert counts==(len(g.mutations),len(a.mutations),len(repo.load_case_snapshot(1).execution_attempts))
    assert google.observe(action=google_prepare(repo,google))['status']=='MATCHES_PROJECTION'
    assert asana.observe(action=operator(repo))['status']=='matches_projection'


def test_ambiguity_stops_all_later_automatic_mutations():
    s,repo,g,a,_,_=service_fixture();repo.rental_cases[1]=replace(repo.rental_cases[1],case_revision=1);add_fact(repo,'guest_count',30,1)
    g.failure='update_failure'
    assert synchronize(s,1)['status']=='review_required'
    counts=(len(g.mutations),len(a.mutations),len(repo.load_case_snapshot(1).execution_attempts))
    assert synchronize(s,1)['status']=='reconciliation_required'
    assert counts==(len(g.mutations),len(a.mutations),len(repo.load_case_snapshot(1).execution_attempts))


def test_disabled_gates_and_production_never_start_or_execute():
    s,repo,g,a,_,_=service_fixture()
    s.config.allow_real_providers=False
    assert start_worker(s) is None
    assert synchronize(s,1)['executed']==[]
    assert len(g.documents)==1
