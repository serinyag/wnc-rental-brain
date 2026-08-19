# Phase 8 Approval, Blocker & Action Orchestration Evaluation

Date:

- August 13, 2026

Status:

- `PHASE_8_5R_EVALUATION_COMPLETE`

## Scope Evaluated

Phase 8.5 plus Phase 8.5-R evaluate the deterministic orchestration layer that converts structured workflow state into:

- governed blocker creation and resolution
- governed approval creation and decisioning
- structured workflow action creation
- workflow-action approval-state progression without execution
- requirement creation from governed reasoning-effect mappings
- artifact freshness packaging
- deterministic case-decision activation
- deterministic proposed-change resolution
- case-revision-safe Supabase persistence commits

Explicitly out of scope:

- external execution adapters
- lifecycle transitions
- outbound communication sending
- proposal or agreement regeneration
- agents, queues, schedulers, or UI

## Repository Areas Evaluated

Architecture and governance inputs:

- `docs/phase-08/PHASE_8_WORKFLOW_EXECUTION_ARCHITECTURE.md`
- `docs/phase-08/PHASE_8_WORKFLOW_DOMAIN_MODEL.md`
- `docs/phase-08/PHASE_8_WORKFLOW_ACTION_TAXONOMY.md`
- `docs/phase-08/PHASE_8_WORKFLOW_BUSINESS_DECISIONS.md`
- `docs/phase-08/PHASE_8_PHASE7_WORKFLOW_CONSUMPTION_CONTRACT.md`
- `docs/phase-08/PHASE_8_IMPLEMENTATION_ROADMAP.md`

Live implementation surfaces:

- `tools/phase_08_workflow/contracts.py`
- `tools/phase_08_workflow/orchestration_types.py`
- `tools/phase_08_workflow/orchestration_repository.py`
- `tools/phase_08_workflow/orchestration_runtime.py`
- `tools/phase_08_workflow/__init__.py`
- `tools/phase_08_workflow/tests/test_orchestration_runtime.py`
- `supabase/migrations/20260813000100_phase_08_orchestration_identity_guards.sql`
- `supabase/migrations/20260813000200_phase_08_orchestration_atomicity_remediation.sql`
- `supabase/tests/38_phase_08_approval_blocker_action_orchestration.sql`
- `supabase/tests/39_phase_08_orchestration_persistence_atomicity_remediation.sql`

## Focused Acceptance Coverage

Focused Phase 8.5 runtime coverage now proves:

- missing client information creates one semantic blocker and one semantic client-information action
- repeated reconciliation is idempotent for unchanged question state
- resolved questions deterministically resolve blockers and supersede stale actions
- approval-required booking-fee waiver proposals stay case-inactive until explicit approval
- approved booking-fee waiver decisions activate case-scoped exception truth without mutating Phase 4 baseline
- rejected booking-fee waiver decisions preserve baseline truth
- same-scope active case-decision conflicts fail closed
- workflow-action approvals advance only through controlled application mutation
- `human_only` workflow actions stop at `approved`
- rejected workflow-action approvals cancel the governed action without execution
- workflow-action approval replays are idempotent
- insufficient current authority does not create current price truth from history
- accepted proposed changes mutate canonical case facts exactly once through the controlled mutation boundary

Focused DB coverage now proves:

- case-decision approval, case revision increment, artifact freshness, stale-action supersession, blocker resolution, and audit append occur atomically
- workflow-action approval can expose `ready_to_execute` state without creating execution attempts
- proposed-change acceptance can atomically update canonical fact state, case revision, artifacts, actions, blockers, and audit rows
- stale revisions fail closed inside the DB helper boundary

## Verification Results

Focused Phase 8.5 runtime suite:

- `python3 -m unittest tools.phase_08_workflow.tests.test_orchestration_runtime`
- result: `13 / 13` passing

Full Phase 8 Python suite:

- `python3 -m unittest discover -s tools/phase_08_workflow/tests`
- result: `73 / 73` passing

Cross-phase Python regressions:

- `python3 -m unittest discover -s tools/phase_07_reasoning/tests`
- result: `127 / 127` passing

- `python3 -m unittest discover -s tools/phase_05_search/tests`
- result: `24 / 24` passing

- `python3 -m unittest discover -s tools/phase_06_search/tests`
- result: `6 / 6` passing

Database regression:

- `npx -y supabase@latest test db --local supabase/tests/39_phase_08_orchestration_persistence_atomicity_remediation.sql`
- result: `10 / 10` assertions passing

- `npx -y supabase@latest test db --local`
- result: `39` files, `1042` tests, `PASS`

Post-reset local verification restoration:

- `python3 -m tools.phase_05_chunking.generate_bulk --load-db`
- rebuilt the current chunk corpus to `22` current chunk sets and `525` chunks

- deterministic local historical embedding reseed inserted `112` historical embeddings
- resulting historical embedding coverage: `100.0%`

## Evaluation Metrics

Deterministic Phase 8.5 acceptance fixture set:

- evaluated runtime scenarios: `13`
- evaluated DB scenarios: `10`
- blocker creation accuracy: `1.0`
- blocker resolution accuracy: `1.0`
- approval-policy accuracy: `1.0`
- CaseDecision activation accuracy: `1.0`
- workflow-action approval-state accuracy: `1.0`
- proposed-change resolution accuracy: `1.0`
- action creation accuracy: `1.0`
- action idempotency: `1.0`
- action supersession accuracy: `1.0`
- artifact freshness behavior: `1.0`
- case revision accuracy: `1.0`
- lifecycle mutation violation count: `0`
- external execution violation count: `0`
- historical-gap-filling violation count: `0`
- Phase 4 mutation count: `0`
- answer-prose influence count: `0`
- duplicate semantic effect count: `0`
- audit completeness: `1.0`

## Validation Notes

The remediation closeout surfaced and resolved three concrete production-shape gaps:

- the local Supabase repository wrapper still pointed at a non-existent case-decision activation helper and was remapped onto the approval-centered atomic commit surface
- the new PL/pgSQL helper outputs initially shadowed unqualified table columns such as `rental_case_id`, so the remediation migration now declares `#variable_conflict use_column`
- a local DB reset removed non-seeded Phase 5 current chunk sets and the active historical embedding fixture, so verification now explicitly restores both before running the full live regression

## Final Judgment

Phase 8.5 passes its deterministic orchestration acceptance slice for both the in-memory runtime and the persisted Supabase commit boundary.

What is now validated:

- structured workflow state deterministically produces blockers, approvals, requirements, and action intent
- unchanged workflow state does not duplicate semantic effects
- approval-gated case decisions stay inactive until explicit approval
- workflow-action approvals release actions into governed ready state without executing them
- historical precedent does not become current case truth
- canonical case-fact mutation remains revision-safe and bounded
- persisted orchestration commits are atomic, auditable, and fail closed on stale state
- orchestration remains separate from lifecycle mutation and external execution

Readiness outcome:

- `READY_FOR_PHASE_8_EXECUTION_AND_FOLLOW_UP_RUNTIME`
