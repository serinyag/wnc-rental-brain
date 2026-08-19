# Phase 8 Workflow Persistence Readiness

Date assessed: 2026-08-09

## Audit Scope

This audit evaluates whether Phase 8.1 persistence faithfully represents the frozen Phase 8.0B workflow architecture and is sufficient for the next implementation boundary.

Assessment includes:

- schema structure
- controlled vocabularies
- case-scope safety
- append-only audit posture
- idempotency representation
- minimal Phase 7 workflow reasoning projection persistence
- typed contract coverage
- focused and regression test outcomes

## Architecture Fidelity

The implemented persistence layer matches the frozen architecture in the following ways:

- every active rental case has explicit lifecycle-state storage
- lifecycle state is constrained to the 12 frozen canonical values
- lifecycle transitions are stored as append-only history rather than inferred from events
- workflow facts are stored separately from lifecycle state, preventing hidden event-triggered mutation
- case-specific truth is scoped to `rental_case_id`
- `CaseDecision` stores baseline references and scoped overrides without mutating Phase 4
- one active decision per case/domain/scope can be enforced through a partial unique index
- material changes stay proposed until accepted
- approvals are modeled independently of any external task surface
- actions exist before execution, and attempts are modeled as separate append-only history
- executable actions are idempotency-protected at the persistence level
- artifact freshness and stale-case-revision detection surfaces exist
- minimal Phase 7 reasoning provenance is persistable without storing full ContextPackages or prompts

## Invariant Coverage

`P8-INV-*` expectations covered in Phase 8.1:

- active rental lifecycle truth: covered
- application-controlled lifecycle state: covered
- Phase 4 remains deterministic truth: covered
- case-specific truth stays case-scoped: covered
- historical precedent does not become workflow policy automatically: covered
- missing authority becomes explicit state: covered through reasoning projections and decision posture surfaces
- material changes stay proposed until accepted: covered
- approval requirements are explicit: covered
- actions exist before execution: covered
- execution failure cannot silently advance case state: covered
- executable actions are idempotency protected: covered
- workflow history is auditable: covered
- generated prose is not workflow truth: covered

## Safety Strengths

- append-only protection on workflow events, lifecycle transitions, execution attempts, and reasoning projections
- `restrict` deletion posture across the aggregate
- same-case foreign keys for directly representable relationships
- controlled-vocabulary checks instead of freeform status fields
- partial unique index for active `CaseDecision` scope conflict prevention
- no SQL trigger silently updates `rental_cases.lifecycle_state` from event insertion
- no external-system approval truth fields were introduced into the core model

## Known Boundaries

These are accepted Phase 8.1 boundaries, not readiness blockers:

- lifecycle transition legality is not yet enforced by runtime logic
- polymorphic references still require application validation when direct FKs are impossible
- no scheduler, executor, retry engine, approval orchestration, or workflow evaluator exists yet
- no inbound email extraction or Phase 7 runtime reasoning execution is implemented
- RLS is enabled and privileges are revoked, but runtime policies are deferred

## Verification Results

Focused Phase 8 verification:

- Phase 8 Python contracts: `14/14` passing
- Phase 8 DB persistence test: `40/40` assertions passing

Regression verification:

- full DB regression: `34 files / 977 assertions PASS`
- Phase 7 reasoning Python regression: `127/127` passing
- Phase 5 search Python regression: `24/24` passing
- Phase 6 search Python regression: `6/6` passing

Verification setup note:

- after local reset, Phase 5 current-corpus bulk state was regenerated
- Phase 6 regression required seeding a deterministic local historical embedding fixture because no `OPENAI_API_KEY` was available and the reset state had no active retrieval-approved historical model

This setup work did not require repository code changes outside the Phase 8.1 implementation itself.

## Blocker Check

No Phase 8.1 blocker remains for:

- canonical rental-case persistence
- lifecycle-state storage
- transition history
- event persistence
- open-question, requirement, blocker, decision, proposed-change, reschedule, approval, action, execution-attempt, follow-up, milestone, artifact, and reasoning-projection persistence
- typed contracts and structural validation
- focused tests
- prior DB and Python regressions

## Readiness Conclusion

READY_FOR_PHASE_8_LIFECYCLE_ENGINE_IMPLEMENTATION
