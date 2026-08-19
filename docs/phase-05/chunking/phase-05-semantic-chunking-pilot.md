# Phase 5 Semantic Chunking Pilot

Date: August 6, 2026

## Summary

This document records the controlled semantic chunking pilot first generated for Task 5.3A and refined in Task 5.3B.

Current follow-up implementation note:

- [5.3b-pilot-refinement-rule-connectivity.md](/Users/serinya/Documents/WNC Rental Automation/docs/phase-05/implementation/5.3b-pilot-refinement-rule-connectivity.md)

Pilot scope:

- pilot governed documents: `4`
- total current chunk sets: `4`
- total current chunks: `82`
- total current chunk traces: `82`
- total stable chunk-rule links: `10`
- total exact chunk-rule links: `0`
- chunking strategy code: `semantic_boundary_first`
- chunking strategy version: `pilot_v1`
- token safeguard: `450` approximate tokens
- oversized splits triggered: `0`

Current parser versions:

- `OPS-001` -> `docx_heading_outline_v1`
- `TPL-006` -> `docx_template_library_v2`
- `TPL-007` -> `docx_checklist_sections_v1`
- `SERV-001` -> `xlsx_service_catalogue_v2`

Pilot documents:

- `OPS-001` WNC Venue Rental Operations Manual
- `TPL-006` WNC Rental Email Template Library
- `TPL-007` Discovery Call Checklist
- `SERV-001` WNC Rental Services Catalogue

The pilot deliberately covers:

1. narrative manual structure
2. checklist/task-group structure
3. reusable template-library structure
4. structured workbook row-group structure

## Selection Rationale

### OPS-001

- governed version: `v1`
- exact extraction source: `sources/phase-01-03/Venue & Operations/WNC Venue Rental Operations Manual.docx`
- parser: `docx_heading_outline`
- parser version: `docx_heading_outline_v1`
- chunking strategy/version: `semantic_boundary_first` / `pilot_v1`
- chunks: `33`
- why chosen: strongest narrative/manual candidate with real heading hierarchy and operational content beyond typed Phase 4 rows
- suitability for later retrieval: `yes, with governance-awareness because the source is still a controlled draft`
- semantic issues: `Wall and beam use` was reviewed in Task 5.3B and intentionally retained as a valid short standalone chunk
- provenance issues: document remains governance draft even though extraction identity is stable

### TPL-006

- governed version: `v1`
- exact extraction source: `sources/phase-01-03/Checklists + Templates/WNC Rental Email Template Library.docx`
- parser: `docx_template_library`
- parser version: `docx_template_library_v2`
- chunking strategy/version: `semantic_boundary_first` / `pilot_v1`
- chunks: `26`
- why chosen: clean template-library structure with strong communication-guidance retrieval value
- suitability for later retrieval: `yes, because internal guidance and client-facing wording are now structurally distinguishable inside each chunk`
- semantic issues: each chunk remains one reusable semantic unit, but Task 5.3B added explicit `INTERNAL GUIDANCE` and `CLIENT-FACING TEMPLATE` boundaries
- provenance issues: no source-identity blocker; broader privacy/access caution from corpus governance still applies

### TPL-007

- governed version: `v1`
- exact extraction source: `sources/phase-01-03/Checklists + Templates/WNC Rental Discovery Call & Site Visit Checklist.docx`
- parser: `docx_checklist_sections`
- parser version: `docx_checklist_sections_v1`
- chunking strategy/version: `semantic_boundary_first` / `pilot_v1`
- chunks: `6`
- why chosen: checklist/workflow candidate with meaningful task-group structure and a real combined-file boundary to prove selective extraction
- suitability for later retrieval: `yes, provided the Discovery Call logical-document boundary remains explicit`
- semantic issues: the top-level discovery block and the final next-action block are both valid but broad
- provenance issues: the same physical file also represents `TPL-008`, but Task 5.3B confirmed that separate governed source links preserve logical document identity while the parser continues excluding the site-visit section

### SERV-001

- governed version: `v1`
- exact extraction source: `sources/phase-01-03/Catalogues/WNC Rental Services Catalogue.xlsm`
- parser: `xlsx_service_catalogue`
- parser version: `xlsx_service_catalogue_v2`
- chunking strategy/version: `semantic_boundary_first` / `pilot_v1`
- chunks: `17`
- why chosen: structured workbook reference source with coherent service rows and controlled-list support values
- suitability for later retrieval: `yes, after removal of the deferred facilitator-catalogue pointer from the derived current chunk`
- semantic issues: `Controlled lists` is lower-value than service-row chunks and may later be demoted to supporting retrieval context
- provenance issues: `facilitator_sourcing` was refined in Task 5.3B so the active chunk no longer points to the deferred `SERV-002` catalogue

## General Review Notes

- All pilot chunks are tied to the exact governed document version and its exact extraction source relationship.
- All pilot chunk sets use one current primary extraction source.
- No excluded extraction representation was used.
- No bulk chunking was run for the other `20` included documents.
- Task 5.3B added `10` stable chunk-level logical-rule links across `OPS-001` and `SERV-001`.
- Task 5.3B intentionally left chunk-level exact-rule-version links at `0` because exact parent evidence is still absent.
- No chunk crossed the `450` token safeguard, so no paragraph-group fallback split was required.

## Chunk Inventory

### OPS-001 — WNC Venue Rental Operations Manual

- `1` `1. How to use this manual` | question: `none` | locator: `Heading path: 1. How to use this manual` | tokens: `145` | covers: source precedence, signed-agreement priority, terms/manual/commercial-rules ordering, and historical-source caution | split: `heading/subheading block` | oversized: `not needed`
- `2` `2. Venue overview` | question: `none` | locator: `Heading path: 2. Venue overview` | tokens: `97` | covers: venue context, live retail/wellness operations, and distinction between core event areas and controlled support rooms | split: `heading/subheading block` | oversized: `not needed`
- `3` `Service levels` | question: `none` | locator: `Heading path: 3. Rental types and service scope > Service levels` | tokens: `25` | covers: distinction between rental type and support/service level | split: `heading/subheading block` | oversized: `not needed`
- `4` `Permits and regulated event activity` | question: `none` | locator: `Heading path: 3. Rental types and service scope > Service levels > Permits and regulated event activity` | tokens: `155` | covers: regulated-event triggers, permit-review timing, and responsibility confirmation before scope finalization | split: `heading/subheading block` | oversized: `not needed`
- `5` `Historical operational lesson` | question: `none` | locator: `Heading path: 3. Rental types and service scope > Service levels > Permits and regulated event activity > Historical operational lesson` | tokens: `51` | covers: historical lesson that late permit/fire-safety/alcohol/sound review creates operational risk | split: `heading/subheading block` | oversized: `not needed`
- `6` `Alcohol` | question: `none` | locator: `Heading path: 3. Rental types and service scope > Service levels > Alcohol` | tokens: `104` | covers: advance alcohol discussion, confirmation questions, and no assumption that private or complimentary service is automatically permitted | split: `heading/subheading block` | oversized: `not needed`
- `7` `Sound and amplified music` | question: `none` | locator: `Heading path: 3. Rental types and service scope > Service levels > Sound and amplified music` | tokens: `105` | covers: normal venue sound scope, DJ/amplified escalation triggers, and external equipment expectations | split: `heading/subheading block` | oversized: `not needed`
- `8` `General access rules` | question: `none` | locator: `Heading path: 4. Rooms, access and restrictions > General access rules` | tokens: `125` | covers: scope-bound room/time access, supplier/client responsibility boundaries, and operational safety override authority | split: `heading/subheading block` | oversized: `not needed`
- `9` `Room restrictions` | question: `none` | locator: `Heading path: 4. Rooms, access and restrictions > Room restrictions` | tokens: `160` | covers: retail-area limitation, 1:1 room nuance, storage/back-office restrictions, and no public-pavement spillover | split: `heading/subheading block` | oversized: `not needed`
- `10` `Standard layout and equipment` | question: `none` | locator: `Heading path: 5. Capacity and standard layout > Standard layout and equipment` | tokens: `156` | covers: normal handover state, standard wellness quantities, confirm-exact-count caveat, and technical inventory as future source of truth | split: `heading/subheading block` | oversized: `not needed`
- `11` `Venue-clearing arrangements` | question: `none` | locator: `Heading path: 6. Venue clearing, Storage Room and Back Office > Venue-clearing arrangements` | tokens: `198` | covers: clearing as separate scope, light host support, reset ownership, and external hallway storage nuance | split: `heading/subheading block` | oversized: `not needed`
- `12` `Storage Room use` | question: `none` | locator: `Heading path: 6. Venue clearing, Storage Room and Back Office > Storage Room use` | tokens: `104` | covers: WNC control of storage, handover specifics, separation of WNC/client goods, and custody caveats | split: `heading/subheading block` | oversized: `not needed`
- `13` `Back Office restrictions` | question: `none` | locator: `Heading path: 6. Venue clearing, Storage Room and Back Office > Back Office restrictions` | tokens: `69` | covers: default back-office restriction, included/limited/excluded states, and pre-use securing requirements | split: `heading/subheading block` | oversized: `not needed`
- `14` `Full rental timeline` | question: `none` | locator: `Heading path: 7. Build-up, breakdown, grace periods and deliveries > Full rental timeline` | tokens: `158` | covers: required timeline completeness, build-up/breakdown inside agreed hours, and multi-day operational ownership detail | split: `heading/subheading block` | oversized: `not needed`
- `15` `Deliveries and collections` | question: `none` | locator: `Heading path: 7. Build-up, breakdown, grace periods and deliveries > Deliveries and collections` | tokens: `113` | covers: default in-window delivery/collection, appointment requirement, and supplier information needed before the event | split: `heading/subheading block` | oversized: `not needed`
- `16` `Appointment-only visits` | question: `none` | locator: `Heading path: 7. Build-up, breakdown, grace periods and deliveries > Appointment-only visits` | tokens: `63` | covers: confirmed-appointment rule for visits outside the rental timeline | split: `heading/subheading block` | oversized: `not needed`
- `17` `Furniture and props` | question: `none` | locator: `Heading path: 8. Furniture, props, walls, beams and signage > Furniture and props` | tokens: `121` | covers: movement restrictions, damage prevention, 1:1 room furniture defaults, and counting rented or borrowed items | split: `heading/subheading block` | oversized: `not needed`
- `18` `Wall and beam use` | question: `none` | locator: `Heading path: 8. Furniture, props, walls, beams and signage > Wall and beam use` | tokens: `15` | covers: spot-testing photograph reminder only; short chunk flagged for review | split: `heading/subheading block` | oversized: `not needed`
- `19` `Signage and exterior restrictions` | question: `none` | locator: `Heading path: 8. Furniture, props, walls, beams and signage > Signage and exterior restrictions` | tokens: `89` | covers: exterior-use prohibition, small-signage approval, and brand-consent requirements | split: `heading/subheading block` | oversized: `not needed`
- `20` `Waste removal` | question: `none` | locator: `Heading path: 9. Waste, cleaning, restricted materials and noise > Waste removal` | tokens: `105` | covers: waste-removal obligations, no abandoned materials, and no quoting historical disposal fees from memory | split: `heading/subheading block` | oversized: `not needed`
- `21` `Cleaning and reset` | question: `none` | locator: `Heading path: 9. Waste, cleaning, restricted materials and noise > Cleaning and reset` | tokens: `136` | covers: client default reset responsibility, catering-cleaning specificity, and additional-cleaning treatment | split: `heading/subheading block` | oversized: `not needed`
- `22` `Restricted materials` | question: `none` | locator: `Heading path: 9. Waste, cleaning, restricted materials and noise > Restricted materials` | tokens: `77` | covers: non-standard materials and installations that require prior written approval | split: `heading/subheading block` | oversized: `not needed`
- `23` `Noise` | question: `none` | locator: `Heading path: 9. Waste, cleaning, restricted materials and noise > Noise` | tokens: `64` | covers: disruption boundary and operational authority to reduce or pause activity | split: `heading/subheading block` | oversized: `not needed`
- `24` `Insurance` | question: `none` | locator: `Heading path: 10. Insurance, incidents and damage reporting > Insurance` | tokens: `69` | covers: client insurance confirmation for larger/full-venue events and limit of WNC venue-insurance scope | split: `heading/subheading block` | oversized: `not needed`
- `25` `Incident response` | question: `none` | locator: `Heading path: 10. Insurance, incidents and damage reporting > Incident response` | tokens: `180` | covers: safety-first incident workflow, evidence capture, witness/client detail capture, and follow-up linkage | split: `heading/subheading block` | oversized: `not needed`
- `26` `Damage and missing items` | question: `none` | locator: `Heading path: 10. Insurance, incidents and damage reporting > Damage and missing items` | tokens: `111` | covers: client responsibility boundary, no premature deduction figure, and close-out counting of missing items | split: `heading/subheading block` | oversized: `not needed`
- `27` `11. Post-event inspection and close-out` | question: `none` | locator: `Heading path: 11. Post-event inspection and close-out` | tokens: `45` | covers: immediate post-breakdown inspection and photo expectation | split: `heading/subheading block` | oversized: `not needed`
- `28` `Close-out actions` | question: `none` | locator: `Heading path: 11. Post-event inspection and close-out > Close-out actions` | tokens: `94` | covers: readiness confirmation, file upload, unresolved-issue tasking, and security-deposit deduction support | split: `heading/subheading block` | oversized: `not needed`
- `29` `12. Open operational decisions` | question: `none` | locator: `Heading path: 12. Open operational decisions` | tokens: `44` | covers: unresolved operational points that remain governed in the decision log and are not final policy | split: `heading/subheading block` | oversized: `not needed`
- `30` `Before confirmation` | question: `none` | locator: `Heading path: Appendix A. Quick operating sequence > Before confirmation` | tokens: `61` | covers: pre-confirmation checklist for scope, risk, and unresolved-policy escalation | split: `heading/subheading block` | oversized: `not needed`
- `31` `Before handover` | question: `none` | locator: `Heading path: Appendix A. Quick operating sequence > Before handover` | tokens: `66` | covers: pre-handover checklist for timeline, rooms, surfaces, and risk documentation | split: `heading/subheading block` | oversized: `not needed`
- `32` `During and after the event` | question: `none` | locator: `Heading path: Appendix A. Quick operating sequence > During and after the event` | tokens: `59` | covers: during-event scope control and post-event documentation/commercial follow-up reminders | split: `heading/subheading block` | oversized: `not needed`
- `33` `Appendix B. Source and governance notes` | question: `none` | locator: `Heading path: Appendix B. Source and governance notes` | tokens: `24` | covers: source-consolidation and governance-note provenance for the manual itself | split: `heading/subheading block` | oversized: `not needed`

### TPL-006 — WNC Rental Email Template Library

- `1` `Library purpose and use principles` | question: `How should the email template library be used?` | locator: `Template library introduction` | tokens: `66` | covers: purpose, tone, and building-block usage principles for the template library | split: `intro guidance block` | oversized: `not needed`
- `2` `New Inquiry Acknowledgement` | question: `How should new inquiry acknowledgement be handled?` | locator: `Template heading: 1. New Inquiry Acknowledgement` | tokens: `183` | covers: first-response acknowledgement with lookbook reference and early-fit language | split: `complete reusable template block` | oversized: `not needed`
- `3` `Initial Information Request / Qualification` | question: `How should initial information request / qualification be handled?` | locator: `Template heading: 2. Initial Information Request / Qualification` | tokens: `200` | covers: qualification request for core details plus a list of relevant-but-not-always-needed fields | split: `complete reusable template block` | oversized: `not needed`
- `4` `Missing Information Request` | question: `How should missing information request be handled?` | locator: `Template heading: 3. Missing Information Request` | tokens: `123` | covers: next-step blocker clarification when one or more missing details prevent progress | split: `complete reusable template block` | oversized: `not needed`
- `5` `Discovery Call Scheduling` | question: `How should discovery call scheduling be handled?` | locator: `Template heading: 4. Discovery Call Scheduling` | tokens: `149` | covers: short-call scheduling when scope is too complex for continued email-only clarification | split: `complete reusable template block` | oversized: `not needed`
- `6` `Site Visit Scheduling` | question: `How should site visit scheduling be handled?` | locator: `Template heading: 5. Site Visit Scheduling` | tokens: `125` | covers: site-visit invitation and option sharing before final layout/logistics decisions | split: `complete reusable template block` | oversized: `not needed`
- `7` `Site Visit Confirmation` | question: `How should site visit confirmation be handled?` | locator: `Template heading: 6. Site Visit Confirmation` | tokens: `119` | covers: simple confirmation of date/time with minimal friendly follow-up language | split: `complete reusable template block` | oversized: `not needed`
- `8` `Availability Confirmation` | question: `How should availability confirmation be handled?` | locator: `Template heading: 7. Availability Confirmation` | tokens: `158` | covers: current-availability language plus internal reminder that availability is not booking confirmation | split: `complete reusable template block` | oversized: `not needed`
- `9` `Proposal Sent` | question: `How should proposal sent be handled?` | locator: `Template heading: 8. Proposal Sent` | tokens: `154` | covers: sending the first tailored proposal with TBC framing and feedback invitation | split: `complete reusable template block` | oversized: `not needed`
- `10` `Proposal Follow-Up` | question: `How should proposal follow-up be handled?` | locator: `Template heading: 9. Proposal Follow-Up` | tokens: `141` | covers: low-pressure follow-up after a sent proposal with room for scope questions or changes | split: `complete reusable template block` | oversized: `not needed`
- `11` `Proposal Revision / Scope Update` | question: `How should proposal revision / scope update be handled?` | locator: `Template heading: 10. Proposal Revision / Scope Update` | tokens: `141` | covers: revised-proposal messaging after requested timing, scope, or guest-count changes | split: `complete reusable template block` | oversized: `not needed`
- `12` `Deposit / Confirmation Payment Request` | question: `How should deposit / confirmation payment request be handled?` | locator: `Template heading: 11. Deposit / Confirmation Payment Request` | tokens: `221` | covers: confirmation-payment request, minimum 30 percent wording, payment link, and terms acceptance statement | split: `complete reusable template block` | oversized: `not needed`
- `13` `Booking Confirmation — Deposit Received` | question: `How should booking confirmation — deposit received be handled?` | locator: `Template heading: 12. Booking Confirmation — Deposit Received` | tokens: `171` | covers: post-payment confirmation language and next-step framing | split: `complete reusable template block` | oversized: `not needed`
- `14` `Agreement Request` | question: `How should agreement request be handled?` | locator: `Template heading: 13. Agreement Request` | tokens: `149` | covers: request for signed agreement after scope/timing/fees are finalized | split: `complete reusable template block` | oversized: `not needed`
- `15` `Balance Payment Reminder` | question: `How should balance payment reminder be handled?` | locator: `Template heading: 14. Balance Payment Reminder` | tokens: `157` | covers: reminder for the remaining balance after a 30 percent deposit route | split: `complete reusable template block` | oversized: `not needed`
- `16` `Final Event Information Request` | question: `How should final event information request be handled?` | locator: `Template heading: 15. Final Event Information Request` | tokens: `187` | covers: last operational details request before the event | split: `complete reusable template block` | oversized: `not needed`
- `17` `Facilitator Confirmation — Client` | question: `How should facilitator confirmation — client be handled?` | locator: `Template heading: 16. Facilitator Confirmation — Client` | tokens: `182` | covers: client-facing facilitator-availability confirmation with coordination framing | split: `complete reusable template block` | oversized: `not needed`
- `18` `External Supplier Information Request` | question: `How should external supplier information request be handled?` | locator: `Template heading: 17. External Supplier Information Request` | tokens: `156` | covers: request for supplier names, timing, and practical details when clients bring external parties | split: `complete reusable template block` | oversized: `not needed`
- `19` `Event Scope & Logistics Recap` | question: `How should event scope & logistics recap be handled?` | locator: `Template heading: 18. Event Scope & Logistics Recap` | tokens: `169` | covers: combined scope/logistics recap after multiple changes or a more complex planning thread | split: `complete reusable template block` | oversized: `not needed`
- `20` `Client No-Response Follow-Up` | question: `How should client no-response follow-up be handled?` | locator: `Template heading: 19. Client No-Response Follow-Up` | tokens: `137` | covers: gentle follow-up when information or a decision is outstanding | split: `complete reusable template block` | oversized: `not needed`
- `21` `Inquiry Postponed / Date Released` | question: `How should inquiry postponed / date released be handled?` | locator: `Template heading: 20. Inquiry Postponed / Date Released` | tokens: `145` | covers: warm release/postponement language before a booking becomes confirmed | split: `complete reusable template block` | oversized: `not needed`
- `22` `Final Event Confirmation` | question: `How should final event confirmation be handled?` | locator: `Template heading: 21. Final Event Confirmation` | tokens: `187` | covers: shortly-before-event confirmation once operational details are complete | split: `complete reusable template block` | oversized: `not needed`
- `23` `Post-Event Thank-You` | question: `How should post-event thank-you be handled?` | locator: `Template heading: 22. Post-Event Thank-You` | tokens: `115` | covers: warm post-event thank-you note | split: `complete reusable template block` | oversized: `not needed`
- `24` `Review Request` | question: `How should review request be handled?` | locator: `Template heading: 23. Review Request` | tokens: `135` | covers: review-request language after a positive event outcome | split: `complete reusable template block` | oversized: `not needed`
- `25` `Cancellation Response — Confirmed Booking` | question: `How should cancellation response — confirmed booking be handled?` | locator: `Template heading: 24. Cancellation Response — Confirmed Booking` | tokens: `302` | covers: empathetic cancellation response for already-confirmed rentals, with policy-sensitive clarity | split: `complete reusable template block` | oversized: `not needed`
- `26` `Decline / Not-Suitable Response` | question: `How should decline / not-suitable response be handled?` | locator: `Template heading: 25. Decline / Not-Suitable Response` | tokens: `172` | covers: respectful decline language when the event is not a fit or cannot be accommodated | split: `complete reusable template block` | oversized: `not needed`

### TPL-007 — Discovery Call Checklist

- `1` `1. Discovery: understand the event` | question: `What should be confirmed about discovery: understand the event?` | locator: `Checklist section: 1. Discovery: understand the event` | tokens: `96` | covers: event objective, format, guest count, date flexibility, guest-facing timeline, and build-up/breakdown basics | split: `checklist section or task group` | oversized: `not needed`
- `2` `Space & layout` | question: `What space and layout details should be confirmed?` | locator: `Checklist section: 1. Discovery: understand the event > Space & layout` | tokens: `61` | covers: studio/entire-venue choice, support-space usage, hallway storage, and layout-clearing requests | split: `checklist section or task group` | oversized: `not needed`
- `3` `Food, beverage & experience` | question: `What food, beverage, and experience details should be confirmed?` | locator: `Checklist section: 1. Discovery: understand the event > Food, beverage & experience` | tokens: `54` | covers: catering path, beverage-service path, and facilitator/experience clarification without overpromising | split: `checklist section or task group` | oversized: `not needed`
- `4` `Production, technical & branding` | question: `What production, technical, and branding details should be confirmed?` | locator: `Checklist section: 1. Discovery: understand the event > Production, technical & branding` | tokens: `76` | covers: service level, technical requirements, branding/installations, and external supplier ownership | split: `checklist section or task group` | oversized: `not needed`
- `5` `Commercial & decision process` | question: `What commercial and decision-process details should be confirmed?` | locator: `Checklist section: 1. Discovery: understand the event > Commercial & decision process` | tokens: `34` | covers: budget, approvers, and proposal deadline | split: `checklist section or task group` | oversized: `not needed`
- `6` `3. Decisions, TBCs & next action` | question: `What should be confirmed about decisions, tbcs & next action?` | locator: `Checklist section: 3. Decisions, TBCs & next action` | tokens: `51` | covers: next action owner/timing plus client and internal follow-up capture | split: `checklist section or task group` | oversized: `not needed`

### SERV-001 — WNC Rental Services Catalogue

- `1` `Venue Only` | question: `What does venue only include?` | locator: `Worksheet "Services catalogue", row 5, service code venue_only` | tokens: `186` | covers: venue-only scope, included basics, excluded responsibilities, pricing method, and owner/approval metadata | split: `service row` | oversized: `not needed`
- `2` `Supported Rental` | question: `What does supported rental include?` | locator: `Worksheet "Services catalogue", row 6, service code supported_rental` | tokens: `141` | covers: supported-rental scope with explicit written deliverables and manual pricing | split: `service row` | oversized: `not needed`
- `3` `Production Coordination` | question: `What does production coordination include?` | locator: `Worksheet "Services catalogue", row 7, service code production_coordination` | tokens: `145` | covers: logistics-focused planning/coordination with clear exclusions and manual quote model | split: `service row` | oversized: `not needed`
- `4` `Full Production` | question: `What does full production include?` | locator: `Worksheet "Services catalogue", row 8, service code full_production` | tokens: `172` | covers: broad creative/sourcing/coordination support with itemization requirement and manual quote treatment | split: `service row` | oversized: `not needed`
- `5` `On-Site Host` | question: `What does on-site host include?` | locator: `Worksheet "Services catalogue", row 9, service code onsite_host` | tokens: `148` | covers: practical venue support, explicit exclusions, and case-specific quoting for host count/hours | split: `service row` | oversized: `not needed`
- `6` `Additional Host` | question: `What does additional host include?` | locator: `Worksheet "Services catalogue", row 10, service code additional_host` | tokens: `137` | covers: extra host support when guest flow/scope/hours require it | split: `service row` | oversized: `not needed`
- `7` `Event Manager` | question: `What does event manager include?` | locator: `Worksheet "Services catalogue", row 11, service code event_manager` | tokens: `151` | covers: on-site flow and coordination responsibility with explicit non-manager exclusions | split: `service row` | oversized: `not needed`
- `8` `Furniture and Equipment Sourcing` | question: `What does furniture and equipment sourcing include?` | locator: `Worksheet "Services catalogue", row 12, service code furniture_equipment_sourcing` | tokens: `143` | covers: sourcing/quote/order coordination and client-approval requirement before commitments | split: `service row` | oversized: `not needed`
- `9` `Catering Coordination` | question: `What does catering coordination include?` | locator: `Worksheet "Services catalogue", row 13, service code catering_coordination` | tokens: `174` | covers: menu/supplier/delivery/service-plan coordination with VAT-sensitive pricing notes and scope clarification requirement | split: `service row` | oversized: `not needed`
- `10` `Facilitator Sourcing` | question: `What does facilitator sourcing include?` | locator: `Worksheet "Services catalogue", row 14, service code facilitator_sourcing` | tokens: `140` | covers: facilitator recommendations and coordination with an explicit reference to the deferred facilitator catalogue boundary | split: `service row` | oversized: `not needed`
- `11` `Experience Design` | question: `What does experience design include?` | locator: `Worksheet "Services catalogue", row 15, service code experience_design` | tokens: `133` | covers: concept/guest-journey development with explicit exclusions and manual quote treatment | split: `service row` | oversized: `not needed`
- `12` `Set-Up Support` | question: `What does set-up support include?` | locator: `Worksheet "Services catalogue", row 16, service code setup_support` | tokens: `140` | covers: practical pre-event layout work with explicit exclusions for heavy/specialist install | split: `service row` | oversized: `not needed`
- `13` `Breakdown and Reset Support` | question: `What does breakdown and reset support include?` | locator: `Worksheet "Services catalogue", row 17, service code breakdown_reset_support` | tokens: `141` | covers: post-event reset support and explicit exclusions for supplier dismantling and deep cleaning | split: `service row` | oversized: `not needed`
- `14` `Cleaning` | question: `What does cleaning include?` | locator: `Worksheet "Services catalogue", row 18, service code cleaning_service` | tokens: `155` | covers: cleaning scope, exclusions, and approximate manual pricing guidance rather than deterministic pricing | split: `service row` | oversized: `not needed`
- `15` `Beverage Package` | question: `What does beverage package include?` | locator: `Worksheet "Services catalogue", row 19, service code beverage_package` | tokens: `151` | covers: beverage package scope, exclusions, and VAT separation reminder for service/coordination | split: `service row` | oversized: `not needed`
- `16` `Technical Coordination` | question: `What does technical coordination include?` | locator: `Worksheet "Services catalogue", row 20, service code technical_coordination` | tokens: `157` | covers: technical planning/coordination beyond standard WNC equipment and explicit external-equipment boundary | split: `service row` | oversized: `not needed`
- `17` `Controlled lists` | question: `What controlled list values support the services catalogue?` | locator: `Worksheet "Controlled lists"` | tokens: `122` | covers: pricing method, VAT treatment, supplier requirement, client approval, and service-status controlled values | split: `controlled list section` | oversized: `not needed`

## Manual Review Outcome

### Coherence

- `OPS-001` chunks are coherent heading-level operational topics.
- `TPL-006` chunks are coherent full reusable templates rather than arbitrary fragments, and internal versus client-sendable text is now explicit.
- `TPL-007` chunks preserve meaningful checklist task groups.
- `SERV-001` chunks preserve coherent service records and one controlled-list support section without activating deferred facilitator-catalogue knowledge.

### Completeness

- All chunks contain enough local context to be understandable without surrounding paragraph windows.
- The shortest chunk is `OPS-001` `Wall and beam use`; Task 5.3B kept it because it is still a genuine standalone operational instruction.

### Separation

- Unrelated operational concepts remain separate in the manual.
- Discovery checklist subsections stay distinct.
- Workbook service rows do not merge across service codes.

### Provenance

- Every chunk has one exact current source trace.
- Every chunk set points back to one exact governed extraction-source relationship.
- The `TPL-007` logical-document boundary is preserved even though the physical file also contains `TPL-008`.

### Governance

- All pilot chunks are attached to the correct governed document version.
- Chunk-level Phase 4 connectivity now exists only as a strict refinement of already-approved document-level governance.
- Narrative/guidance chunks remain contextual knowledge, not deterministic rule truth.

### Retrieval Suitability

- `OPS-001`: suitable after human review of the few sparse or draft-sensitive sections
- `TPL-006`: suitable because the derived chunk now carries explicit internal/client-facing boundaries
- `TPL-007`: suitable with combined-file boundary preserved
- `SERV-001`: suitable with the deferred facilitator reference removed and lower-value controlled-list context still left unlinked

## Status

Next gate:

`PHASE_5_5.3B_PILOT_APPROVAL_REQUIRED`
