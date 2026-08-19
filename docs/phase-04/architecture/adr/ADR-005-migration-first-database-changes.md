# ADR-005: Migration-First Database Changes

## Status

Accepted.

## Context

The repository is greenfield, and the brief explicitly requires a rebuildable development database with no hidden production-only schema state.

## Decision

All database structure changes must enter the repository as ordered migrations first, then be exercised through local reset and tests.

## Consequences

- local development, review, and future deployments share the same schema history
- onboarding remains simpler for later contributors
- policy structure cannot drift silently in an unmanaged remote database

## Workflow

```text
migration
→ local start
→ db reset
→ db test
→ review
→ future deployment
```

## Rejected Alternative

Manual remote schema edits followed by later backfill into migration files.

Why rejected:

- breaks reproducibility
- weakens reviewability
- risks production-only behavior that is absent from source control
