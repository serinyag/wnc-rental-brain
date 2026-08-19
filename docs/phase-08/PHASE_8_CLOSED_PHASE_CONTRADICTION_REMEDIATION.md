# Phase 8 Closed-Phase Contradiction Remediation

Date:

- August 9, 2026

Contradiction ID:

- `CLOSED_PHASE_CONTRADICTION-001`

Final status:

- `REMEDIATED`

## Contradiction

Phase 8.0A identified stale entire-venue grace-period wording in the editable full-venue terms.

Reported drift:

- editable full-venue terms still used `15-minute` entire-venue grace wording
- closed Phase 4 current rule already established `30 minutes` for entire-venue grace

## Affected Source

- `sources/phase-01-03/Client Facing Docs/Full Venue _ Rental Terms and Conditions.docx`

Affected stale wording confirmed before remediation:

- `5. Overtime Charges`
  - `If our staff need to stay beyond the 15-minute grace period ...`
- `11.1 Venue Access & Early Entry`
  - `15-minute arrival window`
  - `... may arrive up to 15 minutes before the official start time ...`

## Frozen Current Rule

Already-frozen current authority confirmed:

- `docs/phase-04/requirements/operational-requirements.md`
- `supabase/seed.sql`
- `sources/phase-01-03/Client Facing Docs/WNC Rental Agreement Template.docx`
- `sources/phase-01-03/Venue & Operations/WNC Venue Rental Operations Manual.docx`

Confirmed rule:

- entire-venue rentals use `30 minutes` before and `30 minutes` after for arrival/departure grace
- grace does not permit setup, unloading, or other operational work

## Why This Was Drift, Not Policy Redesign

- the current authoritative baseline was already frozen in Phase 4
- the agreement template and operations manual already aligned to `30 minutes`
- the stale wording existed only in the editable full-venue terms
- no evidence showed a new human decision to revert entire-venue grace to `15 minutes`

Therefore this was a governed-source correction, not a Phase 4 policy redesign.

## Exact Correction

Only the stale entire-venue wording was changed in the editable master:

- `15-minute grace period` -> `30-minute grace period`
- `15-minute arrival window` -> `30-minute arrival window`
- `arrive up to 15 minutes before` -> `arrive up to 30 minutes before`

Intentionally preserved:

- `15-minute` overtime billing increments
- studio-specific `15-minute` grace behavior in the correct studio sources

## Phase 5 Corpus Impact

`CF-005` participates in the active Phase 5 current corpus.

Therefore remediation required:

- current corpus re-chunking refresh
- embedding refresh for changed current chunks
- retrieval-state validation

## Re-Ingestion / Update Actions

Executed:

1. `python3 -m unittest tools.phase_05_chunking.tests.test_chunking -v`
2. `python3 -m unittest tools.phase_05_chunking.tests.test_bulk_chunking -v`
3. `python3 -m tools.phase_05_chunking.generate_bulk --load-db`
4. `python3 -m tools.phase_05_search.generate_embeddings`
5. `python3 -m tools.phase_05_search.generate_embeddings`
6. `python3 -m tools.phase_05_search.evaluate_hybrid`
7. `python3 -m unittest discover -s tools/phase_05_search/tests -v`
8. `npx -y supabase@latest test db --local`

Observed live corpus state after refresh:

- bulk current chunk sets: `22`
- bulk generated chunks: `525`
- current eligible documents: `21`
- current eligible chunks: `492`
- current approved embeddings: `492`
- embedding coverage: `100.0%`
- `CF-005` current chunk count after refresh: `31`

## Loader / Validation Remediation Required During Refresh

The governed-source correction exposed a real rerun-path issue in the chunk loader:

- `tools/phase_05_chunking/generate_pilot.py` reused a prior `last_succeeded_at` while setting a new later `last_attempted_at`
- this violated `knowledge_document_version_processing_success_after_attempt` during reprocessing of an already-succeeded document version

Controlled remediation applied:

- clear `last_succeeded_at` when moving a document version back to `in_progress`
- clear `last_succeeded_at` on loader failure upsert
- add a focused regression test in `tools/phase_05_chunking/tests/test_bulk_chunking.py`

The refreshed corpus then loaded successfully.

The re-ingestion also exposed one audit-test assumption that counted historical primary extraction rows instead of current ones.

Controlled validation correction applied:

- `supabase/tests/18_phase_05_bulk_chunking_coverage.sql` now scopes the primary-extraction count to `current` chunk sets, matching the test’s stated intent

## Validation Outcome

Focused validation passed:

- Phase 5 chunking tests: `24 / 24` passing across the two targeted files
- Phase 5 search tests: `24 / 24` passing
- hybrid retrieval evaluation regenerated successfully
- Supabase DB regression: `33` files, `937` assertions, `PASS`

Hybrid evaluation snapshot after refresh:

- eligible corpus: `21` documents / `492` chunks
- embeddings: `492 / 492`
- fixture hybrid `Hit@1`: `13 / 13`
- holdout hybrid `Hit@3`: `4 / 4`

## Closure

`CLOSED_PHASE_CONTRADICTION-001` is closed as:

- `REMEDIATED`

Reason:

- stale editable-source drift was corrected
- Phase 4 rule truth was not changed
- Phase 5 corpus was refreshed to reflect the correction
- focused retrieval and DB validation passed after refresh
