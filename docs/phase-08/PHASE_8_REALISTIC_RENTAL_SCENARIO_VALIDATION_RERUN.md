# Phase 8 Realistic Rental Scenario Validation Rerun

Date:

- August 14, 2026

Repository:

- `/Users/serinya/Documents/WNC Rental Automation`

Readiness decision:

- `TEST_CONSOLE_REQUIRES_FURTHER_REMEDIATION`

Machine-readable scorecard:

- `docs/phase-08/evaluations/realistic_rental_scenario_results_rerun.json`

## Executive Summary

This rerun did confirm the two big intended improvements:

- Request-path stability is now real.
- Working Proposal truth projection is materially better on rich cases.

The console stayed responsive through the full 20-scenario rerun on a fresh local instance at `http://127.0.0.1:8767` with:

- root repeated-load median about `0.093s`
- rich case repeated-load median about `0.571s`
- repeated-load failures `0`
- hangs observed `0`
- restarts required `0`

The rich-case operator story is also much stronger than the original audit. Proposed schedule, observed guest count, approvals, blockers, operational context, and human work are now visible and understandable instead of collapsing into generic `unknown` values.

That said, the rerun also exposed two remaining high-severity projection defects:

1. approved booking-fee override does not update the projected effective booking fee
2. fresh console-created cases still project `Studio Space` as current truth even when the inquiry is incomplete, empty, or asks for something else

Those two issues violate the rerun readiness gate:

- no high-severity projection defect makes the console misleading

So the console is much closer, and much more usable, but it is not yet trustworthy enough to be the development surface for the first governed inquiry workflow.

The single biggest missing workflow capability remains:

> there is still no governed path that turns structured inquiry observations into established current facts, open questions, and follow-up-capable workflow for core inquiry fields.

That missing connection is the main reason so many scenarios still stop at:

- observed candidate state
- no current fact
- no open question
- no feasibility posture
- no outbound/client workflow

## Before / After Scorecard

| Metric | Original Audit | Rerun |
| - | -: | -: |
| PASS | 0 | 3 |
| PARTIAL | 9 | 7 |
| FAIL | 1 | 2 |
| NOT CURRENTLY SUPPORTED | 7 | 5 |
| BLOCKED BY MISSING GOVERNED RULE | 3 | 3 |
| Critical bugs | 0 | 0 |
| High-severity bugs | 5 | 2 |

## Scenario Scorecard

| # | Scenario | Original | Rerun | Change | Main finding |
| - | - | - | - | - | - |
| 1 | Straightforward Venue Inquiry | `PARTIAL` | `PARTIAL` | `IMPROVED` | Proposal now shows proposed timing, observed guest count, catering, and a next action, but still does not yield governed current facts or open questions. |
| 2 | Incomplete Inquiry | `PARTIAL` | `FAIL` | `REGRESSED` | Dates and guest count stay unresolved, but the console falsely presents `Studio Space` as current scope. |
| 3 | Capacity / Large Guest Count | `NOT CURRENTLY SUPPORTED` | `NOT CURRENTLY SUPPORTED` | `UNCHANGED` | 85-guest evidence is visible, but capacity authority and whole-venue feasibility are still unwired. |
| 4 | Unsupported Exact Request but Possible Alternative | `NOT CURRENTLY SUPPORTED` | `NOT CURRENTLY SUPPORTED` | `UNCHANGED` | Exact infeasibility vs supported alternative is still not represented operationally. |
| 5 | Booking Fee Waiver | `PARTIAL` | `PARTIAL` | `IMPROVED` | Before approval the commercial story is clear; after approval the effective booking fee is still projected incorrectly. |
| 6 | Historical Storage Price Trap | `BLOCKED BY MISSING GOVERNED RULE` | `BLOCKED BY MISSING GOVERNED RULE` | `UNCHANGED` | No current governed storage-price authority was available, but no historical price leaked into truth. |
| 7 | Material Guest Count Change | `NOT CURRENTLY SUPPORTED` | `NOT CURRENTLY SUPPORTED` | `IMPROVED` | Latest observed guest count is now visible, but there is still no governed change object or impact workflow. |
| 8 | Reschedule Request | `PARTIAL` | `PARTIAL` | `IMPROVED` | Proposed schedule is now clearly separated from active truth, but current active schedule is still unset in the live console path. |
| 9 | Minor Operational Change | `BLOCKED BY MISSING GOVERNED RULE` | `BLOCKED BY MISSING GOVERNED RULE` | `IMPROVED` | Small operational add-on is now visible without invented fees, but low-impact classification is still unguided. |
| 10 | Clearly Material Operational Change | `BLOCKED BY MISSING GOVERNED RULE` | `BLOCKED BY MISSING GOVERNED RULE` | `IMPROVED` | Major operational escalation collapses into the same inert path as the minor case. |
| 11 | Follow-Up | `NOT CURRENTLY SUPPORTED` | `NOT CURRENTLY SUPPORTED` | `UNCHANGED` | Follow-up evaluation is safe, but there is still no usable follow-up creation/progression path. |
| 12 | Stale Client Email Action | `NOT CURRENTLY SUPPORTED` | `NOT CURRENTLY SUPPORTED` | `UNCHANGED` | Client-email stale-action path still cannot be formed through the console surface. |
| 13 | Superseded Action | `NOT CURRENTLY SUPPORTED` | `PARTIAL` | `IMPROVED` | Superseded actions now fail closed and disappear from current attention, but no replacement action is surfaced in the same flow. |
| 14 | Approval-Required Action | `PARTIAL` | `PARTIAL` | `IMPROVED` | Approval activation and blocker resolution now complete, but commercial projection remains wrong after approval. |
| 15 | Fake Provider Failure | `PARTIAL` | `PASS` | `NEWLY_SUPPORTED` | Retryable failure now records attempt state, keeps the action executable, and leaves a clean audit trail. |
| 16 | Fake Timeout / Ambiguous Result | `NOT CURRENTLY SUPPORTED` | `PARTIAL` | `IMPROVED` | Timeout and ambiguity no longer become success, but ambiguity is not surfaced well in top-level current attention. |
| 17 | Cross-Case Isolation | `PARTIAL` | `PASS` | `NEWLY_SUPPORTED` | Wrong-case approval and action challenges failed closed with zero cross-case mutation. |
| 18 | Human Working Proposal Audit | `PARTIAL` | `PARTIAL` | `IMPROVED` | Rich-case readability is much better, but approved effective fee truth and fresh-case scope defaults are still misleading. |
| 19 | Asana Human Work Projection | `PARTIAL` | `PASS` | `NEWLY_SUPPORTED` | Human Work Preview is now staff-usable without real Asana. |
| 20 | Empty / New Rental | `FAIL` | `FAIL` | `IMPROVED` | Console stability is fixed, but empty cases still fabricate `Studio Space` as current scope. |

## Remediation Validation

### Request-Path Remediation

Validated successfully.

Observed during the rerun:

- root page remained responsive throughout
- case pages remained responsive throughout
- repeated navigation stayed stable
- no restart was required
- no root or case-detail hang was observed

Measured repeated-load sample on the live rerun console:

- root:
  - `10 / 10` successes
  - median about `0.093s`
  - slowest about `0.226s`
- rich case `197`:
  - `10 / 10` successes
  - median about `0.571s`
  - slowest about `0.756s`

Observed caution:

- reconciliation POST round trips remained slow at roughly `8.5s` to `16.5s`
- this was a UX/performance issue, not a hang regression

Conclusion:

- Remediation A held.

### Working Proposal Remediation

Validated partially.

Clear improvements observed:

- proposed schedule is separated from active truth
- observed guest count is visible as observed/proposed instead of disappearing
- operational observation fields are visible and labeled as not yet promoted into governed truth
- blocker, approval, and next-action context is much clearer
- Human Work Preview is materially better

Remaining truth defects:

- approved booking-fee override does not update the projected effective booking fee
- fresh/incomplete cases still display `Studio Space` as current scope even when that scope is not governed truth

Conclusion:

- Remediation B materially improved the operator experience, but it did not fully close projection truth safety.

## Detailed Scenario Reports

## Scenario 1 - Straightforward Venue Inquiry

Purpose:

- Validate a simple venue inquiry with modest guest count, timing, and external catering.

Input:

- Case `195`
- client `Acme Brand`
- event reference `October 3 private brand event`
- raw evidence:
  - October 3 private brand event
  - about 35 guests
  - `18:00` to `22:00`
  - venue rental only
  - external catering
- structured observations:
  - `guest_count=35`
  - `active_event_window={"active_event_start":"2026-10-03T18:00:00Z","active_event_end":"2026-10-03T22:00:00Z"}`
  - `catering_arrangement=client_external_caterer`

Operator steps:

1. Create test rental.
2. Inject raw evidence.
3. Inject three structured observations.
4. Run reconciliation.

Persisted state:

- `rental_case_id=195`
- lifecycle stayed `inquiry_active`
- facts `0`
- open questions `0`
- blockers `0`
- reschedule requests `1`
- actions `1`
  - `workflow_action_id=94`
  - `reason_entity_reference=reschedule_request:11`
  - status `ready_to_execute`

Working Proposal:

- current:
  - client/company
  - working scope label
  - lifecycle
- unresolved:
  - current event date/time
  - current guest count
- proposed:
  - proposed event date `2026-10-03`
  - proposed event time `18:00 - 22:00`
  - observed guest count `35`
  - catering arrangement
- next attention:
  - `Review reschedule request 11.`

Expected behavior:

- preserve evidence
- keep unknowns explicit
- give the operator a minimally useful inquiry view

Actual behavior:

- evidence persisted cleanly
- projection is much more usable than the original audit
- there is still no governed current-fact or open-question promotion path

Result:

- `PARTIAL`

Issues:

- `NOT_YET_IMPLEMENTED-OBSERVATION_PROMOTION` (`NOT_YET_IMPLEMENTED` / `MEDIUM`)

Change from original audit:

- `IMPROVED`
- The operator-facing view is now usable, but the case still stops at candidate/proposed state.

## Scenario 2 - Incomplete Inquiry

Purpose:

- Verify that uncertainty stays explicit and no rental truth is fabricated.

Input:

- Case `196`
- raw evidence:
  - interested in renting sometime in October
  - no exact date
  - no exact guest count
  - no defined scope

Operator steps:

1. Create test rental.
2. Inject raw evidence.
3. Run reconciliation.

Persisted state:

- `rental_case_id=196`
- facts `0`
- questions `0`
- requirements `0`
- blockers `0`
- actions `0`
- follow-ups `0`

Working Proposal:

- correctly unresolved:
  - event date `Not provided`
  - event time `Not provided`
  - guest count `Not provided`
  - event type `Not established`
- incorrect current truth:
  - rental type `Studio Space`
  - requested spaces `Studio Space`

Expected behavior:

- no fabricated date
- no fabricated guest count
- no fabricated event type
- no fabricated rental scope

Actual behavior:

- date/time/guest count stayed honest
- rental scope was fabricated by the console shell defaults

Result:

- `FAIL`

Issues:

- `BUG-RERUN-002` (`BUG` / `HIGH`)

Change from original audit:

- `REGRESSED`
- The improved projection now makes the incorrect default scope visible enough to fail the scenario.

## Scenario 3 - Capacity / Large Guest Count

Purpose:

- Test whether an 85-guest whole-venue inquiry yields a usable capacity posture.

Input:

- Case `199`
- event reference `Whole-venue activation for 85 guests`
- raw evidence:
  - whole-venue activation
  - `85` guests
- structured observation:
  - `guest_count=85`

Operator steps:

1. Create test rental.
2. Inject raw evidence.
3. Inject structured guest-count observation.
4. Run reconciliation.

Persisted state:

- no facts
- no blockers
- no actions
- no feasibility decision

Working Proposal:

- observed guest count `85`
- feasibility as requested `Not yet evaluated`
- supported alternative `Not established`
- incorrectly current:
  - rental type `Studio Space`
  - requested spaces `Studio Space`

Expected behavior:

- distinguish whole-venue feasibility from studio assumptions

Actual behavior:

- feasibility is still unwired
- current scope is still misleading on a fresh case

Result:

- `NOT CURRENTLY SUPPORTED`

Issues:

- `BUG-RERUN-002` (`BUG` / `HIGH`)
- `NOT_YET_IMPLEMENTED-CAPACITY` (`NOT_YET_IMPLEMENTED` / `MEDIUM`)

Change from original audit:

- `UNCHANGED`

## Scenario 4 - Unsupported Exact Request but Possible Alternative

Purpose:

- Test exact infeasibility plus possible supported alternative for a professional-kitchen request.

Input:

- Case `200`
- raw evidence:
  - chef showcase
  - asks for full professional kitchen access

Operator steps:

1. Create test rental.
2. Inject raw evidence.
3. Run reconciliation.

Persisted state:

- no facts
- no blockers
- no actions
- no alternative-feasibility record

Working Proposal:

- feasibility as requested `Not yet evaluated`
- supported alternative `Not established`
- incorrectly current:
  - rental type `Studio Space`
  - requested spaces `Studio Space`

Expected behavior:

- do not invent a kitchen
- distinguish exact infeasibility from a possible supported alternative

Actual behavior:

- the runtime still does not express this path operationally

Result:

- `NOT CURRENTLY SUPPORTED`

Issues:

- `BUG-RERUN-002` (`BUG` / `HIGH`)
- `NOT_YET_IMPLEMENTED-CAPACITY` (`NOT_YET_IMPLEMENTED` / `MEDIUM`)

Change from original audit:

- `UNCHANGED`

## Scenario 5 - Booking Fee Waiver

Purpose:

- Validate approval-gated case-specific commercial exception handling.

Input:

- Case `197`
- Blue Ridge Community Summit
- `85` guests
- October 24, 2026
- external catering
- AV / microphones / lighting / theater layout / check-in table
- booking-fee waiver request

Operator steps:

1. Create rich test rental.
2. Inject raw evidence.
3. Inject structured observations for guest count, event window, catering, technical, layout, event-day contact, and booking-fee override.
4. Run reconciliation.
5. Reload rich case.
6. Approve approval request `50`.
7. Reload case again.

Persisted state before approval:

- reschedule request `12` proposed
- case decision `34` proposed
- approval request `50` open
- blocker `66` open
- actions `95` and `96` ready

Working Proposal before approval:

- baseline booking fee `EUR 75 excl. VAT`
- VAT `21%`
- case-specific exception `Pending`
- effective booking fee still baseline
- approval and blocker context clear

Persisted state after approval:

- case revision moved `0 -> 1`
- decision `34` became `active`
- approval `50` became `approved`
- blocker `66` became `resolved`
- actions `95` and `96` became `superseded`

Working Proposal after approval:

- case-specific exception became current
- effective booking fee incorrectly remained `EUR 75 excl. VAT`
- detail incorrectly said no approved exception was active

Expected behavior:

- baseline remains visible
- pending exception stays separate before approval
- approved exception changes the effective fee after approval

Actual behavior:

- before-approval safety and readability were good
- after-approval effective fee projection was wrong

Result:

- `PARTIAL`

Issues:

- `BUG-RERUN-001` (`BUG` / `HIGH`)

Change from original audit:

- `IMPROVED`
- The approval chain is now much clearer, but approved commercial truth is still wrong.

## Scenario 6 - Historical Storage Price Trap

Purpose:

- Ensure historical price precedent does not become current truth without current authority.

Input:

- historical storage-price trap concept using `EUR 300`

Operator steps:

- Evaluate against live rerun cases and current console/runtime surface.

Persisted state:

- no governed storage-price authority surfaced
- no historical storage price surfaced as current truth

Working Proposal:

- warnings section exists on the console
- no persisted storage-authority warning was available in the live rerun cases

Expected behavior:

- historical `EUR 300` never becomes current price without current authority

Actual behavior:

- no unsafe promotion occurred
- current governed authority is still missing

Result:

- `BLOCKED BY MISSING GOVERNED RULE`

Issues:

- `BUSINESS_RULE_GAP-STORAGE_AUTHORITY` (`BUSINESS_RULE_GAP` / `MEDIUM`)

Change from original audit:

- `UNCHANGED`

## Scenario 7 - Material Guest Count Change

Purpose:

- Test whether later guest-count increase becomes a governed proposed change instead of silent mutation.

Input:

- Case `198`
- first observation `30` guests
- later observation `60` guests

Operator steps:

1. Create test rental.
2. Inject raw evidence and guest-count observation `30`.
3. Run reconciliation.
4. Inject updated raw evidence and guest-count observation `60` as a change candidate.
5. Run reconciliation again.

Persisted state:

- facts `0`
- proposed changes `0`
- actions `0`
- observation evidence recorded both `30` and `60`

Working Proposal:

- current guest count remained unresolved
- observed guest count showed latest `60`
- no explicit current `30` vs proposed `60` comparison
- no impact evaluation path

Expected behavior:

- current remains `30` until accepted
- `60` stays proposed
- impact workflow appears

Actual behavior:

- latest candidate is visible
- no governed change object or review path exists

Result:

- `NOT CURRENTLY SUPPORTED`

Issues:

- `NOT_YET_IMPLEMENTED-OBSERVATION_PROMOTION` (`NOT_YET_IMPLEMENTED` / `MEDIUM`)

Change from original audit:

- `IMPROVED`
- The latest candidate no longer disappears, but the real change workflow is still absent.

## Scenario 8 - Reschedule Request

Purpose:

- Validate proposed date change handling.

Input:

- Case `197`
- structured event window request for `2026-10-24 15:00 -> 21:00 UTC`

Operator steps:

1. Reuse the rich case from Scenario 5 before approval.
2. Review reschedule request and Working Proposal.

Persisted state:

- reschedule request `12` persisted as `proposed`
- current active schedule snapshot remained null
- action `96` referenced `reschedule_request:12`

Working Proposal:

- current event date/time stayed unresolved
- proposed event date/time displayed separately
- next action explained the reschedule review reason clearly

Expected behavior:

- proposed date stays separate from active truth

Actual behavior:

- separation is now clear
- full current-vs-proposed date validation remains incomplete because current active date is still unset in the live path

Result:

- `PARTIAL`

Issues:

- `NOT_YET_IMPLEMENTED-OBSERVATION_PROMOTION` (`NOT_YET_IMPLEMENTED` / `MEDIUM`)

Change from original audit:

- `IMPROVED`

## Scenario 9 - Minor Operational Change

Purpose:

- Check whether a small operational add-on is handled without inflation or invention.

Input:

- Case `205`
- structured layout change candidate:
  - `{"welcome_table_flowers": true}`

Operator steps:

1. Create test rental.
2. Inject layout-requirements change candidate for a small flower arrangement.
3. Run reconciliation.

Persisted state:

- actions `0`
- blockers `0`
- proposed changes `0`
- observation effect `no_workflow_effect`

Working Proposal:

- operations now show `Layout Requirements = Welcome Table Flowers`
- state is `proposed`
- detail explicitly says it is not yet promoted into governed truth

Expected behavior:

- preserve evidence/change safely
- avoid invented cost or approval
- classify meaningfully if governed

Actual behavior:

- safety was good
- visibility was much better
- governed minor-change classification is still missing

Result:

- `BLOCKED BY MISSING GOVERNED RULE`

Issues:

- `BUSINESS_RULE_GAP-OPERATIONAL_MATERIALITY` (`BUSINESS_RULE_GAP` / `MEDIUM`)

Change from original audit:

- `IMPROVED`

## Scenario 10 - Clearly Material Operational Change

Purpose:

- Check whether major operational escalation is treated differently from a small one.

Input:

- Case `206`
- structured layout change candidate:
  - `{"flower_arrangements": 400, "extra_setup_access": true}`

Operator steps:

1. Create test rental.
2. Inject material-looking operational change candidate.
3. Run reconciliation.

Persisted state:

- actions `0`
- blockers `0`
- proposed changes `0`
- observation effect `no_workflow_effect`

Working Proposal:

- operations show:
  - `Extra Setup Access`
  - `Flower Arrangements=400`
- still only as proposed candidate

Expected behavior:

- material escalation should route to reassessment once governed

Actual behavior:

- the clearly material case collapses into the same inert path as the minor case

Result:

- `BLOCKED BY MISSING GOVERNED RULE`

Issues:

- `BUSINESS_RULE_GAP-OPERATIONAL_MATERIALITY` (`BUSINESS_RULE_GAP` / `MEDIUM`)

Change from original audit:

- `IMPROVED`

## Scenario 11 - Follow-Up

Purpose:

- Test whether due follow-ups re-enter normal workflow without directly sending mail.

Input:

- Case `196`
- follow-up evaluation on a cold/new inquiry shell

Operator steps:

1. Open the incomplete inquiry case.
2. Use `Evaluate Follow-Ups`.

Persisted state:

- follow-ups `0`
- created actions `0`

Working Proposal:

- communication shows last inbound message
- next actions still show none

Expected behavior:

- schedulable follow-up flow
- due/overdue state
- action creation through normal workflow

Actual behavior:

- evaluation hook is safe
- the full follow-up path still does not exist

Result:

- `NOT CURRENTLY SUPPORTED`

Issues:

- `NOT_YET_IMPLEMENTED-FOLLOWUP_PATH` (`NOT_YET_IMPLEMENTED` / `MEDIUM`)

Change from original audit:

- `UNCHANGED`

## Scenario 12 - Stale Client Email Action

Purpose:

- Ensure a client-email action cannot execute after material case change.

Input:

- desired client-email action at one case revision, then later case mutation

Operator steps:

- Attempted to find a console-supported path to form the action and then stale it.

Persisted state:

- no client-email action path could be formed through the live console surface

Working Proposal:

- not directly applicable because the prerequisite client-email workflow path is still absent

Expected behavior:

- stale email action rejected
- provider invocation stays `0`

Actual behavior:

- scenario still cannot be formed operationally through the console surface

Result:

- `NOT CURRENTLY SUPPORTED`

Issues:

- `NOT_YET_IMPLEMENTED-FOLLOWUP_PATH` (`NOT_YET_IMPLEMENTED` / `MEDIUM`)

Change from original audit:

- `UNCHANGED`

## Scenario 13 - Superseded Action

Purpose:

- Ensure older action is rejected once superseded by newer semantic state.

Input:

- Case `197`
- actions `95` and `96` before approval
- approval of decision `34`
- post-approval action execution attempts on `95` and `96`

Operator steps:

1. Build rich case and reconcile.
2. Approve approval request `50`.
3. Attempt to execute superseded actions `95` and `96`.

Persisted state:

- after approval both actions became `superseded`
- execution attempts on superseded actions created no execution attempt rows
- case `197` remained unchanged

Working Proposal:

- superseded actions disappeared from current attention
- `Needs attention` became none after approval

Expected behavior:

- old action cannot execute
- current attention excludes superseded work

Actual behavior:

- superseded actions failed closed with `action_superseded`
- the same flow did not surface a newer replacement action

Result:

- `PARTIAL`

Issues:

- `UX-RERUN-001` (`UX_GAP` / `MEDIUM`)

Change from original audit:

- `IMPROVED`

## Scenario 14 - Approval-Required Action

Purpose:

- Validate blocked-before-approval and eligible-after-approval behavior.

Input:

- Case `197`
- approval request `50`
- case decision `34`
- blocker `66`
- actions `95`, `96`

Operator steps:

1. Build rich case and observe open approval.
2. Approve approval request `50`.
3. Reload case detail.

Persisted state:

- before:
  - approval `50` open
  - blocker `66` open
  - decision `34` proposed
- after:
  - approval `50` approved
  - blocker `66` resolved
  - decision `34` active
  - actions `95` and `96` superseded

Working Proposal:

- before approval:
  - approval target and blocker were clear
- after approval:
  - current attention cleared
  - approved commercial effective value was still wrong

Expected behavior:

- clear reason chain from issue -> approval -> action

Actual behavior:

- approval activation path is now operational
- post-approval projection still fails the commercial truth check

Result:

- `PARTIAL`

Issues:

- `BUG-RERUN-001` (`BUG` / `HIGH`)

Change from original audit:

- `IMPROVED`

## Scenario 15 - Fake Provider Failure

Purpose:

- Validate deterministic failure handling.

Input:

- Case `202`
- action `97`
- fake execution mode `retryable_failure`

Operator steps:

1. Create simple reschedule-review action fixture.
2. Execute action `97` with `retryable_failure`.
3. Reload case detail.

Persisted state:

- execution attempt `50`
- attempt status `failed`
- failure code `fake_retryable_failure`
- action `97` stayed `ready_to_execute`
- workflow events include:
  - `workflow_action_execution_started`
  - `workflow_action_execution_completed`

Working Proposal:

- next action remained visible and executable
- no false success surfaced

Expected behavior:

- execution attempt exists
- action does not become succeeded
- no silent lifecycle advancement
- audit trail exists

Actual behavior:

- all of those conditions held

Result:

- `PASS`

Change from original audit:

- `NEWLY_SUPPORTED`

## Scenario 16 - Fake Timeout / Ambiguous Result

Purpose:

- Validate that timeout or ambiguity never becomes success.

Input:

- Case `203`
- action `98`
- fake execution mode `timeout`
- Case `204`
- action `99`
- fake execution mode `ambiguous`

Operator steps:

1. Create timeout fixture case and execute `98` with `timeout`.
2. Create ambiguous fixture case and execute `99` with `ambiguous`.
3. Reload both case pages.

Persisted state:

- timeout case `203`:
  - execution attempt `51`
  - attempt status `timeout`
  - failure code `fake_timeout`
  - action `98` returned to `ready_to_execute`
- ambiguous case `204`:
  - execution attempt `52`
  - attempt status `failed`
  - failure code `adapter_outcome_ambiguous`
  - action `99` became `failed`
- both cases recorded:
  - `workflow_action_execution_started`
  - `workflow_action_execution_completed`

Working Proposal:

- timeout case still showed the review action in current attention
- ambiguous case did not elevate the ambiguity back into top-level attention

Expected behavior:

- timeout != success
- ambiguous != success
- no blind duplicate retry

Actual behavior:

- core execution semantics were safe
- operator-facing ambiguity surfacing is still weak

Result:

- `PARTIAL`

Issues:

- `UX-RERUN-001` (`UX_GAP` / `MEDIUM`)

Change from original audit:

- `IMPROVED`

## Scenario 17 - Cross-Case Isolation

Purpose:

- Verify that one case cannot mutate another through normal console use.

Input:

- Case `195`
- Case `197`
- wrong-case approval attempt:
  - `POST /cases/195/approvals/50/approve`
- wrong-case action attempt:
  - `POST /cases/195/actions/96/execute`

Operator steps:

1. Attempt approval `50` through the wrong case path.
2. Attempt action `96` through the wrong case path.
3. Reload both cases.

Persisted state:

- wrong-case approval produced a report with failure code `approval_target_invalid`
- wrong-case action returned `400`
- no approval, action, or attempt state changed on case `197`

Working Proposal:

- no cross-case projection leakage observed

Expected behavior:

- reject cross-case mutation

Actual behavior:

- cross-case mutation remained `0`

Result:

- `PASS`

Issues:

- `UX-RERUN-002` (`UX_GAP` / `MEDIUM`)

Change from original audit:

- `NEWLY_SUPPORTED`

## Scenario 18 - Human Working Proposal Audit

Purpose:

- Assess whether the richest case is understandable to a WNC operator.

Basis case:

- Case `197` before approval, with post-approval spot check for commercial truth

Ratings:

| Question | Rating | Notes |
| - | - | - |
| Who is the client? | `CLEAR` | client/company is explicit |
| What is the current event scope? | `PARTIAL` | proposed timing and observed guest count are clear, but current active schedule is still unset and fresh-case scope defaults remain unsafe |
| What is current vs proposed? | `CLEAR` | current vs proposed separation is much better |
| What is commercially established? | `PARTIAL` | baseline and pending exception are clear before approval, but approved effective fee is wrong after activation |
| What is missing? | `CLEAR` | unresolved values are explicit |
| What is blocked? | `CLEAR` | blocker is explicit and linked to the approval |
| What requires approval? | `CLEAR` | approval target and reason are explicit |
| What needs attention? | `CLEAR` | next actions and human work preview are readable |
| Why does it need attention? | `CLEAR` | linked detail text is strong |
| Is anything stale? | `PARTIAL` | superseded work disappears correctly, but stale/ambiguous outcome surfacing is still weak at top level |

Expected behavior:

- rich case should be understandable enough for a human operator to drive review safely

Actual behavior:

- rich-case readability is materially improved
- two remaining projection defects still prevent full trust

Result:

- `PARTIAL`

Issues:

- `BUG-RERUN-001` (`BUG` / `HIGH`)
- `BUG-RERUN-002` (`BUG` / `HIGH`)

Change from original audit:

- `IMPROVED`

## Scenario 19 - Asana Human Work Projection

Purpose:

- Determine whether the system exposes sensible staff work without real Asana.

Basis case:

- Case `197` before approval

Operator answer:

- `YES`

Observed state:

- Human Work Preview listed:
  - blocker resolution need
  - approval need
  - proposed case-decision review task
  - reschedule review task

Expected behavior:

- staff member can understand what they personally need to do next

Actual behavior:

- preview is now good enough for staff handoff without real Asana

Result:

- `PASS`

Change from original audit:

- `NEWLY_SUPPORTED`

## Scenario 20 - Empty / New Rental

Purpose:

- Validate empty-state quality and guard against fabricated truth or crashes.

Input:

- Case `201`
- minimal new rental created from root form

Operator steps:

1. Create empty test rental.
2. Load case detail page.

Persisted state:

- facts `0`
- blockers `0`
- actions `0`
- follow-ups `0`

Working Proposal:

- correctly unresolved:
  - client/company -> `Unknown`
  - date/time -> `Not provided`
  - guest count -> `Not provided`
  - event type -> `Not established`
- incorrectly current:
  - rental type `Studio Space`
  - requested spaces `Studio Space`

Expected behavior:

- no crash
- no fabricated values
- no accidental actions

Actual behavior:

- stability is now good
- truth safety still fails on default scope projection

Result:

- `FAIL`

Issues:

- `BUG-RERUN-002` (`BUG` / `HIGH`)

Change from original audit:

- `IMPROVED`
- The original hang failure is gone, but fabricated scope still blocks readiness.

## Safety Invariants

Observed safety-violation counts:

- observation -> direct truth mutation = `0`
- generated prose -> workflow truth = `0`
- historical precedent -> current policy = `0`
- unapproved CaseDecision activation = `0`
- pending CaseDecision shown as active = `0`
- proposed change shown as current = `0`
- proposed reschedule shown as current date = `0`
- direct UI lifecycle mutation = `0`
- direct UI action-state mutation = `0`
- pre-approval provider execution = `0`
- stale execution = `0`
- superseded execution = `0`
- duplicate semantic execution = `0`
- provider failure counted as success = `0`
- ambiguous outcome counted as success = `0`
- follow-up directly invoking provider = `0`
- cross-case mutation = `0`
- stale action shown as current next attention = `0`
- superseded action shown as current next attention = `0`
- projection-triggered mutation = `0`
- console hangs = `0`

## Remaining Bugs

### BUG-RERUN-001

- category: `BUG`
- severity: `HIGH`
- scenarios: `5`, `14`, `18`
- component: `test_console_projection / commercial snapshot`
- reproduction:
  - create rich waiver case
  - approve booking-fee override
  - reload case detail
- expected:
  - approved exception becomes effective booking-fee truth
  - governed baseline remains visible separately
- actual:
  - case-specific exception becomes current
  - effective booking fee still shows baseline and explicitly claims no approved exception is active

### BUG-RERUN-002

- category: `BUG`
- severity: `HIGH`
- scenarios: `2`, `3`, `4`, `20`
- component: `test_console create-case seed / working proposal`
- reproduction:
  - create a fresh empty or incomplete case through the root form
  - load case detail
- expected:
  - rental scope remains unresolved until governed truth exists
- actual:
  - rental type and requested spaces show `Studio Space` as current truth

## Remaining UX Gaps

- `UX-RERUN-001` (`MEDIUM`)
  - ambiguous execution outcome is visible in attempt history, but not promoted into top-level current attention
- `UX-RERUN-002` (`MEDIUM`)
  - cross-case invalid approval fails closed but still returns a normal `200` report page
- `UX-RERUN-003` (`MEDIUM`)
  - reconciliation requests remained slow at roughly `8.5s` to `16.5s` even though they completed safely

## Not-Yet-Implemented Capabilities

- governed promotion of structured inquiry observations into established facts and open questions for:
  - requested schedule
  - guest count
  - requested space
  - event type
- capacity and alternative-feasibility orchestration
- follow-up creation/progression and client-email action path

## Business Rule Gaps

- current governed storage-pricing authority for storage-price scenarios
- governed low-impact versus material operational-change classification boundary

## Strongest Parts Of The Current Architecture

- local-first provider safety defaults held cleanly throughout the rerun
- request-path stability now supports sustained manual console testing
- approval/blocker/action state transitions are coherent and auditable
- superseded actions fail closed without side effects
- deterministic fake execution outcomes are now well persisted
- rich-case human work projection is finally useful

## Single Weakest / Missing Workflow Connection

The main missing workflow connection is:

```text
structured observations
-> governed current facts / open questions
-> inquiry reasoning / feasibility posture
-> follow-up or client-facing workflow action
```

Right now the system is still mostly stopping at:

- observed candidate
- proposed candidate
- no current fact
- no open question
- no follow-up
- no outbound workflow

That is the clearest blocker between the current console and the first inquiry MVP.

## Recommended Next Build

1. Remediation C:
   - remove fabricated current rental scope on fresh cases
   - fix effective booking-fee projection after approved override
2. Inquiry Intake Slice 1:
   - promote governed structured observations for requested schedule, guest count, requested space, and event type into current facts or open questions as appropriate
3. Inquiry Workflow Slice 2:
   - create follow-up / client-email workflow intent from governed open-question and waiting-state cases without enabling production sends

## Readiness Decision

`TEST_CONSOLE_REQUIRES_FURTHER_REMEDIATION`

Why:

- request-path stability is now good enough
- rich-case projection is materially improved
- safety invariants remained intact
- many remaining scenario gaps are correctly future-workflow gaps

But:

- there are still two high-severity projection defects that make the console misleading
- the core structured-observation -> governed-fact/open-question connection is still missing

That means the console is close, but not yet trustworthy enough to serve as the development surface for the first governed end-to-end inquiry workflow.
