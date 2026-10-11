# Root Cause

Status: **NOT CERTIFIED — access/context and field-sharing prerequisites unresolved**, 11 October 2026.

The exact provider cause of the original RENT association failure cannot be recovered from the retained evidence. The hosted HTTP 500 and internal ProjectionFailure discarded the underlying Asana status/phrase. It would be incorrect to relabel it as a scope, permission, or entitlement rejection. The original durable start artifact remains unchanged and classified **OUTCOME_UNVERIFIED**. No replay or new association request was made during this diagnosis.

Independent read-only evidence establishes concrete prerequisites that were previously missed: staging has no associated team; Rentals 2026 belongs to a private team unavailable to the current guest; only RENT is workspace-wide; the other four fields are local. These explain why the proposed setup cannot yet be certified, but do not prove what caused the historical RENT-only request.

# Entitlement / Permission Context

| Evidence | Rentals 2026 | Dedicated staging |
|---|---|---|
| Project | 1212669866280530 | 1217642260793817 |
| Workspace | 1208455784737302 | 1208455784737302 |
| UI associated team | Private team, not editable by current project editor | No team, editable |
| API team | null — cannot identify the private team from this account | null |
| Owner | Haylin, 1208455784737290 | Serinya, 1208418485086736 |
| Members | Haylin, Serinya, 1212320845916448 | Serinya |
| State/type/privacy | Active, default_project, private | Active, default_project, private |
| Default/minimum customization access | editor/editor in API; UI project details require admin | editor/editor |
| Custom field settings | Five existing definitions | Empty |

Workspace membership 1208680514377247 confirms integration user 1208418485086736 is active, a guest, and not view-only. The UI account is serinya@gjemmestad.com. The staging team selector exposes Center Team and WNC, but neither is proven to be the reference private team or to have its entitlement; neither was selected.

The reference duplicate dialog explicitly states that its private associated team cannot be copied. Copying was not submitted. The reference Kanban board bundle contains RENT and view/section configuration; it does not contain the other four fields. Its bundle screen also displays an upgrade notice to this account. These observations do not establish that every possible zero-additional-cost path is unavailable, or identify the WNC subscription tier.

Successful current reads prove effective read access to both projects and the current user's membership. Historical successful task executions prove task write access at those execution times. Current projects:write is **unverified**. The configured static staging access token is not proven to be PAT or OAuth, and its scopes are not exposed by these reads. No credential was rotated or broadened. The production OAuth app's three scopes are separate and cannot diagnose the staging credential. [The association endpoint requires projects:write](https://developers.asana.com/reference/addcustomfieldsettingforproject).

# Remediation

Commit 8448f5f22176c7e72e00a004d6edf1f68060299b adds narrow safe provider diagnostics and a read-only context audit. It was deployed only to staging; Render deployment dep-db5p7uvlk1mc73apdhg0 is Live. Diagnostics retain normalized status, error class, non-sensitive phrase/message, operation, and target IDs; they redact credentials, authorization text, email addresses, URLs and long token-like text. They do not retain headers, full response bodies or transport exception text. Existing ambiguity and retry semantics remain intact.

No purchase, trial, seat, add-on or billing change occurred. No additional-cost remediation was attempted. Current guest access cannot place an isolated project inside the known reference private team. An existing licensed WNC admin or guest access to that exact team is needed to inspect its supported €0 setup path; the user has been asked for that access.

Team access alone does not resolve the four local field identities. Asana documents that ordinary project-local fields are unavailable to other projects. Bundle-local fields can be shared through their bundle, but the inspected existing bundle contains only RENT. Promoting the other fields into the organization library or changing a live bundle would affect live field configuration, outside the authorized no-live-mutation scope. Blindly duplicating the project is also unsuitable because preserving those local field IDs is not established. No fields/options/project were created, copied, globalized or reassigned. [Custom field scope](https://developers.asana.com/docs/custom-fields-guide), [bundle-local fields](https://help.asana.com/s/article/bundles).

Safest next step: establish existing private-team access and inspect an admin-supported exact-ID sharing path. If it requires changing live field configuration, a separate explicit scope decision is necessary before proceeding. A paid upgrade is not the established solution.

# Existing Custom Fields

**Audited, not newly attached or reused in staging.** Staging settings remain empty. No duplicate definitions/options were created.

| Field | Existing GID | Scope | Existing options |
|---|---|---|---|
| RENT | 1212662125912127 | Workspace-wide; provider-generated read-only custom ID, prefix RENT | None; never manually allocate/write |
| Room | 1212669866280539 | Local | Studio 1212669866280540; Podcast room 1212669866280541; Whole space 1212669866280542 |
| Event Type | 1212669866280544 | Local | PR 1212669866280545; Personal + private 1212669866280546; Corporate / networking 1212669866280547; Workshop 1212669866280548; Photo Shoot 1212669866280549 |
| Client & Ownership | 1212669866280551 | Local text | Verified POC email only |
| Add ons | 1212669866280553 | Local multi-enum | Catering 1212669866280554; Drink package 1212669866280555; Tech required 1212669866280556; red light 1212669866280557; Staff 1212669866280558; other 1212669866280559 |

# Live Operator Card

No operator-v4 card was written in this diagnostic campaign. The accepted local presentation was not redesigned. Its exact binding, field mapping, stable provider RENT and hidden reconciliation code remain deployed but are not claimed live-certified. Existing staging tasks retain their prior presentation until prerequisites are resolved.

# Follow-Up

No governed follow-up was applied. Cases 598, 591 and 593 remain reserved for the bounded proof. Their existing master IDs are 1219380771906381, 1219380962448743 and 1219380850208438. Their corresponding Google document IDs are 1_Pyw9qywvvbL18TIFkbvxgeKmVW1eDLGn4YNwO3rxf8, 1EDL6E3zG5TWPbDneAAskYQOCUCU2geBdmKJpwrMQItk and 15aGKYk4K1hBZJpulsS_QSqsdBE4xcSCufXwyllsS_SM.

Automatic governed-state proposal synchronization remains implemented and covered by provider-free tests; it was not manually triggered or claimed proven live in this campaign. No Google write, new document or Asana task mutation occurred.

# Reconciliation / Replay

The old ambiguous association remains fenced. No observation cleared it and no retry occurred. Provider-free exact-binding, drift, duplicate/replay and automatic-sync coverage passed. Live operator-v4 matches_projection, stable RENT, unchanged task/subtask reuse, automatic same-document follow-up and zero-update replay proof remain pending; no success is inferred from code tests. Historical task and canonical audit records were not deleted, reparented or rewritten.

# Tests

Nine focused safe-diagnostic/custom-field tests passed, including HTTP 400/402/403/500 diagnostic retention and transport ambiguity/redaction. Full Phase 8: **857 passed, 28 warnings**, 10.63 seconds. No provider call was made by those tests. See phase8_diagnostics.log and tools/phase_08_workflow/tests/test_asana_safe_diagnostics.py.

# Gates

Fresh hosted staging health after deployment confirms all seven gates disabled: real providers, Asana execution, Google proposal, Outlook execution, inbound, inbound preflight and send. None was enabled during this diagnosis. Fresh read-only production durable controls confirm outlook_inbound, outlook_send and asana_mutations false and lease_expires 0. Google production remains unavailable, not an enabled additional lane.

# Production

Production was not deployed, configured or mutated. Only read-only control inspection and a public health request were used for closure verification. Live Rentals 2026 was inspected only. No customer send, Graph call, OpenAI call, Google mutation or Asana mutation occurred during this diagnosis.

# Final Marker

**NOT CERTIFIED.** The requested success marker is withheld because the live proof has not run. ASANA_STAGING_CUSTOM_FIELDS_ENTITLEMENT_BLOCKED is also withheld: a paid-only blocker across all free paths has not been established. Current blockers are inaccessible private-team context, unverified staging projects:write capability, and four non-global field identities under a prohibition on live field changes.

Evidence: context_audit.json; duplicate_team_unavailable.png; staging_no_team.png; reference_bundle_contents.png; diagnostics_staging_deployed.png; diagnosis_health_closed.json; diagnosis_production_controls_read_only.json; diagnosis_canonical_unchanged.json. The original reuse_1212662125912127_started.json remains unchanged.
