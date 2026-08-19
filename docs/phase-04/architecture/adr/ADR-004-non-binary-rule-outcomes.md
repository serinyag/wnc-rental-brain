# ADR-004: Non-Binary Rule Outcomes

## Status

Accepted.

## Context

WNC rentals are nuanced. Several source areas, especially capacities, supplier handling, approvals, and custom scopes, require more than a yes or no answer when facts are missing or approval is still needed.

## Decision

The rule architecture must support unresolved states such as `insufficient_information`, `requires_confirmation`, and `requires_exception`.

## Consequences

- missing layout does not become guessed capacity
- approval-gated rules can surface as confirmation tasks rather than false certainty
- the structured rule layer stays honest about what it knows

## Rejected Alternative

Force every rule result to resolve to approve or reject.

Why rejected:

- would fabricate certainty
- would misrepresent the source material
- would make later AI or human interpretation less trustworthy
