# Holdout Generalization Validation

- date: 2026-08-29
- run slug: `holdout2_scenarios_adjudicated_v2-20260829-123037`
- methodology: hosted staging operator API using the same real deployed intake/reconcile/waiting/draft path as calibration
- holdout version: `second-unseen-holdout-adjudicated-v2`
- holdout size: `12`
- environment: `APP_ENV=staging`, `Outlook=disabled`, `Asana=configured`, no provider execution used

## Summary

- A/B/C/D counts: `{'A': 12, 'B': 0, 'C': 0, 'D': 0}`
- A+B percentage: `100.0%`
- critical failures from baseline rubric: `0`
- unsupported claim count: `0`
- missing-information detection rate: `1.0`
- authority-conflict success rate: `1.0`
- confidentiality safety rate: `1.0`
- correct-next-action rate: `1.0`

## Semantic Uncertainty Matrix

| Holdout | Expected State | System State | Match |
| ------- | -------------- | ------------ | ----- |
| HOLD2-001 | known_conditional | known_conditional | yes |
| HOLD2-002 | known_yes | known_yes | yes |
| HOLD2-003 | known_no | known_no | yes |
| HOLD2-004 | known_no | known_no | yes |
| HOLD2-005 | known_no | known_no | yes |
| HOLD2-006 | known_conditional | known_conditional | yes |
| HOLD2-007 | known_conditional | known_conditional | yes |
| HOLD2-008 | unknown_internal | unknown_internal | yes |
| HOLD2-009 | missing_client_fact | missing_client_fact | yes |
| HOLD2-010 | missing_client_fact | missing_client_fact | yes |
| HOLD2-011 | missing_client_fact | missing_client_fact | yes |
| HOLD2-012 | known_no | known_no | yes |

## Holdout Findings

### HOLD2-001 — Projection-ready board briefing

- coverage: `second_unseen_known_yes`
- expected state: `known_conditional`
- system state: `known_conditional`
- edit burden: `A`
- failures: `[]`
- extra holdout failures: `[]`
- critical failures: `[]`
- facts: `{'guest_count': 12, 'event_type': 'projection-ready board briefing'}`
- feasibility: `{'Feasibility as requested': 'Requires confirmation', 'Supported alternative': 'Not established', 'Confirmation still required': 'Yes', 'Hard constraint': 'Structured confirmation or review must be completed before commitment.'}`
- open questions: `[]`
- actions: `['CREATE_INTERNAL_TASK_ITEM']`
- material proposition results: `[{'proposition': 'primary governed evaluation', 'expected_state': 'known_conditional', 'semantic_match': True, 'expected_action': 'internal_confirmation', 'action_match': True, 'evidence_scope': 'primary_case_outcome'}, {'proposition': 'technical:projection_display', 'expected_state': 'known_conditional', 'semantic_match': True, 'expected_action': None, 'action_match': None, 'evidence_scope': 'reasoning_projection_semantic_states'}, {'proposition': 'technical:audio_playback', 'expected_state': 'known_yes', 'semantic_match': True, 'expected_action': None, 'action_match': None, 'evidence_scope': 'reasoning_projection_semantic_states'}]`

### HOLD2-002 — Quiet planning circle

- coverage: `second_unseen_known_yes`
- expected state: `known_yes`
- system state: `known_yes`
- edit burden: `A`
- failures: `[]`
- extra holdout failures: `[]`
- critical failures: `[]`
- facts: `{'guest_count': 8, 'event_type': 'quiet planning circle'}`
- feasibility: `{'Feasibility as requested': 'Not yet evaluated', 'Supported alternative': 'Not established', 'Confirmation still required': 'No', 'Hard constraint': 'None'}`
- open questions: `[]`
- actions: `[]`
- material proposition results: `[{'proposition': 'primary governed evaluation', 'expected_state': 'known_yes', 'semantic_match': True, 'expected_action': 'deterministic_response', 'action_match': True, 'evidence_scope': 'primary_case_outcome'}, {'proposition': 'catering:external_caterer', 'expected_state': 'known_yes', 'semantic_match': True, 'expected_action': None, 'action_match': None, 'evidence_scope': 'isolated_case_outcome'}]`

### HOLD2-003 — DJ-led anniversary reception

- coverage: `second_unseen_known_no`
- expected state: `known_no`
- system state: `known_no`
- edit burden: `A`
- failures: `['confirmation_requirement_mismatch']`
- extra holdout failures: `[]`
- critical failures: `[]`
- facts: `{'guest_count': 22, 'event_type': 'dj-led anniversary reception'}`
- feasibility: `{'Feasibility as requested': 'Requires confirmation', 'Supported alternative': 'Not established', 'Confirmation still required': 'Yes', 'Hard constraint': 'Current authority must be resolved before consequential workflow commitment.'}`
- open questions: `[]`
- actions: `['CREATE_INTERNAL_TASK_ITEM']`
- material proposition results: `[{'proposition': 'primary governed evaluation', 'expected_state': 'known_no', 'semantic_match': True, 'expected_action': 'deterministic_response', 'action_match': True, 'evidence_scope': 'primary_case_outcome'}, {'proposition': 'technical:dj_sound_booth', 'expected_state': 'known_no', 'semantic_match': True, 'expected_action': None, 'action_match': None, 'evidence_scope': 'reasoning_projection_semantic_states'}]`

### HOLD2-004 — Oversized studio awards huddle

- coverage: `second_unseen_known_no`
- expected state: `known_no`
- system state: `known_no`
- edit burden: `A`
- failures: `['confirmation_requirement_mismatch']`
- extra holdout failures: `[]`
- critical failures: `[]`
- facts: `{'guest_count': 58, 'event_type': 'oversized studio awards huddle'}`
- feasibility: `{'Feasibility as requested': 'Requires confirmation', 'Supported alternative': 'Not established', 'Confirmation still required': 'Yes', 'Hard constraint': 'Current governed policy does not support the requested commitment as stated.'}`
- open questions: `[]`
- actions: `['CREATE_INTERNAL_TASK_ITEM']`
- material proposition results: `[{'proposition': 'primary governed evaluation', 'expected_state': 'known_no', 'semantic_match': True, 'expected_action': 'deterministic_response', 'action_match': True, 'evidence_scope': 'primary_case_outcome'}, {'proposition': 'facilitator:wnc_provided', 'expected_state': 'known_conditional', 'semantic_match': True, 'expected_action': None, 'action_match': None, 'evidence_scope': 'reasoning_projection_semantic_states'}]`

### HOLD2-005 — Amplified product reveal

- coverage: `second_unseen_known_conditional`
- expected state: `known_no`
- system state: `known_no`
- edit burden: `A`
- failures: `[]`
- extra holdout failures: `[]`
- critical failures: `[]`
- facts: `{'guest_count': 20, 'event_type': 'amplified product reveal'}`
- feasibility: `{'Feasibility as requested': 'Not yet evaluated', 'Supported alternative': 'Not established', 'Confirmation still required': 'No', 'Hard constraint': 'Current governed policy does not support the requested commitment as stated.'}`
- open questions: `[]`
- actions: `[]`
- material proposition results: `[{'proposition': 'primary governed evaluation', 'expected_state': 'known_no', 'semantic_match': True, 'expected_action': 'deterministic_response', 'action_match': True, 'evidence_scope': 'primary_case_outcome'}, {'proposition': 'technical:enhanced_sound_system', 'expected_state': 'known_no', 'semantic_match': True, 'expected_action': None, 'action_match': None, 'evidence_scope': 'reasoning_projection_semantic_states'}]`

### HOLD2-006 — Facilitated strategy offsite

- coverage: `second_unseen_known_conditional`
- expected state: `known_conditional`
- system state: `known_conditional`
- edit burden: `A`
- failures: `[]`
- extra holdout failures: `[]`
- critical failures: `[]`
- facts: `{'guest_count': 16, 'event_type': 'facilitated strategy offsite'}`
- feasibility: `{'Feasibility as requested': 'Requires confirmation', 'Supported alternative': 'Not established', 'Confirmation still required': 'Yes', 'Hard constraint': 'Structured confirmation or review must be completed before commitment.'}`
- open questions: `[]`
- actions: `['CREATE_INTERNAL_TASK_ITEM']`
- material proposition results: `[{'proposition': 'primary governed evaluation', 'expected_state': 'known_conditional', 'semantic_match': True, 'expected_action': 'state_condition_or_confirm', 'action_match': True, 'evidence_scope': 'primary_case_outcome'}, {'proposition': 'facilitator:wnc_provided', 'expected_state': 'known_conditional', 'semantic_match': True, 'expected_action': None, 'action_match': None, 'evidence_scope': 'reasoning_projection_semantic_states'}]`

### HOLD2-007 — Custom immersive lab

- coverage: `second_unseen_unknown_internal`
- expected state: `known_conditional`
- system state: `known_conditional`
- edit burden: `A`
- failures: `[]`
- extra holdout failures: `[]`
- critical failures: `[]`
- facts: `{'guest_count': 18, 'event_type': 'custom immersive lab'}`
- feasibility: `{'Feasibility as requested': 'Requires confirmation', 'Supported alternative': 'Not established', 'Confirmation still required': 'Yes', 'Hard constraint': 'Structured confirmation or review must be completed before commitment.'}`
- open questions: `[]`
- actions: `['CREATE_INTERNAL_TASK_ITEM']`
- material proposition results: `[{'proposition': 'primary governed evaluation', 'expected_state': 'known_conditional', 'semantic_match': True, 'expected_action': 'internal_confirmation', 'action_match': True, 'evidence_scope': 'primary_case_outcome'}, {'proposition': 'technical:other_technical', 'expected_state': 'known_conditional', 'semantic_match': True, 'expected_action': None, 'action_match': None, 'evidence_scope': 'reasoning_projection_semantic_states'}]`

### HOLD2-008 — Bespoke experience consultation

- coverage: `second_unseen_unknown_internal`
- expected state: `unknown_internal`
- system state: `unknown_internal`
- edit burden: `A`
- failures: `[]`
- extra holdout failures: `[]`
- critical failures: `[]`
- facts: `{'guest_count': 14, 'event_type': 'bespoke experience consultation'}`
- feasibility: `{'Feasibility as requested': 'Requires confirmation', 'Supported alternative': 'Not established', 'Confirmation still required': 'Yes', 'Hard constraint': 'Current authority must be resolved before consequential workflow commitment.'}`
- open questions: `[]`
- actions: `['CREATE_INTERNAL_TASK_ITEM']`
- material proposition results: `[{'proposition': 'primary governed evaluation', 'expected_state': 'unknown_internal', 'semantic_match': True, 'expected_action': 'internal_confirmation', 'action_match': True, 'evidence_scope': 'primary_case_outcome'}, {'proposition': 'facilitator:custom_experience_design', 'expected_state': 'unknown_internal', 'semantic_match': True, 'expected_action': None, 'action_match': None, 'evidence_scope': 'reasoning_projection_semantic_states'}]`

### HOLD2-009 — Timed lunch briefing

- coverage: `second_unseen_missing_client_fact`
- expected state: `missing_client_fact`
- system state: `missing_client_fact`
- edit burden: `A`
- failures: `[]`
- extra holdout failures: `[]`
- critical failures: `[]`
- facts: `{'guest_count': 24, 'event_type': 'timed lunch briefing'}`
- feasibility: `{'Feasibility as requested': 'Requires confirmation', 'Supported alternative': 'Not established', 'Confirmation still required': 'Yes', 'Hard constraint': 'Open question 1200 must be resolved.'}`
- open questions: `['requested_event_timing']`
- actions: `['CREATE_INTERNAL_TASK_ITEM', 'CREATE_INTERNAL_TASK_ITEM', 'REQUEST_CLIENT_INFORMATION']`
- material proposition results: `[{'proposition': 'primary governed evaluation', 'expected_state': 'missing_client_fact', 'semantic_match': True, 'expected_action': 'request_client_information', 'action_match': True, 'evidence_scope': 'primary_case_outcome'}, {'proposition': 'technical:projection_display', 'expected_state': 'known_conditional', 'semantic_match': True, 'expected_action': None, 'action_match': None, 'evidence_scope': 'reasoning_projection_semantic_states'}]`

### HOLD2-010 — Scope-unspecified member salon

- coverage: `second_unseen_missing_client_fact`
- expected state: `missing_client_fact`
- system state: `missing_client_fact`
- edit burden: `A`
- failures: `[]`
- extra holdout failures: `[]`
- critical failures: `[]`
- facts: `{'guest_count': 26, 'event_type': 'scope-unspecified member salon'}`
- feasibility: `{'Feasibility as requested': 'Not yet evaluated', 'Supported alternative': 'Not established', 'Confirmation still required': 'Yes', 'Hard constraint': 'Open question 1206 must be resolved.'}`
- open questions: `['requested_rental_scope']`
- actions: `['REQUEST_CLIENT_INFORMATION']`
- material proposition results: `[{'proposition': 'primary governed evaluation', 'expected_state': 'missing_client_fact', 'semantic_match': True, 'expected_action': 'request_client_information', 'action_match': True, 'evidence_scope': 'primary_case_outcome'}, {'proposition': 'technical:audio_playback', 'expected_state': 'known_yes', 'semantic_match': True, 'expected_action': None, 'action_match': None, 'evidence_scope': 'reasoning_projection_semantic_states'}]`

### HOLD2-011 — Hybrid curator dinner

- coverage: `second_unseen_missing_client_fact`
- expected state: `missing_client_fact`
- system state: `missing_client_fact`
- edit burden: `A`
- failures: `[]`
- extra holdout failures: `[]`
- critical failures: `[]`
- facts: `{'guest_count': 28, 'event_type': 'hybrid curator dinner'}`
- feasibility: `{'Feasibility as requested': 'Requires confirmation', 'Supported alternative': 'Not established', 'Confirmation still required': 'Yes', 'Hard constraint': 'Open question 1208 must be resolved.'}`
- open questions: `['requested_event_timing']`
- actions: `['CREATE_INTERNAL_TASK_ITEM', 'CREATE_INTERNAL_TASK_ITEM', 'REQUEST_CLIENT_INFORMATION']`
- material proposition results: `[{'proposition': 'primary governed evaluation', 'expected_state': 'missing_client_fact', 'semantic_match': True, 'expected_action': 'request_client_information', 'action_match': True, 'evidence_scope': 'primary_case_outcome'}, {'proposition': 'technical:projection_display', 'expected_state': 'known_conditional', 'semantic_match': True, 'expected_action': None, 'action_match': None, 'evidence_scope': 'reasoning_projection_semantic_states'}, {'proposition': 'technical:other_technical', 'expected_state': 'unknown_internal', 'semantic_match': True, 'expected_action': None, 'action_match': None, 'evidence_scope': 'reasoning_projection_semantic_states'}, {'proposition': 'facilitator:client_external_caterer', 'expected_state': 'known_conditional', 'semantic_match': True, 'expected_action': None, 'action_match': None, 'evidence_scope': 'reasoning_projection_semantic_states'}]`

### HOLD2-012 — Capacity-limited sound salon

- coverage: `second_unseen_known_no`
- expected state: `known_no`
- system state: `known_no`
- edit burden: `A`
- failures: `['confirmation_requirement_mismatch']`
- extra holdout failures: `[]`
- critical failures: `[]`
- facts: `{'guest_count': 62, 'event_type': 'capacity-limited sound salon'}`
- feasibility: `{'Feasibility as requested': 'Requires confirmation', 'Supported alternative': 'Not established', 'Confirmation still required': 'Yes', 'Hard constraint': 'Current governed policy does not support the requested commitment as stated.'}`
- open questions: `[]`
- actions: `['CREATE_INTERNAL_TASK_ITEM']`
- material proposition results: `[{'proposition': 'primary governed evaluation', 'expected_state': 'known_no', 'semantic_match': True, 'expected_action': 'deterministic_response', 'action_match': True, 'evidence_scope': 'primary_case_outcome'}, {'proposition': 'technical:other_technical', 'expected_state': 'known_conditional', 'semantic_match': True, 'expected_action': None, 'action_match': None, 'evidence_scope': 'reasoning_projection_semantic_states'}]`
