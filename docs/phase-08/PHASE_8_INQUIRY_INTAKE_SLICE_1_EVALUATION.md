# Phase 8 Inquiry Intake Slice 1 Evaluation

Date:

- August 14, 2026

Status:

- `PHASE_8_INQUIRY_INTAKE_SLICE_1_EVALUATION_COMPLETE`

## Scope Evaluated

Slice 1 evaluates the deterministic inquiry-intake promotion runtime that consumes already-persisted structured observations and decides whether each of the four core inquiry fields should become:

- governed current case truth
- an unresolved `OpenQuestion`
- a governed `ProposedCaseChange`
- a governed `RescheduleRequest`

Evaluated fields:

- requested schedule
- guest count
- requested rental scope
- event type

Explicitly out of scope:

- follow-up creation
- client email actions
- Outlook inbound transport
- extraction from raw email
- feasibility and capacity evaluation
- lifecycle advancement

## Inspection Summary

Live repository inspection confirmed:

1. observation ingestion, observation effects, and provenance storage already existed from Phase 8.3
2. current governed storage already existed for all four target fields, so a second inquiry-facts store was unnecessary
3. `RentalCase` revision semantics already existed and could be reused for optimistic inquiry-intake commits
4. `OpenQuestion`, `ProposedCaseChange`, `RescheduleRequest`, and `WorkflowEvent` tables were already sufficient for the slice
5. the major pre-slice gap was not storage but the missing deterministic promotion runtime between evidence and governed inquiry truth
6. a live-console validation run exposed one remaining contradiction in `observations.py`: fresh or incomplete schedules could still create `RescheduleRequest` rows at ingestion time
7. that contradiction was remediated during this slice so new inquiry schedules now remain evidence until inquiry intake evaluates them

## Canonical Field Mapping

| Intake field | Structured observation field | Governed current storage |
| - | - | - |
| Requested schedule | `active_event_window` | `rental_cases.active_event_start`, `rental_cases.active_event_end` |
| Guest count | `guest_count` | `rental_case_facts.guest_count` |
| Requested rental scope | `requested_rental_scope` | `rental_cases.rental_type_code` |
| Event type | `event_type` | `rental_case_facts.event_type` |

## Acceptance Coverage

Focused coverage now proves:

- complete initial inquiry can promote all four core fields
- empty inquiry creates four idempotent core open questions
- partial inquiry promotes only the known valid values
- later valid evidence resolves corresponding open questions
- current facts are never silently overwritten
- guest-count changes route to governed proposed changes
- scope changes route to governed proposed changes
- event-type changes route to governed proposed changes
- initial schedule is promoted as current truth rather than becoming a reschedule from nothing
- later date changes route to governed reschedule behavior
- conflicting initial values do not select an arbitrary winner
- cross-case observation state cannot mutate the wrong case
- stale evaluated plans fail closed on commit

## Canonical Console Validation

Validation used the live Supabase-backed Test Console path on Friday, August 14, 2026.

Local server verification:

- `python3 -m tools.phase_08_workflow.test_console`
- root route `GET /` returned `200`
- live case route `GET /cases/286` returned `200`

Canonical case runs used fresh console-created cases:

| Case | Test case id | Result | Observed outcome |
| - | -: | - | - |
| A Complete Inquiry | `286` | `PASS` | schedule, guest count, requested scope, and event type all became governed current truth; core open questions `0`; no reschedule was fabricated |
| B Incomplete Inquiry | `287` | `PASS` | no current facts were fabricated; four governed open questions were created |
| C Partial Inquiry | `288` | `PASS` | guest count `25` and event type `corporate_networking` became current truth; schedule and scope remained unresolved with two open questions |
| D Later Guest Count Change | `289` | `PASS` | current guest count stayed `30`; governed proposed change `30 -> 60` remained visible; repeated intake created no duplicate effect |
| E Later Date Change | `290` | `PASS` | initial October 3 schedule became current truth; later October 10 request stayed proposed in one governed reschedule request; repeated intake created no duplicate effect |
| F Conflicting Evidence | `291` | `PASS` | no guest-count fact was selected; guest count stayed unresolved; four governed open questions existed including guest-count clarification |
| Empty / New Rental | `292` | `PASS` | no facts were fabricated; four governed intake open questions were created after explicit intake |

## Relevant Scenario Reruns

The pre-slice benchmark comes from `docs/phase-08/PHASE_8_REALISTIC_RENTAL_SCENARIO_VALIDATION_FINAL_RERUN.md`.

Post-slice rerun observations:

| Scenario | Pre-slice status | Post-slice status | Change | Notes |
| - | - | - | - | - |
| 1 Straightforward Venue Inquiry | `PARTIAL` | `PARTIAL` | `IMPROVED` | core inquiry truth now becomes governed current state, but the next waiting/follow-up slice is still not implemented |
| 2 Incomplete Inquiry | `PARTIAL` | `PARTIAL` | `IMPROVED` | missing inquiry fields now create governed open questions instead of staying inert |
| 7 Material Guest Count Change | `NOT CURRENTLY SUPPORTED` | `PARTIAL` | `IMPROVED` | governed proposed guest-count change now exists, but downstream impact workflow is still out of scope |
| 8 Reschedule Request | `PARTIAL` | `PARTIAL` | `IMPROVED` | current schedule is now established first and later requested date stays proposed separately |
| 18 Human Working Proposal Audit | `PARTIAL` | `PARTIAL` | `IMPROVED` | inquiry-stage current truth, observed evidence, and unresolved questions are now explicit in the Working Proposal |
| 20 Empty / New Rental | `PASS` | `PASS` | `IMPROVED` | empty cases remain stable and can now materialize four governed intake questions after explicit intake |

## Focused Python Validation

Focused inquiry-intake coverage:

- `python3 -m pytest tools/phase_08_workflow/tests/test_observation_ingestion.py tools/phase_08_workflow/tests/test_inquiry_intake.py -q`
- result: `21 / 21` passing

That focused set now includes:

- initial schedule does not create a reschedule from nothing
- incomplete schedule does not create a reschedule
- full four-field promotion
- open-question idempotency
- open-question resolution
- scope change handling
- event-type change handling
- guest-count conflict handling
- reschedule duplicate suppression
- cross-case isolation
- stale-plan rejection

## Full Regressions

Phase 8:

- `python3 -m pytest tools/phase_08_workflow/tests -q`
- result: `153 / 153` passing

Phase 7:

- `python3 -m pytest tools/phase_07_reasoning/tests -q`
- result: `127 / 127` passing

Phase 5:

- `python3 -m pytest tools/phase_05_chunking/tests -q`
- result: `27 / 27` passing

Phase 6:

- `python3 -m pytest tools/phase_06_search/tests -q`
- result: `6 / 6` passing

Supabase:

- `npx -y supabase@latest test db --local`
- result: `41` files, `1059` tests, `PASS`

Focused DB tests:

- no new focused DB acceptance file was added
- reason: no migration or SQL helper surface change was required for this slice

## Performance

Live Supabase-backed intake timings across `9` canonical console runs:

- `Run Inquiry Intake` median: `12117.2 ms`
- `Run Inquiry Intake` slowest: `16307.6 ms`
- hangs during intake: `0`

Live read-path timings from the same validation run:

- `list_test_cases()` median: `279.0 ms`
- `list_test_cases()` slowest: `279.6 ms`
- `load_case_detail()` median: `1901.3 ms`
- `load_case_detail()` slowest: `2472.9 ms`

Additional WSGI server logs on Friday, August 14, 2026:

- `GET /` completed in about `434.8 ms` and `965.4 ms`
- `GET /cases/286` completed in about `2627.5 ms`

## Safety Metrics

- direct observation -> truth mutation outside promotion runtime = `0`
- LLM-selected promotion decisions = `0`
- generated prose -> case fact = `0`
- ambiguous observation promoted as current = `0`
- conflicting observations silently resolved = `0`
- existing current fact silently overwritten = `0`
- existing schedule silently overwritten = `0`
- initial requested schedule incorrectly created as reschedule = `0`
- duplicate semantic open questions = `0`
- duplicate semantic case facts = `0`
- duplicate semantic proposed changes from repeated intake = `0`
- duplicate semantic reschedule requests from repeated intake = `0`
- stale intake plans committed = `0`
- cross-case mutation = `0`
- intake-triggered lifecycle transitions = `0`
- intake-triggered provider calls = `0`
- intake-triggered Outlook sends = `0`
- intake-triggered Asana calls = `0`
- historical precedent used to fill intake fact = `0`
- Phase 4 global truth mutation = `0`

## Known Limitations

- `custom_scope` still remains the unresolved placeholder and is not treated as an established requested scope
- later guest-count or date changes may already create a governed change object during Phase 8.3 observation ingestion; intake suppresses duplicates rather than creating a second semantic change
- this slice still stops before waiting-state workflow, follow-up generation, and outbound client contact

## Final Judgment

Structured inquiry observations can now reliably become governed inquiry state for the next slice to consume.

The slice now satisfies its intended handoff boundary:

- current inquiry facts can be established deterministically
- missing core inquiry fields become governed open questions
- existing current truth remains safe
- initial requested schedule no longer becomes a reschedule from nothing
- repeated intake stays idempotent

Readiness outcome:

- `READY_FOR_PHASE_8_INQUIRY_WAITING_AND_FOLLOW_UP_SLICE`
