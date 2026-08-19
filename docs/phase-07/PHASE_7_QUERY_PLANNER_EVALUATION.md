# Phase 7 Query Planner Evaluation

Date: August 8, 2026

## 1. Planner Design

The `7.2B` planner is a deterministic application-layer router implemented in:

- `tools.phase_07_reasoning.query_planner`
- `tools.phase_07_reasoning.evaluation_scenarios`

It emits only the frozen `QueryPlan` contract and does not execute any retrieval or authority-resolution step.

## 2. Routing Rules

Core routing sequence:

1. deterministic safety overrides
2. lexical/heuristic class and domain detection
3. bounded ambiguity handling through deterministic broadening
4. post-classification safety augmentation

No LLM router was required.

## 3. Domain Mapping Rules

Phase 4 routing is multi-label and maps natural-language cues into:

- `booking_fee`
- `payment`
- `expedited_surcharge`
- `cancellation`
- `capacity`
- `space_access`
- `operational_requirements`
- `catering_supplier`
- `technical_inventory`
- `technical_capability`
- `service_rules`
- `facilitator_requirements`

## 4. 40-Scenario Results

| Scenario | Expected Layers | Planned Layers | Expected Query Class | Planned Query Class | Expected P4 Domains | Planned P4 Domains | Safety Overrides | Ambiguity Flags | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P7-EVAL-001 | phase_4 | phase_4 | deterministic_current | deterministic_current | payment | payment | current_deterministic_claim_requires_phase_4 | none | PASS |
| P7-EVAL-002 | phase_4 | phase_4 | deterministic_current | deterministic_current | expedited_surcharge | expedited_surcharge | current_deterministic_claim_requires_phase_4 | none | PASS |
| P7-EVAL-003 | phase_4 | phase_4 | deterministic_current | deterministic_current | capacity | capacity | current_deterministic_claim_requires_phase_4 | none | PASS |
| P7-EVAL-004 | phase_4 | phase_4 | deterministic_current | deterministic_current | capacity | capacity | current_deterministic_claim_requires_phase_4 | none | PASS |
| P7-EVAL-005 | phase_4 | phase_4 | deterministic_current | deterministic_current | space_access | space_access | current_deterministic_claim_requires_phase_4 | none | PASS |
| P7-EVAL-006 | phase_4, phase_5 | phase_4, phase_5 | deterministic_current | deterministic_current | payment | payment | current_deterministic_claim_requires_phase_4, current_guidance_request_requires_phase_5 | mixed_guidance_and_deterministic_claim | PASS |
| P7-EVAL-007 | phase_4, phase_5 | phase_4, phase_5 | current_guidance | current_guidance | catering_supplier, operational_requirements | catering_supplier, operational_requirements | current_deterministic_claim_requires_phase_4, current_guidance_request_requires_phase_5 | none | PASS |
| P7-EVAL-008 | phase_4, phase_5 | phase_4, phase_5 | deterministic_current | deterministic_current | catering_supplier | catering_supplier | current_deterministic_claim_requires_phase_4, current_guidance_request_requires_phase_5 | mixed_guidance_and_deterministic_claim | PASS |
| P7-EVAL-009 | phase_4, phase_5 | phase_4, phase_5 | current_guidance | current_guidance | service_rules | service_rules | current_deterministic_claim_requires_phase_4, current_guidance_request_requires_phase_5 | mixed_guidance_and_deterministic_claim | PASS |
| P7-EVAL-010 | phase_4, phase_5 | phase_4, phase_5 | current_guidance | current_guidance | service_rules, facilitator_requirements | service_rules, facilitator_requirements | current_deterministic_claim_requires_phase_4, current_guidance_request_requires_phase_5 | mixed_guidance_and_deterministic_claim | PASS |
| P7-EVAL-011 | phase_5 | phase_5 | current_guidance | current_guidance | none | none | current_guidance_request_requires_phase_5 | none | PASS |
| P7-EVAL-012 | phase_5 | phase_5 | current_guidance | current_guidance | none | none | current_guidance_request_requires_phase_5 | none | PASS |
| P7-EVAL-013 | phase_5 | phase_5 | current_guidance | current_guidance | none | none | current_guidance_request_requires_phase_5 | none | PASS |
| P7-EVAL-014 | phase_5 | phase_5 | current_guidance | current_guidance | none | none | current_guidance_request_requires_phase_5 | none | PASS |
| P7-EVAL-015 | phase_6 | phase_6 | precedent_discovery | precedent_discovery | none | none | none | none | PASS |
| P7-EVAL-016 | phase_6 | phase_6 | precedent_discovery | precedent_discovery | none | none | none | none | PASS |
| P7-EVAL-017 | phase_6 | phase_6 | precedent_discovery | precedent_discovery | none | none | none | none | PASS |
| P7-EVAL-018 | phase_6 | phase_6 | precedent_discovery | precedent_discovery | none | none | none | none | PASS |
| P7-EVAL-019 | phase_4, phase_5, phase_6 | phase_4, phase_5, phase_6 | mixed_current_and_precedent | mixed_current_and_precedent | catering_supplier, operational_requirements | catering_supplier, operational_requirements | current_deterministic_claim_requires_phase_4, current_guidance_request_requires_phase_5 | ambiguous_current_vs_historical_intent, historical_reference_with_current_policy_request, mixed_guidance_and_deterministic_claim | PASS |
| P7-EVAL-020 | phase_4, phase_5, phase_6 | phase_4, phase_5, phase_6 | mixed_current_and_precedent | mixed_current_and_precedent | space_access, operational_requirements, catering_supplier | operational_requirements, space_access, catering_supplier | current_deterministic_claim_requires_phase_4, current_guidance_request_requires_phase_5 | ambiguous_current_vs_historical_intent, historical_reference_with_current_policy_request | PASS |
| P7-EVAL-021 | phase_4, phase_5, phase_6 | phase_4, phase_5, phase_6 | mixed_current_and_precedent | mixed_current_and_precedent | service_rules, facilitator_requirements | service_rules, facilitator_requirements | current_deterministic_claim_requires_phase_4, current_guidance_request_requires_phase_5 | none | PASS |
| P7-EVAL-022 | phase_4, phase_5, phase_6 | phase_4, phase_5, phase_6 | mixed_current_and_precedent | mixed_current_and_precedent | operational_requirements | operational_requirements | current_deterministic_claim_requires_phase_4, current_guidance_request_requires_phase_5 | ambiguous_current_vs_historical_intent, historical_reference_with_current_policy_request | PASS |
| P7-EVAL-023 | phase_4, phase_5, phase_6 | phase_4, phase_5, phase_6 | mixed_current_and_precedent | mixed_current_and_precedent | catering_supplier, operational_requirements | catering_supplier, operational_requirements | current_deterministic_claim_requires_phase_4, current_guidance_request_requires_phase_5 | ambiguous_current_vs_historical_intent, historical_reference_with_current_policy_request | PASS |
| P7-EVAL-024 | phase_4, phase_5, phase_6 | phase_4, phase_5, phase_6 | unresolved_authority | unresolved_authority | technical_capability, technical_inventory | technical_inventory, technical_capability | current_deterministic_claim_requires_phase_4, historical_reference_requires_current_authority_before_prescriptive_answer | ambiguous_technical_inventory_vs_capability, historical_reference_with_current_policy_request | PASS |
| P7-EVAL-025 | phase_4, phase_5, phase_6 | phase_4, phase_5, phase_6 | unresolved_authority | unresolved_authority | space_access, operational_requirements | operational_requirements, space_access | current_deterministic_claim_requires_phase_4, historical_reference_requires_current_authority_before_prescriptive_answer, historical_commercial_claim_requires_current_authority | historical_reference_with_current_policy_request | PASS |
| P7-EVAL-026 | phase_5, phase_6 | phase_5, phase_6 | unresolved_authority | unresolved_authority | none | none | historical_reference_requires_current_authority_before_prescriptive_answer, historical_commercial_claim_requires_current_authority | insufficient_domain_context, historical_reference_with_current_policy_request | PASS |
| P7-EVAL-027 | phase_5, phase_6 | phase_5, phase_6 | unresolved_authority | unresolved_authority | none | none | historical_reference_requires_current_authority_before_prescriptive_answer, historical_commercial_claim_requires_current_authority | insufficient_domain_context, historical_reference_with_current_policy_request | PASS |
| P7-EVAL-028 | phase_5, phase_6 | phase_5, phase_6 | unresolved_authority | unresolved_authority | none | none | historical_reference_requires_current_authority_before_prescriptive_answer, historical_commercial_claim_requires_current_authority | insufficient_domain_context, historical_reference_with_current_policy_request | PASS |
| P7-EVAL-029 | phase_5, phase_6 | phase_5, phase_6 | authority_verification | authority_verification | none | none | historical_reference_requires_current_authority_before_prescriptive_answer, historical_commercial_claim_requires_current_authority, current_guidance_request_requires_phase_5 | insufficient_domain_context, historical_reference_with_current_policy_request | PASS |
| P7-EVAL-030 | phase_4, phase_6 | phase_4, phase_6 | authority_verification | authority_verification | operational_requirements | operational_requirements | current_deterministic_claim_requires_phase_4, historical_reference_requires_current_authority_before_prescriptive_answer | historical_reference_with_current_policy_request | PASS |
| P7-EVAL-031 | phase_4, phase_6 | phase_4, phase_6 | authority_verification | authority_verification | space_access | space_access | current_deterministic_claim_requires_phase_4, historical_reference_requires_current_authority_before_prescriptive_answer | historical_reference_with_current_policy_request | PASS |
| P7-EVAL-032 | phase_4, phase_5, phase_6 | phase_4, phase_5, phase_6 | authority_verification | authority_verification | service_rules | service_rules | current_deterministic_claim_requires_phase_4, historical_reference_requires_current_authority_before_prescriptive_answer, current_guidance_request_requires_phase_5 | historical_reference_with_current_policy_request | PASS |
| P7-EVAL-033 | phase_5 | phase_5 | unresolved_authority | unresolved_authority | none | none | none | ambiguous_deposit_type, insufficient_domain_context | PASS |
| P7-EVAL-034 | phase_5 | phase_5 | unresolved_authority | unresolved_authority | none | none | none | insufficient_domain_context | PASS |
| P7-EVAL-035 | phase_4, phase_5 | phase_4, phase_5 | unresolved_authority | unresolved_authority | technical_capability, technical_inventory | technical_inventory, technical_capability | current_deterministic_claim_requires_phase_4 | ambiguous_technical_inventory_vs_capability | PASS |
| P7-EVAL-036 | phase_4, phase_5 | phase_4, phase_5 | unresolved_authority | unresolved_authority | capacity | capacity | current_deterministic_claim_requires_phase_4 | none | PASS |
| P7-EVAL-037 | phase_6 | phase_6 | precedent_discovery | precedent_discovery | none | none | none | none | PASS |
| P7-EVAL-038 | phase_4, phase_5 | phase_4, phase_5 | deterministic_current | deterministic_current | payment | payment | current_deterministic_claim_requires_phase_4, current_guidance_request_requires_phase_5 | none | PASS |
| P7-EVAL-039 | phase_5, phase_6 | phase_5, phase_6 | authority_verification | authority_verification | none | none | current_guidance_request_requires_phase_5, historical_reference_requires_current_authority_before_prescriptive_answer | historical_reference_with_current_policy_request | PASS |
| P7-EVAL-040 | phase_5, phase_6 | phase_5, phase_6 | authority_verification | authority_verification | none | none | current_guidance_request_requires_phase_5, historical_reference_requires_current_authority_before_prescriptive_answer | historical_reference_with_current_policy_request | PASS |

## 5. Aggregate Metrics

- required-layer recall: `100%`
- exact required-layer-set accuracy: `100%`
- unnecessary-layer rate: `0%`
- query-class accuracy: `100%`
- Phase 4 required-domain recall: `100%`
- Phase 4 exact-domain-set accuracy: `100%`
- safety-override recall: `100%`

## 6. Failure Analysis

No benchmark failures remained after final deterministic rule tuning.

The main iteration themes before convergence were:

- guidance-heavy current questions needing explicit Phase 5 forcing
- historical “handled ... before” phrasing that required stronger precedent detection
- overly broad operational/access cues that needed narrowing for exact domain selectivity
- unresolved commercial conversion scenarios needing a distinct current-authority safety path

## 7. Ambiguity Analysis

Scenarios that still carry meaningful ambiguity flags despite passing include:

- mixed current/historical operational or supplier questions
- unresolved commercial conversion scenarios
- technical inventory versus capability overlaps
- security-deposit ambiguity

These ambiguities are exposed structurally through:

- `ambiguity_flags`
- `routing_confidence`
- `safety_overrides`

They are not hidden in prose reasoning traces.

## 8. LLM Router Decision

The deterministic/heuristic planner was sufficient for the full 40-scenario benchmark.

No model-assisted ambiguity resolver was required for `7.2B`.
