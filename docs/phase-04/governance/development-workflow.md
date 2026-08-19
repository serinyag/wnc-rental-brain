# Development Workflow

## Working Sequence

```text
Requirement
↓
Acceptance criteria
↓
Architecture decision
↓
Implementation
↓
Database reset
↓
Test
↓
Review
↓
Documentation
↓
Release
```

## Practical Git Conventions

- use short-lived feature branches when the work is larger than a small documentation fix
- keep one logical change set per branch where possible
- write migration files in timestamp order
- never rewrite historical migration files after shared review unless the branch is still private
- prefer small PRs or reviewable commits over large mixed batches

## Database Workflow

1. Update the relevant requirement or governance note first if the policy interpretation changes.
2. Add or edit migration SQL.
3. Run `npx -y supabase@latest db reset`.
4. Run `npx -y supabase@latest test db`.
5. Review seeded data and source links.
6. Update architecture or validation docs if the design changed.

## Repository Hygiene

- do not commit secrets
- preserve original source files without rewriting them
- keep seed data conservative and source-backed
- do not load uncertain policy values just because a table exists

## Review Expectations

Every review should check:

- source traceability
- canonical vocabulary alignment
- versioning safety
- migration rebuildability
- tests for new invariants
- documentation drift between design and implementation
