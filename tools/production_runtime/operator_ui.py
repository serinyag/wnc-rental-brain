"""Production operator forms over existing governed services."""
from html import escape as h
from uuid import uuid4
from .auth import CURRENT

def controls(service,case_id):
    from tools.phase_08_workflow.operational_resolution import obligation
    from datetime import datetime,timezone
    snapshot=service._require_case_snapshot(case_id)
    cards=['<section class="panel"><h2>Operational review</h2><p>Verify the case, client facts, internal work and decisions before approving the exact final email. Stop on any ambiguous outcome.</p>']
    for endpoint,label in [('inquiry-intake','Review and apply sourced client facts'),('reconcile','Reconcile case work'),('mailbox','Prepare governed client reply'),('asana-projection','Prepare internal work')]:
        cards.append(f'<form method="post" action="/cases/{case_id}/{endpoint}"><button>{label}</button></form>')
    for action in snapshot.workflow_actions:
        try:contract=obligation(snapshot,action,environment='production')
        except ValueError:continue
        outcomes=('AVAILABLE','UNAVAILABLE') if contract['kind']=='AVAILABILITY_CONFIRMATION' else ('FEASIBLE','NOT_FEASIBLE')
        fields=''.join(f'<label>{h(subject)}<select name="outcome:{h(subject)}"><option value="">Choose verified outcome</option>'+''.join(f'<option>{v}</option>' for v in outcomes)+'</select></label>' for subject in contract['subjects'])
        cards.append(f'''<form method="post" action="/cases/{case_id}/operational-resolutions" class="stack">
        <h3>{h(contract['kind'].replace('_',' ').title())}</h3><p>{h(str(contract['scope']))}</p>
        <input type="hidden" name="action_id" value="{action.workflow_action_id}">
        <input type="hidden" name="revision" value="{snapshot.rental_case.case_revision}">
        <input type="hidden" name="request_id" value="{uuid4()}"><input type="hidden" name="occurred_at" value="{datetime.now(timezone.utc).isoformat()}">{fields}
        <label>Evidence reference<input name="evidence_reference" required></label>
        <label>What did you verify?<textarea name="evidence_text" required></textarea></label>
        <button>Record scoped confirmation</button></form>''')
    options=''.join(f'<option value="{v}">{v.replace("_"," ").title()}</option>' for v in ['guest_count','requested_rental_scope','event_type','catering_arrangement','facilitator_arrangement','technical_requirements','supplier_details','event_day_contact','layout_requirements'])
    cards.append(f'''<form method="post" action="/cases/{case_id}/structured-observations" class="stack"><h3>Record sourced client information or correction</h3>
      <label>Fact<select name="field_code">{options}</select></label><input type="hidden" name="observation_type" value="fact_candidate">
      <label>Claim<select name="claim_kind"><option value="new_information">New information</option><option value="change_request">Correction or change</option></select></label>
      <label>Value<textarea name="value_text" required></textarea></label><label>Source excerpt<textarea name="source_excerpt" required></textarea></label>
      <label>Source reference<input name="external_test_reference" required></label><button>Record evidence for governed review</button></form>''')
    cards.append('</section>')
    return ''.join(cards)

def submit_form(service,case_id,form):
    from datetime import datetime,timezone
    from tools.phase_08_workflow.operational_resolution import obligation
    snapshot=service._require_case_snapshot(case_id)
    action=snapshot.find_workflow_action(int(form['action_id']))
    if action is None:raise ValueError('operational_action_missing')
    contract=obligation(snapshot,action,environment='production')
    submission={'workflow_action_id':action.workflow_action_id,'expected_case_revision':int(form['revision']),
     'contract':contract,'outcomes':{k.removeprefix('outcome:'):v for k,v in form.items() if k.startswith('outcome:')},
     'evidence_reference':form['evidence_reference'],'evidence_text':form['evidence_text'],
     'occurred_at':form['occurred_at'],'idempotency_key':form['request_id'],'synthetic':False}
    return service.submit_operational_resolution(rental_case_id=case_id,submission=submission)
