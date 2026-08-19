# Catering Supplier Rules

## Objective

Model the approved fixed WNC policy for catering arrangements, WNC catering partner availability, external caterers, beverage-service options, kitchen suitability, supplier-specific confirmation requirements, and catering-specific VAT treatment without turning Phase 4 into a live supplier-booking or event-planning system.

## Business Questions

- Is the catering arrangement allowed?
- Does the arrangement rely on an external supplier?
- Is WNC coordination included by default, optional, or absent?
- Do kitchen limitations affect the arrangement?
- What supplier-specific confirmation requirements apply?
- What beverage rules apply to tap water, sparkling water, or external bar service?
- What catering-specific VAT classification applies where authoritative?
- Which questions still require confirmation instead of a guessed default?

## Cross-Domain Boundary

This slice does not replace the generic supplier-operational rules already implemented in `operational_requirements`.

Still authoritative in `operational_requirements`:

- supplier access only during approved access times
- off-timeline supplier access requires approval
- supplier information must be captured where relevant
- the client remains responsible for suppliers unless WNC has accepted coordination in writing
- generic waste-removal and reset responsibilities

This catering/supplier slice adds the supplier-category-specific rules that sit on top of those operational defaults.

## Inputs

The approved source set supports these inputs for the current typed slice:

- `catering_arrangement`
- `rule_type`
- `context_code`
- `vat_category`
- `kitchen_use_requested`
- `as_of_date`

The implementation does not treat menu choice, guest count, dietary complexity, or live supplier availability as deterministic rule inputs.

## Structured Outputs

Current seeded `outcome` values:

- `allowed`
- `conditional`
- `requires_confirmation`
- `wnc_partner_available`

Supporting fields:

- `external_supplier_required`
- `included_by_default`
- `wnc_coordination_available`
- `wnc_coordination_included`
- `kitchen_use_status`
- `vat_category`
- `vat_rate`
- `requires_split_lines`
- `requires_confirmation`
- `manual_review_required`

## Current Arrangement Vocabulary

The current schema supports these arrangement codes:

- `wnc_catering_partner`
- `external_caterer`
- `client_provided`
- `beverage_package`
- `external_barista_team`
- `tap_water`
- `sparkling_water`
- `none`
- `custom`

Not every code is seeded yet. Unseeded codes intentionally return `no_applicable_rule` unless another context requires `insufficient_information`.

## Approved Rules Represented

Current seeded policy covers:

- external caterers are allowed
- WNC catering-partner path exists but must be confirmed per rental
- WNC beverage package can be agreed, but the package scope must be confirmed
- tap water is included
- sparkling water is not included by default, but the client may bring it or WNC may source it
- external barista or bar teams are allowed
- the kitchen is suited to ready-made food, warming, plating, and light assembly
- large-scale food production is not assumed supported and requires explicit confirmation
- external caterers must confirm storage and power-sensitive equipment needs
- external barista teams must confirm storage and machine or power needs
- the WNC coffee machine is available where agreed
- catering coordination or service uses 21% VAT
- food and beverage products use 9% VAT
- mixed catering must be split into separate product and service lines

## Explicit Exclusions

This slice does not implement:

- menu design
- live supplier bookings
- guest-count based catering quantities
- preferred-supplier ranking beyond the current approved WNC partner path
- overtime pricing
- professional-cleaning thresholds
- event-specific delivery schedules
- permit or insurance trigger automation
- live invoice calculations
- proposal wording or supplier emails

## Missing-Information Semantics

- Missing `catering_arrangement` returns `insufficient_information` when the relevant rule family is arrangement-specific.
- Missing `kitchen_use_requested` returns `insufficient_information` where a rule only applies when kitchen use is requested.
- Missing `vat_category` returns `insufficient_information` for VAT-classification lookups.
- Unknown or unseeded arrangements such as `custom` return `no_applicable_rule` unless a narrower seeded rule matches.

## Query Surfaces

- `public.current_catering_supplier_rules`
- `api.get_catering_supplier_rules(p_catering_arrangement, p_rule_type, p_context_code, p_vat_category, p_kitchen_use_requested, p_as_of_date)`

The API may return multiple applicable rows for the same context.

## Example Queries

```sql
select outcome, external_supplier_required, wnc_coordination_available, wnc_coordination_included
from api.get_catering_supplier_rules(
  'external_caterer',
  'arrangement_policy',
  null,
  null,
  false,
  date '2026-08-05'
);
```

Expected current result: external caterer is allowed, requires an external supplier, and does not imply WNC coordination by default.

```sql
select outcome, requires_confirmation
from api.get_catering_supplier_rules(
  'wnc_catering_partner',
  'arrangement_policy',
  null,
  null,
  false,
  date '2026-08-05'
);
```

Expected current result: WNC catering-partner option available, but confirmation required.

```sql
select outcome, kitchen_use_status
from api.get_catering_supplier_rules(
  'external_caterer',
  'kitchen_use',
  'large_scale_food_production',
  null,
  true,
  date '2026-08-05'
);
```

Expected current result: confirmation required for large-scale food production.

```sql
select vat_category, vat_rate, requires_split_lines
from api.get_catering_supplier_rules(
  null,
  'vat_classification',
  null,
  'food_or_beverage_products',
  false,
  date '2026-08-05'
);
```

Expected current result: `food_or_beverage_products`, `0.09`, `false`

```sql
select vat_category, requires_split_lines
from api.get_catering_supplier_rules(
  null,
  'vat_classification',
  null,
  'mixed_catering_split',
  false,
  date '2026-08-05'
);
```

Expected current result: split lines required
