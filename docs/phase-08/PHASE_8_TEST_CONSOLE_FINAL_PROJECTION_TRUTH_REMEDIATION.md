# Phase 8 Test Console Final Projection Truth Remediation

Date:

- August 14, 2026

Status:

- `TEST_CONSOLE_READY_FOR_FINAL_REALISTIC_SCENARIO_RERUN`

Repository:

- `/Users/serinya/Documents/WNC Rental Automation`

## Scope

This remediation addressed only the two remaining high-severity projection defects from the post-remediation realistic-rental rerun:

1. `BUG-RERUN-001`
   - approved booking-fee override did not change the projected effective booking fee
2. `BUG-RERUN-002`
   - fresh empty or incomplete test rentals projected `Studio Space` as current rental scope without governed support

Out of scope and intentionally unchanged:

- inquiry-loop generation
- follow-up creation policy
- capacity-rule wiring
- alternative-feasibility orchestration
- storage-price authority gaps
- lifecycle semantics
- execution semantics
- new business rules
- UI expansion
- provider integrations
- schema migrations

## Root Causes

### `BUG-RERUN-001`

The Working Proposal booking-fee projection only treated an active case decision as effective when the decision payload exposed a truthy `waived` marker.

The real approved waiver case did not use that shape. Its active `booking_fee_override` decision stored:

- `decision_type = booking_fee_override`
- `status = active`
- `baseline_reference = phase4:booking_fee`
- `effective_value_payload = {"booking_fee": 0, "currency": "USD", ...}`

Because no `waived=true` flag existed, the projection incorrectly fell back to the baseline line even after approval and activation.

### `BUG-RERUN-002`

Fresh test rentals were not merely rendered incorrectly; they were persisted incorrectly.

The test-console create path inserted:

- `rental_type_code = studio_space`

for every new case, including empty and incomplete cases.

The projection then humanized that persisted value and deterministically mapped it to:

- `Rental type = Studio Space`
- `Requested spaces = Studio Space`

This was a test-harness default bug, not a cosmetic-only projection bug.

## Remediation

Files changed:

- `tools/phase_08_workflow/test_console_projection.py`
- `tools/phase_08_workflow/test_console_service.py`
- `tools/phase_08_workflow/tests/test_test_console_projection.py`
- `tools/phase_08_workflow/tests/test_test_console_service.py`
- `docs/phase-08/PHASE_8_TEST_CONSOLE_FINAL_PROJECTION_TRUTH_REMEDIATION.md`

No migration was required.

No schema change was required.

### Creation-path correction

`tools/phase_08_workflow/test_console_service.py`

- replaced the test-console fresh-case seed from `studio_space` to `custom_scope`
- added a narrow service test proving new case inserts no longer persist `studio_space`

### Scope projection correction

`tools/phase_08_workflow/test_console_projection.py`

- added an explicit set of specific governed rental-type labels:
  - `studio_space`
  - `entire_venue`
- changed current-scope rendering to:
  - show `Studio Space` only for persisted `studio_space`
  - show `Entire Venue` only for persisted `entire_venue`
  - otherwise show `Not established`
- changed requested-space rendering to use deterministic mapping only when current structured scope safely supports it

### Commercial effective-value correction

`tools/phase_08_workflow/test_console_projection.py`

- added active booking-fee decision selection based on case-decision type, status, and baseline reference
- rendered case-effective booking-fee value from the actual active decision payload
- preserved the baseline line separately for auditability
- treated active zero-fee booking-fee overrides as effective even when the payload does not carry `waived=true`
- kept pending and superseded decisions non-effective

## Canonical Projection Behavior After Remediation

Fresh empty or incomplete case:

- `Rental type = Not established`
- `Requested spaces = Not established`

Explicit governed studio scope:

- `Rental type = Studio Space`
- `Requested spaces = Studio Space`

Explicit governed entire-venue scope:

- `Rental type = Entire Venue`
- `Requested spaces = Entire Venue`

Pending booking-fee exception:

- `Booking fee baseline = governed Phase 4 value`
- `Case-specific exception = Pending`
- `Effective booking fee = governed baseline`

Active booking-fee exception:

- `Booking fee baseline = governed Phase 4 value`
- `Case-specific exception = Waived`
- `Effective booking fee = EUR 0`

Superseded or inactive case decision:

- does not determine the current effective booking fee

## Focused Tests

Focused console subset:

- command:
  - `python3 -m unittest tools.phase_08_workflow.tests.test_test_console_projection tools.phase_08_workflow.tests.test_test_console_service tools.phase_08_workflow.tests.test_test_console_app`
- result:
  - `33 / 33 PASS`

Focused coverage includes:

- fresh empty rental truth safety
- incomplete inquiry scope safety
- explicit studio scope projection
- explicit entire-venue scope projection
- pending booking-fee waiver behavior
- active booking-fee waiver behavior
- superseded booking-fee waiver behavior
- baseline-only commercial behavior
- baseline preserved before vs after approval
- create-case default persistence safety

## Full Regressions

Phase 8:

- command: `python3 -m pytest tools/phase_08_workflow/tests -q`
- result: `141 / 141 PASS`

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

- command: `npx -y supabase@latest test db --local supabase/tests`
- result: `41 files / 1059 tests PASS`

## Request-Path Stability Check

Fresh local console instance:

- `http://127.0.0.1:8767`

Repeated loads:

- root median: `103.8 ms`
- root slowest: `352.7 ms`
- rich-case median: `640.2 ms`
- rich-case slowest: `872.3 ms`

Stability result:

- hangs: `0`
- progressive degradation: `0`

## Targeted Scenario Rerun

| Scenario | Previous rerun result | Post-fix result | Targeted defect status | Evidence |
| - | - | - | - | - |
| `2` Incomplete Inquiry | `FAIL` | `PARTIAL` | `BUG-RERUN-002` closed | fresh case `212` persisted `rental_type_code=custom_scope`; projection shows `Rental type = Not established`, `Requested spaces = Not established`; unresolved inquiry follow-up generation remains out of scope |
| `3` Capacity / Large Guest Count | `NOT CURRENTLY SUPPORTED` | `NOT CURRENTLY SUPPORTED` | `BUG-RERUN-002` closed | fresh case `213` shows observed guest count `85`, but current scope remains `Not established`; capacity / whole-venue feasibility remains unwired |
| `4` Unsupported Exact Request but Possible Alternative | `NOT CURRENTLY SUPPORTED` | `NOT CURRENTLY SUPPORTED` | `BUG-RERUN-002` closed | fresh case `214` keeps current scope `Not established`; alternative-feasibility path still not implemented |
| `5` Booking Fee Waiver | `PARTIAL` | `PASS` | `BUG-RERUN-001` closed | case `145` still shows pending exception with baseline effective fee; case `197` now shows `Case-specific exception = Waived` and `Effective booking fee = EUR 0` while baseline stays `EUR 75 excl. VAT` |
| `14` Approval-Required Action | `PARTIAL` | `PASS` | `BUG-RERUN-001` closed | case `197` shows approval `50` approved, decision `34` active, blocker `66` resolved, actions `95/96` superseded, and no remaining current attention |
| `18` Human Working Proposal Audit | `PARTIAL` | `PARTIAL` | both targeted defects closed | rich case now projects correct approved commercial truth and fresh-case defaults are safe, but broader operator UX gaps remain out of scope |
| `20` Empty / New Rental | `FAIL` | `PASS` | `BUG-RERUN-002` closed | fresh case `211` persisted `custom_scope`, projected `Rental type = Not established`, `Requested spaces = Not established`, and produced no facts, blockers, approvals, actions, or follow-ups |

## Safety Metrics

- fabricated fresh-case scope = `0`
- observation-only scope promoted to current = `0`
- raw prose scope promoted to current = `0`
- pending commercial decision shown as effective = `0`
- superseded commercial decision shown as effective = `0`
- active booking-fee override ignored by projection = `0`
- Phase 4 global booking fee mutated = `0`
- projection-triggered mutation = `0`
- LLM calls added = `0`
- provider calls added = `0`
- business-rule changes = `0`
- workflow semantic changes = `0`

## Remaining Known Out-of-Scope Gaps

1. Incomplete inquiries still do not automatically become useful open-question or follow-up workflows.
2. Whole-venue capacity evaluation is still not expressed operationally through the test-console path.
3. Alternative-feasibility guidance for unsupported exact requests is still not surfaced deterministically.
4. Rich-case stale or ambiguous outcome surfacing at top level is still weaker than ideal.
5. This remediation does not add inquiry promotion, provider execution changes, or new authority rules.

## Readiness Assessment

This remediation closes the only two remaining high-severity projection-truth defects from the post-remediation rerun without changing business rules, workflow semantics, or persistence contracts.

Current readiness marker:

- `TEST_CONSOLE_READY_FOR_FINAL_REALISTIC_SCENARIO_RERUN`
