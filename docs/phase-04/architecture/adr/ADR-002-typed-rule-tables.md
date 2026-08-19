# ADR-002: Typed Rule Tables

## Status

Accepted for the target architecture. Foundation migration deferred to later slices.

## Context

Commercial, capacity, and access logic needs to be queryable, testable, and human-auditable. The source set contains structured concepts like rental type, duration band, VAT rate, capacity, and access status that map naturally to relational columns.

## Decision

Represent important rule values in typed relational tables rather than storing the full rule body in generic JSON.

## Consequences

- SQL constraints can enforce invariants
- range queries and indexed lookups remain simple
- future API functions can expose predictable contracts
- database tests can target named columns rather than JSON paths

## Rejected Alternative

Store all rules in a single JSONB payload per rule row.

Why rejected:

- core business logic becomes harder to query and validate
- uniqueness and range constraints become weaker
- future app code would need more interpretation logic for basic rule retrieval
