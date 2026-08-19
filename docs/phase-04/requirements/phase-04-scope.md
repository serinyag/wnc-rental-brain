# Phase 4 Scope

## Objective

Create the repository and database foundation required to represent approved WNC rental policy as source-traceable, versioned, relational data in Supabase, and prove that design with narrow booking-fee, payment, expedited-surcharge, cancellation, capacity, space-access, operational-requirement, catering-supplier, technical-capability, and service-facilitator slices.

## In Scope

- preserve all supplied Phase 1-3 source files under `sources/phase-01-03/`
- inventory every supplied source and document its authority, status, and Phase 4 relevance
- preserve canonical terminology and machine values from the WNC Rental Data Dictionary
- define PostgreSQL schema boundaries for `public`, `api`, and `private`
- design a rule-governance model with versioning and provenance
- create foundation migrations for canonical entities and rule governance
- seed only clearly approved canonical entities
- implement narrow typed rule domains with source-backed retrieval and tests
- create invariant database tests
- document the architecture, workflow, and validation approach

## Out Of Scope

- populating all Phase 4 rule domains
- building a Next.js application or any frontend
- AI, LLM, embeddings, chunking, or retrieval systems
- email ingestion, intake forms, or autonomous workflows
- historical-case retrieval or proposal generation
- live rental, contact, organization, or calendar state
- production database connection or mutation

## Assumptions

- editable masters outrank their exported PDFs when wording drifts, because the Knowledge Inventory states that editable masters control exports
- historical cases, proposal templates, checklists, and email templates are useful supporting material but are not authoritative policy sources
- open decisions and `TBC` governance fields must not be silently converted into active deterministic rules
- the pricing workbook pair contains unresolved drift overall, but the booking-fee and direct-rental payment rows align across the supplied workbook variants and can be loaded as narrow exceptions

## Dependencies

- Docker and a working local Supabase runtime
- controlled Phase 1-3 source documents
- human review of unresolved policy conflicts and open decisions
- future policy owners for currently role-based governance fields

## Definition Of Done

This repository slice is done when:

- the source files are preserved in-repo
- the source manifest and source authority map are complete
- the rule-classification register is drafted
- the ERD, schema boundaries, table specifications, and ADRs are written
- the Supabase project is initialized
- foundation migrations can rebuild the local database from scratch
- conservative seed data loads successfully
- the booking-fee, payment, expedited-surcharge, cancellation, capacity, space-access, operational-requirement, catering-supplier, technical-capability, and service-facilitator slices load successfully with provenance
- invariant, booking-fee, payment, expedited-surcharge, cancellation, capacity, space-access, operational-requirement, catering-supplier, technical-capability, and service-facilitator database tests run
- unresolved policy remains explicitly documented for review
