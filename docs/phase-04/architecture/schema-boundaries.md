# Schema Boundaries

## `public`

Purpose:

- canonical entities that future applications can read
- rule-governance records
- typed rule tables approved for application use
- approved views that expose current or audit-friendly rule state

Phase 4 implemented foundation tables:

- `public.source_registry`
- `public.rental_types`
- `public.venue_spaces`
- `public.rule_catalogue`
- `public.rule_source_links`

Boundary rules:

- keep canonical business data here
- do not expose raw scratch tables or ingestion intermediates here
- do not use `public` as a dumping ground for future AI artifacts

## `api`

Purpose:

- approved SQL functions and RPC entry points for future applications

Phase 4 position:

- create the schema now
- defer non-trivial RPC functions until a typed rule domain is loaded

Boundary rules:

- keep externally callable functions stable and reviewed
- treat `api` as the contract surface for future application consumption

## `private`

Purpose:

- internal support objects that should not be treated as application-facing canonical data

Examples:

- internal helper functions
- deferred integrity helpers
- implementation details used by triggers or audit helpers

Boundary rules:

- prefer `public` unless there is a clear reason to hide the object
- do not place authoritative policy itself in `private`

## Deliberate Exclusions

The following do not belong in Phase 4 schema design:

- embeddings
- chunk stores
- knowledge vectors
- email ingestion staging
- intake-form submissions
- live rental facts
- contact and organization CRMs
- speculative future automation tables
