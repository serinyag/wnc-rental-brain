# Phase 8 Phase 7 Workflow Consumption Evaluation

Date:

- August 10, 2026

Status:

- `PHASE_8_4_EVALUATION_COMPLETE`

## Scope Evaluated

Phase 8.4 evaluates only the structured Phase 7 to Phase 8 workflow-consumption runtime:

- deterministic consumption of finalized `ContextPackage`
- explicit rejection of unsupported Phase 7 contract versions
- case-scoped revision validation before workflow projection persistence
- workflow-safe authority, conflict, contamination, degraded, and unresolved-authority preservation
- deterministic workflow posture derivation from Phase 7 structure only
- idempotent reasoning-projection persistence through case-scoped identity keys
- structured workflow-effect derivation from persisted reasoning projections
- confidentiality, PI, and de-identification carry-through into workflow-safe projection metadata
- SQL support for the new projection identity and safety fields

Explicitly out of scope:

- answer prose consumption as workflow truth
- lifecycle mutation
- canonical case-fact activation or mutation
- blocker, approval, action, or decision creation
- outbound providers, adapters, agents, or answer generation

## Repository Areas Evaluated

Architecture and governance inputs:

- `docs/phase-08/PHASE_8_PHASE7_WORKFLOW_CONSUMPTION_CONTRACT.md`
- `docs/phase-08/PHASE_8_WORKFLOW_EXECUTION_ARCHITECTURE.md`
- `docs/phase-08/PHASE_8_WORKFLOW_DOMAIN_MODEL.md`
- `docs/phase-08/PHASE_8_WORKFLOW_BUSINESS_DECISIONS.md`
- `docs/phase-08/PHASE_8_IMPLEMENTATION_ROADMAP.md`

Live implementation surfaces:

- `tools/phase_08_workflow/contracts.py`
- `tools/phase_08_workflow/phase7_consumption_types.py`
- `tools/phase_08_workflow/phase7_consumption_repository.py`
- `tools/phase_08_workflow/phase7_workflow_consumer.py`
- `tools/phase_08_workflow/__init__.py`
- `supabase/migrations/20260810000200_phase_08_phase7_workflow_consumption_runtime.sql`
- `supabase/tests/37_phase_08_phase7_workflow_consumption_runtime.sql`

Phase 7 contract sources inspected for live shape alignment:

- `tools/phase_07_reasoning/contracts.py`
- `tools/phase_07_reasoning/context_assembler.py`
- `tools/phase_07_reasoning/authority_resolver.py`
- `tools/phase_07_reasoning/contamination_gate.py`
- `tools/phase_07_reasoning/context_safety.py`
- `tools/phase_07_reasoning/answer_layer.py`

## Focused Acceptance Coverage

Focused Phase 8.4 Python coverage now proves:

- deterministic-current authority becomes a persisted workflow reasoning projection
- duplicate Phase 7 consumption is idempotent within a rental case
- `REQUIRES_CONFIRMATION` remains explicit as review posture and workflow effect
- `INSUFFICIENT_CURRENT_AUTHORITY` remains fail-closed for current-decision use
- workflow effects are derived from structured projection state rather than generated prose
- final confidentiality and de-identification posture carry into the persisted workflow-safe projection
- historical-only items cannot be smuggled into current-truth slots
- stale case revisions and unsupported Phase 7 contract versions fail closed
- zero case revision remains valid for workflow reasoning effects

Database coverage now proves:

- `rental_case_reasoning_projections` includes the Phase 8.4 identity and safety columns
- case-scoped projection identity is unique and idempotency-safe
- reasoning-state, workflow-posture, and confidentiality enumerations are enforced in SQL
- blank identity keys fail closed
- new workflow-consumption boolean safety fields persist predictably

## Verification Results

Focused Phase 8.4 Python suites:

- `python3 -m unittest tools.phase_08_workflow.tests.test_phase7_consumption_types tools.phase_08_workflow.tests.test_phase7_workflow_consumer`
- result: `8 / 8` passing

Full Phase 8 Python suite:

- `python3 -m unittest discover -s tools/phase_08_workflow/tests`
- result: `60 / 60` passing

Cross-phase Python regressions:

- `python3 -m unittest discover -s tools/phase_07_reasoning/tests`
- result: `127 / 127` passing

- `python3 -m unittest discover -s tools/phase_05_search/tests`
- result: `24 / 24` passing

- `python3 -m unittest discover -s tools/phase_06_search/tests`
- result: `6 / 6` passing

Database regression:

- `npx -y supabase@latest test db --local`
- result: `37` files, `1024` tests, `PASS`

Local reset restoration steps required before the final DB run:

- `npx -y supabase@latest db reset --local`
- reapplied migrations through `20260810000200_phase_08_phase7_workflow_consumption_runtime.sql`

- `python3 -m tools.phase_05_chunking.generate_bulk --load-db`
- restored current chunk corpus to `22` generated chunk sets and `525` chunks

- `python3 -m tools.phase_06_search.generate_embeddings`
- restored historical embedding coverage to `112 / 112` eligible units

## Evaluation Metrics

Deterministic Phase 8.4 acceptance fixture set:

- evaluated scenarios: `8`
- answer-prose workflow-truth consumption count: `0`
- duplicate semantic projection count: `0`
- stale-revision unsafe-consumption count: `0`
- unsupported-contract unsafe-consumption count: `0`
- historical-to-current identity contamination violations: `0`
- current-authority fail-open violations: `0`
- confidentiality carry-through mismatch count: `0`
- workflow-effect zero-revision violation count: `0`

## Validation Notes

The evaluation surfaced and resolved two implementation issues before final pass:

- the workflow-consumption effect contract temporarily lost the positive-int validator import during cleanup, which broke effect construction
- the first DB regression attempt ran against a local schema that had not yet been reset to include the new migration, so the final validation was rerun after `supabase db reset --local`

## Final Judgment

Phase 8.4 passes its structured Phase 7 workflow-consumption acceptance slice.

What is now validated:

- Phase 8 consumes structured Phase 7 context, not answer prose
- current, guidance, historical, unresolved, degraded, and contamination signals remain distinct
- workflow posture is derived deterministically from the Phase 7 authority state
- reasoning projection persistence is idempotent and case-scoped
- confidentiality and PI minimization posture survive the handoff into workflow-safe projection metadata

Phase 8.4 is therefore validated as complete for structured Phase 7 workflow consumption and is ready to hand off to downstream approval, blocker, and action-orchestration work.
