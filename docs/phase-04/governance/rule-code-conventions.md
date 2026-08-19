# Rule Code Conventions

## Purpose

Rule codes identify the logical rule across versions. They are stable governance identifiers, not display labels and not migration names.

## Format

- uppercase ASCII
- words separated by underscores
- no embedded version number
- describe the logical rule, not the current numeric value

Recommended shape:

```text
<DOMAIN>_<SUBJECT>_<QUALIFIER>_<BEHAVIOUR>
```

Examples:

```text
FEE_STUDIO_1_TO_3_HOUR_BOOKING
PAYMENT_CONFIRMATION_MINIMUM
SURCHARGE_EXPEDITED_CONFIRMATION
CAPACITY_STUDIO_MOVEMENT
ACCESS_STUDIO_RETAIL_SHARED
VAT_MIXED_CATERING_SPLIT
```

## Domain Prefixes

Recommended prefixes for current Phase 4 domains:

- `PRICE`
- `FEE`
- `SURCHARGE`
- `PAYMENT`
- `CANCELLATION`
- `VAT`
- `CAPACITY`
- `ACCESS`
- `SERVICE`
- `CATERING`
- `SUPPLIER`
- `OPERATIONS`

## Stability Rules

- do not embed `V1`, `V2`, or dates in the code
- create a new rule version row when policy changes
- keep the original code if the logical rule is still the same rule
- mint a new code only when the business concept itself changes materially

## Relationship To Sources

- codes should preserve approved vocabulary from the Data Dictionary and controlled documents
- deprecated room names or legacy aliases must not appear in new rule codes
- if source language is still ambiguous, postpone the final code until governance review resolves the ambiguity
