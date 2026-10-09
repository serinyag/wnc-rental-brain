# Case 586 integration journey — governed resolution boundary

9 October 2026. **Stopped under the user's material-architecture/authority-boundary condition. No final-response-ready or end-to-end certification marker is claimed.** Component certifications remain closed. No runtime implementation, deployment, permission or provider-gate change was made in this journey.

## Completed work

The certified real Inbox lineage was preserved: two immutable provider messages, sources **3104/3105**, one conversation and case **586**. Provider IDs/hashes are in the inbound certification and local audit record. The event window remains **12 November 2026, 14:00–18:00 Europe/Amsterdam**.

An operator extracted only explicit original-message claims from existing source 3104 through the existing observation validator/router, then ran normal inquiry intake:

| Claim | Observation | Result |
|---|---|---|
| 24 guests | 2724 | Current guest count established through intake |
| Studio space | 2725 | Current rental scope established through intake |
| Team workshop | 2726 | Current event type established through intake |
| External caterer | 2727 | Validated request evidence; not an operational confirmation |
| Projection display | 2728 | Validated request evidence; not a capability confirmation |

The case advanced from revision **2 → 3**. The three already-answerable client questions were resolved. No new inbound source or case was created. No fee, availability, technical approval, supplier access window or commercial exception was inferred from the email.

Existing Phase 7 context assembly retrieved **17 Phase 4 results**, **5 Phase 5 results**, and **5 Phase 6 results**, all with successful retrieval states. Phase 8 consumed reasoning projection **603**, then the existing service evaluated its current capacity and technical checks and reconciled canonical workflow.

Current guidance includes references **OPS-002** (chunks 233, 241, 238), **TPL-007** (504), and **OPS-003** (372). Historical contexts **HC-006, HC-002, HC-005, HC-001, HC-003** remained historical context only; no historical pricing, concession, person capability or room use became current authority. Restricted historical/context data were not sent to a drafting model.

## Current posture

Case **586**, revision **3**, `inquiry_active`, Studio scope, 24 guests, team workshop. Commercial and operational summaries remain unknown. Current timing/profile truth comes from governed client observations/intake. Catering and projection remain evidenced requests.

- CLIENT: no open persisted core questions after intake; no invented client answers or extra questions.
- WNC_INTERNAL: layout/capacity (**action 1632**, blocker 2384), event-specific technical setup (**1633**, blocker 2385), and Studio availability (**1634**).
- EXTERNAL_PARTY: no executable supplier-specific action exists; the email did not identify a supplier or request WNC facilitator sourcing. None was invented.
- GOVERNED_DECISION: no commercial exception or fee adjustment was requested, so none was invented.
- Additional canonical reconciliation actions **1630/1631** record missing current authority and structured confirmation needs. No actions have been executed.
- Expected response posture remains pending internal confirmation. No initial/final draft, approval request or Asana master was created before the blocking boundary was confirmed.

The consumed mixed-topic projection has a coarse `semantic_state_code=known_yes` while its authority outcome is `REQUIRES_CONFIRMATION`, posture is `review_required`, and deterministic use is false. This is not evidence that unresolved availability/setup is known yes. No operational or commercial truth was promoted, and this coarse summary must not be used as confirmation.

## Concrete blocking evidence

1. The observation registry supports client requirements and the booking-fee case-decision candidate, but it defines no event-scoped venue-availability confirmation, technical-setup confirmation or operational-resolution outcome. A generic repository insert or free-form note does not supply the missing authority semantics.
2. `derive_resolution_items` recreates availability work for an inquiry/proposal-in-progress with a known time window; it does not consume an approved availability outcome.
3. `with_workflow_actions` maps an existing internal action to `ACTION_CREATED`, even when an in-memory copy of its payload says `resolution_status=RESOLVED`. The read-only reproduction against case 586 is saved in `resolution_boundary_audit.json`; no actual action was marked resolved.
4. The frozen draft contract unconditionally forbids venue/booking availability confirmation. It has no current scoped availability-confirmation admission path.
5. The earlier Asana component certification demonstrated projection of pre-seeded status changes. Its `prepare_update.py` directly changed fixture truth/actions. Reusing those fixture mutations here would violate this request's prohibition on directly patching canonical truth.

Relevant implementation locations:

- `tools/phase_08_workflow/observation_registry.py`: `OBSERVATION_FIELD_DEFINITIONS`.
- `tools/phase_08_workflow/context_aware_drafting.py`: availability construction in `derive_resolution_items`; `with_workflow_actions` completion handling.
- `tools/phase_08_workflow/governed_client_response.py`: `build_draft_contract` forbidden availability assertions and validation.
- `docs/staging/asana_real_execution/prepare_update.py`: prior component fixture setup, not an operational evidence/decision path.

Creating real Asana tasks now would not fix this missing canonical resolution path. No provider work was created merely to make the integration appear complete.

## Required scoped decision

The missing slice must define how explicit synthetic/operator/external evidence is bound to the exact case, event window/revision and proposition; which existing governed decision admits it; how accepted outcomes complete existing canonical work; and how those outcomes become permissible draft claims without weakening the frozen safety rules. Stale/conflicting evidence and replay must remain guarded, and Asana completion must never establish truth.

This is an authority/contract addition, not a routine deployment or adapter correction. The user explicitly required stopping when material architecture is needed and prohibited redesign in this integration task. No such contract was invented or implemented.

## Verification and handoff

**32 targeted integration regressions** and **659 Phase 8 tests** passed. No failures/skips. Existing collection warnings remain. `git diff --check` passed. No full-suite rerun was necessary because runtime implementation was unchanged.

Protected case lineages **424, 584 and 585** match their baselines. Hosted staging is healthy; inbound, preflight, Outlook send and real Asana gates are disabled. No send, Graph call, Asana mutation, draft generation, approval or execution attempt occurred in this journey. Current/historical retrieval used the existing embedding/retrieval path; it was not represented as provider-free.

See [chronological timeline](JOURNEY_TIMELINE.md) for timestamps, events, revision and authority references. Asana creation/update, synthetic resolutions, final draft/approval, Outlook send and final integrated reconciliation are explicitly **not reached**. No production work occurred.
