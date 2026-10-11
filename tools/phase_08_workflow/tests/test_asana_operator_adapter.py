from copy import deepcopy
from html.parser import HTMLParser
import json
from tools.phase_08_workflow.tests.test_asana_projection import harness, prepare, execute, update_case, NOW
from tools.phase_08_workflow.asana_projection import prepare_projection, OPERATOR_VERSION, NUANCED_VERSION


def operator(repo):
    return prepare_projection(repo,rental_case_id=1,workspace_gid='111',project_gid='222',now=NOW,version=OPERATOR_VERSION)


def rich_transport(transport):
    original=transport.send_json
    def send(**kwargs):
        data=kwargs['payload'].get('data',{})
        if 'html_notes' in data:
            class Plain(HTMLParser):
                def __init__(self):super().__init__();self.text=''
                def handle_data(self,value):self.text+=value
            parser=Plain();parser.feed(data['html_notes']);data['notes']=parser.text
        return original(**kwargs)
    transport.send_json=send


def test_legacy_transition_exact_bindings_without_markers_replay_and_followup():
    repo,transport,adapter=harness();execute(repo,adapter,prepare_projection(repo,rental_case_id=1,workspace_gid='111',project_gid='222',now=NOW,version=NUANCED_VERSION));rich_transport(transport)
    before={key:value['gid'] for key,value in repo.load_case_snapshot(1).execution_attempts[0].response_snapshot['bindings'].items()}
    action=operator(repo)
    assert execute(repo,adapter,action).action_status_after=='succeeded'
    latest=repo.load_case_snapshot(1).execution_attempts[-1].response_snapshot['bindings']
    assert all(latest[k]['gid']==gid for k,gid in before.items())
    assert all('WNC reference:' not in t['notes'] and ' / work ' not in t['notes'] for t in transport.tasks.values())
    assert adapter.observe(action=action)['status']=='matches_projection'
    calls=len(transport.mutations);assert execute(repo,adapter,action).already_succeeded_idempotently
    assert len(transport.mutations)==calls
    update_case(repo);updated=operator(repo)
    assert execute(repo,adapter,updated).action_status_after=='succeeded'
    assert repo.load_case_snapshot(1).execution_attempts[-1].response_snapshot['bindings']['master']['gid']==before['master']
    assert adapter.observe(action=updated)['status']=='matches_projection'


def test_exact_duplicate_and_human_drift_remain_review_required():
    repo,transport,adapter=harness();rich_transport(transport);action=operator(repo)
    assert execute(repo,adapter,action).action_status_after=='succeeded'
    master=next(t for t in transport.tasks.values() if t['parent'] is None)
    duplicate=deepcopy(master);duplicate['gid']='9999';transport.tasks['9999']=duplicate
    assert adapter.observe(action=action)['status']=='review_required'
    del transport.tasks['9999'];master['notes']+='\nHuman edit'
    assert adapter.observe(action=action)['status']=='review_required'
    update_case(repo);n=len(transport.mutations)
    assert execute(repo,adapter,operator(repo)).action_status_after=='failed'
    assert len(transport.mutations)==n


def test_ambiguous_unbound_creation_cannot_adopt_by_text_or_retry():
    repo,transport,adapter=harness();rich_transport(transport);action=operator(repo)
    transport.next_failure='timeout_after_accept'
    assert execute(repo,adapter,action).action_status_after=='failed'
    assert adapter.observe(action=action)['status']=='inconclusive'
    update_case(repo);n=len(transport.mutations)
    assert execute(repo,adapter,operator(repo)).failure_codes==('adapter_outcome_ambiguous',)
    assert len(transport.mutations)==n


def test_distinct_journal_bound_checks_with_identical_copy_are_not_duplicates():
    from tools.phase_08_workflow.tests.test_asana_projection import work_action
    repo,transport,adapter=harness();rich_transport(transport)
    for aid,key in [(10,'technical_a'),(11,'technical_b')]:
        repo.create_workflow_action(work_action(aid,key,'Confirm technical handover'))
    # Their distinct source obligations have exact canonical identities even
    # though the accepted human copy happens to be the same.
    action=operator(repo)
    assert execute(repo,adapter,action).action_status_after=='succeeded'
    assert adapter.observe(action=action)['status']=='matches_projection'
    update_case(repo)
    assert execute(repo,adapter,operator(repo)).action_status_after=='succeeded'
