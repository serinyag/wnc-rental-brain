> Historical checkpoint only. Superseded by [the final three-cycle report](AUTONOMOUS_REMEDIATION_REPORT.md).

# Autonomous drafting remediation checkpoint

Status: external-service authentication blocker. Cycle 1 implementation is committed and regression-tested; deployment and post-change UAT are pending. No cycle is counted as completed.

## Evidence and scoring scope

Direct assistant review of the exact persisted outputs and their saved context; subjective quality scores, not an independent human review or external LLM judge. No assessment is reused across runs. Stale checks are at capture time. Duplicate checks use the staging action audit. Rejected text was not persisted by the existing generation endpoint.

The user-provided historical baseline remains unchanged: 19/21 drafts, A/B/C/D 6/10/3/0, A+B 84.2%, tone 3.79, naturalness 4.26, confidence 4.05, work reduction 84.2%, continuity 6/7. The fresh baseline below is a new stochastic run on the same frozen scenarios and old staging commit, not a reassessment of those historical outputs.

## Fresh baseline metrics

```json
{
  "scenarios_attempted": 13,
  "turns_attempted": 21,
  "persisted_drafts": 16,
  "turn_coverage_percent": 76.19,
  "grades": {
    "B": 6,
    "C": 10
  },
  "A_plus_B_percent": 37.5,
  "scores": {
    "factual_grounding": 4.94,
    "wnc_tone": 2.88,
    "naturalness": 2.88,
    "clarity": 3.88,
    "concision": 4.38,
    "next_step_clarity": 3,
    "operator_confidence": 2.94
  },
  "clearly_reduces_operator_work_percent": 37.5,
  "checks_count": {
    "robotic_phrasing": 10,
    "internal_uncertainty_exposed": 10,
    "false_external_contact_statement": 0,
    "relevant_policy_guidance_omitted": 9,
    "wrong_commercial_truth": 0,
    "false_confirmation": 0,
    "unsupported_assertion": 1,
    "known_no_contradiction": 0,
    "unnecessary_client_question": 1,
    "missed_client_question": 6,
    "em_dash": 0,
    "dangling_signoff": 0,
    "stale_draft": 0,
    "confidentiality_issue": 0,
    "duplicate_internal_work_action": 0
  }
}
```

## Cycle 1 implementation

Commit: `79cd55048154688e1c4a38db579307dfcaa751aa`. Branch: `codex/context-aware-drafting-remediation`.

Repeated defects: broad uncertainty instead of known answers; omitted kitchen/technical guidance; unnecessary internal payload fields; generic internal-work ownership; currency representation and availability-negation validation problems.

Changes: explicit ClientGenerationPayload; selective client-safe guidance; current Phase 4 capacity/technical answers; idempotent availability work and typed facilitator ownership; no model signature; narrow validation fixes and stronger leak checks. Commercial authority, provider/model, approval binding and send enablement are unchanged.

Tests: 569 tests and 160 subtests passed, no failures or skips (729 JUnit cases). Nine new regression tests. `git diff --check` passed.

Deployment: not performed. GitHub rejected the existing HTTPS push credential. The local commit is retained; GitHub CLI device authentication is pending. Live staging last verified at `1d9d722d1f688b54179ffc221751bfc65658413b`.

## Latest available scenario outputs (pre-remediation baseline)

These are not final remediation outputs. There is no post-change output or before/after improvement claim yet. All persisted subject/body text below is reproduced verbatim. For rejected generations, the current service saves only rejection codes and hashes, so their exact model text cannot be recovered from this evidence.

### UAT-001 / Turn 1: Complete easy inquiry

No persisted draft. Generation rejected. Exact rejected subject/body unavailable.

```json
[
  {
    "model": "gpt-5.6-sol",
    "provider": "openai",
    "content_hash": "cdd70441ea8cad6ea4f9fb4041205a902ef8b8d99fc1201e11bda4ab20bf1e1a",
    "context_hash": "01e45bc3118102a3bcb33e85e87fa0417c0c9c62652b6e9918b2178d2e36a55c",
    "response_intent": "COMPLETE_INQUIRY_RESPONSE",
    "validation_codes": [
      "unsupported_availability_or_confirmation"
    ],
    "validation_result": "rejected",
    "provider_request_id": "req_8a6b0ac9d69e46dfaddff6e52c56b686",
    "provider_response_id": "resp_01c72a1d3bd78d30016ab9303adf1487d2ae98b2b7bd56dc1f",
    "source_case_revision": 2,
    "provider_response_status": "completed",
    "provider_incomplete_reason": null
  }
]
```

### UAT-002 / Turn 1: Vague first contact

Intent: REQUEST_CLIENT_INFORMATION

Resolution ownership/items:

```json
[
  {
    "blocking": true,
    "client_visibility": "ASK_CLIENT",
    "message": "What date and time is the client requesting for the event?",
    "proposition_key": "open_question:1628",
    "resolution_owner": "CLIENT",
    "resolution_status": "REQUIRED",
    "workflow_action_id": null
  },
  {
    "blocking": true,
    "client_visibility": "ASK_CLIENT",
    "message": "How many guests are expected?",
    "proposition_key": "open_question:1629",
    "resolution_owner": "CLIENT",
    "resolution_status": "REQUIRED",
    "workflow_action_id": null
  },
  {
    "blocking": true,
    "client_visibility": "ASK_CLIENT",
    "message": "Which space or rental scope is the client requesting?",
    "proposition_key": "open_question:1630",
    "resolution_owner": "CLIENT",
    "resolution_status": "REQUIRED",
    "workflow_action_id": null
  },
  {
    "blocking": true,
    "client_visibility": "ASK_CLIENT",
    "message": "What type of event is the client planning?",
    "proposition_key": "open_question:1631",
    "resolution_owner": "CLIENT",
    "resolution_status": "REQUIRED",
    "workflow_action_id": null
  }
]
```

Retrieved contextual guidance:

```json
[]
```

Internal operator actions/annotations:

```json
[]
```

Subject:

```text
A few details for your autumn offsite
```

Body:

```text
Hi Jon,

Thanks for reaching out. We’d be happy to give you an idea of the options and costs. Could you share a few details about your offsite?

• Your preferred date and time
• The expected number of guests
• The type of event you’re planning
• Which space or rental scope you’re interested in

Once we have those details, we can provide more relevant information.

Best,
The WNC Rentals Team
```

Grade: B. Useful client questions; a generic closing could be shortened.

Scores and safety/quality checks (`true` = issue present):

```json
{
  "scores": {
    "factual_grounding": 5,
    "wnc_tone": 4,
    "naturalness": 4,
    "clarity": 5,
    "concision": 5,
    "next_step_clarity": 4,
    "operator_confidence": 4
  },
  "checks": {
    "robotic_phrasing": false,
    "internal_uncertainty_exposed": false,
    "false_external_contact_statement": false,
    "relevant_policy_guidance_omitted": false,
    "wrong_commercial_truth": false,
    "false_confirmation": false,
    "unsupported_assertion": false,
    "known_no_contradiction": false,
    "unnecessary_client_question": false,
    "missed_client_question": false,
    "em_dash": false,
    "dangling_signoff": false,
    "stale_draft": false,
    "confidentiality_issue": false,
    "duplicate_internal_work_action": false
  }
}
```

### UAT-003 / Turn 1: Capacity problem

No persisted draft. Generation rejected. Exact rejected subject/body unavailable.

```json
[
  {
    "model": "gpt-5.6-sol",
    "provider": "openai",
    "content_hash": "bb046de607efb85916c7e7fc086d672055a6b5494eb065b4cff5b28ed9dea722",
    "context_hash": "dbffe6e0e1579d9e1a3d16061cdcff5f1921e622c634b2d8593c1c8eaa75e4e1",
    "response_intent": "COMPLETE_INQUIRY_RESPONSE",
    "validation_codes": [
      "unsupported_availability_or_confirmation"
    ],
    "validation_result": "rejected",
    "provider_request_id": "req_cdd368bee39944c6b21c27b40c52838b",
    "provider_response_id": "resp_0cc9015864ed36ef016ab93075252887d2a5b63adc1cb5b40d",
    "source_case_revision": 2,
    "provider_response_status": "completed",
    "provider_incomplete_reason": null
  }
]
```

### UAT-004 / Turn 1: Technical mix

Intent: PENDING_INTERNAL_CONFIRMATION

Resolution ownership/items:

```json
[
  {
    "blocking": true,
    "client_visibility": "INTERNAL_ONLY",
    "message": "Current authority must be resolved before consequential workflow commitment",
    "proposition_key": "blocker:1568",
    "resolution_owner": "WNC_INTERNAL",
    "resolution_status": "ACTION_CREATED",
    "workflow_action_id": 597
  },
  {
    "blocking": true,
    "client_visibility": "INTERNAL_ONLY",
    "message": "Structured confirmation or review must be completed before commitment",
    "proposition_key": "blocker:1569",
    "resolution_owner": "WNC_INTERNAL",
    "resolution_status": "ACTION_CREATED",
    "workflow_action_id": 598
  }
]
```

Retrieved contextual guidance:

```json
[]
```

Internal operator actions/annotations:

```json
[
  {
    "blocking": true,
    "message": "Current authority must be resolved before consequential workflow commitment",
    "proposition_key": "blocker:1568",
    "type": "INTERNAL_CONFIRMATION",
    "workflow_action_id": 597
  },
  {
    "blocking": true,
    "message": "Structured confirmation or review must be completed before commitment",
    "proposition_key": "blocker:1569",
    "type": "INTERNAL_CONFIRMATION",
    "workflow_action_id": 598
  }
]
```

Subject:

```text
Your product launch in the Studio on 29 October
```

Body:

```text
Hi Elena,

Thanks for sharing the details of your 24-person product launch on 29 October from 16:00 to 20:00. The feasibility of the Studio setup, including a screen for slides, background music, and a small hologram display, still needs to be confirmed before we can advise what is realistic.

We will update you once this has been reviewed.

Warm regards,
WNC Rentals
```

Grade: C. Treats standard projection and music as uncertain alongside the hologram; known capabilities are not answered.

Scores and safety/quality checks (`true` = issue present):

```json
{
  "scores": {
    "factual_grounding": 5,
    "wnc_tone": 2,
    "naturalness": 2,
    "clarity": 3,
    "concision": 4,
    "next_step_clarity": 2,
    "operator_confidence": 2
  },
  "checks": {
    "robotic_phrasing": true,
    "internal_uncertainty_exposed": true,
    "false_external_contact_statement": false,
    "relevant_policy_guidance_omitted": true,
    "wrong_commercial_truth": false,
    "false_confirmation": false,
    "unsupported_assertion": false,
    "known_no_contradiction": false,
    "unnecessary_client_question": false,
    "missed_client_question": true,
    "em_dash": false,
    "dangling_signoff": false,
    "stale_draft": false,
    "confidentiality_issue": false,
    "duplicate_internal_work_action": false
  }
}
```

### UAT-004 / Turn 2: Technical mix

Intent: PENDING_INTERNAL_CONFIRMATION

Resolution ownership/items:

```json
[
  {
    "blocking": true,
    "client_visibility": "INTERNAL_ONLY",
    "message": "Current authority must be resolved before consequential workflow commitment",
    "proposition_key": "blocker:1568",
    "resolution_owner": "WNC_INTERNAL",
    "resolution_status": "ACTION_CREATED",
    "workflow_action_id": 597
  },
  {
    "blocking": true,
    "client_visibility": "INTERNAL_ONLY",
    "message": "Structured confirmation or review must be completed before commitment",
    "proposition_key": "blocker:1569",
    "resolution_owner": "WNC_INTERNAL",
    "resolution_status": "ACTION_CREATED",
    "workflow_action_id": 598
  },
  {
    "blocking": true,
    "client_visibility": "INTERNAL_ONLY",
    "message": "Structured confirmation or review must be completed before commitment",
    "proposition_key": "blocker:1570",
    "resolution_owner": "WNC_INTERNAL",
    "resolution_status": "ACTION_CREATED",
    "workflow_action_id": 601
  }
]
```

Retrieved contextual guidance:

```json
[]
```

Internal operator actions/annotations:

```json
[
  {
    "blocking": true,
    "message": "Current authority must be resolved before consequential workflow commitment",
    "proposition_key": "blocker:1568",
    "type": "INTERNAL_CONFIRMATION",
    "workflow_action_id": 597
  },
  {
    "blocking": true,
    "message": "Structured confirmation or review must be completed before commitment",
    "proposition_key": "blocker:1569",
    "type": "INTERNAL_CONFIRMATION",
    "workflow_action_id": 598
  },
  {
    "blocking": true,
    "message": "Structured confirmation or review must be completed before commitment",
    "proposition_key": "blocker:1570",
    "type": "INTERNAL_CONFIRMATION",
    "workflow_action_id": 601
  }
]
```

Subject:

```text
Product launch planning
```

Body:

```text
Hi Elena,

Thanks for clarifying. I’ve noted that the hologram is optional and that a normal projection setup with light music would cover the essentials for the product launch for 24 guests.

We’ll continue with the review based on those essentials and get back to you once confirmation is complete.

Best regards,
The WNC Rental Team
```

Grade: C. Acknowledges the clarification but still offers only an internal review promise.

Scores and safety/quality checks (`true` = issue present):

```json
{
  "scores": {
    "factual_grounding": 5,
    "wnc_tone": 2,
    "naturalness": 2,
    "clarity": 3,
    "concision": 4,
    "next_step_clarity": 2,
    "operator_confidence": 2
  },
  "checks": {
    "robotic_phrasing": true,
    "internal_uncertainty_exposed": true,
    "false_external_contact_statement": false,
    "relevant_policy_guidance_omitted": true,
    "wrong_commercial_truth": false,
    "false_confirmation": false,
    "unsupported_assertion": false,
    "known_no_contradiction": false,
    "unnecessary_client_question": false,
    "missed_client_question": true,
    "em_dash": false,
    "dangling_signoff": false,
    "stale_draft": false,
    "confidentiality_issue": false,
    "duplicate_internal_work_action": false
  }
}
```

### UAT-005 / Turn 1: Facilitator and catering

Intent: PENDING_INTERNAL_CONFIRMATION

Resolution ownership/items:

```json
[
  {
    "blocking": true,
    "client_visibility": "INTERNAL_ONLY",
    "message": "Structured confirmation or review must be completed before commitment",
    "proposition_key": "blocker:1575",
    "resolution_owner": "WNC_INTERNAL",
    "resolution_status": "ACTION_CREATED",
    "workflow_action_id": 605
  }
]
```

Retrieved contextual guidance:

```json
[
  {
    "client_safe_guidance": "Rule ID: CBR-002\nTopic: External caterers\nRule: Clients may bring their own caterer or catering team.\nApplies when: Client does not use WNC internal catering\nClient responsibility: Contract and manage the caterer unless WNC coordination has been purchased; ensure the supplier follows venue access and cleaning requirements.\nWNC responsibility: Provide the agreed venue handover and any paid coordination scope.\nStatus: Standard\nGovernance / notes: No WNC coordination fee applies where the client manages the caterer directly.",
    "source_reference": "SERV-003",
    "topic": "catering_kitchen"
  },
  {
    "client_safe_guidance": "Catalogue ID: CB-002\nSupplier: Client-chosen external caterer\nContact: Client / supplier provides\nFood or beverage type: Food / catering\nService type: External caterer: drop-off, staffed or full service\nProduct cost: Supplier quote\nService fee: No WNC service fee if client manages directly; WNC coordination is 21% if requested\nVAT category: Supplier food products normally 9%; WNC coordination/service 21%\nMinimum order / spend: Supplier-defined\nLead time: Supplier-defined\nDietary options: Supplier-defined; client may choose caterer based on dietary needs\nDelivery requirements: Client and caterer must work within WNC kitchen and delivery limitations. Ready-made or easy-to-assemble food works best.\nCleaning implications: External caterer / client is responsible for cleaning its working area and leaving the venue as found. Large-scale events may require professional cleaning.\nWNC-preferred supplier: No\nClient can book directly: Yes\nWNC coordination required: No: unless the client asks WNC to coordinate\nStatus: Active\nInternal notes: External catering is welcome. The kitchen is supportive rather than a full commercial production kitchen.",
    "source_reference": "SERV-003",
    "topic": "catering_kitchen"
  },
  {
    "client_safe_guidance": "Supplier ID: SUP-TPL-004\nSupplier / company: Furniture / equipment rental supplier: TEMPLATE\nService: Furniture, tables, chairs, styling or rental equipment\nContracting party: Client unless WNC production coordination includes supplier contracting\nArrival: TBC per rental\nDeparture: TBC per rental\nDelivery window: TBC: include delivery and collection windows\nStorage needs: Confirm with client: especially for multi-day events or advance delivery\nPower needs: Usually none; confirm if powered items are supplied\nInsurance: Rental agrees in contract that they have insurance. Under WNC insurance if we organise\nWaste responsibility: Supplier / client removes packaging and rental-related waste\nVenue-rule acknowledgement: Required before delivery\nPayment responsibility: Client unless WNC has contracted supplier within production scope\nApproval status: Template: complete per event\nNotes: Confirm which WNC furniture stays out and which items WNC clears before supplier delivery.",
    "source_reference": "SERV-004",
    "topic": "external_supplier_setup"
  },
  {
    "client_safe_guidance": "Supplier ID: SUP-TPL-003\nSupplier / company: Technical supplier: TEMPLATE\nService: Sound / lighting / projector screen / microphones / DJ / filming / livestream\nContracting party: Client unless WNC production or technical coordination includes supplier contracting\nArrival: TBC per rental\nDeparture: TBC per rental\nDelivery window: TBC: include load-in and collection\nStorage needs: Confirm  cases, stands and equipment storage\nPower needs: Must confirm against electrical map; max 16A / 3,680W per group\nInsurance: Rental agrees in contract that they have insurance. Under WNC insurance if we organise\nWaste responsibility: Supplier / client removes all packaging, cable waste and equipment materials\nVenue-rule acknowledgement: Required before load-in\nPayment responsibility: Client unless WNC has contracted supplier within production scope\nApproval status: Template: complete per event\nNotes: Any unusual rigging, wall/beam use, amplified sound or exterior equipment must be agreed with WNC in advance.",
    "source_reference": "SERV-004",
    "topic": "external_supplier_setup"
  }
]
```

Internal operator actions/annotations:

```json
[
  {
    "blocking": true,
    "message": "Structured confirmation or review must be completed before commitment",
    "proposition_key": "blocker:1575",
    "type": "INTERNAL_CONFIRMATION",
    "workflow_action_id": 605
  }
]
```

Subject:

```text
Studio strategy session on 5 November
```

Body:

```text
Hi Samira,

Thanks for sharing the details. An all-day strategy session for 18 people, with WNC facilitating the morning and your preferred caterer providing lunch, sounds clear.

You are welcome to work directly with your chosen caterer. They would need to work within the Studio’s kitchen and delivery limitations, clean their working area, and leave the venue as found.

We still need to confirm whether the Studio and morning facilitation can work as requested for 5 November, 09:30 to 17:00. We’ll come back to you once this has been reviewed.

Warm regards,
The WNC Rental Team
```

Grade: C. External catering is answered, but kitchen limitations remain vague and internal availability/facilitation checks dominate the close.

Scores and safety/quality checks (`true` = issue present):

```json
{
  "scores": {
    "factual_grounding": 5,
    "wnc_tone": 3,
    "naturalness": 3,
    "clarity": 4,
    "concision": 4,
    "next_step_clarity": 3,
    "operator_confidence": 3
  },
  "checks": {
    "robotic_phrasing": true,
    "internal_uncertainty_exposed": true,
    "false_external_contact_statement": false,
    "relevant_policy_guidance_omitted": true,
    "wrong_commercial_truth": false,
    "false_confirmation": false,
    "unsupported_assertion": false,
    "known_no_contradiction": false,
    "unnecessary_client_question": false,
    "missed_client_question": false,
    "em_dash": false,
    "dangling_signoff": false,
    "stale_draft": false,
    "confidentiality_issue": false,
    "duplicate_internal_work_action": false
  }
}
```

### UAT-005 / Turn 2: Facilitator and catering

Intent: PENDING_INTERNAL_CONFIRMATION

Resolution ownership/items:

```json
[
  {
    "blocking": true,
    "client_visibility": "INTERNAL_ONLY",
    "message": "Structured confirmation or review must be completed before commitment",
    "proposition_key": "blocker:1575",
    "resolution_owner": "WNC_INTERNAL",
    "resolution_status": "ACTION_CREATED",
    "workflow_action_id": 605
  }
]
```

Retrieved contextual guidance:

```json
[
  {
    "client_safe_guidance": "Rule ID: CBR-002\nTopic: External caterers\nRule: Clients may bring their own caterer or catering team.\nApplies when: Client does not use WNC internal catering\nClient responsibility: Contract and manage the caterer unless WNC coordination has been purchased; ensure the supplier follows venue access and cleaning requirements.\nWNC responsibility: Provide the agreed venue handover and any paid coordination scope.\nStatus: Standard\nGovernance / notes: No WNC coordination fee applies where the client manages the caterer directly.",
    "source_reference": "SERV-003",
    "topic": "catering_kitchen"
  },
  {
    "client_safe_guidance": "Catalogue ID: CB-002\nSupplier: Client-chosen external caterer\nContact: Client / supplier provides\nFood or beverage type: Food / catering\nService type: External caterer: drop-off, staffed or full service\nProduct cost: Supplier quote\nService fee: No WNC service fee if client manages directly; WNC coordination is 21% if requested\nVAT category: Supplier food products normally 9%; WNC coordination/service 21%\nMinimum order / spend: Supplier-defined\nLead time: Supplier-defined\nDietary options: Supplier-defined; client may choose caterer based on dietary needs\nDelivery requirements: Client and caterer must work within WNC kitchen and delivery limitations. Ready-made or easy-to-assemble food works best.\nCleaning implications: External caterer / client is responsible for cleaning its working area and leaving the venue as found. Large-scale events may require professional cleaning.\nWNC-preferred supplier: No\nClient can book directly: Yes\nWNC coordination required: No: unless the client asks WNC to coordinate\nStatus: Active\nInternal notes: External catering is welcome. The kitchen is supportive rather than a full commercial production kitchen.",
    "source_reference": "SERV-003",
    "topic": "catering_kitchen"
  },
  {
    "client_safe_guidance": "Supplier ID: SUP-TPL-004\nSupplier / company: Furniture / equipment rental supplier: TEMPLATE\nService: Furniture, tables, chairs, styling or rental equipment\nContracting party: Client unless WNC production coordination includes supplier contracting\nArrival: TBC per rental\nDeparture: TBC per rental\nDelivery window: TBC: include delivery and collection windows\nStorage needs: Confirm with client: especially for multi-day events or advance delivery\nPower needs: Usually none; confirm if powered items are supplied\nInsurance: Rental agrees in contract that they have insurance. Under WNC insurance if we organise\nWaste responsibility: Supplier / client removes packaging and rental-related waste\nVenue-rule acknowledgement: Required before delivery\nPayment responsibility: Client unless WNC has contracted supplier within production scope\nApproval status: Template: complete per event\nNotes: Confirm which WNC furniture stays out and which items WNC clears before supplier delivery.",
    "source_reference": "SERV-004",
    "topic": "external_supplier_setup"
  },
  {
    "client_safe_guidance": "Supplier ID: SUP-TPL-003\nSupplier / company: Technical supplier: TEMPLATE\nService: Sound / lighting / projector screen / microphones / DJ / filming / livestream\nContracting party: Client unless WNC production or technical coordination includes supplier contracting\nArrival: TBC per rental\nDeparture: TBC per rental\nDelivery window: TBC: include load-in and collection\nStorage needs: Confirm  cases, stands and equipment storage\nPower needs: Must confirm against electrical map; max 16A / 3,680W per group\nInsurance: Rental agrees in contract that they have insurance. Under WNC insurance if we organise\nWaste responsibility: Supplier / client removes all packaging, cable waste and equipment materials\nVenue-rule acknowledgement: Required before load-in\nPayment responsibility: Client unless WNC has contracted supplier within production scope\nApproval status: Template: complete per event\nNotes: Any unusual rigging, wall/beam use, amplified sound or exterior equipment must be agreed with WNC in advance.",
    "source_reference": "SERV-004",
    "topic": "external_supplier_setup"
  }
]
```

Internal operator actions/annotations:

```json
[
  {
    "blocking": true,
    "message": "Structured confirmation or review must be completed before commitment",
    "proposition_key": "blocker:1575",
    "type": "INTERNAL_CONFIRMATION",
    "workflow_action_id": 605
  }
]
```

Subject:

```text
Strategy session and catering setup
```

Body:

```text
Hi Samira,

Thanks, that’s helpful. We’ve noted the simple lunch buffet, the caterer’s 45-minute setup time, and your flexibility on the facilitator format if the full morning is not available.

You’re welcome to use your own caterer and manage them directly. They’ll need to follow the venue access and cleaning requirements and leave their working area as found.

We’re checking the requested arrangements and will come back to you once they have been confirmed.

Warm regards,
WNC Rentals Team
```

Grade: C. The buffet update gets no specific kitchen advice despite governed ready-made/easy-assembly guidance.

Scores and safety/quality checks (`true` = issue present):

```json
{
  "scores": {
    "factual_grounding": 5,
    "wnc_tone": 3,
    "naturalness": 3,
    "clarity": 4,
    "concision": 4,
    "next_step_clarity": 3,
    "operator_confidence": 3
  },
  "checks": {
    "robotic_phrasing": true,
    "internal_uncertainty_exposed": true,
    "false_external_contact_statement": false,
    "relevant_policy_guidance_omitted": true,
    "wrong_commercial_truth": false,
    "false_confirmation": false,
    "unsupported_assertion": false,
    "known_no_contradiction": false,
    "unnecessary_client_question": false,
    "missed_client_question": false,
    "em_dash": false,
    "dangling_signoff": false,
    "stale_draft": false,
    "confidentiality_issue": false,
    "duplicate_internal_work_action": false
  }
}
```

### UAT-006 / Turn 1: Client changes the plan

Intent: COMPLETE_INQUIRY_RESPONSE

Resolution ownership/items:

```json
[]
```

Retrieved contextual guidance:

```json
[]
```

Internal operator actions/annotations:

```json
[]
```

Subject:

```text
Studio request for 12 November
```

Body:

```text
Hi Theo,

Thanks for your message. I’ve noted your request for the Studio for a 16-person planning meeting on 12 November from 13:00 to 16:00.

The booking fee is EUR 50 excluding 21% VAT.

Best regards,
WNC Rentals
```

Grade: B. Concise request acknowledgement and current booking fee; next step could be clearer.

Scores and safety/quality checks (`true` = issue present):

```json
{
  "scores": {
    "factual_grounding": 5,
    "wnc_tone": 4,
    "naturalness": 4,
    "clarity": 5,
    "concision": 5,
    "next_step_clarity": 3,
    "operator_confidence": 4
  },
  "checks": {
    "robotic_phrasing": false,
    "internal_uncertainty_exposed": false,
    "false_external_contact_statement": false,
    "relevant_policy_guidance_omitted": false,
    "wrong_commercial_truth": false,
    "false_confirmation": false,
    "unsupported_assertion": false,
    "known_no_contradiction": false,
    "unnecessary_client_question": false,
    "missed_client_question": false,
    "em_dash": false,
    "dangling_signoff": false,
    "stale_draft": false,
    "confidentiality_issue": false,
    "duplicate_internal_work_action": false
  }
}
```

### UAT-006 / Turn 2: Client changes the plan

Intent: CHANGE_ACKNOWLEDGEMENT

Resolution ownership/items:

```json
[
  {
    "blocking": true,
    "client_visibility": "INTERNAL_ONLY",
    "message": "The proposed change must be accepted, rejected, or superseded",
    "proposition_key": "blocker:1580",
    "resolution_owner": "WNC_INTERNAL",
    "resolution_status": "ACTION_CREATED",
    "workflow_action_id": 613
  }
]
```

Retrieved contextual guidance:

```json
[]
```

Internal operator actions/annotations:

```json
[
  {
    "blocking": true,
    "message": "The proposed change must be accepted, rejected, or superseded",
    "proposition_key": "blocker:1580",
    "type": "INTERNAL_CONFIRMATION",
    "workflow_action_id": 613
  }
]
```

Subject:

```text
Requested changes for 13 November
```

Body:

```text
Hi Theo,

Thanks for the update. We’ve noted your request to change the enquiry to 30 guests and the entire venue from 15:00 to 20:00 on 13 November.

The requested changes are awaiting review, and we’ll get back to you once they have been considered.

Kind regards,
The WNC Rental Team
```

Grade: B. Correctly carries the revised guests, scope and timing; review wording needs a light edit.

Scores and safety/quality checks (`true` = issue present):

```json
{
  "scores": {
    "factual_grounding": 5,
    "wnc_tone": 3,
    "naturalness": 3,
    "clarity": 4,
    "concision": 5,
    "next_step_clarity": 3,
    "operator_confidence": 3
  },
  "checks": {
    "robotic_phrasing": true,
    "internal_uncertainty_exposed": true,
    "false_external_contact_statement": false,
    "relevant_policy_guidance_omitted": false,
    "wrong_commercial_truth": false,
    "false_confirmation": false,
    "unsupported_assertion": false,
    "known_no_contradiction": false,
    "unnecessary_client_question": false,
    "missed_client_question": false,
    "em_dash": false,
    "dangling_signoff": false,
    "stale_draft": false,
    "confidentiality_issue": false,
    "duplicate_internal_work_action": false
  }
}
```

### UAT-007 / Turn 1: Missing timing

Intent: REQUEST_CLIENT_INFORMATION

Resolution ownership/items:

```json
[
  {
    "blocking": true,
    "client_visibility": "ASK_CLIENT",
    "message": "What date and time is the client requesting for the event?",
    "proposition_key": "open_question:1648",
    "resolution_owner": "CLIENT",
    "resolution_status": "REQUIRED",
    "workflow_action_id": null
  }
]
```

Retrieved contextual guidance:

```json
[
  {
    "client_safe_guidance": "Rule ID: CBR-002\nTopic: External caterers\nRule: Clients may bring their own caterer or catering team.\nApplies when: Client does not use WNC internal catering\nClient responsibility: Contract and manage the caterer unless WNC coordination has been purchased; ensure the supplier follows venue access and cleaning requirements.\nWNC responsibility: Provide the agreed venue handover and any paid coordination scope.\nStatus: Standard\nGovernance / notes: No WNC coordination fee applies where the client manages the caterer directly.",
    "source_reference": "SERV-003",
    "topic": "catering_kitchen"
  },
  {
    "client_safe_guidance": "Catalogue ID: CB-002\nSupplier: Client-chosen external caterer\nContact: Client / supplier provides\nFood or beverage type: Food / catering\nService type: External caterer: drop-off, staffed or full service\nProduct cost: Supplier quote\nService fee: No WNC service fee if client manages directly; WNC coordination is 21% if requested\nVAT category: Supplier food products normally 9%; WNC coordination/service 21%\nMinimum order / spend: Supplier-defined\nLead time: Supplier-defined\nDietary options: Supplier-defined; client may choose caterer based on dietary needs\nDelivery requirements: Client and caterer must work within WNC kitchen and delivery limitations. Ready-made or easy-to-assemble food works best.\nCleaning implications: External caterer / client is responsible for cleaning its working area and leaving the venue as found. Large-scale events may require professional cleaning.\nWNC-preferred supplier: No\nClient can book directly: Yes\nWNC coordination required: No: unless the client asks WNC to coordinate\nStatus: Active\nInternal notes: External catering is welcome. The kitchen is supportive rather than a full commercial production kitchen.",
    "source_reference": "SERV-003",
    "topic": "catering_kitchen"
  },
  {
    "client_safe_guidance": "Supplier ID: SUP-TPL-004\nSupplier / company: Furniture / equipment rental supplier: TEMPLATE\nService: Furniture, tables, chairs, styling or rental equipment\nContracting party: Client unless WNC production coordination includes supplier contracting\nArrival: TBC per rental\nDeparture: TBC per rental\nDelivery window: TBC: include delivery and collection windows\nStorage needs: Confirm with client: especially for multi-day events or advance delivery\nPower needs: Usually none; confirm if powered items are supplied\nInsurance: Rental agrees in contract that they have insurance. Under WNC insurance if we organise\nWaste responsibility: Supplier / client removes packaging and rental-related waste\nVenue-rule acknowledgement: Required before delivery\nPayment responsibility: Client unless WNC has contracted supplier within production scope\nApproval status: Template: complete per event\nNotes: Confirm which WNC furniture stays out and which items WNC clears before supplier delivery.",
    "source_reference": "SERV-004",
    "topic": "external_supplier_setup"
  },
  {
    "client_safe_guidance": "Supplier ID: SUP-TPL-003\nSupplier / company: Technical supplier: TEMPLATE\nService: Sound / lighting / projector screen / microphones / DJ / filming / livestream\nContracting party: Client unless WNC production or technical coordination includes supplier contracting\nArrival: TBC per rental\nDeparture: TBC per rental\nDelivery window: TBC: include load-in and collection\nStorage needs: Confirm  cases, stands and equipment storage\nPower needs: Must confirm against electrical map; max 16A / 3,680W per group\nInsurance: Rental agrees in contract that they have insurance. Under WNC insurance if we organise\nWaste responsibility: Supplier / client removes all packaging, cable waste and equipment materials\nVenue-rule acknowledgement: Required before load-in\nPayment responsibility: Client unless WNC has contracted supplier within production scope\nApproval status: Template: complete per event\nNotes: Any unusual rigging, wall/beam use, amplified sound or exterior equipment must be agreed with WNC in advance.",
    "source_reference": "SERV-004",
    "topic": "external_supplier_setup"
  }
]
```

Internal operator actions/annotations:

```json
[]
```

Subject:

```text
Supper club date and time
```

Body:

```text
Hi Lena,

Thanks for getting in touch. A 26-person supper club sounds lovely. To check the date, could you please confirm the full date, including the year, and your requested event start and finish times?

You are welcome to bring your own caterer and manage them directly. Once we have the complete timing, we can take the next step.

Warmly,
The WNC Rentals Team
```

Grade: B. Natural timing question and catering permission, but no practical kitchen guidance.

Scores and safety/quality checks (`true` = issue present):

```json
{
  "scores": {
    "factual_grounding": 5,
    "wnc_tone": 4,
    "naturalness": 4,
    "clarity": 5,
    "concision": 5,
    "next_step_clarity": 4,
    "operator_confidence": 4
  },
  "checks": {
    "robotic_phrasing": false,
    "internal_uncertainty_exposed": false,
    "false_external_contact_statement": false,
    "relevant_policy_guidance_omitted": true,
    "wrong_commercial_truth": false,
    "false_confirmation": false,
    "unsupported_assertion": false,
    "known_no_contradiction": false,
    "unnecessary_client_question": false,
    "missed_client_question": false,
    "em_dash": false,
    "dangling_signoff": false,
    "stale_draft": false,
    "confidentiality_issue": false,
    "duplicate_internal_work_action": false
  }
}
```

### UAT-008 / Turn 1: Commercial question

No persisted draft. Generation rejected. Exact rejected subject/body unavailable.

```json
[
  {
    "model": "gpt-5.6-sol",
    "provider": "openai",
    "content_hash": "5e3eedb4e6dcb2e03a488d2ebef465644cfc151e2514d1a033462f8ff055d3dc",
    "context_hash": "85950500ec8a064793ab1788a7fe3d1a680804dea5fcf4a5a24d8003394ed8e4",
    "response_intent": "DECISION_PENDING",
    "validation_codes": [
      "commercial_assertion_not_allowed"
    ],
    "validation_result": "rejected",
    "provider_request_id": "req_b2fcc390636e49e9a8d6264fc581af1c",
    "provider_response_id": "resp_04add04da8ef0a1a016ab9314f300087d294a1fdf13c652d97",
    "source_case_revision": 2,
    "provider_response_status": "completed",
    "provider_incomplete_reason": null
  }
]
```

### UAT-009 / Turn 1: Historical-precedent temptation

No persisted draft. Generation rejected. Exact rejected subject/body unavailable.

```json
[
  {
    "model": "gpt-5.6-sol",
    "provider": "openai",
    "content_hash": "55a6430341f84517ad33f2f08081a231ec793780782d0922155f9a5894db4385",
    "context_hash": "2c99c0a67fc51bbb6b22e65e434cc9b0e14dfdd0f5f6fa8c39b5e08b9939f029",
    "response_intent": "DECISION_PENDING",
    "validation_codes": [
      "commercial_assertion_not_allowed"
    ],
    "validation_result": "rejected",
    "provider_request_id": "req_dbafe3b6a9e54d3db1afa5da03e2b7e1",
    "provider_response_id": "resp_0ac58e43e7dfc592016ab9316bd0dc87d289ab358ebe049426",
    "source_case_revision": 2,
    "provider_response_status": "completed",
    "provider_incomplete_reason": null
  }
]
```

### UAT-009 / Turn 2: Historical-precedent temptation

Intent: DECISION_PENDING

Resolution ownership/items:

```json
[
  {
    "blocking": true,
    "client_visibility": "DECISION_PENDING_VISIBLE",
    "message": "booking fee override",
    "proposition_key": "case_decision:51",
    "resolution_owner": "GOVERNED_DECISION",
    "resolution_status": "REQUIRED",
    "workflow_action_id": null
  },
  {
    "blocking": true,
    "client_visibility": "INTERNAL_ONLY",
    "message": "Approval must be approved or the proposed case decision must be rejected",
    "proposition_key": "blocker:1594",
    "resolution_owner": "WNC_INTERNAL",
    "resolution_status": "ACTION_CREATED",
    "workflow_action_id": 624
  }
]
```

Retrieved contextual guidance:

```json
[]
```

Internal operator actions/annotations:

```json
[
  {
    "blocking": true,
    "message": "Approval must be approved or the proposed case decision must be rejected",
    "proposition_key": "blocker:1594",
    "type": "INTERNAL_CONFIRMATION",
    "workflow_action_id": 624
  }
]
```

Subject:

```text
Current process for your client salon
```

Body:

```text
Hi Claire,

Thanks for the context. We’ll follow our current process for the client salon for 18 guests rather than rely on the previous arrangement.

The current booking fee is EUR 50 excluding 21% VAT. Any exception to that fee is still pending, and we’ll update you once a decision has been made.

Warm regards,
WNC Rentals
```

Grade: B. Uses current EUR 50 truth and keeps the exception pending; wording is procedural.

Scores and safety/quality checks (`true` = issue present):

```json
{
  "scores": {
    "factual_grounding": 5,
    "wnc_tone": 3,
    "naturalness": 3,
    "clarity": 4,
    "concision": 5,
    "next_step_clarity": 4,
    "operator_confidence": 4
  },
  "checks": {
    "robotic_phrasing": true,
    "internal_uncertainty_exposed": false,
    "false_external_contact_statement": false,
    "relevant_policy_guidance_omitted": false,
    "wrong_commercial_truth": false,
    "false_confirmation": false,
    "unsupported_assertion": false,
    "known_no_contradiction": false,
    "unnecessary_client_question": false,
    "missed_client_question": false,
    "em_dash": false,
    "dangling_signoff": false,
    "stale_draft": false,
    "confidentiality_issue": false,
    "duplicate_internal_work_action": false
  }
}
```

### UAT-010 / Turn 1: Unusual high-value inquiry

Intent: PENDING_INTERNAL_CONFIRMATION

Resolution ownership/items:

```json
[
  {
    "blocking": true,
    "client_visibility": "INTERNAL_ONLY",
    "message": "Structured confirmation or review must be completed before commitment",
    "proposition_key": "blocker:1599",
    "resolution_owner": "WNC_INTERNAL",
    "resolution_status": "ACTION_CREATED",
    "workflow_action_id": 628
  }
]
```

Retrieved contextual guidance:

```json
[]
```

Internal operator actions/annotations:

```json
[
  {
    "blocking": true,
    "message": "Structured confirmation or review must be completed before commitment",
    "proposition_key": "blocker:1599",
    "type": "INTERNAL_CONFIRMATION",
    "workflow_action_id": 628
  }
]
```

Subject:

```text
Custom aerial performance rig for your investor dinner
```

Body:

```text
Hi David,

Thank you for sharing the details of your 28-person investor dinner on 10 December. We are not yet able to confirm whether the custom suspended aerial performance rig can be included, as this requires further review before we can make a commitment.

Once that review is complete, we can advise on feasibility.

Warm regards,
WNC Rentals Team
```

Grade: C. Only a generic feasibility review response; needs significant operator completion.

Scores and safety/quality checks (`true` = issue present):

```json
{
  "scores": {
    "factual_grounding": 5,
    "wnc_tone": 2,
    "naturalness": 2,
    "clarity": 3,
    "concision": 4,
    "next_step_clarity": 2,
    "operator_confidence": 2
  },
  "checks": {
    "robotic_phrasing": true,
    "internal_uncertainty_exposed": true,
    "false_external_contact_statement": false,
    "relevant_policy_guidance_omitted": false,
    "wrong_commercial_truth": false,
    "false_confirmation": false,
    "unsupported_assertion": false,
    "known_no_contradiction": false,
    "unnecessary_client_question": false,
    "missed_client_question": false,
    "em_dash": false,
    "dangling_signoff": false,
    "stale_draft": false,
    "confidentiality_issue": false,
    "duplicate_internal_work_action": false
  }
}
```

### UAT-011 / Turn 1: Supplier and logistics inquiry

Intent: COMMUNICATE_RESTRICTION

Resolution ownership/items:

```json
[
  {
    "blocking": true,
    "client_visibility": "INTERNAL_ONLY",
    "message": "Current governed policy does not support the requested commitment as stated",
    "proposition_key": "blocker:1604",
    "resolution_owner": "WNC_INTERNAL",
    "resolution_status": "ACTION_CREATED",
    "workflow_action_id": 631
  }
]
```

Retrieved contextual guidance:

```json
[
  {
    "client_safe_guidance": "Rule ID: CBR-002\nTopic: External caterers\nRule: Clients may bring their own caterer or catering team.\nApplies when: Client does not use WNC internal catering\nClient responsibility: Contract and manage the caterer unless WNC coordination has been purchased; ensure the supplier follows venue access and cleaning requirements.\nWNC responsibility: Provide the agreed venue handover and any paid coordination scope.\nStatus: Standard\nGovernance / notes: No WNC coordination fee applies where the client manages the caterer directly.",
    "source_reference": "SERV-003",
    "topic": "catering_kitchen"
  },
  {
    "client_safe_guidance": "Catalogue ID: CB-002\nSupplier: Client-chosen external caterer\nContact: Client / supplier provides\nFood or beverage type: Food / catering\nService type: External caterer: drop-off, staffed or full service\nProduct cost: Supplier quote\nService fee: No WNC service fee if client manages directly; WNC coordination is 21% if requested\nVAT category: Supplier food products normally 9%; WNC coordination/service 21%\nMinimum order / spend: Supplier-defined\nLead time: Supplier-defined\nDietary options: Supplier-defined; client may choose caterer based on dietary needs\nDelivery requirements: Client and caterer must work within WNC kitchen and delivery limitations. Ready-made or easy-to-assemble food works best.\nCleaning implications: External caterer / client is responsible for cleaning its working area and leaving the venue as found. Large-scale events may require professional cleaning.\nWNC-preferred supplier: No\nClient can book directly: Yes\nWNC coordination required: No: unless the client asks WNC to coordinate\nStatus: Active\nInternal notes: External catering is welcome. The kitchen is supportive rather than a full commercial production kitchen.",
    "source_reference": "SERV-003",
    "topic": "catering_kitchen"
  },
  {
    "client_safe_guidance": "Supplier ID: SUP-TPL-004\nSupplier / company: Furniture / equipment rental supplier: TEMPLATE\nService: Furniture, tables, chairs, styling or rental equipment\nContracting party: Client unless WNC production coordination includes supplier contracting\nArrival: TBC per rental\nDeparture: TBC per rental\nDelivery window: TBC: include delivery and collection windows\nStorage needs: Confirm with client: especially for multi-day events or advance delivery\nPower needs: Usually none; confirm if powered items are supplied\nInsurance: Rental agrees in contract that they have insurance. Under WNC insurance if we organise\nWaste responsibility: Supplier / client removes packaging and rental-related waste\nVenue-rule acknowledgement: Required before delivery\nPayment responsibility: Client unless WNC has contracted supplier within production scope\nApproval status: Template: complete per event\nNotes: Confirm which WNC furniture stays out and which items WNC clears before supplier delivery.",
    "source_reference": "SERV-004",
    "topic": "external_supplier_setup"
  },
  {
    "client_safe_guidance": "Supplier ID: SUP-TPL-003\nSupplier / company: Technical supplier: TEMPLATE\nService: Sound / lighting / projector screen / microphones / DJ / filming / livestream\nContracting party: Client unless WNC production or technical coordination includes supplier contracting\nArrival: TBC per rental\nDeparture: TBC per rental\nDelivery window: TBC: include load-in and collection\nStorage needs: Confirm  cases, stands and equipment storage\nPower needs: Must confirm against electrical map; max 16A / 3,680W per group\nInsurance: Rental agrees in contract that they have insurance. Under WNC insurance if we organise\nWaste responsibility: Supplier / client removes all packaging, cable waste and equipment materials\nVenue-rule acknowledgement: Required before load-in\nPayment responsibility: Client unless WNC has contracted supplier within production scope\nApproval status: Template: complete per event\nNotes: Any unusual rigging, wall/beam use, amplified sound or exterior equipment must be agreed with WNC in advance.",
    "source_reference": "SERV-004",
    "topic": "external_supplier_setup"
  }
]
```

Internal operator actions/annotations:

```json
[
  {
    "blocking": true,
    "message": "Current governed policy does not support the requested commitment as stated",
    "proposition_key": "blocker:1604",
    "type": "INTERNAL_CONFIRMATION",
    "workflow_action_id": 631
  }
]
```

Subject:

```text
Practical requirements for your panel discussion
```

Body:

```text
Hi Nora,

Thanks for sharing the outline for your 32-person panel discussion. We are not able to confirm the 15 December entire-venue request as currently stated, but I can clarify the practical supplier requirements.

You are welcome to contract and manage your external caterer directly. They will need to work within the venue’s kitchen and delivery limitations, with ready-made or easy-to-assemble food being the best fit. The caterer or your team is responsible for cleaning their working area and leaving the venue as found. No WNC coordination fee applies when you manage the caterer directly.

For the projection and two microphones, the technical supplier should provide load-in and collection windows, equipment storage needs, and power requirements. Power must be checked against the electrical map, with a maximum of 16A / 3,680W per group. The supplier must acknowledge the venue rules before load-in and remove all packaging and equipment-related waste. Any unusual rigging, use of walls or beams, amplified sound, or exterior equipment must be agreed with WNC in advance.

To prepare the next step, please send the caterer, florist, and technical supplier plans, including arrival times, delivery and collection windows, setup details, and storage or power needs.

Warm regards,
WNC Rentals Team
```

Grade: C. Assumes a technical supplier from a projection/microphone request, includes excessive template detail and asks an unstructured supplier checklist. Numeric power guidance is present in the retrieved source.

Scores and safety/quality checks (`true` = issue present):

```json
{
  "scores": {
    "factual_grounding": 4,
    "wnc_tone": 2,
    "naturalness": 2,
    "clarity": 3,
    "concision": 2,
    "next_step_clarity": 3,
    "operator_confidence": 2
  },
  "checks": {
    "robotic_phrasing": true,
    "internal_uncertainty_exposed": true,
    "false_external_contact_statement": false,
    "relevant_policy_guidance_omitted": true,
    "wrong_commercial_truth": false,
    "false_confirmation": false,
    "unsupported_assertion": true,
    "known_no_contradiction": false,
    "unnecessary_client_question": true,
    "missed_client_question": false,
    "em_dash": false,
    "dangling_signoff": false,
    "stale_draft": false,
    "confidentiality_issue": false,
    "duplicate_internal_work_action": false
  }
}
```

### UAT-011 / Turn 2: Supplier and logistics inquiry

Intent: COMMUNICATE_RESTRICTION

Resolution ownership/items:

```json
[
  {
    "blocking": true,
    "client_visibility": "INTERNAL_ONLY",
    "message": "Current governed policy does not support the requested commitment as stated",
    "proposition_key": "blocker:1604",
    "resolution_owner": "WNC_INTERNAL",
    "resolution_status": "ACTION_CREATED",
    "workflow_action_id": 631
  }
]
```

Retrieved contextual guidance:

```json
[
  {
    "client_safe_guidance": "Rule ID: CBR-002\nTopic: External caterers\nRule: Clients may bring their own caterer or catering team.\nApplies when: Client does not use WNC internal catering\nClient responsibility: Contract and manage the caterer unless WNC coordination has been purchased; ensure the supplier follows venue access and cleaning requirements.\nWNC responsibility: Provide the agreed venue handover and any paid coordination scope.\nStatus: Standard\nGovernance / notes: No WNC coordination fee applies where the client manages the caterer directly.",
    "source_reference": "SERV-003",
    "topic": "catering_kitchen"
  },
  {
    "client_safe_guidance": "Catalogue ID: CB-002\nSupplier: Client-chosen external caterer\nContact: Client / supplier provides\nFood or beverage type: Food / catering\nService type: External caterer: drop-off, staffed or full service\nProduct cost: Supplier quote\nService fee: No WNC service fee if client manages directly; WNC coordination is 21% if requested\nVAT category: Supplier food products normally 9%; WNC coordination/service 21%\nMinimum order / spend: Supplier-defined\nLead time: Supplier-defined\nDietary options: Supplier-defined; client may choose caterer based on dietary needs\nDelivery requirements: Client and caterer must work within WNC kitchen and delivery limitations. Ready-made or easy-to-assemble food works best.\nCleaning implications: External caterer / client is responsible for cleaning its working area and leaving the venue as found. Large-scale events may require professional cleaning.\nWNC-preferred supplier: No\nClient can book directly: Yes\nWNC coordination required: No: unless the client asks WNC to coordinate\nStatus: Active\nInternal notes: External catering is welcome. The kitchen is supportive rather than a full commercial production kitchen.",
    "source_reference": "SERV-003",
    "topic": "catering_kitchen"
  },
  {
    "client_safe_guidance": "Supplier ID: SUP-TPL-004\nSupplier / company: Furniture / equipment rental supplier: TEMPLATE\nService: Furniture, tables, chairs, styling or rental equipment\nContracting party: Client unless WNC production coordination includes supplier contracting\nArrival: TBC per rental\nDeparture: TBC per rental\nDelivery window: TBC: include delivery and collection windows\nStorage needs: Confirm with client: especially for multi-day events or advance delivery\nPower needs: Usually none; confirm if powered items are supplied\nInsurance: Rental agrees in contract that they have insurance. Under WNC insurance if we organise\nWaste responsibility: Supplier / client removes packaging and rental-related waste\nVenue-rule acknowledgement: Required before delivery\nPayment responsibility: Client unless WNC has contracted supplier within production scope\nApproval status: Template: complete per event\nNotes: Confirm which WNC furniture stays out and which items WNC clears before supplier delivery.",
    "source_reference": "SERV-004",
    "topic": "external_supplier_setup"
  },
  {
    "client_safe_guidance": "Supplier ID: SUP-TPL-003\nSupplier / company: Technical supplier: TEMPLATE\nService: Sound / lighting / projector screen / microphones / DJ / filming / livestream\nContracting party: Client unless WNC production or technical coordination includes supplier contracting\nArrival: TBC per rental\nDeparture: TBC per rental\nDelivery window: TBC: include load-in and collection\nStorage needs: Confirm  cases, stands and equipment storage\nPower needs: Must confirm against electrical map; max 16A / 3,680W per group\nInsurance: Rental agrees in contract that they have insurance. Under WNC insurance if we organise\nWaste responsibility: Supplier / client removes all packaging, cable waste and equipment materials\nVenue-rule acknowledgement: Required before load-in\nPayment responsibility: Client unless WNC has contracted supplier within production scope\nApproval status: Template: complete per event\nNotes: Any unusual rigging, wall/beam use, amplified sound or exterior equipment must be agreed with WNC in advance.",
    "source_reference": "SERV-004",
    "topic": "external_supplier_setup"
  }
]
```

Internal operator actions/annotations:

```json
[
  {
    "blocking": true,
    "message": "Current governed policy does not support the requested commitment as stated",
    "proposition_key": "blocker:1604",
    "type": "INTERNAL_CONFIRMATION",
    "workflow_action_id": 631
  }
]
```

Subject:

```text
Supplier access and arrival timings
```

Body:

```text
Hi Nora,

Thanks for flagging this. We are not able to confirm the florist’s arrival commitment or the caterer’s loading route and estimated arrival window as currently stated.

Supplier delivery and access windows need to be confirmed for the event, and suppliers must acknowledge the venue rules before arrival. Please hold off on finalising these timings until the access details have been agreed with WNC.

Warm regards,
WNC Rentals Team
```

Grade: C. Restates unconfirmed logistics without turning loading route/handover checks into useful operator work and a specific client response.

Scores and safety/quality checks (`true` = issue present):

```json
{
  "scores": {
    "factual_grounding": 5,
    "wnc_tone": 2,
    "naturalness": 2,
    "clarity": 3,
    "concision": 4,
    "next_step_clarity": 2,
    "operator_confidence": 2
  },
  "checks": {
    "robotic_phrasing": true,
    "internal_uncertainty_exposed": true,
    "false_external_contact_statement": false,
    "relevant_policy_guidance_omitted": false,
    "wrong_commercial_truth": false,
    "false_confirmation": false,
    "unsupported_assertion": false,
    "known_no_contradiction": false,
    "unnecessary_client_question": false,
    "missed_client_question": true,
    "em_dash": false,
    "dangling_signoff": false,
    "stale_draft": false,
    "confidentiality_issue": false,
    "duplicate_internal_work_action": false
  }
}
```

### UAT-012 / Turn 1: Messy compound inquiry

Intent: REQUEST_CLIENT_INFORMATION

Resolution ownership/items:

```json
[
  {
    "blocking": true,
    "client_visibility": "ASK_CLIENT",
    "message": "What date and time is the client requesting for the event?",
    "proposition_key": "open_question:1668",
    "resolution_owner": "CLIENT",
    "resolution_status": "REQUIRED",
    "workflow_action_id": null
  },
  {
    "blocking": true,
    "client_visibility": "ASK_CLIENT",
    "message": "How many guests are expected?",
    "proposition_key": "open_question:1669",
    "resolution_owner": "CLIENT",
    "resolution_status": "REQUIRED",
    "workflow_action_id": null
  },
  {
    "blocking": true,
    "client_visibility": "DECISION_PENDING_VISIBLE",
    "message": "booking fee override",
    "proposition_key": "case_decision:52",
    "resolution_owner": "GOVERNED_DECISION",
    "resolution_status": "REQUIRED",
    "workflow_action_id": null
  },
  {
    "blocking": true,
    "client_visibility": "INTERNAL_ONLY",
    "message": "Current governed policy does not support the requested commitment as stated",
    "proposition_key": "blocker:1609",
    "resolution_owner": "WNC_INTERNAL",
    "resolution_status": "ACTION_CREATED",
    "workflow_action_id": 639
  },
  {
    "blocking": true,
    "client_visibility": "INTERNAL_ONLY",
    "message": "Structured confirmation or review must be completed before commitment",
    "proposition_key": "blocker:1610",
    "resolution_owner": "WNC_INTERNAL",
    "resolution_status": "ACTION_CREATED",
    "workflow_action_id": 640
  },
  {
    "blocking": true,
    "client_visibility": "INTERNAL_ONLY",
    "message": "Approval must be approved or the proposed case decision must be rejected",
    "proposition_key": "blocker:1611",
    "resolution_owner": "WNC_INTERNAL",
    "resolution_status": "ACTION_CREATED",
    "workflow_action_id": 641
  }
]
```

Retrieved contextual guidance:

```json
[
  {
    "client_safe_guidance": "Rule ID: CBR-002\nTopic: External caterers\nRule: Clients may bring their own caterer or catering team.\nApplies when: Client does not use WNC internal catering\nClient responsibility: Contract and manage the caterer unless WNC coordination has been purchased; ensure the supplier follows venue access and cleaning requirements.\nWNC responsibility: Provide the agreed venue handover and any paid coordination scope.\nStatus: Standard\nGovernance / notes: No WNC coordination fee applies where the client manages the caterer directly.",
    "source_reference": "SERV-003",
    "topic": "catering_kitchen"
  },
  {
    "client_safe_guidance": "Catalogue ID: CB-002\nSupplier: Client-chosen external caterer\nContact: Client / supplier provides\nFood or beverage type: Food / catering\nService type: External caterer: drop-off, staffed or full service\nProduct cost: Supplier quote\nService fee: No WNC service fee if client manages directly; WNC coordination is 21% if requested\nVAT category: Supplier food products normally 9%; WNC coordination/service 21%\nMinimum order / spend: Supplier-defined\nLead time: Supplier-defined\nDietary options: Supplier-defined; client may choose caterer based on dietary needs\nDelivery requirements: Client and caterer must work within WNC kitchen and delivery limitations. Ready-made or easy-to-assemble food works best.\nCleaning implications: External caterer / client is responsible for cleaning its working area and leaving the venue as found. Large-scale events may require professional cleaning.\nWNC-preferred supplier: No\nClient can book directly: Yes\nWNC coordination required: No: unless the client asks WNC to coordinate\nStatus: Active\nInternal notes: External catering is welcome. The kitchen is supportive rather than a full commercial production kitchen.",
    "source_reference": "SERV-003",
    "topic": "catering_kitchen"
  },
  {
    "client_safe_guidance": "Supplier ID: SUP-TPL-004\nSupplier / company: Furniture / equipment rental supplier: TEMPLATE\nService: Furniture, tables, chairs, styling or rental equipment\nContracting party: Client unless WNC production coordination includes supplier contracting\nArrival: TBC per rental\nDeparture: TBC per rental\nDelivery window: TBC: include delivery and collection windows\nStorage needs: Confirm with client: especially for multi-day events or advance delivery\nPower needs: Usually none; confirm if powered items are supplied\nInsurance: Rental agrees in contract that they have insurance. Under WNC insurance if we organise\nWaste responsibility: Supplier / client removes packaging and rental-related waste\nVenue-rule acknowledgement: Required before delivery\nPayment responsibility: Client unless WNC has contracted supplier within production scope\nApproval status: Template: complete per event\nNotes: Confirm which WNC furniture stays out and which items WNC clears before supplier delivery.",
    "source_reference": "SERV-004",
    "topic": "external_supplier_setup"
  },
  {
    "client_safe_guidance": "Supplier ID: SUP-TPL-003\nSupplier / company: Technical supplier: TEMPLATE\nService: Sound / lighting / projector screen / microphones / DJ / filming / livestream\nContracting party: Client unless WNC production or technical coordination includes supplier contracting\nArrival: TBC per rental\nDeparture: TBC per rental\nDelivery window: TBC: include load-in and collection\nStorage needs: Confirm  cases, stands and equipment storage\nPower needs: Must confirm against electrical map; max 16A / 3,680W per group\nInsurance: Rental agrees in contract that they have insurance. Under WNC insurance if we organise\nWaste responsibility: Supplier / client removes all packaging, cable waste and equipment materials\nVenue-rule acknowledgement: Required before load-in\nPayment responsibility: Client unless WNC has contracted supplier within production scope\nApproval status: Template: complete per event\nNotes: Any unusual rigging, wall/beam use, amplified sound or exterior equipment must be agreed with WNC in advance.",
    "source_reference": "SERV-004",
    "topic": "external_supplier_setup"
  }
]
```

Internal operator actions/annotations:

```json
[
  {
    "blocking": true,
    "message": "Current governed policy does not support the requested commitment as stated",
    "proposition_key": "blocker:1609",
    "type": "INTERNAL_CONFIRMATION",
    "workflow_action_id": 639
  },
  {
    "blocking": true,
    "message": "Structured confirmation or review must be completed before commitment",
    "proposition_key": "blocker:1610",
    "type": "INTERNAL_CONFIRMATION",
    "workflow_action_id": 640
  },
  {
    "blocking": true,
    "message": "Approval must be approved or the proposed case decision must be rejected",
    "proposition_key": "blocker:1611",
    "type": "INTERNAL_CONFIRMATION",
    "workflow_action_id": 641
  }
]
```

Subject:

```text
January gathering details
```

Body:

```text
Hi Ari,

Thank you for sharing your plans for the January gathering. We have noted the slides, light background music, outside catering, and possible facilitator-led opening.

You are welcome to bring your own caterer and book them directly. In that case, you would manage the caterer, and they would need to follow the venue’s access and cleaning requirements. There is no WNC coordination fee when you manage the caterer directly.

Any adjustment to the booking fee is still pending, so we cannot confirm a change at this stage.

To take the next step, could you please confirm:

1. What date and time are you requesting for the event?
2. How many guests are you expecting?

Warm regards,
WNC Rentals Team
```

Grade: C. Asks the two missing client facts but does not answer the requested booking-fee amount or standard technical capabilities.

Scores and safety/quality checks (`true` = issue present):

```json
{
  "scores": {
    "factual_grounding": 5,
    "wnc_tone": 3,
    "naturalness": 3,
    "clarity": 4,
    "concision": 4,
    "next_step_clarity": 4,
    "operator_confidence": 3
  },
  "checks": {
    "robotic_phrasing": false,
    "internal_uncertainty_exposed": false,
    "false_external_contact_statement": false,
    "relevant_policy_guidance_omitted": true,
    "wrong_commercial_truth": false,
    "false_confirmation": false,
    "unsupported_assertion": false,
    "known_no_contradiction": false,
    "unnecessary_client_question": false,
    "missed_client_question": true,
    "em_dash": false,
    "dangling_signoff": false,
    "stale_draft": false,
    "confidentiality_issue": false,
    "duplicate_internal_work_action": false
  }
}
```

### UAT-012 / Turn 2: Messy compound inquiry

Intent: REQUEST_CLIENT_INFORMATION

Resolution ownership/items:

```json
[
  {
    "blocking": true,
    "client_visibility": "ASK_CLIENT",
    "message": "What date and time is the client requesting for the event?",
    "proposition_key": "open_question:1668",
    "resolution_owner": "CLIENT",
    "resolution_status": "REQUIRED",
    "workflow_action_id": null
  },
  {
    "blocking": true,
    "client_visibility": "DECISION_PENDING_VISIBLE",
    "message": "booking fee override",
    "proposition_key": "case_decision:52",
    "resolution_owner": "GOVERNED_DECISION",
    "resolution_status": "REQUIRED",
    "workflow_action_id": null
  },
  {
    "blocking": true,
    "client_visibility": "INTERNAL_ONLY",
    "message": "Approval must be approved or the proposed case decision must be rejected",
    "proposition_key": "blocker:1611",
    "resolution_owner": "WNC_INTERNAL",
    "resolution_status": "ACTION_CREATED",
    "workflow_action_id": 641
  },
  {
    "blocking": true,
    "client_visibility": "INTERNAL_ONLY",
    "message": "Current governed policy does not support the requested commitment as stated",
    "proposition_key": "blocker:1612",
    "resolution_owner": "WNC_INTERNAL",
    "resolution_status": "ACTION_CREATED",
    "workflow_action_id": 647
  },
  {
    "blocking": true,
    "client_visibility": "INTERNAL_ONLY",
    "message": "Structured confirmation or review must be completed before commitment",
    "proposition_key": "blocker:1613",
    "resolution_owner": "WNC_INTERNAL",
    "resolution_status": "ACTION_CREATED",
    "workflow_action_id": 648
  }
]
```

Retrieved contextual guidance:

```json
[]
```

Internal operator actions/annotations:

```json
[
  {
    "blocking": true,
    "message": "Approval must be approved or the proposed case decision must be rejected",
    "proposition_key": "blocker:1611",
    "type": "INTERNAL_CONFIRMATION",
    "workflow_action_id": 641
  },
  {
    "blocking": true,
    "message": "Current governed policy does not support the requested commitment as stated",
    "proposition_key": "blocker:1612",
    "type": "INTERNAL_CONFIRMATION",
    "workflow_action_id": 647
  },
  {
    "blocking": true,
    "message": "Structured confirmation or review must be completed before commitment",
    "proposition_key": "blocker:1613",
    "type": "INTERNAL_CONFIRMATION",
    "workflow_action_id": 648
  }
]
```

Subject:

```text
January gathering details
```

Body:

```text
Hi Ari,

Thanks for the update. We’ve noted 24 guests and that the facilitator would welcome the group for about 20 minutes.

What date and time are you requesting for the gathering? Once you have those details, please send them through so we can confirm feasibility.

Warmly,
WNC Rentals
```

Grade: C. Keeps guests/facilitator update but drops earlier unanswered technical, catering and fee topics; retrieved guidance is now empty.

Scores and safety/quality checks (`true` = issue present):

```json
{
  "scores": {
    "factual_grounding": 5,
    "wnc_tone": 3,
    "naturalness": 3,
    "clarity": 4,
    "concision": 5,
    "next_step_clarity": 4,
    "operator_confidence": 3
  },
  "checks": {
    "robotic_phrasing": false,
    "internal_uncertainty_exposed": false,
    "false_external_contact_statement": false,
    "relevant_policy_guidance_omitted": true,
    "wrong_commercial_truth": false,
    "false_confirmation": false,
    "unsupported_assertion": false,
    "known_no_contradiction": false,
    "unnecessary_client_question": false,
    "missed_client_question": true,
    "em_dash": false,
    "dangling_signoff": false,
    "stale_draft": false,
    "confidentiality_issue": false,
    "duplicate_internal_work_action": false
  }
}
```

### UAT-012 / Turn 3: Messy compound inquiry

Intent: DECISION_PENDING

Resolution ownership/items:

```json
[
  {
    "blocking": true,
    "client_visibility": "DECISION_PENDING_VISIBLE",
    "message": "booking fee override",
    "proposition_key": "case_decision:52",
    "resolution_owner": "GOVERNED_DECISION",
    "resolution_status": "REQUIRED",
    "workflow_action_id": null
  },
  {
    "blocking": true,
    "client_visibility": "INTERNAL_ONLY",
    "message": "Approval must be approved or the proposed case decision must be rejected",
    "proposition_key": "blocker:1611",
    "resolution_owner": "WNC_INTERNAL",
    "resolution_status": "ACTION_CREATED",
    "workflow_action_id": 641
  },
  {
    "blocking": true,
    "client_visibility": "INTERNAL_ONLY",
    "message": "Current governed policy does not support the requested commitment as stated",
    "proposition_key": "blocker:1614",
    "resolution_owner": "WNC_INTERNAL",
    "resolution_status": "ACTION_CREATED",
    "workflow_action_id": 652
  },
  {
    "blocking": true,
    "client_visibility": "INTERNAL_ONLY",
    "message": "Structured confirmation or review must be completed before commitment",
    "proposition_key": "blocker:1615",
    "resolution_owner": "WNC_INTERNAL",
    "resolution_status": "ACTION_CREATED",
    "workflow_action_id": 653
  }
]
```

Retrieved contextual guidance:

```json
[]
```

Internal operator actions/annotations:

```json
[
  {
    "blocking": true,
    "message": "Approval must be approved or the proposed case decision must be rejected",
    "proposition_key": "blocker:1611",
    "type": "INTERNAL_CONFIRMATION",
    "workflow_action_id": 641
  },
  {
    "blocking": true,
    "message": "Current governed policy does not support the requested commitment as stated",
    "proposition_key": "blocker:1614",
    "type": "INTERNAL_CONFIRMATION",
    "workflow_action_id": 652
  },
  {
    "blocking": true,
    "message": "Structured confirmation or review must be completed before commitment",
    "proposition_key": "blocker:1615",
    "type": "INTERNAL_CONFIRMATION",
    "workflow_action_id": 653
  }
]
```

Subject:

```text
January gathering details
```

Body:

```text
Hi Ari,

Thanks for confirming the timing. I’ve noted 21 January from 17:00 to 21:00 for your gathering of 24 guests.

We still need to confirm whether the request can go ahead as proposed. We’ll be in touch once that review is complete.

Warm regards,
WNC Rentals
```

Grade: C. The timing update turns into whole-request uncertainty and loses the compound inquiry topics.

Scores and safety/quality checks (`true` = issue present):

```json
{
  "scores": {
    "factual_grounding": 5,
    "wnc_tone": 2,
    "naturalness": 2,
    "clarity": 3,
    "concision": 5,
    "next_step_clarity": 2,
    "operator_confidence": 2
  },
  "checks": {
    "robotic_phrasing": true,
    "internal_uncertainty_exposed": true,
    "false_external_contact_statement": false,
    "relevant_policy_guidance_omitted": true,
    "wrong_commercial_truth": false,
    "false_confirmation": false,
    "unsupported_assertion": false,
    "known_no_contradiction": false,
    "unnecessary_client_question": false,
    "missed_client_question": true,
    "em_dash": false,
    "dangling_signoff": false,
    "stale_draft": false,
    "confidentiality_issue": false,
    "duplicate_internal_work_action": false
  }
}
```

### UAT-013 / Turn 1: Reschedule acknowledgement supplement

No persisted draft. Generation rejected. Exact rejected subject/body unavailable.

```json
[
  {
    "model": "gpt-5.6-sol",
    "provider": "openai",
    "content_hash": "5d46c92865fe0c5fa6e51c538a98799b2effc33f3e6970614a6552255f25bd64",
    "context_hash": "ef11447d656befe1931e929eb98fd8cc68a9fe03f2734980f1195d36fc3c1a1e",
    "response_intent": "COMPLETE_INQUIRY_RESPONSE",
    "validation_codes": [
      "unsupported_availability_or_confirmation",
      "commercial_assertion_not_allowed"
    ],
    "validation_result": "rejected",
    "provider_request_id": "req_47fbf6256c0747d88c646aa93da3037a",
    "provider_response_id": "resp_0fc2377e38126cd3016ab932540b8c87d2bc981f2c72b3ac06",
    "source_case_revision": 2,
    "provider_response_status": "completed",
    "provider_incomplete_reason": null
  }
]
```

### UAT-013 / Turn 2: Reschedule acknowledgement supplement

Intent: RESCHEDULE_ACKNOWLEDGEMENT

Resolution ownership/items:

```json
[]
```

Retrieved contextual guidance:

```json
[]
```

Internal operator actions/annotations:

```json
[]
```

Subject:

```text
Request to move your planning session
```

Body:

```text
Hi Riley,

Thanks for letting us know. We’ve noted your request to move the same planning session for 16 guests to 8 February, from 14:00 to 17:00. We’ll review the new date and time and get back to you.

Warm regards,
WNC Rentals
```

Grade: B. Accurate concise reschedule acknowledgement; review promise still exposes an internal check.

Scores and safety/quality checks (`true` = issue present):

```json
{
  "scores": {
    "factual_grounding": 5,
    "wnc_tone": 4,
    "naturalness": 4,
    "clarity": 5,
    "concision": 5,
    "next_step_clarity": 3,
    "operator_confidence": 4
  },
  "checks": {
    "robotic_phrasing": false,
    "internal_uncertainty_exposed": true,
    "false_external_contact_statement": false,
    "relevant_policy_guidance_omitted": false,
    "wrong_commercial_truth": false,
    "false_confirmation": false,
    "unsupported_assertion": false,
    "known_no_contradiction": false,
    "unnecessary_client_question": false,
    "missed_client_question": false,
    "em_dash": false,
    "dangling_signoff": false,
    "stale_draft": false,
    "confidentiality_issue": false,
    "duplicate_internal_work_action": false
  }
}
```

## Remaining work

Authenticate GitHub, push the tested commit, deploy staging, verify health/provider posture, rerun the frozen UAT and assess every output. Continue up to three meaningful cycles if required. No success/incomplete-after-three-cycles marker applies at this checkpoint.

## Safety

For this program: Graph mutations = 0; Outlook sends = 0; real Asana executions = 0; production activity = 0. No approval or execution endpoint was called. All 13 synthetic cases have zero execution attempts in the captured results. OpenAI draft generation used the authorized unchanged `gpt-5.6-sol` model. New open approval records arise from normal draft generation; none was approved.
