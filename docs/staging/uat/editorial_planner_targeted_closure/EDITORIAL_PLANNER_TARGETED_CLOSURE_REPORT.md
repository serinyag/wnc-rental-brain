# Targeted Defects Fixed

Targeted changes deployed once. 21/21 drafts persisted; continuity 6/7; 15 A / 6 B / 0 C / 0 D. The single acceptance run demonstrates remaining issues; no further implementation or generation cycle was performed.

## Known-No Proposition Scoping

Root cause: the restriction validator matched positive capability words anywhere in a compound email. Implementation: identify governed not-supported topics and stable aliases, evaluate capability wording in their clauses, preserve negation, coordinated subjects and subsequent pronoun references. Topic-less legacy contracts retain a conservative fallback. No other validator was changed.

Regressions cover positive projector wording beside a microphone restriction, contradictory microphone assertions, correctly negated and external-supplier statements, coordinated subjects, later contradictory clauses and DJ restrictions.

## Request Topic Matching

Root cause: raw substrings matched dj inside adjust/adjustment and sound in pricing prose. Implementation: one maintained finite token/phrase alias adapter at planner and retrieval-attention boundaries. The kitchen repeat-question selector distinguishes supplier logistics from food-preparation questions. No classifier or model was added.

Regressions cover adjust, adjustment, pricing sounds realistic, background sound system, explicit DJ setup and acknowledged DJ restrictions beside a fee-adjustment question.

## Pricing vs Budget Semantics

Root cause: every overall pricing question produced a budget-aware action. Implementation: independent overall_pricing_requested and absent/general_constraint/explicit_amount budget context. Absent budget produces an event/options pricing check; explicit constraints retain budget context. A budget observation alone does not invent a fee question.

Regressions cover cost/prices questions, tight budget, explicit EUR amount and pricing sound realistic without audio.

## Client-Language Projection

- Audio: project governed supported audio as client_fact.background_music_playback=true; authoritative status remains local.
- Optional hologram: preserve a structured optional preference and the planning that should continue, instead of generic change acknowledgement.
- Aerial rig: project installation and operation safety questions with report_back=true, without an abstract feasibility label.
- Replace one existing style sentence with a concise ordinary-language rule for internal status labels. No provider, model, architecture or approval changes.

The versioned planner/context hash is now editorial_content_plan_v3. Prior evidence and historical draft records are preserved.

# Tests

```json
{
  "focused": 118,
  "focused_subtests": 13,
  "full": 655,
  "phase8_within_full_suite": 438,
  "full_subtests": 160,
  "failures": 0
}
```

Started existing local Docker PostgreSQL container and installed declared dependencies in isolated test environment. Initial full run could not reach Docker and lacked psycopg; no staging or model calls occurred during this repair.

The 438 Phase 8 tests are included in the full repository run. git diff --check passed before implementation commit. Existing collection warnings concern application classes named Test*, not failing tests.

# Deployment

```json
{
  "commit": "b948e09e7bacf1c6f4642ea15abdfdb5ef952bc0",
  "deploy_id": "dep-db0bgju0tbcc73f4aep0",
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

# Frozen UAT

```json
{
  "persisted_drafts": 21,
  "attempted_turns": 21,
  "continuity": "6/7",
  "grades": {
    "A": 15,
    "B": 6,
    "C": 0,
    "D": 0
  },
  "editorial_defects": {
    "known_no_false_positive": 0,
    "substring_topic_collision": 0,
    "invented_budget": 0,
    "unnecessary_information": 1,
    "repetition": 0,
    "policy_dump": 0,
    "policy_copy": 0,
    "system_language": 0,
    "unanswered_request": 1,
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

Exactly one acceptance run on the unchanged 13-scenario, 21-turn manifest. Reviews below are direct assistant assessments of exact outputs and plans, not an external judge or independent human study. Grades are secondary to the defect gates. No accepted or rejected generation was repeated.

## Continuity evidence

```json
[
  {
    "scenario_id": "UAT-004",
    "case_id": 546,
    "turns": 2,
    "result": "PASS",
    "evidence": {
      "UAT-004/1": "Answers slides, music and the custom display; the latter remains a concrete safety check. Supported-status wording is gone. Background music playback is also possible is slightly formal but expresses a direct capability fact without the demonstrated status-label construction.",
      "UAT-004/2": "Acknowledges the structured optional hologram preference and continues projection planning. No dependency wording, repeated music answer or secondary projection checklist. The practical projection check remains useful and unconfirmed."
    }
  },
  {
    "scenario_id": "UAT-005",
    "case_id": 547,
    "turns": 2,
    "result": "PASS",
    "evidence": {
      "UAT-005/1": "Retains the material kitchen suitability constraint and facilitator availability/format check. One compact kitchen paragraph answers the current catering question; no secondary kitchen checklist or unsupported booking assertion.",
      "UAT-005/2": "Responds to the buffet setup duration and flexible facilitator format with the two corresponding checks. Prior kitchen guidance is ALREADY_COMMUNICATED and omitted; no loading route or unrelated handover requirements added."
    }
  },
  {
    "scenario_id": "UAT-006",
    "case_id": 548,
    "turns": 2,
    "result": "PASS",
    "evidence": {
      "UAT-006/1": "Brief acknowledgement and prospective Studio availability check; no fees, capacity figures or unsupported confirmation.",
      "UAT-006/2": "Acknowledges all three requested changes and offers review without confirming them. The sentence pairing is slightly repetitive in phrasing, but it does not repeat old answers or add unrelated information."
    }
  },
  {
    "scenario_id": "UAT-009",
    "case_id": 551,
    "turns": 2,
    "result": "PASS",
    "evidence": {
      "UAT-009/1": "Uses the governed current EUR 50 fee and 21% VAT from this case, while keeping the requested adjustment pending. Does not promote the historical waiver into present authority.",
      "UAT-009/2": "Acknowledges the previous-team clarification and retains only the fee-adjustment check. No repeated price or current-process/historical-authority explanation."
    }
  },
  {
    "scenario_id": "UAT-011",
    "case_id": 553,
    "turns": 2,
    "result": "PASS",
    "evidence": {
      "UAT-011/1": "Persists a valid compound reply covering kitchen suitability, projector setup, external microphones and one immediate access constraint. No false known-no rejection, route claim, actual arrival authorization or secondary supplier checklist. The longer reply is justified by the compound request.",
      "UAT-011/2": "Fresh-case accepted first-turn evidence suppresses kitchen, microphones and access policy; projection is deferred because it is not reopened. Only handover, arrival timing and loading route checks remain. No unrequested technical/catering repetition or invented arrival window."
    }
  },
  {
    "scenario_id": "UAT-012",
    "case_id": 554,
    "turns": 3,
    "result": "FAIL",
    "evidence": {
      "UAT-012/1": "The acknowledged DJ restriction is correctly absent. Required timing/headcount questions, kitchen constraint, projection check and commercial/facilitator next steps remain. However, the selected known audio fact becomes a future setup check instead of a clear capability answer. The global realization witness then treats possible in the unrelated fee sentence as evidence that the audio answer was communicated.",
      "UAT-012/2": "Handles the new headcount and brief facilitator welcome, preserves the outstanding timing question and fee/facilitator checks, and omits technical/catering repetition. Inherited audio realization is not valid proof of a prior capability answer; that defect is counted at turn 1.",
      "UAT-012/3": "Answers the earlier unresolved fee question with newly available EUR 75 excl. VAT and 21% VAT. Retains pending adjustment and facilitator checks, without re-asking timing or repeating technical/catering policy."
    }
  },
  {
    "scenario_id": "UAT-013",
    "case_id": 555,
    "turns": 2,
    "result": "PASS",
    "evidence": {
      "UAT-013/1": "Brief acknowledgement with a prospective availability check, no unrequested facts.",
      "UAT-013/2": "Acknowledges the new date/time and checks the reschedule without confirming it or repeating the earlier event summary."
    }
  }
]
```

## Turn reviews

| Turn | Grade | Result | Findings |
|---|---|---|---|
| UAT-001/1 | A | PASS | Answers the fee with EUR 75 excl. VAT and 21% VAT, plus a prospective availability check. No unsupported confirmation or irrelevant policy. |
| UAT-002/1 | A | PASS | Preserves all four required questions, including year/start/finish. Offers an options and overall-price check without inventing a budget; payload explicitly marks budget absent. |
| UAT-003/1 | A | PASS | Answers suitability using the current within-limits capacity projection, without quoting an irrelevant maximum. Availability remains a prospective check. The historical scenario title does not override current governed capacity. |
| UAT-004/1 | B | PASS | Answers slides, music and the custom display; the latter remains a concrete safety check. Supported-status wording is gone. Background music playback is also possible is slightly formal but expresses a direct capability fact without the demonstrated status-label construction. |
| UAT-004/2 | A | PASS | Acknowledges the structured optional hologram preference and continues projection planning. No dependency wording, repeated music answer or secondary projection checklist. The practical projection check remains useful and unconfirmed. |
| UAT-005/1 | B | PASS | Retains the material kitchen suitability constraint and facilitator availability/format check. One compact kitchen paragraph answers the current catering question; no secondary kitchen checklist or unsupported booking assertion. |
| UAT-005/2 | A | PASS | Responds to the buffet setup duration and flexible facilitator format with the two corresponding checks. Prior kitchen guidance is ALREADY_COMMUNICATED and omitted; no loading route or unrelated handover requirements added. |
| UAT-006/1 | A | PASS | Brief acknowledgement and prospective Studio availability check; no fees, capacity figures or unsupported confirmation. |
| UAT-006/2 | B | PASS | Acknowledges all three requested changes and offers review without confirming them. The sentence pairing is slightly repetitive in phrasing, but it does not repeat old answers or add unrelated information. |
| UAT-007/1 | A | PASS | Preserves the full timing question including year, start and finish. No kitchen guidance, equipment questions or unrelated supplier requirements. |
| UAT-008/1 | A | PASS | Correct fee/VAT, overall pricing and pending flexibility check. Explicit tight budget remains general_constraint; primary need is commercial only, with no audio collision. No discount is asserted as approved. |
| UAT-009/1 | A | PASS | Uses the governed current EUR 50 fee and 21% VAT from this case, while keeping the requested adjustment pending. Does not promote the historical waiver into present authority. |
| UAT-009/2 | A | PASS | Acknowledges the previous-team clarification and retains only the fee-adjustment check. No repeated price or current-process/historical-authority explanation. |
| UAT-010/1 | B | FAIL | The targeted abstract-feasibility wording is gone and the rig check is concrete. However, removing status from the new action value makes the existing fallback fail to recognize a pending check, so it adds an unnecessary venue-availability paragraph to this capability-focused reply. Safe but fails the strict editorial gate; no follow-on implementation is authorized. |
| UAT-011/1 | B | PASS | Persists a valid compound reply covering kitchen suitability, projector setup, external microphones and one immediate access constraint. No false known-no rejection, route claim, actual arrival authorization or secondary supplier checklist. The longer reply is justified by the compound request. |
| UAT-011/2 | A | PASS | Fresh-case accepted first-turn evidence suppresses kitchen, microphones and access policy; projection is deferred because it is not reopened. Only handover, arrival timing and loading route checks remain. No unrequested technical/catering repetition or invented arrival window. |
| UAT-012/1 | B | FAIL | The acknowledged DJ restriction is correctly absent. Required timing/headcount questions, kitchen constraint, projection check and commercial/facilitator next steps remain. However, the selected known audio fact becomes a future setup check instead of a clear capability answer. The global realization witness then treats possible in the unrelated fee sentence as evidence that the audio answer was communicated. |
| UAT-012/2 | A | PASS | Handles the new headcount and brief facilitator welcome, preserves the outstanding timing question and fee/facilitator checks, and omits technical/catering repetition. Inherited audio realization is not valid proof of a prior capability answer; that defect is counted at turn 1. |
| UAT-012/3 | A | PASS | Answers the earlier unresolved fee question with newly available EUR 75 excl. VAT and 21% VAT. Retains pending adjustment and facilitator checks, without re-asking timing or repeating technical/catering policy. |
| UAT-013/1 | A | PASS | Brief acknowledgement with a prospective availability check, no unrequested facts. |
| UAT-013/2 | A | PASS | Acknowledges the new date/time and checks the reschedule without confirming it or repeating the earlier event summary. |

# Exact 21 Drafts

Every subject and body below is reproduced verbatim from saved generation evidence. These drafts were not approved or sent.

## UAT-001/1

DraftRevision 318; captured validator PASS. Exact approval/action binding: PASS.

**Subject**

```text
Studio product workshop
```

**Body**

```text
Hi Maya,

The Studio sounds like a great setting for your product workshop. The booking fee is EUR 75 excl. VAT, with VAT charged at 21%.

I’ll check the Studio’s availability for your requested date and event time, then let you know the next steps.
```

## UAT-002/1

DraftRevision 319; captured validator PASS. Exact approval/action binding: PASS.

**Subject**

```text
Your WNC offsite enquiry
```

**Body**

```text
Hi Jon,

It’s lovely to hear WNC was recommended for your team’s offsite. To give you a useful idea of what may be possible, could you let me know:

• What full date, including the year, start time and finish time would you like?
• How many guests are expected?
• Which space would you like?
• What type of event are you planning?

Once I have those details, I’ll check the options and overall rental pricing, including the booking fee.
```

## UAT-003/1

DraftRevision 320; captured validator PASS. Exact approval/action binding: PASS.

**Subject**

```text
Awards evening enquiry
```

**Body**

```text
Hi Priya,

An awards evening for your colleagues sounds lovely. Your group size is suitable for exclusive use of the whole venue.

I’ll check availability for the requested date and event time and come back to you.
```

## UAT-004/1

DraftRevision 321; captured validator PASS. Exact approval/action binding: PASS.

**Subject**

```text
Product launch technical setup
```

**Body**

```text
Hi Elena,

The product launch sounds like a great use of the Studio. We have a WNC projector for slide projection, and I’ll check the practical setup for the space. Background music playback is also possible.

For the small hologram display, I’ll check whether the requested custom equipment can be installed and operated safely, then report back on what is realistic.
```

## UAT-004/2

DraftRevision 322; captured validator PASS. Exact approval/action binding: PASS.

**Subject**

```text
Projection setup
```

**Body**

```text
Hi Elena,

Understood, we can keep the hologram optional so it does not delay the wider planning. A WNC projector is available for the display, and I’ll check the practical projection setup for your event.
```

## UAT-005/1

DraftRevision 323; captured validator PASS. Exact approval/action binding: PASS.

**Subject**

```text
Studio strategy session
```

**Body**

```text
Hi Samira,

An all-day strategy session with WNC facilitating the morning sounds like a useful format. I’ll check the requested facilitator’s availability and the proposed format.

Your caterer could use the catering kitchen for ready-made food, warming, plating and simple assembly, but it is not suitable for large-scale food production.
```

## UAT-005/2

DraftRevision 324; captured validator PASS. Exact approval/action binding: PASS.

**Subject**

```text
Buffet setup and facilitator
```

**Body**

```text
Hi Samira,

A simple buffet with about 45 minutes of setup is helpful context, and the flexibility on the facilitator format gives us useful options. I’ll check supplier setup access and the facilitator’s availability, including alternative formats if a full morning is not available.
```

## UAT-006/1

DraftRevision 325; captured validator PASS. Exact approval/action binding: PASS.

**Subject**

```text
Studio planning meeting
```

**Body**

```text
Hi Theo,

The Studio sounds like a good setting to consider for your planning meeting. I’ll check the Studio’s availability for your requested date and time and come back to you.
```

## UAT-006/2

DraftRevision 326; captured validator PASS. Exact approval/action binding: PASS.

**Subject**

```text
Updated venue enquiry
```

**Body**

```text
Hi Theo,

I’ve noted that your group has grown and that you now need the entire venue at the revised date and time. I’ll check the updated guest count, full-venue rental and reschedule request, then come back to you.
```

## UAT-007/1

DraftRevision 327; captured validator PASS. Exact approval/action binding: PASS.

**Subject**

```text
Supper club date check
```

**Body**

```text
Hi Lena,

A 26-person supper club with your own caterer sounds lovely. What full date, including the year, and start and finish times would you like me to check?
```

## UAT-008/1

DraftRevision 328; captured validator PASS. Exact approval/action binding: PASS.

**Subject**

```text
Studio pricing
```

**Body**

```text
Hi Omar,

I understand that keeping the leadership session within a tight budget is important. The booking fee is EUR 75 excl. VAT, with VAT charged at 21%.

I’ll check the overall rental pricing for your requested setup with your budget in mind, along with whether any adjustment to the booking fee can be arranged if you confirm quickly.
```

## UAT-009/1

DraftRevision 329; captured validator PASS. Exact approval/action binding: PASS.

**Subject**

```text
Studio booking fee
```

**Body**

```text
Hi Claire,

It would be lovely to welcome you back for another salon. The booking fee is EUR 50 excl. VAT, with VAT at 21%. I’ll check what can be arranged regarding the fee adjustment and come back to you.
```

## UAT-009/2

DraftRevision 330; captured validator PASS. Exact approval/action binding: PASS.

**Subject**

```text
Booking fee adjustment
```

**Body**

```text
Hi Claire,

Thanks for clarifying that the earlier event was under the previous team. I’ll check what can be arranged regarding the booking fee adjustment and come back to you.
```

## UAT-010/1

DraftRevision 331; captured validator PASS. Exact approval/action binding: PASS.

**Subject**

```text
Investor dinner aerial rig
```

**Body**

```text
Hi David,

The suspended aerial performance could be a striking element for the investor dinner. I’ll check whether a custom rig can be installed and operated safely at the venue.

I’ll also check venue availability for your requested date and times, then report back on both points.
```

## UAT-011/1

DraftRevision 332; captured validator PASS. Exact approval/action binding: PASS.

**Subject**

```text
Panel discussion practical requirements
```

**Body**

```text
Hi Nora,

The panel discussion setup sounds clear, including the florist, external caterer and AV needs. The catering kitchen is suitable for ready-made food, warming, plating and simple assembly, but not large-scale food production.

We have a WNC projector, and I’ll check the practical projection setup for the panel. Microphones are not provided, so those would need to come from an external supplier.

Supplier deliveries, unloading and setup must take place within the confirmed rental period unless agreed otherwise in writing. I’ll check the proposed supplier arrival timing and setup access.
```

## UAT-011/2

DraftRevision 333; captured validator PASS. Exact approval/action binding: PASS.

**Subject**

```text
Supplier logistics
```

**Body**

```text
Hi Nora,

Understood that the florist will wait until the venue handover requirements are clear, and that the caterer needs practical arrival details.

I’ll check the venue handover requirements, supplier arrival timing and loading route, then come back to you.
```

## UAT-012/1

DraftRevision 334; captured validator PASS. Exact approval/action binding: PASS.

**Subject**

```text
January Studio gathering
```

**Body**

```text
Hi Ari,

Your plans for slides, background music and an outside caterer sound well suited to a relaxed Studio gathering. WNC has a projector, and I’ll check the practical setup for both the projection and music playback. The catering kitchen is suitable for ready-made food, warming, plating and simple assembly, rather than large-scale food production.

I’ll also check the booking fee, what adjustment may be possible, and the availability and format of a short facilitator-led opening.

What full date, including the year, start time and finish time would you like? How many guests are expected?
```

## UAT-012/2

DraftRevision 335; captured validator PASS. Exact approval/action binding: PASS.

**Subject**

```text
Event details
```

**Body**

```text
Hi Ari,

Thanks for clarifying that the group is now 24 and the facilitator would only be needed for a brief welcome, with flexibility around availability.

Once the timing is settled, I’ll check the booking fee, what can be arranged regarding the requested fee adjustment, and the facilitator’s availability and format.

What full date, including the year, start time and finish time would you like?
```

## UAT-012/3

DraftRevision 336; captured validator PASS. Exact approval/action binding: PASS.

**Subject**

```text
Gathering details
```

**Body**

```text
Hi Ari,

Thanks for clarifying the timing. The booking fee is EUR 75 excl. VAT, with VAT at 21%.

I’ll check what can be arranged regarding an adjustment to the booking fee, as well as the requested facilitator’s availability and format.
```

## UAT-013/1

DraftRevision 337; captured validator PASS. Exact approval/action binding: PASS.

**Subject**

```text
Studio planning session
```

**Body**

```text
Hi Riley,

Thanks for sharing the details of your Studio planning session. I’ll check the requested date and venue availability and follow up with you.
```

## UAT-013/2

DraftRevision 338; captured validator PASS. Exact approval/action binding: PASS.

**Subject**

```text
Session reschedule
```

**Body**

```text
Hi Riley,

I’ve noted the new date and time. I’ll check the requested change and come back to you.
```

# Critical Regression Turns

## UAT-002/1

Previous defect: Invented client budget in the overall pricing next step.

Deterministic root cause: Pricing and budget concepts were conflated in a single fixed action.

Fix: Independent pricing request and budget context, with absent budget excluded from the action.

Result: **PASS**. Preserves all four required questions, including year/start/finish. Offers an options and overall-price check without inventing a budget; payload explicitly marks budget absent.

### Final plan

```json
{
  "acknowledge": [
    {
      "authority_class": "client_request",
      "fingerprint": "5af9b6474d577fd7ebc47159db273bc4b5c5f61477cfba55032edc2d102390b9",
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
        "about": "the enquiry",
        "kind": "new_enquiry"
      }
    }
  ],
  "already_communicated": [],
  "client_visible_pending_state": [
    {
      "action": "check requested booking fee or pricing",
      "status": "check_required",
      "topic": "commercial_next_step"
    },
    {
      "action": "check overall rental pricing for the requested event/options",
      "budget_context": "absent",
      "overall_pricing_requested": true,
      "status": "check_required",
      "topic": "overall_pricing"
    }
  ],
  "defer": [
    {
      "authority_class": "current_governed",
      "fingerprint": "5e1b7a59bf98cd79bf717b0d18768ff2bf2a969ee1c16d258e22d0e6a2ef0bcb",
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
        "fact": "Requested rental type code: custom_scope"
      }
    }
  ],
  "do_not_repeat": [],
  "editorial_rationale": "compound_material_answers_and_client_questions",
  "helpful_now": [],
  "internal_only": [
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
      "fingerprint": "d83409e8b4987ac9891c6923a18e338afe102d2d196568bf4d1f86c3aa0230fa",
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
        "text": "Hard constraint: Open question 2096 must be resolved."
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "c94f21900cb6056372ed23d8592e9e9b47b9d5bffb48544ee0ddbd77ca9d9dbc",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 50,
      "proposition_key": "internal:open_question:2096",
      "reason": "ownership_and_workflow_mechanics_stay_local",
      "role": "INTERNAL_ONLY",
      "semantic_key": "internal:open_question:2096",
      "source_reference": "open_question:2096",
      "topic": "resolution",
      "value": {
        "message": "What date and time is the client requesting for the event?",
        "owner": "CLIENT",
        "status": "REQUIRED"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "76b1fb106d30bc4f6deed58692658af49439aabc7172c9f27d365a417e77b05f",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 50,
      "proposition_key": "internal:open_question:2097",
      "reason": "ownership_and_workflow_mechanics_stay_local",
      "role": "INTERNAL_ONLY",
      "semantic_key": "internal:open_question:2097",
      "source_reference": "open_question:2097",
      "topic": "resolution",
      "value": {
        "message": "How many guests are expected?",
        "owner": "CLIENT",
        "status": "REQUIRED"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "594c80d5bd26969ff37a462e967c4ae3bc357bc9ccda4954e4ff513ae40ddeb2",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 50,
      "proposition_key": "internal:open_question:2098",
      "reason": "ownership_and_workflow_mechanics_stay_local",
      "role": "INTERNAL_ONLY",
      "semantic_key": "internal:open_question:2098",
      "source_reference": "open_question:2098",
      "topic": "resolution",
      "value": {
        "message": "Which space or rental scope is the client requesting?",
        "owner": "CLIENT",
        "status": "REQUIRED"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "ca7eeb73e91cf28c15225824a33b7d6ad33033738d964ec2580991beff62e603",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 50,
      "proposition_key": "internal:open_question:2099",
      "reason": "ownership_and_workflow_mechanics_stay_local",
      "role": "INTERNAL_ONLY",
      "semantic_key": "internal:open_question:2099",
      "source_reference": "open_question:2099",
      "topic": "resolution",
      "value": {
        "message": "What type of event is the client planning?",
        "owner": "CLIENT",
        "status": "REQUIRED"
      }
    }
  ],
  "must_ask": [
    {
      "authority_class": "current_governed",
      "fingerprint": "364cec76f455667510c899940ef02359d2fb96f5c252d093ec153e9f28e0847c",
      "included_in_model_payload": true,
      "prior_turn_status": "not_previously_communicated",
      "priority": 2,
      "proposition_key": "question:2096",
      "reason": "open_client_owned_question",
      "role": "MUST_ASK",
      "semantic_key": "question:2096",
      "source_reference": "governed_case",
      "topic": "client_information",
      "value": {
        "open_question_id": 2096,
        "question": "What full date (including year), start time and finish time would you like?"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "d41b81c6130e65dcf672a9754a17a540e3d7fbefd83494c12c19306d6bc55452",
      "included_in_model_payload": true,
      "prior_turn_status": "not_previously_communicated",
      "priority": 2,
      "proposition_key": "question:2097",
      "reason": "open_client_owned_question",
      "role": "MUST_ASK",
      "semantic_key": "question:2097",
      "source_reference": "governed_case",
      "topic": "client_information",
      "value": {
        "open_question_id": 2097,
        "question": "How many guests are expected?"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "d5452f00c6a8f8597dd2873f6f4964d958918ce23e0342267fef7e0e521d9d90",
      "included_in_model_payload": true,
      "prior_turn_status": "not_previously_communicated",
      "priority": 2,
      "proposition_key": "question:2098",
      "reason": "open_client_owned_question",
      "role": "MUST_ASK",
      "semantic_key": "question:2098",
      "source_reference": "governed_case",
      "topic": "client_information",
      "value": {
        "open_question_id": 2098,
        "question": "Which space would you like?"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "4ba67ebb131b6918fdd6a1e933be5896d9718ea3c663e0b229d402ecebc89d24",
      "included_in_model_payload": true,
      "prior_turn_status": "not_previously_communicated",
      "priority": 2,
      "proposition_key": "question:2099",
      "reason": "open_client_owned_question",
      "role": "MUST_ASK",
      "semantic_key": "question:2099",
      "source_reference": "governed_case",
      "topic": "client_information",
      "value": {
        "open_question_id": 2099,
        "question": "What type of event are you planning?"
      }
    }
  ],
  "must_communicate": [
    {
      "authority_class": "current_governed",
      "fingerprint": "ce5b101ef2c0cf0ac8e6f03a94d256bc5bdcc8cd709f95396f8a767d60c2d110",
      "included_in_model_payload": true,
      "prior_turn_status": "not_previously_communicated",
      "priority": 4,
      "proposition_key": "commercial.check",
      "reason": "requested_answer_not_yet_available",
      "role": "MUST_COMMUNICATE",
      "semantic_key": "commercial.check",
      "source_reference": "governed_case",
      "topic": "commercial_next_step",
      "value": {
        "action": "check requested booking fee or pricing",
        "status": "check_required"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "3be26634bf7d5ab561eeba63ed096d3b5b082ad07e57dab90883c03d157d5df3",
      "included_in_model_payload": true,
      "prior_turn_status": "not_previously_communicated",
      "priority": 1,
      "proposition_key": "commercial.overall_pricing",
      "reason": "overall_pricing_question_is_distinct_from_booking_fee",
      "role": "MUST_COMMUNICATE",
      "semantic_key": "commercial.overall_pricing",
      "source_reference": "governed_case",
      "topic": "overall_pricing",
      "value": {
        "action": "check overall rental pricing for the requested event/options",
        "budget_context": "absent",
        "overall_pricing_requested": true,
        "status": "check_required"
      }
    }
  ],
  "primary_client_need": [
    "client_owned_missing_information"
  ],
  "response_intent": "REQUEST_CLIENT_INFORMATION",
  "source_bindings": [
    {
      "fingerprint": "364cec76f455667510c899940ef02359d2fb96f5c252d093ec153e9f28e0847c",
      "semantic_key": "question:2096",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "d41b81c6130e65dcf672a9754a17a540e3d7fbefd83494c12c19306d6bc55452",
      "semantic_key": "question:2097",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "d5452f00c6a8f8597dd2873f6f4964d958918ce23e0342267fef7e0e521d9d90",
      "semantic_key": "question:2098",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "4ba67ebb131b6918fdd6a1e933be5896d9718ea3c663e0b229d402ecebc89d24",
      "semantic_key": "question:2099",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "5af9b6474d577fd7ebc47159db273bc4b5c5f61477cfba55032edc2d102390b9",
      "semantic_key": "latest_client_detail",
      "source_reference": "current_client_message"
    },
    {
      "fingerprint": "ce5b101ef2c0cf0ac8e6f03a94d256bc5bdcc8cd709f95396f8a767d60c2d110",
      "semantic_key": "commercial.check",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "3be26634bf7d5ab561eeba63ed096d3b5b082ad07e57dab90883c03d157d5df3",
      "semantic_key": "commercial.overall_pricing",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "e084eb1ddf7869d97ab6fe0e778af8f41984f4d766b8f01801864ed1864b18b6",
      "semantic_key": "restriction:Confirmation still required",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "d83409e8b4987ac9891c6923a18e338afe102d2d196568bf4d1f86c3aa0230fa",
      "semantic_key": "restriction:Hard constraint",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "5e1b7a59bf98cd79bf717b0d18768ff2bf2a969ee1c16d258e22d0e6a2ef0bcb",
      "semantic_key": "case_fact:Requested rental type code",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "c94f21900cb6056372ed23d8592e9e9b47b9d5bffb48544ee0ddbd77ca9d9dbc",
      "semantic_key": "internal:open_question:2096",
      "source_reference": "open_question:2096"
    },
    {
      "fingerprint": "76b1fb106d30bc4f6deed58692658af49439aabc7172c9f27d365a417e77b05f",
      "semantic_key": "internal:open_question:2097",
      "source_reference": "open_question:2097"
    },
    {
      "fingerprint": "594c80d5bd26969ff37a462e967c4ae3bc357bc9ccda4954e4ff513ae40ddeb2",
      "semantic_key": "internal:open_question:2098",
      "source_reference": "open_question:2098"
    },
    {
      "fingerprint": "ca7eeb73e91cf28c15225824a33b7d6ad33033738d964ec2580991beff62e603",
      "semantic_key": "internal:open_question:2099",
      "source_reference": "open_question:2099"
    }
  ],
  "substantive_budget": 6,
  "version": "editorial_content_plan_v3"
}
```

### Exact final draft

DraftRevision 319; captured validator PASS. Exact approval/action binding: PASS.

**Subject**

```text
Your WNC offsite enquiry
```

**Body**

```text
Hi Jon,

It’s lovely to hear WNC was recommended for your team’s offsite. To give you a useful idea of what may be possible, could you let me know:

• What full date, including the year, start time and finish time would you like?
• How many guests are expected?
• Which space would you like?
• What type of event are you planning?

Once I have those details, I’ll check the options and overall rental pricing, including the booking fee.
```

## UAT-004/1

Previous defect: Background music can be supported.

Deterministic root cause: A supported status label was supplied as writing material.

Fix: Typed background_music_playback client fact and one concise style rule.

Result: **PASS**. Answers slides, music and the custom display; the latter remains a concrete safety check. Supported-status wording is gone. Background music playback is also possible is slightly formal but expresses a direct capability fact without the demonstrated status-label construction.

### Final plan

```json
{
  "acknowledge": [
    {
      "authority_class": "client_request",
      "fingerprint": "f812f313a58009be9e206d69ddd2257c4c88b545576361b293ac150f368e2c40",
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
        "about": "product launch",
        "kind": "new_enquiry"
      }
    }
  ],
  "already_communicated": [],
  "client_visible_pending_state": [
    {
      "available_equipment": "WNC projector",
      "capability": "projection display",
      "check_required": [
        "practical projection setup"
      ],
      "status": "conditional",
      "topic": "projection_display"
    }
  ],
  "defer": [
    {
      "authority_class": "current_governed",
      "fingerprint": "d48a4e749f26bd87be6140eb859f17d122a1ad07af3a4144f1406fc448f23d20",
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
        "booking_fee": "EUR 75 excl. VAT",
        "vat": "21%"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "6122a3ce441a205292345e4d3d4a38bb3109a91e3f917dd76ae2eef9a236ca7c",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 2,
      "proposition_key": "condition:projection:compatibility",
      "reason": "secondary_condition_covered_by_practical_setup_check",
      "role": "DEFER",
      "semantic_key": "condition:projection:compatibility",
      "source_reference": "phase4:technical_projection_display_confirmation",
      "topic": "projection_detail",
      "value": {
        "check_required": "compatibility",
        "status": "check_required"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "5e8f29a1d9629cc021bd2ccd83aa4468a851fc511a44b7ecad568d55fc4bd47e",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 2,
      "proposition_key": "condition:projection:adapters",
      "reason": "secondary_condition_covered_by_practical_setup_check",
      "role": "DEFER",
      "semantic_key": "condition:projection:adapters",
      "source_reference": "phase4:technical_projection_display_confirmation",
      "topic": "projection_detail",
      "value": {
        "check_required": "adapters",
        "status": "check_required"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "b6312d47aaacfa659bd04872fbbcb938cb4df350aeeac5bd29dcced00b324a89",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 2,
      "proposition_key": "condition:projection:files",
      "reason": "secondary_condition_covered_by_practical_setup_check",
      "role": "DEFER",
      "semantic_key": "condition:projection:files",
      "source_reference": "phase4:technical_projection_display_confirmation",
      "topic": "projection_detail",
      "value": {
        "check_required": "files",
        "status": "check_required"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "387c84d92eb347262b6b659159512dd9b332201e339e80a87b97e954df522a69",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 2,
      "proposition_key": "condition:projection:screenless setup suitability",
      "reason": "secondary_condition_covered_by_practical_setup_check",
      "role": "DEFER",
      "semantic_key": "condition:projection:screenless setup suitability",
      "source_reference": "phase4:technical_projection_display_confirmation",
      "topic": "projection_detail",
      "value": {
        "check_required": "screenless setup suitability",
        "status": "check_required"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "456e120a424a2fe5c89eb23e5e9000bcf6fda29bad8a4c6194d62bb8442f2b58",
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
        "fact": "guest_count: 24"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "2552d1b763e9729607a18482b08844ed4593ecf000cdd90f2d5ea54495dbbbc9",
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
        "fact": "event_type: product launch"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "3a1f8a2a7b03a7dea4ae51bbe7fbfe5fb55647f359d79b107c0d284f05f32c26",
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
        "fact": "Requested rental type code: studio_space"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "6bfe62085eead7f3d038270f40f682c14073f0271832385a90b8f9295c3f041a",
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
        "fact": "Requested active event start: 2026-10-29 16:00:00+00"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "3766935d35a75d618fddd18c07669619c1959cc4e35acb410efb71b784f4c0d6",
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
        "fact": "Requested active event end: 2026-10-29 20:00:00+00"
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
      "fingerprint": "816840951f456995403862c1a3f84422ee194094687b8c3052dc3ce480d52c04",
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
        "text": "Hard constraint: Current authority must be resolved before consequential workflow commitment."
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "83d6a831ab65f3a636e9cc30c5babfdd945a745e35e6781a2d87da5313a126d0",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 50,
      "proposition_key": "internal:blocker:2180",
      "reason": "ownership_and_workflow_mechanics_stay_local",
      "role": "INTERNAL_ONLY",
      "semantic_key": "internal:blocker:2180",
      "source_reference": "blocker:2180",
      "topic": "resolution",
      "value": {
        "message": "Confirm the requested room layout against capacity requirements",
        "owner": "WNC_INTERNAL",
        "status": "ACTION_CREATED"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "fd753f4dec40616cf0fdd67580acaba2b67cb24efddd900a90367eb0a6eea4cc",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 50,
      "proposition_key": "internal:blocker:2181",
      "reason": "ownership_and_workflow_mechanics_stay_local",
      "role": "INTERNAL_ONLY",
      "semantic_key": "internal:blocker:2181",
      "source_reference": "blocker:2181",
      "topic": "resolution",
      "value": {
        "message": "Confirm event-specific technical setup",
        "owner": "WNC_INTERNAL",
        "status": "ACTION_CREATED"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "c2fe8726d57cc00a3394a4d007e8007e3ddc61d10b4bf2c0f556c8c4c7f64d64",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 50,
      "proposition_key": "internal:availability:2026-10-29 16:00:00+00:2026-10-29 20:00:00+00",
      "reason": "ownership_and_workflow_mechanics_stay_local",
      "role": "INTERNAL_ONLY",
      "semantic_key": "internal:availability:2026-10-29 16:00:00+00:2026-10-29 20:00:00+00",
      "source_reference": "availability:2026-10-29 16:00:00+00:2026-10-29 20:00:00+00",
      "topic": "resolution",
      "value": {
        "message": "Confirm studio space availability for 2026-10-29 16:00:00+00 to 2026-10-29 20:00:00+00",
        "owner": "WNC_INTERNAL",
        "status": "ACTION_CREATED"
      }
    }
  ],
  "must_ask": [],
  "must_communicate": [
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
      "fingerprint": "672b1a863ea87ac08dad150ee3c17339d636ca915f70b17294df2679b3424af4",
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
        "client_fact": {
          "background_music_playback": true
        }
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "1e6ee4050b7e8172dbddd436669d38b8ef634bf790b07dd08c6703662b6d9126",
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
        "subject": "requested custom equipment"
      }
    }
  ],
  "primary_client_need": [
    "audio_playback",
    "other_technical",
    "projection_display"
  ],
  "response_intent": "PENDING_INTERNAL_CONFIRMATION",
  "source_bindings": [
    {
      "fingerprint": "f812f313a58009be9e206d69ddd2257c4c88b545576361b293ac150f368e2c40",
      "semantic_key": "latest_client_detail",
      "source_reference": "current_client_message"
    },
    {
      "fingerprint": "d48a4e749f26bd87be6140eb859f17d122a1ad07af3a4144f1406fc448f23d20",
      "semantic_key": "commercial.current",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "6122a3ce441a205292345e4d3d4a38bb3109a91e3f917dd76ae2eef9a236ca7c",
      "semantic_key": "condition:projection:compatibility",
      "source_reference": "phase4:technical_projection_display_confirmation"
    },
    {
      "fingerprint": "5e8f29a1d9629cc021bd2ccd83aa4468a851fc511a44b7ecad568d55fc4bd47e",
      "semantic_key": "condition:projection:adapters",
      "source_reference": "phase4:technical_projection_display_confirmation"
    },
    {
      "fingerprint": "b6312d47aaacfa659bd04872fbbcb938cb4df350aeeac5bd29dcced00b324a89",
      "semantic_key": "condition:projection:files",
      "source_reference": "phase4:technical_projection_display_confirmation"
    },
    {
      "fingerprint": "387c84d92eb347262b6b659159512dd9b332201e339e80a87b97e954df522a69",
      "semantic_key": "condition:projection:screenless setup suitability",
      "source_reference": "phase4:technical_projection_display_confirmation"
    },
    {
      "fingerprint": "611225d828231fc1d2df193b9e2b6261ba6eff562cf33deb3a4577cc0218ebd0",
      "semantic_key": "fact:projection_display",
      "source_reference": "phase4:technical_projection_display_confirmation"
    },
    {
      "fingerprint": "672b1a863ea87ac08dad150ee3c17339d636ca915f70b17294df2679b3424af4",
      "semantic_key": "fact:audio_playback",
      "source_reference": "phase4:technical_audio_playback_supported"
    },
    {
      "fingerprint": "1e6ee4050b7e8172dbddd436669d38b8ef634bf790b07dd08c6703662b6d9126",
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
      "fingerprint": "816840951f456995403862c1a3f84422ee194094687b8c3052dc3ce480d52c04",
      "semantic_key": "restriction:Hard constraint",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "456e120a424a2fe5c89eb23e5e9000bcf6fda29bad8a4c6194d62bb8442f2b58",
      "semantic_key": "case_fact:guest_count",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "2552d1b763e9729607a18482b08844ed4593ecf000cdd90f2d5ea54495dbbbc9",
      "semantic_key": "case_fact:event_type",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "3a1f8a2a7b03a7dea4ae51bbe7fbfe5fb55647f359d79b107c0d284f05f32c26",
      "semantic_key": "case_fact:Requested rental type code",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "6bfe62085eead7f3d038270f40f682c14073f0271832385a90b8f9295c3f041a",
      "semantic_key": "case_fact:Requested active event start",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "3766935d35a75d618fddd18c07669619c1959cc4e35acb410efb71b784f4c0d6",
      "semantic_key": "case_fact:Requested active event end",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "83d6a831ab65f3a636e9cc30c5babfdd945a745e35e6781a2d87da5313a126d0",
      "semantic_key": "internal:blocker:2180",
      "source_reference": "blocker:2180"
    },
    {
      "fingerprint": "fd753f4dec40616cf0fdd67580acaba2b67cb24efddd900a90367eb0a6eea4cc",
      "semantic_key": "internal:blocker:2181",
      "source_reference": "blocker:2181"
    },
    {
      "fingerprint": "c2fe8726d57cc00a3394a4d007e8007e3ddc61d10b4bf2c0f556c8c4c7f64d64",
      "semantic_key": "internal:availability:2026-10-29 16:00:00+00:2026-10-29 20:00:00+00",
      "source_reference": "availability:2026-10-29 16:00:00+00:2026-10-29 20:00:00+00"
    }
  ],
  "substantive_budget": 3,
  "version": "editorial_content_plan_v3"
}
```

### Exact final draft

DraftRevision 321; captured validator PASS. Exact approval/action binding: PASS.

**Subject**

```text
Product launch technical setup
```

**Body**

```text
Hi Elena,

The product launch sounds like a great use of the Studio. We have a WNC projector for slide projection, and I’ll check the practical setup for the space. Background music playback is also possible.

For the small hologram display, I’ll check whether the requested custom equipment can be installed and operated safely, then report back on what is realistic.
```

## UAT-004/2

Previous defect: Without making it a dependency.

Deterministic root cause: Generic latest-message acknowledgement lost the concrete optional preference.

Fix: Structured optional hologram delta and should_not_delay planning targets.

Result: **PASS**. Acknowledges the structured optional hologram preference and continues projection planning. No dependency wording, repeated music answer or secondary projection checklist. The practical projection check remains useful and unconfirmed.

### Final plan

```json
{
  "acknowledge": [
    {
      "authority_class": "client_request",
      "fingerprint": "d8665f4955ec8a185068e698781256468394b5986237af5c840607844782cc6d",
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
        "item": "hologram",
        "kind": "client_preference_change",
        "optional": true,
        "should_not_delay": [
          "projection planning",
          "event planning"
        ]
      }
    }
  ],
  "already_communicated": [
    {
      "authority_class": "current_governed",
      "fingerprint": "672b1a863ea87ac08dad150ee3c17339d636ca915f70b17294df2679b3424af4",
      "included_in_model_payload": false,
      "prior_turn_status": "unchanged_answer_in_prior_draft",
      "priority": 1,
      "proposition_key": "fact:audio_playback",
      "reason": "unchanged_answer_already_explained",
      "role": "ALREADY_COMMUNICATED",
      "semantic_key": "fact:audio_playback",
      "source_reference": "phase4:technical_audio_playback_supported",
      "topic": "audio_playback",
      "value": {
        "client_fact": {
          "background_music_playback": true
        }
      }
    }
  ],
  "client_visible_pending_state": [
    {
      "available_equipment": "WNC projector",
      "capability": "projection display",
      "check_required": [
        "practical projection setup"
      ],
      "status": "conditional",
      "topic": "projection_display"
    }
  ],
  "defer": [
    {
      "authority_class": "current_governed",
      "fingerprint": "d48a4e749f26bd87be6140eb859f17d122a1ad07af3a4144f1406fc448f23d20",
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
        "booking_fee": "EUR 75 excl. VAT",
        "vat": "21%"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "6376528dba101c8aad7ad55646753b38051d5cc40c99279ce62d10d08aae0388",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 50,
      "proposition_key": "guidance:c860c453d6ac37bf",
      "reason": "secondary_or_unstructured_guidance_not_needed_now",
      "role": "DEFER",
      "semantic_key": "guidance:c860c453d6ac37bf",
      "source_reference": "SERV-004",
      "topic": "external_supplier_setup",
      "value": {
        "source_text": "Supplier / client removes packaging and rental-related waste Venue-rule acknowledgement: Required before delivery"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "00fedd00a4fb4fc8f3ba78a4aedfcc6b10b3e45a53a683955b105d74d2cf8fbd",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 50,
      "proposition_key": "guidance:f3bb9a44431341d3",
      "reason": "secondary_or_unstructured_guidance_not_needed_now",
      "role": "DEFER",
      "semantic_key": "guidance:f3bb9a44431341d3",
      "source_reference": "SERV-004",
      "topic": "external_supplier_setup",
      "value": {
        "source_text": "Supplier / client removes all packaging, cable waste and equipment materials Venue-rule acknowledgement: Required before load-in"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "6122a3ce441a205292345e4d3d4a38bb3109a91e3f917dd76ae2eef9a236ca7c",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 2,
      "proposition_key": "condition:projection:compatibility",
      "reason": "secondary_condition_covered_by_practical_setup_check",
      "role": "DEFER",
      "semantic_key": "condition:projection:compatibility",
      "source_reference": "phase4:technical_projection_display_confirmation",
      "topic": "projection_detail",
      "value": {
        "check_required": "compatibility",
        "status": "check_required"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "5e8f29a1d9629cc021bd2ccd83aa4468a851fc511a44b7ecad568d55fc4bd47e",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 2,
      "proposition_key": "condition:projection:adapters",
      "reason": "secondary_condition_covered_by_practical_setup_check",
      "role": "DEFER",
      "semantic_key": "condition:projection:adapters",
      "source_reference": "phase4:technical_projection_display_confirmation",
      "topic": "projection_detail",
      "value": {
        "check_required": "adapters",
        "status": "check_required"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "b6312d47aaacfa659bd04872fbbcb938cb4df350aeeac5bd29dcced00b324a89",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 2,
      "proposition_key": "condition:projection:files",
      "reason": "secondary_condition_covered_by_practical_setup_check",
      "role": "DEFER",
      "semantic_key": "condition:projection:files",
      "source_reference": "phase4:technical_projection_display_confirmation",
      "topic": "projection_detail",
      "value": {
        "check_required": "files",
        "status": "check_required"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "387c84d92eb347262b6b659159512dd9b332201e339e80a87b97e954df522a69",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 2,
      "proposition_key": "condition:projection:screenless setup suitability",
      "reason": "secondary_condition_covered_by_practical_setup_check",
      "role": "DEFER",
      "semantic_key": "condition:projection:screenless setup suitability",
      "source_reference": "phase4:technical_projection_display_confirmation",
      "topic": "projection_detail",
      "value": {
        "check_required": "screenless setup suitability",
        "status": "check_required"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "456e120a424a2fe5c89eb23e5e9000bcf6fda29bad8a4c6194d62bb8442f2b58",
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
        "fact": "guest_count: 24"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "2552d1b763e9729607a18482b08844ed4593ecf000cdd90f2d5ea54495dbbbc9",
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
        "fact": "event_type: product launch"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "3a1f8a2a7b03a7dea4ae51bbe7fbfe5fb55647f359d79b107c0d284f05f32c26",
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
        "fact": "Requested rental type code: studio_space"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "6bfe62085eead7f3d038270f40f682c14073f0271832385a90b8f9295c3f041a",
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
        "fact": "Requested active event start: 2026-10-29 16:00:00+00"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "3766935d35a75d618fddd18c07669619c1959cc4e35acb410efb71b784f4c0d6",
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
        "fact": "Requested active event end: 2026-10-29 20:00:00+00"
      }
    }
  ],
  "do_not_repeat": [
    "audio_playback"
  ],
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
      "fingerprint": "816840951f456995403862c1a3f84422ee194094687b8c3052dc3ce480d52c04",
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
        "text": "Hard constraint: Current authority must be resolved before consequential workflow commitment."
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "fbf3624d885d7396da3f354af2bf7658a31772a9d50427b5c17bccc6ad690c76",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 50,
      "proposition_key": "internal:blocker:2180",
      "reason": "ownership_and_workflow_mechanics_stay_local",
      "role": "INTERNAL_ONLY",
      "semantic_key": "internal:blocker:2180",
      "source_reference": "blocker:2180",
      "topic": "resolution",
      "value": {
        "message": "Confirm the requested room layout against capacity requirements",
        "owner": "WNC_INTERNAL",
        "status": "REQUIRED"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "8b0e8e2f1e8bccaf183ea4bb4b77796a5a4996dc9fc0975d107b86431e001ca3",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 50,
      "proposition_key": "internal:blocker:2181",
      "reason": "ownership_and_workflow_mechanics_stay_local",
      "role": "INTERNAL_ONLY",
      "semantic_key": "internal:blocker:2181",
      "source_reference": "blocker:2181",
      "topic": "resolution",
      "value": {
        "message": "Confirm event-specific technical setup",
        "owner": "WNC_INTERNAL",
        "status": "REQUIRED"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "2ef5298ffd52f7ea4f0b419a8d7666d672493f8d7e6f6ec90eea6ee15cc27a33",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 50,
      "proposition_key": "internal:blocker:2182",
      "reason": "ownership_and_workflow_mechanics_stay_local",
      "role": "INTERNAL_ONLY",
      "semantic_key": "internal:blocker:2182",
      "source_reference": "blocker:2182",
      "topic": "resolution",
      "value": {
        "message": "Confirm event-specific technical setup",
        "owner": "WNC_INTERNAL",
        "status": "ACTION_CREATED"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "059f2612d0ecd91ea61e30f02b3f5ea76062f3a5096e8eb67202c1f48356b286",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 50,
      "proposition_key": "internal:availability:2026-10-29 16:00:00+00:2026-10-29 20:00:00+00",
      "reason": "ownership_and_workflow_mechanics_stay_local",
      "role": "INTERNAL_ONLY",
      "semantic_key": "internal:availability:2026-10-29 16:00:00+00:2026-10-29 20:00:00+00",
      "source_reference": "availability:2026-10-29 16:00:00+00:2026-10-29 20:00:00+00",
      "topic": "resolution",
      "value": {
        "message": "Confirm studio space availability for 2026-10-29 16:00:00+00 to 2026-10-29 20:00:00+00",
        "owner": "WNC_INTERNAL",
        "status": "REQUIRED"
      }
    }
  ],
  "must_ask": [],
  "must_communicate": [
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
    }
  ],
  "primary_client_need": [
    "audio_playback",
    "other_technical",
    "projection_display"
  ],
  "response_intent": "PENDING_INTERNAL_CONFIRMATION",
  "source_bindings": [
    {
      "fingerprint": "d8665f4955ec8a185068e698781256468394b5986237af5c840607844782cc6d",
      "semantic_key": "latest_client_detail",
      "source_reference": "current_client_message"
    },
    {
      "fingerprint": "d48a4e749f26bd87be6140eb859f17d122a1ad07af3a4144f1406fc448f23d20",
      "semantic_key": "commercial.current",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "6376528dba101c8aad7ad55646753b38051d5cc40c99279ce62d10d08aae0388",
      "semantic_key": "guidance:c860c453d6ac37bf",
      "source_reference": "SERV-004"
    },
    {
      "fingerprint": "00fedd00a4fb4fc8f3ba78a4aedfcc6b10b3e45a53a683955b105d74d2cf8fbd",
      "semantic_key": "guidance:f3bb9a44431341d3",
      "source_reference": "SERV-004"
    },
    {
      "fingerprint": "6122a3ce441a205292345e4d3d4a38bb3109a91e3f917dd76ae2eef9a236ca7c",
      "semantic_key": "condition:projection:compatibility",
      "source_reference": "phase4:technical_projection_display_confirmation"
    },
    {
      "fingerprint": "5e8f29a1d9629cc021bd2ccd83aa4468a851fc511a44b7ecad568d55fc4bd47e",
      "semantic_key": "condition:projection:adapters",
      "source_reference": "phase4:technical_projection_display_confirmation"
    },
    {
      "fingerprint": "b6312d47aaacfa659bd04872fbbcb938cb4df350aeeac5bd29dcced00b324a89",
      "semantic_key": "condition:projection:files",
      "source_reference": "phase4:technical_projection_display_confirmation"
    },
    {
      "fingerprint": "387c84d92eb347262b6b659159512dd9b332201e339e80a87b97e954df522a69",
      "semantic_key": "condition:projection:screenless setup suitability",
      "source_reference": "phase4:technical_projection_display_confirmation"
    },
    {
      "fingerprint": "611225d828231fc1d2df193b9e2b6261ba6eff562cf33deb3a4577cc0218ebd0",
      "semantic_key": "fact:projection_display",
      "source_reference": "phase4:technical_projection_display_confirmation"
    },
    {
      "fingerprint": "672b1a863ea87ac08dad150ee3c17339d636ca915f70b17294df2679b3424af4",
      "semantic_key": "fact:audio_playback",
      "source_reference": "phase4:technical_audio_playback_supported"
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
      "fingerprint": "816840951f456995403862c1a3f84422ee194094687b8c3052dc3ce480d52c04",
      "semantic_key": "restriction:Hard constraint",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "456e120a424a2fe5c89eb23e5e9000bcf6fda29bad8a4c6194d62bb8442f2b58",
      "semantic_key": "case_fact:guest_count",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "2552d1b763e9729607a18482b08844ed4593ecf000cdd90f2d5ea54495dbbbc9",
      "semantic_key": "case_fact:event_type",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "3a1f8a2a7b03a7dea4ae51bbe7fbfe5fb55647f359d79b107c0d284f05f32c26",
      "semantic_key": "case_fact:Requested rental type code",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "6bfe62085eead7f3d038270f40f682c14073f0271832385a90b8f9295c3f041a",
      "semantic_key": "case_fact:Requested active event start",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "3766935d35a75d618fddd18c07669619c1959cc4e35acb410efb71b784f4c0d6",
      "semantic_key": "case_fact:Requested active event end",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "fbf3624d885d7396da3f354af2bf7658a31772a9d50427b5c17bccc6ad690c76",
      "semantic_key": "internal:blocker:2180",
      "source_reference": "blocker:2180"
    },
    {
      "fingerprint": "8b0e8e2f1e8bccaf183ea4bb4b77796a5a4996dc9fc0975d107b86431e001ca3",
      "semantic_key": "internal:blocker:2181",
      "source_reference": "blocker:2181"
    },
    {
      "fingerprint": "2ef5298ffd52f7ea4f0b419a8d7666d672493f8d7e6f6ec90eea6ee15cc27a33",
      "semantic_key": "internal:blocker:2182",
      "source_reference": "blocker:2182"
    },
    {
      "fingerprint": "059f2612d0ecd91ea61e30f02b3f5ea76062f3a5096e8eb67202c1f48356b286",
      "semantic_key": "internal:availability:2026-10-29 16:00:00+00:2026-10-29 20:00:00+00",
      "source_reference": "availability:2026-10-29 16:00:00+00:2026-10-29 20:00:00+00"
    }
  ],
  "substantive_budget": 3,
  "version": "editorial_content_plan_v3"
}
```

### Exact final draft

DraftRevision 322; captured validator PASS. Exact approval/action binding: PASS.

**Subject**

```text
Projection setup
```

**Body**

```text
Hi Elena,

Understood, we can keep the hologram optional so it does not delay the wider planning. A WNC projector is available for the display, and I’ll check the practical projection setup for your event.
```

## UAT-010/1

Previous defect: Once its technical feasibility has been assessed.

Deterministic root cause: Abstract feasibility label remained in the selected action.

Fix: Concrete installation and operation safety questions, with report-back instruction.

Result: **FAIL**. The targeted abstract-feasibility wording is gone and the rig check is concrete. However, removing status from the new action value makes the existing fallback fail to recognize a pending check, so it adds an unnecessary venue-availability paragraph to this capability-focused reply. Safe but fails the strict editorial gate; no follow-on implementation is authorized.

### Final plan

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
      "requested_event_window": [
        "Requested active event start: 2026-12-10 17:30:00+00",
        "Requested active event end: 2026-12-10 23:00:00+00"
      ],
      "status": "check_required",
      "subjects": [
        "requested date and venue availability"
      ],
      "topic": "next_step"
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
      "fingerprint": "d6b468ab869d4f99c3c286f1e4707facf12637c588b0e42d796cb5c745554873",
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
        "fact": "Requested active event start: 2026-12-10 17:30:00+00"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "52d0371fb7ab1cad8667420eb74a2f7bcfdb75c46acb1b77aed5e1a6effd6619",
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
        "fact": "Requested active event end: 2026-12-10 23:00:00+00"
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
      "fingerprint": "9a3fd06771469acabf9ed163ed148776d7017f72852337f606f2ecabfb195e5a",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 50,
      "proposition_key": "internal:blocker:2211",
      "reason": "ownership_and_workflow_mechanics_stay_local",
      "role": "INTERNAL_ONLY",
      "semantic_key": "internal:blocker:2211",
      "source_reference": "blocker:2211",
      "topic": "resolution",
      "value": {
        "message": "Confirm event-specific technical setup",
        "owner": "WNC_INTERNAL",
        "status": "ACTION_CREATED"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "b031bc7232f9de59a0cc8ec8d57de13de71b6b718ec67b38e805662a1acf6018",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 50,
      "proposition_key": "internal:availability:2026-12-10 17:30:00+00:2026-12-10 23:00:00+00",
      "reason": "ownership_and_workflow_mechanics_stay_local",
      "role": "INTERNAL_ONLY",
      "semantic_key": "internal:availability:2026-12-10 17:30:00+00:2026-12-10 23:00:00+00",
      "source_reference": "availability:2026-12-10 17:30:00+00:2026-12-10 23:00:00+00",
      "topic": "resolution",
      "value": {
        "message": "Confirm entire venue availability for 2026-12-10 17:30:00+00 to 2026-12-10 23:00:00+00",
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
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "c1c7f7a20d4aa7ac64cbe949fe684e9b8ee6871735c0612d8ec52f513b0a4284",
      "included_in_model_payload": true,
      "prior_turn_status": "not_previously_communicated",
      "priority": 4,
      "proposition_key": "next_step",
      "reason": "immediate_wnc_owned_next_step",
      "role": "MUST_COMMUNICATE",
      "semantic_key": "next_step",
      "source_reference": "governed_case",
      "topic": "next_step",
      "value": {
        "action": "check",
        "requested_event_window": [
          "Requested active event start: 2026-12-10 17:30:00+00",
          "Requested active event end: 2026-12-10 23:00:00+00"
        ],
        "status": "check_required",
        "subjects": [
          "requested date and venue availability"
        ]
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
      "fingerprint": "d6b468ab869d4f99c3c286f1e4707facf12637c588b0e42d796cb5c745554873",
      "semantic_key": "case_fact:Requested active event start",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "52d0371fb7ab1cad8667420eb74a2f7bcfdb75c46acb1b77aed5e1a6effd6619",
      "semantic_key": "case_fact:Requested active event end",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "9a3fd06771469acabf9ed163ed148776d7017f72852337f606f2ecabfb195e5a",
      "semantic_key": "internal:blocker:2211",
      "source_reference": "blocker:2211"
    },
    {
      "fingerprint": "b031bc7232f9de59a0cc8ec8d57de13de71b6b718ec67b38e805662a1acf6018",
      "semantic_key": "internal:availability:2026-12-10 17:30:00+00:2026-12-10 23:00:00+00",
      "source_reference": "availability:2026-12-10 17:30:00+00:2026-12-10 23:00:00+00"
    },
    {
      "fingerprint": "c1c7f7a20d4aa7ac64cbe949fe684e9b8ee6871735c0612d8ec52f513b0a4284",
      "semantic_key": "next_step",
      "source_reference": "governed_case"
    }
  ],
  "substantive_budget": 3,
  "version": "editorial_content_plan_v3"
}
```

### Exact final draft

DraftRevision 331; captured validator PASS. Exact approval/action binding: PASS.

**Subject**

```text
Investor dinner aerial rig
```

**Body**

```text
Hi David,

The suspended aerial performance could be a striking element for the investor dinner. I’ll check whether a custom rig can be installed and operated safely at the venue.

I’ll also check venue availability for your requested date and times, then report back on both points.
```

## UAT-011/1

Previous defect: Correct projector availability triggered the microphone known-no validator.

Deterministic root cause: Positive capability words were scanned globally across topics.

Fix: Clause/topic-scoped known-no validation with maintained capability aliases.

Result: **PASS**. Persists a valid compound reply covering kitchen suitability, projector setup, external microphones and one immediate access constraint. No false known-no rejection, route claim, actual arrival authorization or secondary supplier checklist. The longer reply is justified by the compound request.

### Final plan

```json
{
  "acknowledge": [
    {
      "authority_class": "client_request",
      "fingerprint": "6c83b314a98ced5e282b35b04d84b89f7bd231f7e644f5e8b2391b34df1021a1",
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
        "about": "panel discussion",
        "kind": "new_enquiry"
      }
    }
  ],
  "already_communicated": [],
  "client_visible_pending_state": [
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
      "action": "check",
      "status": "check_required",
      "subjects": [
        "supplier arrival timing",
        "supplier setup access"
      ],
      "topic": "next_step"
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
      "fingerprint": "feb5ab7f9af3e5bf7c3dd68e36294b0925bc52242b9bbf8c907ce1b49c314ff9",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 50,
      "proposition_key": "guidance:74b98767a0208fcb",
      "reason": "secondary_or_unstructured_guidance_not_needed_now",
      "role": "DEFER",
      "semantic_key": "guidance:74b98767a0208fcb",
      "source_reference": "SERV-003",
      "topic": "catering_kitchen",
      "value": {
        "source_text": "Client and caterer must work within WNC kitchen and delivery limitations. Ready-made or easy-to-assemble food works best. External caterer / client is responsible for cleaning its working area and leaving the venue as found. Large-scale events may require professional cleaning."
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "6376528dba101c8aad7ad55646753b38051d5cc40c99279ce62d10d08aae0388",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 50,
      "proposition_key": "guidance:c860c453d6ac37bf",
      "reason": "secondary_or_unstructured_guidance_not_needed_now",
      "role": "DEFER",
      "semantic_key": "guidance:c860c453d6ac37bf",
      "source_reference": "SERV-004",
      "topic": "external_supplier_setup",
      "value": {
        "source_text": "Supplier / client removes packaging and rental-related waste Venue-rule acknowledgement: Required before delivery"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "00fedd00a4fb4fc8f3ba78a4aedfcc6b10b3e45a53a683955b105d74d2cf8fbd",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 50,
      "proposition_key": "guidance:f3bb9a44431341d3",
      "reason": "secondary_or_unstructured_guidance_not_needed_now",
      "role": "DEFER",
      "semantic_key": "guidance:f3bb9a44431341d3",
      "source_reference": "SERV-004",
      "topic": "external_supplier_setup",
      "value": {
        "source_text": "Supplier / client removes all packaging, cable waste and equipment materials Venue-rule acknowledgement: Required before load-in"
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
      "fingerprint": "8335d1f89a919a1ec7e50b783771222caccd9a885ae3279efa0d7c08aa683108",
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
        "requested_guests": 32,
        "scope": "entire venue",
        "status": "within_limits"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "6122a3ce441a205292345e4d3d4a38bb3109a91e3f917dd76ae2eef9a236ca7c",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 2,
      "proposition_key": "condition:projection:compatibility",
      "reason": "secondary_condition_covered_by_practical_setup_check",
      "role": "DEFER",
      "semantic_key": "condition:projection:compatibility",
      "source_reference": "phase4:technical_projection_display_confirmation",
      "topic": "projection_detail",
      "value": {
        "check_required": "compatibility",
        "status": "check_required"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "5e8f29a1d9629cc021bd2ccd83aa4468a851fc511a44b7ecad568d55fc4bd47e",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 2,
      "proposition_key": "condition:projection:adapters",
      "reason": "secondary_condition_covered_by_practical_setup_check",
      "role": "DEFER",
      "semantic_key": "condition:projection:adapters",
      "source_reference": "phase4:technical_projection_display_confirmation",
      "topic": "projection_detail",
      "value": {
        "check_required": "adapters",
        "status": "check_required"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "b6312d47aaacfa659bd04872fbbcb938cb4df350aeeac5bd29dcced00b324a89",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 2,
      "proposition_key": "condition:projection:files",
      "reason": "secondary_condition_covered_by_practical_setup_check",
      "role": "DEFER",
      "semantic_key": "condition:projection:files",
      "source_reference": "phase4:technical_projection_display_confirmation",
      "topic": "projection_detail",
      "value": {
        "check_required": "files",
        "status": "check_required"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "387c84d92eb347262b6b659159512dd9b332201e339e80a87b97e954df522a69",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 2,
      "proposition_key": "condition:projection:screenless setup suitability",
      "reason": "secondary_condition_covered_by_practical_setup_check",
      "role": "DEFER",
      "semantic_key": "condition:projection:screenless setup suitability",
      "source_reference": "phase4:technical_projection_display_confirmation",
      "topic": "projection_detail",
      "value": {
        "check_required": "screenless setup suitability",
        "status": "check_required"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "24d28ccab32948952380e3c189c758fec8057239ed33154b26604337f2de35e8",
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
        "fact": "guest_count: 32"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "7c3eedc84636c3f9be34286910bdf4a0c5627584eea41dcc73b7cf865b7417cc",
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
        "fact": "event_type: panel discussion"
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
      "fingerprint": "3ed4e971a0609c7c8bd316c957b931d5d8f9490fcbf2a5a0899fa6cf7d913a69",
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
        "fact": "Requested active event start: 2026-12-15 14:00:00+00"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "af27304825301255e528224cee0ce5a080cfa671ffca5d7e537b4bc428a2cff0",
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
        "fact": "Requested active event end: 2026-12-15 19:00:00+00"
      }
    }
  ],
  "do_not_repeat": [],
  "editorial_rationale": "compound_material_answers_and_client_questions",
  "helpful_now": [],
  "internal_only": [
    {
      "authority_class": "current_governed",
      "fingerprint": "580e9c78519975eff5f412f177a9d642e378e5f055057fc96f686bbf272aec88",
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
        "text": "Hard constraint: Current governed policy does not support the requested commitment as stated."
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "96b8ca3dccd149c54355c2df6ac5d6136844d1743f48ad61846649bf905dfda6",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 50,
      "proposition_key": "internal:blocker:2216",
      "reason": "ownership_and_workflow_mechanics_stay_local",
      "role": "INTERNAL_ONLY",
      "semantic_key": "internal:blocker:2216",
      "source_reference": "blocker:2216",
      "topic": "resolution",
      "value": {
        "message": "Confirm event-specific technical setup",
        "owner": "WNC_INTERNAL",
        "status": "ACTION_CREATED"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "63a360e83db961df6ad0ed37ab49bfb49cc83d7a68afdfe1eb6af0e0ce520216",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 50,
      "proposition_key": "internal:logistics:supplier_arrival:2026-12-15 14:00:00+00:2026-12-15 19:00:00+00",
      "reason": "ownership_and_workflow_mechanics_stay_local",
      "role": "INTERNAL_ONLY",
      "semantic_key": "internal:logistics:supplier_arrival:2026-12-15 14:00:00+00:2026-12-15 19:00:00+00",
      "source_reference": "logistics:supplier_arrival:2026-12-15 14:00:00+00:2026-12-15 19:00:00+00",
      "topic": "resolution",
      "value": {
        "message": "Confirm supplier arrival and setup windows",
        "owner": "WNC_INTERNAL",
        "status": "ACTION_CREATED"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "09770a6d82e523071e05d47f5a355f7f3db0a192ebf0162ef017e80190b748ba",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 50,
      "proposition_key": "internal:availability:2026-12-15 14:00:00+00:2026-12-15 19:00:00+00",
      "reason": "ownership_and_workflow_mechanics_stay_local",
      "role": "INTERNAL_ONLY",
      "semantic_key": "internal:availability:2026-12-15 14:00:00+00:2026-12-15 19:00:00+00",
      "source_reference": "availability:2026-12-15 14:00:00+00:2026-12-15 19:00:00+00",
      "topic": "resolution",
      "value": {
        "message": "Confirm entire venue availability for 2026-12-15 14:00:00+00 to 2026-12-15 19:00:00+00",
        "owner": "WNC_INTERNAL",
        "status": "ACTION_CREATED"
      }
    }
  ],
  "must_ask": [],
  "must_communicate": [
    {
      "authority_class": "current_governed",
      "fingerprint": "8ba654ac396fc19822cecd67c06d7a927fd97238ba66a337daa3b0d9c888d61a",
      "included_in_model_payload": true,
      "prior_turn_status": "not_previously_communicated",
      "priority": 1,
      "proposition_key": "fact:catering_kitchen",
      "reason": "current_catering_suitability_question",
      "role": "MUST_COMMUNICATE",
      "semantic_key": "fact:catering_kitchen",
      "source_reference": "SERV-003",
      "topic": "catering_kitchen",
      "value": {
        "limitation": "not large-scale food production",
        "suitable_for": [
          "ready-made food",
          "warming",
          "plating",
          "simple assembly"
        ]
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "c44c4347be161b1f3a56fc6ea168b9b0dfb1dffe8f1dd36b6dcf4af26ca0f9c8",
      "included_in_model_payload": true,
      "prior_turn_status": "not_previously_communicated",
      "priority": 5,
      "proposition_key": "fact:supplier_access",
      "reason": "one_immediate_access_constraint",
      "role": "MUST_COMMUNICATE",
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
      "fingerprint": "09129378b9d949ef75a76b88fb1e5d7d3d6fa5f3166dd83ac83d01657a8a38d4",
      "included_in_model_payload": true,
      "prior_turn_status": "not_previously_communicated",
      "priority": 0,
      "proposition_key": "fact:microphones",
      "reason": "material_known_restriction",
      "role": "MUST_COMMUNICATE",
      "semantic_key": "fact:microphones",
      "source_reference": "phase4:technical_microphones_restriction",
      "topic": "microphones",
      "value": {
        "capability": "microphones",
        "status": "not_supported",
        "supplier_requirement": "external supplier"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "b320d8baf1f3da0c554feb37e3a541018738575bda80c7239eccebd8ec4ff0fa",
      "included_in_model_payload": true,
      "prior_turn_status": "not_previously_communicated",
      "priority": 4,
      "proposition_key": "next_step",
      "reason": "immediate_wnc_owned_next_step",
      "role": "MUST_COMMUNICATE",
      "semantic_key": "next_step",
      "source_reference": "governed_case",
      "topic": "next_step",
      "value": {
        "action": "check",
        "status": "check_required",
        "subjects": [
          "supplier arrival timing",
          "supplier setup access"
        ]
      }
    }
  ],
  "primary_client_need": [
    "catering_kitchen",
    "microphones",
    "projection_display",
    "supplier_access"
  ],
  "response_intent": "COMMUNICATE_RESTRICTION",
  "source_bindings": [
    {
      "fingerprint": "6c83b314a98ced5e282b35b04d84b89f7bd231f7e644f5e8b2391b34df1021a1",
      "semantic_key": "latest_client_detail",
      "source_reference": "current_client_message"
    },
    {
      "fingerprint": "24727a7a2ecf805c2767687ac37de1f6072034f1bf7a4d1c7be070e3f621b755",
      "semantic_key": "commercial.current",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "8ba654ac396fc19822cecd67c06d7a927fd97238ba66a337daa3b0d9c888d61a",
      "semantic_key": "fact:catering_kitchen",
      "source_reference": "SERV-003"
    },
    {
      "fingerprint": "feb5ab7f9af3e5bf7c3dd68e36294b0925bc52242b9bbf8c907ce1b49c314ff9",
      "semantic_key": "guidance:74b98767a0208fcb",
      "source_reference": "SERV-003"
    },
    {
      "fingerprint": "6376528dba101c8aad7ad55646753b38051d5cc40c99279ce62d10d08aae0388",
      "semantic_key": "guidance:c860c453d6ac37bf",
      "source_reference": "SERV-004"
    },
    {
      "fingerprint": "00fedd00a4fb4fc8f3ba78a4aedfcc6b10b3e45a53a683955b105d74d2cf8fbd",
      "semantic_key": "guidance:f3bb9a44431341d3",
      "source_reference": "SERV-004"
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
      "fingerprint": "8335d1f89a919a1ec7e50b783771222caccd9a885ae3279efa0d7c08aa683108",
      "semantic_key": "fact:capacity",
      "source_reference": "phase4:capacity_entire_venue_within_capacity"
    },
    {
      "fingerprint": "6122a3ce441a205292345e4d3d4a38bb3109a91e3f917dd76ae2eef9a236ca7c",
      "semantic_key": "condition:projection:compatibility",
      "source_reference": "phase4:technical_projection_display_confirmation"
    },
    {
      "fingerprint": "5e8f29a1d9629cc021bd2ccd83aa4468a851fc511a44b7ecad568d55fc4bd47e",
      "semantic_key": "condition:projection:adapters",
      "source_reference": "phase4:technical_projection_display_confirmation"
    },
    {
      "fingerprint": "b6312d47aaacfa659bd04872fbbcb938cb4df350aeeac5bd29dcced00b324a89",
      "semantic_key": "condition:projection:files",
      "source_reference": "phase4:technical_projection_display_confirmation"
    },
    {
      "fingerprint": "387c84d92eb347262b6b659159512dd9b332201e339e80a87b97e954df522a69",
      "semantic_key": "condition:projection:screenless setup suitability",
      "source_reference": "phase4:technical_projection_display_confirmation"
    },
    {
      "fingerprint": "611225d828231fc1d2df193b9e2b6261ba6eff562cf33deb3a4577cc0218ebd0",
      "semantic_key": "fact:projection_display",
      "source_reference": "phase4:technical_projection_display_confirmation"
    },
    {
      "fingerprint": "09129378b9d949ef75a76b88fb1e5d7d3d6fa5f3166dd83ac83d01657a8a38d4",
      "semantic_key": "fact:microphones",
      "source_reference": "phase4:technical_microphones_restriction"
    },
    {
      "fingerprint": "580e9c78519975eff5f412f177a9d642e378e5f055057fc96f686bbf272aec88",
      "semantic_key": "restriction:Hard constraint",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "24d28ccab32948952380e3c189c758fec8057239ed33154b26604337f2de35e8",
      "semantic_key": "case_fact:guest_count",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "7c3eedc84636c3f9be34286910bdf4a0c5627584eea41dcc73b7cf865b7417cc",
      "semantic_key": "case_fact:event_type",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "d370e3ce4887100fe10395e7cd3ddb34f6987ace8bd19a9c5e72161845a1b0fb",
      "semantic_key": "case_fact:Requested rental type code",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "3ed4e971a0609c7c8bd316c957b931d5d8f9490fcbf2a5a0899fa6cf7d913a69",
      "semantic_key": "case_fact:Requested active event start",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "af27304825301255e528224cee0ce5a080cfa671ffca5d7e537b4bc428a2cff0",
      "semantic_key": "case_fact:Requested active event end",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "96b8ca3dccd149c54355c2df6ac5d6136844d1743f48ad61846649bf905dfda6",
      "semantic_key": "internal:blocker:2216",
      "source_reference": "blocker:2216"
    },
    {
      "fingerprint": "63a360e83db961df6ad0ed37ab49bfb49cc83d7a68afdfe1eb6af0e0ce520216",
      "semantic_key": "internal:logistics:supplier_arrival:2026-12-15 14:00:00+00:2026-12-15 19:00:00+00",
      "source_reference": "logistics:supplier_arrival:2026-12-15 14:00:00+00:2026-12-15 19:00:00+00"
    },
    {
      "fingerprint": "09770a6d82e523071e05d47f5a355f7f3db0a192ebf0162ef017e80190b748ba",
      "semantic_key": "internal:availability:2026-12-15 14:00:00+00:2026-12-15 19:00:00+00",
      "source_reference": "availability:2026-12-15 14:00:00+00:2026-12-15 19:00:00+00"
    },
    {
      "fingerprint": "b320d8baf1f3da0c554feb37e3a541018738575bda80c7239eccebd8ec4ff0fa",
      "semantic_key": "next_step",
      "source_reference": "governed_case"
    }
  ],
  "substantive_budget": 5,
  "version": "editorial_content_plan_v3"
}
```

### Exact final draft

DraftRevision 332; captured validator PASS. Exact approval/action binding: PASS.

**Subject**

```text
Panel discussion practical requirements
```

**Body**

```text
Hi Nora,

The panel discussion setup sounds clear, including the florist, external caterer and AV needs. The catering kitchen is suitable for ready-made food, warming, plating and simple assembly, but not large-scale food production.

We have a WNC projector, and I’ll check the practical projection setup for the panel. Microphones are not provided, so those would need to come from an external supplier.

Supplier deliveries, unloading and setup must take place within the confirmed rental period unless agreed otherwise in writing. I’ll check the proposed supplier arrival timing and setup access.
```

## UAT-011/2

Previous defect: No accepted first-turn realization existed because first-turn validation failed.

Deterministic root cause: The prior rejection prevented continuity evidence; logistics questions could also reopen catering advice.

Fix: Fresh accepted turn-one evidence, conservative projection realization witness and logistics-specific catering repeat selection.

Result: **PASS**. Fresh-case accepted first-turn evidence suppresses kitchen, microphones and access policy; projection is deferred because it is not reopened. Only handover, arrival timing and loading route checks remain. No unrequested technical/catering repetition or invented arrival window.

### Final plan

```json
{
  "acknowledge": [
    {
      "authority_class": "client_request",
      "fingerprint": "984c78f876a4fcf93cdb2ccbd06f73779b4769f6436d3376a8a656104196b1ea",
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
        "focus": "the change or clarification in the latest message",
        "kind": "new_client_detail"
      }
    }
  ],
  "already_communicated": [
    {
      "authority_class": "current_governed",
      "fingerprint": "8ba654ac396fc19822cecd67c06d7a927fd97238ba66a337daa3b0d9c888d61a",
      "included_in_model_payload": false,
      "prior_turn_status": "unchanged_answer_in_prior_draft",
      "priority": 50,
      "proposition_key": "fact:catering_kitchen",
      "reason": "unchanged_answer_already_explained",
      "role": "ALREADY_COMMUNICATED",
      "semantic_key": "fact:catering_kitchen",
      "source_reference": "SERV-003",
      "topic": "catering_kitchen",
      "value": {
        "limitation": "not large-scale food production",
        "suitable_for": [
          "ready-made food",
          "warming",
          "plating",
          "simple assembly"
        ]
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "c44c4347be161b1f3a56fc6ea168b9b0dfb1dffe8f1dd36b6dcf4af26ca0f9c8",
      "included_in_model_payload": false,
      "prior_turn_status": "unchanged_answer_in_prior_draft",
      "priority": 5,
      "proposition_key": "fact:supplier_access",
      "reason": "unchanged_answer_already_explained",
      "role": "ALREADY_COMMUNICATED",
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
      "fingerprint": "09129378b9d949ef75a76b88fb1e5d7d3d6fa5f3166dd83ac83d01657a8a38d4",
      "included_in_model_payload": false,
      "prior_turn_status": "unchanged_answer_in_prior_draft",
      "priority": 0,
      "proposition_key": "fact:microphones",
      "reason": "unchanged_answer_already_explained",
      "role": "ALREADY_COMMUNICATED",
      "semantic_key": "fact:microphones",
      "source_reference": "phase4:technical_microphones_restriction",
      "topic": "microphones",
      "value": {
        "capability": "microphones",
        "status": "not_supported",
        "supplier_requirement": "external supplier"
      }
    }
  ],
  "client_visible_pending_state": [
    {
      "action": "check",
      "status": "check_required",
      "subjects": [
        "venue handover",
        "supplier arrival timing",
        "loading route"
      ],
      "topic": "next_step"
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
      "fingerprint": "feb5ab7f9af3e5bf7c3dd68e36294b0925bc52242b9bbf8c907ce1b49c314ff9",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 50,
      "proposition_key": "guidance:74b98767a0208fcb",
      "reason": "secondary_or_unstructured_guidance_not_needed_now",
      "role": "DEFER",
      "semantic_key": "guidance:74b98767a0208fcb",
      "source_reference": "SERV-003",
      "topic": "catering_kitchen",
      "value": {
        "source_text": "Client and caterer must work within WNC kitchen and delivery limitations. Ready-made or easy-to-assemble food works best. External caterer / client is responsible for cleaning its working area and leaving the venue as found. Large-scale events may require professional cleaning."
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "6376528dba101c8aad7ad55646753b38051d5cc40c99279ce62d10d08aae0388",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 50,
      "proposition_key": "guidance:c860c453d6ac37bf",
      "reason": "secondary_or_unstructured_guidance_not_needed_now",
      "role": "DEFER",
      "semantic_key": "guidance:c860c453d6ac37bf",
      "source_reference": "SERV-004",
      "topic": "external_supplier_setup",
      "value": {
        "source_text": "Supplier / client removes packaging and rental-related waste Venue-rule acknowledgement: Required before delivery"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "00fedd00a4fb4fc8f3ba78a4aedfcc6b10b3e45a53a683955b105d74d2cf8fbd",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 50,
      "proposition_key": "guidance:f3bb9a44431341d3",
      "reason": "secondary_or_unstructured_guidance_not_needed_now",
      "role": "DEFER",
      "semantic_key": "guidance:f3bb9a44431341d3",
      "source_reference": "SERV-004",
      "topic": "external_supplier_setup",
      "value": {
        "source_text": "Supplier / client removes all packaging, cable waste and equipment materials Venue-rule acknowledgement: Required before load-in"
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
      "fingerprint": "8335d1f89a919a1ec7e50b783771222caccd9a885ae3279efa0d7c08aa683108",
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
        "requested_guests": 32,
        "scope": "entire venue",
        "status": "within_limits"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "6122a3ce441a205292345e4d3d4a38bb3109a91e3f917dd76ae2eef9a236ca7c",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 2,
      "proposition_key": "condition:projection:compatibility",
      "reason": "secondary_condition_covered_by_practical_setup_check",
      "role": "DEFER",
      "semantic_key": "condition:projection:compatibility",
      "source_reference": "phase4:technical_projection_display_confirmation",
      "topic": "projection_detail",
      "value": {
        "check_required": "compatibility",
        "status": "check_required"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "5e8f29a1d9629cc021bd2ccd83aa4468a851fc511a44b7ecad568d55fc4bd47e",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 2,
      "proposition_key": "condition:projection:adapters",
      "reason": "secondary_condition_covered_by_practical_setup_check",
      "role": "DEFER",
      "semantic_key": "condition:projection:adapters",
      "source_reference": "phase4:technical_projection_display_confirmation",
      "topic": "projection_detail",
      "value": {
        "check_required": "adapters",
        "status": "check_required"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "b6312d47aaacfa659bd04872fbbcb938cb4df350aeeac5bd29dcced00b324a89",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 2,
      "proposition_key": "condition:projection:files",
      "reason": "secondary_condition_covered_by_practical_setup_check",
      "role": "DEFER",
      "semantic_key": "condition:projection:files",
      "source_reference": "phase4:technical_projection_display_confirmation",
      "topic": "projection_detail",
      "value": {
        "check_required": "files",
        "status": "check_required"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "387c84d92eb347262b6b659159512dd9b332201e339e80a87b97e954df522a69",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 2,
      "proposition_key": "condition:projection:screenless setup suitability",
      "reason": "secondary_condition_covered_by_practical_setup_check",
      "role": "DEFER",
      "semantic_key": "condition:projection:screenless setup suitability",
      "source_reference": "phase4:technical_projection_display_confirmation",
      "topic": "projection_detail",
      "value": {
        "check_required": "screenless setup suitability",
        "status": "check_required"
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
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "24d28ccab32948952380e3c189c758fec8057239ed33154b26604337f2de35e8",
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
        "fact": "guest_count: 32"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "7c3eedc84636c3f9be34286910bdf4a0c5627584eea41dcc73b7cf865b7417cc",
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
        "fact": "event_type: panel discussion"
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
      "fingerprint": "3ed4e971a0609c7c8bd316c957b931d5d8f9490fcbf2a5a0899fa6cf7d913a69",
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
        "fact": "Requested active event start: 2026-12-15 14:00:00+00"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "af27304825301255e528224cee0ce5a080cfa671ffca5d7e537b4bc428a2cff0",
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
        "fact": "Requested active event end: 2026-12-15 19:00:00+00"
      }
    }
  ],
  "do_not_repeat": [
    "catering_kitchen",
    "supplier_access",
    "microphones"
  ],
  "editorial_rationale": "minimal_substantive_items_optional_guidance_ranked_last",
  "helpful_now": [],
  "internal_only": [
    {
      "authority_class": "current_governed",
      "fingerprint": "580e9c78519975eff5f412f177a9d642e378e5f055057fc96f686bbf272aec88",
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
        "text": "Hard constraint: Current governed policy does not support the requested commitment as stated."
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "ecfd2a4046459c456d04d74745485ad43fea514aee2adb2e75fe93a1491eb01f",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 50,
      "proposition_key": "internal:blocker:2216",
      "reason": "ownership_and_workflow_mechanics_stay_local",
      "role": "INTERNAL_ONLY",
      "semantic_key": "internal:blocker:2216",
      "source_reference": "blocker:2216",
      "topic": "resolution",
      "value": {
        "message": "Confirm event-specific technical setup",
        "owner": "WNC_INTERNAL",
        "status": "REQUIRED"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "0d66976c3b73ae4e8a08c82a95b5a95a435c771a2242a0b61b77bb2e9a6d3ea5",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 50,
      "proposition_key": "internal:logistics:loading_route:2026-12-15 14:00:00+00:2026-12-15 19:00:00+00",
      "reason": "ownership_and_workflow_mechanics_stay_local",
      "role": "INTERNAL_ONLY",
      "semantic_key": "internal:logistics:loading_route:2026-12-15 14:00:00+00:2026-12-15 19:00:00+00",
      "source_reference": "logistics:loading_route:2026-12-15 14:00:00+00:2026-12-15 19:00:00+00",
      "topic": "resolution",
      "value": {
        "message": "Confirm the supplier loading route",
        "owner": "WNC_INTERNAL",
        "status": "ACTION_CREATED"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "ad9bddf446bce99303f00b1b9151fdb2874401e25e9605811d2189211e1f62e4",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 50,
      "proposition_key": "internal:logistics:venue_handover:2026-12-15 14:00:00+00:2026-12-15 19:00:00+00",
      "reason": "ownership_and_workflow_mechanics_stay_local",
      "role": "INTERNAL_ONLY",
      "semantic_key": "internal:logistics:venue_handover:2026-12-15 14:00:00+00:2026-12-15 19:00:00+00",
      "source_reference": "logistics:venue_handover:2026-12-15 14:00:00+00:2026-12-15 19:00:00+00",
      "topic": "resolution",
      "value": {
        "message": "Confirm venue handover requirements",
        "owner": "WNC_INTERNAL",
        "status": "ACTION_CREATED"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "219eb72ec3185c74c3902eba2ba4d19e1cc630e1fd6157f4b3893d526549df4d",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 50,
      "proposition_key": "internal:logistics:supplier_arrival:2026-12-15 14:00:00+00:2026-12-15 19:00:00+00",
      "reason": "ownership_and_workflow_mechanics_stay_local",
      "role": "INTERNAL_ONLY",
      "semantic_key": "internal:logistics:supplier_arrival:2026-12-15 14:00:00+00:2026-12-15 19:00:00+00",
      "source_reference": "logistics:supplier_arrival:2026-12-15 14:00:00+00:2026-12-15 19:00:00+00",
      "topic": "resolution",
      "value": {
        "message": "Confirm supplier arrival and setup windows",
        "owner": "WNC_INTERNAL",
        "status": "REQUIRED"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "a1641dc077868106bd60cc675d91929defa52768dbbcfbc6eafab5a6cb959304",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 50,
      "proposition_key": "internal:availability:2026-12-15 14:00:00+00:2026-12-15 19:00:00+00",
      "reason": "ownership_and_workflow_mechanics_stay_local",
      "role": "INTERNAL_ONLY",
      "semantic_key": "internal:availability:2026-12-15 14:00:00+00:2026-12-15 19:00:00+00",
      "source_reference": "availability:2026-12-15 14:00:00+00:2026-12-15 19:00:00+00",
      "topic": "resolution",
      "value": {
        "message": "Confirm entire venue availability for 2026-12-15 14:00:00+00 to 2026-12-15 19:00:00+00",
        "owner": "WNC_INTERNAL",
        "status": "REQUIRED"
      }
    }
  ],
  "must_ask": [],
  "must_communicate": [
    {
      "authority_class": "current_governed",
      "fingerprint": "edff3d559b1e85048a79b7be96b271ad732bc96a40ed9983de29a4f03481918a",
      "included_in_model_payload": true,
      "prior_turn_status": "not_previously_communicated",
      "priority": 4,
      "proposition_key": "next_step",
      "reason": "immediate_wnc_owned_next_step",
      "role": "MUST_COMMUNICATE",
      "semantic_key": "next_step",
      "source_reference": "governed_case",
      "topic": "next_step",
      "value": {
        "action": "check",
        "status": "check_required",
        "subjects": [
          "venue handover",
          "supplier arrival timing",
          "loading route"
        ]
      }
    }
  ],
  "primary_client_need": [
    "catering_kitchen",
    "supplier_access"
  ],
  "response_intent": "COMMUNICATE_RESTRICTION",
  "source_bindings": [
    {
      "fingerprint": "984c78f876a4fcf93cdb2ccbd06f73779b4769f6436d3376a8a656104196b1ea",
      "semantic_key": "latest_client_detail",
      "source_reference": "current_client_message"
    },
    {
      "fingerprint": "24727a7a2ecf805c2767687ac37de1f6072034f1bf7a4d1c7be070e3f621b755",
      "semantic_key": "commercial.current",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "8ba654ac396fc19822cecd67c06d7a927fd97238ba66a337daa3b0d9c888d61a",
      "semantic_key": "fact:catering_kitchen",
      "source_reference": "SERV-003"
    },
    {
      "fingerprint": "feb5ab7f9af3e5bf7c3dd68e36294b0925bc52242b9bbf8c907ce1b49c314ff9",
      "semantic_key": "guidance:74b98767a0208fcb",
      "source_reference": "SERV-003"
    },
    {
      "fingerprint": "6376528dba101c8aad7ad55646753b38051d5cc40c99279ce62d10d08aae0388",
      "semantic_key": "guidance:c860c453d6ac37bf",
      "source_reference": "SERV-004"
    },
    {
      "fingerprint": "00fedd00a4fb4fc8f3ba78a4aedfcc6b10b3e45a53a683955b105d74d2cf8fbd",
      "semantic_key": "guidance:f3bb9a44431341d3",
      "source_reference": "SERV-004"
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
      "fingerprint": "8335d1f89a919a1ec7e50b783771222caccd9a885ae3279efa0d7c08aa683108",
      "semantic_key": "fact:capacity",
      "source_reference": "phase4:capacity_entire_venue_within_capacity"
    },
    {
      "fingerprint": "6122a3ce441a205292345e4d3d4a38bb3109a91e3f917dd76ae2eef9a236ca7c",
      "semantic_key": "condition:projection:compatibility",
      "source_reference": "phase4:technical_projection_display_confirmation"
    },
    {
      "fingerprint": "5e8f29a1d9629cc021bd2ccd83aa4468a851fc511a44b7ecad568d55fc4bd47e",
      "semantic_key": "condition:projection:adapters",
      "source_reference": "phase4:technical_projection_display_confirmation"
    },
    {
      "fingerprint": "b6312d47aaacfa659bd04872fbbcb938cb4df350aeeac5bd29dcced00b324a89",
      "semantic_key": "condition:projection:files",
      "source_reference": "phase4:technical_projection_display_confirmation"
    },
    {
      "fingerprint": "387c84d92eb347262b6b659159512dd9b332201e339e80a87b97e954df522a69",
      "semantic_key": "condition:projection:screenless setup suitability",
      "source_reference": "phase4:technical_projection_display_confirmation"
    },
    {
      "fingerprint": "611225d828231fc1d2df193b9e2b6261ba6eff562cf33deb3a4577cc0218ebd0",
      "semantic_key": "fact:projection_display",
      "source_reference": "phase4:technical_projection_display_confirmation"
    },
    {
      "fingerprint": "09129378b9d949ef75a76b88fb1e5d7d3d6fa5f3166dd83ac83d01657a8a38d4",
      "semantic_key": "fact:microphones",
      "source_reference": "phase4:technical_microphones_restriction"
    },
    {
      "fingerprint": "580e9c78519975eff5f412f177a9d642e378e5f055057fc96f686bbf272aec88",
      "semantic_key": "restriction:Hard constraint",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "24d28ccab32948952380e3c189c758fec8057239ed33154b26604337f2de35e8",
      "semantic_key": "case_fact:guest_count",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "7c3eedc84636c3f9be34286910bdf4a0c5627584eea41dcc73b7cf865b7417cc",
      "semantic_key": "case_fact:event_type",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "d370e3ce4887100fe10395e7cd3ddb34f6987ace8bd19a9c5e72161845a1b0fb",
      "semantic_key": "case_fact:Requested rental type code",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "3ed4e971a0609c7c8bd316c957b931d5d8f9490fcbf2a5a0899fa6cf7d913a69",
      "semantic_key": "case_fact:Requested active event start",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "af27304825301255e528224cee0ce5a080cfa671ffca5d7e537b4bc428a2cff0",
      "semantic_key": "case_fact:Requested active event end",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "ecfd2a4046459c456d04d74745485ad43fea514aee2adb2e75fe93a1491eb01f",
      "semantic_key": "internal:blocker:2216",
      "source_reference": "blocker:2216"
    },
    {
      "fingerprint": "0d66976c3b73ae4e8a08c82a95b5a95a435c771a2242a0b61b77bb2e9a6d3ea5",
      "semantic_key": "internal:logistics:loading_route:2026-12-15 14:00:00+00:2026-12-15 19:00:00+00",
      "source_reference": "logistics:loading_route:2026-12-15 14:00:00+00:2026-12-15 19:00:00+00"
    },
    {
      "fingerprint": "ad9bddf446bce99303f00b1b9151fdb2874401e25e9605811d2189211e1f62e4",
      "semantic_key": "internal:logistics:venue_handover:2026-12-15 14:00:00+00:2026-12-15 19:00:00+00",
      "source_reference": "logistics:venue_handover:2026-12-15 14:00:00+00:2026-12-15 19:00:00+00"
    },
    {
      "fingerprint": "219eb72ec3185c74c3902eba2ba4d19e1cc630e1fd6157f4b3893d526549df4d",
      "semantic_key": "internal:logistics:supplier_arrival:2026-12-15 14:00:00+00:2026-12-15 19:00:00+00",
      "source_reference": "logistics:supplier_arrival:2026-12-15 14:00:00+00:2026-12-15 19:00:00+00"
    },
    {
      "fingerprint": "a1641dc077868106bd60cc675d91929defa52768dbbcfbc6eafab5a6cb959304",
      "semantic_key": "internal:availability:2026-12-15 14:00:00+00:2026-12-15 19:00:00+00",
      "source_reference": "availability:2026-12-15 14:00:00+00:2026-12-15 19:00:00+00"
    },
    {
      "fingerprint": "edff3d559b1e85048a79b7be96b271ad732bc96a40ed9983de29a4f03481918a",
      "semantic_key": "next_step",
      "source_reference": "governed_case"
    }
  ],
  "substantive_budget": 3,
  "version": "editorial_content_plan_v3"
}
```

### Exact final draft

DraftRevision 333; captured validator PASS. Exact approval/action binding: PASS.

**Subject**

```text
Supplier logistics
```

**Body**

```text
Hi Nora,

Understood that the florist will wait until the venue handover requirements are clear, and that the caterer needs practical arrival details.

I’ll check the venue handover requirements, supplier arrival timing and loading route, then come back to you.
```

## UAT-012/1

Previous defect: Already-acknowledged DJ restriction was repeated.

Deterministic root cause: Raw dj substring matched inside adjust, reopening the restriction.

Fix: Normalized token/phrase aliases shared by the finite topic adapter.

Result: **FAIL**. The acknowledged DJ restriction is correctly absent. Required timing/headcount questions, kitchen constraint, projection check and commercial/facilitator next steps remain. However, the selected known audio fact becomes a future setup check instead of a clear capability answer. The global realization witness then treats possible in the unrelated fee sentence as evidence that the audio answer was communicated.

### Final plan

```json
{
  "acknowledge": [
    {
      "authority_class": "client_request",
      "fingerprint": "75b40c4ea32606cc9b53ec24c30927180cddde1d84a4404ffc14ce3d3c21387c",
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
        "about": "January gathering",
        "kind": "new_enquiry"
      }
    }
  ],
  "already_communicated": [],
  "client_visible_pending_state": [
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
      "available_equipment": "WNC projector",
      "capability": "projection display",
      "check_required": [
        "practical projection setup"
      ],
      "status": "conditional",
      "topic": "projection_display"
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
  "defer": [
    {
      "authority_class": "current_governed",
      "fingerprint": "feb5ab7f9af3e5bf7c3dd68e36294b0925bc52242b9bbf8c907ce1b49c314ff9",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 50,
      "proposition_key": "guidance:74b98767a0208fcb",
      "reason": "secondary_or_unstructured_guidance_not_needed_now",
      "role": "DEFER",
      "semantic_key": "guidance:74b98767a0208fcb",
      "source_reference": "SERV-003",
      "topic": "catering_kitchen",
      "value": {
        "source_text": "Client and caterer must work within WNC kitchen and delivery limitations. Ready-made or easy-to-assemble food works best. External caterer / client is responsible for cleaning its working area and leaving the venue as found. Large-scale events may require professional cleaning."
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "6376528dba101c8aad7ad55646753b38051d5cc40c99279ce62d10d08aae0388",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 50,
      "proposition_key": "guidance:c860c453d6ac37bf",
      "reason": "secondary_or_unstructured_guidance_not_needed_now",
      "role": "DEFER",
      "semantic_key": "guidance:c860c453d6ac37bf",
      "source_reference": "SERV-004",
      "topic": "external_supplier_setup",
      "value": {
        "source_text": "Supplier / client removes packaging and rental-related waste Venue-rule acknowledgement: Required before delivery"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "00fedd00a4fb4fc8f3ba78a4aedfcc6b10b3e45a53a683955b105d74d2cf8fbd",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 50,
      "proposition_key": "guidance:f3bb9a44431341d3",
      "reason": "secondary_or_unstructured_guidance_not_needed_now",
      "role": "DEFER",
      "semantic_key": "guidance:f3bb9a44431341d3",
      "source_reference": "SERV-004",
      "topic": "external_supplier_setup",
      "value": {
        "source_text": "Supplier / client removes all packaging, cable waste and equipment materials Venue-rule acknowledgement: Required before load-in"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "6122a3ce441a205292345e4d3d4a38bb3109a91e3f917dd76ae2eef9a236ca7c",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 2,
      "proposition_key": "condition:projection:compatibility",
      "reason": "secondary_condition_covered_by_practical_setup_check",
      "role": "DEFER",
      "semantic_key": "condition:projection:compatibility",
      "source_reference": "phase4:technical_projection_display_confirmation",
      "topic": "projection_detail",
      "value": {
        "check_required": "compatibility",
        "status": "check_required"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "5e8f29a1d9629cc021bd2ccd83aa4468a851fc511a44b7ecad568d55fc4bd47e",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 2,
      "proposition_key": "condition:projection:adapters",
      "reason": "secondary_condition_covered_by_practical_setup_check",
      "role": "DEFER",
      "semantic_key": "condition:projection:adapters",
      "source_reference": "phase4:technical_projection_display_confirmation",
      "topic": "projection_detail",
      "value": {
        "check_required": "adapters",
        "status": "check_required"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "b6312d47aaacfa659bd04872fbbcb938cb4df350aeeac5bd29dcced00b324a89",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 2,
      "proposition_key": "condition:projection:files",
      "reason": "secondary_condition_covered_by_practical_setup_check",
      "role": "DEFER",
      "semantic_key": "condition:projection:files",
      "source_reference": "phase4:technical_projection_display_confirmation",
      "topic": "projection_detail",
      "value": {
        "check_required": "files",
        "status": "check_required"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "387c84d92eb347262b6b659159512dd9b332201e339e80a87b97e954df522a69",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 2,
      "proposition_key": "condition:projection:screenless setup suitability",
      "reason": "secondary_condition_covered_by_practical_setup_check",
      "role": "DEFER",
      "semantic_key": "condition:projection:screenless setup suitability",
      "source_reference": "phase4:technical_projection_display_confirmation",
      "topic": "projection_detail",
      "value": {
        "check_required": "screenless setup suitability",
        "status": "check_required"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "061c04201015b5917cd5a3a988b86ac1a65f368e6c604f8873c2b9e6998138a2",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 50,
      "proposition_key": "fact:dj_sound_booth",
      "reason": "client_already_acknowledges_restriction",
      "role": "DEFER",
      "semantic_key": "fact:dj_sound_booth",
      "source_reference": "phase4:technical_dj_sound_booth_restriction",
      "topic": "dj_sound_booth",
      "value": {
        "capability": "dj sound booth",
        "status": "not_supported",
        "supplier_requirement": "external supplier"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "817fd8b9e509953bbe4fb3746e10a128f733d7fa080be2be2eaa0ed813da73d7",
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
        "fact": "event_type: January gathering"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "3a1f8a2a7b03a7dea4ae51bbe7fbfe5fb55647f359d79b107c0d284f05f32c26",
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
        "fact": "Requested rental type code: studio_space"
      }
    }
  ],
  "do_not_repeat": [],
  "editorial_rationale": "compound_material_answers_and_client_questions",
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
      "fingerprint": "7ef3e32e7f9e2b54ff0e81e7c48e442071d049fb1fd22c43505a051af42e17f9",
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
        "text": "Hard constraint: Open question 2136 must be resolved."
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "fc07a87e3b0453aad92ce5e622a954c336a75d96f194ac68391c78306c05ca1a",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 50,
      "proposition_key": "internal:open_question:2136",
      "reason": "ownership_and_workflow_mechanics_stay_local",
      "role": "INTERNAL_ONLY",
      "semantic_key": "internal:open_question:2136",
      "source_reference": "open_question:2136",
      "topic": "resolution",
      "value": {
        "message": "What date and time is the client requesting for the event?",
        "owner": "CLIENT",
        "status": "REQUIRED"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "ff2a1229a345c6724d7af3ec8fa76fc76a5d36c3208954d9d089044c80134e1d",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 50,
      "proposition_key": "internal:open_question:2137",
      "reason": "ownership_and_workflow_mechanics_stay_local",
      "role": "INTERNAL_ONLY",
      "semantic_key": "internal:open_question:2137",
      "source_reference": "open_question:2137",
      "topic": "resolution",
      "value": {
        "message": "How many guests are expected?",
        "owner": "CLIENT",
        "status": "REQUIRED"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "302eb37f7552381da01a400fab5844a5dd1bdc719b5eb8ed03dae904e2ce8b1c",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 50,
      "proposition_key": "internal:case_decision:79",
      "reason": "ownership_and_workflow_mechanics_stay_local",
      "role": "INTERNAL_ONLY",
      "semantic_key": "internal:case_decision:79",
      "source_reference": "case_decision:79",
      "topic": "resolution",
      "value": {
        "message": "booking fee override",
        "owner": "GOVERNED_DECISION",
        "status": "REQUIRED"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "3141c758e4c6324e0fa9b390493961c10f9cf96a61e2ea0efdcf754bde1434b8",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 50,
      "proposition_key": "internal:blocker:2221",
      "reason": "ownership_and_workflow_mechanics_stay_local",
      "role": "INTERNAL_ONLY",
      "semantic_key": "internal:blocker:2221",
      "source_reference": "blocker:2221",
      "topic": "resolution",
      "value": {
        "message": "Confirm event-specific technical setup",
        "owner": "WNC_INTERNAL",
        "status": "ACTION_CREATED"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "e0528e05c9a264bbc048e06efaf8153b8786c3fa793caa5778b4c64c253f1c3c",
      "included_in_model_payload": false,
      "prior_turn_status": "not_previously_communicated",
      "priority": 50,
      "proposition_key": "internal:blocker:2222",
      "reason": "ownership_and_workflow_mechanics_stay_local",
      "role": "INTERNAL_ONLY",
      "semantic_key": "internal:blocker:2222",
      "source_reference": "blocker:2222",
      "topic": "resolution",
      "value": {
        "message": "Contact facilitator about the requested availability and format",
        "owner": "EXTERNAL_PARTY",
        "status": "CONTACT_REQUIRED"
      }
    }
  ],
  "must_ask": [
    {
      "authority_class": "current_governed",
      "fingerprint": "9c69ec3f2c84743551491cb07b8edeb6a604b43bc4a80f1e6cf2cb73d5663f65",
      "included_in_model_payload": true,
      "prior_turn_status": "not_previously_communicated",
      "priority": 2,
      "proposition_key": "question:2136",
      "reason": "open_client_owned_question",
      "role": "MUST_ASK",
      "semantic_key": "question:2136",
      "source_reference": "governed_case",
      "topic": "client_information",
      "value": {
        "open_question_id": 2136,
        "question": "What full date (including year), start time and finish time would you like?"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "f684006b1f12798f2fe396847d1eba81e883f4f0707f2d7cb5fc45a6f43ed285",
      "included_in_model_payload": true,
      "prior_turn_status": "not_previously_communicated",
      "priority": 2,
      "proposition_key": "question:2137",
      "reason": "open_client_owned_question",
      "role": "MUST_ASK",
      "semantic_key": "question:2137",
      "source_reference": "governed_case",
      "topic": "client_information",
      "value": {
        "open_question_id": 2137,
        "question": "How many guests are expected?"
      }
    }
  ],
  "must_communicate": [
    {
      "authority_class": "current_governed",
      "fingerprint": "ce5b101ef2c0cf0ac8e6f03a94d256bc5bdcc8cd709f95396f8a767d60c2d110",
      "included_in_model_payload": true,
      "prior_turn_status": "not_previously_communicated",
      "priority": 4,
      "proposition_key": "commercial.check",
      "reason": "requested_answer_not_yet_available",
      "role": "MUST_COMMUNICATE",
      "semantic_key": "commercial.check",
      "source_reference": "governed_case",
      "topic": "commercial_next_step",
      "value": {
        "action": "check requested booking fee or pricing",
        "status": "check_required"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "01147dc1762bf2076f3036fcf36755e656ccd63e701a5fbc425912ce7dfd5a3c",
      "included_in_model_payload": true,
      "prior_turn_status": "not_previously_communicated",
      "priority": 4,
      "proposition_key": "decision:booking fee override",
      "reason": "pending_governed_decision_in_current_conversation",
      "role": "MUST_COMMUNICATE",
      "semantic_key": "decision:booking fee override",
      "source_reference": "governed_case",
      "topic": "commercial_next_step",
      "value": {
        "action": "check what can be arranged",
        "request": "booking fee adjustment",
        "status": "check_required"
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "8ba654ac396fc19822cecd67c06d7a927fd97238ba66a337daa3b0d9c888d61a",
      "included_in_model_payload": true,
      "prior_turn_status": "not_previously_communicated",
      "priority": 1,
      "proposition_key": "fact:catering_kitchen",
      "reason": "current_catering_suitability_question",
      "role": "MUST_COMMUNICATE",
      "semantic_key": "fact:catering_kitchen",
      "source_reference": "SERV-003",
      "topic": "catering_kitchen",
      "value": {
        "limitation": "not large-scale food production",
        "suitable_for": [
          "ready-made food",
          "warming",
          "plating",
          "simple assembly"
        ]
      }
    },
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
      "fingerprint": "672b1a863ea87ac08dad150ee3c17339d636ca915f70b17294df2679b3424af4",
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
        "client_fact": {
          "background_music_playback": true
        }
      }
    },
    {
      "authority_class": "current_governed",
      "fingerprint": "52a59b6b10803b5e268da5805c92f7136caa50cd2a3f3f93eca4aa0365abb88c",
      "included_in_model_payload": true,
      "prior_turn_status": "not_previously_communicated",
      "priority": 4,
      "proposition_key": "next_step",
      "reason": "immediate_wnc_owned_next_step",
      "role": "MUST_COMMUNICATE",
      "semantic_key": "next_step",
      "source_reference": "governed_case",
      "topic": "next_step",
      "value": {
        "action": "check",
        "status": "check_required",
        "subjects": [
          "requested facilitator availability and format"
        ]
      }
    }
  ],
  "primary_client_need": [
    "client_owned_missing_information"
  ],
  "response_intent": "REQUEST_CLIENT_INFORMATION",
  "source_bindings": [
    {
      "fingerprint": "9c69ec3f2c84743551491cb07b8edeb6a604b43bc4a80f1e6cf2cb73d5663f65",
      "semantic_key": "question:2136",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "f684006b1f12798f2fe396847d1eba81e883f4f0707f2d7cb5fc45a6f43ed285",
      "semantic_key": "question:2137",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "75b40c4ea32606cc9b53ec24c30927180cddde1d84a4404ffc14ce3d3c21387c",
      "semantic_key": "latest_client_detail",
      "source_reference": "current_client_message"
    },
    {
      "fingerprint": "ce5b101ef2c0cf0ac8e6f03a94d256bc5bdcc8cd709f95396f8a767d60c2d110",
      "semantic_key": "commercial.check",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "01147dc1762bf2076f3036fcf36755e656ccd63e701a5fbc425912ce7dfd5a3c",
      "semantic_key": "decision:booking fee override",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "8ba654ac396fc19822cecd67c06d7a927fd97238ba66a337daa3b0d9c888d61a",
      "semantic_key": "fact:catering_kitchen",
      "source_reference": "SERV-003"
    },
    {
      "fingerprint": "feb5ab7f9af3e5bf7c3dd68e36294b0925bc52242b9bbf8c907ce1b49c314ff9",
      "semantic_key": "guidance:74b98767a0208fcb",
      "source_reference": "SERV-003"
    },
    {
      "fingerprint": "6376528dba101c8aad7ad55646753b38051d5cc40c99279ce62d10d08aae0388",
      "semantic_key": "guidance:c860c453d6ac37bf",
      "source_reference": "SERV-004"
    },
    {
      "fingerprint": "00fedd00a4fb4fc8f3ba78a4aedfcc6b10b3e45a53a683955b105d74d2cf8fbd",
      "semantic_key": "guidance:f3bb9a44431341d3",
      "source_reference": "SERV-004"
    },
    {
      "fingerprint": "6122a3ce441a205292345e4d3d4a38bb3109a91e3f917dd76ae2eef9a236ca7c",
      "semantic_key": "condition:projection:compatibility",
      "source_reference": "phase4:technical_projection_display_confirmation"
    },
    {
      "fingerprint": "5e8f29a1d9629cc021bd2ccd83aa4468a851fc511a44b7ecad568d55fc4bd47e",
      "semantic_key": "condition:projection:adapters",
      "source_reference": "phase4:technical_projection_display_confirmation"
    },
    {
      "fingerprint": "b6312d47aaacfa659bd04872fbbcb938cb4df350aeeac5bd29dcced00b324a89",
      "semantic_key": "condition:projection:files",
      "source_reference": "phase4:technical_projection_display_confirmation"
    },
    {
      "fingerprint": "387c84d92eb347262b6b659159512dd9b332201e339e80a87b97e954df522a69",
      "semantic_key": "condition:projection:screenless setup suitability",
      "source_reference": "phase4:technical_projection_display_confirmation"
    },
    {
      "fingerprint": "611225d828231fc1d2df193b9e2b6261ba6eff562cf33deb3a4577cc0218ebd0",
      "semantic_key": "fact:projection_display",
      "source_reference": "phase4:technical_projection_display_confirmation"
    },
    {
      "fingerprint": "672b1a863ea87ac08dad150ee3c17339d636ca915f70b17294df2679b3424af4",
      "semantic_key": "fact:audio_playback",
      "source_reference": "phase4:technical_audio_playback_supported"
    },
    {
      "fingerprint": "061c04201015b5917cd5a3a988b86ac1a65f368e6c604f8873c2b9e6998138a2",
      "semantic_key": "fact:dj_sound_booth",
      "source_reference": "phase4:technical_dj_sound_booth_restriction"
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
      "fingerprint": "7ef3e32e7f9e2b54ff0e81e7c48e442071d049fb1fd22c43505a051af42e17f9",
      "semantic_key": "restriction:Hard constraint",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "817fd8b9e509953bbe4fb3746e10a128f733d7fa080be2be2eaa0ed813da73d7",
      "semantic_key": "case_fact:event_type",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "3a1f8a2a7b03a7dea4ae51bbe7fbfe5fb55647f359d79b107c0d284f05f32c26",
      "semantic_key": "case_fact:Requested rental type code",
      "source_reference": "governed_case"
    },
    {
      "fingerprint": "fc07a87e3b0453aad92ce5e622a954c336a75d96f194ac68391c78306c05ca1a",
      "semantic_key": "internal:open_question:2136",
      "source_reference": "open_question:2136"
    },
    {
      "fingerprint": "ff2a1229a345c6724d7af3ec8fa76fc76a5d36c3208954d9d089044c80134e1d",
      "semantic_key": "internal:open_question:2137",
      "source_reference": "open_question:2137"
    },
    {
      "fingerprint": "302eb37f7552381da01a400fab5844a5dd1bdc719b5eb8ed03dae904e2ce8b1c",
      "semantic_key": "internal:case_decision:79",
      "source_reference": "case_decision:79"
    },
    {
      "fingerprint": "3141c758e4c6324e0fa9b390493961c10f9cf96a61e2ea0efdcf754bde1434b8",
      "semantic_key": "internal:blocker:2221",
      "source_reference": "blocker:2221"
    },
    {
      "fingerprint": "e0528e05c9a264bbc048e06efaf8153b8786c3fa793caa5778b4c64c253f1c3c",
      "semantic_key": "internal:blocker:2222",
      "source_reference": "blocker:2222"
    },
    {
      "fingerprint": "52a59b6b10803b5e268da5805c92f7136caa50cd2a3f3f93eca4aa0365abb88c",
      "semantic_key": "next_step",
      "source_reference": "governed_case"
    }
  ],
  "substantive_budget": 8,
  "version": "editorial_content_plan_v3"
}
```

### Exact final draft

DraftRevision 334; captured validator PASS. Exact approval/action binding: PASS.

**Subject**

```text
January Studio gathering
```

**Body**

```text
Hi Ari,

Your plans for slides, background music and an outside caterer sound well suited to a relaxed Studio gathering. WNC has a projector, and I’ll check the practical setup for both the projection and music playback. The catering kitchen is suitable for ready-made food, warming, plating and simple assembly, rather than large-scale food production.

I’ll also check the booking fee, what adjustment may be possible, and the availability and format of a short facilitator-led opening.

What full date, including the year, start time and finish time would you like? How many guests are expected?
```

# All Plan and Payload Evidence

The JSON audit stores every complete plan, exact client payload, validator result and realization metadata. The results file stores every captured DraftRevision and action/approval binding; final snapshots establish currentness after follow-ups. Historical turn revisions may legitimately be superseded by later turns.

- [Exact plans and client payloads](acceptance_planner_audit.json)
- [Frozen results and request log](acceptance_results.json)
- [Final case snapshots](acceptance_final_snapshots.json)
- [Plan boundary audit](acceptance_plan_validation.json)
- [Canonical binding audit](acceptance_captured_contract_validation.json)
- [Current draft integrity audit](acceptance_integrity_audit.json)
- [Frozen manifest and prior evidence hashes](frozen_manifest.json)

# Safety Activity

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

Staging health/provider posture and provider-free case/request-log audits establish the reported gates. Activity counts describe this task’s authorized route calls and resulting synthetic cases. No permissions or environment settings were changed.

# Remaining Issues

- UAT-010/1: the concrete aerial-rig action lacks the status field used by the existing fallback selector. The selector therefore adds an unnecessary venue-availability next step. The abstract-feasibility wording is resolved; this new selection side effect prevents the zero-unnecessary-information gate.
- UAT-012/1: the draft casts the selected supported-music fact as a setup check instead of clearly answering capability. The realization witness combines music in one paragraph with possible in the unrelated fee sentence, so subsequent turns treat audio as answered. This counts as one unanswered request and makes answer-completeness continuity 6/7, despite all seven multi-turn cases persisting successfully.
- Provider-free diagnosis confirms both findings in acceptance_remaining_issue_diagnosis.json. No code change, provider-result regeneration or second acceptance run was performed after observing them.
- All reviews are direct assistant assessments, not independent human validation. Finite topic aliases and realization witnesses have limited semantic coverage.

# Final Marker

EDITORIAL_PLANNER_TARGETED_CLOSURE_REVIEW_REQUIRED

Stopped after the single acceptance run. No further implementation cycle, approval, sending enablement or action execution.
