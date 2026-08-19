# Phase 8 Realistic Rental Scenario Validation

Date:

- August 14, 2026

Status:

- `PHASE_8_REALISTIC_RENTAL_SCENARIO_VALIDATION_COMPLETE`

Operational assessment:

- `TEST_CONSOLE_REQUIRES_REMEDIATION_BEFORE_INQUIRY_WORKFLOW_BUILD`

## Executive Summary

If a WNC operator opened the current system today, they could:

- create isolated test RentalCases
- inject raw test evidence
- inject selected structured observations
- run existing reconciliation
- see approvals, blockers, decisions, actions, execution attempts, and human-work preview on richer cases
- execute at least the internal deterministic success path that was already present on case `143`

What they cannot yet do reliably is run a truthful first-inquiry loop from inbound rental information to an operator-usable working proposal.

The biggest missing connection is not a single business rule. It is the end-to-end bridge from persisted structured observations to a truthful human-facing rental overview and next-step workflow. The current runtime can persist meaningful workflow objects, but the Working Proposal still drops too much known state, leaves too many fields `unknown`, and does not yet expose a usable operator narrative for common inquiry handling.

The other major operational blocker is console reliability. During this audit, the local console on `http://127.0.0.1:8765` repeatedly timed out on plain root and case-page reads, including after restart. That moves the system from "rough but usable" into "requires remediation before the first real inquiry MVP can be built on top of it."

## Environment

Workspace:

- `/Users/serinya/Documents/WNC Rental Automation`

Repository state:

- `git rev-parse HEAD` failed with `fatal: ambiguous argument 'HEAD'`
- `git status --short` showed the workspace as effectively untracked from Git's perspective during this audit

Console launch:

- readiness doc launch command: `python3 -m tools.phase_08_workflow.test_console`
- live process used during audit: `python3 -u -m tools.phase_08_workflow.test_console --port 8765`

Console configuration confirmed from source:

- host: `127.0.0.1`
- port: `8765`
- `WORKFLOW_TEST_CONSOLE_ALLOW_REAL_PROVIDERS=false`
- `WORKFLOW_TEST_CONSOLE_ALLOW_NON_LOCAL_BIND=false`

Provider mode:

- fake only
- banner contract in source: `REAL PROVIDER EXECUTION DISABLED`
- email execution maps to deterministic fake
- task-surface execution maps to deterministic fake

Primary evidence cases:

- case `143` / `RC-20260814121627957`
  - minimal case with one successfully executed internal action and one persisted execution attempt
- case `145` / `RC-20260814124011673`
  - richest case used for booking-fee, approval, reschedule, Working Proposal, and human-work inspection
- case `146`
  - `AUDIT S01 Straightforward Venue Inquiry`
- case `147`
  - `RVA S01 Straightforward Venue Inquiry`
- case `148` / `RC-20260814130519697`
  - `AUDIT3 S02 Incomplete Inquiry`

Methodology note:

- This audit stayed inside the black-box / grey-box boundary:
  - `Test Console -> current runtime -> Supabase`
- Direct DB inspection was used only to verify persisted results after console actions.
- No code changes, schema changes, rule changes, or manual row inserts were used.
- Once the console and later direct DB probes became unstable, unsupported and blocked scenarios were recorded honestly rather than forced through private methods.

## Capability Inspection

| Capability | Observed status | Basis |
| - | - | - |
| Raw inbound evidence injection | Yes | Root and case forms, prior successful runtime use |
| Structured test observation injection | Yes | Case form routes and prior successful runtime use |
| Phase 7 reasoning invocation | No direct console control observed | UI surface inspection |
| Orchestration reconciliation | Yes | Case reconcile form and prior successful runtime use |
| Approval / rejection | Yes | Case approval controls on case `145` |
| Fake execution | Yes | Execution mode selector and prior internal success path on case `143` |
| Real Asana execution | No in audit mode | Disabled by provider guard |
| Real Outlook execution | No in audit mode | Disabled by provider guard |

## Scenario Scorecard

| # | Scenario | Result | Main finding |
| - | -------- | ------ | ------------ |
| 1 | Straightforward Venue Inquiry | `PARTIAL` | Evidence persisted, but the operator-facing result never became a usable inquiry view. |
| 2 | Incomplete Inquiry | `PARTIAL` | The system did not obviously invent details, but it also did not surface useful open questions. |
| 3 | Capacity / Large Guest Count | `NOT CURRENTLY SUPPORTED` | Whole-venue feasibility and capacity evaluation are not wired into the current console path. |
| 4 | Unsupported Exact Request but Possible Alternative | `NOT CURRENTLY SUPPORTED` | Alternative-first feasibility is not exposed as a usable end-to-end console behavior. |
| 5 | Booking Fee Waiver | `PARTIAL` | Approval-gated decision safety worked, but the commercial state stayed too opaque for a human operator. |
| 6 | Historical Storage Price Trap | `BLOCKED BY MISSING GOVERNED RULE` | No current governed storage-price authority was available to validate against. |
| 7 | Material Guest Count Change | `NOT CURRENTLY SUPPORTED` | Change-impact handling is not yet surfaced through a distinct proposed-change path. |
| 8 | Reschedule Request | `PARTIAL` | The backend safely created a reschedule request, but the Working Proposal did not explain it clearly. |
| 9 | Minor Operational Change | `BLOCKED BY MISSING GOVERNED RULE` | No governed minor-change classification path was available to evaluate. |
| 10 | Clearly Material Operational Change | `BLOCKED BY MISSING GOVERNED RULE` | No governed materiality boundary was available for this kind of operational escalation. |
| 11 | Follow-Up | `NOT CURRENTLY SUPPORTED` | Follow-up evaluation exists, but no usable follow-up creation/progression path was exposed. |
| 12 | Stale Client Email Action | `NOT CURRENTLY SUPPORTED` | The current audit surface did not expose the needed client-email stale-action path. |
| 13 | Superseded Action | `NOT CURRENTLY SUPPORTED` | The current console did not provide a reliable way to create and compare superseding actions. |
| 14 | Approval-Required Action | `PARTIAL` | Approval controls exist, but the full blocked-then-approved execution path was not completed reliably. |
| 15 | Fake Provider Failure | `PARTIAL` | Failure modes are exposed in the console, but the operator-path failure run could not be completed after instability began. |
| 16 | Fake Timeout / Ambiguous Result | `NOT CURRENTLY SUPPORTED` | Timeout and ambiguous modes are selectable, but not fully operationally validated through the live console path. |
| 17 | Cross-Case Isolation | `PARTIAL` | Normal UI routes are strongly case-scoped, but a deliberate two-case integrity attempt could not be completed cleanly. |
| 18 | Human Working Proposal Audit | `PARTIAL` | The proposal shows blockers and next actions, but it still hides too much known rental truth. |
| 19 | Asana Human Work Projection | `PARTIAL` | Human-work preview exists and is directionally useful, but not yet sufficient for a staff handoff. |
| 20 | Empty / New Rental | `FAIL` | The empty-state flow is not operationally reliable because the console repeatedly timed out at root and case-page level. |

## Detailed Scenario Reports

## Scenario 1 - Straightforward Venue Inquiry

Purpose:

- Validate a simple venue inquiry with modest guest count, timing, and external catering.

Input:

- Raw email:
  - October 3 private brand event
  - about 35 guests
  - 18:00 to 22:00
  - venue rental only
  - client bringing external catering
- Structured observations attempted:
  - `guest_count=35`
  - `active_event_window=2026-10-03 18:00-22:00 UTC`
  - `catering_arrangement=client_external_caterer`

Steps:

- Create test case `146` / `147`
- Inject raw evidence
- Inject structured observations
- Run reconciliation

Initial persisted state:

- Captured state for the surviving scenario snapshot showed:
  - `source_records=2`
  - `observations=1`
  - `effects=1`
  - lifecycle remained `inquiry_active`

Derived workflow state:

- No approvals observed
- No blockers observed
- No actions observed
- No follow-ups observed
- No reschedule requests observed

Working Proposal:

- Not reliably recoverable once the console began timing out

Human actions available:

- Case detail controls existed in the console design
- This specific scenario did not yield meaningful operator work

Execution:

- Not reached

Audit:

- Workflow event capture was present in the DB snapshot

Expected behavior:

- Preserve inbound evidence
- Keep unknowns explicit
- Surface at least a minimal operator-facing interpretation and next questions

Actual behavior:

- Evidence persisted
- The case did not mature into a useful inquiry-handling view
- The console later became unavailable for deeper inspection

Result:

- `PARTIAL`

Issues:

- `BUG-001`
- `UX-001`

## Scenario 2 - Incomplete Inquiry

Purpose:

- Test whether uncertainty remains explicit instead of fabricated.

Input:

- Raw email:
  - interested in renting sometime in October
  - asks for information
  - no exact date, count, duration, or format

Steps:

- Create test case `148`
- Inject raw evidence
- Run reconciliation

Initial persisted state:

- Case `148` was confirmed to exist as `RC-20260814130519697`

Derived workflow state:

- Full row-by-row state was not recoverable after the console and DB probes began stalling

Working Proposal:

- Could not be reloaded reliably

Human actions available:

- Not cleanly inspectable after the console degraded

Execution:

- Not applicable

Audit:

- Case creation and runtime entry were confirmed

Expected behavior:

- No fabricated date
- No fabricated guest count
- No fabricated duration
- No fabricated rental scope

Actual behavior:

- No fabricated truth was observed
- Also no usable open-question workflow was surfaced to the operator

Result:

- `PARTIAL`

Issues:

- `BUG-001`
- `UX-001`

## Scenario 3 - Capacity / Large Guest Count

Purpose:

- Test whether an 85-guest whole-venue inquiry triggers a usable feasibility posture.

Input:

- Whole-venue activation for 85 guests

Steps:

- Prepared as an audit scenario
- Related observed runtime evidence came primarily from case `145`, which included `guest_count=85`

Initial persisted state:

- Rich case `145` preserved the 85-guest context in inbound observation handling

Derived workflow state:

- No connected whole-venue capacity or feasibility decision was surfaced through the console path

Working Proposal:

- Feasibility remained effectively pending / unknown
- No usable capacity interpretation was shown

Human actions available:

- No capacity-specific operator path was exposed

Execution:

- Not applicable

Audit:

- No contradictory or unsafe capacity truth was observed

Expected behavior:

- Distinguish whole-venue feasibility from studio-only assumptions

Actual behavior:

- The current console/runtime does not operationally expose this evaluation

Result:

- `NOT CURRENTLY SUPPORTED`

Issues:

- `TEST_HARNESS_GAP-001`

## Scenario 4 - Unsupported Exact Request but Possible Alternative

Purpose:

- Test alternative-first feasibility for a professional-kitchen request.

Input:

- Client requests a chef showcase with access to a full professional kitchen

Steps:

- Prepared as an audit scenario
- No successful end-to-end alternative-feasibility path was observed in the current console/runtime

Initial persisted state:

- Not fully captured through a complete case run

Derived workflow state:

- No alternative-first workflow surface was observed

Working Proposal:

- No operator-readable exact-vs-alternative feasibility distinction was demonstrated

Human actions available:

- None specific to this decision path

Execution:

- Not applicable

Audit:

- No unsafe invented capability was observed

Expected behavior:

- Do not invent a professional kitchen
- Distinguish exact infeasibility from a possible supported alternative

Actual behavior:

- The current console/runtime does not operationally express this path

Result:

- `NOT CURRENTLY SUPPORTED`

Issues:

- `TEST_HARNESS_GAP-002`

## Scenario 5 - Booking Fee Waiver

Purpose:

- Validate approval-gated case-specific commercial exception handling.

Input:

- Blue Ridge Community Summit
- about 85 guests
- October 24, 2026
- external catering
- AV, microphones, simple lighting, theater layout, check-in table
- request for booking-fee flexibility

Steps:

- Create rich test case `145`
- Inject raw evidence
- Inject structured observations for:
  - `guest_count`
  - `active_event_window`
  - `catering_arrangement`
  - `technical_requirements`
  - `layout_requirements`
  - `event_day_contact`
  - `booking_fee_override`
- Run reconciliation

Initial persisted state:

- `rental_cases.lifecycle_status=inquiry_active`
- `rental_cases.case_revision=0`

Derived workflow state:

- `rental_case_decisions`
  - decision `25`
  - `decision_code=booking_fee_override`
  - `decision_status=proposed`
  - `approval_posture=approval_required`
- `rental_case_approval_requests`
  - approval `37`
  - status `open`
- `rental_case_blockers`
  - blocker `49`
  - `case_decision_approval_required`
- `rental_case_reschedule_requests`
  - request `8`
  - proposed October 24, 2026 time window
- `workflow_actions`
  - two ready internal task items (`70`, `71`)

Working Proposal:

- Correctly did not show the fee waiver as active truth before approval
- Still showed too much as `unknown`, including:
  - booking fee
  - VAT
  - event date
  - event time
  - guest count
  - operational fields such as catering, layout, technical, and event-day contact
- Blockers and approvals were visible

Human actions available:

- Approve
- Reject
- Execute internal actions
- Reconcile
- Evaluate follow-ups

Execution:

- Decision-activation path after approval was not fully completed in the surviving audit evidence

Audit:

- Structured observation reports showed:
  - `guest_count -> no_workflow_effect`
  - `active_event_window -> create_reschedule_request`
  - `booking_fee_override -> create_case_decision_candidate`
- Reconciliation created approvals, blockers, and actions without mutating global truth

Expected behavior:

- Global booking fee remains governed baseline before approval
- Proposed waiver stays separate
- Human operator can see both the baseline and the pending exception

Actual behavior:

- Safety was good before approval
- Human commercial clarity was not good enough

Result:

- `PARTIAL`

Issues:

- `BUG-002`
- `BUG-003`

## Scenario 6 - Historical Storage Price Trap

Purpose:

- Ensure historical price precedent does not become current truth without current authority.

Input:

- Storage-cost-sensitive case concept using historical `EUR 300` as the trap value

Steps:

- Scenario framed against the current runtime and Working Proposal behavior
- No current governed storage-price authority was available through the console path

Initial persisted state:

- No completed storage-price case run

Derived workflow state:

- No current storage-price authority surfaced

Working Proposal:

- No historical storage price was shown as current truth in the observed cases

Human actions available:

- None sufficient to resolve pricing truth

Execution:

- Not applicable

Audit:

- No unsafe historical-to-current promotion was observed

Expected behavior:

- Refuse to present `EUR 300` as active policy without current authority

Actual behavior:

- The runtime did not provide enough governed authority to complete the scenario safely

Result:

- `BLOCKED BY MISSING GOVERNED RULE`

Issues:

- `BUSINESS_RULE_GAP-001`

## Scenario 7 - Material Guest Count Change

Purpose:

- Test whether a later guest-count increase becomes a proposed change instead of silent truth mutation.

Input:

- Start at 30 guests
- Later update to 60 guests

Steps:

- Related evidence came from guest-count handling on case `145`

Initial persisted state:

- Guest-count observations were accepted into the inbound observation flow

Derived workflow state:

- Observed `guest_count` handling produced `Disposition: no_workflow_effect`
- No `rental_case_proposed_changes` record was observed
- No impact-evaluation path was surfaced

Working Proposal:

- Did not show a clean current-vs-proposed distinction

Human actions available:

- None specific to accepting or rejecting the change

Execution:

- Not applicable

Audit:

- No silent material truth overwrite was observed

Expected behavior:

- Proposed change object
- explicit impact evaluation
- no premature Working Proposal mutation

Actual behavior:

- The change architecture is not yet exposed operationally in the current console path

Result:

- `NOT CURRENTLY SUPPORTED`

Issues:

- `TEST_HARNESS_GAP-003`

## Scenario 8 - Reschedule Request

Purpose:

- Validate proposed date change handling.

Input:

- Original event context
- Later request to move timing to October 24, 2026 from 15:00 to 21:00 UTC in case `145`

Steps:

- Inject `active_event_window` structured observation on case `145`

Initial persisted state:

- Original active snapshot remained null in the captured row

Derived workflow state:

- `rental_case_reschedule_requests` row created
- `current_active_date_snapshot` remained separate from `requested_date_payload`

Working Proposal:

- Did not mutate active date directly
- Also did not explain the proposed date clearly enough to the human

Human actions available:

- Reconcile
- general approval/action controls on the case

Execution:

- No date-change acceptance flow was completed

Audit:

- Reschedule request creation was a meaningful positive result

Expected behavior:

- Proposed date separate from active truth

Actual behavior:

- Backend posture was safe
- Human-facing communication remained incomplete

Result:

- `PARTIAL`

Issues:

- `BUG-004`

## Scenario 9 - Minor Operational Change

Purpose:

- Check whether a small operational add-on is handled without inflation or invention.

Input:

- Small flower arrangement for a welcome table

Steps:

- Scenario assessed against observed handling of operational structured inputs on case `145`

Initial persisted state:

- Operational facts such as catering, technical needs, layout, and event-day contact were accepted as observations

Derived workflow state:

- Observed dispositions were `no_workflow_effect`

Working Proposal:

- Operational values still displayed as `unknown`

Human actions available:

- No dedicated low-impact operational review path

Execution:

- Not applicable

Audit:

- No invented fee or severe blocker was observed

Expected behavior:

- Remain evidence or low-impact proposed change
- avoid invented policy

Actual behavior:

- The current system lacks the governed classification needed to finish this scenario meaningfully

Result:

- `BLOCKED BY MISSING GOVERNED RULE`

Issues:

- `BUSINESS_RULE_GAP-002`

## Scenario 10 - Clearly Material Operational Change

Purpose:

- Check whether a major operational escalation is treated differently from a small one.

Input:

- approximately 400 flower arrangements plus extra setup access

Steps:

- Scenario assessed against the same observed `no_workflow_effect` pattern on operational fields

Initial persisted state:

- No completed runtime case produced a material operational reassessment object

Derived workflow state:

- No materiality boundary or reassessment path was surfaced

Working Proposal:

- No clear distinction between minor and material operational implications was available

Human actions available:

- None specific to material operational reevaluation

Execution:

- Not applicable

Audit:

- The absence of a governed classification boundary prevented a safe deterministic judgment

Expected behavior:

- Trigger reassessment without inventing unsupported policy

Actual behavior:

- The current system cannot complete this distinction safely

Result:

- `BLOCKED BY MISSING GOVERNED RULE`

Issues:

- `BUSINESS_RULE_GAP-003`
- `BUG-005`

## Scenario 11 - Follow-Up

Purpose:

- Test whether due follow-ups route back into normal workflow instead of directly sending mail.

Input:

- cold/new inquiry needing scheduled follow-up

Steps:

- Use follow-up evaluation on case `143`

Initial persisted state:

- No follow-ups existed on the observed case

Derived workflow state:

- Follow-up evaluation returned:
  - evaluated follow-ups: `0`
  - due follow-ups: `0`
  - overdue follow-ups: `0`
  - created actions: `0`

Working Proposal:

- No follow-up-specific operator guidance surfaced

Human actions available:

- `Evaluate Follow-Ups` button exists

Execution:

- No follow-up-generated action to execute

Audit:

- No evidence of direct provider invocation from follow-up evaluation

Expected behavior:

- schedulable follow-up flow
- due state
- overdue state
- action creation through normal workflow

Actual behavior:

- The evaluation hook exists, but the full operator path does not

Result:

- `NOT CURRENTLY SUPPORTED`

Issues:

- `TEST_HARNESS_GAP-004`

## Scenario 12 - Stale Client Email Action

Purpose:

- Ensure a client-email action cannot execute after the case has materially changed.

Input:

- client-email action bound to one case revision, then later case mutation

Steps:

- Scenario could not be completed through the current audit surface

Initial persisted state:

- Not reached end-to-end

Derived workflow state:

- No completed stale client-email action path was observed

Working Proposal:

- Not applicable

Human actions available:

- No reliable client-email stale-action path was exposed

Execution:

- Not reached

Audit:

- No unsafe provider invocation was observed

Expected behavior:

- reject stale execution
- provider invocation count stays `0`

Actual behavior:

- The current console path did not expose this scenario reliably enough to validate

Result:

- `NOT CURRENTLY SUPPORTED`

Issues:

- `TEST_HARNESS_GAP-005`

## Scenario 13 - Superseded Action

Purpose:

- Ensure an older action is rejected once superseded by newer semantic work.

Input:

- two actions with the later one superseding the former

Steps:

- Scenario could not be formed cleanly from the current console surface

Initial persisted state:

- Not reached end-to-end

Derived workflow state:

- No explicit supersession visualization was observed in the current console

Working Proposal:

- Not applicable

Human actions available:

- Current console did not expose a reliable supersession comparison path

Execution:

- Not reached

Audit:

- No duplicate side effect was observed

Expected behavior:

- reject old action
- provider invocation count stays `0`

Actual behavior:

- Not operationally testable through the current surface

Result:

- `NOT CURRENTLY SUPPORTED`

Issues:

- `TEST_HARNESS_GAP-006`

## Scenario 14 - Approval-Required Action

Purpose:

- Validate blocked-before-approval and eligible-after-approval behavior.

Input:

- approval-required work associated with case `145`

Steps:

- Observe open approval and approve/reject controls
- Observe ready internal actions on the same case

Initial persisted state:

- approval request `37` open
- decision `25` proposed
- blocker `49` open

Derived workflow state:

- Approval gate was visible
- Case was not allowed to silently activate the decision

Working Proposal:

- Approval requirement and blocker were visible

Human actions available:

- Approve
- Reject
- Execute actions

Execution:

- Full before-approval rejection and after-approval success path was not captured end-to-end in surviving audit evidence

Audit:

- Approval and blocker creation were correctly recorded

Expected behavior:

- pre-approval execution blocked
- post-approval execution eligible if other guards pass

Actual behavior:

- Approval surface exists, but the full operator path was not reliably completed under console instability

Result:

- `PARTIAL`

Issues:

- `BUG-001`
- `UX-002`

## Scenario 15 - Fake Provider Failure

Purpose:

- Validate deterministic failure handling.

Input:

- eligible action run through fake failure mode

Steps:

- Confirmed from console source that execution modes include:
  - `retryable_failure`
  - `permanent_failure`
  - `timeout`
  - `ambiguous`
- Confirmed separately from case `143` that the internal success path can create an execution attempt and mark success

Initial persisted state:

- Case `143` already demonstrated:
  - action `68` -> `succeeded`
  - execution attempt `37` -> `succeeded`

Derived workflow state:

- Failure-mode controls are present in the UI

Working Proposal:

- Not central to this scenario

Human actions available:

- Execute action with fake execution mode selector

Execution:

- The live failure-mode run could not be completed once the console began timing out

Audit:

- Existing success-path evidence proves the execution surface is at least partially live

Expected behavior:

- execution attempt recorded
- action not marked succeeded
- no silent lifecycle advancement

Actual behavior:

- The surface appears to support this, but the operator-path failure case was not completed reliably

Result:

- `PARTIAL`

Issues:

- `BUG-001`
- `TEST_HARNESS_GAP-007`

## Scenario 16 - Fake Timeout / Ambiguous Result

Purpose:

- Validate that timeout or ambiguity never becomes success.

Input:

- eligible action with `timeout` or `ambiguous` execution mode

Steps:

- Console source confirmed both selector values exist

Initial persisted state:

- No completed runtime example was captured

Derived workflow state:

- Not validated end-to-end

Working Proposal:

- Not central to this scenario

Human actions available:

- Timeout and ambiguous modes are selectable in the UI design

Execution:

- Not fully completed through the live console path

Audit:

- No contradictory success-on-timeout result was observed

Expected behavior:

- timeout is not success
- ambiguous is not success
- no blind duplicate retry

Actual behavior:

- The current operator path did not allow a clean completed validation

Result:

- `NOT CURRENTLY SUPPORTED`

Issues:

- `TEST_HARNESS_GAP-008`

## Scenario 17 - Cross-Case Isolation

Purpose:

- Verify that one case cannot accidentally mutate another through normal console use.

Input:

- Case A
- Case B

Steps:

- Inspect the current console routes and forms

Initial persisted state:

- All observed console actions are case-scoped by URL:
  - `/cases/{id}/raw-evidence`
  - `/cases/{id}/structured-observations`
  - `/cases/{id}/reconcile`
  - `/cases/{id}/approvals/{approval_id}/approve`
  - `/cases/{id}/actions/{action_id}/execute`

Derived workflow state:

- No normal UI control was observed that cross-wired case data intentionally

Working Proposal:

- Separate per case

Human actions available:

- Only case-local actions are exposed

Execution:

- A deliberate two-case integrity attempt was not completed once console instability set in

Audit:

- No cross-case mutation was observed

Expected behavior:

- reject cross-case mutation

Actual behavior:

- Surface design is case-scoped, but the audit did not complete a stronger integrity challenge through the live console

Result:

- `PARTIAL`

Issues:

- `TEST_HARNESS_GAP-009`

## Scenario 18 - Human Working Proposal Audit

Purpose:

- Assess whether the richest case is actually understandable to a WNC operator.

Basis case:

- case `145`

Field ratings:

- Client identity: `CLEAR`
- What event is proposed: `PARTIALLY CLEAR`
- When: `MISLEADING`
- How many people: `MISLEADING`
- What space: `MISSING`
- Commercial position: `MISLEADING`
- Current feasibility: `PARTIALLY CLEAR`
- What is still unknown: `PARTIALLY CLEAR`
- Current blockers: `CLEAR`
- Pending approvals: `CLEAR`
- Proposed changes: `PARTIALLY CLEAR`
- Next action: `PARTIALLY CLEAR`
- Last relevant communication: `PARTIALLY CLEAR`
- Fresh / stale status: `MISSING`

Working Proposal strengths:

- Blockers visible
- Approvals visible
- Next actions visible
- No premature activation of the booking-fee waiver

Working Proposal weaknesses:

- Structured rental knowledge was not surfaced as current known context
- Proposed schedule was not explained clearly
- Commercial baseline was not explicit

Result:

- `PARTIAL`

Issues:

- `BUG-002`
- `BUG-003`
- `BUG-004`
- `UX-001`

## Scenario 19 - Asana Human Work Projection

Purpose:

- Determine whether the system exposes sensible staff work without enabling production Asana.

Basis case:

- case `145`

Observed state:

- `Asana Master Task` panel exists
- `Human Work Preview` panel exists
- Preview is explicitly described as derived from structured state, not live Asana state

Operator answer:

- `PARTIALLY`

Why:

- A staff member can see that approvals and internal tasks exist
- A staff member cannot yet rely on the proposal alone to understand the full commercial and operational picture

Result:

- `PARTIAL`

Issues:

- `UX-001`
- `UX-002`

## Scenario 20 - Empty / New Rental

Purpose:

- Validate empty-state quality and guard against fabricated truth or crashes.

Input:

- Minimal newly created test RentalCase through the root create form

Steps:

- Root create flow was previously used successfully during earlier audit steps
- Later, repeated attempts to load the root page and case pages timed out
- Browser navigation to the root page also timed out

Initial persisted state:

- Minimal cases such as `143` did not show obvious fabricated facts in the surviving observed state

Derived workflow state:

- No accidental actions or approvals were observed on the minimal case

Working Proposal:

- Empty-ish cases did not obviously backfill historical truths

Human actions available:

- Operationally unreliable because the page itself repeatedly stalled

Execution:

- Not applicable

Audit:

- `curl --max-time 5 http://127.0.0.1:8765/` timed out with `0 bytes received`
- Browser navigation to the same URL timed out with `Page.navigate`
- The timeout repeated after restarting the console on the same port

Expected behavior:

- New cases open reliably
- unknown remains unknown
- no crashes

Actual behavior:

- Truth-safety looked acceptable in the minimal surviving state
- Basic operator usability failed because the console repeatedly stopped responding

Result:

- `FAIL`

Issues:

- `BUG-001`

## Safety Invariants

Observed violation counts:

| Metric | Observed violation count | Note |
| - | - | - |
| observation -> direct material truth mutation | `0` | No silent material fact overwrite was observed. |
| generated prose -> workflow truth | `0` | No prose-only activation path was observed. |
| historical precedent -> current policy promotion | `0` | No historical value was observed becoming current truth in tested cases. Scenario 6 remained blocked by missing authority. |
| unapproved CaseDecision activation | `0` | Case `145` kept the booking-fee waiver separate before approval. |
| direct UI lifecycle mutation | `0` | No direct lifecycle edit controls were observed. |
| direct UI action-state mutation | `0` | Action mutation remained behind runtime execution. |
| pre-approval execution | `0` | No pre-approval bypass was observed. |
| blocked execution counted as success | `0` | No such contradiction was observed. |
| stale execution counted as success | `0` | Not fully exercised; no violation observed. |
| superseded execution counted as success | `0` | Not fully exercised; no violation observed. |
| duplicate semantic execution | `0` | No duplicate provider side effect was observed. |
| execution failure counted as success | `0` | Failure modes were not fully run; no false success observed. |
| follow-up directly invoking provider | `0` | Follow-up evaluation on case `143` created no provider side effect. |
| cross-case mutation | `0` | No cross-case mutation was observed through normal UI paths. |
| Working Proposal showing proposed state as active truth | `0` | The main failure was omission / unknown display, not premature activation. |

## UX Findings

Case overview:

- Strongest on blockers, approvals, and visible actions
- Weakest on known rental facts and commercial clarity

Working Proposal:

- Best at staying conservative
- Worst at surfacing already known structured information

Action visibility:

- Action controls are visible
- Relationship between action, approval, and case narrative is not strong enough

Approval clarity:

- Approvals are visible and explicit
- Human impact of each approval is not expressed clearly enough in the overview

Stale / superseded clarity:

- Not surfaced clearly enough to support operator trust

Event timeline usefulness:

- Useful as an audit surface
- Not enough on its own to make the case operationally understandable

Operator understanding:

- Partial at best on the richest case
- poor once the console starts timing out

## Missing Workflow Connections

1. Structured observations are not yet turning into a consistently truthful case overview.
2. Inquiry uncertainty is not yet surfacing as operator-facing open questions in a usable way.
3. Proposed commercial and schedule changes are persisted, but not communicated clearly enough in the Working Proposal.
4. Operational facts and operational changes are accepted into the system but not projected back into meaningful human work.
5. Failure, timeout, stale, and superseded execution paths exist architecturally, but not yet as a reliable operator-validation loop in the console.

## Business Rule Gaps

1. Current governed storage pricing authority was not available for the historical-price trap scenario.
2. WNC does not yet expose a governed minor-vs-material operational change classification path for the tested scenarios.
3. The current audit surface did not expose a governed exact-vs-supported-alternative policy path for the professional-kitchen request.

## Bugs

### BUG-001

- Severity: `High`
- Scenario: `20`, also affected `1`, `2`, `14`, `15`
- Reproduction steps:
  - launch `python3 -u -m tools.phase_08_workflow.test_console --port 8765`
  - request `GET /` or navigate to a case page after modest console use
  - wait 5-20 seconds
- Expected:
  - root and case pages return promptly and remain available during normal audit use
- Actual:
  - root page and case pages repeatedly hung with no bytes returned
  - browser navigation timed out
  - the same behavior reproduced after restarting the console on the same port
- Affected component:
  - test console request path / runtime availability
- Suggested next remediation scope:
  - isolate the blocking call chain for root and case-detail reads before any new inquiry-loop work

### BUG-002

- Severity: `High`
- Scenario: `5`, `18`
- Reproduction steps:
  - create or open rich case `145`
  - inject structured observations for guest count, catering, technical, layout, and contact
  - reconcile
  - read the Working Proposal
- Expected:
  - Working Proposal shows known structured context conservatively but usefully
- Actual:
  - Working Proposal still showed core fields as `unknown`
  - observed operational facts remained hidden from the human operator
- Affected component:
  - Working Proposal projection / human case overview
- Suggested next remediation scope:
  - wire persisted structured state into the proposal without promoting unapproved changes into active truth

### BUG-003

- Severity: `High`
- Scenario: `5`, `18`
- Reproduction steps:
  - use case `145`
  - inject `booking_fee_override`
  - reconcile
  - inspect decision, approval, blocker, and Working Proposal
- Expected:
  - human sees governed baseline booking fee plus clearly pending waiver decision
- Actual:
  - proposal did not activate the waiver early, which is correct
  - proposal also failed to show the commercial baseline clearly enough, leaving booking fee as `unknown`
- Affected component:
  - commercial-state projection in the Working Proposal
- Suggested next remediation scope:
  - expose baseline commercial truth and pending exception state side by side

### BUG-004

- Severity: `High`
- Scenario: `8`, `18`
- Reproduction steps:
  - inject `active_event_window` on case `145`
  - confirm `rental_case_reschedule_requests` row exists
  - inspect Working Proposal
- Expected:
  - active date and proposed date are both understandable to the operator
- Actual:
  - proposed date persisted safely
  - human-facing overview still left event date effectively `unknown`
- Affected component:
  - reschedule projection in the Working Proposal
- Suggested next remediation scope:
  - project active-vs-proposed schedule state explicitly in the case overview

### BUG-005

- Severity: `High`
- Scenario: `10`
- Reproduction steps:
  - compare observed operational-field dispositions on case `145`
  - note that catering, technical, layout, and event-day contact all resolved to `no_workflow_effect`
  - consider a materially larger operational change path
- Expected:
  - materially larger operational changes should at least surface reassessment work, even if final rule outcome is governed elsewhere
- Actual:
  - current observed behavior collapses too much operational input into no visible workflow effect
- Affected component:
  - operational-change handling and projection
- Suggested next remediation scope:
  - introduce a surfaced reassessment path that does not invent business policy but does expose human review work

## UX Gaps

### UX-001

- Severity: `High`
- Scenario: `1`, `2`, `18`, `19`
- Reproduction steps:
  - open a case after structured input has been added
  - compare known runtime state with the Working Proposal
- Expected:
  - proposal is the fastest truthful human summary
- Actual:
  - too many known values remain invisible or read as `unknown`
- Affected component:
  - Working Proposal / case overview
- Suggested next remediation scope:
  - make the overview the canonical human read model for current known truth, proposed change, and uncertainty

### UX-002

- Severity: `Medium`
- Scenario: `14`, `19`
- Reproduction steps:
  - open case `145`
  - inspect approvals, blockers, actions, and human-work preview
- Expected:
  - operator can instantly tell what to do next and why
- Actual:
  - controls exist, but the reason-to-action chain is too implicit
- Affected component:
  - approval/action/human-work presentation
- Suggested next remediation scope:
  - bind each visible action and approval more explicitly to the underlying case condition

### UX-003

- Severity: `Medium`
- Scenario: `8`, `13`, `18`
- Reproduction steps:
  - inspect case state after change-like inputs
- Expected:
  - current, proposed, stale, and superseded states are obvious
- Actual:
  - these distinctions are not operator-obvious enough
- Affected component:
  - case freshness and change-state presentation
- Suggested next remediation scope:
  - add explicit freshness / revision / proposed-state labeling in the overview and action panels

### UX-004

- Severity: `High`
- Scenario: `20`
- Reproduction steps:
  - attempt repeated root and case navigation during ordinary audit use
- Expected:
  - empty-state and root navigation remain dependable
- Actual:
  - the operator cannot trust the console to stay available
- Affected component:
  - basic console usability
- Suggested next remediation scope:
  - stabilize request handling before adding more user-facing workflow complexity

## Recommended Next Build Order

1. Stabilize the console request path so root and case pages load reliably under ordinary audit usage.
2. Repair the Working Proposal projection so persisted structured state, baseline commercial truth, approvals, blockers, and active-vs-proposed schedule are surfaced truthfully.
3. Add the first usable inquiry-state projection layer for open questions, known facts, and operator next steps without directly mutating governed truth.
4. Expose follow-up creation and stale / superseded execution states in the console so safety paths can be tested end-to-end.
5. Add reliable console validation coverage for fake failure, timeout, and ambiguous execution outcomes.

## Final Judgment

The current system has meaningful underlying workflow pieces:

- case-local evidence persistence
- approval-gated case decisions
- separate reschedule-request persistence
- deterministic execution scaffolding
- human-work preview surfaces

That said, the audit result is still:

- `TEST_CONSOLE_REQUIRES_REMEDIATION_BEFORE_INQUIRY_WORKFLOW_BUILD`

Why:

- the console is not operationally reliable enough
- the Working Proposal does not yet tell a truthful enough rental story from known structured state
- the first inquiry loop is still missing the human-usable bridge between evidence persistence and operator action

