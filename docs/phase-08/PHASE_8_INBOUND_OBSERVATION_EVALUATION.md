# Phase 8.3 Inbound Observation Evaluation

Date:

- August 10, 2026

Status:

- `PHASE_8_3_EVALUATION_COMPLETE`

## Scope Evaluated

Phase 8.3 evaluates only the safe inbound observation and proposed-change foundation:

- provider-neutral inbound source normalization
- deterministic case-association boundary
- governed observation field registry
- structural observation validation
- deterministic routing to safe proposed workflow effects
- proposed change, proposed decision, reschedule, requirement-evidence, and open-question-answer candidate creation
- stale-observation and revalidation posture
- idempotent source replay behavior
- SQL integrity for same-case linkage and append-only evidence records

Explicitly out of scope:

- live Outlook or external platform ingestion
- LLM extraction providers
- direct lifecycle transitions from observations
- direct canonical fact activation from observations
- approval activation
- action planning or adapter execution
- UI, agents, persistence consumers, or answer generation

## Repository Areas Evaluated

Architecture and governance inputs:

- `docs/phase-08/PHASE_8_WORKFLOW_EXECUTION_ARCHITECTURE.md`
- `docs/phase-08/PHASE_8_WORKFLOW_DOMAIN_MODEL.md`
- `docs/phase-08/PHASE_8_WORKFLOW_BUSINESS_DECISIONS.md`
- `docs/phase-08/PHASE_8_PHASE7_WORKFLOW_CONSUMPTION_CONTRACT.md`
- `docs/phase-08/PHASE_8_IMPLEMENTATION_ROADMAP.md`
- `docs/phase-08/PHASE_8_WORKFLOW_PERSISTENCE_SCHEMA.md`
- `sources/phase-01-03/Knowledge Governance/WNC Rental Data Dictionary.xlsm`

Live implementation surfaces:

- `tools/phase_08_workflow/observation_contracts.py`
- `tools/phase_08_workflow/observation_types.py`
- `tools/phase_08_workflow/observation_registry.py`
- `tools/phase_08_workflow/observation_repository.py`
- `tools/phase_08_workflow/observations.py`
- `supabase/migrations/20260810000100_phase_08_inbound_observation_foundation.sql`
- `supabase/tests/36_phase_08_inbound_observation_foundation.sql`

## Focused Acceptance Coverage

Python observation coverage now proves:

- governed unknown-field rejection without dynamic truth creation
- deterministic case-association failure when no reliable case binding exists
- distinct handling for previously unknown values versus changed values
- material/current fact changes becoming `ProposedCaseChange`
- booking-fee waiver inputs becoming proposed `CaseDecision` only
- active-event change requests becoming `RescheduleRequest` only
- open-question candidate answers staying `answered_pending_validation`
- stale observations requiring revalidation
- duplicate source replay creating zero duplicate semantic effects
- cross-case requirement evidence writes failing closed
- lifecycle state staying unchanged when workflow events are recorded from observations

Database coverage now proves:

- the new provider-neutral source, observation, effect, and case-fact tables exist in the live schema
- RLS and no-ordinary-role direct grants apply to the new tables
- source dedupe keys are unique
- resolved versus unresolved case-association constraints fail closed
- observation confidence, target-pair, and identity constraints are enforced
- effect linkage stays same-case through composite foreign keys
- source records and observation effects are append-only
- observation persistence does not mutate lifecycle state

## Verification Results

Focused observation Python suites:

- `python3 -m unittest tools.phase_08_workflow.tests.test_observation_contracts tools.phase_08_workflow.tests.test_observation_registry tools.phase_08_workflow.tests.test_observation_ingestion`
- result: `15 / 15` passing

Full Phase 8 Python suite:

- `python3 -m unittest discover -s tools/phase_08_workflow/tests`
- result: `52 / 52` passing

Cross-phase Python regressions:

- `python3 -m unittest discover -s tools/phase_07_reasoning/tests`
- result: `127 / 127` passing

- `python3 -m unittest discover -s tools/phase_05_search/tests`
- result: `24 / 24` passing

- `python3 -m unittest discover -s tools/phase_06_search/tests`
- result: `6 / 6` passing

Database regression:

- `npx -y supabase@latest test db --local`
- result: `36` files, `1013` tests, `PASS`

Local reset restoration steps required before the final DB run:

- `python3 -m tools.phase_05_chunking.generate_bulk --load-db`
- rebuilt current chunk corpus to `22` current chunk sets and `525` generated chunks

- `python3 -m tools.phase_06_search.generate_embeddings`
- reseeded deterministic historical embeddings to `112 / 112` eligible units

## Evaluation Metrics

Deterministic observation acceptance fixture set:

- evaluated scenarios: `15`
- structured observation validation accuracy: `1.0`
- duplicate side-effect count: `0`
- unknown-field truth-creation count: `0`
- direct material truth mutation count: `0`
- active `CaseDecision`-from-observation violation count: `0`
- direct reschedule activation count: `0`
- cross-case write violation count: `0`
- ambiguous-case auto-association count: `0`
- lifecycle mutation from observation count: `0`
- stale-observation unsafe-consumption count: `0`
- provenance completeness: `1.0`

## Validation Notes

The evaluation surfaced and resolved three implementation issues before final pass:

- observation contract and ingestion request modules were missing the optional non-negative revision validator import
- package import/export needed the observation contract version and stable ingestion entry point wired at package level
- the same-case foreign-key DB test initially reused an observation row that already had an effect, so the test fixture was corrected to use a fresh observation row before asserting the cross-case failure

## Final Judgment

Phase 8.3 passes its containment-layer acceptance slice.

What is now validated:

- extraction remains evidence, not authority
- inbound structured observations cannot directly mutate canonical workflow truth
- client or operator inputs can safely become proposed workflow records with provenance
- field hallucinations fail closed through unmapped or quarantine paths
- stale and ambiguous observations remain review-bound rather than silently consumed
- observation persistence does not choose lifecycle state or trigger hidden lifecycle mutation

Phase 8.3 is therefore validated as complete for the inbound observation and proposed-change foundation layer.
