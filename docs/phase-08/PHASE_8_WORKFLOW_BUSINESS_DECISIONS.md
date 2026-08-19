# Phase 8 Workflow Business Decisions

Date:

- August 9, 2026

Status:

- `AUTHORITATIVE_PHASE_8_PRE_ARCHITECTURE_DECISION_RECORD`

## Governance Boundary

These decisions are:

- human-approved Phase 8 workflow semantics
- approved inputs to Phase 8.0B workflow architecture
- distinct from pre-existing Phase 4 deterministic rule truth
- distinct from pre-existing Phase 5 governed knowledge
- distinct from Phase 6 historical precedent
- distinct from Phase 7 reasoning/runtime behavior

They do not automatically rewrite closed-phase authority unless a specific upstream governed-source correction is explicitly carried out.

## Resolved Architecture-Blocking Decisions

### `P8D-001` / `WD-001`

Title:

- `PRACTICAL_PROPOSAL_READY_THRESHOLD`

Final decision:

- A proposal may be finalized and sent when core scope, feasibility, and pricing are sufficiently resolved and no unresolved issue remains that could materially change feasibility, price, scope, or core commercial terms.
- Non-material operational details may remain unresolved until later pre-event planning.
- A working draft may exist before `PROPOSAL_READY`.

Rationale:

- WNC needs a practical commercial threshold, not a requirement that every final operational detail already be complete.

Workflow implication:

- `PROPOSAL_READY` is a materiality gate, not an everything-known gate.

Blocker/action implication:

- Material unresolved issues block proposal send.
- Non-material detail gaps do not block proposal send by default.

Human-in-loop implication:

- Human review remains available for borderline materiality judgment.

Authority implications:

- This is a Phase 8 workflow decision, not a retroactive Phase 4 or Phase 5 source claim.

Downstream architecture requirement:

- 8.0B must support draft proposals, proposal blockers, and explicit materiality-aware readiness checks.

Date decided:

- August 9, 2026

Status:

- `RESOLVED`

### `P8D-002` / `WD-002`

Title:

- `RISK_BASED_APPROVAL`

Final decision:

- Approval is neither universally manual nor fully unrestricted.
- Routine low-risk paths may progressively automate after operational validation.
- Materially consequential areas still require human approval, including commercial exceptions, waivers, custom rates, custom payment terms, unresolved current authority, legal/compliance uncertainty, unusual supplier arrangements, and material operational risk.
- The application controls automation level.
- The LLM may not decide its own approval requirements.

Rationale:

- WNC needs scalable workflow control without letting the model invent approval policy.

Workflow implication:

- Approval is policy-driven and risk-based.

Blocker/action implication:

- High-impact exceptions create explicit approval requirements instead of silent progression.

Human-in-loop implication:

- Human review remains concentrated on consequential decisions rather than every trivial update.

Authority implications:

- Approval policy is structured workflow truth, not generated prose.

Downstream architecture requirement:

- 8.0B must support replaceable approval-policy logic and structured approval requests.

Date decided:

- August 9, 2026

Status:

- `RESOLVED`

### `P8D-003` / `WD-004`

Title:

- `ALTERNATIVE_FIRST_FEASIBILITY`

Final decision:

- Event suitability is not modeled as a simplistic binary.
- When a request cannot be satisfied exactly as requested, the workflow should first look for a current-authority-supported alternative before recommending rejection.
- Possible outcomes include feasible as requested, feasible with supported alternative, feasible only after confirmation, or hard constraint requiring human review or decline.
- Unsupported alternatives may not be invented.

Rationale:

- WNC often solves fit problems through scoped alternatives rather than immediate rejection.

Workflow implication:

- Qualification must handle alternatives, confirmations, and hard constraints distinctly.

Blocker/action implication:

- Unsupported requests can become alternative proposals or confirmation blockers instead of automatic declines.

Human-in-loop implication:

- Hard-constraint and special-case handling remains reviewable.

Authority implications:

- Alternatives must come from current authority, not historical precedent or model invention.

Downstream architecture requirement:

- 8.0B must represent feasibility outcomes beyond pass/fail.

Date decided:

- August 9, 2026

Status:

- `RESOLVED`

### `P8D-004` / `WD-005`

Title:

- `CASE_BY_CASE_COMPLIANCE_OWNERSHIP`

Final decision:

- Compliance is not permanently assigned to one fixed WNC role.
- The person handling the rental is responsible for obtaining the right information and exercising judgment.
- Automation should identify current governed compliance requirements, surface them, create structured tasks/requirements, track status, and make them visible downstream.
- AI may summarize relevant compliance requirements, but may not independently declare unresolved legal/compliance issues resolved.

Rationale:

- Compliance work varies by case and cannot safely be flattened into one universal owner or a fully automated legal decision.

Workflow implication:

- Compliance becomes tracked workflow state with explicit status, ownership, and visibility.

Blocker/action implication:

- Unresolved compliance items remain blockers or tracked requirements instead of disappearing in email.

Human-in-loop implication:

- Legal/compliance resolution stays human-controlled.

Authority implications:

- Current governed knowledge identifies requirements; workflow state tracks whether they have been addressed.

Downstream architecture requirement:

- 8.0B must separate requirement detection from requirement resolution.

Date decided:

- August 9, 2026

Status:

- `RESOLVED`

### `P8D-005` / `WD-006`

Title:

- `DECLARATION_BASED_INSURANCE`

Final decision:

- For full-venue events, larger activations, and productions where the current agreement requires insurance, the signed agreement attestation is the default operational confirmation.
- Default workflow behavior must not create an `INSURANCE_DOCUMENT_MISSING` blocker merely because no certificate has been uploaded.
- For smaller studio/custom rentals, no default insurance-document workflow should be invented.
- Unusual or high-risk smaller rentals may still be handled case-by-case.

Rationale:

- The current agreement already captures the client declaration for higher-impact scopes, and the workflow should not invent a stronger default evidence requirement.

Workflow implication:

- Insurance handling depends on scope and current authority rather than a universal upload requirement.

Blocker/action implication:

- Entire-venue/larger-activation insurance defaults to attestation-through-agreement.
- Smaller/high-risk exceptions may still produce case-specific review requirements.

Human-in-loop implication:

- Case-by-case exceptions remain reviewable.

Authority implications:

- This decision aligns with current agreement wording for full-venue/larger activation scopes and resolves the workflow treatment.

Downstream architecture requirement:

- 8.0B must support attestation-based compliance satisfaction and optional case-specific evidence escalation.

Date decided:

- August 9, 2026

Status:

- `RESOLVED`

### `P8D-006` / `WD-007`

Title:

- `CONDITIONAL_FINAL_INFORMATION_DEADLINE`

Final decision:

- Rentals requiring WNC staffing should materially finalize applicable operational information `30 days before event`.
- Rentals without WNC staffing requirements should materially finalize applicable operational information `14 days before event`.
- The required package is conditional by event scope.
- Late information does not automatically invalidate the rental; it enters the controlled change/late-change workflow.

Rationale:

- The workflow needs milestone logic that reflects operational load and staffing dependency rather than one universal checklist or one universal deadline.

Workflow implication:

- Final-information gating is conditional and scope-sensitive.

Blocker/action implication:

- Missing material information becomes a blocker, urgency flag, or late-change item based on scope and timing.

Human-in-loop implication:

- Materiality and case-specific late-information consequences remain reviewable.

Authority implications:

- This is a Phase 8 workflow policy decision and must not be falsely back-attributed to already-frozen Phase 5 wording.

Downstream architecture requirement:

- 8.0B must support conditional final-info requirements, milestone recalculation, and late-info escalation.

Date decided:

- August 9, 2026

Status:

- `RESOLVED`

### `P8D-007` / `WD-008`

Title:

- `EVENT_READY`

Final decision:

- `EVENT_READY` is a strict operational readiness gate.
- It means no unresolved material issue remains that could prevent or materially disrupt delivery, and every required operational responsibility has an owner and status.
- Only applicable requirements matter.
- Minor residual details do not block readiness.

Rationale:

- WNC needs a strong delivery-readiness concept that is stricter than calendar timing but more practical than perfection.

Workflow implication:

- Event readiness is a material operational state, not merely “the date has arrived.”

Blocker/action implication:

- Missing material prerequisites block `EVENT_READY`.

Human-in-loop implication:

- Borderline materiality and exceptional readiness judgments remain reviewable.

Authority implications:

- Readiness evaluation must use structured workflow state plus current authority, not generated prose.

Downstream architecture requirement:

- 8.0B must support applicability-aware readiness checks, owners, statuses, and unresolved material blockers.

Date decided:

- August 9, 2026

Status:

- `RESOLVED`

### `P8D-008` / `WD-009`

Title:

- `CHANGE_IMPACT_WORKFLOW`

Final decision:

- Inbound changes from email or another event source are extracted into structured proposed case changes.
- A detected statement does not immediately rewrite canonical case truth.
- Changes are evaluated by impact:
  - low impact
  - material impact
  - fundamental scope change
- Accepted changes update the canonical `RentalCase`; affected downstream artifacts refresh from that truth.

Rationale:

- WNC needs controlled change handling without letting email or draft artifacts silently diverge from operations truth.

Workflow implication:

- Change handling is proposal-first and impact-aware.

Blocker/action implication:

- Material-impact and fundamental-scope changes can reopen targeted review or earlier workflow stages.

Human-in-loop implication:

- Consequential client-facing or commercial updates require review before commitment.

Authority implications:

- Extraction is not authority; accepted structured change state is.

Downstream architecture requirement:

- 8.0B must support proposed changes, impact evaluation, acceptance, and refresh of dependent artifacts.

Date decided:

- August 9, 2026

Status:

- `RESOLVED`

### `P8D-009` / `WD-010`

Title:

- `NEGOTIATED_RESCHEDULE_WORKFLOW`

Final decision:

- A client request to move the date creates `PROPOSED_DATE_CHANGE`, not an immediate case update.
- Rescheduling supports negotiation, current-authority re-evaluation, and explicit client confirmation before the active date changes.
- Urgent or last-minute changes escalate priority and checking depth but do not bypass authority or confirmation.

Rationale:

- Date changes are negotiated commercial and operational events, not a single-field overwrite.

Workflow implication:

- Rescheduling is a stateful negotiation with re-evaluation.

Blocker/action implication:

- Venue availability, class conflicts, staffing, facilitators, suppliers, pricing, deadlines, and other time-sensitive obligations must be reassessed before commitment.

Human-in-loop implication:

- Consequential reschedule decisions remain reviewable.

Authority implications:

- Current authority controls all consequences and fees; historical rates may not be copied.

Downstream architecture requirement:

- 8.0B must support proposed-date-change state, consequence re-evaluation, and explicit activation only after confirmation.

Date decided:

- August 9, 2026

Status:

- `RESOLVED`

### `P8D-010` / `WD-011`

Title:

- `ADAPTIVE_FOLLOW_UP`

Final decision:

- No single universal stale-case cadence exists.
- Follow-up depends on lead warmth, time to event, required response, and operational/commercial urgency.
- New/cold inquiries use an approximate weekly cadence before dormancy.
- Dormant is distinct from declined/lost.
- Confirmed or operationally critical rentals do not become dormant just because the client stops replying; they escalate based on risk and timing.

Rationale:

- Sales and operations urgency changes materially over time and by case state.

Workflow implication:

- Follow-up is dynamic, contextual, and stage-sensitive.

Blocker/action implication:

- Dormancy, escalation, and urgent follow-up must be modeled explicitly.

Human-in-loop implication:

- Date release, loss/decline, and critical escalations remain human-controlled.

Authority implications:

- Cadence is a workflow policy, not something inferred from generated email wording.

Downstream architecture requirement:

- 8.0B must support configurable follow-up policy, dormancy, and operational escalation.

Date decided:

- August 9, 2026

Status:

- `RESOLVED`

### `P8D-011` / `WD-012`

Title:

- `PRAGMATIC_CLOSE_OUT`

Final decision:

- The workflow distinguishes `EVENT_COMPLETE`, `CLOSE_OUT_IN_PROGRESS`, and `CLOSED`.
- The automation should not require perfect administrative tidiness before closure.
- The human interface must allow closure when keeping the rental active no longer adds meaningful value.
- Manual closure must remain auditable and must not erase unresolved material issues.

Rationale:

- Automation should stop when it ceases to add meaningful operational value, without hiding material post-event obligations.

Workflow implication:

- Close-out is a staged completion model rather than one rigid all-items-perfect rule.

Blocker/action implication:

- Material unresolved obligations keep the rental in close-out handling.
- Trivial residual matters do not have to keep the rental operationally active.

Human-in-loop implication:

- Human closure remains allowed and auditable.

Authority implications:

- Closure state is structured workflow truth, not a side effect of communication completion.

Downstream architecture requirement:

- 8.0B must support manual close, material-outstanding tracking, and non-destructive post-event resolution state.

Date decided:

- August 9, 2026

Status:

- `RESOLVED`

## Cross-Cutting Architecture Requirements

### `P8X-001`

Title:

- `CASE_SPECIFIC_OPERATIONAL_TRUTH`

Final decision:

- Phase 8 must distinguish:
  - Phase 4 global deterministic truth
  - Phase 5 governed guidance
  - Phase 6 historical precedent
  - Phase 8 case-specific operational truth
- Approved rental-specific exceptions affect only the relevant rental unless separately promoted through formal governance.

Workflow implication:

- A case-specific exception changes effective case truth without rewriting the global rule.

Authority implications:

- Case-specific truth requires its own authority and approval handling.

Downstream architecture requirement:

- 8.0B must support a concept equivalent to `CaseDecision` or `CaseOverride`.

### `P8X-002`

Title:

- `EMAIL_AS_EVIDENCE_NOT_AUTHORITY`

Final decision:

- Email may provide evidence for a proposed case decision or a proposed case change.
- Extraction itself is not authority.
- Only the workflow’s authority and approval mechanism may promote a proposal into active rental-specific truth.

Workflow implication:

- Inbound text becomes structured proposed state before any effective-case update.

Downstream architecture requirement:

- 8.0B must separate extraction, authority check, approval, and activation.

### `P8X-003`

Title:

- `APPROVAL_SURFACE_INDEPENDENCE`

Final decision:

- `ApprovalRequest` belongs to the WNC workflow system/source of truth.
- Humans may interact with it through Asana first or another approved interface later.
- The core workflow records the structured approval result, not the UI surface.

Workflow implication:

- Approval UI is replaceable.

Downstream architecture requirement:

- 8.0B must keep approval state independent from Asana-specific implementation.

### `P8X-004`

Title:

- `EXTERNAL_SYSTEMS_AS_INTERFACES`

Final decision:

- External systems such as Asana, n8n, Outlook, Google Calendar, or Mollie are interfaces/execution adapters rather than sources of business truth.
- Business state remains in the WNC Rental workflow system.

Workflow implication:

- External execution cannot silently become the hidden business-logic layer.

Downstream architecture requirement:

- 8.0B must model structured actions and state before any adapter executes them.

### `P8X-005`

Title:

- `PHASE_8_RELIABILITY_PRINCIPLES`

Final decision:

- No autonomous workflow agent.
- Generated prose is not workflow truth.
- Missing authority becomes workflow state.
- Decisions and communication are separate.
- Actions exist as structured records before execution.
- External execution cannot silently advance state.
- Case changes are proposals before becoming truth.
- Case-specific exceptions are scoped.
- Approval UI is replaceable.
- Human-in-the-loop is risk based.

Workflow implication:

- Later workflow logic must remain state-machine/application controlled and structured-data driven.

Downstream architecture requirement:

- 8.0B must enforce these principles directly in workflow architecture, not treat them as optional guidance.
