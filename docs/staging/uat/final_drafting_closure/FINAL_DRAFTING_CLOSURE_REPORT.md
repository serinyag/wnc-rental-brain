# Final Two Defects

Targeted changes deployed once. 21/21 drafts persisted; continuity 6/7; 12 A / 9 B / 0 C / 0 D. The single acceptance run demonstrates remaining issues; no further implementation or generation cycle was performed.

## Pending-action detection

Root cause: the venue-availability fallback looked only for status labels, so the concrete aerial-rig action was invisible to it. `is_pending_check_action` recognizes concrete action=check values with subjects/questions as well as the existing conditional/check_required/pending shapes. Both the fallback and client-visible pending-state audit use this helper. A background-music fact does not count as pending. Unrequested availability stays DEFER when the concrete rig check already supplies the next step; an explicit availability question still wins.

## Known audio and item-scoped realization

Root cause: known audio could be merged into a conditional projection check, and the realization witness combined music in one paragraph with possible in a fee sentence. Audio now carries a known client fact and action_required=false; conditional projection retains its practical setup check. One generation rule requires known facts to remain known. Audio realization requires a positive capability predicate in the audio clause and excludes prospective/negative/conditional wording. A previously requested known audio answer without valid realization evidence remains mandatory on follow-up.

Editorial planner v3, current information budgets, topic-safe known-no validation, commercial authority, historical precedence, external-contact semantics and exact DraftRevision approvals remain in place. The context hash includes a normalization revision so old contexts cannot be mistaken for these semantics.

# Date Year Inference

Ordinary day/month expressions are normalized in application code using the authoritative inbound received_at (or occurred_at), in Europe/Amsterdam. A future calendar date uses the current year; an elapsed month/day uses the next valid occurrence. Explicit years are preserved even when past; invalid explicit dates and ambiguous clock times are quarantined rather than repaired by inference. February 29 advances to the next valid leap year when the year was omitted. Same-calendar-day requests remain eligible as today; missing times remain questions.

Raw client text remains unchanged. Source-linked timing observations persist date_provenance, including year_source, explicit_client_year, resolved_year, source_reference, reference_timestamp and timezone. Inferred years are not stored as explicit client year components. Time-only follow-ups preserve the original date provenance. A later explicit correction gets explicit provenance and follows normal intake/reschedule governance; inference does not approve a changed booking.

Only genuinely missing date/time components are asked. Known day/month with unknown timing asks for start and finish; a known month without a day asks for the day. Complete timing is promoted through normal intake and closes the timing question.

```json
{
  "anchor": "Inbound received_at, otherwise occurred_at; never generation wall clock",
  "timezone": "Europe/Amsterdam",
  "same_calendar_day": "eligible as today; missing times remain questions",
  "provenance": "date_provenance.year_source = client_explicit or system_inferred_next_occurrence, persisted on immutable source-linked observations",
  "later_correction": "Newest requested timing carries explicit provenance; current canonical dates change only through existing intake/reschedule governance",
  "invalid_or_ambiguous": "Quarantine calendar/time candidates; do not infer over contradictions or DST ambiguity"
}
```

# Provider-Free Regressions

```json
{
  "concrete_check_without_status": "PASS",
  "legacy_status_check": "PASS",
  "known_audio_not_pending": "PASS",
  "conditional_projection_pending": "PASS",
  "distinct_fact_and_check_payload": "PASS",
  "positive_audio_realization": "PASS",
  "future_check_not_realized": "PASS",
  "cross_clause_realization_rejected": "PASS",
  "rig_no_unrequested_availability": "PASS",
  "compound_audio_and_projection": "PASS",
  "continuity_only_after_valid_realization": "PASS",
  "future_day_month_current_year": "PASS",
  "past_day_month_next_year": "PASS",
  "explicit_year_wins": "PASS",
  "later_explicit_correction_governed_reschedule": "PASS",
  "leap_day_including_century": "PASS",
  "authoritative_timezone_date_boundary": "PASS",
  "DST_ambiguity_no_guessed_schedule": "PASS",
  "raw_inbound_timestamp_provenance": "PASS",
  "partial_date_time_completion": "PASS",
  "only_genuinely_missing_components_asked": "PASS"
}
```

# Tests

```json
{
  "focused": 124,
  "focused_subtests": 0,
  "phase8": 489,
  "phase8_subtests": 126,
  "full": 706,
  "full_subtests": 160,
  "failures": 0,
  "git_diff_check": "PASS"
}
```

Full Phase 8 and full repository suites were run separately. Existing collection warnings concern application classes named Test*. All required provider-free checks passed before any OpenAI UAT call.

# Deployment

```json
{
  "commit": "a7e2978d0f421ea177dde7c6066e5851793dd070",
  "deploy_id": "dep-db0c8enavr4c73f2ba9g",
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

# Final Frozen UAT

```json
{
  "persisted_drafts": 21,
  "attempted_turns": 21,
  "continuity": "6/7",
  "grades": {
    "A": 12,
    "B": 9,
    "C": 0,
    "D": 0
  },
  "editorial_defects": {
    "unnecessary_availability": 0,
    "known_audio_answer_omitted": 3,
    "audio_converted_to_pending": 0,
    "cross_clause_realization": 0,
    "unnecessary_year_question": 0,
    "known_no_false_positive": 0,
    "substring_topic_collision": 0,
    "invented_budget": 0,
    "unnecessary_information": 0,
    "repetition": 2,
    "policy_dump": 0,
    "policy_copy": 0,
    "system_language": 0,
    "unanswered_request": 3,
    "missing_client_question": 0
  },
  "safety_failures": 0,
  "safety_defects": {},
  "em_dashes": 0,
  "rejected_candidates": 0,
  "captured_plans": 21,
  "canonical_binding_checks": 21,
  "current_revision_checks": 13,
  "stale_current_drafts": 0,
  "wrong_commercial_claims": 0,
  "false_confirmations": 0,
  "known_no_contradictions": 0,
  "false_external_contact": 0,
  "confidentiality_failures": 0
}
```

One run of the same 13 scenarios / 21 client turns. Client text and non-timing observations remain frozen. Per the new product decision, fixture-assigned ISO years/UTC windows were not injected: the application derived timing candidates from the original messages and recorded inbound timestamps. This authorized expectation change is recorded in frozen_manifest.json; prior evidence hashes remain unchanged. No accepted or rejected model output was regenerated.

```json
{
  "turn": "UAT-012/3",
  "original_results_file": "acceptance_results_raw.json",
  "raw_sha256": "a10399c2a732ac34cc2629defdf8d354888b7a523bdc122a2c1185dd36482516",
  "failed_stage": "inquiry-waiting transport response",
  "generation_repeated": false,
  "case_or_message_reinjected": false
}
```

## Continuity

```json
[
  {
    "scenario_id": "UAT-004",
    "case_id": 559,
    "turns": 2,
    "result": "PASS",
    "evidence": {
      "UAT-004/1": "States music availability as a known fact, separate from projection and hologram checks. No abstract feasibility label or invented pending audio state.",
      "UAT-004/2": "Acknowledges the optional hologram without dependency language, retains the practical projection check, and omits audio after a valid positive first-turn realization."
    }
  },
  {
    "scenario_id": "UAT-005",
    "case_id": 560,
    "turns": 2,
    "result": "PASS",
    "evidence": {
      "UAT-005/1": "Retains the one material kitchen suitability constraint and facilitator availability/format check. Slightly formal catering paragraph, but no secondary checklist or unsupported confirmation.",
      "UAT-005/2": "Focuses on 45-minute supplier setup and flexible facilitator format. Prior kitchen guidance is omitted using valid first-turn realization evidence."
    }
  },
  {
    "scenario_id": "UAT-006",
    "case_id": 561,
    "turns": 2,
    "result": "PASS",
    "evidence": {
      "UAT-006/1": "Concise acknowledgement and prospective availability check, without a year question or irrelevant facts.",
      "UAT-006/2": "Acknowledges the larger group, entire-venue request and changed timing as requests to check. Date normalization did not bypass reschedule governance or falsely confirm the changes."
    }
  },
  {
    "scenario_id": "UAT-009",
    "case_id": 564,
    "turns": 2,
    "result": "PASS",
    "evidence": {
      "UAT-009/1": "Uses the current governed EUR 50 fee and 21% VAT, while leaving the requested historical fee waiver/adjustment pending. No historical arrangement is treated as current authority.",
      "UAT-009/2": "Briefly acknowledges the client’s request to use present arrangements and retains the fee-adjustment check. No repeated price, internal classification explanation or claim that the old waiver applies."
    }
  },
  {
    "scenario_id": "UAT-011",
    "case_id": 566,
    "turns": 2,
    "result": "PASS",
    "evidence": {
      "UAT-011/1": "Compound requirements are covered with one kitchen constraint, one access constraint, projection check and external microphones. Projector is available does not falsely contradict the microphone restriction. Slightly formal AV wording is not an internal status claim.",
      "UAT-011/2": "Focuses only on handover, arrival timing and loading route. Prior kitchen/access/projection/microphone answers are ALREADY_COMMUNICATED. Confirmed information is a future report-back, not a present authorization or external-contact claim."
    }
  },
  {
    "scenario_id": "UAT-012",
    "case_id": 567,
    "turns": 3,
    "result": "FAIL",
    "evidence": {
      "UAT-012/1": "Typed known audio and conditional projection are distinct in the payload, and the DJ restriction is absent. However, the draft only acknowledges that music was requested; it omits the positive known capability answer. The corrected witness correctly records no audio realization, even though possible appears in the unrelated facilitator-format sentence. Day/start/finish questions correctly omit year.",
      "UAT-012/2": "The planner correctly retains the still-unanswered audio fact rather than falsely suppressing it, but the draft again only notes music as part of the plan. Audio realization remains absent. Headcount, facilitator update, fee checks and genuinely missing timing components are handled correctly. The unchanged music-plan acknowledgement is repeated instead of answering capability.",
      "UAT-012/3": "Provides the newly available EUR 75 fee/VAT and pending adjustment/facilitator checks. Date normalization closes the January timing question without asking for year. However, the reply again acknowledges planned music instead of stating known availability; audio realization correctly remains absent. This repeats the earlier music-plan acknowledgement. Generated once after bounded pre-generation transport recovery."
    }
  },
  {
    "scenario_id": "UAT-013",
    "case_id": 568,
    "turns": 2,
    "result": "PASS",
    "evidence": {
      "UAT-013/1": "Prospective Studio availability check, using the normalized February 2027 date internally and asking no year question.",
      "UAT-013/2": "Acknowledges the requested change and keeps it subject to review. Slightly formal report-back wording, but no present booking/date confirmation or repeated case details."
    }
  }
]
```

## Direct quality review

These are direct assistant assessments, not an external LLM judge or independent human acceptance study. A/B grades are secondary to the hard gates.

| Turn | Grade | Result | Assessment |
|---|---|---|---|
| UAT-001/1 | B | PASS | Correct EUR 75 fee and 21% VAT with a prospective availability check. Opening is direct rather than especially warm, but it answers the inquiry without unrequested detail or a year question. |
| UAT-002/1 | A | PASS | Asks the four required information questions, including date/start/finish without asking for year. Covers overall pricing and fee checks without invented budget context. |
| UAT-003/1 | B | PASS | Correctly answers current governed capacity and keeps availability prospective. The separate report-back closing is mildly wordy, but no extra policy or unsupported fact is introduced. |
| UAT-004/1 | A | PASS | States music availability as a known fact, separate from projection and hologram checks. No abstract feasibility label or invented pending audio state. |
| UAT-004/2 | A | PASS | Acknowledges the optional hologram without dependency language, retains the practical projection check, and omits audio after a valid positive first-turn realization. |
| UAT-005/1 | B | PASS | Retains the one material kitchen suitability constraint and facilitator availability/format check. Slightly formal catering paragraph, but no secondary checklist or unsupported confirmation. |
| UAT-005/2 | A | PASS | Focuses on 45-minute supplier setup and flexible facilitator format. Prior kitchen guidance is omitted using valid first-turn realization evidence. |
| UAT-006/1 | A | PASS | Concise acknowledgement and prospective availability check, without a year question or irrelevant facts. |
| UAT-006/2 | A | PASS | Acknowledges the larger group, entire-venue request and changed timing as requests to check. Date normalization did not bypass reschedule governance or falsely confirm the changes. |
| UAT-007/1 | A | PASS | Keeps the supplied 19 November and asks only start and finish times. No year/date repetition, kitchen paragraph or supplier-policy expansion. |
| UAT-008/1 | A | PASS | Answers fee/VAT, retains the explicitly stated budget constraint, and checks pricing/flexibility without approving an adjustment or misclassifying pricing language as audio. |
| UAT-009/1 | A | PASS | Uses the current governed EUR 50 fee and 21% VAT, while leaving the requested historical fee waiver/adjustment pending. No historical arrangement is treated as current authority. |
| UAT-009/2 | B | PASS | Briefly acknowledges the client’s request to use present arrangements and retains the fee-adjustment check. No repeated price, internal classification explanation or claim that the old waiver applies. |
| UAT-010/1 | A | PASS | Answers only the aerial-rig capability question with concrete installation/operation safety checks and report-back. Unrequested venue availability is DEFER in the plan and absent from the exact draft; no abstract feasibility wording. |
| UAT-011/1 | B | PASS | Compound requirements are covered with one kitchen constraint, one access constraint, projection check and external microphones. Projector is available does not falsely contradict the microphone restriction. Slightly formal AV wording is not an internal status claim. |
| UAT-011/2 | A | PASS | Focuses only on handover, arrival timing and loading route. Prior kitchen/access/projection/microphone answers are ALREADY_COMMUNICATED. Confirmed information is a future report-back, not a present authorization or external-contact claim. |
| UAT-012/1 | B | FAIL | Typed known audio and conditional projection are distinct in the payload, and the DJ restriction is absent. However, the draft only acknowledges that music was requested; it omits the positive known capability answer. The corrected witness correctly records no audio realization, even though possible appears in the unrelated facilitator-format sentence. Day/start/finish questions correctly omit year. |
| UAT-012/2 | B | FAIL | The planner correctly retains the still-unanswered audio fact rather than falsely suppressing it, but the draft again only notes music as part of the plan. Audio realization remains absent. Headcount, facilitator update, fee checks and genuinely missing timing components are handled correctly. The unchanged music-plan acknowledgement is repeated instead of answering capability. |
| UAT-012/3 | B | FAIL | Provides the newly available EUR 75 fee/VAT and pending adjustment/facilitator checks. Date normalization closes the January timing question without asking for year. However, the reply again acknowledges planned music instead of stating known availability; audio realization correctly remains absent. This repeats the earlier music-plan acknowledgement. Generated once after bounded pre-generation transport recovery. |
| UAT-013/1 | A | PASS | Prospective Studio availability check, using the normalized February 2027 date internally and asking no year question. |
| UAT-013/2 | B | PASS | Acknowledges the requested change and keeps it subject to review. Slightly formal report-back wording, but no present booking/date confirmation or repeated case details. |

# Exact 21 Drafts

All subjects and bodies are reproduced verbatim from saved generation evidence. None was approved or sent.

## UAT-001/1

DraftRevision 339. Validator PASS. Exact canonical action/revision/content/context/recipient/approval binding PASS.

**Subject**

```text
Studio workshop enquiry
```

**Body**

```text
Hi Maya,

The Studio booking fee for your product workshop is EUR 75 excl. VAT, with VAT charged at 21%.

I’ll check the requested date and Studio availability, then come back to you with the next steps.
```

## UAT-002/1

DraftRevision 340. Validator PASS. Exact canonical action/revision/content/context/recipient/approval binding PASS.

**Subject**

```text
WNC offsite enquiry
```

**Body**

```text
Hi Jon,

It’s great to hear WNC was recommended for your team’s autumn offsite. To suggest a suitable setup and check the overall rental price and any booking fee, could you let me know:

• What date, start time and finish time would you like?
• How many guests are expected?
• Which space would you like?
• What type of event are you planning?
```

## UAT-003/1

DraftRevision 341. Validator PASS. Exact canonical action/revision/content/context/recipient/approval binding PASS.

**Subject**

```text
Awards evening venue enquiry
```

**Body**

```text
Hi Priya,

Your awards evening sounds like a great occasion. The whole venue can accommodate 65 colleagues, and I’ll check availability for your requested date and event times.

I’ll come back to you once I’ve checked.
```

## UAT-004/1

DraftRevision 342. Validator PASS. Exact canonical action/revision/content/context/recipient/approval binding PASS.

**Subject**

```text
Product launch technical setup
```

**Body**

```text
Hi Elena,

Your product launch sounds exciting. Background music playback is available. We have a WNC projector for the slides, and I’ll check the practical projection setup.

I’ll also check whether a small hologram display can be installed and operated safely, then report back on what is realistic.
```

## UAT-004/2

DraftRevision 343. Validator PASS. Exact canonical action/revision/content/context/recipient/approval binding PASS.

**Subject**

```text
Projection planning
```

**Body**

```text
Hi Elena,

Understood, we’ll keep the hologram optional so it does not delay the wider event planning. A WNC projector is available for the display, and I’ll check the practical projection setup needed for your plans.
```

## UAT-005/1

DraftRevision 344. Validator PASS. Exact canonical action/revision/content/context/recipient/approval binding PASS.

**Subject**

```text
Studio strategy session
```

**Body**

```text
Hi Samira,

An all-day strategy session in the Studio sounds worth exploring. The catering kitchen is suitable for ready-made food, warming, plating and simple assembly, rather than large-scale food production, so your caterer would need to plan lunch accordingly.

I’ll check the requested facilitator’s availability and the proposed morning format.
```

## UAT-005/2

DraftRevision 345. Validator PASS. Exact canonical action/revision/content/context/recipient/approval binding PASS.

**Subject**

```text
Buffet setup and facilitator
```

**Body**

```text
Hi Samira,

A simple buffet with about 45 minutes of setup is helpful to know, and the flexibility on the facilitator format gives us useful options. I’ll check supplier setup access and the facilitator’s availability, including whether an alternative format would work if the full morning is unavailable.
```

## UAT-006/1

DraftRevision 346. Validator PASS. Exact canonical action/revision/content/context/recipient/approval binding PASS.

**Subject**

```text
Studio planning meeting
```

**Body**

```text
Hi Theo,

Thanks for sharing the details of your planning meeting. I’ll check the Studio’s availability for your requested date and time and come back to you.
```

## UAT-006/2

DraftRevision 347. Validator PASS. Exact canonical action/revision/content/context/recipient/approval binding PASS.

**Subject**

```text
Updated venue enquiry
```

**Body**

```text
Hi Theo,

Thanks for the update about the larger group and revised venue request. I’ll check the change to 30 guests, the request for the entire venue, and the new date and time, then come back to you.
```

## UAT-007/1

DraftRevision 348. Validator PASS. Exact canonical action/revision/content/context/recipient/approval binding PASS.

**Subject**

```text
Supper club enquiry
```

**Body**

```text
Hi Lena,

A 26-person supper club sounds lovely. To check 19 November for you, what start time and finish time would you like?
```

## UAT-008/1

DraftRevision 349. Validator PASS. Exact canonical action/revision/content/context/recipient/approval binding PASS.

**Subject**

```text
Studio pricing
```

**Body**

```text
Hi Omar,

The Studio sounds like a good setting to explore for your leadership session. The booking fee is EUR 75 excl. VAT, with VAT at 21%.

I’ll check the overall rental pricing for your requested event and options with your budget in mind. I’ll also check what flexibility can be arranged on the booking fee if you confirm quickly.
```

## UAT-009/1

DraftRevision 350. Validator PASS. Exact canonical action/revision/content/context/recipient/approval binding PASS.

**Subject**

```text
Studio salon booking fee
```

**Body**

```text
Hi Claire,

It would be lovely to welcome you back for another salon. The standard booking fee is EUR 50 excl. VAT, with VAT at 21%.

I’ll check what can be arranged regarding the booking fee adjustment and come back to you.
```

## UAT-009/2

DraftRevision 351. Validator PASS. Exact canonical action/revision/content/context/recipient/approval binding PASS.

**Subject**

```text
Next steps
```

**Body**

```text
Hi Claire,

That context is helpful. I’ll work from the arrangements in place now and check what can be arranged regarding the booking fee adjustment.
```

## UAT-010/1

DraftRevision 352. Validator PASS. Exact canonical action/revision/content/context/recipient/approval binding PASS.

**Subject**

```text
Custom aerial rig
```

**Body**

```text
Hi David,

The suspended aerial performance sounds like a striking element for the investor dinner. I’ll check whether the custom rig can be installed and operated safely in the venue, then report back on whether it can be included.
```

## UAT-011/1

DraftRevision 353. Validator PASS. Exact canonical action/revision/content/context/recipient/approval binding PASS.

**Subject**

```text
Panel discussion requirements
```

**Body**

```text
Hi Nora,

It’s helpful to know you’re planning a panel discussion with both florist and caterer setup. The catering kitchen is suitable for ready-made food, warming, plating and simple assembly, but not for large-scale food production.

Deliveries, unloading and setup must take place within the confirmed rental period unless agreed in writing in advance. I’ll check the supplier arrival timing and setup access.

The WNC projector is available for projection display, and I’ll check the practical projection setup for the panel. Microphones are not provided, so these would need to come from an external supplier.
```

## UAT-011/2

DraftRevision 354. Validator PASS. Exact canonical action/revision/content/context/recipient/approval binding PASS.

**Subject**

```text
Supplier arrival details
```

**Body**

```text
Hi Nora,

Understood that the florist will wait until the venue handover requirements are clear, and that the caterer needs practical arrival details. I’ll check the handover requirements, supplier arrival timing and loading route, then come back to you with the confirmed information.
```

## UAT-012/1

DraftRevision 355. Validator PASS. Exact canonical action/revision/content/context/recipient/approval binding PASS.

**Subject**

```text
January Studio gathering
```

**Body**

```text
Hi Ari,

Your January gathering in the Studio sounds lovely. I’ve noted the slides and light background music. I’ll check the practical setup for using WNC’s projector, along with the requested facilitator’s availability and possible format.

For the outside caterer, the kitchen is suitable for ready-made food, warming, plating and simple assembly, rather than large-scale food production. I’ll also check the booking fee for your request and whether any adjustment can be arranged.

What day, start time and finish time would you like? How many guests are expected?
```

## UAT-012/2

DraftRevision 356. Validator PASS. Exact canonical action/revision/content/context/recipient/approval binding PASS.

**Subject**

```text
Updated event details
```

**Body**

```text
Hi Ari,

Thanks for clarifying that the group is now 24 and that the facilitator would only be needed for a 20-minute welcome, with flexibility around WNC availability. I’ve also noted that background music playback is part of the plan.

I’ll check the requested facilitator availability and format, along with the booking fee and pricing, including what can be arranged regarding your requested fee adjustment. What day, start time and finish time would you like?
```

## UAT-012/3

DraftRevision 359. Validator PASS. Exact canonical action/revision/content/context/recipient/approval binding PASS.

**Subject**

```text
Gathering details
```

**Body**

```text
Hi Ari,

Thanks for confirming the date and time for the gathering.

The booking fee is EUR 75 excl. VAT, with VAT at 21%. I’ll check what can be arranged regarding an adjustment to that fee.

I’ve noted that you’ll be playing background music. I’ll also check the requested facilitator’s availability and the proposed format and come back to you.
```

## UAT-013/1

DraftRevision 357. Validator PASS. Exact canonical action/revision/content/context/recipient/approval binding PASS.

**Subject**

```text
Studio planning session
```

**Body**

```text
Hi Riley,

Your Studio planning session sounds like a great use of the space. I’ll check the requested date and Studio availability and come back to you.
```

## UAT-013/2

DraftRevision 358. Validator PASS. Exact canonical action/revision/content/context/recipient/approval binding PASS.

**Subject**

```text
Requested session change
```

**Body**

```text
Hi Riley,

I’ve noted the new requested time. I’ll check the change and come back to you once it has been reviewed.
```

# UAT-010

## Final plan

```json
{
  "acknowledge": [
    {
      "authority_class": "client_request",
      "fingerprint": "d44552ae4b558b8f640e7b870d05c92914f9f1c251a01ee8876945970b7e5bbe",
      "included_in_model_payload": true,
      "prior_turn_status": "not_previously_communicated",
      "priority": 3,
      "proposition_key": "latest_client_detail",
      "reason": "current_turn_delta",
      "role": "ACKNOWLEDGE",
      "semantic_key": "latest_client_detail",
      "source_reference": "current_client_message",
      "topic": "latest_client_detail",
      "value": {
        "about": "investor dinner",
        "kind": "new_enquiry"
      }
    }
  ],
  "already_communicated": [],
  "client_visible_pending_state": [
    {
      "action": "check",
      "questions": [
        "can it be installed safely",
        "can it be operated safely"
      ],
      "report_back": true,
      "subject": "custom aerial rig",
      "topic": "other_technical"
    }
  ],
  "defer": [
    {
      "authority_class": "current_governed",
      "fingerprint": "24727a7a2ecf805c2767687ac37de1f6072034f1bf7a4d1c7be070e3f621b755",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 1,
      "proposition_key": "commercial.current",
      "reason": "not_needed_for_current_question",
      "role": "DEFER",
      "semantic_key": "commercial.current",
      "source_reference": "governed_case",
      "topic": "commercial",
      "value": {
        "booking_fee": "EUR 250 excl. VAT",
        "vat": "21%"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "c44c4347be161b1f3a56fc6ea168b9b0dfb1dffe8f1dd36b6dcf4af26ca0f9c8",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 50,
      "proposition_key": "fact:supplier_access",
      "reason": "not_needed_in_current_turn",
      "role": "DEFER",
      "semantic_key": "fact:supplier_access",
      "source_reference": "CF-005",
      "topic": "supplier_access",
      "value": {
        "activities": [
          "deliveries",
          "unloading",
          "setup"
        ],
        "exception": "prior written agreement",
        "within": "confirmed rental period"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "80b3f63de7932486a0adc203d3da5afb0d0af7abfced21fbddac1dd37440ccee",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 50,
      "proposition_key": "guidance:0385ebf31967963a",
      "reason": "secondary_or_unstructured_guidance_not_needed_now",
      "role": "DEFER",
      "semantic_key": "guidance:0385ebf31967963a",
      "source_reference": "CF-005",
      "topic": "capacity",
      "value": {
        "source_text": "To ensure smooth operations and respect ongoing bookings, drop-ins to the venue are strictly by confirmed appointment only.\nBecause the space may be rented for private events, used for wellness classes, or our team may not have capacity to receive visitors, the Client and all associated vendors must communicate with their designated point of contact before coming into the space.\nUnannounced visits may not be accommodated, and access is not guaranteed without prior confirmation."
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "94e9ac5a771942b591aeeb1c9c88f098cd2f75c6a8ad184878524ad0ef412a22",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 50,
      "proposition_key": "fact:capacity",
      "reason": "not_needed_in_current_turn",
      "role": "DEFER",
      "semantic_key": "fact:capacity",
      "source_reference": "phase4:capacity_entire_venue_within_capacity",
      "topic": "capacity",
      "value": {
        "near_limit": false,
        "requested_guests": 28,
        "scope": "entire venue",
        "status": "within_limits"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "82709a2186378773f7372c2d40ba2c8f65c9ecf94a7ee67944be879cf803de3f",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 50,
      "proposition_key": "case_fact:guest_count",
      "reason": "case_summary_not_needed_for_this_reply",
      "role": "DEFER",
      "semantic_key": "case_fact:guest_count",
      "source_reference": "governed_case",
      "topic": "guest_count",
      "value": {
        "fact": "guest_count: 28"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "23a1e535d6b58f99be59c7aebab06bdd3188100fadb072a554b0db3fa5205204",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 50,
      "proposition_key": "case_fact:event_type",
      "reason": "case_summary_not_needed_for_this_reply",
      "role": "DEFER",
      "semantic_key": "case_fact:event_type",
      "source_reference": "governed_case",
      "topic": "event_type",
      "value": {
        "fact": "event_type: investor dinner"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "d370e3ce4887100fe10395e7cd3ddb34f6987ace8bd19a9c5e72161845a1b0fb",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 50,
      "proposition_key": "case_fact:Requested rental type code",
      "reason": "case_summary_not_needed_for_this_reply",
      "role": "DEFER",
      "semantic_key": "case_fact:Requested rental type code",
      "source_reference": "governed_case",
      "topic": "Requested rental type code",
      "value": {
        "fact": "Requested rental type code: entire_venue"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "81a3f3fcf2d57fddf29451903f3e0d1efd9068dc10fa6402701adb2b6b88f8f2",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 50,
      "proposition_key": "case_fact:Requested active event start",
      "reason": "case_summary_not_needed_for_this_reply",
      "role": "DEFER",
      "semantic_key": "case_fact:Requested active event start",
      "source_reference": "governed_case",
      "topic": "Requested active event start",
      "value": {
        "fact": "Requested active event start: 2026-12-10 16:30:00+00"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "cda413fe1fc53183565945f7cb9e2cd3194d0ba007326fb89be4649b2846c62c",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 50,
      "proposition_key": "case_fact:Requested active event end",
      "reason": "case_summary_not_needed_for_this_reply",
      "role": "DEFER",
      "semantic_key": "case_fact:Requested active event end",
      "source_reference": "governed_case",
      "topic": "Requested active event end",
      "value": {
        "fact": "Requested active event end: 2026-12-10 22:00:00+00"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "1391a35bfba161659451c77a2e493c1ed818432be34c2ed79eebd887a4a96057",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 50,
      "proposition_key": "next_step.availability",
      "reason": "concrete_requested_check_already_supplies_next_step",
      "role": "DEFER",
      "semantic_key": "next_step.availability",
      "source_reference": "governed_case",
      "topic": "next_step",
      "value": {
        "action": "check",
        "subjects": [
          "requested date and venue availability"
        ]
      }
    }
  ],
  "do_not_repeat": [],
  "editorial_rationale": "minimal_substantive_items_optional_guidance_ranked_last",
  "helpful_now": [],
  "internal_only": [
    {
      "authority_class": "current_governed",
      "fingerprint": "e58cd246d69f9a9a9241d352320ae18d8796238ebca0e9217e78e5f7278f2c20",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 0,
      "proposition_key": "restriction:Feasibility as requested",
      "reason": "internal_feasibility_summary",
      "role": "INTERNAL_ONLY",
      "semantic_key": "restriction:Feasibility as requested",
      "source_reference": "governed_case",
      "topic": "restriction",
      "value": {
        "text": "Feasibility as requested: Requires confirmation"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "e084eb1ddf7869d97ab6fe0e778af8f41984f4d766b8f01801864ed1864b18b6",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 0,
      "proposition_key": "restriction:Confirmation still required",
      "reason": "internal_feasibility_summary",
      "role": "INTERNAL_ONLY",
      "semantic_key": "restriction:Confirmation still required",
      "source_reference": "governed_case",
      "topic": "restriction",
      "value": {
        "text": "Confirmation still required: Yes"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "4a2e9adbd90b5520b4344ba06a5adf2921a9809c9a796664d1e27625e4bf821c",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 0,
      "proposition_key": "restriction:Hard constraint",
      "reason": "internal_feasibility_summary",
      "role": "INTERNAL_ONLY",
      "semantic_key": "restriction:Hard constraint",
      "source_reference": "governed_case",
      "topic": "restriction",
      "value": {
        "text": "Hard constraint: Structured confirmation or review must be completed before commitment."
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "9b6d9ce7c6d58f7fa1782e1b3eeed271e73313d25ab70c3e7c5ce99d7b9d3ef8",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 50,
      "proposition_key": "internal:blocker:2279",
      "reason": "ownership_and_workflow_mechanics_stay_local",
      "role": "INTERNAL_ONLY",
      "semantic_key": "internal:blocker:2279",
      "source_reference": "blocker:2279",
      "topic": "resolution",
      "value": {
        "message": "Confirm event-specific technical setup",
        "owner": "WNC_INTERNAL",
        "status": "ACTION_CREATED"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "56867f51b3ef2ae8428d098b52497af509c4c8ae6d535f0a230ffd21c23468a5",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 50,
      "proposition_key": "internal:availability:2026-12-10 16:30:00+00:2026-12-10 22:00:00+00",
      "reason": "ownership_and_workflow_mechanics_stay_local",
      "role": "INTERNAL_ONLY",
      "semantic_key": "internal:availability:2026-12-10 16:30:00+00:2026-12-10 22:00:00+00",
      "source_reference": "availability:2026-12-10 16:30:00+00:2026-12-10 22:00:00+00",
      "topic": "resolution",
      "value": {
        "message": "Confirm entire venue availability for 2026-12-10 16:30:00+00 to 2026-12-10 22:00:00+00",
        "owner": "WNC_INTERNAL",
        "status": "ACTION_CREATED"
      }
    }
  ],
  "must_ask": [],
  "must_communicate": [
    {
      "authority_class": "current_governed",
      "fingerprint": "17c6b1201c328b878f3a7333a74be03fa7730aea9fee0a43d374982b546203e1",
      "included_in_model_payload": true,
      "prior_turn_status": "not_previously_communicated",
      "priority": 1,
      "proposition_key": "fact:other_technical",
      "reason": "requested_technical_capability",
      "role": "MUST_COMMUNICATE",
      "semantic_key": "fact:other_technical",
      "source_reference": "phase4:technical_other_technical_confirmation",
      "topic": "other_technical",
      "value": {
        "action": "check",
        "questions": [
          "can it be installed safely",
          "can it be operated safely"
        ],
        "report_back": true,
        "subject": "custom aerial rig"
      }
    }
  ],
  "primary_client_need": [
    "other_technical"
  ],
  "response_intent": "PENDING_INTERNAL_CONFIRMATION",
  "source_bindings": [
    {
      "fingerprint": "d44552ae4b558b8f640e7b870d05c92914f9f1c251a01ee8876945970b7e5bbe",
      "semantic_key": "latest_client_detail",
      "source_reference": "current_client_message"
    },
    {
      "fingerprint": "24727a7a2ecf805c2767687ac37de1f6072034f1bf7a4d1c7be070e3f621b755",
      "semantic_key": "commercial.current",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "c44c4347be161b1f3a56fc6ea168b9b0dfb1dffe8f1dd36b6dcf4af26ca0f9c8",
      "semantic_key": "fact:supplier_access",
      "source_reference": "CF-005"
    },
    {
      "fingerprint": "80b3f63de7932486a0adc203d3da5afb0d0af7abfced21fbddac1dd37440ccee",
      "semantic_key": "guidance:0385ebf31967963a",
      "source_reference": "CF-005"
    },
    {
      "fingerprint": "94e9ac5a771942b591aeeb1c9c88f098cd2f75c6a8ad184878524ad0ef412a22",
      "semantic_key": "fact:capacity",
      "source_reference": "phase4:capacity_entire_venue_within_capacity"
    },
    {
      "fingerprint": "17c6b1201c328b878f3a7333a74be03fa7730aea9fee0a43d374982b546203e1",
      "semantic_key": "fact:other_technical",
      "source_reference": "phase4:technical_other_technical_confirmation"
    },
    {
      "fingerprint": "e58cd246d69f9a9a9241d352320ae18d8796238ebca0e9217e78e5f7278f2c20",
      "semantic_key": "restriction:Feasibility as requested",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "e084eb1ddf7869d97ab6fe0e778af8f41984f4d766b8f01801864ed1864b18b6",
      "semantic_key": "restriction:Confirmation still required",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "4a2e9adbd90b5520b4344ba06a5adf2921a9809c9a796664d1e27625e4bf821c",
      "semantic_key": "restriction:Hard constraint",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "82709a2186378773f7372c2d40ba2c8f65c9ecf94a7ee67944be879cf803de3f",
      "semantic_key": "case_fact:guest_count",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "23a1e535d6b58f99be59c7aebab06bdd3188100fadb072a554b0db3fa5205204",
      "semantic_key": "case_fact:event_type",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "d370e3ce4887100fe10395e7cd3ddb34f6987ace8bd19a9c5e72161845a1b0fb",
      "semantic_key": "case_fact:Requested rental type code",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "81a3f3fcf2d57fddf29451903f3e0d1efd9068dc10fa6402701adb2b6b88f8f2",
      "semantic_key": "case_fact:Requested active event start",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "cda413fe1fc53183565945f7cb9e2cd3194d0ba007326fb89be4649b2846c62c",
      "semantic_key": "case_fact:Requested active event end",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "9b6d9ce7c6d58f7fa1782e1b3eeed271e73313d25ab70c3e7c5ce99d7b9d3ef8",
      "semantic_key": "internal:blocker:2279",
      "source_reference": "blocker:2279"
    },
    {
      "fingerprint": "56867f51b3ef2ae8428d098b52497af509c4c8ae6d535f0a230ffd21c23468a5",
      "semantic_key": "internal:availability:2026-12-10 16:30:00+00:2026-12-10 22:00:00+00",
      "source_reference": "availability:2026-12-10 16:30:00+00:2026-12-10 22:00:00+00"
    },
    {
      "fingerprint": "1391a35bfba161659451c77a2e493c1ed818432be34c2ed79eebd887a4a96057",
      "semantic_key": "next_step.availability",
      "source_reference": "governed_case"
    }
  ],
  "substantive_budget": 3,
  "version": "editorial_content_plan_v3"
}
```

## Availability fallback evidence

```json
{
  "selected_values": [
    {
      "action": "check",
      "questions": [
        "can it be installed safely",
        "can it be operated safely"
      ],
      "report_back": true,
      "subject": "custom aerial rig",
      "topic": "other_technical"
    }
  ],
  "deferred_availability": [
    {
      "authority_class": "current_governed",
      "fingerprint": "1391a35bfba161659451c77a2e493c1ed818432be34c2ed79eebd887a4a96057",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 50,
      "proposition_key": "next_step.availability",
      "reason": "concrete_requested_check_already_supplies_next_step",
      "role": "DEFER",
      "semantic_key": "next_step.availability",
      "source_reference": "governed_case",
      "topic": "next_step",
      "value": {
        "action": "check",
        "subjects": [
          "requested date and venue availability"
        ]
      }
    }
  ]
}
```

## Exact draft

DraftRevision 352. Validator PASS. Exact canonical action/revision/content/context/recipient/approval binding PASS.

**Subject**

```text
Custom aerial rig
```

**Body**

```text
Hi David,

The suspended aerial performance sounds like a striking element for the investor dinner. I’ll check whether the custom rig can be installed and operated safely in the venue, then report back on whether it can be included.
```

# UAT-012

## UAT-012/1

### Audio/projection state and realized evidence

```json
{
  "selected_values": [
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
    }
  ],
  "do_not_repeat_topics": []
}
```

### Exact draft

DraftRevision 355. Validator PASS. Exact canonical action/revision/content/context/recipient/approval binding PASS.

**Subject**

```text
January Studio gathering
```

**Body**

```text
Hi Ari,

Your January gathering in the Studio sounds lovely. I’ve noted the slides and light background music. I’ll check the practical setup for using WNC’s projector, along with the requested facilitator’s availability and possible format.

For the outside caterer, the kitchen is suitable for ready-made food, warming, plating and simple assembly, rather than large-scale food production. I’ll also check the booking fee for your request and whether any adjustment can be arranged.

What day, start time and finish time would you like? How many guests are expected?
```

## UAT-012/2

### Audio/projection state and realized evidence

```json
{
  "selected_values": [
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
    "catering_kitchen"
  ]
}
```

### Exact draft

DraftRevision 356. Validator PASS. Exact canonical action/revision/content/context/recipient/approval binding PASS.

**Subject**

```text
Updated event details
```

**Body**

```text
Hi Ari,

Thanks for clarifying that the group is now 24 and that the facilitator would only be needed for a 20-minute welcome, with flexibility around WNC availability. I’ve also noted that background music playback is part of the plan.

I’ll check the requested facilitator availability and format, along with the booking fee and pricing, including what can be arranged regarding your requested fee adjustment. What day, start time and finish time would you like?
```

## UAT-012/3

### Audio/projection state and realized evidence

```json
{
  "selected_values": [
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
    "catering_kitchen"
  ]
}
```

### Exact draft

DraftRevision 359. Validator PASS. Exact canonical action/revision/content/context/recipient/approval binding PASS.

**Subject**

```text
Gathering details
```

**Body**

```text
Hi Ari,

Thanks for confirming the date and time for the gathering.

The booking fee is EUR 75 excl. VAT, with VAT at 21%. I’ll check what can be arranged regarding an adjustment to that fee.

I’ve noted that you’ll be playing background music. I’ll also check the requested facilitator’s availability and the proposed format and come back to you.
```

# Timestamp and Year Provenance Evidence

```json
{
  "provider_calls": 0,
  "observations": [
    {
      "scenario_id": "UAT-001",
      "observation_id": 2562,
      "status": "validated",
      "value": {
        "active_event_end": "2026-10-14T12:00:00+00:00",
        "active_event_start": "2026-10-14T08:00:00+00:00",
        "date_provenance": {
          "client_components": {
            "day": 14,
            "finish_time": "14:00",
            "month": 10,
            "start_time": "10:00"
          },
          "explicit_client_year": null,
          "reference_timestamp": "2026-10-03 09:04:15.013092+00",
          "resolved_year": 2026,
          "rule": "next_calendar_occurrence_v1",
          "source_reference": "inbound_source_record:2932",
          "timezone": "Europe/Amsterdam",
          "year_source": "system_inferred_next_occurrence"
        },
        "day": 14,
        "finish_time": "14:00",
        "month": 10,
        "resolved_date": "2026-10-14",
        "start_time": "10:00"
      },
      "source_received_at": "2026-10-03 09:04:15.013092+00",
      "provenance_validation": "PASS"
    },
    {
      "scenario_id": "UAT-003",
      "observation_id": 2566,
      "status": "validated",
      "value": {
        "active_event_end": "2026-10-22T21:00:00+00:00",
        "active_event_start": "2026-10-22T16:00:00+00:00",
        "date_provenance": {
          "client_components": {
            "day": 22,
            "finish_time": "23:00",
            "month": 10,
            "start_time": "18:00"
          },
          "explicit_client_year": null,
          "reference_timestamp": "2026-10-03 09:06:42.720005+00",
          "resolved_year": 2026,
          "rule": "next_calendar_occurrence_v1",
          "source_reference": "inbound_source_record:2937",
          "timezone": "Europe/Amsterdam",
          "year_source": "system_inferred_next_occurrence"
        },
        "day": 22,
        "finish_time": "23:00",
        "month": 10,
        "resolved_date": "2026-10-22",
        "start_time": "18:00"
      },
      "source_received_at": "2026-10-03 09:06:42.720005+00",
      "provenance_validation": "PASS"
    },
    {
      "scenario_id": "UAT-004",
      "observation_id": 2570,
      "status": "validated",
      "value": {
        "active_event_end": "2026-10-29T19:00:00+00:00",
        "active_event_start": "2026-10-29T15:00:00+00:00",
        "date_provenance": {
          "client_components": {
            "day": 29,
            "finish_time": "20:00",
            "month": 10,
            "start_time": "16:00"
          },
          "explicit_client_year": null,
          "reference_timestamp": "2026-10-03 09:08:00.262424+00",
          "resolved_year": 2026,
          "rule": "next_calendar_occurrence_v1",
          "source_reference": "inbound_source_record:2941",
          "timezone": "Europe/Amsterdam",
          "year_source": "system_inferred_next_occurrence"
        },
        "day": 29,
        "finish_time": "20:00",
        "month": 10,
        "resolved_date": "2026-10-29",
        "start_time": "16:00"
      },
      "source_received_at": "2026-10-03 09:08:00.262424+00",
      "provenance_validation": "PASS"
    },
    {
      "scenario_id": "UAT-005",
      "observation_id": 2576,
      "status": "validated",
      "value": {
        "active_event_end": "2026-11-05T16:00:00+00:00",
        "active_event_start": "2026-11-05T08:30:00+00:00",
        "date_provenance": {
          "client_components": {
            "day": 5,
            "finish_time": "17:00",
            "month": 11,
            "start_time": "09:30"
          },
          "explicit_client_year": null,
          "reference_timestamp": "2026-10-03 09:09:45.428408+00",
          "resolved_year": 2026,
          "rule": "next_calendar_occurrence_v1",
          "source_reference": "inbound_source_record:2948",
          "timezone": "Europe/Amsterdam",
          "year_source": "system_inferred_next_occurrence"
        },
        "day": 5,
        "finish_time": "17:00",
        "month": 11,
        "resolved_date": "2026-11-05",
        "start_time": "09:30"
      },
      "source_received_at": "2026-10-03 09:09:45.428408+00",
      "provenance_validation": "PASS"
    },
    {
      "scenario_id": "UAT-006",
      "observation_id": 2587,
      "status": "validated",
      "value": {
        "active_event_end": "2026-11-13T19:00:00+00:00",
        "active_event_start": "2026-11-13T14:00:00+00:00",
        "date_provenance": {
          "client_components": {
            "day": 13,
            "finish_time": "20:00",
            "month": 11,
            "start_time": "15:00"
          },
          "explicit_client_year": null,
          "reference_timestamp": "2026-10-03 09:11:48.716848+00",
          "resolved_year": 2026,
          "rule": "next_calendar_occurrence_v1",
          "source_reference": "inbound_source_record:2960",
          "timezone": "Europe/Amsterdam",
          "year_source": "system_inferred_next_occurrence"
        },
        "day": 13,
        "finish_time": "20:00",
        "month": 11,
        "resolved_date": "2026-11-13",
        "start_time": "15:00"
      },
      "source_received_at": "2026-10-03 09:11:48.716848+00",
      "provenance_validation": "PASS"
    },
    {
      "scenario_id": "UAT-006",
      "observation_id": 2583,
      "status": "validated",
      "value": {
        "active_event_end": "2026-11-12T15:00:00+00:00",
        "active_event_start": "2026-11-12T12:00:00+00:00",
        "date_provenance": {
          "client_components": {
            "day": 12,
            "finish_time": "16:00",
            "month": 11,
            "start_time": "13:00"
          },
          "explicit_client_year": null,
          "reference_timestamp": "2026-10-03 09:11:33.486456+00",
          "resolved_year": 2026,
          "rule": "next_calendar_occurrence_v1",
          "source_reference": "inbound_source_record:2956",
          "timezone": "Europe/Amsterdam",
          "year_source": "system_inferred_next_occurrence"
        },
        "day": 12,
        "finish_time": "16:00",
        "month": 11,
        "resolved_date": "2026-11-12",
        "start_time": "13:00"
      },
      "source_received_at": "2026-10-03 09:11:33.486456+00",
      "provenance_validation": "PASS"
    },
    {
      "scenario_id": "UAT-007",
      "observation_id": 2590,
      "status": "validated",
      "value": {
        "date_provenance": {
          "client_components": {
            "day": 19,
            "month": 11
          },
          "explicit_client_year": null,
          "reference_timestamp": "2026-10-03 09:13:16.068199+00",
          "resolved_year": 2026,
          "rule": "next_calendar_occurrence_v1",
          "source_reference": "inbound_source_record:2963",
          "timezone": "Europe/Amsterdam",
          "year_source": "system_inferred_next_occurrence"
        },
        "day": 19,
        "month": 11,
        "resolved_date": "2026-11-19"
      },
      "source_received_at": "2026-10-03 09:13:16.068199+00",
      "provenance_validation": "PASS"
    },
    {
      "scenario_id": "UAT-008",
      "observation_id": 2595,
      "status": "validated",
      "value": {
        "active_event_end": "2026-11-26T14:00:00+00:00",
        "active_event_start": "2026-11-26T09:00:00+00:00",
        "date_provenance": {
          "client_components": {
            "day": 26,
            "finish_time": "15:00",
            "month": 11,
            "start_time": "10:00"
          },
          "explicit_client_year": null,
          "reference_timestamp": "2026-10-03 09:14:39.015647+00",
          "resolved_year": 2026,
          "rule": "next_calendar_occurrence_v1",
          "source_reference": "inbound_source_record:2968",
          "timezone": "Europe/Amsterdam",
          "year_source": "system_inferred_next_occurrence"
        },
        "day": 26,
        "finish_time": "15:00",
        "month": 11,
        "resolved_date": "2026-11-26",
        "start_time": "10:00"
      },
      "source_received_at": "2026-10-03 09:14:39.015647+00",
      "provenance_validation": "PASS"
    },
    {
      "scenario_id": "UAT-009",
      "observation_id": 2600,
      "status": "validated",
      "value": {
        "active_event_end": "2026-12-03T20:00:00+00:00",
        "active_event_start": "2026-12-03T17:00:00+00:00",
        "date_provenance": {
          "client_components": {
            "day": 3,
            "finish_time": "21:00",
            "month": 12,
            "start_time": "18:00"
          },
          "explicit_client_year": null,
          "reference_timestamp": "2026-10-03 09:16:02.338437+00",
          "resolved_year": 2026,
          "rule": "next_calendar_occurrence_v1",
          "source_reference": "inbound_source_record:2973",
          "timezone": "Europe/Amsterdam",
          "year_source": "system_inferred_next_occurrence"
        },
        "day": 3,
        "finish_time": "21:00",
        "month": 12,
        "resolved_date": "2026-12-03",
        "start_time": "18:00"
      },
      "source_received_at": "2026-10-03 09:16:02.338437+00",
      "provenance_validation": "PASS"
    },
    {
      "scenario_id": "UAT-010",
      "observation_id": 2605,
      "status": "validated",
      "value": {
        "active_event_end": "2026-12-10T22:00:00+00:00",
        "active_event_start": "2026-12-10T16:30:00+00:00",
        "date_provenance": {
          "client_components": {
            "day": 10,
            "finish_time": "23:00",
            "month": 12,
            "start_time": "17:30"
          },
          "explicit_client_year": null,
          "reference_timestamp": "2026-10-03 09:17:43.603808+00",
          "resolved_year": 2026,
          "rule": "next_calendar_occurrence_v1",
          "source_reference": "inbound_source_record:2979",
          "timezone": "Europe/Amsterdam",
          "year_source": "system_inferred_next_occurrence"
        },
        "day": 10,
        "finish_time": "23:00",
        "month": 12,
        "resolved_date": "2026-12-10",
        "start_time": "17:30"
      },
      "source_received_at": "2026-10-03 09:17:43.603808+00",
      "provenance_validation": "PASS"
    },
    {
      "scenario_id": "UAT-011",
      "observation_id": 2610,
      "status": "validated",
      "value": {
        "active_event_end": "2026-12-15T18:00:00+00:00",
        "active_event_start": "2026-12-15T13:00:00+00:00",
        "date_provenance": {
          "client_components": {
            "day": 15,
            "finish_time": "19:00",
            "month": 12,
            "start_time": "14:00"
          },
          "explicit_client_year": null,
          "reference_timestamp": "2026-10-03 09:18:54.226721+00",
          "resolved_year": 2026,
          "rule": "next_calendar_occurrence_v1",
          "source_reference": "inbound_source_record:2984",
          "timezone": "Europe/Amsterdam",
          "year_source": "system_inferred_next_occurrence"
        },
        "day": 15,
        "finish_time": "19:00",
        "month": 12,
        "resolved_date": "2026-12-15",
        "start_time": "14:00"
      },
      "source_received_at": "2026-10-03 09:18:54.226721+00",
      "provenance_validation": "PASS"
    },
    {
      "scenario_id": "UAT-012",
      "observation_id": 2627,
      "status": "validated",
      "value": {
        "active_event_end": "2027-01-21T20:00:00+00:00",
        "active_event_start": "2027-01-21T16:00:00+00:00",
        "date_provenance": {
          "client_components": {
            "day": 21,
            "finish_time": "21:00",
            "month": 1,
            "start_time": "17:00"
          },
          "explicit_client_year": null,
          "reference_timestamp": "2026-10-03 09:21:14.26621+00",
          "resolved_year": 2027,
          "rule": "next_calendar_occurrence_v1",
          "source_reference": "inbound_source_record:3003",
          "timezone": "Europe/Amsterdam",
          "year_source": "system_inferred_next_occurrence"
        },
        "day": 21,
        "finish_time": "21:00",
        "month": 1,
        "resolved_date": "2027-01-21",
        "start_time": "17:00"
      },
      "source_received_at": "2026-10-03 09:21:14.26621+00",
      "provenance_validation": "PASS"
    },
    {
      "scenario_id": "UAT-012",
      "observation_id": 2618,
      "status": "validated",
      "value": {
        "date_provenance": {
          "explicit_client_year": null,
          "reference_timestamp": "2026-10-03 09:20:26.245766+00",
          "source_reference": "inbound_source_record:2993",
          "timezone": "Europe/Amsterdam",
          "year_source": "unresolved"
        },
        "month": 1
      },
      "source_received_at": "2026-10-03 09:20:26.245766+00",
      "provenance_validation": "PASS"
    },
    {
      "scenario_id": "UAT-013",
      "observation_id": 2632,
      "status": "validated",
      "value": {
        "active_event_end": "2027-02-08T16:00:00+00:00",
        "active_event_start": "2027-02-08T13:00:00+00:00",
        "date_provenance": {
          "client_components": {
            "day": 8,
            "finish_time": "17:00",
            "month": 2,
            "start_time": "14:00"
          },
          "explicit_client_year": null,
          "reference_timestamp": "2026-10-03 09:22:32.348089+00",
          "resolved_year": 2027,
          "rule": "next_calendar_occurrence_v1",
          "source_reference": "inbound_source_record:3008",
          "timezone": "Europe/Amsterdam",
          "year_source": "system_inferred_next_occurrence"
        },
        "day": 8,
        "finish_time": "17:00",
        "month": 2,
        "resolved_date": "2027-02-08",
        "start_time": "14:00"
      },
      "source_received_at": "2026-10-03 09:22:32.348089+00",
      "provenance_validation": "PASS"
    },
    {
      "scenario_id": "UAT-013",
      "observation_id": 2628,
      "status": "validated",
      "value": {
        "active_event_end": "2027-02-07T12:00:00+00:00",
        "active_event_start": "2027-02-07T09:00:00+00:00",
        "date_provenance": {
          "client_components": {
            "day": 7,
            "finish_time": "13:00",
            "month": 2,
            "start_time": "10:00"
          },
          "explicit_client_year": null,
          "reference_timestamp": "2026-10-03 09:22:15.80702+00",
          "resolved_year": 2027,
          "rule": "next_calendar_occurrence_v1",
          "source_reference": "inbound_source_record:3004",
          "timezone": "Europe/Amsterdam",
          "year_source": "system_inferred_next_occurrence"
        },
        "day": 7,
        "finish_time": "13:00",
        "month": 2,
        "resolved_date": "2027-02-07",
        "start_time": "10:00"
      },
      "source_received_at": "2026-10-03 09:22:15.80702+00",
      "provenance_validation": "PASS"
    }
  ],
  "draft_question_checks": [
    {
      "turn": "UAT-001/1",
      "asks_client_for_year": false
    },
    {
      "turn": "UAT-002/1",
      "asks_client_for_year": false
    },
    {
      "turn": "UAT-003/1",
      "asks_client_for_year": false
    },
    {
      "turn": "UAT-004/1",
      "asks_client_for_year": false
    },
    {
      "turn": "UAT-004/2",
      "asks_client_for_year": false
    },
    {
      "turn": "UAT-005/1",
      "asks_client_for_year": false
    },
    {
      "turn": "UAT-005/2",
      "asks_client_for_year": false
    },
    {
      "turn": "UAT-006/1",
      "asks_client_for_year": false
    },
    {
      "turn": "UAT-006/2",
      "asks_client_for_year": false
    },
    {
      "turn": "UAT-007/1",
      "asks_client_for_year": false
    },
    {
      "turn": "UAT-008/1",
      "asks_client_for_year": false
    },
    {
      "turn": "UAT-009/1",
      "asks_client_for_year": false
    },
    {
      "turn": "UAT-009/2",
      "asks_client_for_year": false
    },
    {
      "turn": "UAT-010/1",
      "asks_client_for_year": false
    },
    {
      "turn": "UAT-011/1",
      "asks_client_for_year": false
    },
    {
      "turn": "UAT-011/2",
      "asks_client_for_year": false
    },
    {
      "turn": "UAT-012/1",
      "asks_client_for_year": false
    },
    {
      "turn": "UAT-012/2",
      "asks_client_for_year": false
    },
    {
      "turn": "UAT-012/3",
      "asks_client_for_year": false
    },
    {
      "turn": "UAT-013/1",
      "asks_client_for_year": false
    },
    {
      "turn": "UAT-013/2",
      "asks_client_for_year": false
    }
  ]
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
  "approval calls": 0,
  "execution calls": 0,
  "ExecutionAttempts created": 0,
  "provider": "openai",
  "model": "gpt-5.6-sol",
  "synthetic_UAT_generation_requests": 21
}
```

Activity zeros are established from this task’s restricted request log and resulting synthetic case snapshots. Provider-free canonical and currentness checks passed; no production, Exchange RBAC, Entra permission, model/provider or environment-setting changes were made.

# Evidence Files

- [Exact plans and client-generation payloads](acceptance_planner_audit.json)
- [Frozen results, draft revisions and request log](acceptance_results.json)
- [Final snapshots](acceptance_final_snapshots.json)
- [Canonical binding audit](acceptance_captured_contract_validation.json)
- [Current draft and disabled-send audit](acceptance_integrity_audit.json)
- [Date provenance audit](acceptance_date_provenance.json)
- [Frozen manifest and authorized date expectations](frozen_manifest.json)

# Remaining Issues

- UAT-012 turns 1, 2 and 3: the selected known-audio fact is not stated as a positive capability. Each exact draft instead acknowledges the client’s music plan. Typed known/action_required=false semantics and the concise generation rule did not ensure realization in this run. Three per-turn unanswered-audio defects remain; continuity is 6/7.
- UAT-012 turns 2 and 3 repeat the unchanged music-plan acknowledgement. The corrected realization witness correctly records no audio evidence, and the planner correctly keeps the unanswered fact mandatory; the model again fails to express that fact. There is no cross-clause false-positive realization.
- One non-JSON/truncated response occurred during UAT-012/3 inquiry-waiting, before generation. The original request log proves no third-turn generation was attempted. One bounded recovery resumed waiting/reconciliation and generated that turn once; no case/message was reinjected and no accepted/rejected model result was repeated. Original evidence is preserved in acceptance_results_raw.json.
- No implementation change or second acceptance run followed these findings. Quality grades and defect counts are direct assistant assessments, not independent human validation.

# Final Marker

WNC_GOVERNED_DRAFTING_HUMAN_REVIEW_REQUIRED

Stopped after the single authorized acceptance run. No further implementation cycle or sending enablement.
