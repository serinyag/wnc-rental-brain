# ADR-003: Immutable Rule Versioning

## Status

Accepted.

## Context

The brief requires historical querying and explicitly forbids ordinary in-place overwrites of policy. The source set also contains unresolved and evolving policy, so auditability matters.

## Decision

Rule changes create new rule versions under the same `rule_code`. Historical rows remain preserved.

## Consequences

- past policy can be reconstructed
- source provenance stays aligned to the specific rule version
- future releases can activate a new version without destroying the old one

## Rejected Alternative

Update the existing rule row in place.

Why rejected:

- destroys history
- weakens auditability
- makes source conflicts harder to investigate later
