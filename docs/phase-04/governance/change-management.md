# Change Management

## Principle

Supabase must never become the undocumented place where policy is invented.

## Target Policy Change Flow

```text
Policy decision
↓
WNC Rental Policy Decisions & Change Log updated
↓
Authoritative human source updated
↓
New structured rule version created
↓
Database reset and tests run
↓
Review
↓
Migration / release
```

## Required Inputs Before A Rule Change

- the decision exists in a controlled source or is explicitly approved for entry there
- the rule owner or accountable role is known
- effective timing is either known or explicitly still `not specified`
- any affected client-facing or internal documents are identified

## Required Outputs After A Rule Change

- new rule version row instead of in-place overwrite
- updated provenance links
- updated tests if a new invariant was introduced
- updated documentation if the architecture or domain coverage changed

## What Must Trigger Human Review

- unresolved conflicts between controlled sources
- new canonical machine values
- waiver logic that still depends on open management criteria
- any change that affects VAT, payment, cancellation, liability, capacity, or legal terms
- any rule that still contains `TBC`, `manual decision`, or open approval language
