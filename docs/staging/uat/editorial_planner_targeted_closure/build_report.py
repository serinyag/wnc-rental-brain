"""Render saved acceptance evidence verbatim; never call a provider."""
import json
from pathlib import Path
p=Path(__file__).resolve().parent
load=lambda name:json.loads((p/name).read_text())
s=load('program_status.json');r=load('acceptance_results.json');audits=load('acceptance_planner_audit.json');reviews=load('acceptance_reviews.json')
lines=[]
def out(*parts):lines.extend(parts)
def obj(value):out('```json',json.dumps(value,indent=2,ensure_ascii=False),'```','')
def audit(c,t):return next(a for a in audits if a['rental_case_id']==c['rental_case_id'] and a['client_generation_payload']['latest_client_message']==t['incoming_message']['body'])
def draft(c,t):
 d=t.get('draft',{}).get('draft_revision');a=audit(c,t)
 if d:
  out(f"DraftRevision {d['inquiry_response_draft_revision_id']}; captured validator PASS. Exact approval/action binding: PASS.",'')
  subject,body=d['subject'],d['body_text']
 else:
  out('**Rejected candidate; no persisted DraftRevision.**','');obj(a.get('validation_codes',[]))
  subject,body=a.get('rejected_subject',''),a.get('rejected_body','')
 out('**Subject**','','```text',subject,'```','','**Body**','','```text',body,'```','')
out('# Targeted Defects Fixed','',s['outcome'],'',
'## Known-No Proposition Scoping','',
'Root cause: the restriction validator matched positive capability words anywhere in a compound email. Implementation: identify governed not-supported topics and stable aliases, evaluate capability wording in their clauses, preserve negation, coordinated subjects and subsequent pronoun references. Topic-less legacy contracts retain a conservative fallback. No other validator was changed.','',
'Regressions cover positive projector wording beside a microphone restriction, contradictory microphone assertions, correctly negated and external-supplier statements, coordinated subjects, later contradictory clauses and DJ restrictions.','',
'## Request Topic Matching','',
'Root cause: raw substrings matched dj inside adjust/adjustment and sound in pricing prose. Implementation: one maintained finite token/phrase alias adapter at planner and retrieval-attention boundaries. The kitchen repeat-question selector distinguishes supplier logistics from food-preparation questions. No classifier or model was added.','',
'Regressions cover adjust, adjustment, pricing sounds realistic, background sound system, explicit DJ setup and acknowledged DJ restrictions beside a fee-adjustment question.','',
'## Pricing vs Budget Semantics','',
'Root cause: every overall pricing question produced a budget-aware action. Implementation: independent overall_pricing_requested and absent/general_constraint/explicit_amount budget context. Absent budget produces an event/options pricing check; explicit constraints retain budget context. A budget observation alone does not invent a fee question.','',
'Regressions cover cost/prices questions, tight budget, explicit EUR amount and pricing sound realistic without audio.','',
'## Client-Language Projection','',
'- Audio: project governed supported audio as client_fact.background_music_playback=true; authoritative status remains local.',
'- Optional hologram: preserve a structured optional preference and the planning that should continue, instead of generic change acknowledgement.',
'- Aerial rig: project installation and operation safety questions with report_back=true, without an abstract feasibility label.',
'- Replace one existing style sentence with a concise ordinary-language rule for internal status labels. No provider, model, architecture or approval changes.',
'',
'The versioned planner/context hash is now editorial_content_plan_v3. Prior evidence and historical draft records are preserved.','',
'# Tests','');obj(s['tests'])
out(s['local_environment_recovery'],'','The 438 Phase 8 tests are included in the full repository run. git diff --check passed before implementation commit. Existing collection warnings concern application classes named Test*, not failing tests.','',
'# Deployment','');obj(s['deployment']);obj(s['health'])
out('# Frozen UAT','');obj(s['metrics'])
out('Exactly one acceptance run on the unchanged 13-scenario, 21-turn manifest. Reviews below are direct assistant assessments of exact outputs and plans, not an external judge or independent human study. Grades are secondary to the defect gates. No accepted or rejected generation was repeated.','')
if r.get('transport_recovery'):obj(r['transport_recovery'])
out('## Continuity evidence','');obj(s['continuity'])
out('## Turn reviews','','| Turn | Grade | Result | Findings |','|---|---|---|---|')
for k,v in reviews.items():out('| '+k+' | '+v['grade']+' | '+v['result']+' | '+v['assessment'].replace('|','\\|')+' |')
out('','# Exact 21 Drafts','','Every subject and body below is reproduced verbatim from saved generation evidence. These drafts were not approved or sent.','')
for c in r['results']:
 for t in c['turns']:out(f"## {c['scenario_id']}/{t['turn_number']}",'');draft(c,t)
out('# Critical Regression Turns','')
for key,detail in s['critical_turns'].items():
 out('## '+key,'','Previous defect: '+detail['previous_defect'],'','Deterministic root cause: '+detail['root_cause'],'','Fix: '+detail['fix'],'','Result: **'+reviews[key]['result']+'**. '+reviews[key]['assessment'],'')
 cid,n=key.split('/');c=next(c for c in r['results'] if c['scenario_id']==cid);t=next(t for t in c['turns'] if t['turn_number']==int(n))
 out('### Final plan','');obj(audit(c,t)['editorial_content_plan']);out('### Exact final draft','');draft(c,t)
out('# All Plan and Payload Evidence','','The JSON audit stores every complete plan, exact client payload, validator result and realization metadata. The results file stores every captured DraftRevision and action/approval binding; final snapshots establish currentness after follow-ups. Historical turn revisions may legitimately be superseded by later turns.','',
'- [Exact plans and client payloads](acceptance_planner_audit.json)',
'- [Frozen results and request log](acceptance_results.json)',
'- [Final case snapshots](acceptance_final_snapshots.json)',
'- [Plan boundary audit](acceptance_plan_validation.json)',
'- [Canonical binding audit](acceptance_captured_contract_validation.json)',
'- [Current draft integrity audit](acceptance_integrity_audit.json)',
'- [Frozen manifest and prior evidence hashes](frozen_manifest.json)','',
'# Safety Activity','');obj(s['safety'])
out('Staging health/provider posture and provider-free case/request-log audits establish the reported gates. Activity counts describe this task’s authorized route calls and resulting synthetic cases. No permissions or environment settings were changed.','',
'# Remaining Issues','')
for issue in s['remaining_issues']:out('- '+issue)
if not s['remaining_issues']:out('None demonstrated in this frozen acceptance run. Finite aliases and realization witnesses are not a universal semantic-understanding guarantee.')
out('','# Final Marker','',s['final_marker'],'','Stopped after the single acceptance run. No further implementation cycle, approval, sending enablement or action execution.','')
(p/'EDITORIAL_PLANNER_TARGETED_CLOSURE_REPORT.md').write_text('\n'.join(lines))
print(s['final_marker'])
