# Phase 8 Workflow Unresolved Decisions

Date:

- August 9, 2026

Purpose:

- preserve the original 8.0A unresolved-question history
- show which architecture blockers were resolved by the human-approved 8.0A-R decisions
- isolate the remaining questions that still stay open without blocking 8.0B architecture

## Status Summary

- original unresolved register items: `17`
- resolved by human decision in 8.0A-R: `11`
- remaining unresolved non-blocking items: `6`
- remaining architecture-blocking items: `0`

## Resolved Former Architecture Blockers

| Question ID | Original unresolved question | Previous gap type | Previous priority | Resolution status | Resolution reference | Resolution summary | 8.0B blocked now? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `WD-001` | What exact information must exist before a proposal may be sent, and does that differ by rental type or service level? | `PROCESS_DEFINITION_GAP` | `ARCHITECTURE_BLOCKING` | `RESOLVED_BY_HUMAN_DECISION` | `P8D-001` | Proposal send is blocked only by unresolved material issues affecting feasibility, price, scope, or core commercial terms. | `No` |
| `WD-002` | Is internal proposal approval required, in which situations, and by whom? | `OWNERSHIP_GAP` | `ARCHITECTURE_BLOCKING` | `RESOLVED_BY_HUMAN_DECISION` | `P8D-002` | Approval is risk-based and policy-controlled, with human review retained for materially consequential exceptions. | `No` |
| `WD-004` | Which event types, use cases, or risk conditions are unsuitable, and which require special approval instead of outright rejection? | `BUSINESS_POLICY_GAP` | `ARCHITECTURE_BLOCKING` | `RESOLVED_BY_HUMAN_DECISION` | `P8D-003` | Qualification uses alternative-first feasibility, confirmation blockers, and hard-constraint review rather than a simplistic suitable/unsuitable binary. | `No` |
| `WD-005` | Who owns permit, exemption, and compliance confirmation, and what exactly must be checked before a regulated event scope is treated as final? | `OWNERSHIP_GAP` | `ARCHITECTURE_BLOCKING` | `RESOLVED_BY_HUMAN_DECISION` | `P8D-004` | Compliance ownership is case-specific, tracked structurally, and not fully automated; unresolved legal/compliance issues remain human-resolved. | `No` |
| `WD-006` | When is event or public-liability insurance mandatory, and what evidence must be collected before the event proceeds? | `BUSINESS_POLICY_GAP` | `ARCHITECTURE_BLOCKING` | `RESOLVED_BY_HUMAN_DECISION` | `P8D-005` | Entire-venue/larger-activation insurance defaults to signed-agreement attestation rather than certificate collection; smaller/high-risk cases remain case-by-case. | `No` |
| `WD-007` | What exact final-information package is required by 14 days before the event, and does that package vary by rental type or service level? | `PROCESS_DEFINITION_GAP` | `ARCHITECTURE_BLOCKING` | `RESOLVED_BY_HUMAN_DECISION` | `P8D-006` | Final-information requirements are conditional by scope, with `30 days` for staffed rentals and `14 days` as the urgent milestone for non-staffed rentals. | `No` |
| `WD-008` | What precisely marks a rental as event-ready beyond the current checklist examples? | `PROCESS_DEFINITION_GAP` | `ARCHITECTURE_BLOCKING` | `RESOLVED_BY_HUMAN_DECISION` | `P8D-007` | `EVENT_READY` means no unresolved material delivery risk remains and all required operational responsibilities have owner/status. | `No` |
| `WD-009` | How are last-minute client changes inside 14 days assessed, approved, repriced, or refused? | `AUTOMATION_POLICY_GAP` | `ARCHITECTURE_BLOCKING` | `RESOLVED_BY_HUMAN_DECISION` | `P8D-008` | Changes become structured proposed case changes, are evaluated by impact, and require review before consequential commitment. | `No` |
| `WD-010` | How are postponements and rescheduling handled, and is a rescheduled booking the same rental or a new case? | `BUSINESS_POLICY_GAP` | `ARCHITECTURE_BLOCKING` | `RESOLVED_BY_HUMAN_DECISION` | `P8D-009` | Date changes use a negotiated proposed-date-change workflow; canonical date updates only after explicit confirmation and current-authority re-evaluation. | `No` |
| `WD-011` | What exact rule pauses, closes, or releases stale inquiries and stale proposals when the client stops responding? | `PROCESS_DEFINITION_GAP` | `ARCHITECTURE_BLOCKING` | `RESOLVED_BY_HUMAN_DECISION` | `P8D-010` | Follow-up is adaptive; dormant is distinct from lost/declined; confirmed/critical rentals escalate instead of going dormant. | `No` |
| `WD-012` | What exactly marks close-out complete and allows the rental to be marked closed? | `PROCESS_DEFINITION_GAP` | `ARCHITECTURE_BLOCKING` | `RESOLVED_BY_HUMAN_DECISION` | `P8D-011` | Close-out distinguishes `EVENT_COMPLETE`, `CLOSE_OUT_IN_PROGRESS`, and `CLOSED`, with auditable manual close allowed when automation no longer adds meaningful value. | `No` |

## Remaining Unresolved Non-Blocking Questions

| Question ID | Exact unresolved question | Gap type | Evidence inspected | Why still unresolved | Architecture impact | Priority | Recommended decision owner | 8.0B blocked? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `WD-003` | What exact trigger makes a discovery call mandatory, a site visit mandatory, or email-only scoping sufficient? | `PROCESS_DEFINITION_GAP` | `TPL-006`; `TPL-007`; `OPS-001`; `GOV-002 OPEN-009`; `GOV-002 OPEN-010` | The workflow can represent manual branching and optional review without freezing one trigger matrix yet. | Qualification branching should remain configurable/manual until policy is governed. | `IMPLEMENTATION_BLOCKING` | WNC rental lead + operations | `No` |
| `WD-013` | What is the current security-deposit matrix by rental scope and risk profile? | `BUSINESS_POLICY_GAP` | `CF-003`; `CF-005`; `CF-007`; `GOV-002 DEC-030` to `DEC-033`; `docs/phase-04/phase-04-closure.md` (`BLK-003`) | Deposits remain real, but one stable deterministic matrix is still not governed. | Deposit calculation and some commercial automation must remain manual/configurable. | `IMPLEMENTATION_BLOCKING` | WNC management + finance | `No` |
| `WD-014` | What minimum lead time and operational prerequisites apply to venue clearing? | `PROCESS_DEFINITION_GAP` | `OPS-001`; `GOV-002 OPEN-008`; `HC-001`; `HC-006` as historical context only | The workflow can track venue-clearing requirements without freezing one global lead-time rule. | Complex takeover feasibility should stay partially manual. | `IMPLEMENTATION_BLOCKING` | Operations manager | `No` |
| `WD-015` | When is professional cleaning mandatory rather than case-by-case? | `PROCESS_DEFINITION_GAP` | `OPS-001`; `SERV-003` `CBR-007`; `CF-005`; `GOV-002 OPEN-006` | Current sources still preserve review-only or working-rule behavior. | Cleaning triggers and quote logic must remain configurable/manual. | `IMPLEMENTATION_BLOCKING` | Operations manager | `No` |
| `WD-016` | Who may approve unusual materials and installations such as fake snow, exterior signage, suspended items, or heavy builds? | `OWNERSHIP_GAP` | `CF-003`; `CF-005`; `CF-007`; `OPS-001`; `GOV-002 OPEN-012` | Approval is clearly required, but the accountable approver is still not governed. | Exception routing must keep a manual approval placeholder. | `IMPLEMENTATION_BLOCKING` | Operations manager + management | `No` |
| `WD-017` | What host-staffing matrix applies across rental types, service levels, and event scopes? | `BUSINESS_POLICY_GAP` | `SERV-001`; `OPS-001`; `SERV-003` `CBR-003` and `CBR-004`; `GOV-002 OPEN-004` | The workflow can carry staffing requirements and late-change impact without a universal staffing matrix yet. | Staffing recommendation logic must stay manual/configurable. | `IMPLEMENTATION_BLOCKING` | Operations manager | `No` |

## Notes

- `RESOLVED_BY_HUMAN_DECISION` means the question was unresolved in the original 8.0A audit but has now been resolved by the explicit Phase 8.0A-R human decision record.
- The remaining unresolved questions are still important, but they do not prevent Phase 8.0B from representing them as configurable policy, manual review, or future-governance placeholders.
