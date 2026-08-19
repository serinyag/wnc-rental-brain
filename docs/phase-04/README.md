# Phase 4 Foundation, Commercial Rules, Space Access, And Operational Requirements

This directory holds the Phase 4 source analysis, architecture, governance, implementation, and validation materials for the structured rental rule catalogue.

## Subdirectories

- `requirements/`: scope, acceptance criteria, source authority map, and rule classification register
- `architecture/`: schema boundaries, ERD, table specifications, and ADRs
- `governance/`: source manifest, rule-code conventions, workflow, and change-management guidance
- `validation/`: database validation approach and scenario planning for current and future rule slices

## Current Implemented Slices

The shared rule-governance foundation is implemented, and the current typed rule domains are `booking_fee_rules`, `payment_rules`, `expedited_surcharge_rules`, `cancellation_rules`, `capacity_rules`, `space_access_rules`, `operational_requirements`, `catering_supplier_rules`, `technical_capability_rules`, `service_rules`, and `facilitator_requirement_rules`. Other commercial and operational domains remain outside the active schema until their source conflicts or policy gaps are resolved.

## Working Principle

Phase 4 structures fixed WNC rental policy consequences. It does not automate full rental feasibility decisions. Where required facts are missing, the system must preserve uncertainty instead of guessing.
