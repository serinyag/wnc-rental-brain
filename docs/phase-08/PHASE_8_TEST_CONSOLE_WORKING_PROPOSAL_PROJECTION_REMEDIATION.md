# Phase 8 Test Console Working Proposal Projection Remediation

Date:

- August 14, 2026

Status:

- `TEST_CONSOLE_READY_FOR_REALISTIC_SCENARIO_RERUN`

Repository:

- `/Users/serinya/Documents/WNC Rental Automation`

## Scope

This remediation addressed the remaining major audit finding after Request-Path Remediation A:

> The Working Proposal hid too much persisted structured truth behind `unknown`, and the relationship between current state, unresolved issues, approvals, and next actions was too implicit for an operator.

This work stayed inside the projection / read-model boundary:

- no inbound Outlook work
- no inquiry extraction
- no new business rules
- no new AI reasoning
- no workflow mutations during projection
- no schema migration

## Projection Root Causes

The prior Working Proposal was conservative in the right direction, but it was losing too much truth because:

1. it flattened rich structured state into plain display strings too early
2. it projected mostly from `RentalCase` and a few current entities, while ignoring observation candidates, reschedule requests, case decisions, and action reason references already in memory
3. it treated many missing display mappings as `unknown` instead of distinguishing `not provided`, `not yet confirmed`, `not established`, and `none`
4. it had no deterministic operator-facing join between:
   - current truth
   - proposed state
   - approvals
   - blockers
   - workflow actions
5. it did not surface governed commercial baseline authority next to case-specific exceptions

## Field / Source Matrix

| Human field | Current source | Projection rule |
| - | - | - |
| Client / company | test-console case metadata, fallback `rental_cases.client_account_ref` | show as current when present |
| Working scope label | test-console case metadata, fallback `rental_cases.service_level_or_type` | show as current label, not as governed event type |
| Rental type | `rental_cases.rental_type_code` | show as current |
| Requested spaces | deterministic mapping from `rental_type_code` when specific (`studio_space`, `entire_venue`) | show as current when specific, otherwise `Not established` |
| Current event date/time | `rental_cases.active_event_start`, `active_event_end` | show as current only when governed current fields exist |
| Proposed event date/time | active `rental_case_reschedule_requests` | show separately as proposed; never replace current date |
| Guest count current | `rental_case_facts.guest_count` | show as current only when fact exists |
| Guest count observed | latest structured observation candidate | show separately as proposed / observed candidate |
| Operational fields | `rental_case_facts.*` first, otherwise latest structured observation candidate | facts show as current; observation-only values show as proposed / not yet governed |
| Open questions | `rental_case_open_questions` | show only unresolved current questions |
| Requirements | `rental_case_requirements` | show only unresolved current requirements |
| Blockers | `rental_case_blockers` | show only open blockers |
| Approvals | `rental_case_approval_requests` | show only open approvals with linked target context when available |
| Proposed changes | `rental_case_proposed_changes` | show current/prior and proposed values side by side |
| Reschedules | `rental_case_reschedule_requests` | show current schedule separately from proposed schedule |
| Case-specific commercial exceptions | `rental_case_decisions` | proposed decisions stay pending; active decisions become effective case truth |
| Booking-fee baseline | bounded Phase 4 lookup via `api.get_booking_fee_rule(...)` when schedule scope is explicit enough | show governed baseline separately from case-specific exception |
| VAT | same Phase 4 booking-fee lookup | show only when governed baseline lookup succeeds |
| Communication | latest raw evidence event already loaded into console evidence bundles | show last inbound context without provider calls |
| Follow-ups | `follow_ups` | show current due / overdue / escalated state without implying email was already sent |
| Next actions | `workflow_actions` + linked reason references + related approvals/blockers | show `what`, `why`, and linked blocking context where safely derivable |
| Proposal freshness | `artifact_references` for `proposal` artifacts | show freshness and revision gap deterministically |
| Authority warnings | `reasoning_projections` unresolved authority / warning / conflict / contamination codes | show in a dedicated warning section |

## Projection Precedence

The projection now preserves explicit state categories:

- `current`
- `proposed`
- `unresolved`
- `blocked`
- `stale`
- `reference`
- `none`

Rules applied:

1. observation-only values never become current truth
2. proposed changes never overwrite current truth in place
3. proposed reschedules never replace the active date until governed acceptance has already happened elsewhere
4. pending case decisions never become effective case truth
5. active case decisions can override case-effective value, but the governed baseline still remains visible
6. historical or unresolved authority never fills a current-value gap

## Implementation Summary

### Projection contract

`tools/phase_08_workflow/test_console_projection.py`

- replaced flat string-only projection sections with typed `ProjectionItem` values
- added typed input contexts for:
  - `ObservedFieldCandidate`
  - `LatestCommunicationContext`
  - `BookingFeeRuleContext`
- added a dedicated warnings section

### Service-side projection assembly

`tools/phase_08_workflow/test_console_service.py`

- builds latest observed-field candidates from already-loaded evidence bundles
- builds latest communication context from already-loaded raw evidence
- adds one bounded Phase 4 booking-fee lookup only when schedule scope is explicit enough
- keeps projection read-only and server-side

### UI rendering

`tools/phase_08_workflow/test_console.py`

- kept the template thin
- added state badges for `current / proposed / unresolved / blocked / stale / reference / none`
- renamed the main Working Proposal group labels to better match operator questions

## Manual UX Review

Richest live case reviewed:

- case `145`

Operator questions after remediation:

| Question | Rating | Notes |
| - | - | - |
| Who is the client? | `CLEAR` | Client and working scope label are immediately visible |
| What is the current event scope? | `PARTIAL` | Rental type and proposed schedule are clear, but no governed current event type exists yet |
| What is current vs proposed? | `CLEAR` | current event date stays unresolved while proposed date/time and observed guest count are called out separately |
| What is commercially established? | `PARTIAL` | booking-fee baseline and VAT are clear; broader commercial items still remain intentionally unestablished |
| What is missing? | `CLEAR` | unresolved values are now shown as `Not provided`, `Not yet confirmed`, or `Not established` instead of generic `unknown` |
| What is blocked? | `CLEAR` | blocker is explicit and tied to the case decision |
| What needs approval? | `CLEAR` | approval target and commercial context are explicit |
| What needs attention next? | `CLEAR` | current task items are visible and distinct from other state |
| Why does it need attention? | `CLEAR` | action detail now shows linked reason plus related approval / blocker where available |
| Is anything stale? | `PARTIAL` | freshness surface is explicit, but the richest live case does not currently contain a stale artifact/action example |

Additional spot checks:

- case `146`
  - guest-count observation now surfaces as an observed candidate instead of disappearing into `unknown`
  - date/time remain `Not provided` because they are not structurally persisted as governed truth yet
- case `148`
  - empty / incomplete inquiry fields remain explicit and non-fabricated

## Focused Tests

Command:

```text
python3 -m unittest
  tools.phase_08_workflow.tests.test_test_console_projection
  tools.phase_08_workflow.tests.test_test_console_service
  tools.phase_08_workflow.tests.test_test_console_app
```

Result:

- `26 / 26 PASS`

Focused coverage now includes:

- empty inquiry truth safety
- current fact vs observed candidate separation
- proposed change current/proposed projection
- reschedule current/proposed separation
- pending booking-fee waiver baseline safety
- active booking-fee waiver effective-value projection
- operational observation projection
- authority warning projection
- blocker + approval + action context chain
- superseded action exclusion from current attention
- follow-up due-state projection
- stale proposal artifact visibility

## Full Regressions

Phase 8:

- command: `python3 -m pytest tools/phase_08_workflow/tests -q`
- result: `134 / 134 PASS`

Phase 7:

- command: `python3 -m pytest tools/phase_07_reasoning/tests -q`
- result: `127 / 127 PASS`

Phase 5:

- command: `python3 -m pytest tools/phase_05_chunking/tests -q`
- result: `27 / 27 PASS`

Phase 6:

- command: `python3 -m pytest tools/phase_06_search/tests -q`
- result: `6 / 6 PASS`

Supabase:

- command: `npx -y supabase@latest test db --local`
- result: `41 files / 1059 tests PASS`

## Performance Check

Fresh local console instance benchmarked on:

- `http://127.0.0.1:8766`

Repeated-load sample:

- root median: `0.094s`
- root slowest: `0.447s`
- rich-case median: `0.599s`
- rich-case slowest: `0.695s`

Stability result:

- indefinitely hanging requests: `0`
- progressive degradation observed: `0`
- repeated navigation remained stable: `yes`

Compared with Remediation A:

- root remained in the same sub-second range after the richer projection
- rich-case detail remained bounded and stable despite the added projection context

## Safety Metrics

- business-rule changes = `0`
- lifecycle semantic changes = `0`
- approval semantic changes = `0`
- WorkflowAction semantic changes = `0`
- inquiry extraction added = `0`
- Outlook inbound added = `0`
- new LLM reasoning behavior = `0`
- LLM calls during projection = `0`
- provider calls during projection = `0`
- projection-triggered workflow mutations = `0`
- observation displayed as current truth without governance = `0`
- proposed change displayed as current truth = `0`
- pending CaseDecision displayed as active = `0`
- historical precedent displayed as current authority = `0`
- proposed reschedule displayed as active date = `0`
- stale action displayed as current next action = `0`
- superseded action displayed as current next action = `0`
- cross-case projection leakage = `0`
- browser-exposed privileged credentials = `0`
- request hangs reintroduced = `0`

## Remaining Projection Limitations

1. Event type still remains `Not established` unless it is persisted structurally; this remediation does not infer it from raw client prose.
2. Requested spaces are only shown when `rental_type_code` is already specific enough to support a deterministic label.
3. Broader commercial position is still limited to what current structured authority actually supports in the case path; this remediation does not invent venue pricing, deposits, or extra fees.
4. Missing-information creation is still downstream work; if no `OpenQuestion` exists, the console will not invent one from raw email.
5. Action reason chains are explicit only where `reason_entity_reference`, structured payload, and linked entities already make the relationship safely derivable.
6. This work does not make the system inquiry-complete; it only makes already-persisted structured state readable and truthful.

## Readiness Assessment

The console is now human-usable enough to rerun the formal realistic rental scenario validation.

Readiness marker:

- `TEST_CONSOLE_READY_FOR_REALISTIC_SCENARIO_RERUN`

This remediation does **not** yet justify:

- `TEST_CONSOLE_READY_FOR_INQUIRY_WORKFLOW_BUILD`

That stronger marker still depends on a separate formal rerun of the 20-scenario audit and the later inquiry-loop work that remains out of scope here.
