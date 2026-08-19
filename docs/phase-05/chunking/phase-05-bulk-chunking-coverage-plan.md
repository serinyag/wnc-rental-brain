# Phase 5 Bulk Chunking Coverage Plan

Date: August 6, 2026

## Purpose

This document records the pre-load eligibility decision used for Task 5.3C on a clean local database reset.

It answers:

- which governed logical documents were safe bulk-chunking candidates
- which documents were intentionally excluded from chunk generation
- which parser family was selected for each current eligible source

This plan was derived before the first 5.3C bulk load.

## Eligibility Summary

- governed logical documents reviewed: `24`
- current included documents with `active` governance: `22`
- pre-load `READY_TO_CHUNK`: `21`
- pre-load `ALREADY_PILOTED`: `1`
- pre-load generation targets: `22`
- `NO_SAFE_PARSER`: `1`
- `NOT_CURRENT`: `1`
- `SOURCE_UNAVAILABLE`: `0`
- `PROVENANCE_REVIEW_REQUIRED`: `0`

Pre-load interpretation notes:

- `OPS-001` remained an approved preserved pilot even though the governed document version is still `draft`.
- `TPL-006`, `TPL-007`, and `SERV-001` were approved pilot outputs from 5.3B, but on a clean reset they still needed deterministic reload into the database, so they remained `READY_TO_CHUNK` at pre-load evaluation time.
- `CF-001` remained intentionally unchunked because the currently eligible source is a PNG export, not a safe deterministic text/workbook representation.
- `GOV-003` remained intentionally unchunked because the governed version is still `draft`.

## Coverage Matrix

| Code | Title | Corpus | Governance | Extraction source | Source role | Source available | Usage disposition | Parser selected | Pre-load disposition | Reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `CF-001` | Updated Rental Lookbook 2026 | `include` | `active` | `sources/phase-01-03/Client Facing Docs/Updated Rental Lookbook 2026.png` | `export` | `yes` | `eligible_for_extraction` | `none` | `NO_SAFE_PARSER` | Current eligible source is a PNG export with unresolved lookbook master/provenance drift, so no safe deterministic chunk parser is approved. |
| `CF-003` | Studio Rental Terms | `include` | `active` | `sources/phase-01-03/Client Facing Docs/Studio Space _ Terms and Conditions.docx` | `authoritative_editable_source` | `yes` | `eligible_for_extraction` | `docx_heading_outline_v1` | `READY_TO_CHUNK` | Active included document with an eligible local source and a deterministic parser. |
| `CF-005` | Full Venue Rental Terms | `include` | `active` | `sources/phase-01-03/Client Facing Docs/Full Venue _ Rental Terms and Conditions.docx` | `authoritative_editable_source` | `yes` | `eligible_for_extraction` | `docx_heading_outline_v1` | `READY_TO_CHUNK` | Active included document with an eligible local source and a deterministic parser. |
| `CF-007` | WNC Rental Agreement Template | `include` | `active` | `sources/phase-01-03/Client Facing Docs/WNC Rental Agreement Template.docx` | `authoritative_editable_source` | `yes` | `eligible_for_extraction` | `docx_heading_outline_with_tables_v1` | `READY_TO_CHUNK` | Active included document with an eligible local source and a deterministic parser. |
| `GOV-001` | WNC Rental Knowledge Inventory | `include` | `active` | `sources/phase-01-03/Knowledge Governance/WNC Rental Knowledge Inventory.xlsm` | `authoritative_editable_source` | `yes` | `eligible_for_extraction` | `xlsx_governance_inventory_v1` | `READY_TO_CHUNK` | Active included document with an eligible local source and a deterministic parser. |
| `GOV-002` | WNC Rental Policy Decisions & Change Log | `include` | `active` | `sources/phase-01-03/Knowledge Governance/WNC Rental Policy Decisions & Change Log.xlsm` | `authoritative_editable_source` | `yes` | `eligible_for_extraction` | `xlsx_policy_decision_log_v1` | `READY_TO_CHUNK` | Active included document with an eligible local source and a deterministic parser. |
| `GOV-003` | WNC Rental Data Dictionary | `include` | `draft` | `sources/phase-01-03/Knowledge Governance/WNC Rental Data Dictionary.xlsm` | `authoritative_editable_source` | `yes` | `eligible_for_extraction` | `none` | `NOT_CURRENT` | Governance status is `draft`, so the document is not an active bulk-chunking candidate. |
| `OPS-001` | WNC Venue Rental Operations Manual | `include` | `draft` | `sources/phase-01-03/Venue & Operations/WNC Venue Rental Operations Manual.docx` | `authoritative_editable_source` | `yes` | `eligible_for_extraction` | `docx_heading_outline_v1` | `ALREADY_PILOTED` | Approved 5.3B pilot output was preserved for reload even though governance status remains `draft`. |
| `OPS-002` | WNC Venue Technical & Equipment Inventory | `include` | `active` | `sources/phase-01-03/Venue & Operations/WNC Venue Technical & Equipment Inventory.xlsm` | `authoritative_editable_source` | `yes` | `eligible_for_extraction` | `xlsx_technical_inventory_v1` | `READY_TO_CHUNK` | Active included document with an eligible local source and a deterministic parser. |
| `OPS-003` | WNC Capacity & Space Use Rules | `include` | `active` | `sources/phase-01-03/Venue & Operations/WNC Venue Technical & Equipment Inventory.xlsm` | `supporting_source` | `yes` | `eligible_for_extraction` | `xlsx_capacity_space_rules_v1` | `READY_TO_CHUNK` | Active included document with an eligible local source and a deterministic parser. Shared workbook scope stayed logically separate from `OPS-002`. |
| `SERV-001` | WNC Rental Services Catalogue | `include` | `active` | `sources/phase-01-03/Catalogues/WNC Rental Services Catalogue.xlsm` | `authoritative_editable_source` | `yes` | `eligible_for_extraction` | `xlsx_service_catalogue_v2` | `READY_TO_CHUNK` | Approved pilot output existed conceptually but still required deterministic reload on the clean reset. |
| `SERV-003` | WNC Catering, Beverage & Supplier Catalogue | `include` | `active` | `sources/phase-01-03/Catalogues/WNC Catering, Beverage & Supplier Catalogue.xlsm` | `authoritative_editable_source` | `yes` | `eligible_for_extraction` | `xlsx_catering_supplier_catalogue_v1` | `READY_TO_CHUNK` | Active included document with an eligible local source and a deterministic parser. |
| `SERV-004` | External Supplier Requirements | `include` | `active` | `sources/phase-01-03/Catalogues/WNC Catering, Beverage & Supplier Catalogue.xlsm` | `supporting_source` | `yes` | `eligible_for_extraction` | `xlsx_external_supplier_requirements_v1` | `READY_TO_CHUNK` | Active included document with an eligible local source and a deterministic parser. Shared workbook scope stayed logically separate from `SERV-003`. |
| `TPL-001` | Studio Rental Proposal Template | `include` | `active` | `sources/phase-01-03/Checklists + Templates/Proposal Templates/Studio Rental Proposal Template.docx` | `authoritative_editable_source` | `yes` | `eligible_for_extraction` | `docx_numbered_template_sections_v1` | `READY_TO_CHUNK` | Active included document with an eligible local source and a deterministic parser. |
| `TPL-002` | Entire Venue Proposal Template | `include` | `active` | `sources/phase-01-03/Checklists + Templates/Proposal Templates/Entire Venue Proposal Template.docx` | `authoritative_editable_source` | `yes` | `eligible_for_extraction` | `docx_numbered_template_sections_v1` | `READY_TO_CHUNK` | Active included document with an eligible local source and a deterministic parser. |
| `TPL-003` | Custom Scope Proposal Template | `include` | `active` | `sources/phase-01-03/Checklists + Templates/Proposal Templates/Custom Scope Proposal Template.docx` | `authoritative_editable_source` | `yes` | `eligible_for_extraction` | `docx_numbered_template_sections_v1` | `READY_TO_CHUNK` | Active included document with an eligible local source and a deterministic parser. |
| `TPL-004` | Production Coordination Proposal Template | `include` | `active` | `sources/phase-01-03/Checklists + Templates/Proposal Templates/Production Coordination Proposal Template.docx` | `authoritative_editable_source` | `yes` | `eligible_for_extraction` | `docx_numbered_template_sections_v1` | `READY_TO_CHUNK` | Active included document with an eligible local source and a deterministic parser. |
| `TPL-005` | Full Production Proposal Template | `include` | `active` | `sources/phase-01-03/Checklists + Templates/Proposal Templates/Full Production Proposal Template.docx` | `authoritative_editable_source` | `yes` | `eligible_for_extraction` | `docx_numbered_template_sections_v1` | `READY_TO_CHUNK` | Active included document with an eligible local source and a deterministic parser. |
| `TPL-006` | WNC Rental Email Template Library | `include` | `active` | `sources/phase-01-03/Checklists + Templates/WNC Rental Email Template Library.docx` | `authoritative_editable_source` | `yes` | `eligible_for_extraction` | `docx_template_library_v2` | `READY_TO_CHUNK` | Approved pilot output existed conceptually but still required deterministic reload on the clean reset. |
| `TPL-007` | Discovery Call Checklist | `include` | `active` | `sources/phase-01-03/Checklists + Templates/WNC Rental Discovery Call & Site Visit Checklist.docx` | `authoritative_editable_source` | `yes` | `eligible_for_extraction` | `docx_checklist_sections_v1` | `READY_TO_CHUNK` | Approved pilot output existed conceptually but still required deterministic reload on the clean reset. |
| `TPL-008` | Site Visit Checklist | `include` | `active` | `sources/phase-01-03/Checklists + Templates/WNC Rental Discovery Call & Site Visit Checklist.docx` | `supporting_source` | `yes` | `eligible_for_extraction` | `docx_numbered_checklist_sections_v1` | `READY_TO_CHUNK` | Active included document with an eligible local source and a deterministic parser. Shared DOCX scope stayed logically separate from `TPL-007`. |
| `TPL-009` | Event Handover Checklist | `include` | `active` | `sources/phase-01-03/Checklists + Templates/WNC Rental Event Handover & Final Readiness Checklist.docx` | `authoritative_editable_source` | `yes` | `eligible_for_extraction` | `docx_numbered_checklist_sections_v1` | `READY_TO_CHUNK` | Active included document with an eligible local source and a deterministic parser. |
| `TPL-010` | Final Readiness Checklist | `include` | `active` | `sources/phase-01-03/Checklists + Templates/WNC Rental Event Handover & Final Readiness Checklist.docx` | `supporting_source` | `yes` | `eligible_for_extraction` | `docx_numbered_checklist_sections_v1` | `READY_TO_CHUNK` | Active included document with an eligible local source and a deterministic parser. Shared DOCX scope stayed logically separate from `TPL-009`. |
| `TPL-013` | Rental Close-Out Checklist | `include` | `active` | `sources/phase-01-03/Checklists + Templates/WNC Rental Close-Out Checklist.docx` | `authoritative_editable_source` | `yes` | `eligible_for_extraction` | `docx_linear_checklist_sections_v1` | `READY_TO_CHUNK` | Active included document with an eligible local source and a deterministic parser. |

## Execution Notes

- Shared-file patterns remained separate for:
  - `TPL-007` / `TPL-008`
  - `TPL-009` / `TPL-010`
  - `OPS-002` / `OPS-003`
  - `SERV-003` / `SERV-004`
- No LLM-based parsing, classification, or link generation was introduced.
- No corpus governance state was changed to make a document chunkable.
- `CF-001` and `GOV-003` remained explicit non-generation outcomes and were later recorded in processing as `not_applicable` with explanatory reasons.
