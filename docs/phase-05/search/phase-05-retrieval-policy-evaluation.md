# Phase 5 Retrieval Policy Evaluation

Date: August 7, 2026

## Evaluation Mode

- mode: `report`
- retrieval evidence source: approved Phase 5 FTS + semantic comparison results
- evaluation fixture count: `13`

## Candidate Strategies

- `fts_first_append_semantic`: FTS-first Append Semantic
- `semantic_first_append_fts`: Semantic-first Append FTS
- `rrf_unweighted`: RRF Unweighted
- `rrf_policy_weighted`: RRF With Governed Policy Modifiers

## Baseline Substrates

| Retrieval Layer | Hit@1 | Hit@3 | Preferred Before Secondary | Relevant@5 |
| --- | ---: | ---: | ---: | ---: |
| FTS | 9/13 | 11/13 | 10/13 | 0.508 |
| Semantic | 11/13 | 13/13 | 11/13 | 0.723 |

## Metrics

| Policy | Hit@1 | Hit@3 | Preferred Before Secondary | Relevant@5 |
| --- | ---: | ---: | ---: | ---: |
| FTS-first Append Semantic | 10/13 | 13/13 | 11/13 | 0.662 |
| Semantic-first Append FTS | 11/13 | 13/13 | 11/13 | 0.723 |
| RRF Unweighted | 11/13 | 13/13 | 11/13 | 0.708 |
| RRF With Governed Policy Modifiers | 13/13 | 13/13 | 13/13 | 0.692 |

## Known Cases

### `payment within 14 days`

- fixture note: Operational payment sources should rank above governance history while keeping governance visible.
- FTS: top `GOV-002` / `DEC-007 — Confirmation payment for bookings within 14 days` status `acceptable` | preferred in top 3: `True`
- Semantic: top `CF-003` / `4.1 Short-Notice Bookings` status `preferred` | preferred in top 3: `True`
- FTS-first Append Semantic: top `GOV-002` / `DEC-007 — Confirmation payment for bookings within 14 days` status `acceptable` | preferred in top 3: `True`
- Semantic-first Append FTS: top `CF-003` / `4.1 Short-Notice Bookings` status `preferred` | preferred in top 3: `True`
- RRF Unweighted: top `GOV-002` / `DEC-007 — Confirmation payment for bookings within 14 days` status `acceptable` | preferred in top 3: `True`
- RRF With Governed Policy Modifiers: top `CF-003` / `4.1 Short-Notice Bookings` status `preferred` | preferred in top 3: `True`

### `can we bring our own catering`

- fixture note: Explicit external-catering guidance should outrank adjacent kitchen or general supplier clauses.
- FTS: top `SERV-003` / `CBR-002 — External caterers` status `preferred` | preferred in top 3: `True`
- Semantic: top `SERV-003` / `CBR-001 — Kitchen suitability` status `irrelevant` | preferred in top 3: `True`
- FTS-first Append Semantic: top `SERV-003` / `CBR-002 — External caterers` status `preferred` | preferred in top 3: `True`
- Semantic-first Append FTS: top `SERV-003` / `CBR-001 — Kitchen suitability` status `irrelevant` | preferred in top 3: `True`
- RRF Unweighted: top `SERV-003` / `CBR-002 — External caterers` status `preferred` | preferred in top 3: `True`
- RRF With Governed Policy Modifiers: top `SERV-003` / `CBR-002 — External caterers` status `preferred` | preferred in top 3: `True`

### `can we visit the venue beforehand`

- fixture note: Specific site-visit guidance should outrank broader access clauses for this procedural paraphrase.
- FTS: top `None` / `None` status `none` | preferred in top 3: `False`
- Semantic: top `CF-005` / `11.1 Venue Access & Early Entry` status `acceptable` | preferred in top 3: `True`
- FTS-first Append Semantic: top `CF-005` / `11.1 Venue Access & Early Entry` status `acceptable` | preferred in top 3: `True`
- Semantic-first Append FTS: top `CF-005` / `11.1 Venue Access & Early Entry` status `acceptable` | preferred in top 3: `True`
- RRF Unweighted: top `CF-005` / `11.1 Venue Access & Early Entry` status `acceptable` | preferred in top 3: `True`
- RRF With Governed Policy Modifiers: top `TPL-008` / `People & spaces` status `preferred` | preferred in top 3: `True`

### `security deposit`

- fixture note: Direct client-facing deposit clauses should outrank governance summaries.
- FTS: top `CF-007` / `Security deposit and inspection` status `preferred` | preferred in top 3: `True`
- Semantic: top `CF-003` / `5. Security Deposit` status `preferred` | preferred in top 3: `True`
- FTS-first Append Semantic: top `CF-007` / `Security deposit and inspection` status `preferred` | preferred in top 3: `True`
- Semantic-first Append FTS: top `CF-003` / `5. Security Deposit` status `preferred` | preferred in top 3: `True`
- RRF Unweighted: top `CF-007` / `Security deposit and inspection` status `preferred` | preferred in top 3: `True`
- RRF With Governed Policy Modifiers: top `CF-007` / `Security deposit and inspection` status `preferred` | preferred in top 3: `True`

## Recommendation

- recommended policy: `RRF With Governed Policy Modifiers`
- policy code: `rrf_policy_weighted`

## Diagnostic Query Snapshots

### `payment within 14 days`

- FTS:
  - `1` `GOV-002` | section `DEC-007 — Confirmation payment for bookings within 14 days` | rank `0.910212`
  - `2` `CF-007` | section `7. Fees, payment and security deposit` | rank `0.161765`
  - `3` `CF-003` | section `4.1 Short-Notice Bookings` | rank `0.021189`
- Semantic:
  - `1` `CF-003` | section `4.1 Short-Notice Bookings` | similarity `0.516640`
  - `2` `GOV-002` | section `DEC-007 — Confirmation payment for bookings within 14 days` | similarity `0.478026`
  - `3` `CF-003` | section `4.3 Payments via Storefront (If Applicable)` | similarity `0.407983`
- FTS-first Append Semantic:
  - `1` `GOV-002` | section `DEC-007 — Confirmation payment for bookings within 14 days` | rank `0.910212`
  - `2` `CF-007` | section `7. Fees, payment and security deposit` | rank `0.161765`
  - `3` `CF-003` | section `4.1 Short-Notice Bookings` | rank `0.021189`
- Semantic-first Append FTS:
  - `1` `CF-003` | section `4.1 Short-Notice Bookings` | similarity `0.516640`
  - `2` `GOV-002` | section `DEC-007 — Confirmation payment for bookings within 14 days` | similarity `0.478026`
  - `3` `CF-003` | section `4.3 Payments via Storefront (If Applicable)` | similarity `0.407983`
- RRF Unweighted:
  - `1` `GOV-002` | section `DEC-007 — Confirmation payment for bookings within 14 days` | policy_score `0.093074`
  - `2` `CF-003` | section `4.1 Short-Notice Bookings` | policy_score `0.091097`
  - `3` `CF-007` | section `7. Fees, payment and security deposit` | policy_score `0.085455`
- RRF With Governed Policy Modifiers:
  - `1` `CF-003` | section `4.1 Short-Notice Bookings` | policy_score `0.101097`
  - `2` `CF-007` | section `7. Fees, payment and security deposit` | policy_score `0.095455`
  - `3` `GOV-002` | section `DEC-007 — Confirmation payment for bookings within 14 days` | policy_score `0.073074`

### `when does the remaining balance need to be paid`

- FTS:
  - none
- Semantic:
  - `1` `TPL-006` | section `Balance Payment Reminder` | similarity `0.502311`
  - `2` `GOV-002` | section `DEC-005 — Remaining balance deadline` | similarity `0.475429`
  - `3` `CF-007` | section `Payment plan` | similarity `0.422521`
- FTS-first Append Semantic:
  - `1` `TPL-006` | section `Balance Payment Reminder` | similarity `0.502311`
  - `2` `GOV-002` | section `DEC-005 — Remaining balance deadline` | similarity `0.475429`
  - `3` `CF-007` | section `Payment plan` | similarity `0.422521`
- Semantic-first Append FTS:
  - `1` `TPL-006` | section `Balance Payment Reminder` | similarity `0.502311`
  - `2` `GOV-002` | section `DEC-005 — Remaining balance deadline` | similarity `0.475429`
  - `3` `CF-007` | section `Payment plan` | similarity `0.422521`
- RRF Unweighted:
  - `1` `TPL-006` | section `Balance Payment Reminder` | policy_score `0.047619`
  - `2` `GOV-002` | section `DEC-005 — Remaining balance deadline` | policy_score `0.045455`
  - `3` `CF-007` | section `Payment plan` | policy_score `0.043478`
- RRF With Governed Policy Modifiers:
  - `1` `TPL-006` | section `Balance Payment Reminder` | policy_score `0.056619`
  - `2` `TPL-013` | section `Final notes` | policy_score `0.052667`
  - `3` `CF-007` | section `Payment plan` | policy_score `0.048478`

### `can we visit the venue beforehand`

- FTS:
  - none
- Semantic:
  - `1` `CF-005` | section `11.1 Venue Access & Early Entry` | similarity `0.506787`
  - `2` `CF-005` | section `11. Appointment-Only Access to the Venue` | similarity `0.500440`
  - `3` `TPL-008` | section `People & spaces` | similarity `0.487022`
- FTS-first Append Semantic:
  - `1` `CF-005` | section `11.1 Venue Access & Early Entry` | similarity `0.506787`
  - `2` `CF-005` | section `11. Appointment-Only Access to the Venue` | similarity `0.500440`
  - `3` `TPL-008` | section `People & spaces` | similarity `0.487022`
- Semantic-first Append FTS:
  - `1` `CF-005` | section `11.1 Venue Access & Early Entry` | similarity `0.506787`
  - `2` `CF-005` | section `11. Appointment-Only Access to the Venue` | similarity `0.500440`
  - `3` `TPL-008` | section `People & spaces` | similarity `0.487022`
- RRF Unweighted:
  - `1` `CF-005` | section `11.1 Venue Access & Early Entry` | policy_score `0.047619`
  - `2` `CF-005` | section `11. Appointment-Only Access to the Venue` | policy_score `0.045455`
  - `3` `TPL-008` | section `People & spaces` | policy_score `0.043478`
- RRF With Governed Policy Modifiers:
  - `1` `TPL-008` | section `People & spaces` | policy_score `0.054478`
  - `2` `TPL-008` | section `2. Site visit — if applicable` | policy_score `0.052667`
  - `3` `CF-005` | section `11.1 Venue Access & Early Entry` | policy_score `0.052619`

