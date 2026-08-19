# Validation Plan

## Goal

Validate the repository foundation and each implemented typed rule domain from Git-controlled files only.

## Validation Layers

### 1. Source validation

- confirm every supplied file exists under `sources/phase-01-03/`
- confirm authority notes match the Knowledge Inventory
- confirm conflicts and ambiguities are documented instead of silently resolved

### 2. Schema validation

- run `npx -y supabase@latest db reset`
- confirm migrations recreate `public`, `api`, and `private`
- confirm foundation tables exist and seed data loads

### 3. Invariant testing

- duplicate `(rule_code, rule_version)` must fail
- invalid `effective_from` / `effective_until` ranges must fail
- self-supersession must fail
- active or superseded rules without provenance must fail at commit
- provenance links must reference valid rules and sources

### 4. Documentation cross-check

- README commands match the actual Supabase setup
- implemented tables match `table-specifications.md`
- seeded canonical values match the Data Dictionary

### 5. Review gate before next slice

Before loading the next typed rule domain:

- confirm the current slice is source-backed and fully tested
- document any unresolved blockers separately from the implemented domain
- keep platform-specific or live-state logic out of the shared rule tables

## Booking-Fee Pilot Validation

For this slice specifically:

- confirm the booking-fee rows align across both supplied workbook variants
- confirm the decision log supports every seeded booking-fee rule
- confirm whole-hour normalization maps `181` minutes and `210` minutes into the `4-hour` Studio Space booking-fee bucket
- confirm the explicit Entire Venue full-day no-fee rule returns a match with `is_fee_charged = false`
- confirm overlap protection rejects ambiguous active duration bands for the same rental type and date window

## Payment-Rule Validation

For this slice specifically:

- confirm the direct-rental payment rows align across both supplied workbook variants
- confirm the decision log supports every seeded payment rule
- confirm the retrieval contract can return multiple stage-specific rules instead of forcing a single winner
- confirm short-notice deadline precedence is represented as non-overlapping `15-29 day` and `0-14 day` lead-time bands
- confirm the `upfront_30` option and the dependent `final_balance` rule are structurally suppressed for `0-14 day` confirmations
- confirm missing `booking_lead_time_days` or `payment_plan_option` suppresses contingent payment rules instead of guessing
- confirm the final-balance rule remains stored as `14 days before event` policy rather than a derived operational due date

## Expedited-Surcharge Validation

For this slice specifically:

- confirm the expedited-surcharge row aligns across both supplied workbook variants
- confirm the decision log supports the trigger window, all-rental-type scope, 10 percent rate, excluded-charge basis, and 21 percent VAT treatment
- confirm the reusable calendar lead-time helper treats `14` days as applicable, `15` days as not applicable, and same-day confirmation as `0`
- confirm missing `confirmation_date` or `event_date` returns `insufficient_information` instead of a guessed applicable surcharge
- confirm `confirmation_date > event_date` raises the documented validation error
- confirm the stored calculation basis remains `venue_rental_only` and does not require a live rental subtotal

## Cancellation Validation

For this slice specifically:

- confirm the pricing workbook pair aligns on the client-cancellation rows and security-deposit treatment used in the typed cancellation table
- confirm the decision log supports the `31+` day and `0-30` day client-cancellation boundaries and the non-refundability of agreed production and production-coordination fees
- confirm the editable Studio and Full Venue terms support the distinct `wnc_cancellation_no_client_breach` and `client_breach_termination` scenarios
- confirm the shared calendar lead-time helper treats `31` days as the refundable rental-payment window, `30` days as the non-refundable rental-payment window, and same-day cancellation as `0`
- confirm missing `cancellation_date` or `event_date` yields `insufficient_information` only for timing-dependent categories, while timing-independent consequences still apply
- confirm the retrieval contract can return multiple category-specific consequences for a single client-cancellation scenario instead of collapsing them into one synthetic refund percentage
- confirm `cancellation_date > event_date` raises the documented validation error
- confirm non-recoverable-cost and valid-deduction outcomes stay structured as manual-review treatments rather than guessed live refund amounts

## Capacity Validation

For this slice specifically:

- confirm the technical inventory capacity rows are loaded only for the approved current scopes and configurations
- confirm the operations manual and agreement template support the whole-venue legal maximum hierarchy and the warning that approved event capacity may still be lower than the legal ceiling
- confirm Studio and Retail capacities stay configuration-aware and are not reduced to one generic space number
- confirm missing required configuration yields `insufficient_information` instead of falling back to another capacity rule
- confirm whole-venue legal maximum is not substituted for Studio or Retail queries
- confirm `must_confirm` and `not_event_capacity_space` rows stay explicit rather than being flattened into fake numeric capacities
- confirm negative guest counts raise the documented validation error
- confirm capacity overlap protection rejects ambiguous active rules for the same scope and configuration

## Space-Access Validation

For this slice specifically:

- confirm the technical inventory and operations manual support every seeded Studio and Entire Venue access rule
- confirm Retail Area and Conversation Pit remain shared during Studio rentals and included during Entire Venue rentals
- confirm Hallway and Bathrooms stay structurally available for access without becoming private event space
- confirm Back Office and Storage Room remain explicit restricted support spaces rather than silently included rooms
- confirm 1:1 / Podcast Room rows preserve default inclusion signals while still retaining setup and preparation nuance
- confirm unresolved `custom_scope` combinations return `no_applicable_rule` instead of default inclusion
- confirm access overlap protection rejects ambiguous active rules for the same rental type and space
- confirm historical space-access versions remain queryable by `as_of_date` and excluded from the current view

## Operational-Requirements Validation

For this slice specifically:

- confirm Studio and Entire Venue grace-period rows return `15` and `30` minutes respectively, with `arrival_departure_only` semantics
- confirm setup-start and early-operational-access rules stay separate so grace time cannot be misread as free setup time
- confirm supplier timing and supplier-responsibility defaults are stored without assuming WNC coordination
- confirm Entire Venue clearing remains conditional and preparation-sensitive rather than silently included
- confirm Storage Room and Back Office operational rules do not contradict the restricted access semantics already implemented in the space-access domain
- confirm installation prohibitions remain prohibited while conditional low-risk methods stay explicit conditional rules
- confirm waste-removal and reset responsibility stay with the client by default unless another scope item is separately included
- confirm professional-cleaning questions return manual review instead of a fabricated threshold
- confirm missing rental type or multi-day context returns `insufficient_information` where the rule scope requires it
- confirm the retrieval surface can return multiple applicable operational rows for one known rental context
- confirm operational overlap protection rejects ambiguous active rules for the same applicability scope
- confirm historical operational versions remain queryable by `as_of_date` and excluded from the current view

## Catering-Supplier Validation

For this slice specifically:

- confirm external caterer arrangements are allowed without implying WNC coordination is included by default
- confirm the current WNC catering-partner path is represented as available but confirmation-sensitive
- confirm tap water and sparkling-water rules stay distinct rather than being flattened into one generic beverage assumption
- confirm external barista or bar-team rules preserve agreement-based machine access and supplier-specific storage or power confirmation needs
- confirm kitchen suitability is limited to ready-made food, warming, plating, and light assembly, while large-scale food production still requires explicit confirmation
- confirm the slice does not duplicate the generic supplier timing, supplier information, or default client supplier responsibility rules already implemented in `operational_requirements`
- confirm catering VAT classification returns `9%` for products, `21%` for coordination or service, and split-line treatment for mixed catering
- confirm missing catering arrangement or VAT category returns `insufficient_information` where the rule family depends on that input
- confirm unseeded arrangements such as `custom` return `no_applicable_rule` instead of inheriting another catering policy
- confirm catering-supplier overlap protection rejects ambiguous active rules for the same arrangement, rule type, context, VAT category, and kitchen-use scope
- confirm historical catering-supplier versions remain queryable by `as_of_date` and excluded from the current view

## Technical Capability Validation

For this slice specifically:

- confirm technical inventory facts remain queryable separately from capability rules
- confirm capability availability and requirement-support rows stay distinct so possession does not imply full support
- confirm the projector and projection-screen facts remain separate and do not collapse into one generic projection promise
- confirm ordinary audio support through Sonos does not imply amplified event sound, microphone support, or DJ capability
- confirm standard Wi-Fi does not imply dedicated livestream support or performance guarantees
- confirm standard venue lighting and production-lighting rules stay distinct
- confirm high-load power remains confirmation-sensitive rather than auto-approved from standard plug access
- confirm request-only inventory and quantity evaluation preserve `requires_confirmation` or `insufficient_quantity` rather than guessed availability
- confirm equipment quantity evaluation does not alter the already authoritative capacity rules
- confirm technical capability overlap protection rejects ambiguous active rules for the same capability or requirement scope
- confirm historical technical capability versions remain queryable by `as_of_date` and excluded from the current view

## Service And Facilitator Validation

For this slice specifically:

- confirm service levels remain separate from service items and do not collapse into one flat vocabulary
- confirm `production_coordination` is treated as a current `service_type`, not promoted to a seeded `service_level`
- confirm `venue_only` remains the standard base service level while `supported_rental` and `full_production` preserve written-scope and manual-quote semantics
- confirm current service items such as `onsite_host`, `facilitator_sourcing`, and `technical_coordination` stay conditional rather than silently included
- confirm `event_manager` remains manual-review scope rather than a fully deterministic responsibility matrix
- confirm `other_service` remains an explicit manual-review path
- confirm client-provided facilitator arrangements remain allowed without silently shifting responsibility to WNC
- confirm WNC-provided and recommendation-requested facilitator arrangements require availability confirmation before commitment
- confirm `none` does not trigger facilitator requirements
- confirm `under_consideration` and `unknown` preserve uncertainty rather than inferring WNC provision
- confirm the slice does not seed the deferred individual `WNC Facilitators & Rental Experiences` catalogue
- confirm the current canonical service vocabulary excludes unapproved `additional_host` machine seeding and documents that gap separately
- confirm service and facilitator overlap protection rejects ambiguous active rules for the same scope and date window
- confirm historical service or facilitator versions remain queryable by `as_of_date` and excluded from the current views
