# Phase 5 Hybrid Retrieval Evaluation

Date: August 9, 2026

## Approved Policy Specification

- retrieval policy: `rrf_policy_weighted`
- RRF parameter: `k = 20`
- final result limit: `5`
- per-substrate candidate depth: `10`
- governed category modifiers:
  - `operational_procedure`: `+0.011`
  - `communication_guidance`: `+0.009`
  - `service_supplier_guidance`: `+0.007`
  - `technical_venue_reference`: `+0.007`
  - `client_facing_controlled_document`: `+0.005`
  - `proposal_guidance`: `+0.001`
  - `governance_canonical`: `-0.010`

## Eligible Corpus

- current eligible documents: `21`
- current eligible chunks: `492`
- current approved embeddings: `492`
- embedding coverage: `100.0`%

## Original 13-Query Fixture Metrics

| Retrieval Layer | Hit@1 | Hit@3 | Preferred Before Secondary | Relevant@5 |
| --- | ---: | ---: | ---: | ---: |
| FTS | 9/13 | 11/13 | 10/13 | 0.508 |
| Semantic | 11/13 | 13/13 | 11/13 | 0.723 |
| Hybrid | 13/13 | 13/13 | 13/13 | 0.662 |

## Holdout Metrics

| Retrieval Layer | Hit@1 | Hit@3 | Preferred Before Secondary | Relevant@5 |
| --- | ---: | ---: | ---: | ---: |
| FTS | 1/4 | 1/4 | 1/4 | 0.100 |
| Semantic | 2/4 | 4/4 | 4/4 | 0.400 |
| Hybrid | 2/4 | 4/4 | 4/4 | 0.350 |

## Diagnostic Query Results

### `payment within 14 days`

- fixture note: Operational payment sources should rank above governance history while keeping governance visible.
- FTS:
  - `1` `GOV-002` | section `DEC-007 — Confirmation payment for bookings within 14 days` | rank `0.910212`
  - `2` `CF-007` | section `7. Fees, payment and security deposit` | rank `0.161765`
  - `3` `CF-003` | section `4.1 Short-Notice Bookings` | rank `0.021189`
- Semantic:
  - `1` `CF-003` | section `4.1 Short-Notice Bookings` | similarity `0.516640`
  - `2` `GOV-002` | section `DEC-007 — Confirmation payment for bookings within 14 days` | similarity `0.478026`
  - `3` `CF-003` | section `4.3 Payments via Storefront (If Applicable)` | similarity `0.407983`
- Hybrid:
  - `1` `CF-003` | section `4.1 Short-Notice Bookings` | final_score `0.096097`
  - `2` `CF-007` | section `7. Fees, payment and security deposit` | final_score `0.090455`
  - `3` `CF-005` | section `2. Payment Terms` | final_score `0.083704`

### `can we bring our own catering`

- fixture note: Explicit external-catering guidance should outrank adjacent kitchen or general supplier clauses.
- FTS:
  - `1` `SERV-003` | section `CBR-002 — External caterers` | rank `0.058333`
  - `2` `TPL-006` | section `External Supplier Information Request` | rank `0.035897`
  - `3` `SERV-003` | section `CBR-010 — Sparkling water` | rank `0.005517`
- Semantic:
  - `1` `SERV-003` | section `CBR-001 — Kitchen suitability` | similarity `0.464896`
  - `2` `CF-007` | section `Catering, suppliers and facilitators` | similarity `0.453884`
  - `3` `SERV-004` | section `SUP-TPL-001 — External caterer: TEMPLATE` | similarity `0.451031`
- Hybrid:
  - `1` `SERV-003` | section `CBR-002 — External caterers` | final_score `0.094619`
  - `2` `SERV-003` | section `CBR-001 — Kitchen suitability` | final_score `0.054619`
  - `3` `TPL-006` | section `External Supplier Information Request` | final_score `0.054455`

### `can we visit the venue beforehand`

- fixture note: Specific site-visit guidance should outrank broader access clauses for this procedural paraphrase.
- FTS:
  - none
- Semantic:
  - `1` `CF-005` | section `11.1 Venue Access & Early Entry` | similarity `0.504979`
  - `2` `CF-005` | section `11. Appointment-Only Access to the Venue` | similarity `0.500440`
  - `3` `TPL-008` | section `People & spaces` | similarity `0.487043`
- Hybrid:
  - `1` `TPL-008` | section `People & spaces` | final_score `0.054478`
  - `2` `TPL-008` | section `2. Site visit — if applicable` | final_score `0.052667`
  - `3` `CF-005` | section `11.1 Venue Access & Early Entry` | final_score `0.052619`

### `security deposit`

- fixture note: Direct client-facing deposit clauses should outrank governance summaries.
- FTS:
  - `1` `CF-007` | section `Security deposit and inspection` | rank `1.820000`
  - `2` `GOV-002` | section `DEC-024 — Security-deposit refund deductions` | rank `1.624450`
  - `3` `GOV-002` | section `DEC-030 — Security deposit: studio` | rank `1.570000`
- Semantic:
  - `1` `CF-003` | section `5. Security Deposit` | similarity `0.521751`
  - `2` `CF-007` | section `Security deposit and inspection` | similarity `0.492007`
  - `3` `CF-005` | section `3. Security Deposit` | similarity `0.486266`
- Hybrid:
  - `1` `CF-007` | section `Security deposit and inspection` | final_score `0.098074`
  - `2` `CF-003` | section `5. Security Deposit` | final_score `0.087102`
  - `3` `CF-007` | section `7. Fees, payment and security deposit` | final_score `0.082037`

### `when does the remaining balance need to be paid`

- fixture note: Paraphrase retrieval should recover direct operational balance guidance.
- FTS:
  - none
- Semantic:
  - `1` `TPL-006` | section `Balance Payment Reminder` | similarity `0.502311`
  - `2` `GOV-002` | section `DEC-005 — Remaining balance deadline` | similarity `0.475429`
  - `3` `CF-007` | section `Payment plan` | similarity `0.422521`
- Hybrid:
  - `1` `TPL-006` | section `Balance Payment Reminder` | final_score `0.056619`
  - `2` `TPL-013` | section `Final notes` | final_score `0.052667`
  - `3` `CF-007` | section `Payment plan` | final_score `0.048478`

## Holdout Query Results

### `venue walkthrough before the event`

- fixture note: Operational site-visit guidance should still beat generic access language on a new paraphrase.
- FTS:
  - `1` `CF-005` | section `11.1 Venue Access & Early Entry` | rank `0.002703`
  - `2` `CF-005` | section `C. Ice Bath Room usage` | rank `0.001887`
- Semantic:
  - `1` `TPL-009` | section `3. Space & Set-Up` | similarity `0.490221`
  - `2` `TPL-008` | section `2. Site visit — if applicable` | similarity `0.481191`
  - `3` `TPL-007` | section `1. Discovery: understand the event` | similarity `0.478115`
- Hybrid:
  - `1` `TPL-009` | section `3. Space & Set-Up` | final_score `0.058619`
  - `2` `TPL-008` | section `2. Site visit — if applicable` | final_score `0.056455`
  - `3` `TPL-007` | section `1. Discovery: understand the event` | final_score `0.054478`

### `outside supplier details`

- fixture note: Supplier-information phrasing should recover the operational request template rather than only adjacent supplier context.
- FTS:
  - `1` `CF-005` | section `14. Event Production & Coordination (When Applicable)` | rank `0.000690`
- Semantic:
  - `1` `SERV-004` | section `External supplier requirements overview` | similarity `0.557839`
  - `2` `SERV-004` | section `SUP-TPL-003 — Technical supplier: TEMPLATE` | similarity `0.534014`
  - `3` `TPL-006` | section `External Supplier Information Request` | similarity `0.524268`
- Hybrid:
  - `1` `SERV-004` | section `External supplier requirements overview` | final_score `0.054619`
  - `2` `CF-005` | section `14. Event Production & Coordination (When Applicable)` | final_score `0.052619`
  - `3` `TPL-006` | section `External Supplier Information Request` | final_score `0.052478`

### `event manager support`

- fixture note: A held-out service query should remain strongly anchored to the service catalogue.
- FTS:
  - `1` `GOV-001` | section `SERV-001 — WNC Rental Services Catalogue` | rank `0.137241`
  - `2` `GOV-002` | section `DEC-048 — Host support during venue clearing` | rank `0.040476`
  - `3` `SERV-001` | section `On-Site Host` | rank `0.026132`
- Semantic:
  - `1` `SERV-001` | section `Event Manager` | similarity `0.497742`
  - `2` `TPL-003` | section `1. Event Overview` | similarity `0.419159`
  - `3` `TPL-009` | section `1. Event Snapshot` | similarity `0.409863`
- Hybrid:
  - `1` `SERV-001` | section `Event Manager` | final_score `0.054619`
  - `2` `TPL-009` | section `1. Event Snapshot` | final_score `0.054478`
  - `3` `TPL-009` | section `4. People & Services` | final_score `0.051000`

### `balance payment reminder`

- fixture note: Held-out payment phrasing should preserve the template-first ordering for direct reminder language.
- FTS:
  - `1` `TPL-006` | section `Balance Payment Reminder` | rank `2.293060`
- Semantic:
  - `1` `TPL-006` | section `Balance Payment Reminder` | similarity `0.619616`
  - `2` `CF-007` | section `Payment plan` | similarity `0.419122`
  - `3` `GOV-002` | section `DEC-005 — Remaining balance deadline` | similarity `0.381782`
- Hybrid:
  - `1` `TPL-006` | section `Balance Payment Reminder` | final_score `0.104238`
  - `2` `TPL-006` | section `Deposit / Confirmation Payment Request` | final_score `0.050667`
  - `3` `CF-007` | section `Payment plan` | final_score `0.050455`

## Performance Observations

- original-fixture average query embedding time: `306.0` ms
- original-fixture average FTS retrieval time: `154.87` ms
- original-fixture average semantic retrieval time: `234.2` ms
- original-fixture average hybrid retrieval time: `172.14` ms
- holdout average query embedding time: `250.8` ms
- holdout average FTS retrieval time: `189.91` ms
- holdout average semantic retrieval time: `268.66` ms
- holdout average hybrid retrieval time: `205.74` ms

## Known Residual Quirks

- `when does the remaining balance need to be paid` should keep the correct primary result. Secondary ordering may still place `TPL-013` above `CF-007`, which remains the approved non-blocking quirk from 5.6A.
- The hybrid surface degrades predictably to FTS-only for a given query if no query embedding is supplied, while still keeping category modifiers and current-governance eligibility intact.
- Missing chunk embeddings do not remove eligible chunks from FTS retrieval because semantic ranking is additive rather than a mandatory eligibility gate.

