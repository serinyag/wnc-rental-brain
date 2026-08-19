# Acceptance Criteria

The current Phase 4 slice is acceptable when all of the following are true:

1. Every current authoritative rule domain used in the design has a traceable primary source and any relevant supporting or governance sources.
2. Canonical terminology and machine values match the WNC Rental Data Dictionary where Phase 4 uses those concepts.
3. Important rule values are modeled as typed relational data in the target architecture, not assumed to live in generic JSON.
4. The rule-governance model preserves historical versions instead of overwriting old rule values in place.
5. The architecture explicitly supports unresolved outcomes such as `insufficient_information`, `requires_confirmation`, and `requires_exception`.
6. Missing input facts do not force guessed feasibility conclusions.
7. Historical cases, proposal templates, and email examples are excluded from authoritative rule activation.
8. Open decisions and `TBC` governance fields are documented and not silently promoted to active policy.
9. The local development database can be rebuilt entirely from migrations and seed data.
10. No production-only manual schema state is required for the implemented schema.
11. The repository contains an explicit Supabase development workflow and change-management path.
12. Foundation tests cover duplicate rule versions, invalid date ranges, self-supersession, and provenance integrity.
13. Booking fee retrieval is deterministic for supported rental types and supported duration bands, and returns no guessed result outside those bands.
14. Payment-rule retrieval preserves stage-specific multiplicity, suppresses contingent rules when required context is missing, prevents `0-14 day` confirmations from returning the `upfront_30` path, and stores relative timing policy rather than live rental due dates.
15. Expedited-surcharge retrieval derives `applies`, `does_not_apply`, and `insufficient_information` from calendar lead time, stores the approved 10% venue-rental-only basis and 21% VAT policy, and treats waiver as an explicit future exception rather than an automatic outcome.
16. Cancellation retrieval can return multiple category-specific consequences for one cancellation scenario, uses the shared calendar lead-time helper for `31+` versus `0-30` day client-cancellation boundaries, and preserves manual-review outcomes for non-recoverable committed costs and valid deduction checks.
17. Capacity retrieval remains configuration-aware, distinguishes whole-venue legal maximum from layout-specific operational maxima, returns `insufficient_information` when required configuration is missing, and exposes `requires_confirmation` or `not_event_capacity_space` instead of inventing numeric capacities.
18. The implementation stops after the current narrow typed-rule slices and does not drift into full rule population or later-phase application code.
