# Phase 5 Source Corpus Matrix

## 1. Executive Summary

This matrix accounts for the complete known controlled rental source set visible in the repository by combining:

- the Phase 4 `source_registry` seed inventory
- the Phase 4 source manifest and authoritative source map
- the Knowledge Inventory workbook as the broadest Phase 2 corpus register
- the physical files present under `sources/phase-01-03/`

Important scope note:

- The Knowledge Inventory tracks some **logical documents or embedded subdocuments** that are not separate rows in `public.source_registry`, such as `CF-001`, `OPS-003`, `SERV-002`, `SERV-004`, `TPL-008`, and `TPL-010`.
- The `source_registry` tracks some **physical source representations** separately, such as `COM-001-XLSM` and `COM-001-XLSX`.
- This matrix keeps both layers visible so Task 5.1 can model logical documents, document versions, and physical source representations correctly.

Important provenance findings before the matrix:

- `CF-001` exists in the Knowledge Inventory as the lookbook editable master, but no local physical file is present.
- `CF-002` is inconsistent across sources:
  - Knowledge Inventory: "Updated Rental Lookbook 2026: PDF"
  - local physical/source manifest/source registry: `Updated Rental Lookbook 2026.png`
- `COM-001` exists logically in the Knowledge Inventory, but local physical representations are split into `COM-001-XLSM` and `COM-001-XLSX`, with unresolved drift.
- `OPS-003` is not a separate file; it is an embedded governed rules section inside `OPS-002`.
- `SERV-004` is not a separate file; it is an embedded governed tab/set inside `SERV-003`.
- `TPL-008` is combined into the same physical file as `TPL-007`.
- `TPL-010` is combined into the same physical file as `TPL-009`.
- The deferred `SERV-002` facilitator catalogue is referenced in governance, but no physical source is present locally.

## 2. Corpus Matrix

| Existing source code | Source title | Physical file | File available | File type | Existing authority | Existing lifecycle/status | Current/superseded/historical | Proposed logical document | Source representation role | Phase 5 disposition | Disposition reason | Proposed primary knowledge category | Knowledge role | Applicable rental types | Intended audiences | Access/confidentiality observation | Phase 4 domain overlap | Candidate logical rule codes | Exact rule-version relevance | Proposed semantic chunking strategy | Search value | Provenance issues | Review required |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `GOV-001` | WNC Rental Knowledge Inventory | `sources/phase-01-03/Knowledge Governance/WNC Rental Knowledge Inventory.xlsm` | yes | `xlsm` | authoritative | Inventory: `Current`; source_registry: `current` | current | WNC Rental Knowledge Inventory | authoritative workbook | `INCLUDE` | Master corpus/governance index for the whole source set | Governance & corpus governance | authoritative controlled document | all (`studio_space`, `entire_venue`, `custom_scope`) | WNC Rental Knowledge Owner; rental coordinator; management | internal governance; not for anonymous read | none direct; governs corpus rather than a Phase 4 rule domain | none direct | `NO` | workbook; chunk by source-record row / governed section | finding source ownership, status, applies-to scope, review gaps | none material | no |
| `GOV-002` | WNC Rental Policy Decisions & Change Log | `sources/phase-01-03/Knowledge Governance/WNC Rental Policy Decisions & Change Log.xlsm` | yes | `xlsm` | authoritative | Inventory: `To create`; source_registry: `current_controlled_record` | current, but metadata discrepancy | WNC Rental Policy Decisions & Change Log | authoritative workbook | `INCLUDE` | Active governance source for canonical decisions and open decisions | Governance & policy explanation | authoritative controlled document | all (`studio_space`, `entire_venue`, `custom_scope`) | WNC Rental Knowledge Owner; General Manager; rental coordinator | internal governance; commercially sensitive; not for broad read | cross-domain governance for all 10 Phase 4 domains | `FEE_*`; `PAYMENT_*`; `EXPEDITED_SURCHARGE_WITHIN_14_DAYS`; `CANCELLATION_*`; cross-domain chunk-level review | `POSSIBLE` | workbook; chunk by decision row / open-decision row | explaining why a rule exists, what is still open, what must not be automated | inventory and seed disagree on lifecycle/status granularity | yes: lifecycle discrepancy and broad cross-domain span |
| `GOV-003` | WNC Rental Data Dictionary | `sources/phase-01-03/Knowledge Governance/WNC Rental Data Dictionary.xlsm` | yes | `xlsm` | authoritative | Inventory: `Existing: review required`; source_registry: `current_controlled_draft`; workbook overview: `Current: controlled Phase 2 draft` | current controlled draft with wording discrepancy | WNC Rental Data Dictionary | authoritative workbook | `INCLUDE` | Canonical terminology and machine-value authority is core Phase 5 knowledge | Governance & canonical definitions | authoritative controlled document | all (`studio_space`, `entire_venue`, `custom_scope`) | WNC Rental Knowledge Owner; builders of governed systems; rental coordinator | internal governance; not for anonymous read | strongest overlap with service/facilitator, rental types, spaces; indirect cross-domain reuse | none direct; vocabulary source more than rule-code source | `NO` | workbook; chunk by dictionary row / enum group / alias block | defining canonical machine values, rental types, spaces, service types, facilitator arrangements | lifecycle wording differs across inventory, source registry, and workbook overview | yes: lifecycle wording discrepancy |
| `GOV-004` | WNC Rental Informal Rules | `sources/phase-01-03/Venue & Operations/WNC Rental Informal Rules.xlsm` | yes | `xlsm` | unverified | Inventory: `To create`; source_registry: `working_non_authoritative`; source manifest: unverified, non-authoritative | unresolved / non-authoritative working source | WNC Rental Informal Rules | working workbook | `DEFER` | Legitimate governance source, but explicitly unverified and not safe for active governed corpus | Governance working material | unresolved/blocked material | all (`studio_space`, `entire_venue`, `custom_scope`) | rental point of contact; General Manager | internal only; should clearly not inherit anonymous read | cross-domain but non-authoritative | none safe to rely on directly | `POSSIBLE` | workbook; chunk by informal rule row after future review only | locating unresolved practices and ambiguities for governance review | non-authoritative status is explicit; should not be blended into active corpus | yes: defer until governance review |
| `CF-001` | Updated Rental Lookbook 2026: editable master | not present locally; Knowledge Inventory only | no | not specified locally; inventory implies editable source | authoritative | Inventory: `Current` | current | Updated Rental Lookbook 2026 | authoritative editable source | `INCLUDE` | Active client-facing knowledge document; logical parent of current export | Client-facing controlled document | authoritative controlled document | all (`studio_space`, `entire_venue`, `custom_scope`) | prospective clients; rental coordinator; marketing/brand | client-facing; published/commercially sensitive; not private but not ideal for raw anonymous corpus without review | likely booking fees, capacity, space access, service/facilitator, plus deferred venue-pricing context | `requires chunk-level review`; likely `CAPACITY_*`; possible booking-fee references | `NO` | likely narrative + offer sections; chunk by page/section/topic block | answering what WNC offers, how the venue is positioned, what clients can expect | logical master exists in inventory but physical local file is missing; export record disagrees on file format | yes: missing physical file; export format discrepancy |
| `CF-002` | Updated Rental Lookbook 2026 export | `sources/phase-01-03/Client Facing Docs/Updated Rental Lookbook 2026.png` | yes | inventory says PDF export; local file is `png` | authoritative | Inventory: `Current`; source_registry: `current_export` | current export; format discrepancy | Updated Rental Lookbook 2026 | export | `INCLUDE` | Current client-facing representation of the lookbook still has retrieval value, despite not being the logical master | Client-facing controlled document | reference material / client-facing export | all (`studio_space`, `entire_venue`, `custom_scope`) | prospective clients; rental coordinator; marketing/brand | client-facing; published/commercially sensitive | likely booking fees, capacity, space access, service/facilitator, deferred venue-pricing context | `requires chunk-level review` | `NO` | image/PDF-style artifact; later chunk by visual section or OCR-backed page block | retrieving published client-facing descriptions, capacities, positioning, offer framing | inventory says PDF; local artifact and source manifest say PNG | yes: file-format/title discrepancy |
| `CF-003` | Studio Rental Terms editable master | `sources/phase-01-03/Client Facing Docs/Studio Space _ Terms and Conditions.docx` | yes | `docx` | authoritative | Inventory: `Current`; source_registry: `current` | current | Studio Rental Terms | authoritative editable source | `INCLUDE` | Active controlled client-facing terms with strong contextual and contractual value | Client-facing controlled document | authoritative controlled document | `studio_space` | client; rental coordinator; General Manager; client-facing staff | client-facing contractual text; should not inherit anonymous read without review | payment; expedited surcharge; cancellation; space access; operational requirements; catering; service/facilitator | `EXPEDITED_SURCHARGE_WITHIN_14_DAYS`; `OPER_STUDIO_GRACE_PERIOD`; `ACCESS_STUDIO_*`; `CATER_VAT_COORDINATION_SERVICE_21_PERCENT`; chunk-level review | `POSSIBLE` | narrative document; chunk by heading/subheading/clause block | explaining studio booking terms, access, payment, cancellation, client obligations | current master paired with older drifted export `CF-004` | yes: high structured-truth overlap |
| `CF-004` | Studio Rental Terms export | `sources/phase-01-03/Client Facing Docs/Studio Space _ Terms and Conditions (2).pdf` | yes | `pdf` | authoritative | Inventory: `Current`; source_registry: `current_export`; source manifest: current export but drifted | current export with older wording | Studio Rental Terms | export | `EXCLUDE` | Useful for conflict detection and historical wording review, but not a separate active governed document | Client-facing controlled document | historical/example-adjacent export | `studio_space` | client; rental coordinator | client-facing contractual export; outdated wording risk | payment; expedited surcharge; cancellation; operational requirements | same logical family as `CF-003`; no separate stable links needed | `YES` | if ever used, chunk by clause/page for historical comparison only | resolving wording drift between export and editable master | manifest says export appears older than editable master | yes: drifted export |
| `CF-005` | Full Venue Rental Terms editable master | `sources/phase-01-03/Client Facing Docs/Full Venue _ Rental Terms and Conditions.docx` | yes | `docx` | authoritative | Inventory: `Current`; source_registry: `current` | current | Full Venue Rental Terms | authoritative editable source | `INCLUDE` | Active controlled client-facing terms with strong contractual and operational context | Client-facing controlled document | authoritative controlled document | `entire_venue` | client; rental coordinator; General Manager; client-facing staff | client-facing contractual text; should not inherit anonymous read without review | payment; expedited surcharge; cancellation; capacity; space access; operational requirements; catering | `EXPEDITED_SURCHARGE_WITHIN_14_DAYS`; `ACCESS_ENTIRE_VENUE_*`; `CAPACITY_ENTIRE_VENUE_LEGAL_MAX`; `OPER_ENTIRE_VENUE_GRACE_PERIOD`; chunk-level review | `POSSIBLE` | narrative document; chunk by heading/subheading/clause block | explaining full-venue obligations, access, payment, cancellation, event restrictions | current master paired with drifted export `CF-006` | yes: high structured-truth overlap |
| `CF-006` | Full Venue Rental Terms export | `sources/phase-01-03/Client Facing Docs/Full Venue _ Rental Terms and Conditions.pdf` | yes | `pdf` | authoritative | Inventory: `Current`; source_registry: `current_export`; source manifest: current export but drifted | current export with older wording | Full Venue Rental Terms | export | `EXCLUDE` | Export is not the governed primary source and appears older than the editable master | Client-facing controlled document | historical/example-adjacent export | `entire_venue` | client; rental coordinator | client-facing contractual export; outdated wording risk | payment; expedited surcharge; cancellation; operational requirements | same logical family as `CF-005`; no separate stable links needed | `YES` | if ever used, chunk by clause/page for historical comparison only | resolving wording drift between export and editable master | manifest says export appears older than editable master | yes: drifted export |
| `CF-007` | WNC Rental Agreement Template | `sources/phase-01-03/Client Facing Docs/WNC Rental Agreement Template.docx` | yes | `docx` | authoritative | Inventory: `Current`; source_registry: `current` | current | WNC Rental Agreement Template | authoritative editable source | `INCLUDE` | Core controlled document for confirmed rental wording and scoped commitments | Client-facing controlled document | authoritative controlled document | all confirmed rentals; likely all (`studio_space`, `entire_venue`, `custom_scope`) | client; rental coordinator; General Manager; operations | client-facing contractual template; commercially sensitive; should not inherit anonymous read | overlaps all 10 domains except only partial booking-fee specifics in practice; strongest on payment, cancellation, access, operations, service/facilitator, technical | `PAYMENT_CONFIRMATION_MINIMUM_30_PERCENT`; `EXPEDITED_SURCHARGE_WITHIN_14_DAYS`; `CANCELLATION_*`; `ACCESS_*`; `OPER_*`; `SERVICE_*`; `FACILITATOR_*`; chunk-level review | `POSSIBLE` | template; chunk by agreement section / schedule / clause block | retrieving confirmed-scope wording, schedule language, cancellation clauses, technical responsibility language | current logical master; version/effective-date placeholders suggest future version tracking matters | yes: very high structured-truth overlap |
| `COM-001` | WNC Rental Pricing, Fees & Payment Rules | logical record only in Knowledge Inventory | no separate local physical file under this exact ID | logical workbook record | authoritative | Inventory: `Current`; authoritative source map and source manifest say conflict exists | current but unresolved/conflict-flagged | WNC Rental Pricing, Fees & Payment Rules | logical workbook record | `DEFER` | Legitimate corpus source, but physical representations drift and provenance is unresolved | Commercial rules | unresolved/blocked material | all (`studio_space`, `entire_venue`, `custom_scope`) | rental coordinator; finance; management | highly commercially sensitive; clearly not for broad read | booking fees; payment; expedited surcharge; cancellation; catering VAT; deferred venue pricing | `FEE_*`; `PAYMENT_*`; `EXPEDITED_SURCHARGE_WITHIN_14_DAYS`; `CANCELLATION_*`; `CATER_VAT_*`; chunk-level review | `YES` | workbook; later chunk by sheet / rule row / policy block | commercial rule explanations, pricing logic, payment timing, cancellation treatments | logical workbook maps to two drifting local physical representations | yes: unresolved logical-to-physical provenance |
| `COM-001-XLSM` | WNC Rental Pricing, Fees & Payment Rules (xlsm) | `sources/phase-01-03/Commercial Rules/WNC Rental Pricing, Fees & Payment Rules.xlsm` | yes | `xlsm` | authoritative | source_registry: `current_conflict_flagged`; source manifest: authoritative current conflict flagged | current but unresolved/conflict-flagged | WNC Rental Pricing, Fees & Payment Rules | workbook representation | `DEFER` | Active but unresolved commercial representation; defer from active corpus until provenance/conflict handling is designed | Commercial rules | unresolved/blocked material | all (`studio_space`, `entire_venue`, `custom_scope`) | rental coordinator; finance; management | highly commercially sensitive; not for broad read | booking fees; payment; expedited surcharge; cancellation; catering VAT; deferred venue pricing | `FEE_STUDIO_1_TO_3_HOUR_BOOKING`; `PAYMENT_CONFIRMATION_MINIMUM_30_PERCENT`; `EXPEDITED_SURCHARGE_WITHIN_14_DAYS`; `CANCELLATION_CLIENT_OVER_30_RENTAL_PAYMENTS`; `CATER_VAT_PRODUCTS_9_PERCENT` | `YES` | workbook; chunk by sheet and governed row group | commercial policy lookup and historical conflict analysis | conflicts with `COM-001-XLSX`; may represent one logical doc or unresolved duplicates | yes: conflict-flagged |
| `COM-001-XLSX` | WNC Rental Pricing, Fees & Payment Rules (xlsx) | `sources/phase-01-03/Venue & Operations/WNC Rental Pricing, Fees & Payment Rules.xlsx` | yes | `xlsx` | authoritative-looking duplicate | source_registry: `current_conflict_flagged`; source manifest: unresolved drift | current but unresolved/conflict-flagged | WNC Rental Pricing, Fees & Payment Rules | workbook representation | `DEFER` | Same logical family as `COM-001-XLSM`, but precedence is unresolved | Commercial rules | unresolved/blocked material | all (`studio_space`, `entire_venue`, `custom_scope`) | rental coordinator; finance; management | highly commercially sensitive; not for broad read | booking fees; payment; expedited surcharge; cancellation; catering VAT; deferred venue pricing | same core codes as `COM-001-XLSM`; chunk-level review | `YES` | workbook; chunk by sheet and governed row group | comparing conflicting commercial wording/values across workbook variants | source manifest says closer to decision log in some places, but relationship to xlsm is unresolved | yes: conflict-flagged duplicate |
| `OPS-001` | WNC Venue Rental Operations Manual | `sources/phase-01-03/Venue & Operations/WNC Venue Rental Operations Manual.docx` | yes | `docx` | authoritative | Inventory: `Current`; source_registry: `current_controlled_draft`; document control says version `0.9: Phase 2 controlled draft`, effective date upon approval | current controlled draft | WNC Venue Rental Operations Manual | authoritative editable source | `INCLUDE` | Core internal operational knowledge document with clear retrieval value beyond deterministic rows | Operational procedure | authoritative controlled document | all (`studio_space`, `entire_venue`, `custom_scope`) | operations; rental coordinator; General Manager; event lead | internal operational; should not inherit anonymous read | operational requirements; space access; capacity; technical capability; catering/external suppliers; event suitability context | `OPER_STUDIO_GRACE_PERIOD`; `OPER_ENTIRE_VENUE_GRACE_PERIOD`; `OPER_SETUP_START_AT_BOOKED_TIME`; `OPER_EARLY_OPERATIONAL_ACCESS_REQUIRES_APPROVAL`; `OPER_SUPPLIER_ACCESS_APPROVED_TIMELINE_ONLY`; `OPER_PROFESSIONAL_CLEANING_MANUAL_REVIEW` | `POSSIBLE` | manual; chunk by heading/subheading/procedure block | preparing, operating, clearing, handing over, restricting materials, managing supplier access | lifecycle/status wording differs between inventory, source_registry, and in-file control block | yes: status/effective-date review |
| `OPS-002` | WNC Venue Technical & Equipment Inventory | `sources/phase-01-03/Venue & Operations/WNC Venue Technical & Equipment Inventory.xlsm` | yes | `xlsm` | authoritative | Inventory: `Current`; source_registry: `current` | current | WNC Venue Technical & Equipment Inventory | authoritative workbook | `INCLUDE` | Core venue reference and technical feasibility knowledge source | Technical & venue reference | authoritative controlled document | all (`studio_space`, `entire_venue`, `custom_scope`) | operations; facilities; rental coordinator; site-visit staff | internal operational; commercially sensitive; not for broad read | capacity; space access; technical capability/equipment | `CAPACITY_ENTIRE_VENUE_LEGAL_MAX`; `ACCESS_STUDIO_RETAIL_SHARED`; `ACCESS_ENTIRE_VENUE_ONE_TO_ONE_INCLUDED`; `TECH_WIFI_STANDARD`; `TECH_BASIC_PROJECTOR_REQUEST_ONLY`; `TECH_REQ_CUSTOM_TECH_CONFIRM` | `NO` | workbook; chunk by tab / coherent rule matrix / inventory row group | answering what spaces, capacities, equipment, and technical capabilities currently exist | also contains embedded logical subdocument `OPS-003` | yes: embedded subdocument and high structured overlap |
| `OPS-003` | WNC Capacity & Space Use Rules | embedded in `OPS-002` workbook | yes via parent workbook | embedded workbook section | authoritative | Inventory: `Current` | current | WNC Capacity & Space Use Rules | embedded subdocument / supporting source | `INCLUDE` | Knowledge Inventory treats this as a distinct governed rules source even though the file is shared with `OPS-002` | Technical & venue reference | authoritative controlled document | all (`studio_space`, `entire_venue`, `custom_scope`) | operations; General Manager; rental coordinator; safety reviewers | internal operational; venue safety relevance | capacity; space access | `CAPACITY_ENTIRE_VENUE_LEGAL_MAX`; `CAPACITY_STUDIO_LYING_DOWN`; `CAPACITY_RETAIL_STANDING`; `ACCESS_*`; requires chunk-level review | `NO` | workbook subdocument; chunk by rules table/space-use block | answering venue capacity and room-use constraints | no separate physical file; logical subdocument inside `OPS-002` | yes: embedded-subdocument modeling |
| `SERV-001` | WNC Rental Services Catalogue | `sources/phase-01-03/Catalogues/WNC Rental Services Catalogue.xlsm` | yes | `xlsm` | authoritative | Inventory: `Current`; source_registry: `current` | current | WNC Rental Services Catalogue | authoritative workbook | `INCLUDE` | Active service-definition source with strong retrieval value and high Phase 4 overlap | Service & supplier guidance | authoritative controlled document | all (`studio_space`, `entire_venue`, `custom_scope`) | rental coordinator; operations; General Manager | internal commercial/service guidance; not for broad read | service/facilitator requirements; some catering and technical coordination context | `SERVICE_LEVEL_VENUE_ONLY`; `SERVICE_LEVEL_SUPPORTED_RENTAL`; `SERVICE_LEVEL_FULL_PRODUCTION`; `SERVICE_ITEM_EVENT_MANAGER`; `SERVICE_ITEM_FACILITATOR_SOURCING`; `FACILITATOR_WNC_PROVIDED_CONFIRMATION_REQUIRED` | `NO` | workbook; chunk by service row / controlled-list section | explaining service scope, service items, manual quote boundaries, facilitator sourcing | overlaps with deferred facilitator catalogue boundary | yes: high structured overlap and deferred-boundary sensitivity |
| `SERV-002` | WNC Facilitators & Rental Experiences | no local file; Knowledge Inventory only | no | not available locally | authoritative in inventory, but explicitly deferred in Phase 4 governance | Inventory: `To create`; future enhancement `FE-002` | deferred / not yet active | WNC Facilitators & Rental Experiences | planned logical document | `DEFER` | Explicit deferred boundary; do not pull into active Phase 5 corpus now | Facilitator information | future/hypothetical material | `RENTAL_APPLICABILITY_REVIEW_REQUIRED` | rental point of contact; facilitator-program owners | likely sensitive/private; no current file to inspect | none active in current Phase 4; facilitator catalogue explicitly excluded | none current | `NO` | unknown; no file to inspect | none until the catalogue exists and is governed | referenced in inventory and future enhancements only; no physical source | yes: explicit deferred boundary |
| `SERV-003` | WNC Catering, Beverage & Supplier Catalogue | `sources/phase-01-03/Catalogues/WNC Catering, Beverage & Supplier Catalogue.xlsm` | yes | `xlsm` | authoritative | Inventory: `Current`; source_registry: `current` | current | WNC Catering, Beverage & Supplier Catalogue | authoritative workbook | `INCLUDE` | Active operational/service guidance with clear value beyond typed rule rows | Service & supplier guidance | authoritative controlled document | all (`studio_space`, `entire_venue`, `custom_scope`) | rental coordinator; operations; supplier coordinators | internal operational/commercial guidance; not for broad read | catering/external suppliers; operational requirements; service/facilitator; technical confirmation context | `CATER_EXTERNAL_CATERERS_ALLOWED`; `CATER_WNC_PARTNER_CONFIRMATION_REQUIRED`; `CATER_VAT_PRODUCTS_9_PERCENT`; `CATER_VAT_COORDINATION_SERVICE_21_PERCENT`; `CATER_VAT_MIXED_SPLIT_REQUIRED` | `NO` | workbook; chunk by tab / rule row / supplier-requirement block | handling caterers, baristas, VAT treatment, supplier requirements, kitchen use | also contains embedded `SERV-004`; some working-rule content remains unresolved | yes: high overlap and working-rule sensitivity |
| `SERV-004` | External Supplier Requirements | embedded tab in `SERV-003` workbook | yes via parent workbook | embedded workbook section | authoritative | Inventory: `Current` | current | External Supplier Requirements | embedded subdocument / supporting source | `INCLUDE` | Knowledge Inventory treats external supplier operating requirements as a distinct governed source within the catalogue | Service & supplier guidance | authoritative controlled document | all (`studio_space`, `entire_venue`, `custom_scope`) | operations; rental coordinator; supplier coordinators | internal operational guidance; not for broad read | catering/external suppliers; operational requirements; some technical confirmation | `CATER_EXTERNAL_CATERER_STORAGE_CONFIRM`; `CATER_BARISTA_NON_STANDARD_MACHINE_CONFIRM`; requires chunk-level review | `NO` | workbook subdocument; chunk by requirement row / supplier category | retrieving non-standard supplier operating requirements and confirmations | no separate physical file; embedded inside `SERV-003` | yes: embedded-subdocument modeling |
| `TPL-001` | Studio Rental Proposal Template | `sources/phase-01-03/Checklists + Templates/Proposal Templates/Studio Rental Proposal Template.docx` | yes | `docx` | guidance | Inventory/source_registry: `Current` | current | Studio Rental Proposal Template | authoritative current guidance representation | `INCLUDE` | Proposal wording and structure are core Phase 5 guidance material | Proposal guidance | communication/template guidance | `studio_space` | rental coordinator; client-facing staff | internal guidance for client-facing output; commercially sensitive | service/facilitator; booking fees; payment; catering; operational requirements; but mostly contextual | `SERVICE_LEVEL_*`; possible `FEE_*`; chunk-level review | `NO` | template; chunk by proposal section / reusable section block | drafting studio proposals and scope wording | no major provenance issue | no |
| `TPL-002` | Entire Venue Proposal Template | `sources/phase-01-03/Checklists + Templates/Proposal Templates/Entire Venue Proposal Template.docx` | yes | `docx` | guidance | current | current | Entire Venue Proposal Template | current guidance representation | `INCLUDE` | Proposal guidance for entire-venue rentals belongs in active corpus | Proposal guidance | communication/template guidance | `entire_venue` | rental coordinator; client-facing staff | internal guidance for client-facing output; commercially sensitive | service/facilitator; payment; operational requirements; catering; capacity/access context | `SERVICE_LEVEL_*`; `ACCESS_ENTIRE_VENUE_*`; chunk-level review | `NO` | template; chunk by proposal section / reusable section block | drafting full-venue proposals and scope language | no major provenance issue | no |
| `TPL-003` | Custom Scope Proposal Template | `sources/phase-01-03/Checklists + Templates/Proposal Templates/Custom Scope Proposal Template.docx` | yes | `docx` | guidance | current | current | Custom Scope Proposal Template | current guidance representation | `INCLUDE` | Needed because `custom_scope` is a canonical rental type and Phase 4 leaves many defaults manual | Proposal guidance | communication/template guidance | `custom_scope` | rental coordinator; client-facing staff | internal guidance for client-facing output; commercially sensitive | service/facilitator; access; operational requirements; technical; capacity review context | likely `SERVICE_*`; `ACCESS_*`; `OPER_*`; requires chunk-level review | `NO` | template; chunk by proposal section / reusable section block | drafting unusual/custom scope proposals without inventing defaults | `custom_scope` remains policy-sensitive in Phase 4 blockers | yes: custom-scope sensitivity |
| `TPL-004` | Production Coordination Proposal Template | `sources/phase-01-03/Checklists + Templates/Proposal Templates/Production Coordination Proposal Template.docx` | yes | `docx` | guidance | current | current | Production Coordination Proposal Template | current guidance representation | `INCLUDE` | Active proposal guidance even though pricing remains manual | Proposal guidance | communication/template guidance | `RENTAL_APPLICABILITY_REVIEW_REQUIRED` | rental coordinator; production coordination staff | internal guidance; commercially sensitive | service/facilitator; technical; catering; operational requirements | `SERVICE_ITEM_PRODUCTION_COORDINATION`; `SERVICE_ITEM_TECHNICAL_COORDINATION`; chunk-level review | `NO` | template; chunk by proposal section / reusable section block | drafting production-coordination proposals and scope language | service-level/service-scope rather than rental-type-scoped | yes: rental applicability review |
| `TPL-005` | Full Production Proposal Template | `sources/phase-01-03/Checklists + Templates/Proposal Templates/Full Production Proposal Template.docx` | yes | `docx` | guidance | current | current | Full Production Proposal Template | current guidance representation | `INCLUDE` | Active guidance for a real service path, despite manual pricing and open methodology | Proposal guidance | communication/template guidance | `RENTAL_APPLICABILITY_REVIEW_REQUIRED` | rental coordinator; General Manager; production staff | internal guidance; commercially sensitive | service/facilitator; technical; catering; operational requirements | `SERVICE_LEVEL_FULL_PRODUCTION`; `SERVICE_ITEM_EVENT_MANAGER`; `SERVICE_ITEM_PRODUCTION_COORDINATION`; chunk-level review | `NO` | template; chunk by proposal section / reusable section block | drafting full-production proposals and explaining manual-scope deliverables | full-production pricing remains manual/open | yes: service-level rather than rental-type scoping |
| `TPL-006` | WNC Rental Email Template Library | `sources/phase-01-03/Checklists + Templates/WNC Rental Email Template Library.docx` | yes | `docx` | guidance | current | current | WNC Rental Email Template Library | current guidance representation | `INCLUDE` | Communication guidance is a named Phase 5 need and is clearly present in corpus | Communication guidance | communication/template guidance | all (`studio_space`, `entire_venue`, `custom_scope`) | rental coordinator; client-facing staff | internal guidance; may contain personal-information risk in examples; should not inherit anonymous read | generally contextual; can touch payment, follow-up, proposals, operational clarifications | none required at document level; chunk-level review for scenario-specific references | `NO` | template library; chunk by complete email template / scenario block | retrieving appropriate client wording and response patterns | source manifest notes privacy-sensitive example risk in broader system | yes: privacy/access review |
| `TPL-007` | Discovery Call Checklist: combined | `sources/phase-01-03/Checklists + Templates/WNC Rental Discovery Call & Site Visit Checklist.docx` | yes | `docx` | guidance | current | current | Discovery Call Checklist | current guidance representation; combined file with site-visit checklist | `INCLUDE` | Active intake/discovery guidance with strong operational retrieval value | Checklist / workflow guidance | operational guidance | all (`studio_space`, `entire_venue`, `custom_scope`) | rental coordinator; client-facing staff | internal operational guidance; not for broad read | operational requirements; capacity; access; technical; catering; service/facilitator | likely indirect only; `requires chunk-level review` | `NO` | checklist; chunk by section / task group / intake topic | preparing discovery calls and identifying missing facts without guessing policy | combined physical file also represents `TPL-008` | yes: combined logical docs |
| `TPL-008` | Site Visit Checklist: combines | no separate file; combined into `TPL-007` physical doc | yes via parent file | embedded/combined doc section | guidance | current | current | Site Visit Checklist | combined logical subdocument | `INCLUDE` | Inventory treats site visits as a distinct logical guidance object | Checklist / workflow guidance | operational guidance | all (`studio_space`, `entire_venue`, `custom_scope`) | rental coordinator; operations; site-visit staff | internal operational guidance; not for broad read | capacity; access; technical; operational requirements | likely indirect only; `requires chunk-level review` | `NO` | checklist; chunk by site-visit section / task group | conducting venue visits and feasibility reviews | no separate physical file; combined into discovery checklist file | yes: combined logical docs |
| `TPL-009` | Event Handover Checklist | `sources/phase-01-03/Checklists + Templates/WNC Rental Event Handover & Final Readiness Checklist.docx` | yes | `docx` | guidance | current | current | Event Handover Checklist | current guidance representation; combined file with final-readiness checklist | `INCLUDE` | Active operational handover guidance is valuable contextual knowledge | Checklist / workflow guidance | operational guidance | all confirmed rentals; likely all (`studio_space`, `entire_venue`, `custom_scope`) | rental coordinator; operations; event lead | internal operational guidance; not for broad read | operational requirements; suppliers; technical; service/facilitator; catering | likely indirect only; `requires chunk-level review` | `NO` | checklist; chunk by section / task group / readiness block | handing confirmed rentals over into delivery | combined physical file also represents `TPL-010` | yes: combined logical docs |
| `TPL-010` | Final Readiness Checklist | no separate file; combined into `TPL-009` physical doc | yes via parent file | embedded/combined doc section | guidance | current | current | Final Readiness Checklist | combined logical subdocument | `INCLUDE` | Inventory treats final readiness as distinct operational guidance | Checklist / workflow guidance | operational guidance | all confirmed rentals; likely all (`studio_space`, `entire_venue`, `custom_scope`) | operations; event lead | internal operational guidance; not for broad read | operational requirements; suppliers; technical; service/facilitator; catering | likely indirect only; `requires chunk-level review` | `NO` | checklist; chunk by readiness section / task group | final pre-event operational readiness and missing-item checks | no separate physical file; combined into handover checklist file | yes: combined logical docs |
| `TPL-013` | Rental Close-Out Checklist | `sources/phase-01-03/Checklists + Templates/WNC Rental Close-Out Checklist.docx` | yes | `docx` | guidance | current | current | Rental Close-Out Checklist | current guidance representation | `INCLUDE` | Active close-out guidance belongs in Phase 5 procedural knowledge | Checklist / workflow guidance | operational guidance | all (`studio_space`, `entire_venue`, `custom_scope`) | rental coordinator; finance; operations | internal operational/commercial guidance; not for broad read | cancellation follow-up context; service/facilitator; operational completion; but mostly contextual | none required at document level | `NO` | checklist; chunk by close-out section / task group | post-event reconciliation and operational/financial wrap-up | no major provenance issue | no |
| `HC-AMO-000` | Historical Case Library | `sources/phase-01-03/Historical Cases/WNC Rental Historical Case Library.docx` | yes | `docx` | reference_only | Inventory: `Historical: locate and classify`; source_registry: `historical_reference`; source manifest: explicitly excluded from authoritative activation | historical | WNC Rental Historical Case Library | historical reference source | `DEFER` | Explicitly deferred/historical; useful later for examples but not active Phase 5 corpus | Historical/example material | historical/example material | `RENTAL_APPLICABILITY_REVIEW_REQUIRED` | rental coordinator; operations; management | internal reference; may contain sensitive client/event details; not for broad read | no active deterministic dependency required; some contextual overlap with capacity, ops, suppliers | none required for active corpus | `NO` | narrative cases; later chunk by case / lesson block | future example retrieval, precedent review, lessons learned | explicit later-phase boundary; should not be promoted into active governed knowledge now | yes: deferred to later historical/example phase |

## A. Proposed Active Phase 5 Corpus

Recommended `INCLUDE` logical documents:

- `GOV-001` WNC Rental Knowledge Inventory
- `GOV-002` WNC Rental Policy Decisions & Change Log
- `GOV-003` WNC Rental Data Dictionary
- `CF-001` Updated Rental Lookbook 2026
- `CF-002` Updated Rental Lookbook 2026 current export representation
- `CF-003` Studio Rental Terms
- `CF-005` Full Venue Rental Terms
- `CF-007` WNC Rental Agreement Template
- `OPS-001` WNC Venue Rental Operations Manual
- `OPS-002` WNC Venue Technical & Equipment Inventory
- `OPS-003` WNC Capacity & Space Use Rules
- `SERV-001` WNC Rental Services Catalogue
- `SERV-003` WNC Catering, Beverage & Supplier Catalogue
- `SERV-004` External Supplier Requirements
- `TPL-001` Studio Rental Proposal Template
- `TPL-002` Entire Venue Proposal Template
- `TPL-003` Custom Scope Proposal Template
- `TPL-004` Production Coordination Proposal Template
- `TPL-005` Full Production Proposal Template
- `TPL-006` WNC Rental Email Template Library
- `TPL-007` Discovery Call Checklist
- `TPL-008` Site Visit Checklist
- `TPL-009` Event Handover Checklist
- `TPL-010` Final Readiness Checklist
- `TPL-013` Rental Close-Out Checklist

Counts:

- Included logical documents: `25`
- Included currently available physical source representations: `20`
- Included logical documents without separate local physical files: `5`
  - `CF-001`
  - `OPS-003`
  - `SERV-004`
  - `TPL-008`
  - `TPL-010`
- Obvious document-version / multi-representation families identifiable now: `3` included current families
  - Lookbook (`CF-001` + `CF-002`, though file-format provenance needs review)
  - Studio Terms (`CF-003` + excluded `CF-004`)
  - Full Venue Terms (`CF-005` + excluded `CF-006`)

## B. Deferred Sources

- `GOV-004`: legitimate governance source, but explicitly unverified and non-authoritative.
- `COM-001`: logical commercial workbook is real, but unresolved conflict means it should not enter the active corpus yet.
- `COM-001-XLSM`: conflict-flagged physical representation of the commercial workbook.
- `COM-001-XLSX`: conflict-flagged physical representation of the commercial workbook.
- `SERV-002`: explicitly deferred facilitator catalogue boundary from Phase 4 governance.
- `HC-AMO-000`: historical/example material reserved for later work.

## C. Excluded Sources

- `CF-004`: older Studio Terms export; useful for drift review, but not an active governed document.
- `CF-006`: older Full Venue Terms export; useful for drift review, but not an active governed document.

## D. Proposed Knowledge Category Taxonomy

Only categories supported by the actual corpus are recommended:

### Governance & Canonical Definitions

Justified by:

- `GOV-001`
- `GOV-002`
- `GOV-003`

### Client-Facing Controlled Documents

Justified by:

- `CF-001`
- `CF-002`
- `CF-003`
- `CF-005`
- `CF-007`

### Operational Procedure

Justified by:

- `OPS-001`
- `TPL-007`
- `TPL-008`
- `TPL-009`
- `TPL-010`
- `TPL-013`

### Technical & Venue Reference

Justified by:

- `OPS-002`
- `OPS-003`

### Service & Supplier Guidance

Justified by:

- `SERV-001`
- `SERV-003`
- `SERV-004`

### Proposal Guidance

Justified by:

- `TPL-001`
- `TPL-002`
- `TPL-003`
- `TPL-004`
- `TPL-005`

### Communication Guidance

Justified by:

- `TPL-006`

Not recommended yet as separate active categories:

- FAQ
  - no standalone current FAQ source was found
- staff training material
  - no separate training corpus exists yet beyond manuals/checklists/templates
- facilitator information
  - explicit deferred boundary because `SERV-002` is not active
- event-planning guidance
  - the actual corpus fits better under proposal guidance plus checklist/workflow guidance

## E. Audience Concepts Observed

Recurring audience concepts visible in the corpus:

- WNC Rental Knowledge Owner
- WNC rental point of contact / rental coordinator
- General Manager
- operations
- facilities
- event lead
- finance
- marketing/brand
- client-facing staff
- prospective clients
- confirmed clients
- supplier coordinators

Secondary/mentioned but less central audience concepts:

- external suppliers
- facilitators

## F. Provenance Patterns Observed

### Master / export pairs

- `CF-001` logical lookbook master + `CF-002` current export, but file-format provenance is inconsistent across governance sources.
- `CF-003` Studio Terms master + `CF-004` older export.
- `CF-005` Full Venue Terms master + `CF-006` older export.

### Multiple physical representations of one logical workbook

- `COM-001` logical commercial workbook + `COM-001-XLSM` + `COM-001-XLSX`, with unresolved drift and precedence.

### Embedded logical subdocuments inside one workbook

- `OPS-003` inside `OPS-002`
- `SERV-004` inside `SERV-003`

### Combined logical documents sharing one physical file

- `TPL-007` + `TPL-008`
- `TPL-009` + `TPL-010`

### Missing local physical sources

- `CF-001` editable lookbook master
- `SERV-002` facilitator catalogue

### Standalone current governed sources

- `GOV-001`
- `GOV-002`
- `GOV-003`
- `CF-007`
- `OPS-001`
- `SERV-001`
- `TPL-001`
- `TPL-002`
- `TPL-003`
- `TPL-004`
- `TPL-005`
- `TPL-006`
- `TPL-013`

## G. Phase 4 Connectivity Summary

### Included documents with heavy structured-rule overlap

- `GOV-002`
- `CF-003`
- `CF-005`
- `CF-007`
- `OPS-001`
- `OPS-002`
- `OPS-003`
- `SERV-001`
- `SERV-003`
- `SERV-004`

These are likely to need later stable logical-rule linking and, for some families, careful exact-rule-version handling.

### Included documents that appear primarily contextual or procedural

- `GOV-001`
- `GOV-003`
- `CF-001`
- `CF-002`
- `TPL-001` through `TPL-006`
- `TPL-007`
- `TPL-008`
- `TPL-009`
- `TPL-010`
- `TPL-013`

These are valuable for retrieval even when no exact Phase 4 rule link is required.

### Documents with especially clear stable `rule_code` relationship needs

- `COM-001` family
- `CF-003`
- `CF-005`
- `CF-007`
- `OPS-001`
- `OPS-002`
- `OPS-003`
- `SERV-001`
- `SERV-003`
- `SERV-004`

### Cases where exact historical rule-version relationships may matter

- `CF-004`
- `CF-006`
- `COM-001`
- `COM-001-XLSM`
- `COM-001-XLSX`

Reason:

- older or drifted exports
- unresolved duplicate workbook representations
- document wording that may align to specific historical policy states

### Cases where no direct Phase 4 relationship seems required at document level

- `GOV-001`
- `TPL-006`
- `TPL-013`
- much of the proposal-template family, except where they explicitly discuss governed scope/service concepts

## H. Inputs Required for Task 5.1

The corpus creates these concrete architecture requirements:

- support for **logical documents** distinct from **physical source representations**
- support for **embedded logical subdocuments** inside a single workbook
- support for **combined logical documents** that share one physical file
- support for **missing local physical files** while retaining governed logical records
- support for **many-to-many rental applicability** using existing canonical rental types
- support for a new **audience taxonomy**
- support for a new **confidentiality/access classification**
- support for a compact **knowledge-category taxonomy** grounded in the real corpus
- support for **stable logical-rule relationships** where documents discuss enduring rule concepts
- support for **exact rule-version relationships** where older exports or conflicting workbook variants matter
- support for **provenance review flags** rather than forced normalization
- support for **semantic chunking profiles by document type**
  - governance workbook
  - operational manual
  - technical/reference workbook
  - services/supplier workbook
  - proposal template
  - email template library
  - checklist
- support for **active / deferred / excluded** corpus status
- support for **high structured-truth dependency** flags so retrieval does not treat client-facing or guidance docs as a substitute for Phase 4 deterministic truth

## 3. Key Findings

1. The complete known controlled source set is broader than the Phase 4 `source_registry`.
   The Knowledge Inventory contributes additional logical-source records that Task 5.1 must model.

2. The active Phase 5 corpus should be mostly made of current governance, client-facing masters/current exports, operational manuals, reference workbooks, templates, and checklists.

3. The commercial workbook family is the most important `DEFER` case.
   It is clearly important, but its unresolved provenance and drift should not be silently flattened into the first active corpus release.

4. Current drifted PDF exports of the Studio and Full Venue Terms should not be promoted into the active corpus as separate governed documents.
   They remain useful only for historical comparison and exact-version review.

5. The corpus strongly supports a small practical taxonomy.
   It does not support separate active categories for FAQ, staff training, or facilitator catalogue content yet.

6. Several included sources have substantial Phase 4 overlap and must later be treated as contextual/explanatory companions to deterministic truth, not replacements for it.
