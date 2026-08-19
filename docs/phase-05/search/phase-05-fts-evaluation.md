# Phase 5 FTS Evaluation

Date: August 7, 2026

## Configuration

- PostgreSQL text-search configuration: `english`
- query parser: `websearch_to_tsquery`
- ranking function: `ts_rank_cd`
- weighting:
  - `A`: document title snapshot
  - `B`: section heading, heading path, question label
  - `D`: body text
- searchable corpus surface: `private.current_knowledge_chunks`

## Searchable Corpus

- searchable current documents: `21`
- searchable current chunk sets: `21`
- searchable current chunks: `492`
- top results captured per query: `5`

## Evaluation Summary

- strong: `11`
- partial: `1`
- weak: `0`
- misses: `0`
- obvious successes: `external caterer, site visit, setup and breakdown, projector, client cancellation, supported rental, security deposit, sparkling water, facilitator sourcing, Can we bring an external caterer?, payment due within 14 days`
- weak ranking cases: `payment within 14 days`

## Query Results

### `external caterer`

- expected families: `SERV-003, SERV-004`
- fixture note: Supplier and catering guidance should dominate this exact operational term.
- expected result assessment: `strong`
- assessment detail: Top result SERV-003 is in the expected document family.
- top results:
  - `1` `SERV-003` WNC Catering, Beverage & Supplier Catalogue | section `CB-002 — Client-chosen external caterer` | rank `1.826600` | preview: Catalogue ID: CB-002 Supplier: Client-chosen external caterer Contact: Client / supplier provides Food or beverage type: Food / catering Service ty...
  - `2` `SERV-003` WNC Catering, Beverage & Supplier Catalogue | section `CBR-002 — External caterers` | rank `1.578100` | preview: Rule ID: CBR-002 Topic: External caterers Rule: Clients may bring their own caterer or catering team. Applies when: Client does not use WNC interna...
  - `3` `SERV-004` External Supplier Requirements | section `SUP-TPL-001 — External caterer: TEMPLATE` | rank `1.564550` | preview: Supplier ID: SUP-TPL-001 Supplier / company: External caterer: TEMPLATE Service: Catering / food service Contracting party: Client unless WNC has e...
  - `4` `SERV-003` WNC Catering, Beverage & Supplier Catalogue | section `CBR-011 — External barista / bar team` | rank `0.275238` | preview: Rule ID: CBR-011 Topic: External barista / bar team Rule: Clients may use their own team or an external barista company. Applies when: Client does...
  - `5` `TPL-007` Discovery Call Checklist | section `Food, beverage & experience` | rank `0.141667` | preview: Catering: WNC / Amelie / external caterer / client-provided / not needed Beverage service: WNC bar / client team / external barista / simple self-s...

### `payment within 14 days`

- expected families: `CF-003, CF-005, CF-007, TPL-006`
- fixture note: Current payment timing language appears across client-facing terms, the agreement template, and related communication guidance.
- expected result assessment: `partial`
- assessment detail: Expected code(s) CF-007, CF-003 appear in the top three, but not at rank one.
- top results:
  - `1` `GOV-002` WNC Rental Policy Decisions & Change Log | section `DEC-007 — Confirmation payment for bookings within 14 days` | rank `0.910212` | preview: Decision ID: DEC-007 Topic: Confirmation payment for bookings within 14 days Previous ambiguity: The payment deadline for urgent bookings was not c...
  - `2` `CF-007` WNC Rental Agreement Template | section `7. Fees, payment and security deposit` | rank `0.161765` | preview: The agreed fees, VAT treatment, due dates and payment status are set out in Schedule 3. VAT is applied per line item, rather than as one blended ra...
  - `3` `CF-003` Studio Rental Terms | section `4.1 Short-Notice Bookings` | rank `0.021189` | preview: Bookings made less than 30 days before the rental date: deposit must be paid within 3 days Bookings made within 14 days of the rental date: deposit...
  - `4` `CF-005` Full Venue Rental Terms | section `2. Payment Terms` | rank `0.017452` | preview: You may choose to pay 30% or 100% of the rental fee. If you choose to pay 30%, the remaining 70% balance must be paid two weeks before the event. V...
  - `5` `GOV-002` WNC Rental Policy Decisions & Change Log | section `DEC-006 — Confirmation payment for bookings under 30 days` | rank `0.009030` | preview: Decision ID: DEC-006 Topic: Confirmation payment for bookings under 30 days Previous ambiguity: Last-minute payment deadlines were not separated by...

### `site visit`

- expected families: `TPL-008, TPL-006, TPL-009`
- fixture note: Checklist and communication guidance should outrank unrelated corpora.
- expected result assessment: `strong`
- assessment detail: Top result TPL-008 is in the expected document family.
- top results:
  - `1` `TPL-008` Site Visit Checklist | section `2. Site visit — if applicable` | rank `2.540480` | preview: Use this section only when the client visits the venue. If the physical setup is already clear, do not force every item.
  - `2` `TPL-006` WNC Rental Email Template Library | section `Site Visit Confirmation` | rank `2.352810` | preview: INTERNAL GUIDANCE When to use Once a client has selected a site-visit time. Tone Friendly + simple. Variables {{first_name}} {{site_visit_date}} {{...
  - `3` `TPL-006` WNC Rental Email Template Library | section `Site Visit Scheduling` | rank `2.019130` | preview: INTERNAL GUIDANCE When to use When the client would benefit from seeing the venue before finalising layout, logistics or production requirements. T...
  - `4` `GOV-002` WNC Rental Policy Decisions & Change Log | section `OPEN-009 — Site-visit requirement` | rank `1.751540` | preview: Open ID: OPEN-009 Topic: Site-visit requirement Current ambiguity: There is no controlled trigger for when a site visit is mandatory. Decision requ...
  - `5` `GOV-001` WNC Rental Knowledge Inventory | section `TPL-008 — Site Visit Checklist: combines` | rank `1.542930` | preview: Source ID: TPL-008 Document name: Site Visit Checklist: combines Drive link: combined above Knowledge category: 05: Templates & Checklists Subcateg...

### `setup and breakdown`

- expected families: `TPL-009, CF-007, TPL-001, TPL-002, TPL-003, TPL-004, TPL-005`
- fixture note: Current searchable knowledge cannot rely on OPS-001 because the preserved pilot remains draft and is excluded by the eligibility surface.
- expected result assessment: `strong`
- assessment detail: Top result CF-007 is in the expected document family.
- top results:
  - `1` `CF-007` WNC Rental Agreement Template | section `Agreed responsibility split` | rank `0.005882` | preview: Area: Guest management; WNC responsibility: [ ]; Client responsibility: [ ] Area: Programme / speakers / content; WNC responsibility: [ ]; Client r...
  - `2` `CF-007` WNC Rental Agreement Template | section `4. Access, build-up and breakdown` | rank `0.005556` | preview: The full rental timeline, including deliveries, build-up, client access, guest access, event hours, breakdown and collection, is set out in Schedul...
  - `3` `SERV-001` WNC Rental Services Catalogue | section `Breakdown and Reset Support` | rank `0.005000` | preview: Service code: breakdown_reset_support Display name: Breakdown and Reset Support Description: Practical WNC labour after the event to return agreed...
  - `4` `CF-003` Studio Rental Terms | section `7.1 Access & Early Entry` | rank `0.002703` | preview: Access to the studio is strictly limited to the confirmed rental period. Setup, unloading, deliveries, furniture movement, technical installation a...

### `projector`

- expected families: `OPS-002, TPL-009, SERV-001`
- fixture note: Technical inventory should normally dominate named venue-equipment queries.
- expected result assessment: `strong`
- assessment detail: Top result OPS-002 is in the expected document family.
- top results:
  - `1` `OPS-002` WNC Venue Technical & Equipment Inventory | section `ST-008 — Projection` | rank `0.200000` | preview: Item ID: ST-008 Category: Projection Feature / item: Basic projector Quantity / specification: 1 basic projector Status: available_on_request Inclu...
  - `2` `OPS-002` WNC Venue Technical & Equipment Inventory | section `TC-002 — Projection` | rank `0.200000` | preview: Capability ID: TC-002 Area: Projection Capability: Basic projector Owned / installed specification: 1 basic projector Status: available_on_request...
  - `3` `SERV-001` WNC Rental Services Catalogue | section `Technical Coordination` | rank `0.200000` | preview: Service code: technical_coordination Display name: Technical Coordination Description: Planning and coordination of technical requirements beyond W...
  - `4` `CF-007` WNC Rental Agreement Template | section `Equipment and setup` | rank `0.100000` | preview: Item: Yoga mats; Quantity / status: [ ]; Setup / condition: [ ] Item: Meditation cushions; Quantity / status: [ ]; Setup / condition: [ ] Item: Eye...
  - `5` `CF-007` WNC Rental Agreement Template | section `Technical and installation requirements` | rank `0.100000` | preview: Requirement: Sound / microphones; WNC provides: [ ]; Client / supplier provides: [ ]; Approval / testing notes: [ ] Requirement: Projector / displa...

### `client cancellation`

- expected families: `CF-003, CF-005, TPL-006, CF-007`
- fixture note: Chunk search does not include the Phase 4 deterministic cancellation tables, so current chunked guidance is the relevant baseline.
- expected result assessment: `strong`
- assessment detail: Top result CF-007 is in the expected document family.
- top results:
  - `1` `CF-007` WNC Rental Agreement Template | section `8. Cancellation, additional costs and overtime` | rank `0.267993` | preview: If the Client cancels more than 30 days before the rental, rental payments received are refundable except for the booking fee, agreed production or...
  - `2` `TPL-006` WNC Rental Email Template Library | section `Cancellation Response — Confirmed Booking` | rank `0.097714` | preview: INTERNAL GUIDANCE When to use When a client asks to cancel a rental that has already been confirmed through payment. Tone Empathetic + clear + firm...
  - `3` `GOV-002` WNC Rental Policy Decisions & Change Log | section `DEC-028 — Facilitator cancellation charge trigger` | rank `0.092262` | preview: Decision ID: DEC-028 Topic: Facilitator cancellation charge trigger Previous ambiguity: It was unclear when class cancellation costs should be char...
  - `4` `CF-005` Full Venue Rental Terms | section `7. Cancellation Policy` | rank `0.027079` | preview: More than 30 days before the rental date: Rental payments received will be refunded, excluding the flat booking fee and any production or productio...
  - `5` `CF-003` Studio Rental Terms | section `4.2 Late Confirmation & Class Cancellations` | rank `0.026786` | preview: When Nature Calls operates as an active wellness studio with a fixed class schedule. We guarantee payment to facilitators for scheduled classes wit...

### `supported rental`

- expected families: `SERV-001`
- fixture note: This is an exact current service-catalogue term.
- expected result assessment: `strong`
- assessment detail: Top result SERV-001 is in the expected document family.
- top results:
  - `1` `SERV-001` WNC Rental Services Catalogue | section `Supported Rental` | rank `1.959480` | preview: Service code: supported_rental Display name: Supported Rental Description: Venue rental with one or more specifically agreed WNC support services a...
  - `2` `SERV-003` WNC Catering, Beverage & Supplier Catalogue | section `CBR-003 — Included bar staffing` | rank `0.144124` | preview: Rule ID: CBR-003 Topic: Included bar staffing Rule: Every rental includes two WNC hosts for agreed operational support or drink service during the...
  - `3` `CF-007` WNC Rental Agreement Template | section `Agreement overview` | rank `0.109091` | preview: WHEN NATURE CALLS Rental Agreement [CLIENT / EVENT NAME] [EVENT DATE OR DATE RANGE] Thank you for choosing When Nature Calls. This agreement brings...
  - `4` `GOV-001` WNC Rental Knowledge Inventory | section `SERV-001 — WNC Rental Services Catalogue` | rank `0.102128` | preview: Source ID: SERV-001 Document name: WNC Rental Services Catalogue Drive link: https://docs.google.com/spreadsheets/d/1LJ-s9VXR45aA-VJ2sh7nofQnNs4koq...
  - `5` `TPL-007` Discovery Call Checklist | section `Production, technical & branding` | rank `0.100000` | preview: Production level: Venue only / supported rental / production coordination / full production / TBC Technical requirements: Projector, screen, microp...

### `security deposit`

- expected families: `CF-007, TPL-013, CF-005`
- fixture note: Agreement, close-out, and full-venue terms are the most likely current chunk families.
- expected result assessment: `strong`
- assessment detail: Top result CF-007 is in the expected document family.
- top results:
  - `1` `CF-007` WNC Rental Agreement Template | section `Security deposit and inspection` | rank `1.820000` | preview: Security deposit amount: [€ / None] Return period: [ ] working days after inspection Inspection owner / date: [ ] Agreed deduction basis: Damage, m...
  - `2` `GOV-002` WNC Rental Policy Decisions & Change Log | section `DEC-024 — Security-deposit refund deductions` | rank `1.624450` | preview: Decision ID: DEC-024 Topic: Security-deposit refund deductions Previous ambiguity: Permitted deductions were not consolidated into one rule. Final...
  - `3` `GOV-002` WNC Rental Policy Decisions & Change Log | section `DEC-030 — Security deposit: studio` | rank `1.570000` | preview: Decision ID: DEC-030 Topic: Security deposit: studio Previous ambiguity: Historical studio deposits varied. Final decision: The standard security d...
  - `4` `GOV-002` WNC Rental Policy Decisions & Change Log | section `DEC-033 — Security deposit: custom scope` | rank `1.538310` | preview: Decision ID: DEC-033 Topic: Security deposit: custom scope Previous ambiguity: There was no controlled method for unusual rental risk. Final decisi...
  - `5` `GOV-002` WNC Rental Policy Decisions & Change Log | section `DEC-031 — Security deposit: one-day entire venue` | rank `1.510000` | preview: Decision ID: DEC-031 Topic: Security deposit: one-day entire venue Previous ambiguity: Historical one-day deposits varied. Final decision: The stan...

### `sparkling water`

- expected families: `SERV-003`
- fixture note: Beverage catalogue guidance should win this exact product query.
- expected result assessment: `strong`
- assessment detail: Top result SERV-003 is in the expected document family.
- top results:
  - `1` `SERV-003` WNC Catering, Beverage & Supplier Catalogue | section `CBR-010 — Sparkling water` | rank `1.827020` | preview: Rule ID: CBR-010 Topic: Sparkling water Rule: Sparkling water is not included. Clients may bring their own or WNC may source it when appropriate. A...
  - `2` `SERV-003` WNC Catering, Beverage & Supplier Catalogue | section `CB-005 — Client-supplied or externally sourced` | rank `0.303374` | preview: Catalogue ID: CB-005 Supplier: Client-supplied or externally sourced Contact: Client / supplier provides Food or beverage type: Sparkling water Ser...

### `facilitator sourcing`

- expected families: `SERV-001, TPL-006`
- fixture note: Service catalogue and communication guidance both contain current facilitator wording.
- expected result assessment: `strong`
- assessment detail: Top result SERV-001 is in the expected document family.
- top results:
  - `1` `SERV-001` WNC Rental Services Catalogue | section `Facilitator Sourcing` | rank `1.754290` | preview: Service code: facilitator_sourcing Display name: Facilitator Sourcing Description: Identifying, recommending and coordinating a facilitator or priv...
  - `2` `GOV-001` WNC Rental Knowledge Inventory | section `SERV-002 — WNC Facilitators & Rental Experiences` | rank `0.156611` | preview: Source ID: SERV-002 Document name: WNC Facilitators & Rental Experiences Drive link: TBC Knowledge category: 04: Services, Suppliers & Facilitators...
  - `3` `GOV-002` WNC Rental Policy Decisions & Change Log | section `DEC-052 — Full production scope` | rank `0.150000` | preview: Decision ID: DEC-052 Topic: Full production scope Previous ambiguity: The distinction between coordination and creative/on-site production was uncl...
  - `4` `SERV-001` WNC Rental Services Catalogue | section `Full Production` | rank `0.103571` | preview: Service code: full_production Display name: Full Production Description: Broad creative, sourcing, coordination and on-site production support tail...
  - `5` `OPS-003` WNC Capacity & Space Use Rules | section `ACC-009 — Entire Venue rental` | rank `0.020000` | preview: Access ID: ACC-009 Rental type: Entire Venue rental Space: 1:1 / Podcast Room Access status: included Exclusive or shared: Exclusive to client Incl...

### `Can we bring an external caterer?`

- expected families: `SERV-003, SERV-004`
- fixture note: This is a natural-language query intended to show the English web-search parser baseline.
- expected result assessment: `strong`
- assessment detail: Top result SERV-003 is in the expected document family.
- top results:
  - `1` `SERV-003` WNC Catering, Beverage & Supplier Catalogue | section `CBR-002 — External caterers` | rank `0.025000` | preview: Rule ID: CBR-002 Topic: External caterers Rule: Clients may bring their own caterer or catering team. Applies when: Client does not use WNC interna...
  - `2` `TPL-006` WNC Rental Email Template Library | section `External Supplier Information Request` | rank `0.022975` | preview: INTERNAL GUIDANCE When to use When a client is bringing their own caterer, barista, production partner or other external supplier. Tone Helpful + p...
  - `3` `SERV-003` WNC Catering, Beverage & Supplier Catalogue | section `CB-005 — Client-supplied or externally sourced` | rank `0.002924` | preview: Catalogue ID: CB-005 Supplier: Client-supplied or externally sourced Contact: Client / supplier provides Food or beverage type: Sparkling water Ser...
  - `4` `SERV-003` WNC Catering, Beverage & Supplier Catalogue | section `CB-006 — Client team / external barista company` | rank `0.000901` | preview: Catalogue ID: CB-006 Supplier: Client team / external barista company Contact: Client / supplier provides Food or beverage type: Coffee / bar servi...

### `payment due within 14 days`

- expected families: `CF-003, CF-005, CF-007, TPL-006`
- fixture note: Natural phrasing should still find current payment-timing language without embeddings.
- expected result assessment: `strong`
- assessment detail: Top result CF-007 is in the expected document family.
- top results:
  - `1` `CF-007` WNC Rental Agreement Template | section `7. Fees, payment and security deposit` | rank `0.157311` | preview: The agreed fees, VAT treatment, due dates and payment status are set out in Schedule 3. VAT is applied per line item, rather than as one blended ra...
  - `2` `CF-005` Full Venue Rental Terms | section `2. Payment Terms` | rank `0.003513` | preview: You may choose to pay 30% or 100% of the rental fee. If you choose to pay 30%, the remaining 70% balance must be paid two weeks before the event. V...

## Baseline Findings

- FTS handles exact governed terminology, named services, concrete equipment nouns, and repeated operational phrases well.
- Natural-language phrasing is usable because `websearch_to_tsquery` tolerates ordinary questions better than raw `to_tsquery` syntax.
- Search quality is still bounded by the governed current chunk surface. For example, preserved draft chunk sets such as `OPS-001` remain intentionally excluded from current search even though they contain useful operational prose.
- Queries that depend on synonymy, policy inference, or cross-document reasoning still show the expected semantic gap that later embedding work can evaluate against this baseline.

## Likely Semantic-Search Follow-Ups

- paraphrases that do not reuse governed vocabulary directly
- policy questions that require combining multiple chunks across document families
- requests whose best answer lives in current deterministic Phase 4 rule tables rather than in chunked narrative knowledge
- nuanced operational questions where relevant evidence is split between checklists, catalogues, and client-facing terms

