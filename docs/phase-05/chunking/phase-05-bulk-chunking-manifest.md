# Phase 5 Bulk Chunking Manifest

Date: August 6, 2026

Status gate: `PHASE_5_5.3C_CORPUS_COVERAGE_REVIEW_REQUIRED`

## Summary

Task 5.3C bulk-generated deterministic semantic chunks for every currently eligible and safely extractable governed document version in the Phase 5 corpus, while preserving the approved `OPS-001` pilot output and explicitly leaving the two intentional non-generation cases unchunked.

Final current-corpus totals after the successful load and identical rerun:

- current chunk sets: `22`
- superseded chunk sets: `0`
- current chunks: `525`
- current chunk provenance traces: `525`
- processing rows: `24`
- processing rows with `succeeded`: `22`
- processing rows with `not_applicable`: `2`
- active included documents: `22`
- active included documents chunked: `21`
- active included documents intentionally unchunked: `1`
- preserved draft pilot chunked: `1`
- stable chunk-rule links: `10`
- linked current chunks: `9`
- exact chunk-rule links: `0`

Current parser versions in use:

- `CF-003` -> `docx_heading_outline_v1`
- `CF-005` -> `docx_heading_outline_v1`
- `CF-007` -> `docx_heading_outline_with_tables_v1`
- `GOV-001` -> `xlsx_governance_inventory_v1`
- `GOV-002` -> `xlsx_policy_decision_log_v1`
- `OPS-001` -> `docx_heading_outline_v1`
- `OPS-002` -> `xlsx_technical_inventory_v1`
- `OPS-003` -> `xlsx_capacity_space_rules_v1`
- `SERV-001` -> `xlsx_service_catalogue_v2`
- `SERV-003` -> `xlsx_catering_supplier_catalogue_v1`
- `SERV-004` -> `xlsx_external_supplier_requirements_v1`
- `TPL-001` -> `docx_numbered_template_sections_v1`
- `TPL-002` -> `docx_numbered_template_sections_v1`
- `TPL-003` -> `docx_numbered_template_sections_v1`
- `TPL-004` -> `docx_numbered_template_sections_v1`
- `TPL-005` -> `docx_numbered_template_sections_v1`
- `TPL-006` -> `docx_template_library_v2`
- `TPL-007` -> `docx_checklist_sections_v1`
- `TPL-008` -> `docx_numbered_checklist_sections_v1`
- `TPL-009` -> `docx_numbered_checklist_sections_v1`
- `TPL-010` -> `docx_numbered_checklist_sections_v1`
- `TPL-013` -> `docx_linear_checklist_sections_v1`

## Current Corpus Inventory

| Code | Status | Current chunk set | Parser version | Chunks | Processing | Logical links | Exact links |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `CF-001` | intentionally unchunked | `none` | `none` | `0` | `not_applicable` | `0` | `0` |
| `CF-003` | current | `30` | `docx_heading_outline_v1` | `19` | `succeeded` | `0` | `0` |
| `CF-005` | current | `31` | `docx_heading_outline_v1` | `31` | `succeeded` | `0` | `0` |
| `CF-007` | current | `32` | `docx_heading_outline_with_tables_v1` | `27` | `succeeded` | `0` | `0` |
| `GOV-001` | current | `33` | `xlsx_governance_inventory_v1` | `34` | `succeeded` | `0` | `0` |
| `GOV-002` | current | `34` | `xlsx_policy_decision_log_v1` | `79` | `succeeded` | `0` | `0` |
| `GOV-003` | intentionally unchunked | `none` | `none` | `0` | `not_applicable` | `0` | `0` |
| `OPS-001` | current preserved pilot | `35` | `docx_heading_outline_v1` | `33` | `succeeded` | `4` | `0` |
| `OPS-002` | current | `36` | `xlsx_technical_inventory_v1` | `121` | `succeeded` | `0` | `0` |
| `OPS-003` | current | `37` | `xlsx_capacity_space_rules_v1` | `42` | `succeeded` | `0` | `0` |
| `SERV-001` | current | `38` | `xlsx_service_catalogue_v2` | `17` | `succeeded` | `6` | `0` |
| `SERV-003` | current | `39` | `xlsx_catering_supplier_catalogue_v1` | `24` | `succeeded` | `0` | `0` |
| `SERV-004` | current | `40` | `xlsx_external_supplier_requirements_v1` | `7` | `succeeded` | `0` | `0` |
| `TPL-001` | current | `41` | `docx_numbered_template_sections_v1` | `8` | `succeeded` | `0` | `0` |
| `TPL-002` | current | `42` | `docx_numbered_template_sections_v1` | `8` | `succeeded` | `0` | `0` |
| `TPL-003` | current | `43` | `docx_numbered_template_sections_v1` | `8` | `succeeded` | `0` | `0` |
| `TPL-004` | current | `44` | `docx_numbered_template_sections_v1` | `9` | `succeeded` | `0` | `0` |
| `TPL-005` | current | `45` | `docx_numbered_template_sections_v1` | `9` | `succeeded` | `0` | `0` |
| `TPL-006` | current | `46` | `docx_template_library_v2` | `26` | `succeeded` | `0` | `0` |
| `TPL-007` | current | `47` | `docx_checklist_sections_v1` | `6` | `succeeded` | `0` | `0` |
| `TPL-008` | current | `48` | `docx_numbered_checklist_sections_v1` | `5` | `succeeded` | `0` | `0` |
| `TPL-009` | current | `49` | `docx_numbered_checklist_sections_v1` | `8` | `succeeded` | `0` | `0` |
| `TPL-010` | current | `50` | `docx_numbered_checklist_sections_v1` | `1` | `succeeded` | `0` | `0` |
| `TPL-013` | current | `51` | `docx_linear_checklist_sections_v1` | `3` | `succeeded` | `0` | `0` |

## Intentional Non-Generation Outcomes

### `CF-001`

- governance: `active`
- corpus state: `include`
- processing status: `not_applicable`
- reason: current eligible source is a PNG export with unresolved lookbook master/provenance drift, so no safe deterministic chunk parser is approved

### `GOV-003`

- governance: `draft`
- corpus state: `include`
- processing status: `not_applicable`
- reason: governed version is not current, so it remains outside the active bulk corpus

## Implementation Notes

Key 5.3C parser/loader decisions:

- added DOCX parser support for agreement-with-tables, numbered proposal sections, numbered checklist sections, and linear close-out checklist sections
- added workbook parser support for governance inventory, policy decision log, technical inventory, capacity/space rules, catering catalogue, and external supplier requirements
- preserved logical separation for all approved shared-file patterns
- corrected workbook row-boundary handling so row-4 headers do not become chunks
- corrected workbook row alignment so empty interior cells do not shift later values under the wrong headers
- updated bulk eligibility handling so `OPS-001` reloads correctly on a clean database reset while still remaining a preserved approved pilot output

## Validation

Completed on August 6, 2026:

1. `npx -y supabase@latest db reset`
   Result: passed
2. `npx -y supabase@latest test db`
   Result: passed with `18` SQL test files and `392` DB tests
3. `python3 -m unittest discover -s tools/phase_05_chunking/tests -v`
   Result: passed with `23` parser/chunker tests
4. `python3 -m tools.phase_05_chunking.generate_bulk --write-json /tmp/phase_05_bulk_manifest.json --load-db`
   Result: passed, loaded `22` current chunk sets and `525` current chunks
5. `python3 -m tools.phase_05_chunking.generate_bulk --load-db`
   Result: passed unchanged; corpus remained at `22` current chunk sets, `0` superseded chunk sets, and `525` current chunks

## Review Notes

- Chunk-level logical-rule connectivity remains intentionally narrow and still only covers the approved pilot-linked areas:
  - `OPS-001` logical links: `4`
  - `SERV-001` logical links: `6`
- No exact chunk-rule-version links were added in 5.3C.
- No application-layer retrieval, embeddings, FTS, proposals, automation, or live rental/client records were introduced.

Next gate:

- `PHASE_5_5.3C_CORPUS_COVERAGE_REVIEW_REQUIRED`
