# Required Semantic Realization Gate

Implemented and deployed. Targeted UAT-012 passes all three turns. The full run persists all 21 drafts with complete required answers and three bounded corrections, but overall acceptance requires review because UAT-006/2 repeats its report-back promise. No further implementation or generation cycle followed.

A generated candidate now passes safety validation first, then a deterministic completeness gate, before any immutable DraftRevision, send action or approval is created for that candidate. The existing planner v3 selects content; the new boundary does not change facts, retrieval or editorial budgets.

Typed requirements distinguish questions, known assertions, restrictions, commercial truth, pending actions, conditional capability checks, practical guidance and recorded external states. Only MUST_ASK and MUST_COMMUNICATE items require current-turn realization. ACKNOWLEDGE and HELPFUL_NOW remain optional; DEFER, INTERNAL_ONLY and ALREADY_COMMUNICATED create no current-turn obligations. Unknown mandatory shapes fail closed.

Audio reuses the item-scoped positive-capability witness, with support for natural WNC-can-accommodate wording. Acknowledgements and future checks fail. Other supported shapes reuse existing witnesses with question-component, sentence and action scope. These are bounded deterministic language witnesses, not a universal semantic parser or an LLM judge.

# Corrective Retry

One safe initial candidate missing required meaning receives one corrective request. It carries the original client-safe payload, initial candidate and typed unmet meanings, with no prescribed final sentence. No extra facts or retrieval are added. The same DraftContract object, case revision, context hash, plan, authoritative facts, recipient and response intent remain bound across both attempts. Case state, events, facts and recipient metadata are rechecked before acceptance; a changed binding stops the operation.

Safety-invalid candidates do not enter this retry mechanism. Both candidates undergo safety validation; only a safe, complete final candidate may persist. A second omission or any corrected-candidate safety failure rejects the operation. Provider failures are not retried by this policy. Internal candidate attempts do not create client turns or DraftRevisions. Existing exact revision reuse preserves approval state.

Audit records include attempt numbers, provider request/response identifiers, initial/corrected candidate hashes, unmet semantic keys, correction reason, final realization results and contract/plan identities. The initial omitted candidate remains non-current and non-approvable. Hash-only first-candidate evidence avoids retaining unnecessary prose. Correction-provider failures preserve the initial audit in a failure event.

# Provider-Free Tests

All 15 requested cases are covered: positive audio variants; rejection of acknowledgement/check language; exactly one correction; successful corrected acceptance; exhaustion; no safety retry; immutable bindings; only-final persistence; non-approvable first candidate; valid turn-one realization and turn-two/three ALREADY_COMMUNICATED suppression; explicit reopening. Further regressions cover prices/VAT, restrictions, pending decisions, multiple next-step subjects, missing question components, stale recipient/events, provider failure audit and existing-revision reuse.

45 new tests pass. Applying the gate offline to the previous 21 saved outputs flags exactly the three demonstrated audio omissions. No historical output was regenerated.

# UAT-012 Targeted Test

```json
{
  "result": "PASS",
  "assessment_method": "Direct assistant review of all exact drafts, plan/audit evidence and provider-free case snapshot; no LLM judge",
  "persisted_drafts": "3/3",
  "case_id": 569,
  "retry_count_per_turn": [
    0,
    0,
    0
  ],
  "model_candidates": 3,
  "safety_failures": 0,
  "unanswered_required_semantic_items": 0,
  "repetition": 0,
  "unnecessary_year_questions": 0,
  "turns": [
    {
      "turn": 1,
      "grade": "B",
      "assessment": "Directly states light background music playback is available; practical projection setup remains a check. Kitchen constraint, fee and adjustment checks, facilitator availability/format, and day/start/finish/headcount questions are present. Slightly formal opening is harmless. Audio realization is recorded."
    },
    {
      "turn": 2,
      "grade": "A",
      "assessment": "Audio is ALREADY_COMMUNICATED and omitted. The 24-person update, flexible 20-minute welcome, fee/adjustment and facilitator checks are covered. Only day/start/finish remain questions."
    },
    {
      "turn": 3,
      "grade": "A",
      "assessment": "Audio remains ALREADY_COMMUNICATED and omitted. EUR 75 excl. VAT and 21% VAT are stated. Adjustment and facilitator checks remain prospective. The timestamped January date resolves to 2027; no date/year question remains."
    }
  ],
  "retry_demonstration": "Targeted model candidates were complete on their initial attempt; corrective behavior is demonstrated by provider-free transport/persistence tests, not a live retry in this targeted sample."
}
```

## UAT-012/1

DraftRevision 360; exact action/revision/content/context/recipient/approval binding checked provider-free.

Subject:

```text
January Studio gathering
```

Body:

```text
Hi Ari,

Your plans for a January gathering in the Studio sound thoughtful. WNC’s projector can display your slides, and light background music playback is available. I’ll check the practical projection setup, along with the availability and format of a short facilitator-led opening.

For your outside caterer, the kitchen is suitable for ready-made food, warming, plating and simple assembly, rather than large-scale food production. I’ll also check the booking fee for your request and what, if any, adjustment can be arranged.

What day, start time and finish time would you like? How many guests are expected?
```

```json
{
  "attempts": [
    {
      "candidate_hash": "808527135f11e4f6c01c48f1b4666d97bac8192ce2e5763e3ad1444d0e056752",
      "failed_realization_item_ids": [],
      "generation_attempt": 1,
      "provider_request_id": "req_d5f2816203644abe8dbb52ae24d95587",
      "provider_response_id": "resp_01ecb10adeb8eb7f016ac0d8d8209c87d2b7f293be0243b3a0",
      "realization_results": [
        {
          "fingerprint": "9b363ec03f13be4df3759887a35044d4f52ed62dbd78881b3733ab1c0d85f896",
          "kind": "question",
          "realized": true,
          "required_meaning": {
            "open_question_id": 2196,
            "question": "What day, start time and finish time would you like?"
          },
          "semantic_key": "question:2196",
          "topic": "client_information"
        },
        {
          "fingerprint": "d8e91680d1479430425f9d1136304343050d769f9433385a8dc73ecc9210766b",
          "kind": "question",
          "realized": true,
          "required_meaning": {
            "open_question_id": 2197,
            "question": "How many guests are expected?"
          },
          "semantic_key": "question:2197",
          "topic": "client_information"
        },
        {
          "fingerprint": "ce5b101ef2c0cf0ac8e6f03a94d256bc5bdcc8cd709f95396f8a767d60c2d110",
          "kind": "pending_action",
          "realized": true,
          "required_meaning": {
            "action": "check requested booking fee or pricing",
            "status": "check_required"
          },
          "semantic_key": "commercial.check",
          "topic": "commercial_next_step"
        },
        {
          "fingerprint": "01147dc1762bf2076f3036fcf36755e656ccd63e701a5fbc425912ce7dfd5a3c",
          "kind": "pending_action",
          "realized": true,
          "required_meaning": {
            "action": "check what can be arranged",
            "request": "booking fee adjustment",
            "status": "check_required"
          },
          "semantic_key": "decision:booking fee override",
          "topic": "commercial_next_step"
        },
        {
          "fingerprint": "8ba654ac396fc19822cecd67c06d7a927fd97238ba66a337daa3b0d9c888d61a",
          "kind": "guidance",
          "realized": true,
          "required_meaning": {
            "limitation": "not large-scale food production",
            "suitable_for": [
              "ready-made food",
              "warming",
              "plating",
              "simple assembly"
            ]
          },
          "semantic_key": "fact:catering_kitchen",
          "topic": "catering_kitchen"
        },
        {
          "fingerprint": "611225d828231fc1d2df193b9e2b6261ba6eff562cf33deb3a4577cc0218ebd0",
          "kind": "conditional_capability",
          "realized": true,
          "required_meaning": {
            "available_equipment": "WNC projector",
            "capability": "projection display",
            "check_required": [
              "practical projection setup"
            ],
            "status": "conditional"
          },
          "semantic_key": "fact:projection_display",
          "topic": "projection_display"
        },
        {
          "fingerprint": "56b7098e5b0a9ac30ba8cfde8467b7169972402c237cfbc411622176ff694303",
          "kind": "known_fact",
          "realized": true,
          "required_meaning": {
            "action_required": false,
            "client_fact": {
              "background_music_playback": true
            },
            "fact_state": "known"
          },
          "semantic_key": "fact:audio_playback",
          "topic": "audio_playback"
        },
        {
          "fingerprint": "52a59b6b10803b5e268da5805c92f7136caa50cd2a3f3f93eca4aa0365abb88c",
          "kind": "pending_action",
          "realized": true,
          "required_meaning": {
            "action": "check",
            "status": "check_required",
            "subjects": [
              "requested facilitator availability and format"
            ]
          },
          "semantic_key": "next_step",
          "topic": "next_step"
        }
      ],
      "safety_failure_codes": []
    }
  ],
  "context_hash": "df8411953c09eefb1e4923cf834f5a5318929992d974f2c483041e8779f24d70",
  "contract_identity": "d37683a448a7be161f64dd4c2f7c4e619d7221b23a44bea01d2fc53255075cea",
  "corrective_retry_count": 0,
  "final_realization_results": [
    {
      "fingerprint": "9b363ec03f13be4df3759887a35044d4f52ed62dbd78881b3733ab1c0d85f896",
      "kind": "question",
      "realized": true,
      "required_meaning": {
        "open_question_id": 2196,
        "question": "What day, start time and finish time would you like?"
      },
      "semantic_key": "question:2196",
      "topic": "client_information"
    },
    {
      "fingerprint": "d8e91680d1479430425f9d1136304343050d769f9433385a8dc73ecc9210766b",
      "kind": "question",
      "realized": true,
      "required_meaning": {
        "open_question_id": 2197,
        "question": "How many guests are expected?"
      },
      "semantic_key": "question:2197",
      "topic": "client_information"
    },
    {
      "fingerprint": "ce5b101ef2c0cf0ac8e6f03a94d256bc5bdcc8cd709f95396f8a767d60c2d110",
      "kind": "pending_action",
      "realized": true,
      "required_meaning": {
        "action": "check requested booking fee or pricing",
        "status": "check_required"
      },
      "semantic_key": "commercial.check",
      "topic": "commercial_next_step"
    },
    {
      "fingerprint": "01147dc1762bf2076f3036fcf36755e656ccd63e701a5fbc425912ce7dfd5a3c",
      "kind": "pending_action",
      "realized": true,
      "required_meaning": {
        "action": "check what can be arranged",
        "request": "booking fee adjustment",
        "status": "check_required"
      },
      "semantic_key": "decision:booking fee override",
      "topic": "commercial_next_step"
    },
    {
      "fingerprint": "8ba654ac396fc19822cecd67c06d7a927fd97238ba66a337daa3b0d9c888d61a",
      "kind": "guidance",
      "realized": true,
      "required_meaning": {
        "limitation": "not large-scale food production",
        "suitable_for": [
          "ready-made food",
          "warming",
          "plating",
          "simple assembly"
        ]
      },
      "semantic_key": "fact:catering_kitchen",
      "topic": "catering_kitchen"
    },
    {
      "fingerprint": "611225d828231fc1d2df193b9e2b6261ba6eff562cf33deb3a4577cc0218ebd0",
      "kind": "conditional_capability",
      "realized": true,
      "required_meaning": {
        "available_equipment": "WNC projector",
        "capability": "projection display",
        "check_required": [
          "practical projection setup"
        ],
        "status": "conditional"
      },
      "semantic_key": "fact:projection_display",
      "topic": "projection_display"
    },
    {
      "fingerprint": "56b7098e5b0a9ac30ba8cfde8467b7169972402c237cfbc411622176ff694303",
      "kind": "known_fact",
      "realized": true,
      "required_meaning": {
        "action_required": false,
        "client_fact": {
          "background_music_playback": true
        },
        "fact_state": "known"
      },
      "semantic_key": "fact:audio_playback",
      "topic": "audio_playback"
    },
    {
      "fingerprint": "52a59b6b10803b5e268da5805c92f7136caa50cd2a3f3f93eca4aa0365abb88c",
      "kind": "pending_action",
      "realized": true,
      "required_meaning": {
        "action": "check",
        "status": "check_required",
        "subjects": [
          "requested facilitator availability and format"
        ]
      },
      "semantic_key": "next_step",
      "topic": "next_step"
    }
  ],
  "initial_candidate_hash": "808527135f11e4f6c01c48f1b4666d97bac8192ce2e5763e3ad1444d0e056752",
  "plan_identity": "2ae8ab877c11aa18f77c013f02910ccb3ce4f57f3134d4d096c2601cd5bd31ad",
  "policy": "required_realization_single_correction_v1",
  "source_case_revision": 2
}
```

## UAT-012/2

DraftRevision 361; exact action/revision/content/context/recipient/approval binding checked provider-free.

Subject:

```text
Updated group plans
```

Body:

```text
Hi Ari,

The update to 24 people and a flexible 20-minute welcome is helpful. Once the timing is clearer, I’ll check the requested facilitator availability and format, as well as the booking fee and what adjustment can be arranged.

What day, start time and finish time would you like?
```

```json
{
  "attempts": [
    {
      "candidate_hash": "6e872cd7d61b124dfb00a2bd78cb435f91bed0fe501b5cdad3fe18a1431895df",
      "failed_realization_item_ids": [],
      "generation_attempt": 1,
      "provider_request_id": "req_741c866d1a6f4391b8427df1aed82b48",
      "provider_response_id": "resp_0ab3b3d7b6aaa3d7016ac0d8ef978087d2be6be542ed7ea039",
      "realization_results": [
        {
          "fingerprint": "9b363ec03f13be4df3759887a35044d4f52ed62dbd78881b3733ab1c0d85f896",
          "kind": "question",
          "realized": true,
          "required_meaning": {
            "open_question_id": 2196,
            "question": "What day, start time and finish time would you like?"
          },
          "semantic_key": "question:2196",
          "topic": "client_information"
        },
        {
          "fingerprint": "ce5b101ef2c0cf0ac8e6f03a94d256bc5bdcc8cd709f95396f8a767d60c2d110",
          "kind": "pending_action",
          "realized": true,
          "required_meaning": {
            "action": "check requested booking fee or pricing",
            "status": "check_required"
          },
          "semantic_key": "commercial.check",
          "topic": "commercial_next_step"
        },
        {
          "fingerprint": "01147dc1762bf2076f3036fcf36755e656ccd63e701a5fbc425912ce7dfd5a3c",
          "kind": "pending_action",
          "realized": true,
          "required_meaning": {
            "action": "check what can be arranged",
            "request": "booking fee adjustment",
            "status": "check_required"
          },
          "semantic_key": "decision:booking fee override",
          "topic": "commercial_next_step"
        },
        {
          "fingerprint": "52a59b6b10803b5e268da5805c92f7136caa50cd2a3f3f93eca4aa0365abb88c",
          "kind": "pending_action",
          "realized": true,
          "required_meaning": {
            "action": "check",
            "status": "check_required",
            "subjects": [
              "requested facilitator availability and format"
            ]
          },
          "semantic_key": "next_step",
          "topic": "next_step"
        }
      ],
      "safety_failure_codes": []
    }
  ],
  "context_hash": "e48755306968a0ea3bf3d1747fb27052eb3a0d6b9c0f58b5550e386e66e600a0",
  "contract_identity": "f4ab1194f776a733849dd9233e9ee8bb08662884a1ed3b009094eabebf145880",
  "corrective_retry_count": 0,
  "final_realization_results": [
    {
      "fingerprint": "9b363ec03f13be4df3759887a35044d4f52ed62dbd78881b3733ab1c0d85f896",
      "kind": "question",
      "realized": true,
      "required_meaning": {
        "open_question_id": 2196,
        "question": "What day, start time and finish time would you like?"
      },
      "semantic_key": "question:2196",
      "topic": "client_information"
    },
    {
      "fingerprint": "ce5b101ef2c0cf0ac8e6f03a94d256bc5bdcc8cd709f95396f8a767d60c2d110",
      "kind": "pending_action",
      "realized": true,
      "required_meaning": {
        "action": "check requested booking fee or pricing",
        "status": "check_required"
      },
      "semantic_key": "commercial.check",
      "topic": "commercial_next_step"
    },
    {
      "fingerprint": "01147dc1762bf2076f3036fcf36755e656ccd63e701a5fbc425912ce7dfd5a3c",
      "kind": "pending_action",
      "realized": true,
      "required_meaning": {
        "action": "check what can be arranged",
        "request": "booking fee adjustment",
        "status": "check_required"
      },
      "semantic_key": "decision:booking fee override",
      "topic": "commercial_next_step"
    },
    {
      "fingerprint": "52a59b6b10803b5e268da5805c92f7136caa50cd2a3f3f93eca4aa0365abb88c",
      "kind": "pending_action",
      "realized": true,
      "required_meaning": {
        "action": "check",
        "status": "check_required",
        "subjects": [
          "requested facilitator availability and format"
        ]
      },
      "semantic_key": "next_step",
      "topic": "next_step"
    }
  ],
  "initial_candidate_hash": "6e872cd7d61b124dfb00a2bd78cb435f91bed0fe501b5cdad3fe18a1431895df",
  "plan_identity": "c17c19f2fc38456560983425090e3bef5639441b40fb9ca81e969a51a9f8cd10",
  "policy": "required_realization_single_correction_v1",
  "source_case_revision": 3
}
```

## UAT-012/3

DraftRevision 362; exact action/revision/content/context/recipient/approval binding checked provider-free.

Subject:

```text
21 January gathering
```

Body:

```text
Hi Ari,

Thanks for confirming the gathering would be on 21 January from 17:00 to 21:00.

The booking fee is EUR 75 excl. VAT, with VAT at 21%. I’ll check what can be arranged regarding an adjustment to the fee, along with the requested facilitator’s availability and format.
```

```json
{
  "attempts": [
    {
      "candidate_hash": "c2f9199cf07b4feb70242afef98c30926e7f62b60065ddb54bbcd8a36c850015",
      "failed_realization_item_ids": [],
      "generation_attempt": 1,
      "provider_request_id": "req_d3ccff0551c34fe2b0ab5c4027f204f6",
      "provider_response_id": "resp_092b7f226d04ae3a016ac0d8fff8c887d283db485a26802c80",
      "realization_results": [
        {
          "fingerprint": "d48a4e749f26bd87be6140eb859f17d122a1ad07af3a4144f1406fc448f23d20",
          "kind": "commercial",
          "realized": true,
          "required_meaning": {
            "booking_fee": "EUR 75 excl. VAT",
            "vat": "21%"
          },
          "semantic_key": "commercial.current",
          "topic": "commercial"
        },
        {
          "fingerprint": "01147dc1762bf2076f3036fcf36755e656ccd63e701a5fbc425912ce7dfd5a3c",
          "kind": "pending_action",
          "realized": true,
          "required_meaning": {
            "action": "check what can be arranged",
            "request": "booking fee adjustment",
            "status": "check_required"
          },
          "semantic_key": "decision:booking fee override",
          "topic": "commercial_next_step"
        },
        {
          "fingerprint": "52a59b6b10803b5e268da5805c92f7136caa50cd2a3f3f93eca4aa0365abb88c",
          "kind": "pending_action",
          "realized": true,
          "required_meaning": {
            "action": "check",
            "status": "check_required",
            "subjects": [
              "requested facilitator availability and format"
            ]
          },
          "semantic_key": "next_step",
          "topic": "next_step"
        }
      ],
      "safety_failure_codes": []
    }
  ],
  "context_hash": "32656ee4099a8920451ecb71007c2a931806ab57586a84b9128bf03ac284d50f",
  "contract_identity": "e45561598b7dd00e62e89d29d6390a29a29a6305135f64d87f0c89881d4b5832",
  "corrective_retry_count": 0,
  "final_realization_results": [
    {
      "fingerprint": "d48a4e749f26bd87be6140eb859f17d122a1ad07af3a4144f1406fc448f23d20",
      "kind": "commercial",
      "realized": true,
      "required_meaning": {
        "booking_fee": "EUR 75 excl. VAT",
        "vat": "21%"
      },
      "semantic_key": "commercial.current",
      "topic": "commercial"
    },
    {
      "fingerprint": "01147dc1762bf2076f3036fcf36755e656ccd63e701a5fbc425912ce7dfd5a3c",
      "kind": "pending_action",
      "realized": true,
      "required_meaning": {
        "action": "check what can be arranged",
        "request": "booking fee adjustment",
        "status": "check_required"
      },
      "semantic_key": "decision:booking fee override",
      "topic": "commercial_next_step"
    },
    {
      "fingerprint": "52a59b6b10803b5e268da5805c92f7136caa50cd2a3f3f93eca4aa0365abb88c",
      "kind": "pending_action",
      "realized": true,
      "required_meaning": {
        "action": "check",
        "status": "check_required",
        "subjects": [
          "requested facilitator availability and format"
        ]
      },
      "semantic_key": "next_step",
      "topic": "next_step"
    }
  ],
  "initial_candidate_hash": "c2f9199cf07b4feb70242afef98c30926e7f62b60065ddb54bbcd8a36c850015",
  "plan_identity": "58189ed32aada22bc68d0124611473c70b886d0f7107abe45cd26b6f25016bd7",
  "policy": "required_realization_single_correction_v1",
  "source_case_revision": 4
}
```

## Realization and continuity evidence

### 360

```json
{
  "must_say": [
    {
      "action": "check requested booking fee or pricing",
      "status": "check_required",
      "topic": "commercial_next_step"
    },
    {
      "action": "check what can be arranged",
      "request": "booking fee adjustment",
      "status": "check_required",
      "topic": "commercial_next_step"
    },
    {
      "limitation": "not large-scale food production",
      "suitable_for": [
        "ready-made food",
        "warming",
        "plating",
        "simple assembly"
      ],
      "topic": "catering_kitchen"
    },
    {
      "available_equipment": "WNC projector",
      "capability": "projection display",
      "check_required": [
        "practical projection setup"
      ],
      "status": "conditional",
      "topic": "projection_display"
    },
    {
      "action_required": false,
      "client_fact": {
        "background_music_playback": true
      },
      "fact_state": "known",
      "topic": "audio_playback"
    },
    {
      "action": "check",
      "status": "check_required",
      "subjects": [
        "requested facilitator availability and format"
      ],
      "topic": "next_step"
    }
  ],
  "audio_projection_items": [
    {
      "authority_class": "current_governed",
      "fingerprint": "611225d828231fc1d2df193b9e2b6261ba6eff562cf33deb3a4577cc0218ebd0",
      "included_in_model_payload": true,
      "prior_turn_status": "not_previously_communicated",
      "priority": 1,
      "proposition_key": "fact:projection_display",
      "reason": "requested_technical_capability",
      "role": "MUST_COMMUNICATE",
      "semantic_key": "fact:projection_display",
      "source_reference": "phase4:technical_projection_display_confirmation",
      "topic": "projection_display",
      "value": {
        "available_equipment": "WNC projector",
        "capability": "projection display",
        "check_required": [
          "practical projection setup"
        ],
        "status": "conditional"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "56b7098e5b0a9ac30ba8cfde8467b7169972402c237cfbc411622176ff694303",
      "included_in_model_payload": true,
      "prior_turn_status": "not_previously_communicated",
      "priority": 1,
      "proposition_key": "fact:audio_playback",
      "reason": "requested_technical_capability",
      "role": "MUST_COMMUNICATE",
      "semantic_key": "fact:audio_playback",
      "source_reference": "phase4:technical_audio_playback_supported",
      "topic": "audio_playback",
      "value": {
        "action_required": false,
        "client_fact": {
          "background_music_playback": true
        },
        "fact_state": "known"
      }
    }
  ],
  "communicated_editorial_items": [
    {
      "fingerprint": "8ba654ac396fc19822cecd67c06d7a927fd97238ba66a337daa3b0d9c888d61a",
      "semantic_key": "fact:catering_kitchen",
      "source_reference": "SERV-003",
      "topic": "catering_kitchen"
    },
    {
      "fingerprint": "56b7098e5b0a9ac30ba8cfde8467b7169972402c237cfbc411622176ff694303",
      "semantic_key": "fact:audio_playback",
      "source_reference": "phase4:technical_audio_playback_supported",
      "topic": "audio_playback"
    }
  ],
  "do_not_repeat_topics": []
}
```

### 361

```json
{
  "must_say": [
    {
      "action": "check requested booking fee or pricing",
      "status": "check_required",
      "topic": "commercial_next_step"
    },
    {
      "action": "check what can be arranged",
      "request": "booking fee adjustment",
      "status": "check_required",
      "topic": "commercial_next_step"
    },
    {
      "action": "check",
      "status": "check_required",
      "subjects": [
        "requested facilitator availability and format"
      ],
      "topic": "next_step"
    }
  ],
  "audio_projection_items": [
    {
      "authority_class": "current_governed",
      "fingerprint": "56b7098e5b0a9ac30ba8cfde8467b7169972402c237cfbc411622176ff694303",
      "included_in_model_payload": false,
      "prior_turn_status": "unchanged_answer_in_prior_draft",
      "priority": 50,
      "proposition_key": "fact:audio_playback",
      "reason": "unchanged_answer_already_explained",
      "role": "ALREADY_COMMUNICATED",
      "semantic_key": "fact:audio_playback",
      "source_reference": "phase4:technical_audio_playback_supported",
      "topic": "audio_playback",
      "value": {
        "action_required": false,
        "client_fact": {
          "background_music_playback": true
        },
        "fact_state": "known"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "611225d828231fc1d2df193b9e2b6261ba6eff562cf33deb3a4577cc0218ebd0",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 50,
      "proposition_key": "fact:projection_display",
      "reason": "not_needed_in_current_turn",
      "role": "DEFER",
      "semantic_key": "fact:projection_display",
      "source_reference": "phase4:technical_projection_display_confirmation",
      "topic": "projection_display",
      "value": {
        "available_equipment": "WNC projector",
        "capability": "projection display",
        "check_required": [
          "practical projection setup"
        ],
        "status": "conditional"
      }
    }
  ],
  "communicated_editorial_items": [],
  "do_not_repeat_topics": [
    "catering_kitchen",
    "audio_playback"
  ]
}
```

### 362

```json
{
  "must_say": [
    {
      "booking_fee": "EUR 75 excl. VAT",
      "topic": "commercial",
      "vat": "21%"
    },
    {
      "action": "check what can be arranged",
      "request": "booking fee adjustment",
      "status": "check_required",
      "topic": "commercial_next_step"
    },
    {
      "action": "check",
      "status": "check_required",
      "subjects": [
        "requested facilitator availability and format"
      ],
      "topic": "next_step"
    }
  ],
  "audio_projection_items": [
    {
      "authority_class": "current_governed",
      "fingerprint": "56b7098e5b0a9ac30ba8cfde8467b7169972402c237cfbc411622176ff694303",
      "included_in_model_payload": false,
      "prior_turn_status": "unchanged_answer_in_prior_draft",
      "priority": 50,
      "proposition_key": "fact:audio_playback",
      "reason": "unchanged_answer_already_explained",
      "role": "ALREADY_COMMUNICATED",
      "semantic_key": "fact:audio_playback",
      "source_reference": "phase4:technical_audio_playback_supported",
      "topic": "audio_playback",
      "value": {
        "action_required": false,
        "client_fact": {
          "background_music_playback": true
        },
        "fact_state": "known"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "611225d828231fc1d2df193b9e2b6261ba6eff562cf33deb3a4577cc0218ebd0",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 50,
      "proposition_key": "fact:projection_display",
      "reason": "not_needed_in_current_turn",
      "role": "DEFER",
      "semantic_key": "fact:projection_display",
      "source_reference": "phase4:technical_projection_display_confirmation",
      "topic": "projection_display",
      "value": {
        "available_equipment": "WNC projector",
        "capability": "projection display",
        "check_required": [
          "practical projection setup"
        ],
        "status": "conditional"
      }
    }
  ],
  "communicated_editorial_items": [
    {
      "fingerprint": "d48a4e749f26bd87be6140eb859f17d122a1ad07af3a4144f1406fc448f23d20",
      "semantic_key": "commercial.current",
      "source_reference": "governed_case",
      "topic": "commercial"
    }
  ],
  "do_not_repeat_topics": [
    "catering_kitchen",
    "audio_playback"
  ]
}
```

# Full Frozen UAT

```json
{
  "result": "FAIL",
  "assessment_method": "Direct assistant review of all exact final drafts, supported by saved provider-free audits; no external model judge",
  "coverage": "21/21",
  "scenario_count": 13,
  "continuity": "6/7",
  "required_answer_continuity": "7/7",
  "continuity_definition": "The historical headline metric includes repetition defects. Required-answer continuity separately tracks answered requests across turns; UAT-006 has complete answers but repeated report-back prose within turn 2.",
  "continuity_by_scenario": [
    {
      "scenario": "UAT-004",
      "required_answer_continuity": "PASS",
      "editorial_continuity": "PASS"
    },
    {
      "scenario": "UAT-005",
      "required_answer_continuity": "PASS",
      "editorial_continuity": "PASS"
    },
    {
      "scenario": "UAT-006",
      "required_answer_continuity": "PASS",
      "editorial_continuity": "FAIL"
    },
    {
      "scenario": "UAT-009",
      "required_answer_continuity": "PASS",
      "editorial_continuity": "PASS"
    },
    {
      "scenario": "UAT-011",
      "required_answer_continuity": "PASS",
      "editorial_continuity": "PASS"
    },
    {
      "scenario": "UAT-012",
      "required_answer_continuity": "PASS",
      "editorial_continuity": "PASS"
    },
    {
      "scenario": "UAT-013",
      "required_answer_continuity": "PASS",
      "editorial_continuity": "PASS"
    }
  ],
  "grades": {
    "A": 17,
    "B": 4,
    "C": 0,
    "D": 0
  },
  "editorial_defects": {
    "unanswered_request": 0,
    "repetition": 1,
    "unnecessary_information": 0,
    "policy_dump": 0,
    "system_language": 0,
    "unnecessary_year_question": 0,
    "unnecessary_availability": 0,
    "known_audio_answer_omitted": 0,
    "audio_converted_to_pending": 0,
    "cross_clause_realization": 0
  },
  "unanswered_required_semantic_items": 0,
  "safety_failures": 0,
  "wrong_commercial_claims": 0,
  "false_confirmations": 0,
  "known_no_contradictions": 0,
  "confidentiality_failures": 0,
  "stale_current_drafts": 0,
  "em_dashes": 0,
  "corrective_retries": 3,
  "model_candidates": 24,
  "accepted_revision_count": 21,
  "retry_count_by_turn": {
    "UAT-001/1": 0,
    "UAT-002/1": 0,
    "UAT-003/1": 0,
    "UAT-004/1": 0,
    "UAT-004/2": 0,
    "UAT-005/1": 0,
    "UAT-005/2": 1,
    "UAT-006/1": 0,
    "UAT-006/2": 1,
    "UAT-007/1": 0,
    "UAT-008/1": 0,
    "UAT-009/1": 0,
    "UAT-009/2": 0,
    "UAT-010/1": 0,
    "UAT-011/1": 0,
    "UAT-011/2": 0,
    "UAT-012/1": 0,
    "UAT-012/2": 0,
    "UAT-012/3": 0,
    "UAT-013/1": 0,
    "UAT-013/2": 1
  },
  "reviews": {
    "UAT-001/1": {
      "grade": "A",
      "result": "PASS",
      "assessment": "Concise governed EUR 75 excl. VAT and 21% VAT answer, with prospective date/venue availability check. No extra rules or invented facts.",
      "editorial_flags": [],
      "safety_flags": []
    },
    "UAT-002/1": {
      "grade": "A",
      "result": "PASS",
      "assessment": "Asks all four missing client information needs, including day/start/finish without demanding year. Overall price and booking fee are prospective checks. No invented budget.",
      "editorial_flags": [],
      "safety_flags": []
    },
    "UAT-003/1": {
      "grade": "A",
      "result": "PASS",
      "assessment": "States governed whole-venue capacity for 65 guests; availability remains prospective. Concise, without price or unrelated guidance.",
      "editorial_flags": [],
      "safety_flags": []
    },
    "UAT-004/1": {
      "grade": "A",
      "result": "PASS",
      "assessment": "Directly states background playback is possible, separate from practical projection and custom hologram safety checks. No unrelated availability fallback.",
      "editorial_flags": [],
      "safety_flags": []
    },
    "UAT-004/2": {
      "grade": "A",
      "result": "PASS",
      "assessment": "Keeps optional hologram subordinate to ordinary planning, retains practical projection check, and omits previously realized audio.",
      "editorial_flags": [],
      "safety_flags": []
    },
    "UAT-005/1": {
      "grade": "B",
      "result": "PASS",
      "assessment": "Retains kitchen suitability/production limitation and prospective facilitator availability/format. Slightly formal final check wording, with no false confirmation.",
      "editorial_flags": [],
      "safety_flags": []
    },
    "UAT-005/2": {
      "grade": "A",
      "result": "PASS",
      "assessment": "Covers the changed simple buffet, 45-minute setup need and flexible facilitator format. Checks supplier access and facilitator availability without repeating kitchen guidance or promising an access window.",
      "editorial_flags": [],
      "safety_flags": []
    },
    "UAT-006/1": {
      "grade": "A",
      "result": "PASS",
      "assessment": "Concise prospective Studio/date availability check, with no year question or unsupported confirmation.",
      "editorial_flags": [],
      "safety_flags": []
    },
    "UAT-006/2": {
      "grade": "B",
      "result": "FAIL",
      "assessment": "All three requested changes remain prospective and timing is handled without a year question. However, the reply repeats the check-and-report-back promise three times: come back to you, update you on that too, then come back to you once checked. This redundant process wording fails the zero-repetition acceptance gate.",
      "editorial_flags": [
        "repetition"
      ],
      "safety_flags": []
    },
    "UAT-007/1": {
      "grade": "A",
      "result": "PASS",
      "assessment": "Asks only start and finish because day/month are already known. Date check remains prospective, with no year demand or kitchen policy dump.",
      "editorial_flags": [],
      "safety_flags": []
    },
    "UAT-008/1": {
      "grade": "A",
      "result": "PASS",
      "assessment": "States current EUR 75 excl. VAT and 21% VAT, distinguishes overall rental pricing from fee flexibility, and preserves the supplied budget context without confirming a concession.",
      "editorial_flags": [],
      "safety_flags": []
    },
    "UAT-009/1": {
      "grade": "A",
      "result": "PASS",
      "assessment": "Uses current governed EUR 50 fee and 21% VAT, with requested adjustment still pending. Historical fee treatment is not presented as current authority.",
      "editorial_flags": [],
      "safety_flags": []
    },
    "UAT-009/2": {
      "grade": "B",
      "result": "PASS",
      "assessment": "Briefly acknowledges the historical-team clarification, retains the fee-adjustment check and avoids repeating the price or asserting that the previous arrangement applies. Slightly formal acknowledgement.",
      "editorial_flags": [],
      "safety_flags": []
    },
    "UAT-010/1": {
      "grade": "A",
      "result": "PASS",
      "assessment": "Only the requested aerial-rig installation/operation safety check is communicated. No unrelated venue-availability fallback.",
      "editorial_flags": [],
      "safety_flags": []
    },
    "UAT-011/1": {
      "grade": "A",
      "result": "PASS",
      "assessment": "Covers kitchen suitability and its limitation, conditional projector setup, external microphones, and the governed rental-period access restriction. Arrival/setup checks remain prospective; no unrelated capability contradiction.",
      "editorial_flags": [],
      "safety_flags": []
    },
    "UAT-011/2": {
      "grade": "A",
      "result": "PASS",
      "assessment": "Focuses on new handover, arrival timing and loading-route needs. Prior kitchen, microphone and general access guidance are omitted rather than repeated; no concrete access window or completed arrangement is invented.",
      "editorial_flags": [],
      "safety_flags": []
    },
    "UAT-012/1": {
      "grade": "A",
      "result": "PASS",
      "assessment": "Directly states background music playback availability. Practical projection and facilitator checks stay prospective; kitchen guidance and fee/adjustment checks are present. Asks only missing day/start/finish/headcount.",
      "editorial_flags": [],
      "safety_flags": []
    },
    "UAT-012/2": {
      "grade": "A",
      "result": "PASS",
      "assessment": "Omits already answered audio and kitchen guidance. Handles the shorter flexible welcome, facilitator and fee checks; the supplied headcount closes that question while timing questions remain.",
      "editorial_flags": [],
      "safety_flags": []
    },
    "UAT-012/3": {
      "grade": "A",
      "result": "PASS",
      "assessment": "Omits audio again, states EUR 75 excl. VAT and 21% VAT, and keeps adjustment/facilitator checks prospective. Timing questions are closed without demanding year.",
      "editorial_flags": [],
      "safety_flags": []
    },
    "UAT-013/1": {
      "grade": "A",
      "result": "PASS",
      "assessment": "Prospective Studio/date availability check, using normalized February 2027 timing without asking for year.",
      "editorial_flags": [],
      "safety_flags": []
    },
    "UAT-013/2": {
      "grade": "B",
      "result": "PASS",
      "assessment": "Acknowledges only the requested date/time change and keeps the reschedule subject to review. Slightly formal wording, but no false confirmation or year question.",
      "editorial_flags": [],
      "safety_flags": []
    }
  },
  "remaining_issues": [
    "UAT-006/2 repeats the check-and-report-back promise three times. All required meanings and safety checks pass, but the zero-repetition editorial acceptance gate fails. No style repair or further generation cycle was performed."
  ]
}
```

# Exact Final Drafts

## UAT-001/1

DraftRevision 363; exact action/revision/content/context/recipient/approval binding checked provider-free.

Subject:

```text
Studio workshop enquiry
```

Body:

```text
Hi Maya,

The Studio booking fee is EUR 75 excl. VAT, with VAT charged at 21%.

I’ll check availability for your requested date and venue, then come back to you with the next steps.
```

Corrective retries: 0. Required realization: PASS.

## UAT-002/1

DraftRevision 364; exact action/revision/content/context/recipient/approval binding checked provider-free.

Subject:

```text
WNC offsite enquiry
```

Body:

```text
Hi Jon,

It’s lovely to hear WNC was recommended for your team’s offsite. To help me understand what might suit and check the overall rental price, including any booking fee, could you let me know:

• What date, start time and finish time would you like?
• How many guests are expected?
• Which space would you like?
• What type of event are you planning?
```

Corrective retries: 0. Required realization: PASS.

## UAT-003/1

DraftRevision 365; exact action/revision/content/context/recipient/approval binding checked provider-free.

Subject:

```text
Awards evening venue enquiry
```

Body:

```text
Hi Priya,

Your awards evening sounds lovely. A group of 65 is within capacity for exclusive use of the whole venue.

I’ll check the requested date and venue availability and come back to you.
```

Corrective retries: 0. Required realization: PASS.

## UAT-004/1

DraftRevision 366; exact action/revision/content/context/recipient/approval binding checked provider-free.

Subject:

```text
Product launch equipment
```

Body:

```text
Hi Elena,

Your product launch sounds like an exciting event. We have a WNC projector for the slide display, and I’ll check the practical projection setup. Background music playback is possible.

For the small hologram display, I’ll check whether the requested custom equipment can be installed and operated safely, then report back on what is realistic.
```

Corrective retries: 0. Required realization: PASS.

## UAT-004/2

DraftRevision 367; exact action/revision/content/context/recipient/approval binding checked provider-free.

Subject:

```text
Projection setup
```

Body:

```text
Hi Elena,

Understood, we’ll keep the hologram optional and continue planning around the essentials. A WNC projector is available for the display, and I’ll check the practical projection setup for your event.
```

Corrective retries: 0. Required realization: PASS.

## UAT-005/1

DraftRevision 368; exact action/revision/content/context/recipient/approval binding checked provider-free.

Subject:

```text
Studio strategy session
```

Body:

```text
Hi Samira,

An all-day strategy session sounds like a good use of the Studio. I’ll check the requested facilitator’s availability and the proposed format before confirming what is workable.

Your caterer could use the catering kitchen for ready-made food, warming, plating and simple assembly, but it is not suitable for large-scale food production.
```

Corrective retries: 0. Required realization: PASS.

## UAT-005/2

DraftRevision 369; exact action/revision/content/context/recipient/approval binding checked provider-free.

Subject:

```text
Buffet setup and facilitation
```

Body:

```text
Hi Samira,

It’s helpful to know the lunch will be a simple buffet requiring about 45 minutes of setup, and that you have flexibility on the facilitator format. I’ll check whether that supplier setup access can be accommodated. I’ll also check the facilitator’s availability for the requested timing and what format may be possible if the full morning is unavailable.
```

Corrective retries: 1. Required realization: PASS.

## UAT-006/1

DraftRevision 370; exact action/revision/content/context/recipient/approval binding checked provider-free.

Subject:

```text
Studio planning meeting
```

Body:

```text
Hi Theo,

Thanks for sharing the details of your planning meeting. I’ll check the Studio’s availability for your requested date and time and come back to you.
```

Corrective retries: 0. Required realization: PASS.

## UAT-006/2

DraftRevision 371; exact action/revision/content/context/recipient/approval binding checked provider-free.

Subject:

```text
Enquiry update
```

Body:

```text
Hi Theo,

I’ve noted that your group is now 30 and you’re requesting the entire venue. I’ll check the revised guest count and come back to you, and I’ll separately check the full-venue request and update you on that too.

I’ll also review the requested move to 13 November from 15:00 to 20:00 and come back to you once that has been checked.
```

Corrective retries: 1. Required realization: PASS.

## UAT-007/1

DraftRevision 372; exact action/revision/content/context/recipient/approval binding checked provider-free.

Subject:

```text
Supper club enquiry
```

Body:

```text
Hi Lena,

The 26-person supper club sounds lovely. What start time and finish time would you like? Once I have those, I’ll check the date for you.
```

Corrective retries: 0. Required realization: PASS.

## UAT-008/1

DraftRevision 373; exact action/revision/content/context/recipient/approval binding checked provider-free.

Subject:

```text
Studio pricing
```

Body:

```text
Hi Omar,

The Studio sounds like a good setting to explore for your leadership session. The booking fee is EUR 75 excl. VAT, with VAT at 21%.

I’ll check the overall rental pricing for your requested event and options with your budget in mind. I’ll also check what flexibility can be arranged on the booking fee if you confirm quickly.
```

Corrective retries: 0. Required realization: PASS.

## UAT-009/1

DraftRevision 374; exact action/revision/content/context/recipient/approval binding checked provider-free.

Subject:

```text
Studio salon booking fee
```

Body:

```text
Hi Claire,

It would be lovely to welcome you back for another salon. The standard booking fee is EUR 50 excl. VAT, with VAT at 21%.

I’ll check what can be arranged regarding a booking fee adjustment this time.
```

Corrective retries: 0. Required realization: PASS.

## UAT-009/2

DraftRevision 375; exact action/revision/content/context/recipient/approval binding checked provider-free.

Subject:

```text
Next step
```

Body:

```text
Hi Claire,

That context is helpful, and I understand the earlier event was handled by the previous team. I’ll check what can be arranged regarding the booking fee adjustment and come back to you.
```

Corrective retries: 0. Required realization: PASS.

## UAT-010/1

DraftRevision 376; exact action/revision/content/context/recipient/approval binding checked provider-free.

Subject:

```text
Custom aerial rig
```

Body:

```text
Hi David,

The suspended aerial performance sounds like a striking element for the investor dinner. I’ll check whether the custom rig can be installed and operated safely in the venue, then report back.
```

Corrective retries: 0. Required realization: PASS.

## UAT-011/1

DraftRevision 377; exact action/revision/content/context/recipient/approval binding checked provider-free.

Subject:

```text
Panel discussion practical requirements
```

Body:

```text
Hi Nora,

Thanks for outlining the panel discussion and the planned supplier setup. The catering kitchen is suitable for ready-made food, warming, plating and simple assembly, but not for large-scale food production.

For projection, WNC has a projector, and I’ll check the practical setup for your panel. Microphones are not provided, so they would need to come from an external supplier.

Supplier deliveries, unloading and setup need to take place within the confirmed rental period unless agreed otherwise in writing. I’ll check the supplier arrival timing and setup access for you.
```

Corrective retries: 0. Required realization: PASS.

## UAT-011/2

DraftRevision 378; exact action/revision/content/context/recipient/approval binding checked provider-free.

Subject:

```text
Florist and caterer logistics
```

Body:

```text
Hi Nora,

Understood on the florist waiting until the venue handover requirements are clear. I’ll check the handover details, supplier arrival timing and the loading route, then come back to you with the practical arrangements.
```

Corrective retries: 0. Required realization: PASS.

## UAT-012/1

DraftRevision 379; exact action/revision/content/context/recipient/approval binding checked provider-free.

Subject:

```text
January Studio gathering
```

Body:

```text
Hi Ari,

Your January gathering sounds lovely. Light background music playback is available, and the WNC projector can be used for slides. I’ll check the practical projection setup, along with the availability and format of a short facilitator-led opening.

For outside catering, the kitchen is suitable for ready-made food, warming, plating and simple assembly, rather than large-scale food production. I’ll also check the booking fee that would apply and whether any adjustment can be arranged.

What day, start time and finish time would you like? How many guests are expected?
```

Corrective retries: 0. Required realization: PASS.

## UAT-012/2

DraftRevision 380; exact action/revision/content/context/recipient/approval binding checked provider-free.

Subject:

```text
Facilitator timing and booking fee
```

Body:

```text
Hi Ari,

The shorter welcome and flexibility around WNC availability are helpful. I’ll check the requested facilitator’s availability and whether that 20-minute format can be arranged. I’ll also check the booking fee and what may be possible regarding an adjustment.

What day, start time and finish time would you like?
```

Corrective retries: 0. Required realization: PASS.

## UAT-012/3

DraftRevision 381; exact action/revision/content/context/recipient/approval binding checked provider-free.

Subject:

```text
Gathering details
```

Body:

```text
Hi Ari,

I’ve noted the updated date and timing for the gathering. The booking fee is EUR 75 excl. VAT, with VAT at 21%, and I’ll check what can be arranged regarding the requested fee adjustment.

I’ll also check the requested facilitator’s availability and whether the requested format can be arranged.
```

Corrective retries: 0. Required realization: PASS.

## UAT-013/1

DraftRevision 382; exact action/revision/content/context/recipient/approval binding checked provider-free.

Subject:

```text
Studio planning session
```

Body:

```text
Hi Riley,

Thanks for sharing the details of your Studio planning session. I’ll check the requested date and Studio availability and come back to you.
```

Corrective retries: 0. Required realization: PASS.

## UAT-013/2

DraftRevision 383; exact action/revision/content/context/recipient/approval binding checked provider-free.

Subject:

```text
Session reschedule
```

Body:

```text
Hi Riley,

Thanks for clarifying that you’d like to move the session to 8 February from 14:00 to 17:00, with everything else unchanged. The requested reschedule is awaiting review, and I’ll check whether we can make the change and come back to you.
```

Corrective retries: 1. Required realization: PASS.

# Date Inference

Date normalization source, ingestion logic and boundary regressions remain byte-for-byte unchanged from the accepted implementation. The frozen client text and non-timing observations are unchanged. As in the accepted date run, fixture-assigned ISO timing observations are excluded from injection; the application derives timing from the original inbound text and authoritative message timestamp. The `observations` field in result files describes the original frozen fixture, not injected timing values. Runtime provenance is in the captured case snapshots.

```json
{
  "normalization_and_observation_sources_unchanged": "PASS",
  "frozen_prior_evidence_hashes": "PASS",
  "timestamp_provenance_observations_checked": 17,
  "drafts_without_year_question": 24,
  "targeted_January_21": "2027-01-21",
  "targeted_provenance": "system_inferred_next_occurrence"
}
```

# Tests

```json
{
  "focused": 170,
  "focused_subtests": 13,
  "phase8": 534,
  "phase8_subtests": 126,
  "full": 751,
  "full_subtests": 160,
  "failures": 0,
  "skipped": 0,
  "git_diff_check": "PASS"
}
```

# Deployment

```json
{
  "commit": "4b31672ec26ea233208a65d59a365344e94370c9",
  "deploy_id": "dep-db0dg860tbcc73fc117g",
  "status": "live"
}
```

```json
{
  "application": {
    "detail": "WSGI application responded.",
    "metrics": {
      "outlook_human_edit_identity_policy": "trusted_configured_mailbox_and_bound_graph_id; provided_smtp_fields_must_match; absent_identity_fields_allowed"
    },
    "status": "ok"
  },
  "database": {
    "detail": "Bounded database query succeeded.",
    "status": "ok"
  },
  "environment": "staging",
  "phase5": {
    "detail": "Phase 5 current corpus and semantic embedding coverage are bootstrapped.",
    "metrics": {
      "active_model_count": 1,
      "active_model_id": 1,
      "eligible_chunks": 492,
      "embedded_chunks": 492,
      "missing_chunks": 0
    },
    "status": "ok"
  },
  "phase6": {
    "detail": "Phase 6 historical retrieval model and embedding coverage are bootstrapped.",
    "metrics": {
      "active_model_count": 1,
      "active_model_id": 1,
      "eligible_units": 112,
      "embedded_units": 112,
      "missing_units": 0,
      "stale_units": 0
    },
    "status": "ok"
  },
  "providers": {
    "asana": "configured_but_disabled",
    "outlook": "configured_draft_only"
  },
  "status": "ok"
}
```

# Safety

```json
{
  "environment": "staging",
  "health": "ok",
  "outlook": "configured_draft_only",
  "send_gate": "DISABLED",
  "asana": "configured_but_disabled",
  "Graph mutations": 0,
  "Outlook sends": 0,
  "real Asana executions": 0,
  "production activity": 0,
  "actions approved": 0,
  "actions executed": 0,
  "ExecutionAttempts created": 0,
  "generation_operations": 24,
  "model_candidates": 27,
  "corrective_retries": 3,
  "provider": "openai",
  "model": "gpt-5.6-sol"
}
```

All 14 synthetic cases contain exactly the accepted revision IDs captured by the UAT; none of the three initial incomplete candidates became a persisted revision.

Activity zeros are scoped to this task and established from the guarded request logs and synthetic case snapshots. No sending gate, provider/model, production, Entra or Exchange permission settings were changed. Draft approvals were created only for accepted synthetic drafts; none was approved or executed.

# Remaining Findings

- UAT-006/2 repeats the check-and-report-back promise three times. All required meanings and safety checks pass, but the zero-repetition editorial acceptance gate fails. No style repair or further generation cycle was performed.

# Evidence

- [Frozen scenarios, accepted date policy and historical file hashes](frozen_manifest.json)
- [Targeted results and request log](targeted_results.json)
- [Targeted plans, payloads and generation audits](targeted_planner_audit.json)
- [Provider-free binding validation](targeted_captured_contract_validation.json)
- [Final staging snapshots](targeted_final_snapshots.json)
- [Deployment screenshot](staging_deployment.png)
- [Full UAT exact results and guarded request log](full_results.json)
- [Full UAT candidate hashes, unmet IDs and final realization audit](full_generation_audit.json)
- [Full UAT exact binding checks](full_captured_contract_validation.json)
- [Full UAT final state and disabled-send audit](full_integrity_audit.json)
- [Full UAT timestamp provenance](full_date_provenance.json)
- [Accepted-revision cardinality proof](accepted_revision_cardinality.json)

# Final Marker

WNC_REQUIRED_REALIZATION_REVIEW_REQUIRED

Stopped at the authorized acceptance boundary. Sending remains disabled.
