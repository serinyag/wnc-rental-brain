"""Render every captured plan, exact writing payload and draft without a judge call."""
import json,sys
from pathlib import Path
p=Path(__file__).resolve().parent
load=lambda f:json.loads((p/f).read_text())
slug=sys.argv[1];status=load('program_status.json');data=load(f'{slug}_results.json');reviews=load(f'{slug}_reviews.json')
audits=load(f'{slug}_planner_audit.json');by_revision={a['draft_revision_id']:a for a in audits if a.get('draft_revision_id')}
roles=['acknowledge','must_communicate','must_ask','helpful_now','already_communicated','defer','internal_only']
lines=[]
def text(*values):lines.extend(values)
def obj(value):text('```json',json.dumps(value,indent=2,ensure_ascii=False),'```','')
def draft(t):
 r=t.get('draft',{}).get('draft_revision')
 if not r:
  candidate=next((a for a in audits if a.get('rejected_body') and a['client_generation_payload']['latest_client_message']==t['incoming_message']['body']),None)
  text('**REJECTED CANDIDATE: no DraftRevision was persisted.**','')
  if candidate:text('Validation codes: `'+', '.join(candidate['validation_codes'])+'`.','','```text',candidate['rejected_subject'],'',candidate['rejected_body'],'```','')
  else:text(str(t.get('failure',''))[:300],'')
  return
 text('**Subject**','','```text',r['subject'],'```','','**Body**','','```text',r['body_text'],'```','')
text('# Editorial Planner Architecture','','The deterministic planner sits inside DraftContract → ClientGenerationPayload, after governed case truth, current factual retrieval and ownership/intent resolution, and before the existing single bounded OpenAI drafter. The full contract remains local for the existing validators. Planning does not create policy, pricing, permissions, approvals, availability or workflow truth.','',status['outcome'],'')
text('# Domain Model','','`EditorialRole` is a string enum: MUST_COMMUNICATE, MUST_ASK, ACKNOWLEDGE, HELPFUL_NOW, ALREADY_COMMUNICATED, DEFER, INTERNAL_ONLY.','',
'`EditorialContentItem` contains semantic_key, topic, source_reference, proposition_key, authority_class, structured value, role, reason, prior_turn_status and priority. A SHA-256 fingerprint binds semantic identity, source and current value. Inclusion follows the role, not a free-form prompt suggestion.','',
'`EditorialContentPlan` contains response_intent, primary_client_need, typed items, substantive_budget, budget_reason and version. Its audit projection exposes each role separately, do_not_repeat, client_visible_pending_state, editorial_rationale and source_bindings.','')
text('# Selection Rules','','1. Retain every client-owned open question and material current answer. Preserve current restrictions and pending-change semantics.','',
'2. Select requested current capability answers from typed Phase 4 projections. Project recognized current kitchen/access guidance into practical semantic values; defer secondary or unstructured document text.','',
'3. Use earlier client requests and realized draft metadata to retain unanswered commercial questions. A newly available or changed governed fee must be included. An unrelated budget mention does not request a fee quote.','',
'4. Use stable source/value fingerprints to identify unchanged prior answers. A current explicit question may justify repeating one. The audit records that reason. Planned-but-unrealized items do not count as communicated.','',
'5. Default to three substantive items for simple replies and up to four for ordinary replies. Required compound answers and client-owned questions can expand the budget explicitly; optional guidance loses priority. Acknowledgement does not consume a substantive slot.','',
'6. Keep full internal ownership and authority material in the local audit. Only selected client-safe values enter generation. No deferred raw guidance or prior draft bodies are sent.','',
'Novelty uses the last accepted generated or edited draft event per earlier client turn, not case revision alone. Current-turn drafts/regenerations are excluded. Operator edits without a fresh realization audit do not inherit that turn’s metadata. “Communicated” here means present in a prior accepted draft, never proof of sending or receipt.','',
'Request-topic selectors and realization witnesses are finite deterministic adapters. They are not a second NLP model. Unrecognized wording is conservative: it does not establish a previous answer or new authority. Current sources always remain authoritative.','')
text('# Before / After Pipeline','','```mermaid','flowchart TD','  A[Governed truth + retrieval + current turn + thread metadata] --> B[Deterministic editorial plan]','  B --> C[Selected client-safe payload]','  C --> D[One existing bounded drafter]','  D --> E[Existing deterministic validators]','  E --> F[Immutable approval-bound DraftRevision]','  B --> G[Local candidate and omission audit]','```','','Before: the payload exposed almost all guidance and the model chose what to mention. After: application logic assigns each candidate an editorial role, excludes deferred/internal/unchanged content, and gives the model the selected writing plan.','')
text('# Implementation Passes','')
for cycle in status['passes']:obj(cycle)
text('# UAT Planner Evidence','','Each plan and payload below was captured in the generated draft event. The candidate table deliberately omits raw internal text; full source bindings and exclusion decisions remain in the local JSON audit. The JSON is the exact client-writing payload passed to the drafter, with no credentials.','')
for case in data['results']:
 for t in case['turns']:
  key=f"{case['scenario_id']}/{t['turn_number']}";text('## '+key,'')
  r=t.get('draft',{}).get('draft_revision')
  a=by_revision[r['inquiry_response_draft_revision_id']] if r else next(a for a in audits if a['rental_case_id']==case['rental_case_id'] and a['client_generation_payload']['latest_client_message']==t['incoming_message']['body'])
  if not r:text('**Plan for a rejected candidate; no accepted draft.**','')
  plan=a['editorial_content_plan']
  text('Response intent: `'+plan['response_intent']+'`. Primary need: `'+', '.join(plan['primary_client_need'])+'`.','',
       f"Substantive budget: {plan['substantive_budget']}; reason: `{plan['editorial_rationale']}`.",'')
  for role in roles:
   text('### '+role.upper(),'')
   if not plan[role]:text('None.','');continue
   text('| Topic / semantic key | Source | Reason | Prior-turn status | In payload |','|---|---|---|---|---|')
   for i in plan[role]:
    clean=lambda x:str(x).replace('|','\\|').replace('\n',' ')
    text('| '+' | '.join(map(clean,[i['topic']+' / '+i['semantic_key'],i['source_reference'],i['reason'],i['prior_turn_status'],'yes' if i['included_in_model_payload'] else 'no']))+' |')
   text('')
  text('### Exact client generation payload','');obj(a['client_generation_payload'])
text('# Every Final Draft','','All subjects and bodies are verbatim. Rejected candidates are explicitly distinguished from persisted DraftRevisions. None was approved or sent.','')
for c in data['results']:
 for t in c['turns']:text(f"## {c['scenario_id']}/{t['turn_number']}",'');draft(t)
text('# Regression Targets','')
for target in status['regression_targets']:
 text('## '+target['turn'],'','Previous defect: '+target['previous_defect'],'','Planner decision: '+target['planner_decision'],'','Result: **'+target['result']+'**. '+target['assessment'],'')
 cid,turn=target['turn'].split('/');c=next(c for c in data['results'] if c['scenario_id']==cid);draft(next(t for t in c['turns'] if t['turn_number']==int(turn)))
text('# Human Acceptance Review','','These are direct assistant reviews of every exact draft and its plan, not an external LLM judge or an independent human acceptance study. Grades are secondary to demonstrated defects.','',
'| Turn | Operator feel | Unnecessary fact | Repetition | Policy-copy feel | System-language leakage | Unanswered request | Missing client question | Materially shorter | Grade |','|---|---|---|---|---|---|---|---|---|---|')
for key,r in reviews.items():
 vals=[key,r['operator_feel'],*('yes' if r[k] else 'no' for k in ['unnecessary_fact','repetition','policy_copy','system_language','unanswered_request','missing_client_question','materially_shorter']),r['grade']]
 text('| '+' | '.join(vals)+' |')
text('')
for key,r in reviews.items():text('**'+key+':** '+r['reason'],'')
text('# Coverage and Safety','','The preceding baseline had 21/21 persisted drafts and 7/7 continuity. Final coverage regressed to 19/21 and 6/7 because both supplier candidates failed the preserved validator. Accepted-only grades do not erase that regression. Safety-content counts below apply to persisted drafts; both rejected candidates and their exact known_no_contradiction codes are retained separately. Unanswered-request flags on those two turns reflect the lack of a persisted answer.','');obj(status['metrics'])
text('## Transport recovery','','A Render HTTP 502 occurred during creation of UAT-004 before any client turn or model call. The original result file is preserved with its hash; only that unrun scenario was retried on the same deployed Pass 2 code. Accepted and rejected generations were not repeated. The run used 21 generation requests in each pass.','')
text('# Tests','','The full repository suite uses `pytest --import-mode=importlib` because Phase 7 and Phase 8 contain test modules with identical basenames. Initial default collection hit that name collision; the importlib run includes both modules. Tests use local Postgres and fake provider transports. No test requires real Outlook or Asana. JUnit evidence is retained per pass.','');obj(status['tests'])
text('# Deployment','');obj(status['deployment'])
text('# Safety Activity','');obj(status['safety'])
text('# Evidence','','`pass1_results.json` and `pass2_results.json` retain the frozen turns and route logs. `pass2_results_raw.json` preserves the initial transport failure; `pass2_transport_recovery.json` records its bounded recovery. `pass2_planner_audit.json` holds all 21 plans and exact client payloads, including rejected candidates. The plan, contract and current-state audit files record provider-free checks. Rejection and topic-collision diagnostics preserve the unresolved causes. Original scenarios and baseline evidence hashes remain unchanged.','','# Remaining Limitations','')
for x in status['remaining_issues']:text('- '+x)
text('','# Final Marker','',status['final_marker'])
(p/'EDITORIAL_CONTENT_PLANNER_REPORT.md').write_text('\n'.join(lines)+'\n')
print(p/'EDITORIAL_CONTENT_PLANNER_REPORT.md')
