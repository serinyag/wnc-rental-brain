# Google Proposal Architecture

Status: implemented and provider-free verified; complete live workflow certification is pending Google runtime authorization. No complete certification marker is issued.

The Google proposal is an outbound projection of the existing canonical case. It uses the normal Phase 8 WorkflowAction execution path, repository and execution journal. The existing five WNC Word templates supply seven sections, styles and page geometry. Example content is replaced by managed section blocks; the source files are unchanged. Layout identity persists across scope changes, while title and current details change. Studio and production layouts were rendered and visually checked locally.

Implementation: `tools/phase_08_workflow/google_proposal.py`, `google_proposal_adapter.py`, existing console service/routes, runtime configuration, Asana projection and additive migration `20261010000100`.

# Canonical Authority Boundary

Supabase remains canonical. A public-field allowlist excludes raw reasoning, source references, provider IDs, internal notes and financial facts. Requested values remain TBC. Commercial amounts require an active commercial decision with evidence and its matching approved case-decision approval. Template VAT examples and unapproved amounts are excluded. Operational confirmations reuse the existing scoped client assertions from accepted immutable operational evidence. Neither provider reads nor reconciliation mutate case facts or accept business decisions.

# Google Provider Binding

The stable proposal identity hashes the canonical case UUID and proposal purpose. Action plans bind the staging OAuth application identity, allowlisted folder, exact case revision and projection hash. Normal execution snapshots persist case/proposal identity, file/document ID, template identity, synchronized case revision, content hash, provider revision, synchronization timestamp and document fingerprint.

No hosted Google runtime credential currently exists. The connected Drive tool and earlier manually created working document are not hosted application credentials or certified runtime bindings. A dedicated staging OAuth app with only `drive.file`, a refresh credential and a dedicated app-accessible staging folder are required. No Google app, folder, document, grant or credential was created in this campaign. Permission approval is pending.

# Create / Update / Reconciliation

Creation converts the governed Word artifact into a native Google document with app-private identity properties and its explicit staging parent. Identity search is performed before creation. Updates modify the existing document in place using native UTF-16 ranges and `requiredRevisionId`; no replacement document is created for a case revision change. Unchanged public content generates no document write, even when an unrelated case revision advances.

The adapter re-reads canonical state immediately before mutations, verifies folder/app/case identity, rejects duplicate identities and persists confirmed bindings through the execution journal. A database row lock fences concurrent actions and unresolved attempts; projection payloads and provider scope are immutable. Transport mutations are never automatically retried. Unknown outcomes retain their ambiguity and block later mutations.

Read-only observation reports MATCHES_PROJECTION, DRIFT_DETECTED, MISSING or AMBIGUOUS. Orphan discovery after a timeout identifies the existing candidate using app metadata, never title similarity. Discovery does not silently rebind or clear the original journal fence. Explicit operator recovery remains required for ambiguous or drifted work; this campaign does not provide an automatic override.

Google reference contracts: [Docs revision-controlled atomic batch updates](https://developers.google.com/workspace/docs/api/reference/rest/v1/documents/batchUpdate), [Drive upload and document conversion](https://developers.google.com/workspace/drive/api/guides/manage-uploads), [Drive application properties](https://developers.google.com/workspace/drive/api/guides/properties).

# Human Edit Behavior

PROPOSAL_DOC_CANONICAL_PROJECTION_WITH_MANUAL_DRIFT_REVIEW

Document fingerprints include text, formatting, document styles, title and other returned structural metadata, excluding volatile document/revision identifiers. Human edits stop synchronization and remain preserved. Revision control also rejects an edit made between read and write; post-write revision/content verification fences uncertain results. Unsupported multiple tabs or non-text content require review. There is no Google-to-case truth import.

# Asana Integration

The existing rental-specific Asana department/task planner is retained. Its nuanced master projection includes the bound Google proposal URL, current/review status and a short next action. It does not duplicate the proposal or show provider metadata. Outlook pre-send validation blocks proposal-required cases whose document is stale, failed, missing, ambiguous or drifted and performs a final read-only document check. Existing certified cases without a Google proposal action retain their prior contract.

# Scenario A — Simple Studio

Provider-free execution creates one synthetic Studio document, persists identity and replays without mutation. The real hosted Outlook → case → Asana → Google → approved staging send journey was not run. It requires the dedicated Google runtime grant and credential.

# Scenario B — Production Rental

Provider-free checks cover production scope, schedules, load-in/out and technical requirements, approved commercial decisions and accepted operational confirmations. A database-backed test verifies that the document uses exactly the same scoped availability statement as client drafting. No invented service or booking commitment is introduced. The complete hosted real-provider journey remains pending.

# Scenario C — Changed Requirements

Provider-free tests update guest count, schedule/date, venue/scope, production scope, services and technical requirements while retaining the same document ID. An accepted operational statement disappears after a canonical date change makes its scope obsolete. Replay and restart retain identity. The real hosted follow-up/conversation/master/document journey remains pending.

# Cross-Surface Consistency

Deterministic checks compare native document text with the canonical managed projection, verify the Asana URL/status, and compare accepted scoped operational statements with the client drafting editorial contract. The four real final surfaces for scenarios A/B/C have not been certified. Provider-free results are not presented as live journey evidence.

# Failure / Idempotency Evidence

Focused tests cover create timeout after acceptance, update failure, stale preparation, revision changes during provider reads, human text/format edits, provider revision races, missing documents, wrong-case/wrong-folder identity, duplicate identity, replay, unrelated no-op revisions, verified TLS, no automatic mutation retry and staging/production isolation. PostgreSQL tests verify persisted bindings, database concurrency fencing, immutable action/scope, service execution mapping and observation audit. Canonical fixtures/DDL roll back locally.

The staging migration changed only safety DDL and its migration ledger. Canonical case, fact, action, event and attempt counts were unchanged; zero Google actions existed after migration.

# Tests

38 focused checks and 1,045 repository tests passed, including the database-backed integration proofs (45 existing warnings; no skipped tests in the final run). Final repository regression results are recorded in `focused.log`, `focused.xml`, `full_suite.log` and `full_suite.xml` in this directory. External provider HTTP was blocked in the Google tests. Local PostgreSQL was explicitly pinned to localhost. Native Google conversion and real OAuth response shapes remain to be verified against the dedicated staging provider.

# Staging Deployment

The shared runtime, including the previously undeployed nuanced Asana/working-proposal changes, was deployed only to Render staging service `srv-da2m6qdg1s2s73d10ro0`. The staging source branch is `codex/asana-live-working-document`. Migration `20261010000100` was applied only to Supabase staging project `mspcopnsbounmdpivkvq` through its validated session-pooler route. Final deployed commit `587e9c7f8934a7b9c907c6db8a82165914561a8e`, deployment `dep-db51uorbc2fs73e1d19g`, succeeded and hosted health returned OK. Evidence is recorded in `deployment.json` and `health_deployed.json`.

# Provider Gate State

Final hosted health confirmed all seven gates disabled: Outlook inbound, inbound preflight, Outlook execution, Outlook send, Asana execution, Google proposal execution and the global real-provider gate. Values are recorded in `health_deployed.json`. The global switch was also explicitly saved OFF and its live state verified after restart. Google has its independent default-OFF `STAGING_ALLOW_REAL_GOOGLE` flag and `STAGING_ALLOWED_GOOGLE_FOLDER_IDS` allowlist. This campaign did not enable any execution gate. No real Graph, Asana, Google document mutation, OpenAI call or client send was performed.

# Production State

Production service/configuration/database/provider resources were not mutated or deployed. Its existing execution controls remain unchanged and OFF according to the prior provisioned baseline. A read-only production health check returned `status: ok`, `environment: production`; its public health endpoint does not expose the private gate configuration. No production cases, credentials, grants or traffic were created. No paid plan, purchase or upgrade was initiated.

# Remaining Pilot Blockers

1. Authorize and provision the dedicated Google staging OAuth app/drive.file credential and staging folder. This is the new external access boundary; approval is pending.
2. Complete native Google create/update/replay/reconciliation certification through the hosted action path, including content/layout and provider revision validation.
3. Run the three real hosted supervised journeys and compare their final canonical case, Asana, Google document and client draft, closing all gates afterward.

The prior core staging certification remains valid for its covered components. The complete live-workflow certification marker is withheld.

![Staging deployment evidence](/Users/serinya/Documents/WNC Rental Automation/docs/staging/google_proposal/staging_deployed.png)
