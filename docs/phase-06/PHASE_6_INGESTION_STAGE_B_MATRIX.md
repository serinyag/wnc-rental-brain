# Phase 6 Ingestion Stage B Matrix

Date: August 7, 2026

## Summary

Stage B loaded the governed historical-corpus content for `HC-001` through `HC-009`:

- governed responsibility statements
- governed historical decisions
- governed lessons, cautions, and analyst inference
- statement-level provenance back to the shared Historical Case Library association
- statement-level historical-value and contamination metadata
- stable Phase 4 logical-rule relationships
- stable Phase 5 knowledge-document relationships

Task `6.3C` then completed the final blocker-resolution pass and activated the corpus.

Final production result:

- all `9` production case versions are `active`
- `HC-003`, `HC-004`, `HC-008`, and `HC-009` are `limited`
- `HC-001`, `HC-002`, `HC-005`, `HC-006`, and `HC-007` remain `active`
- statement totals remain `35` responsibilities, `25` decisions, and `43` lessons
- statement provenance remains complete
- stable current-authority totals remain `30` Phase 4 links and `38` Phase 5 links
- exact Phase 4 links remain `0`
- exact Phase 5 links remain `0`

## Final Per-Case Matrix

| Case | Responsibilities | Decisions | Lessons | Lesson-kind breakdown | Availability | Governance Status | Phase 4 Stable Links | Phase 5 Stable Links | Activation Result |
| --- | ---: | ---: | ---: | --- | --- | --- | ---: | ---: | --- |
| `HC-001` | 3 | 3 | 5 | `curated_lesson` 4, `analyst_inference` 1 | `active` | `active` | 6 | 4 | `ACTIVATED` |
| `HC-002` | 5 | 3 | 5 | `curated_lesson` 4, `analyst_inference` 1 | `active` | `active` | 4 | 4 | `ACTIVATED` |
| `HC-003` | 7 | 3 | 7 | `curated_lesson` 6, `analyst_inference` 1 | `limited` | `active` | 6 | 5 | `ACTIVATED_LIMITED` |
| `HC-004` | 3 | 3 | 5 | `curated_lesson` 3, `caution_warning` 1, `analyst_inference` 1 | `limited` | `active` | 1 | 4 | `ACTIVATED_LIMITED` |
| `HC-005` | 5 | 3 | 4 | `curated_lesson` 4 | `active` | `active` | 4 | 4 | `ACTIVATED` |
| `HC-006` | 4 | 3 | 6 | `curated_lesson` 4, `caution_warning` 1, `analyst_inference` 1 | `active` | `active` | 3 | 5 | `ACTIVATED` |
| `HC-007` | 4 | 3 | 5 | `curated_lesson` 2, `caution_warning` 2, `analyst_inference` 1 | `active` | `active` | 3 | 4 | `ACTIVATED` |
| `HC-008` | 3 | 2 | 3 | `curated_lesson` 2, `analyst_inference` 1 | `limited` | `active` | 0 | 4 | `ACTIVATED_LIMITED` |
| `HC-009` | 1 | 2 | 3 | `caution_warning` 2, `analyst_inference` 1 | `limited` | `active` | 3 | 4 | `ACTIVATED_LIMITED` |

## High-Risk Historical Rows

| Case | Governed statement retained as historical-only | Original disposition at end of Stage B | Final disposition after 6.3C | Final availability |
| --- | --- | --- | --- | --- |
| `HC-001` | External storage was used because onsite space was insufficient. | `potential_conflict_with_current_knowledge` | `potential_conflict_with_current_knowledge` | `active` |
| `HC-002` | WNC removed the decorative rocks and stored them in the courtyard before the event. | `no_current_rule_implication` | `no_current_rule_implication` | `active` |
| `HC-003` | External bike-storage / hallway storage was hired for `EUR 300` for the day. | `potential_conflict_with_current_knowledge` | `potential_conflict_with_current_knowledge` | `limited` |
| `HC-003` | Haylin could provide floral arrangement support where included. | `current_status_unknown` | `current_status_unknown` | `limited` |
| `HC-004` | Upcoming-brand status and gifts or exposure did not automatically justify discounted rental. | `current_status_unknown` | `current_status_unknown` | `limited` |
| `HC-006` | If build-up runs late, additional WNC staffing or overtime should apply. | `current_status_unknown` | `check_phase_5` | `active` |
| `HC-007` | Grace period does not equal setup time, and the historical misuse must not be treated as a current setup allowance. | `check_phase_4` | `check_phase_4` | `active` |
| `HC-007` | Fake snow is not permitted. | `potential_conflict_with_current_knowledge` | `potential_conflict_with_current_knowledge` | `active` |
| `HC-008` | WNC confirmed that unbranded equipment could be used. | `current_status_unknown` | `current_status_unknown` | `limited` |
| `HC-009` | The historical ADE solution is not current legal precedent. | `potential_conflict_with_current_knowledge` | `potential_conflict_with_current_knowledge` | `limited` |

## 6.3C Resolution Audit Trail

### HC-003

- Original blocker:
  `WNC could include floral arrangement support where agreed.`
- Original blocker:
  `Haylin could provide floral arrangement support where included.`
- Final result:
  both statements remain `current_status_unknown`
- Availability change:
  `active` -> `limited`
- Rationale:
  current Phase 4 rules and current Phase 5 governed documents cover venue support, catering, suppliers, and production coordination, but they do not evidence a current governed WNC floral-service capability or a named-person floral promise.

### HC-004

- Original blocker:
  `The client negotiated commercial terms around discount or collaboration.`
- Original blocker:
  `Upcoming-brand status and gifts or exposure did not automatically justify discounted rental.`
- Original blocker:
  `WNC should not discount merely because a brand is new or offers exposure or gifts.`
- Original blocker:
  `Collaboration pricing should have a clear strategic reason.`
- Final result:
  all four statements remain `current_status_unknown`
- Availability change:
  `active` -> `limited`
- Rationale:
  Phase 4 contains no deterministic discount rule, and the linked Phase 5 governed documents do not establish a current discount-or-collaboration policy that safely generalizes the historical commercial judgement.

### HC-006

- Original blocker:
  `If build-up runs late, additional WNC staffing or overtime should apply.`
- Original blocker:
  `Late build-up should not create indefinite WNC onsite obligation.`
- Final result:
  both statements resolved to `check_phase_5`
- Availability change:
  no change; remains `active`
- Current authority relied on:
  `CF-005` / `Full Venue Rental Terms`
- Current authority relied on:
  `TPL-010` / `Final Readiness Checklist`
- Supporting governed context:
  `TPL-007`, `TPL-009`, and `SERV-001`
- Rationale:
  the current governed corpus clearly supports applying written overtime or additional-cost handling and recording those consequences when time runs beyond the agreed boundary, even though historical specifics remain historical.

## Current Authority Connectivity Totals

Per-case stable Phase 4 counts:

- `HC-001`: 6
- `HC-002`: 4
- `HC-003`: 6
- `HC-004`: 1
- `HC-005`: 4
- `HC-006`: 3
- `HC-007`: 3
- `HC-008`: 0
- `HC-009`: 3

Per-case stable Phase 5 counts:

- `HC-001`: 4
- `HC-002`: 4
- `HC-003`: 5
- `HC-004`: 4
- `HC-005`: 4
- `HC-006`: 5
- `HC-007`: 4
- `HC-008`: 4
- `HC-009`: 4

Exact relationship totals remain:

- Phase 4 exact links: `0`
- Phase 5 exact links: `0`

Rationale:

- the corpus still lacks exact historical dates
- exact current-version matching would overstate precision

## Activation State

The Stage B draft boundary is now historical only.

Current production state:

- `version_number = 1` for all nine cases
- `governance_status = 'active'` for all nine cases
- `activated_at` populated for all nine cases
- no `draft`, `superseded`, or `retired` production case versions

## Deferred Scope

Still deferred beyond `6.3C`:

- historical retrieval units
- chunking of historical corpus content
- historical embeddings
- retrieval APIs or FTS surfaces for historical cases
- answer generation or RAG
