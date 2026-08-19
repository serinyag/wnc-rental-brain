# Phase 6 Historical Case Corpus Matrix

Date: August 7, 2026

## 1. Executive Summary

This audit found `9` stable historical precedents in the current Phase 6 corpus: `7` substantial cases and `2` smaller precedents preserved inside the curated historical source `HC-AMO-000`.

Evidence found:

- `9` case-specific primary evidence items inside the historical case library itself
- `0` separate case-named supporting historical artifacts located elsewhere in the repository

Inclusion-status breakdown:

- `READY_FOR_PHASE_6`: `7`
- `READY_WITH_LIMITATIONS`: `2`
- `HOLD_FOR_REVIEW`: `0`
- `EXCLUDE`: `0`

Strongest recurring precedent themes:

- venue clearing and storage sequencing
- explicit responsibility boundaries between WNC, client, and suppliers
- production access, setup timing, and overtime boundaries
- technical assessment for non-standard production requirements
- catering, alcohol, and supplier coordination
- cleaning, residue, and venue-damage risk

Biggest evidence gaps:

- no exact event dates are evidenced for any of the `9` cases
- no case-specific emails, proposals, agreements, handovers, schedules, or quotes were located in-repo
- the corpus is heavily narrative-first rather than artifact-rich
- the two smaller precedents are materially thinner than the seven substantial cases
- ADE remains especially thin on case identity, date, and completion status

Biggest historical/current boundary risks:

- historical commercial values such as the `€300` external-storage arrangement
- named individual capability such as Haylin providing florals
- historical staffing and overtime handling
- historical grace-period application
- historical venue configuration details
- historical compliance solutions, especially for ADE

Confidentiality posture:

- curated narrative risk is mostly `MEDIUM` to `HIGH` commercial sensitivity
- personal information is `CONFIRMED` in some case narratives because named individuals appear
- raw evidence, if later located, would likely be more sensitive than the curated narrative preserved today

Corpus sufficiency finding:

- the corpus is sufficient to proceed to Task `6.1`, but the architecture must explicitly support narrative-only cases, missing dates, historical-value-only facts, and stronger separation between curated case knowledge and any future raw evidence

## 2. Corpus Scope

Primary source inspected:

- `HC-AMO-000` / `WNC Rental Historical Case Library` recorded in [supabase/seed.sql](../../supabase/seed.sql), [docs/phase-04/governance/source-manifest.md](../phase-04/governance/source-manifest.md), and [docs/phase-05/PHASE_5_SOURCE_CORPUS_MATRIX.md](../phase-05/PHASE_5_SOURCE_CORPUS_MATRIX.md)
- physical file verified at [WNC Rental Historical Case Library.docx](/Users/serinya/Documents/WNC%20Rental%20Automation/sources/phase-01-03/Historical%20Cases/WNC%20Rental%20Historical%20Case%20Library.docx)

Supporting sources inspected:

- [PHASE_6_HISTORICAL_CASE_REPOSITORY_DEPENDENCY_AUDIT.md](/Users/serinya/Documents/WNC%20Rental%20Automation/docs/phase-06/PHASE_6_HISTORICAL_CASE_REPOSITORY_DEPENDENCY_AUDIT.md)
- [source-manifest.md](/Users/serinya/Documents/WNC%20Rental%20Automation/docs/phase-04/governance/source-manifest.md)
- [PHASE_5_SOURCE_CORPUS_MATRIX.md](/Users/serinya/Documents/WNC%20Rental%20Automation/docs/phase-05/PHASE_5_SOURCE_CORPUS_MATRIX.md)
- [phase-05-controlled-catalogue-manifest.md](/Users/serinya/Documents/WNC%20Rental%20Automation/docs/phase-05/catalogue/phase-05-controlled-catalogue-manifest.md)
- [supabase/seed.sql](/Users/serinya/Documents/WNC%20Rental%20Automation/supabase/seed.sql)

Search boundaries used:

- exact searches for the known case names and client/event names
- repository/source-record verification of `HC-AMO-000`
- no open-ended search for unrelated historical rentals
- no ingestion of additional historical material

What was deliberately not included:

- unrelated current policy documents as case evidence
- speculative historical rentals not named in the corpus
- open-ended historical archaeology beyond the nine known precedents

Additional candidate cases discovered:

- none

Scope note:

This corpus is historical precedent only. It documents what happened or what WNC learned from past cases. It is not current policy, current pricing, or current operational authority.

## 3. Stable Case Identity Matrix

| Case Code | Case Title | Status | Date Confidence | Event/Rental Type | Evidence Strength | Inclusion Status |
| --- | --- | --- | --- | --- | --- | --- |
| `HC-001` | Merrachi Multi-Day Retail Pop-Up | completed | `UNKNOWN` | multi-day entire-venue brand / retail takeover | strong curated narrative, primary source only | `READY_FOR_PHASE_6` |
| `HC-002` | Philips Coffee Machine Showcase | completed | `UNKNOWN` | brand activation / product showcase | strong curated narrative, primary source only | `READY_FOR_PHASE_6` |
| `HC-003` | WineGB Trade & Press Showcase | completed | `UNKNOWN` | trade / press showcase with production support | strong curated narrative, primary source only | `READY_FOR_PHASE_6` |
| `HC-004` | Amoué PR Wellness Event | completed | `UNKNOWN` | beauty / PR brand event with wellness programming | strong curated narrative, primary source only | `READY_FOR_PHASE_6` |
| `HC-005` | British Embassy / GreenTech Corporate Reception | completed | `UNKNOWN` | corporate networking / reception | strong curated narrative, primary source only | `READY_FOR_PHASE_6` |
| `HC-006` | Sheso Trading Event | completed | `UNKNOWN` | one-day PR / industry activation | strong curated narrative, primary source only | `READY_FOR_PHASE_6` |
| `HC-007` | MOOI / Little Wonderland PR Activation | completed | `UNKNOWN` | whole-venue PR / beauty activation | strong curated narrative, primary source only | `READY_FOR_PHASE_6` |
| `HC-008` | Vanessa Corporate Wellness Outing / Lululemon Branding Requirement | completed | `UNKNOWN` | small corporate wellness rental / branded-company event | brief curated precedent only | `READY_WITH_LIMITATIONS` |
| `HC-009` | ADE Event Permit, Alcohol, Sound & Operational Compliance Precedent | unclear; planning precedent with historical solution referenced | `UNKNOWN` | nightlife-adjacent / higher-impact event planning precedent | brief curated precedent only | `READY_WITH_LIMITATIONS` |

## 4. Evidence Matrix

| Case Code | Evidence Item | Evidence Type | Primary/Secondary | Source Identity | PI Status | Commercial Sensitivity | Later Ingestion Suitability |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `HC-001` | Historical Case Library section: Merrachi Multi-Day Retail Pop-Up | historical case library narrative | primary | `HC-AMO-000`; repository file [WNC Rental Historical Case Library.docx](/Users/serinya/Documents/WNC%20Rental%20Automation/sources/phase-01-03/Historical%20Cases/WNC%20Rental%20Historical%20Case%20Library.docx) | `CONFIRMED` | `HIGH` | suitable as curated case narrative; no separate raw evidence found |
| `HC-002` | Historical Case Library section: Philips Coffee Machine Showcase | historical case library narrative | primary | `HC-AMO-000`; repository file [WNC Rental Historical Case Library.docx](/Users/serinya/Documents/WNC%20Rental%20Automation/sources/phase-01-03/Historical%20Cases/WNC%20Rental%20Historical%20Case%20Library.docx) | `NONE_OBSERVED` | `MEDIUM` | suitable as curated case narrative; no separate raw evidence found |
| `HC-003` | Historical Case Library section: WineGB Trade & Press Showcase | historical case library narrative | primary | `HC-AMO-000`; repository file [WNC Rental Historical Case Library.docx](/Users/serinya/Documents/WNC%20Rental%20Automation/sources/phase-01-03/Historical%20Cases/WNC%20Rental%20Historical%20Case%20Library.docx) | `CONFIRMED` | `HIGH` | suitable as curated case narrative; no separate raw evidence found |
| `HC-004` | Historical Case Library section: Amoué PR Wellness Event | historical case library narrative | primary | `HC-AMO-000`; repository file [WNC Rental Historical Case Library.docx](/Users/serinya/Documents/WNC%20Rental%20Automation/sources/phase-01-03/Historical%20Cases/WNC%20Rental%20Historical%20Case%20Library.docx) | `NONE_OBSERVED` | `HIGH` | suitable as curated case narrative; no separate raw evidence found |
| `HC-005` | Historical Case Library section: British Embassy / GreenTech Corporate Reception | historical case library narrative | primary | `HC-AMO-000`; repository file [WNC Rental Historical Case Library.docx](/Users/serinya/Documents/WNC%20Rental%20Automation/sources/phase-01-03/Historical%20Cases/WNC%20Rental%20Historical%20Case%20Library.docx) | `NONE_OBSERVED` | `MEDIUM` | suitable as curated case narrative; no separate raw evidence found |
| `HC-006` | Historical Case Library section: Sheso Trading Event | historical case library narrative | primary | `HC-AMO-000`; repository file [WNC Rental Historical Case Library.docx](/Users/serinya/Documents/WNC%20Rental%20Automation/sources/phase-01-03/Historical%20Cases/WNC%20Rental%20Historical%20Case%20Library.docx) | `NONE_OBSERVED` | `HIGH` | suitable as curated case narrative; no separate raw evidence found |
| `HC-007` | Historical Case Library section: MOOI / Little Wonderland PR Activation | historical case library narrative | primary | `HC-AMO-000`; repository file [WNC Rental Historical Case Library.docx](/Users/serinya/Documents/WNC%20Rental%20Automation/sources/phase-01-03/Historical%20Cases/WNC%20Rental%20Historical%20Case%20Library.docx) | `NONE_OBSERVED` | `HIGH` | suitable as curated case narrative; no separate raw evidence found |
| `HC-008` | Historical Case Library section: Vanessa Corporate Wellness Outing / Lululemon Branding Requirement | historical case library narrative | primary | `HC-AMO-000`; repository file [WNC Rental Historical Case Library.docx](/Users/serinya/Documents/WNC%20Rental%20Automation/sources/phase-01-03/Historical%20Cases/WNC%20Rental%20Historical%20Case%20Library.docx) | `NONE_OBSERVED` | `MEDIUM` | suitable with limitations; narrative is brief and no support artifacts were found |
| `HC-009` | Historical Case Library section: ADE Event Permit, Alcohol, Sound & Operational Compliance | historical case library narrative | primary | `HC-AMO-000`; repository file [WNC Rental Historical Case Library.docx](/Users/serinya/Documents/WNC%20Rental%20Automation/sources/phase-01-03/Historical%20Cases/WNC%20Rental%20Historical%20Case%20Library.docx) | `NONE_OBSERVED` | `HIGH` | suitable with limitations; useful as precedent warning, not as strong case reconstruction |

## 5. Detailed Case Audits

### HC-001 Merrachi Multi-Day Retail Pop-Up

#### Identity

- Proposed stable case code: `HC-001`
- Source title: `Merrachi Multi-Day Retail Pop-Up`
- Identity assessment: stable and sufficiently specific
- Underlying event count: appears to represent one real rental/takeover
- Identity caveat: none material beyond missing date

#### Status and date

- Status: completed
- Event date/period: not stated
- Date evidence source: `HC-AMO-000` curated narrative only
- Date confidence: `UNKNOWN`

#### Context

- Rental type: multi-day entire-venue brand / retail takeover
- Venue scope: effective whole-venue white-box handover
- Duration: multi-day
- Client operation model: client largely operated independently after handover
- Spaces/context evidenced:
  - full venue
  - former Ice Bath / Storage Room
  - Back Office contents
  - kitchen items
  - offsite storage

#### Responsibility split

WNC responsibilities:

- full clearing of agreed venue areas
- moving WNC stock, furniture, equipment, kitchen items, and Back Office contents out of sight
- preparing the venue for white-box handover
- managing transition from normal WNC operations into rental

Client responsibilities:

- event operation
- drinks team
- cleaning team
- client products and event materials
- day-to-day operation after handover

External supplier responsibilities:

- not separately detailed beyond client-provided teams

Boundary clarity:

- clear and strong

#### Operational complexities

- full venue-clearing plan rather than normal event support
- sequencing clearing around WNC’s last normal operating day
- insufficient onsite storage alone
- progressive offsite storage use
- preserving operational stock until shortly before handover

#### Decisions made

| Historical Decision | Current-Rule Implication | Notes |
| --- | --- | --- |
| WNC cleared the venue and handed over a white-box-style space. | `CURRENT_RULE_EXISTS_CHECK_PHASE_4` | Current clearing/access authority should come from Phase 4 space access and operational requirements, not from this case alone. |
| External storage was used because onsite space was insufficient. | `CURRENT_KNOWLEDGE_EXISTS_CHECK_PHASE_5` | Historical storage method is precedent, not current default policy or pricing. |
| After handover, the client largely ran its own event operations and support teams. | `CURRENT_RULE_EXISTS_CHECK_PHASE_4` | Supports current responsibility-boundary interpretation without becoming policy itself. |

#### Lessons / precedent

Evidence-supported lessons:

- large takeovers need a detailed clearing and moving plan
- clearing must be sequenced around WNC’s last normal operating day
- offsite storage can become necessary when onsite capacity is insufficient
- once fully handed over, a client-run takeover may not require ongoing WNC operational involvement

Analyst inference:

- `INFERRED`: later architecture should separate “handover complexity” from “guest-facing event complexity” because this case is operationally difficult even though WNC did not run the event itself

#### Phase 4 relevance

- `space_access`
  - verified logical rule codes: `ACCESS_ENTIRE_VENUE_STUDIO_INCLUDED`, `ACCESS_ENTIRE_VENUE_RETAIL_INCLUDED`, `ACCESS_ENTIRE_VENUE_ONE_TO_ONE_INCLUDED`
  - relevance: `PRIMARY`
- `operational_requirement`
  - verified logical rule codes: `OPER_ENTIRE_VENUE_CLEARING_REQUIRES_DEFINED_SCOPE`, `OPER_STORAGE_ROOM_OPERATIONAL_STORAGE_CONDITIONAL`
  - relevance: `PRIMARY`
- `service_facilitator`
  - verified logical rule codes: `SERVICE_LEVEL_VENUE_ONLY`
  - relevance: `SECONDARY`

#### Phase 5 relevance

- `CF-005` / Full Venue Rental Terms
- `CF-007` / WNC Rental Agreement Template
- `OPS-002` / WNC Venue Technical & Equipment Inventory
- `TPL-010` / Final Readiness Checklist

#### Historical/current boundary risks

- historical use of the former Ice Bath / Storage Room as a clearing destination: `MEDIUM`
- historical offsite storage practice: `HIGH`
- historical handover model may be mistaken for current default for full takeovers: `MEDIUM`

#### Evidence available

- primary: `HC-AMO-000` curated case narrative
- separate supporting artifacts found in repo: none

#### Missing evidence

- no exact date
- no agreement
- no handover document
- no schedule
- no storage quote/invoice
- no independent confirmation of final clearing timeline

#### Confidentiality / personal-information assessment

- personal information: `CONFIRMED`
- commercial sensitivity: `HIGH`
- rationale:
  - named individual `Patrick`
  - operational-storage and handover details
  - internal stock/furniture movement details

#### Inclusion recommendation

- `READY_FOR_PHASE_6`
- rationale: identity is clear, precedent value is high, and uncertainty is manageable if preserved explicitly

### HC-002 Philips Coffee Machine Showcase

#### Identity

- Proposed stable case code: `HC-002`
- Source title: `Philips Coffee Machine Showcase`
- Identity assessment: stable and sufficiently specific
- Underlying event count: appears to represent one real showcase event

#### Status and date

- Status: completed
- Event date/period: not stated
- Date evidence source: `HC-AMO-000` curated narrative only
- Date confidence: `UNKNOWN`

#### Context

- Rental type: brand activation / product showcase
- Venue scope: substantial production setup with venue changes
- Duration: not stated
- Client operation model: client brought production setup and equipment; WNC handled venue-side preparation and cleaning

#### Responsibility split

WNC responsibilities:

- venue preparation
- agreed venue clearing
- cleaning
- removing agreed venue elements such as rocks
- venue-side operational coordination

Client responsibilities:

- product showcase
- coffee machines and production equipment
- technical production requirements
- production team and suppliers

External supplier responsibilities:

- not separately broken out beyond production team/suppliers

Boundary clarity:

- mostly clear

#### Operational complexities

- high simultaneous electrical demand
- need for qualified technical/electrical assessment
- removal and temporary storage of major venue elements
- high-footfall catering cleanup load

#### Decisions made

| Historical Decision | Current-Rule Implication | Notes |
| --- | --- | --- |
| WNC should not independently validate complex electrical load; client production should bring qualified technical assessment. | `CURRENT_RULE_EXISTS_CHECK_PHASE_4` | Current technical-confirmation rules exist, but the exact historical setup remains precedent only. |
| WNC removed the decorative rocks and stored them in the courtyard before the event. | `NO_CURRENT_RULE_IMPLICATION` | Venue-specific historical logistics, not a standing rule. |
| WNC handled cleaning for the event. | `CURRENT_KNOWLEDGE_EXISTS_CHECK_PHASE_5` | Historical cleaning arrangement does not define today’s default cleaning scope or threshold. |

#### Lessons / precedent

Evidence-supported lessons:

- collect power requirements per machine early
- recommend qualified electrical assessment for heavy-load setups
- major physical venue changes need lead time
- high-footfall catered events can create much more cleaning than expected

Analyst inference:

- `INFERRED`: this case supports separating “technical feasibility confirmation” from “simple venue inventory availability” in future precedent reasoning

#### Phase 4 relevance

- `technical_capability`
  - verified logical rule codes: `TECH_REQ_HIGH_LOAD_POWER_CONFIRM`, `TECH_REQ_CUSTOM_TECH_CONFIRM`
  - relevance: `PRIMARY`
- `operational_requirement`
  - verified logical rule codes: `OPER_PROFESSIONAL_CLEANING_MANUAL_REVIEW`
  - relevance: `PRIMARY`
- `catering_supplier`
  - verified logical rule codes: `CATER_EXTERNAL_CATERER_ALLOWED`
  - relevance: `SECONDARY`

#### Phase 5 relevance

- `OPS-002` / WNC Venue Technical & Equipment Inventory
- `SERV-003` / WNC Catering, Beverage & Supplier Catalogue
- `CF-007` / WNC Rental Agreement Template
- `TPL-008` / Site Visit Checklist

#### Historical/current boundary risks

- historical removal of rocks and courtyard storage: `MEDIUM`
- historical cleaning approach may be mistaken for an automatic WNC cleaning inclusion: `HIGH`
- historical coffee-machine-specific setup may be mistaken for current general technical approval: `MEDIUM`

#### Evidence available

- primary: `HC-AMO-000` curated case narrative
- separate supporting artifacts found in repo: none

#### Missing evidence

- no exact date
- no technical load sheet
- no supplier list
- no cleaning invoice
- no final event schedule

#### Confidentiality / personal-information assessment

- personal information: `NONE_OBSERVED`
- commercial sensitivity: `MEDIUM`
- rationale:
  - equipment, setup, and cleaning lessons are specific but not obviously person-specific in the surviving narrative

#### Inclusion recommendation

- `READY_FOR_PHASE_6`
- rationale: clear identity and strong operational precedent despite missing underlying artifacts

### HC-003 WineGB Trade & Press Showcase

#### Identity

- Proposed stable case code: `HC-003`
- Source title: `WineGB Trade & Press Showcase`
- Identity assessment: stable and sufficiently specific
- Underlying event count: appears to represent one real trade / press event

#### Status and date

- Status: completed
- Event date/period: not stated
- Date evidence source: `HC-AMO-000` curated narrative only
- Date confidence: `UNKNOWN`

#### Context

- Rental type: trade / press showcase
- Venue scope: significant WNC production support
- Duration: not stated
- Client operation model: WNC supported venue and production scope while the client ran the guest-facing event

#### Responsibility split

WNC responsibilities:

- venue preparation and agreed production setup
- furniture/equipment coordination where included
- supplier and delivery coordination
- storage coordination
- venue cleanliness and operational support
- floral arrangements where included

Client responsibilities:

- running the trade showcase
- hosting attendees
- exhibitor activity
- guest-facing event operation

External supplier responsibilities:

- catering and hired production items as applicable

Boundary clarity:

- strong; the case explicitly separates WNC support from guest-facing hosting

#### Operational complexities

- multiple suppliers and deliveries
- advance delivery and storage of large wine volume
- insufficient standard venue storage
- procurement timing and item availability
- physical production setup by WNC

#### Decisions made

| Historical Decision | Current-Rule Implication | Notes |
| --- | --- | --- |
| WNC provided real production coordination and physical setup. | `CURRENT_RULE_EXISTS_CHECK_PHASE_4` | Current service-level and production-coordination concepts exist, but exact case scope remains historical. |
| External bike-storage / hallway storage was hired for `€300` for the day. | `POTENTIAL_CONFLICT_WITH_CURRENT_KNOWLEDGE` | Historical value only; not current pricing or default storage policy. |
| Haylin could provide floral arrangement support where included. | `CURRENT_STATUS_UNKNOWN` | Person-specific historical capability, not a controlled current service promise. |

#### Lessons / precedent

Evidence-supported lessons:

- production coordination can include physical setup, not just emails
- delivery dates and storage needs must be agreed before products arrive
- large-volume deliveries may require extra storage
- clients should be asked how much must be stored, not just whether storage is needed
- sourcing should happen early because items can go out of stock
- WNC support can remain venue/production-focused without turning into guest-facing service

Analyst inference:

- `INFERRED`: this case is a strong precedent for distinguishing “supported rental” from “full production” in later modelling

#### Phase 4 relevance

- `service_facilitator`
  - verified logical rule codes: `SERVICE_LEVEL_SUPPORTED_RENTAL`, `SERVICE_ITEM_PRODUCTION_COORDINATION`, `SERVICE_ITEM_FURNITURE_EQUIPMENT_SOURCING`
  - relevance: `PRIMARY`
- `operational_requirement`
  - verified logical rule codes: `OPER_DELIVERIES_WITHIN_RENTAL_WINDOW`, `OPER_SUPPLIER_INFORMATION_REQUIRED`
  - relevance: `PRIMARY`
- `catering_supplier`
  - verified logical rule codes: `CATER_EXTERNAL_CATERER_ALLOWED`
  - relevance: `SECONDARY`

#### Phase 5 relevance

- `SERV-001` / WNC Rental Services Catalogue
- `SERV-003` / WNC Catering, Beverage & Supplier Catalogue
- `SERV-004` / External Supplier Requirements
- `TPL-007` / Discovery Call Checklist
- `TPL-010` / Final Readiness Checklist

#### Historical/current boundary risks

- historical `€300` external-storage arrangement: `HIGH`
- named individual floral capability: `HIGH`
- historical WNC support scope may be overgeneralized into full current production promise: `MEDIUM`

#### Evidence available

- primary: `HC-AMO-000` curated case narrative
- separate supporting artifacts found in repo: none

#### Missing evidence

- no exact date
- no storage quote
- no production scope document
- no supplier list
- no event schedule

#### Confidentiality / personal-information assessment

- personal information: `CONFIRMED`
- commercial sensitivity: `HIGH`
- rationale:
  - named individual `Haylin`
  - historical commercial/storage detail
  - internal production-support boundaries

#### Inclusion recommendation

- `READY_FOR_PHASE_6`
- rationale: clear identity and strong precedent value despite clear historical-value-only details

### HC-004 Amoué PR Wellness Event

#### Identity

- Proposed stable case code: `HC-004`
- Source title: `Amoué PR Wellness Event`
- Identity assessment: stable and sufficiently specific
- Underlying event count: appears to represent one real PR / wellness event

#### Status and date

- Status: completed
- Event date/period: not stated
- Date evidence source: `HC-AMO-000` curated narrative only
- Date confidence: `UNKNOWN`

#### Context

- Rental type: beauty / PR event with wellness programming
- Venue scope: event plus use of 1:1 / Podcast Room as overflow storage
- Duration: not stated
- Client operation model: WNC did not handle catering

#### Responsibility split

WNC responsibilities:

- venue provision
- practical overflow space through the 1:1 / Podcast Room

Client responsibilities:

- catering decisions
- PR / brand-event operation
- negotiation around commercial terms

External supplier responsibilities:

- catering not handled by WNC; supplier details not preserved

Boundary clarity:

- partial; the case is strongest on lessons rather than a full operational responsibility ledger

#### Operational complexities

- scent conflict between food and sensory brand experience
- use of 1:1 / Podcast Room for bags and overflow storage
- negotiation pressure around exposure, gifts, and reduced venue rate

#### Decisions made

| Historical Decision | Current-Rule Implication | Notes |
| --- | --- | --- |
| Strong-smelling food should be avoided for scent-sensitive beauty/perfume activations. | `CURRENT_KNOWLEDGE_EXISTS_CHECK_PHASE_5` | Useful present-day guidance topic, but not a verified deterministic Phase 4 rule. |
| Upcoming-brand status and gifts/exposure did not automatically justify discounted rental. | `CURRENT_STATUS_UNKNOWN` | Current deterministic discount policy does not exist in Phase 4; preserve as historical commercial judgement. |
| The 1:1 / Podcast Room was used as overflow storage in practice. | `CURRENT_RULE_EXISTS_CHECK_PHASE_4` | Historical use does not override current access/storage rules. |

#### Lessons / precedent

Evidence-supported lessons:

- catering smell should match the intended guest experience
- scent-sensitive activations should avoid strong-smelling food
- WNC should not discount merely because a brand is new or offers exposure/gifts
- collaboration pricing should have a clear strategic reason

Analyst inference:

- `INFERRED`: this case supports storing “event-sensory-fit” as a precedent topic even when no deterministic policy exists

#### Phase 4 relevance

- `space_access`
  - verified logical rule codes: `ACCESS_STUDIO_ONE_TO_ONE_INCLUDED`
  - relevance: `SECONDARY`
- `operational_requirement`
  - verified logical rule codes: no exact overflow-storage logical rule verified
  - relevance: `SECONDARY`
- `catering_supplier`
  - verified logical rule codes: no exact smell-specific rule verified
  - relevance: `PRIMARY`

#### Phase 5 relevance

- `SERV-003` / WNC Catering, Beverage & Supplier Catalogue
- `TPL-006` / WNC Rental Email Template Library
- `TPL-003` / Custom Scope Proposal Template
- `CF-007` / WNC Rental Agreement Template

#### Historical/current boundary risks

- historical discount/collaboration decision may be misread as a fixed current pricing rule: `HIGH`
- historical use of the 1:1 / Podcast Room as overflow may be misread as a default storage entitlement: `MEDIUM`
- scent/catering guidance may be over-generalized beyond sensory events: `MEDIUM`

#### Evidence available

- primary: `HC-AMO-000` curated case narrative
- separate supporting artifacts found in repo: none

#### Missing evidence

- no exact date
- no actual catering menu
- no proposal or pricing negotiation record
- no event schedule
- no documented final responsibility split beyond the narrative summary

#### Confidentiality / personal-information assessment

- personal information: `NONE_OBSERVED`
- commercial sensitivity: `HIGH`
- rationale:
  - discount/collaboration negotiation
  - commercially sensitive decision-making

#### Inclusion recommendation

- `READY_FOR_PHASE_6`
- rationale: strong precedent value; limitations are manageable if commercial-judgement content is clearly marked historical

### HC-005 British Embassy / GreenTech Corporate Reception

#### Identity

- Proposed stable case code: `HC-005`
- Source title: `British Embassy / GreenTech Corporate Reception`
- Identity assessment: stable enough, though dual naming suggests one event with multiple identifying labels
- Underlying event count: appears to represent one real corporate reception

#### Status and date

- Status: completed
- Event date/period: not stated
- Date evidence source: `HC-AMO-000` curated narrative only
- Date confidence: `UNKNOWN`

#### Context

- Rental type: corporate networking / reception
- Venue scope: standing reception with catering, drinks, furniture, and AV planning
- Duration: not stated
- Client operation model: client brought wine; WNC role was venue/support oriented

#### Responsibility split

WNC responsibilities:

- venue
- agreed catering / supplier coordination
- agreed equipment and venue support
- operational guidance

Client responsibilities:

- corporate event content
- guests
- client-provided wine
- client-specific event requirements

External supplier responsibilities:

- implied for catering and AV support, but not fully itemized

Boundary clarity:

- good, especially around supplied versus client-provided elements

#### Operational complexities

- alcohol arrangements
- catering responsibilities
- furniture/equipment requirements
- technical setup
- division between WNC-provided and client-provided elements

#### Decisions made

| Historical Decision | Current-Rule Implication | Notes |
| --- | --- | --- |
| The client brought wine while other venue/service needs were part of planning. | `CURRENT_KNOWLEDGE_EXISTS_CHECK_PHASE_5` | Historical split is useful precedent but not automatically the current default. |
| Responsibility for drinks, supply, and service needed to be explicit. | `CURRENT_RULE_EXISTS_CHECK_PHASE_4` | Aligns with current supplier/service-boundary concepts. |
| Corporate receptions can work at WNC without wellness programming. | `NO_CURRENT_RULE_IMPLICATION` | Historical positioning precedent, not a deterministic rule. |

#### Lessons / precedent

Evidence-supported lessons:

- drinks arrangements need explicit supply and service ownership
- technical requirements should be identified before final handover
- corporate receptions can fit the venue
- responsibility boundaries matter even in relatively straightforward events

#### Phase 4 relevance

- `catering_supplier`
  - verified logical rule codes: `CATER_EXTERNAL_CATERER_ALLOWED`
  - relevance: `PRIMARY`
- `technical_capability`
  - verified logical rule codes: `TECH_REQ_BASIC_PROJECTION_CONFIRM`
  - relevance: `SECONDARY`
- `operational_requirement`
  - verified logical rule codes: `OPER_SUPPLIERS_CLIENT_RESPONSIBILITY`, `OPER_SUPPLIER_INFORMATION_REQUIRED`
  - relevance: `PRIMARY`

#### Phase 5 relevance

- `SERV-003` / WNC Catering, Beverage & Supplier Catalogue
- `SERV-004` / External Supplier Requirements
- `CF-007` / WNC Rental Agreement Template
- `OPS-002` / WNC Venue Technical & Equipment Inventory

#### Historical/current boundary risks

- historical client-provided wine arrangement may be overread as current default beverage policy: `MEDIUM`
- historical equipment/support split may be overread as a standard package: `MEDIUM`

#### Evidence available

- primary: `HC-AMO-000` curated case narrative
- separate supporting artifacts found in repo: none

#### Missing evidence

- no exact date
- no final catering plan
- no AV list
- no agreement or handover checklist

#### Confidentiality / personal-information assessment

- personal information: `NONE_OBSERVED`
- commercial sensitivity: `MEDIUM`
- rationale:
  - event identity and operational arrangements are specific but not person-named in the surviving narrative

#### Inclusion recommendation

- `READY_FOR_PHASE_6`
- rationale: useful and sufficiently clear precedent despite missing underlying case files

### HC-006 Sheso Trading Event

#### Identity

- Proposed stable case code: `HC-006`
- Source title: `Sheso Trading Event`
- Identity assessment: stable and sufficiently specific
- Underlying event count: appears to represent one real one-day activation

#### Status and date

- Status: completed
- Event date/period: not stated
- Date evidence source: `HC-AMO-000` curated narrative only
- Date confidence: `UNKNOWN`

#### Context

- Rental type: one-day PR / industry event
- Venue scope: not a full multi-day white-box clearing like Merrachi
- Duration: one-day event with evening-before build-up
- Client operation model: client kept much of WNC’s furniture/character but brought substantial materials

#### Responsibility split

WNC responsibilities:

- partial venue clearing
- managing visible WNC retail-stock removal needs
- onsite staff presence during build-up

Client responsibilities:

- build-up activity
- event materials
- event operation

External supplier responsibilities:

- external catering and wellness elements are mentioned but not fully itemized

Boundary clarity:

- mixed; the case is especially strong on where the boundary was stressed

#### Operational complexities

- insufficient planned storage
- partial rather than full clearing
- visible retail stock still needed removal
- build-up overran agreed end time
- additional WNC staffing/overtime pressure

#### Decisions made

| Historical Decision | Current-Rule Implication | Notes |
| --- | --- | --- |
| For one-day activations, storage volume must be discussed explicitly, not just whether storage is needed. | `CURRENT_KNOWLEDGE_EXISTS_CHECK_PHASE_5` | Strong current planning guidance value. |
| Build-up hours need a firm end time. | `CURRENT_RULE_EXISTS_CHECK_PHASE_4` | Connects to current setup/access boundary logic. |
| If build-up runs late, additional WNC staffing / overtime should apply. | `CURRENT_STATUS_UNKNOWN` | Historical handling only; deterministic overtime/staffing rules remain unresolved in Phase 4 blockers. |

#### Lessons / precedent

Evidence-supported lessons:

- ask about approximate storage volume
- many one-day activations keep WNC furniture but still need retail-stock clearing
- create a clear storage destination for cleared materials
- build-up hours need a firm end time
- late build-up should not create indefinite WNC onsite obligation

Analyst inference:

- `INFERRED`: later case modelling should allow both “partial clearing” and “full clearing” rather than flattening them into one binary whole-venue concept

#### Phase 4 relevance

- `operational_requirement`
  - verified logical rule codes: `OPER_ENTIRE_VENUE_CLEARING_REQUIRES_DEFINED_SCOPE`, `OPER_SETUP_START_AT_BOOKED_TIME`
  - relevance: `PRIMARY`
- `space_access`
  - verified logical rule codes: `ACCESS_ENTIRE_VENUE_RETAIL_INCLUDED`
  - relevance: `SECONDARY`
- `service_facilitator`
  - verified logical rule codes: no exact overtime/additional-host logical rule verified
  - relevance: `PRIMARY`

#### Phase 5 relevance

- `CF-005` / Full Venue Rental Terms
- `TPL-007` / Discovery Call Checklist
- `TPL-009` / Event Handover Checklist
- `TPL-010` / Final Readiness Checklist
- `SERV-001` / WNC Rental Services Catalogue

#### Historical/current boundary risks

- historical staffing/overtime handling may be mistaken for a current fixed commercial rule: `HIGH`
- historical partial-clearing practice may be mistaken for a default whole-venue setup policy: `MEDIUM`
- historical storage workaround may be mistaken for guaranteed current storage availability: `MEDIUM`

#### Evidence available

- primary: `HC-AMO-000` curated case narrative
- separate supporting artifacts found in repo: none

#### Missing evidence

- no exact date
- no staffing/overtime record
- no storage inventory
- no final schedule
- no supporting commercial record

#### Confidentiality / personal-information assessment

- personal information: `NONE_OBSERVED`
- commercial sensitivity: `HIGH`
- rationale:
  - staffing/overtime handling
  - operational boundary and storage-pressure details

#### Inclusion recommendation

- `READY_FOR_PHASE_6`
- rationale: strong operational precedent; unresolved current commercial implications can be preserved as historical-only

### HC-007 MOOI / Little Wonderland PR Activation

#### Identity

- Proposed stable case code: `HC-007`
- Source title: `MOOI / Little Wonderland PR Activation`
- Identity assessment: stable enough, though dual branding suggests one activation with multiple identifying labels
- Underlying event count: appears to represent one real activation

#### Status and date

- Status: completed
- Event date/period: not stated
- Date evidence source: `HC-AMO-000` curated narrative only
- Date confidence: `UNKNOWN`

#### Context

- Rental type: whole-venue PR / beauty activation
- Venue scope: entire-venue with pre-rental arrival grace period and production styling
- Duration: one-day activation implied
- Client operation model: production-heavy setup with unusual materials

#### Responsibility split

WNC responsibilities:

- venue access
- enforcing time boundaries
- cleanup/reset expectations
- equipment protection

Client responsibilities:

- setup activity
- production materials
- cleanup obligations implied

External supplier responsibilities:

- not separately detailed

Boundary clarity:

- the case exists largely because the boundary was not enforced clearly enough

#### Operational complexities

- grace period treated as setup time
- fake snow residue
- actual equipment damage
- need for explicit build-up/end-time boundaries

#### Decisions made

| Historical Decision | Current-Rule Implication | Notes |
| --- | --- | --- |
| The 30-minute entire-venue grace period is for arrival, not free setup time. | `CURRENT_RULE_EXISTS_CHECK_PHASE_4` | This aligns directly with current grace-period and setup-start rules. |
| Fake snow is not permitted. | `POTENTIAL_CONFLICT_WITH_CURRENT_KNOWLEDGE` | Strong historical lesson, but no exact current fake-snow logical rule was verified in Phase 4. |
| Other residue/damage-prone materials should be discussed in advance. | `CURRENT_KNOWLEDGE_EXISTS_CHECK_PHASE_5` | Strong policy-adjacent guidance but not a fully verified deterministic rule code. |

#### Lessons / precedent

Evidence-supported lessons:

- grace period does not equal setup time
- if extra production time is needed, it must be included in the schedule
- fake snow is prohibited in this historical precedent
- production agencies need explicit timing, materials, and reset boundaries

Analyst inference:

- `INFERRED`: future case modelling should distinguish “access buffer” from “operational setup time” because they are commonly confused in production-heavy rentals

#### Phase 4 relevance

- `operational_requirement`
  - verified logical rule codes: `OPER_ENTIRE_VENUE_GRACE_PERIOD`, `OPER_SETUP_START_AT_BOOKED_TIME`, `OPER_PROFESSIONAL_CLEANING_MANUAL_REVIEW`
  - relevance: `PRIMARY`
- `operational_requirement`
  - verified logical rule codes: no exact fake-snow logical rule verified
  - relevance: `SECONDARY`

#### Phase 5 relevance

- `CF-005` / Full Venue Rental Terms
- `CF-007` / WNC Rental Agreement Template
- `TPL-008` / Site Visit Checklist
- `TPL-010` / Final Readiness Checklist

#### Historical/current boundary risks

- historical fake-snow prohibition may be mistaken for a fully codified current rule when repository evidence currently supports it mainly as precedent: `HIGH`
- historical grace-period misuse could be misread as current allowed practice if not explicitly bounded: `HIGH`
- equipment-damage narrative could imply a general current damages workflow that is not modelled here: `MEDIUM`

#### Evidence available

- primary: `HC-AMO-000` curated case narrative
- separate supporting artifacts found in repo: none

#### Missing evidence

- no exact date
- no damage record
- no cleanup invoice
- no material-approval communications

#### Confidentiality / personal-information assessment

- personal information: `NONE_OBSERVED`
- commercial sensitivity: `HIGH`
- rationale:
  - damage and cleanup failure details
  - production-material restrictions

#### Inclusion recommendation

- `READY_FOR_PHASE_6`
- rationale: strong cautionary precedent with clear operational value

### HC-008 Vanessa Corporate Wellness Outing / Lululemon Branding Requirement

#### Identity

- Proposed stable case code: `HC-008`
- Source title: `Vanessa Corporate Wellness Outing / Lululemon Branding Requirement`
- Identity assessment: useful but thinner than the major cases
- Underlying event count: appears to represent one small corporate wellness rental, though the title combines a person/event label with a brand requirement
- Identity caveat: combined naming should be preserved explicitly later

#### Status and date

- Status: completed
- Event date/period: not stated
- Date evidence source: `HC-AMO-000` smaller-precedent narrative only
- Date confidence: `UNKNOWN`

#### Context

- Rental type: small corporate wellness rental
- Approximate attendance: about `12` guests
- Interaction with normal operations: explicitly intersected with WNC’s class schedule
- Special context: competitor-brand visibility constraint

#### Responsibility split

WNC responsibilities:

- providing unbranded equipment option
- managing class-schedule interaction

Client responsibilities:

- branded-company requirement
- event use and participant-facing experience

External supplier responsibilities:

- not evidenced

Boundary clarity:

- partial; the source is a short precedent note rather than a full case narrative

#### Operational complexities

- competitor-brand restriction
- unbranded equipment need
- coexistence with WNC’s existing class schedule

#### Decisions made

| Historical Decision | Current-Rule Implication | Notes |
| --- | --- | --- |
| WNC confirmed that unbranded equipment could be used. | `CURRENT_STATUS_UNKNOWN` | Historical operational accommodation, not a verified current standing rule. |
| Competitor-brand visibility mattered materially to the client. | `NO_CURRENT_RULE_IMPLICATION` | Client-specific precedent, not a policy rule. |

#### Lessons / precedent

Evidence-supported lessons:

- ask about competitor-brand restrictions for branded-company events
- minor logo/equipment details can matter significantly to the client

Analyst inference:

- `INFERRED`: future case modelling may need a way to store “brand-sensitivity constraints” even when they do not map to Phase 4 rules

#### Phase 4 relevance

- `technical_capability`
  - verified logical rule codes: no exact brand-restriction logical rule verified
  - relevance: `SECONDARY`
- `service_facilitator`
  - verified logical rule codes: no exact branded-corporate-wellness logical rule verified
  - relevance: `SECONDARY`
- `operational_requirement`
  - verified logical rule codes: no exact class-schedule interaction logical rule verified
  - relevance: `PRIMARY`

#### Phase 5 relevance

- `CF-003` / Studio Rental Terms
- `SERV-001` / WNC Rental Services Catalogue
- `TPL-007` / Discovery Call Checklist
- `TPL-006` / WNC Rental Email Template Library

#### Historical/current boundary risks

- historical unbranded-equipment accommodation may be mistaken for a standing product promise: `MEDIUM`
- case-specific competitor-brand restriction may be overgeneralized into policy: `MEDIUM`

#### Evidence available

- primary: `HC-AMO-000` smaller-precedent narrative
- separate supporting artifacts found in repo: none

#### Missing evidence

- no exact date
- no agreement
- no schedule
- no explicit room/rental-type confirmation beyond narrative implication
- no detailed responsibility split beyond the short note

#### Confidentiality / personal-information assessment

- personal information: `NONE_OBSERVED`
- commercial sensitivity: `MEDIUM`
- rationale:
  - branded-client requirements are commercially specific even though the surviving narrative is brief

#### Inclusion recommendation

- `READY_WITH_LIMITATIONS`
- rationale: useful precedent with clear theme, but materially thinner than the major cases

### HC-009 ADE Event Permit, Alcohol, Sound & Operational Compliance Precedent

#### Identity

- Proposed stable case code: `HC-009`
- Source title: `ADE Event: Permit, Alcohol, Sound & Operational Compliance`
- Identity assessment: useful but notably weaker than the other cases
- Underlying event count: likely one ADE-related event/planning context, but the source does not fully establish the final event identity
- Identity caveat: this reads more like a planning/compliance precedent than a fully reconstructed case

#### Status and date

- Status: unclear; planning precedent with historical solution referenced
- Event date/period: not stated
- Date evidence source: `HC-AMO-000` smaller-precedent narrative only
- Date confidence: `UNKNOWN`

#### Context

- Event type: ADE / nightlife-adjacent / higher-impact activation
- Key context: DJs, amplified music, alcohol, fire-safety review, municipal/event requirements
- Completion status: not directly evidenced

#### Responsibility split

WNC responsibilities:

- early permit and compliance check trigger

Client responsibilities:

- not fully specified; likely event-specific operating/compliance responsibilities existed but are not preserved in detail

External supplier responsibilities:

- not evidenced

Boundary clarity:

- weak; this precedent is strongest as a caution, not as a complete responsibility map

#### Operational complexities

- permit/compliance review
- alcohol arrangements
- amplified sound
- DJ setup
- fire-safety considerations
- non-standard event use

#### Decisions made

| Historical Decision | Current-Rule Implication | Notes |
| --- | --- | --- |
| Events involving DJs, amplified music, alcohol, non-standard guest use, or public-space activity should trigger early permit/compliance review. | `CURRENT_KNOWLEDGE_EXISTS_CHECK_PHASE_5` | Strong modern planning relevance, but not a verified deterministic Phase 4 rule. |
| The historical ADE solution is not current legal precedent. | `POTENTIAL_CONFLICT_WITH_CURRENT_KNOWLEDGE` | The source itself warns against policy contamination. |

#### Lessons / precedent

Evidence-supported lessons:

- high-impact/non-standard events need early permit and compliance review
- historical compliance solutions must not be reused without current legal checking

Analyst inference:

- `INFERRED`: later modelling may need a distinct “historical warning/caution” concept separate from a normal operational lesson

#### Phase 4 relevance

- `technical_capability`
  - verified logical rule codes: `TECH_REQ_AMPLIFIED_SOUND_EXTERNAL`, `TECH_REQ_DJ_AUDIO_EXTERNAL`, `TECH_REQ_MICROPHONE_USE_EXTERNAL`
  - relevance: `PRIMARY`
- `operational_requirement`
  - verified logical rule codes: no exact permit/compliance logical rule verified
  - relevance: `PRIMARY`
- `catering_supplier`
  - verified logical rule codes: no exact alcohol/compliance logical rule verified
  - relevance: `SECONDARY`

#### Phase 5 relevance

- `CF-007` / WNC Rental Agreement Template
- `SERV-001` / WNC Rental Services Catalogue
- `TPL-008` / Site Visit Checklist
- `TPL-010` / Final Readiness Checklist

#### Historical/current boundary risks

- historical compliance solution may be mistaken for current legal guidance: `HIGH`
- thin case detail may encourage overreading of a short cautionary note: `MEDIUM`

#### Evidence available

- primary: `HC-AMO-000` smaller-precedent narrative
- separate supporting artifacts found in repo: none

#### Missing evidence

- no exact date
- no confirmed completion status
- no permit record
- no agreement
- no schedule
- no detailed supplier/responsibility map

#### Confidentiality / personal-information assessment

- personal information: `NONE_OBSERVED`
- commercial sensitivity: `HIGH`
- rationale:
  - regulatory/compliance handling is sensitive and could be misused if treated as current guidance

#### Inclusion recommendation

- `READY_WITH_LIMITATIONS`
- rationale: useful as a cautionary historical precedent, but much thinner and more contamination-prone than the major cases

## 6. Phase 4 Relevance Matrix

| Case | Phase 4 Domain | Verified Logical Rule Code(s) | Relevance | Notes |
| --- | --- | --- | --- | --- |
| `HC-001` | space access | `ACCESS_ENTIRE_VENUE_STUDIO_INCLUDED`, `ACCESS_ENTIRE_VENUE_RETAIL_INCLUDED`, `ACCESS_ENTIRE_VENUE_ONE_TO_ONE_INCLUDED` | `PRIMARY` | Whole-venue takeover context |
| `HC-001` | operational requirements | `OPER_ENTIRE_VENUE_CLEARING_REQUIRES_DEFINED_SCOPE`, `OPER_STORAGE_ROOM_OPERATIONAL_STORAGE_CONDITIONAL` | `PRIMARY` | Clearing and storage sequencing |
| `HC-001` | services | `SERVICE_LEVEL_VENUE_ONLY` | `SECONDARY` | Client largely operated event after handover |
| `HC-002` | technical capability | `TECH_REQ_HIGH_LOAD_POWER_CONFIRM`, `TECH_REQ_CUSTOM_TECH_CONFIRM` | `PRIMARY` | Heavy power/production assessment |
| `HC-002` | operational requirements | `OPER_PROFESSIONAL_CLEANING_MANUAL_REVIEW` | `PRIMARY` | High-footfall cleaning implication |
| `HC-002` | catering / suppliers | `CATER_EXTERNAL_CATERER_ALLOWED` | `SECONDARY` | Full catering context present |
| `HC-003` | services | `SERVICE_LEVEL_SUPPORTED_RENTAL`, `SERVICE_ITEM_PRODUCTION_COORDINATION`, `SERVICE_ITEM_FURNITURE_EQUIPMENT_SOURCING` | `PRIMARY` | WNC production-support boundary |
| `HC-003` | operational requirements | `OPER_DELIVERIES_WITHIN_RENTAL_WINDOW`, `OPER_SUPPLIER_INFORMATION_REQUIRED` | `PRIMARY` | Supplier and delivery coordination |
| `HC-004` | catering / suppliers | none verified for scent-specific handling | `PRIMARY` | Strong precedent value but not codified deterministically |
| `HC-004` | space access | `ACCESS_STUDIO_ONE_TO_ONE_INCLUDED` | `SECONDARY` | 1:1 room used as overflow space in practice |
| `HC-004` | operational requirements | none verified for overflow-storage handling | `SECONDARY` | Useful precedent, weak deterministic overlap |
| `HC-005` | catering / suppliers | `CATER_EXTERNAL_CATERER_ALLOWED` | `PRIMARY` | Supplier/catering boundary |
| `HC-005` | technical capability | `TECH_REQ_BASIC_PROJECTION_CONFIRM` | `SECONDARY` | AV planning reference |
| `HC-005` | operational requirements | `OPER_SUPPLIERS_CLIENT_RESPONSIBILITY`, `OPER_SUPPLIER_INFORMATION_REQUIRED` | `PRIMARY` | Responsibility split |
| `HC-006` | operational requirements | `OPER_ENTIRE_VENUE_CLEARING_REQUIRES_DEFINED_SCOPE`, `OPER_SETUP_START_AT_BOOKED_TIME` | `PRIMARY` | Partial clearing and build-up boundary |
| `HC-006` | space access | `ACCESS_ENTIRE_VENUE_RETAIL_INCLUDED` | `SECONDARY` | Visible retail-stock clearing issue |
| `HC-006` | services | none verified for overtime/additional-host charging | `PRIMARY` | Current deterministic gap should remain explicit |
| `HC-007` | operational requirements | `OPER_ENTIRE_VENUE_GRACE_PERIOD`, `OPER_SETUP_START_AT_BOOKED_TIME`, `OPER_PROFESSIONAL_CLEANING_MANUAL_REVIEW` | `PRIMARY` | Grace-period and cleanup boundary |
| `HC-007` | operational requirements | none verified for fake-snow specifically | `SECONDARY` | Strong precedent, not verified as exact current logical rule |
| `HC-008` | operational requirements | none verified for class-schedule interaction | `PRIMARY` | Real precedent, weak deterministic overlap |
| `HC-008` | technical capability | none verified for competitor-brand restriction / unbranded equipment | `SECONDARY` | Historical accommodation only |
| `HC-009` | technical capability | `TECH_REQ_AMPLIFIED_SOUND_EXTERNAL`, `TECH_REQ_DJ_AUDIO_EXTERNAL`, `TECH_REQ_MICROPHONE_USE_EXTERNAL` | `PRIMARY` | Sound/DJ/compliance-adjacent planning |
| `HC-009` | operational requirements | none verified for permit/compliance trigger | `PRIMARY` | Important current gap to preserve |

## 7. Phase 5 Relevance Matrix

| Case | Current Knowledge Area | Verified Document Code | Relationship Rationale |
| --- | --- | --- | --- |
| `HC-001` | full-venue contractual and operational boundary | `CF-005` | Entire-venue access/handover context |
| `HC-001` | confirmed-rental scope and responsibility language | `CF-007` | Handover and scope boundaries |
| `HC-001` | current space and storage context | `OPS-002` | Current venue/storage reality for comparison |
| `HC-001` | current final-readiness process | `TPL-010` | Useful present-day interpretation layer |
| `HC-002` | current technical venue capability | `OPS-002` | Power/capability comparison |
| `HC-002` | catering/supplier guidance | `SERV-003` | Catering and cleaning-context interpretation |
| `HC-002` | confirmed-rental technical responsibility language | `CF-007` | Technical responsibility framing |
| `HC-002` | site-visit / review prompts | `TPL-008` | Early technical review relevance |
| `HC-003` | service-level and production-support scope | `SERV-001` | Supported-rental / production-coordination comparison |
| `HC-003` | supplier and catering guidance | `SERV-003` | Supplier, deliveries, storage-adjacent interpretation |
| `HC-003` | external supplier operating requirements | `SERV-004` | Delivery and supplier-boundary interpretation |
| `HC-003` | intake/discovery prompts | `TPL-007` | Early storage and delivery scoping |
| `HC-004` | catering and supplier guidance | `SERV-003` | Sensory-fit/catering interpretation |
| `HC-004` | communication guidance | `TPL-006` | Client-facing handling of collaboration/discount conversations |
| `HC-004` | custom-scope proposal guidance | `TPL-003` | Useful for non-standard scope framing |
| `HC-005` | catering and beverage guidance | `SERV-003` | Supplier and beverage responsibility context |
| `HC-005` | external supplier operating guidance | `SERV-004` | Clarifies coordination responsibilities |
| `HC-005` | confirmed-rental scope language | `CF-007` | Responsibility split and event requirements |
| `HC-005` | current technical venue reference | `OPS-002` | AV/equipment interpretation |
| `HC-006` | full-venue contractual boundary | `CF-005` | Current whole-venue timing/access interpretation |
| `HC-006` | discovery/intake prompts | `TPL-007` | Storage and scope questions |
| `HC-006` | handover and timing checks | `TPL-009` | Build-up/boundary interpretation |
| `HC-006` | final readiness | `TPL-010` | End-time and operational readiness interpretation |
| `HC-006` | service/support scope | `SERV-001` | Staffing/support comparison |
| `HC-007` | full-venue terms | `CF-005` | Arrival/build-up boundary interpretation |
| `HC-007` | confirmed-rental scope language | `CF-007` | Material/responsibility comparison |
| `HC-007` | site-visit checklist | `TPL-008` | Early material and production review prompts |
| `HC-007` | final readiness | `TPL-010` | Build-up/end-time enforcement comparison |
| `HC-008` | studio rental terms | `CF-003` | Small studio/corporate-wellness context |
| `HC-008` | services catalogue | `SERV-001` | Corporate wellness / facilitator-adjacent context |
| `HC-008` | discovery/intake guidance | `TPL-007` | Branding and equipment questions |
| `HC-008` | client-facing communication guidance | `TPL-006` | Managing special client constraints |
| `HC-009` | rental agreement template | `CF-007` | Current agreement boundary for non-standard events |
| `HC-009` | services catalogue | `SERV-001` | Technical coordination / production-support interpretation |
| `HC-009` | site-visit checklist | `TPL-008` | Early compliance-review prompts |
| `HC-009` | final readiness checklist | `TPL-010` | Readiness/compliance handoff context |

## 8. Historical-Value Risk Register

| ID | Case | Historical Detail | Risk | Why It Could Be Misread | Current Authority To Consult |
| --- | --- | --- | --- | --- | --- |
| `P6-HIST-001` | `HC-001` | Offsite storage was used progressively and specific items were hidden or relocated onsite. | `MEDIUM` | Could be mistaken for a current default clearing/storage playbook. | Phase 4 and Phase 5 |
| `P6-HIST-002` | `HC-002` | Venue rocks were removed and stored in the courtyard before the event. | `MEDIUM` | Old physical-configuration detail could be mistaken for a current available setup. | Phase 5 |
| `P6-HIST-003` | `HC-003` | External bike-storage / hallway storage was hired for `€300` for the day. | `HIGH` | Looks like a current storage price or standard charge. | Phase 4 and Phase 5 |
| `P6-HIST-004` | `HC-003` | Haylin could provide floral arrangements. | `HIGH` | Person-specific capability could be mistaken for a current WNC service promise. | Phase 5 |
| `P6-HIST-005` | `HC-004` | Discount/collaboration was not justified merely by exposure or gifts. | `HIGH` | Could be mistaken for a codified current discount rule even though Phase 4 does not model discounts deterministically. | Phase 4 and Phase 5 |
| `P6-HIST-006` | `HC-006` | Late build-up should trigger additional WNC staffing / overtime charge. | `HIGH` | Overtime/staffing is not currently governed deterministically in Phase 4. | Phase 4 and Phase 5 |
| `P6-HIST-007` | `HC-007` | Grace period was treated as setup time until corrected by lesson learned. | `HIGH` | Users could mistake historical misuse for current allowed practice. | Phase 4 |
| `P6-HIST-008` | `HC-007` | Fake snow is prohibited in the historical lesson. | `HIGH` | Could be mistaken for a fully codified current rule when repo evidence currently supports it primarily as precedent. | Phase 4 and Phase 5 |
| `P6-HIST-009` | `HC-008` | Unbranded equipment was used to satisfy a branded client’s restriction. | `MEDIUM` | Could be mistaken for a standing current product/service feature. | Phase 5 |
| `P6-HIST-010` | `HC-009` | The ADE compliance solution used historically is explicitly not current legal precedent. | `HIGH` | Reusing it as current guidance could produce operational or legal errors. | Phase 4 and Phase 5 |

## 9. Evidence Gaps

Corpus-level acceptable limitations:

- all nine cases currently survive as curated narrative rather than artifact-rich case files
- exact dates are absent throughout the corpus
- most cases do not state precise durations, attendance counts, or final commercial terms

Requires human review later if higher fidelity is needed:

- whether underlying emails, proposals, agreements, schedules, or handovers exist outside the current repo
- whether dual-titled cases such as `HC-005`, `HC-007`, and `HC-008` need canonical naming guidance
- whether ADE should remain a smaller planning precedent or be expanded only if stronger evidence appears

Architecture considerations:

- the corpus contains both “full case” narratives and thinner “small precedent” notes
- the corpus mixes factual description, explicit lessons, and present-day cautionary statements in one artifact
- some useful lessons depend on narrative interpretation rather than structured evidence

Potential exclusion reasons not currently triggered:

- no case is so weak or misleading that exclusion is presently required
- no duplicate distinct case record was discovered

## 10. Confidentiality & Personal-Information Matrix

| Case | PI Risk | Commercial Sensitivity | Raw Evidence Risk | Curated Narrative Risk | Notes |
| --- | --- | --- | --- | --- | --- |
| `HC-001` | `CONFIRMED` | `HIGH` | `HIGH` | `HIGH` | Named individual plus internal clearing/storage operations |
| `HC-002` | `NONE_OBSERVED` | `MEDIUM` | `HIGH` | `MEDIUM` | Technical load and cleanup details would likely be more sensitive in raw files |
| `HC-003` | `CONFIRMED` | `HIGH` | `HIGH` | `HIGH` | Named individual plus commercial storage detail |
| `HC-004` | `NONE_OBSERVED` | `HIGH` | `HIGH` | `HIGH` | Discount/collaboration negotiations are commercially sensitive |
| `HC-005` | `NONE_OBSERVED` | `MEDIUM` | `HIGH` | `MEDIUM` | Corporate event details could be more sensitive in raw correspondence |
| `HC-006` | `NONE_OBSERVED` | `HIGH` | `HIGH` | `HIGH` | Staffing/overtime disputes would likely be more sensitive in raw evidence |
| `HC-007` | `NONE_OBSERVED` | `HIGH` | `HIGH` | `HIGH` | Damage/cleanup/material issues are sensitive even in narrative form |
| `HC-008` | `NONE_OBSERVED` | `MEDIUM` | `MEDIUM` | `MEDIUM` | Brief narrative, but brand-restriction details are still client-specific |
| `HC-009` | `NONE_OBSERVED` | `HIGH` | `HIGH` | `HIGH` | Compliance handling is highly contamination-prone if raw artifacts appear later |

## 11. Candidate Precedent Taxonomy

Corpus-derived recurring precedent topics:

- venue clearing
  - supported by `HC-001`, `HC-002`, `HC-006`
- storage and offsite storage
  - supported by `HC-001`, `HC-003`, `HC-004`, `HC-006`
- responsibility split
  - supported by `HC-001`, `HC-003`, `HC-005`, `HC-006`
- client-operated events
  - supported by `HC-001`, `HC-003`, `HC-005`
- production coordination / support
  - supported by `HC-003`, `HC-005`, `HC-006`, `HC-007`
- technical assessment / electrical load
  - supported by `HC-002`, `HC-005`, `HC-009`
- catering fit and supplier coordination
  - supported by `HC-002`, `HC-004`, `HC-005`
- alcohol and beverage boundaries
  - supported by `HC-005`, `HC-009`
- build-up, access, and overtime boundaries
  - supported by `HC-006`, `HC-007`
- unusual materials, residue, cleanup, and damage
  - supported by `HC-002`, `HC-007`
- brand restrictions / collaboration pressure
  - supported by `HC-004`, `HC-008`
- class-schedule interaction
  - supported by `HC-001`, `HC-008`
- permit and compliance review
  - supported by `HC-009`

## 12. Candidate Structured Case Fields

Recurring information dimensions actually present in the corpus:

- stable case code
- case title
- source section / evidence reference
- case status
- date confidence
- rental/event type
- duration pattern such as one-day or multi-day
- attendance when preserved
- spaces used or operational areas affected
- WNC responsibilities
- client responsibilities
- external supplier responsibilities
- operational complexities
- historical decisions made
- evidence-supported lessons
- analyst-inferred lessons
- Phase 4 relevance
- Phase 5 relevance
- historical/current boundary risks
- evidence availability
- missing evidence
- personal-information risk
- commercial sensitivity
- inclusion recommendation

Dimensions that recur inconsistently but still appear important:

- exact date
- exact attendance
- exact pricing or cost
- final completion evidence
- final handover/close-out evidence
- named individual capability

## 13. Corpus Findings That Constrain Architecture

- one repository source artifact currently contains multiple stable cases
- some cases are full narratives while others are much shorter precedents
- case identity can be stable even when exact dates are absent
- one case can include both factual reconstruction and retrospective lessons in the same source section
- the corpus contains historical-value-only commercial and operational details that must not be treated as current rules
- some cases name individuals, while others contain only organizational names
- one case may relate to multiple current rule domains and multiple current knowledge documents at once
- responsibility split may need three-way handling: WNC, client, and external supplier
- curated narrative may be suitable for inclusion even when no raw artifact set is present
- raw evidence, if added later, may need stricter confidentiality handling than the curated narrative

## 14. Open Questions for Task 6.1

Combined unresolved questions from `6.0A` and the corpus audit:

1. Should one historical library file map to many stable case entities while also preserving the library as a source artifact in its own right?
2. How should Phase 6 distinguish between a full case narrative and a smaller precedent note like `HC-008` or `HC-009`?
3. How should the system represent cases that have clear identity but no exact date?
4. How should the system represent a historical decision that points toward a current rule domain but does not map cleanly to an existing exact logical rule code?
5. How should evidence-supported lessons be distinguished from analyst inference?
6. How should historical-value-only details such as `€300` storage or named staff capability be stored without being mistaken for current policy?
7. How should Phase 6 handle case titles that combine multiple identifying labels, such as `British Embassy / GreenTech` or `MOOI / Little Wonderland`?
8. Should curated case narratives and any future raw evidence use different confidentiality handling and retrieval eligibility?
9. How should cases like ADE, which are highly cautionary but thinly evidenced, be represented without overstating factual confidence?
10. When a case is relevant to both stable logical rules and current knowledge documents, what relationship vocabulary will keep precedent clearly non-authoritative?

## 15. Corpus Readiness Decision

`READY_FOR_6_1`

Reason:

- the corpus contains `9` stable precedents with clear enough identity to constrain architecture design
- no blocker was found that prevents architecture work from beginning
- the major remaining issues are modelling questions about narrative strength, missing dates, confidentiality separation, and historical/current boundary handling rather than corpus insufficiency
