# WNC Rental Brain

`wnc-rental-brain` is the greenfield repository for the When Nature Calls rental knowledge system.

The current repository state implements the completed Phase 4 through Phase 7 foundation:

- controlled source preservation for approved Phase 1-3 assets
- governance and architecture documentation for structured rental rules
- Supabase CLI project setup
- foundation database migrations, conservative seed data, and invariant tests
- implemented `booking_fee_rules` storage, retrieval, provenance, and pgTAP coverage
- implemented `payment_rules` storage, retrieval, provenance, and pgTAP coverage
- implemented `expedited_surcharge_rules` storage, retrieval, provenance, and pgTAP coverage
- implemented `cancellation_rules` storage, retrieval, provenance, and pgTAP coverage
- implemented `capacity_rules` storage, retrieval, provenance, and pgTAP coverage
- implemented `space_access_rules` storage, retrieval, provenance, and pgTAP coverage
- implemented `operational_requirements` storage, retrieval, provenance, and pgTAP coverage
- implemented `catering_supplier_rules` storage, retrieval, provenance, and pgTAP coverage
- implemented `technical_capability_rules` plus `technical_equipment_inventory` storage, retrieval, provenance, and pgTAP coverage
- implemented `service_rules` and `facilitator_requirement_rules` storage, retrieval, provenance, and pgTAP coverage
- implemented Phase 5 governed knowledge chunking, hybrid retrieval, and retrieval evaluation
- implemented Phase 6 governed historical precedent ingestion, retrieval, and contamination-aware historical search
- implemented Phase 7 authority-aware reasoning, context safety, bounded answer generation, and one live bounded OpenAI answer adapter

It does not yet implement a production web app, downstream workflow orchestration, autonomous agents, unrestricted RAG, CRM/email/calendar actions, or external workflow tooling.

## Current Phase

Phase 7 is complete.

Current top-level statuses:

- `PHASE_7_COMPLETE`
- `PHASE_7_READY_FOR_DOWNSTREAM_USE`

The repository now provides:

- Phase 4 deterministic current rule truth
- Phase 5 current governed knowledge retrieval
- Phase 6 historical precedent retrieval
- Phase 7 authority-aware reasoning, contamination handling, confidentiality-safe projection, bounded live-model synthesis, and deterministic answer validation

The live repository does not define an exact post-Phase-7 phase name.

## Repository Layout

```text
.
├── README.md
├── .env.example
├── .gitignore
├── docs/
│   ├── phase-04/
│   ├── phase-05/
│   ├── phase-06/
│   └── phase-07/
├── sources/
│   └── phase-01-03/
├── tools/
│   ├── phase_05_search/
│   ├── phase_06_search/
│   └── phase_07_reasoning/
└── supabase/
    ├── config.toml
    ├── migrations/
    ├── tests/
    └── seed.sql
```

## Source Documents

Approved source files are preserved without modification under `sources/phase-01-03/`. The source review, authority notes, and Phase 4 relevance map live under `docs/phase-04/governance/` and `docs/phase-04/requirements/`.

## Prerequisites

- Docker Desktop or another working Docker runtime
- Node.js and `npm` for running the Supabase CLI via `npx`, or a separately installed Supabase CLI
- Git

The repository was initialized and validated with `supabase` CLI `2.111.0` on Monday, August 3, 2026.

## Local Development

Start local Supabase services:

```bash
npx -y supabase@latest start
```

Rebuild the local database from migrations and seed data:

```bash
npx -y supabase@latest db reset
```

Run database tests:

```bash
npx -y supabase@latest test db
```

Create a new migration:

```bash
npx -y supabase@latest migration new short_description
```

Create or update local secrets for semantic tooling:

```bash
python3 tools/setup_local_env.py
```

Non-interactive example:

```bash
python3 tools/setup_local_env.py --openai-api-key "your-key-here"
```

Stop local services:

```bash
npx -y supabase@latest stop
```

## Local Secrets

Semantic tooling reads `OPENAI_API_KEY` from the live shell environment first, then `.env.local`, then `.env`.

Recommended local setup:

1. Run `python3 tools/setup_local_env.py`.
2. Enter the OpenAI key when prompted, or pass `--openai-api-key`.
3. Keep the generated `.env.local` file uncommitted.

The repository already ignores `.env.local` through `.gitignore`.

## Supabase Workflow

This repository follows a migration-first workflow:

1. Update requirements and governance docs when the policy changes.
2. Add or revise migration SQL.
3. Reset the local database from scratch.
4. Run database tests.
5. Review documentation, seed data, and source provenance before release.

No manual production-only schema changes should be introduced outside migrations.

## What Is Implemented

- The approved public/client-facing Phase 4 read contract is the granted `public.current_*` view surface.
- Phase 4 `api.*` retrieval and evaluation functions currently exist for internal or owner-context database use and are not the approved public client contract at this stage.
- `public`, `api`, and `private` PostgreSQL schema boundaries
- canonical seed tables for rental types and venue spaces
- source registry and rule-governance foundation tables
- provenance links between rules and controlled sources
- the `public.booking_fee_rules` typed rule table
- the `public.current_booking_fee_rules` view and `api.get_booking_fee_rule(...)` retrieval function
- seeded current approved booking fee rules with primary, governance, and supporting provenance
- the `public.payment_rules` typed rule table
- the `public.current_payment_rules` view and `api.get_payment_rules(...)` retrieval function
- seeded current approved direct-rental payment rules with primary, governance, and supporting provenance
- the `public.expedited_surcharge_rules` typed rule table
- the `public.current_expedited_surcharge_rules` view and `api.get_expedited_surcharge_rule(...)` retrieval function
- seeded current approved expedited surcharge rules with primary, governance, and supporting provenance
- the `public.cancellation_rules` typed rule table
- the `public.current_cancellation_rules` view and `api.get_cancellation_rules(...)` retrieval function
- seeded current approved cancellation rules with primary, governance, and supporting provenance where the approved source set provides them
- the `public.capacity_rules` typed rule table
- the `public.current_capacity_rules` view plus `api.get_capacity_rule(...)` and `api.evaluate_capacity(...)` retrieval functions
- seeded current approved capacity rules with primary and supporting provenance from the technical inventory and operations sources
- the `public.space_access_rules` typed rule table
- the `public.current_space_access_rules` view plus `api.get_space_access_rule(...)` and `api.evaluate_space_access(...)` retrieval functions
- seeded current approved Studio and Entire Venue space-access rules with primary and supporting provenance from the technical inventory, operations manual, terms, and agreement template
- the `public.operational_requirements` typed rule table
- the `public.current_operational_requirements` view plus `api.get_operational_requirements(...)` retrieval function
- seeded current approved operational timing, supplier, clearing, installation, storage, waste, and reset rules with source-backed uncertainty preserved where policy remains non-deterministic
- the `public.catering_supplier_rules` typed rule table
- the `public.current_catering_supplier_rules` view plus `api.get_catering_supplier_rules(...)` retrieval function
- the `public.technical_equipment_inventory` current-inventory table plus `public.current_technical_equipment_inventory` and quantity-evaluation retrieval
- the `public.technical_capability_rules` typed rule table
- the `public.current_technical_capability_rules` view plus `api.get_technical_capability(...)` and `api.evaluate_technical_requirement(...)` retrieval functions
- the `public.service_rules` typed rule table
- the `public.current_service_rules` view plus `api.get_service_rules(...)` retrieval function
- the `public.facilitator_requirement_rules` typed rule table
- the `public.current_facilitator_requirement_rules` view plus `api.get_facilitator_requirements(...)` retrieval function
- seeded current approved catering, beverage, kitchen-suitability, supplier-specific confirmation, and catering-specific VAT rules without duplicating the operational supplier-access truth
- seeded current approved technical inventory facts separately from support and feasibility rules so possession does not imply capability
- seeded current approved Wi-Fi, projection, sound, lighting, power, filming, and livestream capability rules with request-only, external-supplier, and confirmation-sensitive semantics preserved
- seeded current approved service-level, service-item, and facilitator-arrangement rules with written-scope, manual-quote, availability-confirmation, and responsibility semantics preserved
- tests for rule versioning, provenance invariants, booking fee lookups, payment-rule lookups, expedited-surcharge lookups, cancellation-rule lookups, capacity-rule lookups, space-access lookups, operational-requirement lookups, catering-supplier lookups, technical-capability lookups, and service-facilitator lookups

## What Is Explicitly Not Built Yet

- Next.js or Vercel application code
- direct model access outside the bounded Phase 7 runtime
- multi-provider routing or provider fallback
- Outlook ingestion, intake forms, or proposal-generation workflows
- Asana, n8n, calendar, or automation workflows
- live rental, client, organization, or contact records
- full Phase 4 rule population

## Current Pilot

The currently implemented typed rule domains are `booking_fee_rules`, `payment_rules`, `expedited_surcharge_rules`, `cancellation_rules`, `capacity_rules`, `space_access_rules`, `operational_requirements`, `catering_supplier_rules`, `technical_capability_rules`, `service_rules`, and `facilitator_requirement_rules`.

Current approved seeded outcomes:

- Studio Space, 1 to 3 hours: EUR 50 excluding VAT
- Studio Space, 4 to 8 hours: EUR 75 excluding VAT
- Entire Venue, 1 to 3 hours: EUR 100 excluding VAT
- Entire Venue, 4 to 7 hours: EUR 250 excluding VAT
- Entire Venue, full day: no booking fee
- Direct-rental upfront payment options: 30% or 100%, but 0 to 14 day confirmations are 100%-only
- Booking confirmation threshold: minimum 30% on cleared receipt
- Final balance rule: remaining 70% due 14 days before the event
- Short-notice confirmation deadline: within 3 days for bookings made 15 to 29 days before the event
- Urgent confirmation deadline: 100% within 24 hours for bookings made 0 to 14 days before the event
- Expedited surcharge: applies when confirmation occurs 0 to 14 calendar days before the event, at 10% of venue rental only, plus 21% VAT, with waiver authority limited to the WNC rental point of contact
- Client cancellation more than 30 days before the event: rental payments refundable, while booking fees and agreed production or coordination fees remain non-refundable
- Client cancellation 30 days or fewer before the event: rental payments non-refundable, with ongoing responsibility for non-recoverable committed costs
- Cancellation-specific committed-cost and security-deposit outcomes are stored as structured manual-review treatments rather than guessed live euro amounts
- WNC cancellation unrelated to client breach: all fees and deposits refunded in full
- Client breach termination: all payments received may be retained by WNC
- Entire Venue legal maximum: `110` guests as a distinct legal-ceiling rule
- Studio capacities: `25` lying down, `20` movement, `40` seated, and `40` standing
- Retail Area standing capacity: `60`
- 1:1 / Podcast Room: no fixed published guest number; confirmation required
- Back Office, Storage Room, and Hallway/Bathrooms: explicitly not event-capacity spaces
- Studio rental access: Studio Space included; Retail Area and Conversation Pit shared; Hallway/Bathrooms included for access; Back Office and Storage Room restricted
- Entire Venue access: Studio Space, Retail Area, and Conversation Pit included; Hallway/Bathrooms included for access; Back Office and Storage Room restricted
- 1:1 / Podcast Room access: included by default in Studio and Entire Venue scope, with setup and remaining-item nuance preserved in the rule details
- Operational timing: Studio rentals carry a 15 minute arrival/departure grace period, Entire Venue rentals carry a 30 minute arrival/departure grace period, and setup begins at booked time rather than during grace time
- Early operational access and off-timeline visits: explicit approval or confirmed appointment required
- Supplier handling: supplier access stays inside approved timeline windows, supplier details must be captured where in scope, and supplier responsibility stays with the client unless WNC has accepted it in writing
- Entire Venue clearing: structured as a conditional preparation requirement rather than an automatic inclusion
- Back Office and Storage Room operational use: modeled as conditional support-space arrangements that do not override the existing restricted access semantics
- Installation restrictions: plaster-wall fixings and strong-bond adhesives prohibited; removable low-risk adhesives, wooden-beam fixings, and exterior items remain conditional
- Waste and reset: client responsibility by default unless another scope item is explicitly included
- Professional cleaning: stored as manual review for significant mess or residue scenarios instead of a guessed threshold
- Catering supplier policy: external caterers and external barista teams are allowed without implying WNC coordination is included by default
- WNC catering partner path: available but confirmation-sensitive
- Beverage policy: tap water included; sparkling water optional rather than included by default
- Kitchen policy: ready-made food, warming, plating, and light assembly are supported; large-scale food production still requires explicit confirmation
- Catering VAT policy: products at `9%`, coordination or service at `21%`, and mixed catering split into separate product and service lines
- Technical inventory facts: current approved rows for mats, cushions, eye masks, blankets, glassware, furniture, cutlery, projector, extension cable, Casambi lights, and Sonos speakers
- Technical capability policy: Wi-Fi, Sonos playback, Casambi lighting, venue power, and wall plug infrastructure are distinct from external-only screen, microphone, DJ, production-lighting, filming, and dedicated-livestream capabilities
- Technical feasibility policy: ordinary playback, standard Wi-Fi, standard venue lighting, and standard power access are internally supported, while amplified event sound, microphone use, DJ audio, production lighting, filming, and dedicated livestreaming require external or client-provided solutions
- Technical confirmation policy: basic projection, high-load power, and custom technical setups require explicit confirmation rather than a guessed approval
- Service levels: `venue_only`, `supported_rental`, and `full_production` are stored separately from individual service items, with `supported_rental` and `full_production` remaining written-scope and manual-quote based
- Service items: current approved typed rows cover on-site host, event manager, production coordination, furniture and equipment sourcing, catering coordination, facilitator sourcing, experience design, setup support, breakdown/reset support, cleaning, beverage package, technical coordination, and manual-review `other_service`
- Facilitator arrangements: `client_provided` remains allowed and client-managed, while `wnc_provided`, `recommendation_requested`, and `custom_experience_design` preserve availability, scope, technical, and commitment-confirmation semantics instead of promising a facilitator by default
- Deferred boundary: the individual `WNC Facilitators & Rental Experiences` catalogue is still intentionally excluded from the typed rule layer

These slices intentionally still exclude deposit-amount logic, payment state for individual rentals, standalone Conversation Pit capacity, a full pairwise space-compatibility matrix, custom-scope default room access, staffing, insurance trigger automation, refund processing, cleaning pricing, deterministic professional-cleaning thresholds, preferred-supplier ranking, the deferred individual facilitator catalogue, live facilitator booking or availability, live equipment reservation or maintenance tracking, and all venue pricing beyond the approved booking-fee rows.

## Recommended Next Slice

The repository is now ready for downstream consumers to use the frozen Phase 7 runtime rather than reopening Phase 7 architecture. Because the live repository roadmap does not define an exact post-Phase-7 phase name, downstream work should be described against the relevant consumer/problem area rather than by inventing a new phase label here.
