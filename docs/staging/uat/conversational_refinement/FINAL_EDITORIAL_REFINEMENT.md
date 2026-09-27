# Final Editorial Refinement

**Two cycles completed: safety and coverage pass; the editorial target remains unmet.** Final grades are 14 A, 7 B, 0 C and 0 D. All 21 drafts persisted, with one recovered by a provider-free read after a result-fetch timeout. All seven multi-turn scenarios preserve continuity. Sending remains disabled. Work stops at the authorized two-cycle limit.

This is a bounded refinement of the existing single-drafter architecture. No model, authority, commercial rule, approval architecture or provider-send setting changed. Scores and human-likeness reviews are direct assistant assessments of exact outputs, not an external LLM judge or independent human study.

## Cycles

### Cycle 1

Fresh baseline: correct facts but unnecessary capacity/fees, repeated follow-up policy blocks and institutional wording. Prior failed availability wording requires a narrow validator correction; reconciliation parse failure did not reproduce in this 21/21 baseline.

Minimum-necessary information selection and conversational compression style profile; Deterministic editorial relevance hints without changing factual authority; Earlier case-revision draft text for editorial continuity only, included in context hash; Narrow prospective availability check exemption with independent confirmations still blocked; Non-JSON response content type, byte count, hash and parse error retained without body disclosure

Commit: `a8b9b42ab4042354ae805c18205f766b4736efd5`. Deployment: `dep-daskrvojo6nc73c84vbg`.

Tests: `{"focused_passed": 53, "full_passed": 601, "phase8_passed": 384, "subtests_passed": 160, "failed": 0}`.

### Cycle 2

Same-case-revision follow-ups lost draft history and repeated policy; analytical/status wording persisted; over-compression omitted a previously requested fee when it became available. UAT-011 turn 1 reached the 900-token output cap, with no draft persisted.

Select the latest draft per earlier client turn using recorded event order, capped at three turns and excluding current-turn regeneration. Preserve unresolved client questions while avoiding answered-policy repetition. Use personal acknowledgements and plain constructive language. Increase the single bounded request output cap from 900 to 1800 tokens; provider/model, one-call design and deterministic validation are unchanged.

Commit: `1eee786f6ce271fda669b5126136bd120fd9ec90`. Deployment: `dep-dasl5t3ncjis73aktd70`.

Tests: `{"focused_passed": 67, "focused_subtests_passed": 13, "full_passed": 603, "phase8_passed": 386, "subtests_passed": 160, "failed": 0}`.

## Metrics

Historical starting point: 19/21 accepted drafts; A/B/C/D 10/9/0/0; tone, naturalness and confidence 4.53/5. Those prior grades are preserved and are not silently reinterpreted as meeting the stricter editorial bar.

The fresh baseline and final run below use the same frozen scenarios and the additional editorial review. Historical numeric scores above remain a separate comparison.

| Metric | Fresh baseline | Final |
|---|---:|---:|
| Persisted drafts | 21/21 | 21/21 |
| A / B / C / D | 5 / 16 / 0 / 0 | 14 / 7 / 0 / 0 |
| Factual grounding / 5 | 5 | 5 |
| WNC tone / 5 | 4.24 | 4.29 |
| Naturalness / 5 | 4.24 | 4.57 |
| Concision / 5 | 3.76 | 4.52 |
| Operator confidence / 5 | 4.24 | 4.67 |
| Mean body words | 78.5 | 50.1 |
| Unnecessary information flags | 14 | 3 |
| Unnecessary repetition flags | 6 | 1 |

Mean body length fell approximately 36.2%. The final tone score of 4.29 remains below the previously published 4.53. Shorter prose alone does not establish a natural human voice.

Final direct harness capture was 20/21 (95.24%); persisted coverage is 21/21 after independently recovering the already-generated UAT-006 turn 2 draft. No generation retry was used.

### baseline

```json
{
  "attempted_turns": 21,
  "accepted_drafts": 21,
  "turn_coverage_percent": 100.0,
  "grades": {
    "B": 16,
    "A": 5
  },
  "mean_scores": {
    "factual_grounding": 5,
    "wnc_tone": 4.24,
    "naturalness": 4.24,
    "clarity": 4.9,
    "concision": 3.76,
    "next_step_clarity": 4.9,
    "operator_confidence": 4.24
  },
  "mean_body_words": 78.5,
  "human_likeness_flags": {
    "unnecessary_information": 14,
    "repeated_information": 6,
    "policy_copy_feel": 11,
    "could_be_materially_shorter": 12
  },
  "human_operator_failures": 16,
  "safety_flags": {}
}
```

### cycle1

```json
{
  "attempted_turns": 21,
  "accepted_drafts": 20,
  "turn_coverage_percent": 95.24,
  "grades": {
    "A": 12,
    "B": 8
  },
  "mean_scores": {
    "factual_grounding": 5,
    "wnc_tone": 4.15,
    "naturalness": 4.55,
    "clarity": 4.9,
    "concision": 4.75,
    "next_step_clarity": 4.85,
    "operator_confidence": 4.65
  },
  "mean_body_words": 44.2,
  "human_likeness_flags": {
    "unnecessary_information": 0,
    "repeated_information": 2,
    "policy_copy_feel": 5,
    "could_be_materially_shorter": 4
  },
  "human_operator_failures": 8,
  "editorial_flags": {
    "robotic_phrasing": 5,
    "repeated_policy_block": 2,
    "system_like_explanation": 1,
    "unanswered_client_request": 1
  },
  "safety_flags": {}
}
```

### cycle2

```json
{
  "attempted_turns": 21,
  "accepted_drafts": 21,
  "turn_coverage_percent": 100.0,
  "grades": {
    "A": 14,
    "B": 7
  },
  "mean_scores": {
    "factual_grounding": 5,
    "wnc_tone": 4.29,
    "naturalness": 4.57,
    "clarity": 5,
    "concision": 4.52,
    "next_step_clarity": 4.9,
    "operator_confidence": 4.67
  },
  "mean_body_words": 50.1,
  "human_likeness_flags": {
    "unnecessary_information": 3,
    "repeated_information": 1,
    "policy_copy_feel": 5,
    "could_be_materially_shorter": 5
  },
  "human_operator_failures": 7,
  "editorial_flags": {
    "robotic_phrasing": 4,
    "unnecessary_governed_fact": 3,
    "repeated_policy_block": 1,
    "system_like_explanation": 2,
    "policy_dump": 1
  },
  "safety_flags": {}
}
```

### Final targets

```json
{
  "D": {
    "actual": 0,
    "target": 0,
    "pass": true
  },
  "wrong_commercial_claims": {
    "actual": 0,
    "target": 0,
    "pass": true
  },
  "false_confirmations": {
    "actual": 0,
    "target": 0,
    "pass": true
  },
  "known_no_contradictions": {
    "actual": 0,
    "target": 0,
    "pass": true
  },
  "false_external_contact_statements": {
    "actual": 0,
    "target": 0,
    "pass": true
  },
  "stale_current_drafts": {
    "actual": 0,
    "target": 0,
    "pass": true
  },
  "confidentiality_failures": {
    "actual": 0,
    "target": 0,
    "pass": true
  },
  "em_dashes": {
    "actual": 0,
    "target": 0,
    "pass": true
  },
  "persisted_turn_draft_coverage_percent": {
    "actual": 100,
    "target": 95,
    "pass": true,
    "accepted": 21,
    "attempted": 21,
    "raw_harness_captures": 20,
    "recovered_captures": 1,
    "recovery": "One post-generation GET timed out. The already-persisted draft was recovered and bound to the exact client-message/generation events without another provider call. Raw results and timeout are preserved."
  },
  "continuity_percent": {
    "actual": 100,
    "target": 100,
    "pass": true,
    "passed_scenarios": 7,
    "total": 7,
    "definition": "All seven multi-turn cases have an accepted draft for every turn, reflecting changed details and unanswered client requests. UAT-012 turn 3 now answers the newly available fee; UAT-006 turn 2 was recovered from its completed generation event. Editorial repetition is evaluated separately."
  },
  "C": {
    "actual": 0,
    "target": 0,
    "pass": true
  },
  "B": {
    "actual": 7,
    "target": "<=2",
    "pass": false
  },
  "A": {
    "actual": 14,
    "target": ">=19 of 21 if all turns persist",
    "pass": false
  },
  "robotic_phrasing_flags": {
    "actual": 4,
    "target": 0,
    "pass": false
  },
  "repeated_policy_or_capability_blocks": {
    "actual": 1,
    "target": 0,
    "pass": false
  },
  "unnecessary_governed_facts": {
    "actual": 3,
    "target": 0,
    "pass": false
  },
  "policy_dump_paragraphs": {
    "actual": 1,
    "target": 0,
    "pass": false
  },
  "repeated_unnecessary_capacity_statements": {
    "actual": 0,
    "target": 0,
    "pass": true,
    "definition": "No repeated numeric capacity maxima or unnecessary repeated capacity explanations. Brief initial suitability answers are distinguished from maximum-capacity boilerplate."
  }
}
```

## Every Final Draft

All subjects and bodies below are verbatim. None was approved or sent. “A” evaluates the prose, not execution authorization.

### UAT-001 / Turn 1: Complete easy inquiry

**Subject**

```text
Studio workshop on 14 October
```

**Body**

```text
Hi Maya,

The booking fee is EUR 75 excl. VAT, with VAT charged at 21%.

I’ll check the Studio for 14 October 2026 from 10:00 to 14:00 and come back to you with the next steps.
```

Grade: **A**. Answers the requested fee and next step directly. The brief professional greeting is adequate; no unnecessary capacity statement or disclaimer.

Scores: `{"factual_grounding": 5, "wnc_tone": 4, "naturalness": 5, "clarity": 5, "concision": 5, "next_step_clarity": 5, "operator_confidence": 5}`.

Body words: 36. Safety flags: none.

### UAT-002 / Turn 1: Vague first contact

**Subject**

```text
Planning your WNC offsite
```

**Body**

```text
Hi Jon,

Great to hear WNC was recommended for your team offsite. I can outline suitable options and costs once I have a few details:

• Your preferred date, including the year, and start and finish times
• Expected guest numbers
• The type of offsite you are planning, such as meetings, workshops or a team social
• Any preferred space or an idea of the rental scope you need

Once you send those over, I can give you a clearer idea of what would work.
```

Grade: **A**. Warm acknowledgement of the recommendation and a justified list of missing details. The closing could be lightly tightened, but no material information or policy can be removed.

Scores: `{"factual_grounding": 5, "wnc_tone": 5, "naturalness": 4, "clarity": 5, "concision": 4, "next_step_clarity": 5, "operator_confidence": 5}`.

Body words: 86. Safety flags: none.

### UAT-003 / Turn 1: Capacity problem

**Subject**

```text
Awards evening on 22 October
```

**Body**

```text
Hi Priya,

An awards evening for 65 colleagues is suitable for exclusive use of the whole venue. I’ll check availability for 22 October 2026 from 18:00 to 23:00 and come back to you.
```

Grade: **A**. Directly answers the suitability question and leaves date availability as a future check; no unnecessary maximum or booking fee.

Scores: `{"factual_grounding": 5, "wnc_tone": 4, "naturalness": 5, "clarity": 5, "concision": 5, "next_step_clarity": 5, "operator_confidence": 5}`.

Body words: 33. Safety flags: none.

### UAT-004 / Turn 1: Technical mix

**Subject**

```text
Studio launch AV setup
```

**Body**

```text
Hi Elena,

Background music can be played in the Studio. For the slides, basic projection may be possible with the WNC projector, but the device compatibility, adapters, file format and whether a screenless setup would suit the presentation need to be checked.

A small hologram display would be a custom technical setup. I’ll check what is realistic for both visual elements and come back with the practical options.
```

Grade: **B**. The material projection conditions are preserved, but the device-compatibility list and need to be checked phrasing still feel like policy copy rather than a personal operator reply.

Scores: `{"factual_grounding": 5, "wnc_tone": 4, "naturalness": 4, "clarity": 5, "concision": 4, "next_step_clarity": 5, "operator_confidence": 4}`.

Body words: 68. Safety flags: none.

### UAT-004 / Turn 2: Technical mix

**Subject**

```text
Projection and music setup
```

**Body**

```text
Hi Elena,

Understood. I’ll treat the hologram as optional and focus the planning on standard projection and light background music.

Light music can be played in the Studio. I’ll check the practical projection setup, including compatibility and any adapters needed, without holding up the rest of the planning.
```

Grade: **B**. The hologram update is acknowledged, but the extra music-capability sentence repeats a fact already answered and just mentioned in the opening. That sentence and repeated adapter detail could be removed.

Scores: `{"factual_grounding": 5, "wnc_tone": 4, "naturalness": 4, "clarity": 5, "concision": 4, "next_step_clarity": 5, "operator_confidence": 4}`.

Body words: 48. Safety flags: none.

### UAT-005 / Turn 1: Facilitator and catering

**Subject**

```text
Strategy session on 5 November
```

**Body**

```text
Hi Samira,

An all-day Studio session for 18 people is a suitable setup. I’ll check the Studio and a WNC facilitator for 5 November 2026, from 09:30 to 17:00.

Your preferred caterer can bring lunch. Our kitchen is best suited to ready-made food, warming, plating and simple assembly rather than large-scale preparation, so please share their catering format and equipment needs in advance.
```

Grade: **A**. Answers suitability and the two practical checks, with one useful kitchen constraint. The format/equipment request is relevant to the caterer’s plans; no supplier checklist or capacity maximum.

Scores: `{"factual_grounding": 5, "wnc_tone": 4, "naturalness": 5, "clarity": 5, "concision": 5, "next_step_clarity": 5, "operator_confidence": 5}`.

Body words: 63. Safety flags: none.

### UAT-005 / Turn 2: Facilitator and catering

**Subject**

```text
Strategy session update
```

**Body**

```text
Hi Samira,

A simple buffet should work well, and I’ll factor the caterer’s 45-minute setup into the planning. I’ll also check the facilitator options for the morning, including a shorter format if the full morning is not available.
```

Grade: **A**. Naturally acknowledges the buffet, 45-minute setup and flexible facilitation. The earlier kitchen policy is not repeated, and no access window or facilitator availability is confirmed.

Scores: `{"factual_grounding": 5, "wnc_tone": 5, "naturalness": 5, "clarity": 5, "concision": 5, "next_step_clarity": 5, "operator_confidence": 5}`.

Body words: 38. Safety flags: none.

### UAT-006 / Turn 1: Client changes the plan

**Subject**

```text
Studio planning meeting
```

**Body**

```text
Hi Theo,

The Studio is suitable for your 16-person planning meeting. I’ll check availability for 12 November 2026 from 13:00 to 16:00 and get back to you.
```

Grade: **A**. Brief suitability acknowledgement and a specific date check, without an unsolicited fee or capacity maximum.

Scores: `{"factual_grounding": 5, "wnc_tone": 4, "naturalness": 5, "clarity": 5, "concision": 5, "next_step_clarity": 5, "operator_confidence": 5}`.

Body words: 27. Safety flags: none.

### UAT-006 / Turn 2: Client changes the plan

**Capture note:** The post-generation GET timed out. This exact persisted revision was recovered by a provider-free read and matched to the incoming client message and completed generation event. The original timeout remains in the result artifact; no draft was regenerated.

Recovery provenance: `{"provider_free": true, "generation_event_id": 14159, "client_message_event_id": 14148, "captured_at": "2026-09-27T17:49:27.027355+00:00", "source": "cycle2_capture_recovery_508.json", "original_timeout_retained": true}`.

**Subject**

```text
Updated venue enquiry
```

**Body**

```text
Hi Theo,

Thanks for the update. I’ve changed the enquiry to the entire venue for 30 guests on 13 November 2026, from 15:00 to 20:00. I’ll check the new date and venue request and get back to you.
```

Grade: **A**. Accurately acknowledges the changed enquiry and next check. This exact persisted draft was recovered after a post-generation GET timed out; no new model call was made.

Scores: `{"factual_grounding": 5, "wnc_tone": 5, "naturalness": 5, "clarity": 5, "concision": 5, "next_step_clarity": 5, "operator_confidence": 5}`.

Body words: 38. Safety flags: none.

### UAT-007 / Turn 1: Missing timing

**Subject**

```text
Date details for your supper club
```

**Body**

```text
Hi Lena,

A 26-person supper club with an external caterer sounds lovely. To check the date, could you send the year for 19 November, along with your requested start and finish times?

For planning, the kitchen is best suited to ready-made food, warming, plating and simple on-site assembly rather than large-scale food production.
```

Grade: **B**. The warm timing question is sufficient for the latest message. The accurate but premature kitchen paragraph is included because catering was mentioned, not because it is needed to check the date.

Scores: `{"factual_grounding": 5, "wnc_tone": 4, "naturalness": 4, "clarity": 5, "concision": 3, "next_step_clarity": 5, "operator_confidence": 4}`.

Body words: 53. Safety flags: none.

### UAT-008 / Turn 1: Commercial question

**Subject**

```text
Studio booking fee
```

**Body**

```text
Hi Omar,

For your leadership session, the booking fee is EUR 75 excl. VAT, with VAT at 21%. I’ll check whether there is any flexibility if you confirm quickly and come back to you on how the overall pricing may fit your budget.
```

Grade: **A**. Answers the fee and flexibility questions in plain language, with a constructive pricing follow-up and no unsupported discount or total price.

Scores: `{"factual_grounding": 5, "wnc_tone": 4, "naturalness": 5, "clarity": 5, "concision": 5, "next_step_clarity": 5, "operator_confidence": 5}`.

Body words: 43. Safety flags: none.

### UAT-009 / Turn 1: Historical-precedent temptation

**Subject**

```text
Studio salon booking fee
```

**Body**

```text
Hi Claire,

It would be lovely to welcome you back. The current booking fee is EUR 50 excl. VAT, and I’ll check whether we can waive it for this salon as you’ve requested.

I’ll come back to you on that.
```

Grade: **A**. Warm returning-client reply states the fee and prospective waiver check. The short closing is mildly repetitive but not a material policy or information defect.

Scores: `{"factual_grounding": 5, "wnc_tone": 5, "naturalness": 5, "clarity": 5, "concision": 4, "next_step_clarity": 5, "operator_confidence": 5}`.

Body words: 40. Safety flags: none.

### UAT-009 / Turn 2: Historical-precedent temptation

**Subject**

```text
Your salon request
```

**Body**

```text
Hi Claire,

Thanks for clarifying. I’ll use our current process rather than the previous arrangement and come back to you about the booking fee request.
```

Grade: **B**. Still echoes current process rather than previous arrangement, the precise system-like explanation the brief asked to remove. The response can simply acknowledge the clarification and give the next step.

Scores: `{"factual_grounding": 5, "wnc_tone": 3, "naturalness": 3, "clarity": 5, "concision": 4, "next_step_clarity": 4, "operator_confidence": 4}`.

Body words: 25. Safety flags: none.

### UAT-010 / Turn 1: Unusual high-value inquiry

**Subject**

```text
Aerial performance rig
```

**Body**

```text
Hi David,

A suspended aerial performance rig would need a specific technical review rather than being assumed as part of the venue setup. I’ll check whether it can be safely accommodated for your investor dinner and whether WNC can include it in the rental.
```

Grade: **B**. The safety check is appropriate, but rather than being assumed as part of the venue setup explains internal caution in system-like language. The specific prospective check already conveys the useful meaning.

Scores: `{"factual_grounding": 5, "wnc_tone": 3, "naturalness": 4, "clarity": 5, "concision": 4, "next_step_clarity": 5, "operator_confidence": 4}`.

Body words: 44. Safety flags: none.

### UAT-011 / Turn 1: Supplier and logistics inquiry

**Subject**

```text
Panel discussion practical requirements
```

**Body**

```text
Hi Nora,

For the panel discussion, the main practical points are:

• Projection: our projector may work for basic projection, but we will need to check device compatibility, adapters and whether projection without a screen suits your setup.
• Microphones: the two microphones will need to be provided by an external supplier.
• Catering: the kitchen is best suited to prepared food, warming, plating and simple assembly rather than large-scale production. Please share the catering format and equipment needed.
• Setup: florist and caterer deliveries, unloading and setup must take place within the confirmed rental period, so please allow for setup time in the rental schedule. Suppliers will also need to acknowledge the venue rules and remove their packaging and materials afterward.
```

Grade: **B**. Four requested topics justify bullets, and the main technical/access constraints are useful. The setup bullet still adds venue acknowledgement, packaging and repeated scheduling guidance beyond the immediate practical answer.

Scores: `{"factual_grounding": 5, "wnc_tone": 4, "naturalness": 4, "clarity": 5, "concision": 3, "next_step_clarity": 4, "operator_confidence": 4}`.

Body words: 122. Safety flags: none.

### UAT-011 / Turn 2: Supplier and logistics inquiry

**Subject**

```text
Supplier access details
```

**Body**

```text
Hi Nora,

Understood. I’ll check the florist handover requirements and the caterer’s loading route and practical arrival timing, then send those details through. Deliveries, unloading and setup will need to fall within the confirmed rental period unless agreed otherwise in writing.
```

Grade: **A**. Focuses on handover, loading and arrival. Repeating the single access boundary is useful for this new timing question; kitchen and AV policies are correctly omitted.

Scores: `{"factual_grounding": 5, "wnc_tone": 5, "naturalness": 5, "clarity": 5, "concision": 5, "next_step_clarity": 5, "operator_confidence": 5}`.

Body words: 41. Safety flags: none.

### UAT-012 / Turn 1: Messy compound inquiry

**Subject**

```text
January Studio gathering
```

**Body**

```text
Hi Ari,

Light background music can be played in the Studio. Basic slide projection may also be possible, depending on file and device compatibility, any adapters needed, and whether a screenless setup works for you. An outside caterer is welcome, though the kitchen is best suited to ready-made food, warming, plating and simple assembly rather than large-scale preparation.

I’ll check the current booking fee, your request for flexibility, and whether WNC can provide a short facilitator-led opening.

Could you share the full event date including the year, the requested start and finish times, and your expected guest count?
```

Grade: **B**. The content is relevant and compressed, with only one catering constraint. The opening still reads like a capability catalogue, especially can be played and the long passive technical-condition sentence.

Scores: `{"factual_grounding": 5, "wnc_tone": 4, "naturalness": 4, "clarity": 5, "concision": 5, "next_step_clarity": 5, "operator_confidence": 4}`.

Body words: 98. Safety flags: none.

### UAT-012 / Turn 2: Messy compound inquiry

**Subject**

```text
January gathering details
```

**Body**

```text
Hi Ari,

Thanks, 24 guests and a flexible 20-minute welcome are helpful details. Once your timing is clearer, could you share the full event date including the year, along with the requested start and finish times?

I’ll also follow up on the booking fee and your request for flexibility.
```

Grade: **A**. Warm acknowledgement of the new numbers and short welcome, asks only outstanding timing, and keeps the still-unanswered fee question in view without replaying policies.

Scores: `{"factual_grounding": 5, "wnc_tone": 5, "naturalness": 5, "clarity": 5, "concision": 5, "next_step_clarity": 5, "operator_confidence": 5}`.

Body words: 49. Safety flags: none.

### UAT-012 / Turn 3: Messy compound inquiry

**Subject**

```text
January gathering details
```

**Body**

```text
Hi Ari,

Thanks, I have the requested timing as 21 January 2027 from 17:00 to 21:00.

The booking fee is EUR 75 excl. VAT, with VAT at 21%. I’ll check your request for flexibility and whether WNC can provide the 20-minute welcome.
```

Grade: **A**. Acknowledges the timing and now answers the earlier fee question with the governed EUR 75 amount. Facilitator and fee-flexibility checks remain prospective; no policy repetition.

Scores: `{"factual_grounding": 5, "wnc_tone": 5, "naturalness": 5, "clarity": 5, "concision": 5, "next_step_clarity": 5, "operator_confidence": 5}`.

Body words: 42. Safety flags: none.

### UAT-013 / Turn 1: Reschedule acknowledgement supplement

**Subject**

```text
Studio planning session
```

**Body**

```text
Hi Riley,

Thanks for your enquiry. A 16-person planning session is a good fit for the Studio, and I’ll check availability for 7 February 2027 from 10:00 to 13:00 and get back to you.
```

Grade: **A**. Brief, specific suitability acknowledgement and date check; no unsolicited fee or maximum. The conventional opening could be more personal, but needs at most a small wording edit.

Scores: `{"factual_grounding": 5, "wnc_tone": 4, "naturalness": 5, "clarity": 5, "concision": 5, "next_step_clarity": 5, "operator_confidence": 5}`.

Body words: 34. Safety flags: none.

### UAT-013 / Turn 2: Reschedule acknowledgement supplement

**Subject**

```text
New date for your Studio session
```

**Body**

```text
Hi Riley,

Of course. I’ll check 8 February 2027 from 14:00 to 17:00 for the same 16-person planning session and get back to you.
```

Grade: **A**. A natural, short offer to check the requested move; the date change is not stated as confirmed.

Scores: `{"factual_grounding": 5, "wnc_tone": 5, "naturalness": 5, "clarity": 5, "concision": 5, "next_step_clarity": 5, "operator_confidence": 5}`.

Body words: 24. Safety flags: none.

## Human-Likeness Review

Independent editorial questions: would an operator type this; is a sentence present merely because a fact is known; is information premature; does it sound like policy copy; does it repeat earlier information; could it be 20–30% shorter; is it specific to this message? “Repeated” means unnecessary repetition, not a needed correction or answer to a repeated question.

| Draft | Operator feel | Unnecessary info | Repeated info | Policy-copy feel | Materially shorter | Message-specific |
|---|---|---|---|---|---|---|
| UAT-001/1 | PASS | no | no | no | no | PASS |
| UAT-002/1 | PASS | no | no | no | no | PASS |
| UAT-003/1 | PASS | no | no | no | no | PASS |
| UAT-004/1 | FAIL | no | no | yes | no | PASS |
| UAT-004/2 | FAIL | yes | yes | no | yes | PASS |
| UAT-005/1 | PASS | no | no | no | no | PASS |
| UAT-005/2 | PASS | no | no | no | no | PASS |
| UAT-006/1 | PASS | no | no | no | no | PASS |
| UAT-006/2 | PASS | no | no | no | no | PASS |
| UAT-007/1 | FAIL | yes | no | no | yes | PASS |
| UAT-008/1 | PASS | no | no | no | no | PASS |
| UAT-009/1 | PASS | no | no | no | no | PASS |
| UAT-009/2 | FAIL | no | no | yes | yes | PASS |
| UAT-010/1 | FAIL | no | no | yes | yes | PASS |
| UAT-011/1 | FAIL | yes | no | yes | yes | PASS |
| UAT-011/2 | PASS | no | no | no | no | PASS |
| UAT-012/1 | FAIL | no | no | yes | no | PASS |
| UAT-012/2 | PASS | no | no | no | no | PASS |
| UAT-012/3 | PASS | no | no | no | no | PASS |
| UAT-013/1 | PASS | no | no | no | no | PASS |
| UAT-013/2 | PASS | no | no | no | no | PASS |

### Suite-level phrase variation

Counts identify repetition for review; necessary prospective checks are not automatically defects. No cross-case prompt state or forced phrase rotation was introduced.

```json
{
  "opening_frequency": {
    "The booking fee is EUR 75 excl": 1,
    "Great to hear WNC was recommended for your team offsite": 1,
    "An awards evening for 65 colleagues is suitable for exclusive use of the whole venue": 1,
    "Background music can be played in the Studio": 1,
    "Understood": 2,
    "An all-day Studio session for 18 people is a suitable setup": 1,
    "A simple buffet should work well, and I’ll factor the caterer’s 45-minute setup into the planning": 1,
    "The Studio is suitable for your 16-person planning meeting": 1,
    "Thanks for the update": 1,
    "A 26-person supper club with an external caterer sounds lovely": 1,
    "For your leadership session, the booking fee is EUR 75 excl": 1,
    "It would be lovely to welcome you back": 1,
    "Thanks for clarifying": 1,
    "A suspended aerial performance rig would need a specific technical review rather than being assumed as part of the venue setup": 1,
    "For the panel discussion, the main practical points are:": 1,
    "Light background music can be played in the Studio": 1,
    "Thanks, 24 guests and a flexible 20-minute welcome are helpful details": 1,
    "Thanks, I have the requested timing as 21 January 2027 from 17:00 to 21:00": 1,
    "Thanks for your enquiry": 1,
    "Of course": 1
  },
  "ending_frequency": {
    "I’ll check the Studio for 14 October 2026 from 10:00 to 14:00 and come back to you with the next steps.": 1,
    "I can outline suitable options and costs once I have a few details:\n\n• Your preferred date, including the year, and start and finish times\n• Expected guest numbers\n• The type of offsite you are planning, such as meetings, workshops or a team social\n• Any preferred space or an idea of the rental scope you need\n\nOnce you send those over, I can give you a clearer idea of what would work.": 1,
    "I’ll check availability for 22 October 2026 from 18:00 to 23:00 and come back to you.": 1,
    "I’ll check what is realistic for both visual elements and come back with the practical options.": 1,
    "I’ll check the practical projection setup, including compatibility and any adapters needed, without holding up the rest of the planning.": 1,
    "Our kitchen is best suited to ready-made food, warming, plating and simple assembly rather than large-scale preparation, so please share their catering format and equipment needs in advance.": 1,
    "I’ll also check the facilitator options for the morning, including a shorter format if the full morning is not available.": 1,
    "I’ll check availability for 12 November 2026 from 13:00 to 16:00 and get back to you.": 1,
    "I’ll check the new date and venue request and get back to you.": 1,
    "For planning, the kitchen is best suited to ready-made food, warming, plating and simple on-site assembly rather than large-scale food production.": 1,
    "I’ll check whether there is any flexibility if you confirm quickly and come back to you on how the overall pricing may fit your budget.": 1,
    "I’ll come back to you on that.": 1,
    "I’ll use our current process rather than the previous arrangement and come back to you about the booking fee request.": 1,
    "I’ll check whether it can be safely accommodated for your investor dinner and whether WNC can include it in the rental.": 1,
    "Suppliers will also need to acknowledge the venue rules and remove their packaging and materials afterward.": 1,
    "Deliveries, unloading and setup will need to fall within the confirmed rental period unless agreed otherwise in writing.": 1,
    "Could you share the full event date including the year, the requested start and finish times, and your expected guest count?": 1,
    "I’ll also follow up on the booking fee and your request for flexibility.": 1,
    "I’ll check your request for flexibility and whether WNC can provide the 20-minute welcome.": 1,
    "A 16-person planning session is a good fit for the Studio, and I’ll check availability for 7 February 2027 from 10:00 to 13:00 and get back to you.": 1,
    "I’ll check 8 February 2027 from 14:00 to 17:00 for the same 16-person planning session and get back to you.": 1
  },
  "phrase_counts": {
    "I will check": 15,
    "I have noted": 0,
    "capacity maximum": 0,
    "booking fee": 7
  },
  "paragraph_structure_frequency_excluding_salutation": {
    "prose / prose": 8,
    "prose / bullets / prose": 1,
    "prose": 10,
    "prose / bullets": 1,
    "prose / prose / prose": 1
  },
  "pricing_sentence_frequency": {
    "The booking fee is EUR 75 excl. VAT, with VAT charged at 21%.": 1,
    "For your leadership session, the booking fee is EUR 75 excl. VAT, with VAT at 21%.": 1,
    "The current booking fee is EUR 50 excl. VAT, and I’ll check whether we can waive it for this salon as you’ve requested.": 1,
    "I’ll use our current process rather than the previous arrangement and come back to you about the booking fee request.": 1,
    "I’ll check the current booking fee, your request for flexibility, and whether WNC can provide a short facilitator-led opening.": 1,
    "I’ll also follow up on the booking fee and your request for flexibility.": 1,
    "The booking fee is EUR 75 excl. VAT, with VAT at 21%.": 1
  },
  "capacity_sentence_frequency": {}
}
```

## Before / After

Every turn is included so materially changed drafts cannot be cherry-picked. OLD is the previous autonomous program’s final output, the primary evaluation source. FINAL is this pass’s last run.

### UAT-001 / Turn 1

OLD:

```text
Studio hire for your October workshop

Hi Maya,

Thanks for the details. The Studio can accommodate 20 guests, with a maximum capacity of 40.

The booking fee is EUR 75 excl. VAT, with VAT charged at 21%. I’ll check the Studio’s availability for 14 October 2026 from 10:00 to 14:00 and come back to you with the next steps.
```

FINAL:

```text
Studio workshop on 14 October

Hi Maya,

The booking fee is EUR 75 excl. VAT, with VAT charged at 21%.

I’ll check the Studio for 14 October 2026 from 10:00 to 14:00 and come back to you with the next steps.
```

Editorial assessment: Answers the requested fee and next step directly. The brief professional greeting is adequate; no unnecessary capacity statement or disclaimer.

### UAT-002 / Turn 1

OLD:

```text
Planning your WNC offsite

Hi Jon,

Thanks for getting in touch. We’d be happy to give you a clearer idea of suitable options and costs. Could you share:

• Your preferred date, including the year, and start and finish times
• The expected number of guests
• The type of offsite you’re planning
• Whether you have a particular space in mind or would like us to suggest a rental scope

With those details, we can point you toward the most practical options.
```

FINAL:

```text
Planning your WNC offsite

Hi Jon,

Great to hear WNC was recommended for your team offsite. I can outline suitable options and costs once I have a few details:

• Your preferred date, including the year, and start and finish times
• Expected guest numbers
• The type of offsite you are planning, such as meetings, workshops or a team social
• Any preferred space or an idea of the rental scope you need

Once you send those over, I can give you a clearer idea of what would work.
```

Editorial assessment: Warm acknowledgement of the recommendation and a justified list of missing details. The closing could be lightly tightened, but no material information or policy can be removed.

### UAT-003 / Turn 1

OLD:

No accepted draft in this run.

FINAL:

```text
Awards evening on 22 October

Hi Priya,

An awards evening for 65 colleagues is suitable for exclusive use of the whole venue. I’ll check availability for 22 October 2026 from 18:00 to 23:00 and come back to you.
```

Editorial assessment: Directly answers the suitability question and leaves date availability as a future check; no unnecessary maximum or booking fee.

### UAT-004 / Turn 1

OLD:

```text
Technical setup for your product launch

Hi Elena,

Thanks for the extra details. Background music is supported with the current audio provision. For slides, basic projection may be possible with the WNC projector, but we still need to check file compatibility, any adapters required, and whether a screenless setup would work for you.

A small hologram display would be a custom technical setup, so I’ll check what can realistically be arranged.
```

FINAL:

```text
Studio launch AV setup

Hi Elena,

Background music can be played in the Studio. For the slides, basic projection may be possible with the WNC projector, but the device compatibility, adapters, file format and whether a screenless setup would suit the presentation need to be checked.

A small hologram display would be a custom technical setup. I’ll check what is realistic for both visual elements and come back with the practical options.
```

Editorial assessment: The material projection conditions are preserved, but the device-compatibility list and need to be checked phrasing still feel like policy copy rather than a personal operator reply.

### UAT-004 / Turn 2

OLD:

```text
Projection and audio for your product launch

Hi Elena,

Thanks for clarifying. We’ve noted that the hologram is optional and won’t hold up the rest of the planning.

Light music is supported. Basic projection may be possible with the WNC projector, and I’ll check compatibility, any adapter or file requirements, and whether a screenless setup would work for your slides.
```

FINAL:

```text
Projection and music setup

Hi Elena,

Understood. I’ll treat the hologram as optional and focus the planning on standard projection and light background music.

Light music can be played in the Studio. I’ll check the practical projection setup, including compatibility and any adapters needed, without holding up the rest of the planning.
```

Editorial assessment: The hologram update is acknowledged, but the extra music-capability sentence repeats a fact already answered and just mentioned in the opening. That sentence and repeated adapter detail could be removed.

### UAT-005 / Turn 1

OLD:

```text
Studio strategy session on 5 November 2026

Hi Samira,

Thanks for the details. A group of 18 is within the Studio’s maximum capacity of 40.

Your preferred caterer can bring lunch. The kitchen is best suited to ready-made food, warming, plating and simple assembly rather than large-scale preparation. The caterer will need to follow the venue and delivery rules, remove packaging and other waste, clean their work area and leave the venue as found.

I’ll check the Studio for 5 November 2026, from 09:30 to 17:00, and whether WNC can facilitate the morning.
```

FINAL:

```text
Strategy session on 5 November

Hi Samira,

An all-day Studio session for 18 people is a suitable setup. I’ll check the Studio and a WNC facilitator for 5 November 2026, from 09:30 to 17:00.

Your preferred caterer can bring lunch. Our kitchen is best suited to ready-made food, warming, plating and simple assembly rather than large-scale preparation, so please share their catering format and equipment needs in advance.
```

Editorial assessment: Answers suitability and the two practical checks, with one useful kitchen constraint. The format/equipment request is relevant to the caterer’s plans; no supplier checklist or capacity maximum.

### UAT-005 / Turn 2

OLD:

```text
Studio strategy session on 5 November

Hi Samira,

Thanks for the extra details. We’ve noted the simple buffet, the caterer’s requested 45-minute setup and your flexibility on the facilitation format.

The Studio can accommodate 18 guests, within its maximum of 40. A ready-made buffet with simple warming, plating or assembly is a good fit for the kitchen, rather than food being produced at scale on site. The caterer will need to leave the work area as found, remove packaging and other delivery waste, and acknowledge the venue rules before delivery. We’ll coordinate any setup access separately rather than assuming a window from the event start time.

I’ll check the Studio for 5 November 2026 and what facilitation option we can offer for the morning.
```

FINAL:

```text
Strategy session update

Hi Samira,

A simple buffet should work well, and I’ll factor the caterer’s 45-minute setup into the planning. I’ll also check the facilitator options for the morning, including a shorter format if the full morning is not available.
```

Editorial assessment: Naturally acknowledges the buffet, 45-minute setup and flexible facilitation. The earlier kitchen policy is not repeated, and no access window or facilitator availability is confirmed.

### UAT-006 / Turn 1

OLD:

```text
Studio planning meeting on 12 November 2026

Hi Theo,

Thanks for the details. The Studio can accommodate 16 guests, with a maximum capacity of 40. The booking fee is EUR 50 excl. VAT at 21%.

I’ll check availability for 12 November 2026 from 13:00 to 16:00 and get back to you.
```

FINAL:

```text
Studio planning meeting

Hi Theo,

The Studio is suitable for your 16-person planning meeting. I’ll check availability for 12 November 2026 from 13:00 to 16:00 and get back to you.
```

Editorial assessment: Brief suitability acknowledgement and a specific date check, without an unsolicited fee or capacity maximum.

### UAT-006 / Turn 2

OLD:

```text
Updated venue enquiry for 13 November

Hi Theo,

Thanks for the update. I’ve noted your request to change the enquiry to the entire venue for 30 guests, from 15:00 to 20:00 on 13 November 2026. I’ll check the new date and full-venue request and get back to you.
```

FINAL:

```text
Updated venue enquiry

Hi Theo,

Thanks for the update. I’ve changed the enquiry to the entire venue for 30 guests on 13 November 2026, from 15:00 to 20:00. I’ll check the new date and venue request and get back to you.
```

Editorial assessment: Accurately acknowledges the changed enquiry and next check. This exact persisted draft was recovered after a post-generation GET timed out; no new model call was made.

### UAT-007 / Turn 1

OLD:

```text
Supper club date check

Hi Lena,

Thanks for the details. A 26-person supper club is within the capacity for the entire venue.

For the date check, what full date, including the year, and start and finish times would you like? As you’re bringing an external caterer, please also share the catering format and equipment needs. The kitchen is best suited to ready-made food, warming, plating and simple on-site assembly rather than large-scale food production.
```

FINAL:

```text
Date details for your supper club

Hi Lena,

A 26-person supper club with an external caterer sounds lovely. To check the date, could you send the year for 19 November, along with your requested start and finish times?

For planning, the kitchen is best suited to ready-made food, warming, plating and simple on-site assembly rather than large-scale food production.
```

Editorial assessment: The warm timing question is sufficient for the latest message. The accurate but premature kitchen paragraph is included because catering was mentioned, not because it is needed to check the date.

### UAT-008 / Turn 1

OLD:

```text
Studio leadership session pricing

Hi Omar,

Thanks for sharing the budget context. The current booking fee is EUR 75 excl. VAT, with VAT at 21%.

I’ve noted your request for flexibility if you confirm quickly. I’ll check what may be possible, along with the likely Studio hire pricing for your 22-person session, so you can see whether it fits your budget.
```

FINAL:

```text
Studio booking fee

Hi Omar,

For your leadership session, the booking fee is EUR 75 excl. VAT, with VAT at 21%. I’ll check whether there is any flexibility if you confirm quickly and come back to you on how the overall pricing may fit your budget.
```

Editorial assessment: Answers the fee and flexibility questions in plain language, with a constructive pricing follow-up and no unsupported discount or total price.

### UAT-009 / Turn 1

OLD:

```text
Studio salon on 3 December

Hi Claire,

Thanks for getting in touch again. A salon for 18 guests is within the Studio’s maximum capacity of 40.

The current booking fee is EUR 50 excl. VAT, with VAT at 21%. We’ve noted your request to waive it again, and I’ll check this for you.
```

FINAL:

```text
Studio salon booking fee

Hi Claire,

It would be lovely to welcome you back. The current booking fee is EUR 50 excl. VAT, and I’ll check whether we can waive it for this salon as you’ve requested.

I’ll come back to you on that.
```

Editorial assessment: Warm returning-client reply states the fee and prospective waiver check. The short closing is mildly repetitive but not a material policy or information defect.

### UAT-009 / Turn 2

OLD:

```text
Studio salon booking fee

Hi Claire,

Thanks for clarifying. We’ll use our current process rather than the previous arrangement. The current booking fee is EUR 50 excl. VAT, and I’ve noted your request to waive it for this event.

A group of 18 is within the Studio’s maximum capacity of 40.
```

FINAL:

```text
Your salon request

Hi Claire,

Thanks for clarifying. I’ll use our current process rather than the previous arrangement and come back to you about the booking fee request.
```

Editorial assessment: Still echoes current process rather than previous arrangement, the precise system-like explanation the brief asked to remove. The response can simply acknowledge the clarification and give the next step.

### UAT-010 / Turn 1

OLD:

```text
Investor dinner and aerial rig

Hi David,

Thanks for the details. A 28-person dinner is within the entire venue’s maximum capacity of 110 guests.

A suspended aerial performance rig would require a specific technical review rather than being included as a standard venue capability. I’ll check whether the proposed rig can be safely accommodated and what would be involved.

Please note that any unloading, installation, or technical setup must take place within the confirmed rental period unless earlier access is approved in writing.
```

FINAL:

```text
Aerial performance rig

Hi David,

A suspended aerial performance rig would need a specific technical review rather than being assumed as part of the venue setup. I’ll check whether it can be safely accommodated for your investor dinner and whether WNC can include it in the rental.
```

Editorial assessment: The safety check is appropriate, but rather than being assumed as part of the venue setup explains internal caution in system-like language. The specific prospective check already conveys the useful meaning.

### UAT-011 / Turn 1

OLD:

```text
Practical requirements for your panel discussion

Hi Nora,

Thanks for the extra details. For 32 guests, the entire venue is within the current maximum capacity of 110.

For your setup on 15 December 2026:

• Access, unloading, deliveries and setup must take place within the rental period. Vendors may arrive up to 30 minutes early for check-in only, but cannot unload or begin work early without written approval.
• The florist, caterer and any technical supplier must acknowledge the venue rules before load-in and remove all packaging, cable waste and rental materials afterward.
• The kitchen is best suited to ready-made food, warming, plating and simple assembly rather than large-scale cooking. The caterer should share their format and equipment needs in advance and must clean their work area and leave the venue as found.
• Basic projection may be possible using the WNC projector, but device compatibility, adapters, file format and whether a screenless setup works for you will need to be checked.
• Two microphones will need to come from an external technical supplier.

Any venue visit or supplier walkthrough must also be arranged by appointment.
```

FINAL:

```text
Panel discussion practical requirements

Hi Nora,

For the panel discussion, the main practical points are:

• Projection: our projector may work for basic projection, but we will need to check device compatibility, adapters and whether projection without a screen suits your setup.
• Microphones: the two microphones will need to be provided by an external supplier.
• Catering: the kitchen is best suited to prepared food, warming, plating and simple assembly rather than large-scale production. Please share the catering format and equipment needed.
• Setup: florist and caterer deliveries, unloading and setup must take place within the confirmed rental period, so please allow for setup time in the rental schedule. Suppliers will also need to acknowledge the venue rules and remove their packaging and materials afterward.
```

Editorial assessment: Four requested topics justify bullets, and the main technical/access constraints are useful. The setup bullet still adds venue acknowledgement, packaging and repeated scheduling guidance beyond the immediate practical answer.

### UAT-011 / Turn 2

OLD:

```text
Practical setup requirements for your panel discussion

Hi Nora,

Thanks for the extra details. For an entire-venue rental, 32 guests is within the maximum capacity of 110.

Florist and caterer setup, unloading and deliveries must take place within the confirmed rental period unless agreed otherwise in writing. Suppliers may arrive up to 30 minutes early to check in, but they cannot unload or begin setup then. Both suppliers will also need to acknowledge the venue rules before load-in and remove their packaging and related waste afterward.

I’ll check the appropriate loading route and timing guidance for the caterer. The kitchen is best suited to ready-made food, warming, plating and simple assembly rather than large-scale production, and the caterer should leave its working area clean.

Basic projection may be possible using the WNC projector, subject to compatibility, adapters, file format and whether a screenless setup works for you. Two microphones would need to come from an external supplier.
```

FINAL:

```text
Supplier access details

Hi Nora,

Understood. I’ll check the florist handover requirements and the caterer’s loading route and practical arrival timing, then send those details through. Deliveries, unloading and setup will need to fall within the confirmed rental period unless agreed otherwise in writing.
```

Editorial assessment: Focuses on handover, loading and arrival. Repeating the single access boundary is useful for this new timing question; kitchen and AV policies are correctly omitted.

### UAT-012 / Turn 1

OLD:

```text
January Studio gathering details

Hi Ari,

Thanks for the extra details. Light background music is supported. For slides, WNC has a basic projector, but we will need to check compatibility, adapters and whether a screenless setup works for you.

An outside caterer is welcome. The kitchen is best for ready-made food, warming, plating and simple assembly rather than large-scale preparation. Please share the catering format and equipment needs; the caterer will also need to follow WNC’s delivery, clean-up and waste-removal requirements.

I’ll check what may be possible for a short facilitator-led opening, as well as the current booking fee and your request for flexibility.

What full date, including the year, and start and finish times are you considering? How many guests do you expect?
```

FINAL:

```text
January Studio gathering

Hi Ari,

Light background music can be played in the Studio. Basic slide projection may also be possible, depending on file and device compatibility, any adapters needed, and whether a screenless setup works for you. An outside caterer is welcome, though the kitchen is best suited to ready-made food, warming, plating and simple assembly rather than large-scale preparation.

I’ll check the current booking fee, your request for flexibility, and whether WNC can provide a short facilitator-led opening.

Could you share the full event date including the year, the requested start and finish times, and your expected guest count?
```

Editorial assessment: The content is relevant and compressed, with only one catering constraint. The opening still reads like a capability catalogue, especially can be played and the long passive technical-condition sentence.

### UAT-012 / Turn 2

OLD:

No accepted draft in this run.

FINAL:

```text
January gathering details

Hi Ari,

Thanks, 24 guests and a flexible 20-minute welcome are helpful details. Once your timing is clearer, could you share the full event date including the year, along with the requested start and finish times?

I’ll also follow up on the booking fee and your request for flexibility.
```

Editorial assessment: Warm acknowledgement of the new numbers and short welcome, asks only outstanding timing, and keeps the still-unanswered fee question in view without replaying policies.

### UAT-012 / Turn 3

OLD:

```text
January gathering details

Hi Ari,

Thanks for confirming the timing. We’ve noted 24 guests for 21 January 2027, from 17:00 to 21:00, and I’ll check the Studio and the possibility of a 20-minute facilitator-led welcome.

Light background music is supported. Basic projection may be possible with the WNC projector, depending on file compatibility, adapters and whether a screenless setup works for you.

Your caterer can use the kitchen for warming, plating and simple assembly rather than large-scale food preparation. They will need to leave the area as found, remove their packaging and waste, and acknowledge the venue rules before delivery.

The current booking fee is EUR 75 excl. VAT, with 21% VAT. We’ve also noted your request to adjust the fee.
```

FINAL:

```text
January gathering details

Hi Ari,

Thanks, I have the requested timing as 21 January 2027 from 17:00 to 21:00.

The booking fee is EUR 75 excl. VAT, with VAT at 21%. I’ll check your request for flexibility and whether WNC can provide the 20-minute welcome.
```

Editorial assessment: Acknowledges the timing and now answers the earlier fee question with the governed EUR 75 amount. Facilitator and fee-flexibility checks remain prospective; no policy repetition.

### UAT-013 / Turn 1

OLD:

```text
Studio planning session on 7 February

Hi Riley,

Thanks for the details. The Studio can accommodate your group of 16, as its current maximum capacity is 40 guests. The booking fee is EUR 50 excl. VAT, with 21% VAT.

I’ll check the Studio’s availability for your planning session on 7 February 2027 from 10:00 to 13:00.
```

FINAL:

```text
Studio planning session

Hi Riley,

Thanks for your enquiry. A 16-person planning session is a good fit for the Studio, and I’ll check availability for 7 February 2027 from 10:00 to 13:00 and get back to you.
```

Editorial assessment: Brief, specific suitability acknowledgement and date check; no unsolicited fee or maximum. The conventional opening could be more personal, but needs at most a small wording edit.

### UAT-013 / Turn 2

OLD:

```text
Planning session date change

Hi Riley,

Thanks for the update. I’ve noted your request to move the planning session to 8 February 2027 from 14:00 to 17:00, with everything else unchanged. I’ll check the new date and time and get back to you.
```

FINAL:

```text
New date for your Studio session

Hi Riley,

Of course. I’ll check 8 February 2027 from 14:00 to 17:00 for the same 16-person planning session and get back to you.
```

Editorial assessment: A natural, short offer to check the requested move; the date change is not stated as confirmed.

## Coverage Defects

UAT-003: the exact previously rejected prospective-availability candidate now passes the deterministic validator in provider-free replay. The final live scenario also persisted its draft. Narrow regression tests still reject actual confirmations and a prospective check followed by a separate confirmation.

UAT-012 turn 2: the historical non-JSON failure did not reproduce in the fresh baseline, Cycle 1 or Cycle 2. All three compound turns completed in each run. No transport repair or root-cause claim is made. The harness now retains content type, declared/actual byte length, body hash and JSON error/offset/line/column; malformed and empty responses remain errors.

Cycle 1 UAT-011 turn 1: OpenAI returned incomplete with reason max_output_tokens at the 900-token cap. Cycle 2 increased the same single-call cap to 1800; that scenario completed. Provider/model, one no-tool request and deterministic validation remain unchanged.

Cycle 2 UAT-006 turn 2: generation completed, then the result GET timed out after 90 seconds. A provider-free read recovered revision 265, tied to the exact incoming message and completed generation event. No new draft was generated. The original timeout and raw artifact are retained. Persisted coverage is 21/21; direct harness capture was 20/21.

### Exact historical UAT-003 candidate replay

This was a rejected candidate, not a historical accepted draft. It now passes the narrow provider-free validator regression; that does not approve or execute its historical action.

```text
Awards evening on 22 October 2026

Hi Priya,

Thanks for getting in touch. An awards evening for 65 guests is within the whole-venue capacity of 110.

I’ll check whether the venue is available for exclusive use on 22 October 2026 from 18:00 to 23:00. The booking fee is EUR 250 excl. VAT, with VAT at 21%.
```

Original failure: `unsupported_availability_or_confirmation`. Current failure codes: none.

## Tests

Cycle 2: **67 focused tests plus 13 subtests; 603 full-suite tests plus 160 subtests; zero failures.** The full suite includes 386 Phase 8 tests. Cycle 1 counts are recorded above. JUnit XML is retained in this directory. Tests include prospective wording versus actual confirmations, editorial-history authority isolation, revision-history stability, guidance retention and malformed-response diagnostics.

## Deployment

```json
[
  {
    "number": 1,
    "commit": "a8b9b42ab4042354ae805c18205f766b4736efd5",
    "tests": {
      "focused_passed": 53,
      "full_passed": 601,
      "phase8_passed": 384,
      "subtests_passed": 160,
      "failed": 0
    },
    "diagnosis": "Fresh baseline: correct facts but unnecessary capacity/fees, repeated follow-up policy blocks and institutional wording. Prior failed availability wording requires a narrow validator correction; reconciliation parse failure did not reproduce in this 21/21 baseline.",
    "changes": "Minimum-necessary information selection and conversational compression style profile; Deterministic editorial relevance hints without changing factual authority; Earlier case-revision draft text for editorial continuity only, included in context hash; Narrow prospective availability check exemption with independent confirmations still blocked; Non-JSON response content type, byte count, hash and parse error retained without body disclosure",
    "deploy_id": "dep-daskrvojo6nc73c84vbg",
    "deployment": "live"
  },
  {
    "number": 2,
    "commit": "1eee786f6ce271fda669b5126136bd120fd9ec90",
    "tests": {
      "focused_passed": 67,
      "focused_subtests_passed": 13,
      "full_passed": 603,
      "phase8_passed": 386,
      "subtests_passed": 160,
      "failed": 0
    },
    "diagnosis": "Same-case-revision follow-ups lost draft history and repeated policy; analytical/status wording persisted; over-compression omitted a previously requested fee when it became available. UAT-011 turn 1 reached the 900-token output cap, with no draft persisted.",
    "changes": "Select the latest draft per earlier client turn using recorded event order, capped at three turns and excluding current-turn regeneration. Preserve unresolved client questions while avoiding answered-policy repetition. Use personal acknowledgements and plain constructive language. Increase the single bounded request output cap from 900 to 1800 tokens; provider/model, one-call design and deterministic validation are unchanged.",
    "deploy_id": "dep-dasl5t3ncjis73aktd70",
    "deployment": "live"
  }
]
```

## Safety

```json
{
  "environment": "staging",
  "health": "ok",
  "outlook_posture": "configured_draft_only",
  "send_gate": "DISABLED",
  "asana_posture": "configured_but_disabled",
  "graph_mutations": 0,
  "outlook_sends": 0,
  "real_asana_executions": 0,
  "production_activity": 0,
  "approval_calls": 0,
  "execution_calls": 0,
  "execution_attempts_created": 0,
  "current_drafts_checked": 13,
  "current_revision_and_case_bindings": "PASS",
  "captured_canonical_contracts_checked": 21,
  "canonical_revision_content_context_recipient_approval_bindings": "PASS",
  "duplicate_active_internal_resolution_actions": 0,
  "frozen_scenario_and_original_evidence_hashes": "UNCHANGED",
  "provider": "openai",
  "model": "gpt-5.6-sol",
  "scope": "Synthetic @example.test staging cases only; historical recovery records were not targeted. OpenAI generation was authorized and used; no zero-OpenAI-call claim is made."
}
```

## Remaining Demonstrated Issues

1. Technical language remains formal in UAT-004/1 and UAT-012/1; UAT-009/2 still echoes current-process logic, and UAT-010/1 still explains what should not be assumed. Four robotic-phrasing flags remain.

2. Selection still includes unnecessary known information: UAT-004/2 repeats the music capability, UAT-007/1 appends kitchen rules to a date-check question, and UAT-011/1 adds later supplier requirements and repeated scheduling detail. Three unnecessary-information flags and one policy-dump flag remain.

3. Seven final drafts remain B under the stricter editorial review, exceeding the limit of two. No C or D drafts were found. Tone is 4.29/5, below the earlier published 4.53/5; the fresh same-program baseline was 4.24/5. Compression did not fully achieve the requested human voice.

4. A post-generation case-read timeout occurred. The persisted draft was recovered without generation or mutation; the latency cause was not established. The older reconciliation JSON failure was not reproduced, so its underlying cause is not claimed resolved.

## Evidence

Frozen scenarios and original evaluation artifacts are unchanged. Per-run JSON retains every accepted draft, current governed context, exact bindings, request logs and failure diagnostics. Quality grades are subjective; the human-likeness review applies the new editorial bar independently of earlier numeric scores. Rejected text is preserved separately where available.

The raw final capture is retained in `cycle2_results_raw.json`; recovered results and their provenance are in `cycle2_results.json` and `cycle2_capture_recovery_508.json`. Provider-free canonical validation covers all 21 captured revisions; the final-state audit covers all 13 current case revisions. Neither check performs approval or execution.

## Final Marker

WNC_CONVERSATIONAL_DRAFTING_REFINEMENT_INCOMPLETE
