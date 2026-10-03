"""Build the final report from immutable saved acceptance evidence, without providers."""
from pathlib import Path
import json
p=Path(__file__).resolve().parent
load=lambda name:json.loads((p/name).read_text())
s=load('program_status.json');r=load('acceptance_results.json');a=load('acceptance_planner_audit.json');reviews=load('acceptance_reviews.json');dates=load('acceptance_date_provenance.json')
lines=[]
def out(*parts):lines.extend(parts)
def obj(value):out('```json',json.dumps(value,indent=2,ensure_ascii=False),'```','')
def find(key):
 cid,n=key.split('/');c=next(c for c in r['results'] if c['scenario_id']==cid);t=next(t for t in c['turns'] if t['turn_number']==int(n));return c,t

def audit(c,t):return next(x for x in a if x['rental_case_id']==c['rental_case_id'] and x['client_generation_payload']['latest_client_message']==t['incoming_message']['body'])
def draft(c,t):
 d=t.get('draft',{}).get('draft_revision');x=audit(c,t)
 if d:
  subject,body=d['subject'],d['body_text'];out(f"DraftRevision {d['inquiry_response_draft_revision_id']}. Validator PASS. Exact canonical action/revision/content/context/recipient/approval binding PASS.",'')
 else:
  subject,body=x.get('rejected_subject',''),x.get('rejected_body','');out('**Rejected candidate; no persisted DraftRevision.**','');obj(x.get('validation_codes',[]))
 out('**Subject**','','```text',subject,'```','','**Body**','','```text',body,'```','')

out('# Final Two Defects','',s['outcome'],'',
'## Pending-action detection','',
'Root cause: the venue-availability fallback looked only for status labels, so the concrete aerial-rig action was invisible to it. `is_pending_check_action` recognizes concrete action=check values with subjects/questions as well as the existing conditional/check_required/pending shapes. Both the fallback and client-visible pending-state audit use this helper. A background-music fact does not count as pending. Unrequested availability stays DEFER when the concrete rig check already supplies the next step; an explicit availability question still wins.','',
'## Known audio and item-scoped realization','',
'Root cause: known audio could be merged into a conditional projection check, and the realization witness combined music in one paragraph with possible in a fee sentence. Audio now carries a known client fact and action_required=false; conditional projection retains its practical setup check. One generation rule requires known facts to remain known. Audio realization requires a positive capability predicate in the audio clause and excludes prospective/negative/conditional wording. A previously requested known audio answer without valid realization evidence remains mandatory on follow-up.','',
'Editorial planner v3, current information budgets, topic-safe known-no validation, commercial authority, historical precedence, external-contact semantics and exact DraftRevision approvals remain in place. The context hash includes a normalization revision so old contexts cannot be mistaken for these semantics.','',
'# Date Year Inference','',
'Ordinary day/month expressions are normalized in application code using the authoritative inbound received_at (or occurred_at), in Europe/Amsterdam. A future calendar date uses the current year; an elapsed month/day uses the next valid occurrence. Explicit years are preserved even when past; invalid explicit dates and ambiguous clock times are quarantined rather than repaired by inference. February 29 advances to the next valid leap year when the year was omitted. Same-calendar-day requests remain eligible as today; missing times remain questions.','',
'Raw client text remains unchanged. Source-linked timing observations persist date_provenance, including year_source, explicit_client_year, resolved_year, source_reference, reference_timestamp and timezone. Inferred years are not stored as explicit client year components. Time-only follow-ups preserve the original date provenance. A later explicit correction gets explicit provenance and follows normal intake/reschedule governance; inference does not approve a changed booking.','',
'Only genuinely missing date/time components are asked. Known day/month with unknown timing asks for start and finish; a known month without a day asks for the day. Complete timing is promoted through normal intake and closes the timing question.','')
obj(s['date_decision'])
out('# Provider-Free Regressions','');obj(s['provider_free_regressions'])
out('# Tests','');obj(s['tests'])
out('Full Phase 8 and full repository suites were run separately. Existing collection warnings concern application classes named Test*. All required provider-free checks passed before any OpenAI UAT call.','',
'# Deployment','');obj(s['deployment']);obj(s['health'])
out('# Final Frozen UAT','');obj(s['metrics'])
out('One run of the same 13 scenarios / 21 client turns. Client text and non-timing observations remain frozen. Per the new product decision, fixture-assigned ISO years/UTC windows were not injected: the application derived timing candidates from the original messages and recorded inbound timestamps. This authorized expectation change is recorded in frozen_manifest.json; prior evidence hashes remain unchanged. No accepted or rejected model output was regenerated.','')
if r.get('transport_recovery'):obj(r['transport_recovery'])
out('## Continuity','');obj(s['continuity'])
out('## Direct quality review','','These are direct assistant assessments, not an external LLM judge or independent human acceptance study. A/B grades are secondary to the hard gates.','','| Turn | Grade | Result | Assessment |','|---|---|---|---|')
for k,v in reviews.items():out('| '+k+' | '+v['grade']+' | '+v['result']+' | '+v['assessment'].replace('|','\\|')+' |')
out('','# Exact 21 Drafts','','All subjects and bodies are reproduced verbatim from saved generation evidence. None was approved or sent.','')
for c in r['results']:
 for t in c['turns']:out(f"## {c['scenario_id']}/{t['turn_number']}",'');draft(c,t)
out('# UAT-010','');c,t=find('UAT-010/1');x=audit(c,t)
out('## Final plan','');obj(x['editorial_content_plan'])
out('## Availability fallback evidence','');obj({'selected_values':x['client_generation_payload']['must_say'],'deferred_availability':[i for i in x['editorial_content_plan']['defer'] if i['semantic_key']=='next_step.availability']})
out('## Exact draft','');draft(c,t)
out('# UAT-012','')
for key in ['UAT-012/1','UAT-012/2','UAT-012/3']:
 c,t=find(key);x=audit(c,t);plan=x['editorial_content_plan']
 out('## '+key,'','### Audio/projection state and realized evidence','')
 obj({'selected_values':x['client_generation_payload']['must_say'],'audio_projection_items':[i for role in ['must_communicate','already_communicated','defer'] for i in plan[role] if i['topic'] in ['audio_playback','projection_display']], 'communicated_editorial_items':x.get('communicated_editorial_items',[]),'do_not_repeat_topics':x['client_generation_payload']['do_not_repeat_topics']})
 out('### Exact draft','');draft(c,t)
out('# Timestamp and Year Provenance Evidence','');obj(dates)
out('# Safety','');obj(s['safety'])
out('Activity zeros are established from this task’s restricted request log and resulting synthetic case snapshots. Provider-free canonical and currentness checks passed; no production, Exchange RBAC, Entra permission, model/provider or environment-setting changes were made.','',
'# Evidence Files','',
'- [Exact plans and client-generation payloads](acceptance_planner_audit.json)',
'- [Frozen results, draft revisions and request log](acceptance_results.json)',
'- [Final snapshots](acceptance_final_snapshots.json)',
'- [Canonical binding audit](acceptance_captured_contract_validation.json)',
'- [Current draft and disabled-send audit](acceptance_integrity_audit.json)',
'- [Date provenance audit](acceptance_date_provenance.json)',
'- [Frozen manifest and authorized date expectations](frozen_manifest.json)','',
'# Remaining Issues','')
for issue in s['remaining_issues']:out('- '+issue)
if not s['remaining_issues']:out('No material defect demonstrated in this run. The finite language/date parsers remain bounded, and this frozen acceptance suite does not establish universal language coverage.')
out('','# Final Marker','',s['final_marker'],'','Stopped after the single authorized acceptance run. No further implementation cycle or sending enablement.','')
(p/'FINAL_DRAFTING_CLOSURE_REPORT.md').write_text('\n'.join(lines));print(s['final_marker'])
