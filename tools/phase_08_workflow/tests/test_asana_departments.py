import copy
from dataclasses import replace
from tools.phase_08_workflow.tests.test_asana_projection import harness,execute,update_case,prepare,NOW
from tools.phase_08_workflow.asana_projection import prepare_projection,DEPARTMENT_VERSION,build_projection
from tools.phase_08_workflow.live_proposal import render_live_proposal
from tools.phase_08_workflow.contracts import ArtifactReference


def departments(repo):
    return prepare_projection(repo,rental_case_id=1,workspace_gid='111',project_gid='222',now=NOW,version=DEPARTMENT_VERSION)


def test_nested_groups_reuse_bindings_complete_checks_and_replay():
    repo,provider,adapter=harness();a=departments(repo)
    assert execute(repo,adapter,a).action_status_after=='succeeded'
    bindings=repo.execution_attempts[1][0].response_snapshot['bindings']
    assert [provider.tasks[bindings['department:'+name.lower()]['gid']]['name'] for name in ('Admin','Logistics','Experience','Post-event')]==['Admin','Logistics','Experience','Post-event']
    assert provider.tasks[bindings['item:venue']['gid']]['parent']['gid']==bindings['department:admin']['gid']
    assert provider.tasks[bindings['group:EXTERNAL_PARTY:supplier-logistics']['gid']]['parent']['gid']==bindings['department:logistics']['gid']
    assert adapter.observe(action=a)['status']=='matches_projection'
    before=copy.deepcopy(bindings);update_case(repo);a=departments(repo)
    assert execute(repo,adapter,a).action_status_after=='succeeded'
    after=repo.execution_attempts[1][-1].response_snapshot['bindings']
    assert all(after[k]['gid']==b['gid'] for k,b in before.items())
    assert provider.tasks[after['item:venue']['gid']]['completed'] is True
    assert after['item:technical']['parent_key']=='department:logistics'
    count=len(provider.mutations);assert execute(repo,adapter,departments(repo)).already_succeeded_idempotently
    assert len(provider.mutations)==count and adapter.observe(action=a)['status']=='matches_projection'


def test_flat_bound_case_is_not_silently_reparented():
    repo,provider,adapter=harness();assert execute(repo,adapter,prepare(repo)).action_status_after=='succeeded'
    before=len(provider.mutations)
    assert execute(repo,adapter,departments(repo)).action_status_after=='failed'
    assert len(provider.mutations)==before
    assert repo.execution_attempts[1][-1].response_snapshot['reason']=='existing_hierarchy_requires_explicit_migration'


def test_live_document_refreshes_truth_and_flags_old_proposal():
    repo,_,_=harness();snapshot=repo.load_case_snapshot(1)
    snapshot=replace(snapshot,rental_case=replace(snapshot.rental_case,current_proposal_artifact_id=1),
      artifacts=(ArtifactReference(1,1,'proposal',0,'current',external_reference='https://docs.google.com/document/d/synthetic/edit'),))
    page=render_live_proposal(snapshot);assert 'Current' in page and 'Open proposal in Google Docs' in page
    update_case(repo);snapshot=replace(repo.load_case_snapshot(1),rental_case=replace(repo.rental_cases[1],current_proposal_artifact_id=1),artifacts=snapshot.artifacts)
    page=render_live_proposal(snapshot)
    assert 'Stale — refresh and review required' in page and '>30<' in page
    assert 'content="60"' in page and 'No verified operational outcomes recorded yet.' in page


def test_trusted_production_link_and_html_escaping():
    repo,_,_=harness();snapshot=repo.load_case_snapshot(1)
    plan=build_projection(snapshot,workspace_gid='111',project_gid='222',version=DEPARTMENT_VERSION,application_origin='https://pilot.example.test')
    assert 'https://pilot.example.test/cases/1/live-proposal' in plan['master']['notes']
    snapshot=replace(snapshot,rental_case=replace(snapshot.rental_case,client_account_ref='<script>bad</script>'))
    assert '<script>' not in render_live_proposal(snapshot)


def test_ambiguous_nested_create_preserves_partial_bindings_and_fences_replay():
    repo,provider,adapter=harness();original=provider.send_json;mutations=[]
    def send(**kwargs):
        if kwargs['method']!='GET':
            mutations.append(True)
            if len(mutations)==2:provider.next_failure='timeout_after_accept'
        return original(**kwargs)
    provider.send_json=send
    result=execute(repo,adapter,departments(repo))
    assert result.action_status_after=='failed' and not result.retry_eligible
    attempt=repo.execution_attempts[1][-1]
    assert 'master' in attempt.response_snapshot['bindings'] and len(provider.tasks)==2
    before=len(provider.mutations);update_case(repo)
    assert execute(repo,adapter,departments(repo)).failure_codes==('adapter_outcome_ambiguous',)
    assert len(provider.mutations)==before
