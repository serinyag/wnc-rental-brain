# Phase 5 Repository Dependency Audit

## 1. Executive Summary

Phase 4 gives Phase 5 a strong governed foundation, but it does **not** yet provide every identity layer that Phase 5 will need.

The most important architectural finding is this:

- Exact rule versions are first-class rows in `public.rule_catalogue`, keyed by `id`.
- Stable logical rules are represented only by repeating the same `rule_code` across version rows.
- There is **no separate logical-rule table** that Phase 5 can foreign-key to today.

That means the current implemented model is:

- **Model B**: each rule version is its own `rule_catalogue` row, with a stable `rule_code` repeated across versions.

Implications for Phase 5:

- Phase 5 can safely reference an **exact historical rule version** by foreign key to `public.rule_catalogue.id`.
- Phase 5 cannot currently reference a **stable logical rule** with equivalent relational integrity, because `rule_code` is not a unique parent key and no dedicated logical-rule entity exists.
- If strict FK-backed logical-rule relationships are required, that is a real architecture review point and may become a `POTENTIAL_PHASE_4_DEPENDENCY`.

Other headline findings:

- Canonical machine tables already exist for `rental_types` and `venue_spaces`; Phase 5 should reuse them.
- Some other vocabularies are only check-constrained text inside typed rule tables, not reusable lookup tables.
- There is no current RLS/policy layer. The repo currently exposes approved read surfaces through `public.current_*` views and `api.*` functions granted to `anon`, `authenticated`, and `service_role`.
- There are no storage buckets, storage-object metadata tables, pgvector, pg_trgm, or full-text search implementations in the repository yet.
- `public.source_registry` is useful as a controlled source inventory, but it is **not** yet a full document-version / source-object provenance model.

## 2. Repository Sources Reviewed

Primary architecture sources reviewed:

- `README.md`
- `supabase/config.toml`
- `supabase/seed.sql`
- `supabase/migrations/20260803000100_phase_04_foundation.sql`
- `supabase/migrations/20260803000200_booking_fee_rules.sql`
- `supabase/migrations/20260803000300_payment_rules.sql`
- `supabase/migrations/20260803000400_expedited_surcharge_rules.sql`
- `supabase/migrations/20260805000500_cancellation_rules.sql`
- `supabase/migrations/20260805000600_capacity_rules.sql`
- `supabase/migrations/20260805000700_space_access_rules.sql`
- `supabase/migrations/20260805000800_operational_requirements.sql`
- `supabase/migrations/20260805000900_catering_supplier_rules.sql`
- `supabase/migrations/20260805001000_technical_capability_rules.sql`
- `supabase/migrations/20260805001100_service_facilitator_rules.sql`

Primary test sources reviewed:

- `supabase/tests/01_foundation_invariants.sql`
- `supabase/tests/02_booking_fee_rules.sql`
- `supabase/tests/03_payment_rules.sql`
- `supabase/tests/04_expedited_surcharge_rules.sql`
- `supabase/tests/05_cancellation_rules.sql`
- `supabase/tests/06_capacity_rules.sql`
- `supabase/tests/07_space_access_rules.sql`
- `supabase/tests/08_operational_requirements.sql`
- `supabase/tests/09_catering_supplier_rules.sql`
- `supabase/tests/10_technical_capability_rules.sql`
- `supabase/tests/11_service_facilitator_rules.sql`

Primary documentation sources reviewed:

- `docs/phase-04/phase-04-closure.md`
- `docs/phase-04/phase-04-completeness-audit.md`
- `docs/phase-04/governance/implementation-blockers.md`
- `docs/phase-04/governance/source-manifest.md`
- `docs/phase-04/governance/rule-code-conventions.md`
- `docs/phase-04/requirements/authoritative-source-map.md`
- `docs/phase-04/requirements/phase-04-scope.md`
- `docs/phase-04/architecture/schema-boundaries.md`
- `docs/phase-04/architecture/table-specifications.md`
- `docs/phase-04/architecture/erd.md`
- `docs/phase-04/architecture/adr/ADR-003-immutable-rule-versioning.md`

These are the primary sources for understanding the current architecture. The migrations and tests are the strongest evidence, with the docs accurately explaining the implemented Phase 4 intent and boundaries.

## 3. Existing Phase 4 Rule Architecture

### 3.1 Foundation tables

Phase 4 foundation is centered on five base tables:

- `public.source_registry`
- `public.rental_types`
- `public.venue_spaces`
- `public.rule_catalogue`
- `public.rule_source_links`

Key implemented relationships:

- `rule_source_links.rule_id -> rule_catalogue.id`
- `rule_source_links.source_id -> source_registry.id`
- `rule_catalogue.supersedes_rule_id -> rule_catalogue.id`

### 3.2 Typed rule tables

Each typed rule table stores structured business values for exactly one governed rule version:

- `public.booking_fee_rules`
- `public.payment_rules`
- `public.expedited_surcharge_rules`
- `public.cancellation_rules`
- `public.capacity_rules`
- `public.space_access_rules`
- `public.operational_requirements`
- `public.catering_supplier_rules`
- `public.technical_capability_rules`
- `public.service_rules`
- `public.facilitator_requirement_rules`

Pattern:

- each typed table uses `rule_id bigint primary key references public.rule_catalogue(id) on delete cascade`
- the typed row is therefore a 1:1 extension of one exact `rule_catalogue` row
- structured values live in the typed table, not JSON
- rule metadata and lifecycle live in `rule_catalogue`
- provenance lives in `rule_source_links`

`public.technical_equipment_inventory` is related but not rule-versioned in the same way. It is a current inventory fact table linked to `source_registry`.

### 3.3 Rule catalogue structure

`public.rule_catalogue` is the governance spine for every typed rule version. Important columns:

- `id bigint` primary key
- `rule_code text`
- `rule_domain text`
- `rule_kind text`
- `rule_version integer`
- `status text`
- `effective_from date`
- `effective_until date`
- `plain_language_explanation text`
- `owner_role text`
- `supersedes_rule_id bigint`
- `last_reviewed_at date`

Implemented integrity:

- unique `(rule_code, rule_version)`
- partial unique index on `rule_code` where `status = 'active'`
- `supersedes_rule_id` may only point to a row with the same `rule_code`
- active, superseded, and retired rules must have at least one `primary` or `governance` source link before commit

### 3.4 How versioning actually works

Implemented behavior from migrations, ADR-003, and tests:

- changing a rule creates a new `rule_catalogue` row
- the new row keeps the same `rule_code`
- the new row increments `rule_version`
- the new row may point to the previous row via `supersedes_rule_id`
- the old row remains preserved

Observed test pattern:

- `TEST_BOOKING_FEE_HISTORY` inserts version 1 as `superseded` and version 2 as `active`, both with the same `rule_code`
- `TEST_EXPEDITED_HISTORY` does the same and verifies historical lookups return version 1 for past dates and version 2 for later dates

### 3.5 How current rules are determined

Each domain has a `public.current_*` view. The consistent pattern is:

- join typed table to `rule_catalogue`
- filter `rc.status = 'active'`
- filter date window where:
  - `effective_from is null or effective_from <= current_date`
  - `effective_until is null or effective_until >= current_date`
- expose aggregated provenance arrays from `rule_source_links` and `source_registry`

Each domain also has `api.*` retrieval functions. Their consistent historical-query pattern is:

- allow an explicit `as_of_date`
- search `status in ('active', 'superseded', 'retired')`
- respect the effective-date window for the provided date
- return source-code provenance arrays

### 3.6 Domains, categories, and structured values

Implemented representation is mixed by design:

- domain identity is stored in `rule_catalogue.rule_domain`
- stable scoped entities use FKs to canonical tables where they exist:
  - `rental_type_id -> public.rental_types.id`
  - `venue_space_id -> public.venue_spaces.id`
- many other business vocabularies are implemented as check-constrained text in typed tables

Examples:

- `service_rules.service_level`
- `service_rules.service_type`
- `facilitator_requirement_rules.facilitator_arrangement`
- `source_registry.authority_level`
- `rule_source_links.relation_type`

### 3.7 Rule metadata storage

Metadata is split across layers:

- rule lifecycle and governance metadata: `rule_catalogue`
- structured domain truth: typed rule tables
- source provenance: `rule_source_links`
- source metadata: `source_registry`

This separation is strong and reusable for Phase 5.

## 4. Stable Rule vs Rule-Version Finding

### 4.1 Answer to the critical question

There is **not** a true separate stable logical-rule entity table in the current implementation.

The actual implemented architecture is:

- one row in `public.rule_catalogue` per exact rule version
- repeated `rule_code` across versions to represent stable logical identity
- typed rule rows keyed to the exact `rule_catalogue.id`

So the repository is using **Model B**, not Model A.

### 4.2 What can be referenced directly today

Phase 5 can already reference:

- **exact rule version**: `public.rule_catalogue.id`

Phase 5 cannot directly FK to an existing stable logical-rule entity because:

- `rule_code` is not a unique parent key in `rule_catalogue`
- multiple rows intentionally share the same `rule_code`
- no separate `logical_rules` or equivalent table exists

### 4.3 Does `rule_code` currently have relational integrity?

Partially, but not as a standalone FK target.

Implemented guarantees:

- `(rule_code, rule_version)` is unique
- at most one `active` row exists for a given `rule_code`
- `supersedes_rule_id` cannot cross rule codes

Missing guarantee:

- there is no unique row representing "`PAYMENT_SHORT_NOTICE` as a logical concept independent of version"

### 4.4 How Phase 5 can represent both relationship types

**Exact historical rule-version relationship**

Use a direct FK to `public.rule_catalogue.id`.

This matches the existing architecture and preserves exact historical provenance.

**Stable logical-rule relationship**

This is the harder part. Under the current Phase 4 architecture, Phase 5 has no existing FK-safe parent entity for the logical rule itself.

Therefore the current state is:

- exact-version link: supported directly
- logical-rule link: not supported directly with equivalent FK integrity

### 4.5 Is a normalization issue present?

Yes, if Phase 5 requires both of these simultaneously:

- a stable logical-rule relation with database-level referential integrity
- an exact rule-version relation with database-level referential integrity

Exact version identity is normalized.
Logical rule identity is still implicit in `rule_code`.

### 4.6 Does solving this require changing Phase 4?

Possibly.

If the requirement is merely:

- "store a logical-rule code consistently"

then Phase 5 could add its own logical-rule layer, but that would create a second authority for logical rule identity unless carefully designed.

If the requirement is:

- "support a true stable logical-rule FK with proper integrity back to the rule-version catalogue"

then a dedicated logical-rule entity likely needs architecture review and may require a structural normalization step related to Phase 4 governance objects rather than Phase 5 content tables alone.

That should be flagged as:

- `POTENTIAL_PHASE_4_DEPENDENCY`

because it is an architecture dependency, not a reopening of Phase 4 policy truth.

## 5. Existing Canonical Tables / Vocabulary

### 5.1 Strong reusable canonical structures

These are safe reuse candidates for Phase 5:

| Concept | Existing structure | Canonical machine value | Reuse guidance |
| ------- | ------------------ | ----------------------- | -------------- |
| rental type | `public.rental_types` | `rental_type_code` | Reuse directly via FK |
| venue space | `public.venue_spaces` | `space_code` | Reuse directly via FK |
| rule provenance relation | `public.rule_source_links` | `relation_type` | Reuse conceptually |
| source authority | `public.source_registry` | `authority_level` | Reuse conceptually |
| source identity | `public.source_registry` | `source_code` | Reuse where raw source artifacts are involved |

Seeded reusable rental types:

- `studio_space`
- `entire_venue`
- `custom_scope`

Seeded reusable venue spaces:

- `studio_space`
- `one_to_one_room`
- `retail_area`
- `conversation_pit`
- `storage_room`
- `back_office`
- `hallway_bathrooms`
- `other_space`

### 5.2 Existing controlled vocabularies that are not first-class tables

These exist, but only as check-constrained text:

| Concept | Implemented location | Reuse guidance |
| ------- | -------------------- | -------------- |
| service level | `public.service_rules.service_level` | Reuse machine values, but there is no lookup table yet |
| service type | `public.service_rules.service_type` | Reuse machine values, but there is no lookup table yet |
| facilitator arrangement | `public.facilitator_requirement_rules.facilitator_arrangement` | Reuse carefully if needed |
| source lifecycle | `public.source_registry.lifecycle_status` | Exists as text, but not strongly normalized |
| rule status | `public.rule_catalogue.status` | Reuse for rule lifecycle only |

Important nuance:

- the Data Dictionary is treated as authoritative for service-level and service-type machine values
- the database currently enforces those values through `CHECK` constraints, not through reference tables

### 5.3 Concepts not currently modeled as reusable canonical tables

Not found as first-class reusable tables:

- audience taxonomy
- organizational knowledge roles/audiences
- confidentiality classification
- generic tags
- generic categories for knowledge artifacts
- a logical document table
- a document-version table
- a source-object table

### 5.4 Multi-valued classification dependency

For many-to-many classification, existing reuse options are:

- rental types: yes, via `public.rental_types`
- spaces: yes, via `public.venue_spaces`
- service types: machine values exist, but not as FK-safe reference rows
- audiences: no existing canonical table found
- tags: no existing canonical table found

Practical Phase 5 implication:

- do not store rental type or venue space as unrestricted text
- audience and tag modeling will need new Phase 5 structures unless another canonical source is introduced first

## 6. Database Conventions

### 6.1 IDs and keys

- primary keys are `bigint generated by default as identity`
- foreign keys also use `bigint`
- no UUID conventions are implemented in the current Phase 4 schema
- stable business identifiers are usually text codes such as:
  - `source_code`
  - `rental_type_code`
  - `space_code`
  - `rule_code`

### 6.2 Timestamps

Standard pattern:

- `created_at timestamptz not null default timezone('utc', now())`
- `updated_at timestamptz not null default timezone('utc', now())`
- `private.touch_updated_at()` trigger updates `updated_at` on row update

### 6.3 Created-by / updated-by

Not implemented in Phase 4 tables.

There are no current conventions for:

- `created_by`
- `updated_by`
- actor/user audit IDs

### 6.4 Effective dates

Rule timing convention lives in `rule_catalogue`:

- `effective_from`
- `effective_until`

Current-state views use `current_date`.
Historical retrieval functions accept explicit `as_of_date`.

### 6.5 Version numbering and supersession

Implemented conventions:

- `rule_version` is a positive integer
- unique per `rule_code`
- `supersedes_rule_id` links one version row to an earlier row of the same `rule_code`

Important limit:

- the database does **not** enforce a complete logical-version chain beyond same-code supersession and version uniqueness
- it does not require contiguous version numbers
- it does not require every non-v1 row to populate `supersedes_rule_id`

### 6.6 Status and lifecycle

Implemented status conventions:

- `rule_catalogue.status`: `draft`, `active`, `superseded`, `retired`
- `source_registry.authority_level`: `authoritative`, `guidance`, `reference_only`, `unverified`
- `source_registry.lifecycle_status`: non-empty free text, not a closed enum

### 6.7 Soft deletion

No general soft-delete pattern found.

What exists instead:

- `is_active` flags on `rental_types` and `venue_spaces`
- lifecycle/status fields on rules and sources

No `deleted_at` or row tombstone convention is implemented.

### 6.8 Audit trail

The current audit pattern is:

- immutable version rows in `rule_catalogue`
- typed rule rows keyed to those versions
- provenance links through `rule_source_links`

There is no generic row-history or change-log table in the schema itself.

### 6.9 Constraints and triggers

Strong conventions already in use:

- non-empty text checks
- domain-specific `CHECK` constraints
- unique constraints on canonical codes
- overlap-prevention triggers for non-draft rules
- provenance enforcement as deferred constraint triggers
- `updated_at` maintenance triggers

Phase 5 should follow these conventions unless there is a strong architectural reason not to.

## 7. Security / RLS Conventions

Implemented findings:

- no `ENABLE ROW LEVEL SECURITY` statements found
- no `CREATE POLICY` statements found
- no `auth.*` helper usage found
- no current user-context policy helpers found

Current access pattern is grant-based, not RLS-based:

- `GRANT SELECT` on `public.current_*` views
- `GRANT EXECUTE` on `api.*` functions
- grants go to `anon`, `authenticated`, and `service_role`
- `GRANT USAGE ON SCHEMA api` is present

Observed convention:

- expose curated read surfaces
- do not expose the typed tables as the application contract

Phase 5 implication:

- this repo does not yet establish a privacy-sensitive knowledge access model
- organizational knowledge may be the first phase that should not simply mirror broad `anon` / `authenticated` read grants
- Phase 5 can follow the "curated surface first" pattern, but likely needs a stricter security design than current public policy-read surfaces

## 8. Storage / Provenance Findings

### 8.1 Supabase storage state

Repository findings:

- `supabase/config.toml` has `[storage] enabled = true`
- no repository-defined storage buckets are configured
- no storage buckets are created in migrations
- no storage RLS or storage policies are implemented
- no `storage.objects` metadata model exists in repo SQL

So the effective current state is:

- storage service enabled in local config
- no project buckets yet

### 8.2 Existing provenance model

Current provenance model is rule-centric:

- `source_registry` stores controlled source artifacts and metadata
- `rule_source_links` links exact rule versions to those source artifacts
- current views aggregate provenance as `primary_source_codes`, `governance_source_codes`, and `supporting_source_codes`

This is useful and should be reused conceptually.

### 8.3 What the existing model does not provide

It does **not** currently model:

- logical document identity
- document version identity
- multiple physical representations of one document version
- explicit roles such as editable master, export, attachment, or supporting object
- storage-object metadata tied to bucket/object paths

Important evidence:

- `source_registry` stores `CF-003` and `CF-004` as separate rows for editable master vs export
- their relationship is documented only through `source_type`, `lifecycle_status`, and notes
- there is no relational grouping that says "these are two artifacts of the same document version"

### 8.4 Answer to the provenance architecture dependency

The existing repository does **not** provide a full reusable model for:

- `document version`
- `version-source relationship`
- `source object`

Phase 5 should introduce a dedicated provenance model for governed knowledge documents and their physical representations.

Classification:

- `PHASE_5_CAN_ADD`

`source_registry` may still be reused as the controlled inventory of Phase 1-3 authoritative source files, but it is not sufficient on its own for the later governed document-version model.

## 9. Search / Extension Findings

Database-search findings:

- no `pgvector` / `vector` extension enabled in migrations
- no `pg_trgm` extension enabled in migrations
- no full-text search implementation found
- no `tsvector` / `to_tsvector` usage found
- no GIN or GiST search indexes found
- no embedding schema found

Only extension usage found:

- `pgtap`, created inside the database test files

Important nuance:

- `supabase/config.toml` includes `[storage.vector]`
- that is a storage-service configuration section, not a PostgreSQL `vector` extension enablement
- it does **not** mean pgvector is already available in the Phase 4 schema

Phase 5 implication:

- vector search would require later database work
- keyword search would also require explicit Phase 5 schema/index design
- there is no repository search convention yet beyond ordinary B-tree uniqueness and lookup indexes

## 10. Testing Conventions

Phase 4 database tests are highly consistent.

Framework and structure:

- pgTAP test files under `supabase/tests/`
- each file starts with `begin;`
- each file enables `pgtap` in `extensions`
- each file sets a local `search_path`
- each file declares `select plan(...)`
- each file ends with `select * from finish();` and `rollback;`

Current suite shape:

- 11 SQL test files
- 188 total tests from the file plans

Patterns in use:

- invariant tests for base governance rules
- happy-path retrieval tests against seeded data
- overlap-protection failure tests
- wrong-domain / wrong-kind failure tests
- provenance-required commit tests
- historical version behavior tests using `superseded` and `active` rows with the same `rule_code`
- current-view provenance exposure tests

Fixture approach:

- `supabase db reset` loads migrations plus `supabase/seed.sql`
- tests rely on seeded canonical rows
- tests insert temporary rows inside the transaction when they need targeted edge cases

Storage and security test state:

- no storage bucket tests found
- no RLS/policy tests found

Phase 5 should follow the same migration-plus-pgTAP discipline.

## 11. Phase 5 Architecture Dependencies

| Dependency | Classification | Finding |
| ---------- | -------------- | ------- |
| exact rule-version relationship | `REUSE_EXISTING` | Use FK to `public.rule_catalogue.id` |
| stable logical-rule relationship | `REQUIRES_ARCHITECTURE_REVIEW` | No existing logical-rule entity exists; `rule_code` is repeated across version rows |
| strict FK integrity for logical-rule identity | `POTENTIAL_PHASE_4_DEPENDENCY` | May require first-class logical-rule normalization tied to the Phase 4 rule catalogue |
| rental type classification | `REUSE_EXISTING` | Reuse `public.rental_types` |
| venue space classification | `REUSE_EXISTING` | Reuse `public.venue_spaces` |
| service-level / service-type identifiers | `REUSE_EXISTING` | Reuse existing machine values, but note they are not lookup tables |
| audience taxonomy | `PHASE_5_CAN_ADD` | No reusable audience table exists today |
| tag taxonomy | `PHASE_5_CAN_ADD` | No reusable generic tag table exists today |
| confidentiality classification | `PHASE_5_CAN_ADD` | No implemented classification exists today |
| governed document version model | `PHASE_5_CAN_ADD` | Needed; not provided by `source_registry` |
| source-object / master-export relationship model | `PHASE_5_CAN_ADD` | Needed; current repo only stores separate artifact rows plus notes |
| storage buckets for Phase 5 documents | `PHASE_5_CAN_ADD` | No existing buckets are created |
| search / FTS / vector capability | `PHASE_5_CAN_ADD` | No current implementation exists |
| security model for organizational knowledge | `REQUIRES_ARCHITECTURE_REVIEW` | Current repo has no RLS and broad read grants on approved rule views |

## 12. Open Questions

Only genuine unresolved architecture questions identified from the implemented repo:

1. Does Phase 5 require true database-level FK integrity for stable logical-rule relationships, or is a controlled `rule_code` registry layer acceptable?
2. If a logical-rule entity is required, should it be introduced as a new Phase 5 normalization layer only, or should `rule_catalogue` itself become a child of a first-class logical-rule table?
3. Should `source_registry` remain strictly the preserved Phase 1-3 source inventory, or should Phase 5 build a separate document/source-object model beside it?
4. Are audiences intended to be knowledge-only classifications, or should they align with a future broader staff/workflow role model?
5. Should Phase 5 knowledge artifacts inherit the current broad read-grant posture, or should Phase 5 be the first layer to introduce explicit private/internal access controls?

## 13. Recommendation for Task 5.1

The Phase 5 architecture proposal should proceed with these constraints in mind:

- treat `public.rule_catalogue.id` as the authoritative FK target for exact rule-version links
- explicitly address the missing first-class logical-rule entity before designing knowledge-to-rule relationships
- reuse `rental_types` and `venue_spaces` rather than reintroducing those concepts as free text
- distinguish between canonical lookup tables that already exist and vocabularies that currently exist only as constrained text
- introduce a dedicated governed document/document-version/source-object provenance model rather than forcing that onto `source_registry`
- assume search, buckets, embeddings, and stricter security are future Phase 5 additions, not existing foundations

In short: Phase 5 can build cleanly on Phase 4 for exact rule versions, provenance patterns, canonical rental scope, and test discipline, but the logical-rule identity layer and the governed document-version provenance layer are the two main architecture decisions that need explicit treatment before schema design is finalized.
