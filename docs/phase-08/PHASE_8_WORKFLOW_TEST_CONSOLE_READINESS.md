# Phase 8 Workflow Test Console Readiness

## Purpose

The Rental Workflow Test Console exists to make existing Phase 8 case state and workflow control visible to a human operator before the first governed inbound inquiry flow is wired.

This phase adds:

- a local-only server-rendered console
- a read aggregation layer over existing Phase 8 repositories
- controlled test RentalCase creation
- controlled raw evidence and structured observation test input
- guarded runtime triggers for reconciliation, approvals, action execution, and follow-up evaluation
- a read-only Living Working Proposal projection

This phase does **not** add new workflow logic, new AI extraction, inbound Outlook, or autonomous agents.

## Framework Choice

Selected stack:

- Python standard-library WSGI app via `wsgiref.simple_server`
- server-rendered HTML
- existing Python repository/runtime modules

Reasoning:

- the repository is Python-heavy and does not contain an existing web framework
- a local internal harness does not justify a Node or React stack
- privileged Supabase access remains server-side
- integration tests can exercise the app without a browser automation dependency

## Local-Only Security Model

Default environment:

- `WORKFLOW_TEST_CONSOLE_HOST=127.0.0.1`
- `WORKFLOW_TEST_CONSOLE_PORT=8765`
- `WORKFLOW_TEST_CONSOLE_ALLOW_NON_LOCAL_BIND=false`
- `WORKFLOW_TEST_CONSOLE_ALLOW_REAL_PROVIDERS=false`

Behavior:

- non-local binding fails closed unless explicitly enabled
- browser code never receives Supabase service credentials
- browser code never receives Asana or Outlook credentials
- real provider execution is disabled by default
- when enabled, the UI displays `REAL PROVIDER EXECUTION ENABLED`

## Test-Case Isolation

Test cases are identified through a persisted `workflow_events` marker:

- `event_type_code = test_console_case_registered`
- `source_type = test_console`

This avoids parallel case state and preserves append-only audit semantics.

Test-only operations:

- require the marker event
- reject unmarked cases
- do not expose delete or reset of non-test cases

## Read Projection Architecture

The console reads through:

```text
console UI
  -> test console service/query layer
  -> existing Phase 8 repositories/runtimes
  -> Supabase
```

The read layer aggregates:

- case snapshot
- facts
- questions
- requirements
- blockers
- changes
- decisions
- approvals
- actions
- attempts
- follow-ups
- reasoning projections
- workflow events
- raw evidence marker events

## Mutation Boundaries

The console does not directly edit business rows from the browser.

Mutations use:

- `ingest_structured_observations(...)`
- `reconcile_workflow_orchestration(...)`
- `apply_approval_decision(...)`
- `execute_workflow_action(...)`
- `evaluate_due_follow_ups(...)`

Raw test evidence storage uses a test-console fixture boundary:

- inbound source record persistence
- test-console workflow event carrying full pasted/raw message content

This is explicitly test-only and not the future inbound Outlook ingestion architecture.

## Working Proposal Projection

The Living Working Proposal is a deterministic projection built from:

- current `RentalCase`
- `RentalCaseFact`
- open workflow entities
- artifact freshness
- latest visible communication evidence

It is:

- human-readable
- read-only
- derived from structured truth

It is not:

- editable machine truth
- a second truth store
- a document-generation phase

## Runtime Controls Exposed

Exposed controls:

- run orchestration reconciliation
- approve request
- reject request
- execute eligible workflow action
- evaluate follow-ups
- inject raw test evidence
- inject structured test observation

Not exposed:

- direct lifecycle-state edits
- direct workflow-action status edits
- direct blocker status edits
- direct canonical truth updates from UI fields

## Current Limitations

- the console is intentionally server-rendered and utilitarian
- no production authentication layer is introduced in this phase
- raw test evidence persistence is a test harness, not inbound email ingestion
- cleanup is documented as local reset / namespace handling, not exposed as production-capable delete
- no DOCX output is generated in this phase

## Launch

```bash
python3 -m tools.phase_08_workflow.test_console
```

The Phase 8 architecture remains ready for the first end-to-end inquiry flow, and now has a human-visible local test harness suitable for building and validating it.
