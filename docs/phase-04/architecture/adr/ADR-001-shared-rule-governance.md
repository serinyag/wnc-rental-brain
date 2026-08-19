# ADR-001: Shared Rule Governance Model

## Status

Accepted for the Phase 4 foundation.

## Context

Phase 4 needs stable rule identity, versioning, lifecycle status, and provenance before it loads typed business-rule values. The source set also shows that a single rule can be supported by multiple documents and can change over time without changing its logical meaning.

## Decision

Create a shared `rule_catalogue` table for lifecycle and version governance, separate from typed rule-value tables.

## Consequences

- every logical rule gets a stable `rule_code`
- versioning, effective dates, and supersession stay consistent across domains
- provenance links do not need to be re-designed for each typed table
- typed rule tables stay focused on domain values, not governance metadata

## Rejected Alternative

Store governance columns independently in every typed rule table.

Why rejected:

- duplicates versioning behavior across domains
- increases drift risk
- complicates source linking and audit queries
