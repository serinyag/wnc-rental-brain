# Technical Capability Rules

## Objective

Model the approved fixed WNC technical capabilities and equipment-related feasibility rules without collapsing physical inventory facts into broader technical-support promises.

## Business Questions

- What technical capability exists?
- What physical equipment exists?
- What quantity exists where the current source gives an authoritative quantity?
- Is the capability standard, available on request, external-only, or confirmation-sensitive?
- Is the technical requirement internally supported, or does it need an external supplier or client-provided solution?
- Which technical requests still require confirmation instead of a guessed default?
- When a quantity is requested, can WNC confirm it directly, or does it still require confirmation?

## Cross-Domain Boundary

This slice does not replace the already implemented domains that remain authoritative for their own concerns.

Still authoritative elsewhere:

- `capacity_rules`: guest capacity must not be inferred from equipment quantity
- `space_access_rules`: equipment availability does not imply access to restricted rooms
- `operational_requirements`: installation restrictions, exterior items, and timeline/access handling remain there
- `catering_supplier_rules`: coffee machine, kitchen-use, cold-storage, and catering-specific power overlays remain there when tied to catering scope

This slice adds only the current technical inventory facts and the venue capability or feasibility rules that sit on top of them.

## Inputs

The approved source set supports these inputs for the current typed slice:

- `equipment_code`
- `equipment_category`
- `requested_quantity`
- `rule_type`
- `capability_code`
- `requirement_code`
- `technical_area`
- `as_of_date`

The implementation does not treat vague production briefs, decibel targets, connector types, streaming performance expectations, or arbitrary electrical-load calculations as deterministic rule inputs.

## Structured Outputs

Current seeded capability `support_status` values:

- `standard`
- `available_on_request`
- `external_supplier_required`
- `supported`
- `not_available`
- `requires_confirmation`

Inventory status values:

- `standard`
- `available_on_request`
- `must_confirm`

Supporting fields:

- `included_in_base_rental`
- `internal_equipment_exists`
- `internal_support_sufficient`
- `client_may_self_organise`
- `wnc_can_coordinate`
- `coordination_fee_possible`
- `requires_confirmation`
- `manual_review_required`

Quantity evaluation statuses:

- `quantity_available`
- `insufficient_quantity`
- `requires_confirmation`
- `no_applicable_equipment`

## Architecture Decision

This slice uses two structures on purpose:

- `public.technical_equipment_inventory`
- `public.technical_capability_rules`

`technical_equipment_inventory` stores current authoritative inventory facts such as item name, current standard quantity, inclusion status, and location summary. These are traceable to the technical inventory source but are not forced into `rule_catalogue` versioning because the current Phase 4 goal is current approved stock facts, not full historical inventory-state replay.

`technical_capability_rules` stores versioned, source-provenanced support and feasibility rules. This is where WNC distinguishes possession from actual support. For example, the venue owns Sonos speakers, but amplified event sound and DJ audio still require an external solution.

## Current Capability Vocabulary

Current seeded `capability_code` values:

- `wifi`
- `basic_projector`
- `projection_screen`
- `installed_sonos_system`
- `additional_sound_system`
- `microphones`
- `dj_setup`
- `casambi_dimmable_venue_lighting`
- `production_lighting`
- `electrical_groups`
- `voltage_220v`
- `plug_points`
- `basic_extension_cable`
- `filming_setup`
- `livestream_system`

Current seeded `requirement_code` values:

- `standard_wifi`
- `ordinary_audio_playback`
- `amplified_event_sound`
- `microphone_use`
- `dj_audio_setup`
- `basic_projection`
- `projection_with_dedicated_screen`
- `standard_venue_lighting`
- `production_lighting`
- `standard_power_access`
- `high_load_power`
- `filming`
- `dedicated_livestreaming`
- `custom_technical_setup`

## Approved Inventory Facts Represented

Current seeded inventory covers:

- yoga mats
- meditation cushions
- eye masks
- blankets
- glassware
- standard WNC furniture
- cutlery
- one basic projector
- one basic extension cable
- installed Casambi dimmable venue lighting
- four Sonos speakers

Exact live quantity is intentionally not guaranteed for every item. The inventory source itself says quantities should still be confirmed when the event depends on an exact count.

## Approved Capability Rules Represented

Current seeded policy covers:

- venue Wi-Fi as a standard included capability
- one basic projector as request-only capability
- no dedicated projection screen owned by WNC
- installed Sonos playback as standard ordinary-audio capability
- no additional production sound system owned by WNC
- no microphones owned by WNC
- no DJ setup owned by WNC
- installed Casambi venue lighting as standard capability
- no specialist production lighting owned by WNC
- standard venue power through electrical groups, wall plug points, and 220V plug power
- one basic extension cable available on request
- no internal filming setup
- no dedicated livestream system or dedicated streaming capacity
- ordinary audio playback supported internally
- amplified event sound, microphones, DJ audio, production lighting, filming, and dedicated livestreaming requiring external or client-provided solutions
- basic projection and high-load power treated as confirmation-sensitive rather than silently guaranteed
- custom technical setup treated as confirmation-required rather than guessed

## Intentionally Excluded Or Left In Other Domains

This slice does not implement:

- creative AV or lighting design
- arbitrary electrical-load calculation
- bandwidth or streaming guarantees
- connector or mixer compatibility matrices
- equipment reservation workflows
- maintenance or replacement tracking
- kitchen, coffee-machine, fridge, freezer, or bar-equipment scope beyond the already authoritative catering domain
- wall-installation restrictions already governed in `operational_requirements`

Source statements intentionally not promoted into this slice as technical rules:

- plaster-wall installation restrictions and related approval paths, because they are already authoritative in `operational_requirements`
- coffee machine, dishwasher, stoves, fridges, and freezer capability rows, because the current authoritative implementation keeps those tied to catering and supplier scope
- event-specific sound, streaming, or production design guidance that does not define one stable support rule

## Missing-Information Semantics

- Missing `capability_code` for a capability lookup returns `insufficient_information`.
- Missing `requirement_code` for a requirement evaluation returns `insufficient_information`.
- Unknown capability or requirement codes return `no_applicable_rule`.
- Quantity evaluation does not guess. If the requested quantity depends on a non-guaranteed count, the result is `requires_confirmation`.
- Requested quantity above a numeric standard stock can return `insufficient_quantity`, but that does not redefine event feasibility or capacity.

## Query Surfaces

- `public.current_technical_equipment_inventory`
- `api.get_technical_equipment_inventory(p_equipment_code, p_equipment_category)`
- `api.evaluate_technical_equipment_quantity(p_equipment_code, p_requested_quantity)`
- `public.current_technical_capability_rules`
- `api.get_technical_capability(p_rule_type, p_capability_code, p_requirement_code, p_technical_area, p_as_of_date)`
- `api.evaluate_technical_requirement(p_requirement_code, p_as_of_date)`

## Example Queries

```sql
select support_status, included_in_base_rental
from api.get_technical_capability(
  'capability_availability',
  'wifi',
  null,
  'connectivity',
  date '2026-08-05'
);
```

Expected current result: `standard`, included in base rental.

```sql
select support_status, requires_confirmation
from api.get_technical_capability(
  'capability_availability',
  'basic_projector',
  null,
  'projection',
  date '2026-08-05'
);
```

Expected current result: `available_on_request`, confirmation-sensitive.

```sql
select support_status
from api.evaluate_technical_requirement(
  'amplified_event_sound',
  date '2026-08-05'
);
```

Expected current result: `external_supplier_required`

```sql
select support_status, internal_equipment_exists, internal_support_sufficient
from api.evaluate_technical_requirement(
  'dj_audio_setup',
  date '2026-08-05'
);
```

Expected current result: internal equipment may still exist in the venue, but DJ support is not internally sufficient and requires an external solution.

```sql
select equipment_name, quantity_numeric, quantity_evaluation_status
from api.evaluate_technical_equipment_quantity(
  'basic_projector',
  2
);
```

Expected current result: `insufficient_quantity`

```sql
select equipment_name, availability_status, quantity_numeric
from api.get_technical_equipment_inventory(
  'sonos_speakers',
  null
);
```

Expected current result: four Sonos speakers exist as standard included equipment, but that does not change the separate audio-support rules.
