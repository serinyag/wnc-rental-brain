# Phase 4 Closure

## Objective achieved

Phase 4 was intended to convert current approved WNC rental policy into a governed, typed rule catalogue where deterministic truth could be stored structurally with provenance, versioning, and test coverage, while leaving unresolved or non-deterministic areas explicitly outside automation.

## Implemented structured domains

- governance and provenance foundation
- canonical rental types and spaces
- booking fees
- payment
- expedited surcharge
- cancellation
- capacity
- space access
- operational requirements
- catering and supplier feasibility
- technical capability and current inventory facts
- service and facilitator requirements

## Active policy blockers

These items remain intentionally unstructured because the approved source set is incomplete or conflicted, but they do not invalidate the correctness of the existing structured catalogue:

- `BLK-002`: broader commercial workbook precedence and drift outside the rows already loaded
- `BLK-003`: security-deposit risk matrix and standardization
- `BLK-004`: insurance trigger policy
- `BLK-005`: mandatory professional-cleaning threshold
- `BLK-006`: controlled host staffing matrix
- `BLK-007` to `BLK-009`: site-visit, final-information, and last-minute-change workflow policy
- `BLK-010` and `BLK-011`: full-production pricing methodology and staff-overtime conflict
- `BLK-012` and `BLK-013`: event-management scope and unusual-material approval ownership
- `BLK-014` and `BLK-015`: Storefront payment path and standard confirmation timing nuance
- `BLK-016` and `BLK-017`: expedited-waiver criteria and postponement/rescheduling treatment
- `BLK-018` to `BLK-020`: standalone Conversation Pit capacity, `custom_scope` room defaults, and venue-clearing lead time
- `BLK-022`: `additional_host` vocabulary gap
- `BLK-023`: facilitator cancellation commercial conflict
- `BLK-024`: unsuitable-event policy
- `BLK-025`: `light support` canonicalization and task-boundary decision

## Manual-by-policy items

Important areas intentionally left to human judgement rather than deterministic automation include:

- discounts and waiver criteria beyond storing waiver authority
- production-coordination pricing
- full-production pricing in its current approved manual state
- cleaning charges where pricing remains manual or approximate
- other custom-scope or support-service pricing that must still be quoted per event
- event-scope decisions that the approved sources require to be explicitly listed in the proposal, agreement, or schedule rather than inferred

## Deferred items

The following remain intentionally outside Phase 4 closure:

- Phase 5 guidance such as proposal wording, communication wording, and historical-case examples
- future operational data such as live rental facts, actual invoice state, actual supplier lists, facilitator availability, reservations, and post-event reconciliation records
- future enhancements in [future-enhancements.md](/Users/serinya/Documents/WNC Rental Automation/docs/phase-04/governance/future-enhancements.md), including preferred-supplier ranking and any later curated facilitator catalogue

## Validation status

Final clean validation result:

- `supabase db reset`: passed locally on August 5, 2026
- `supabase test db`: `PASS` on August 5, 2026 with 11 files and 188 tests

## Change process

Future policy changes should follow the existing Phase 4 governance and versioning process rather than editing active rule truth in place:

- immutable rule versioning in [ADR-003](/Users/serinya/Documents/WNC Rental Automation/docs/phase-04/architecture/adr/ADR-003-immutable-rule-versioning.md)
- non-binary outcome handling in [ADR-004](/Users/serinya/Documents/WNC Rental Automation/docs/phase-04/architecture/adr/ADR-004-non-binary-rule-outcomes.md)
- provenance and governance references in the authoritative source map, rule classification register, blocker register, and source manifest

## Closure decision

Phase 4 is `READY_TO_CLOSE`.
