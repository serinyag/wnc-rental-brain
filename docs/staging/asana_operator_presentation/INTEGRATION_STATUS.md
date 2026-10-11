# Asana operator integration — stopped before live certification

Status: **NOT CERTIFIED**. The accepted operator presentation and narrow adapter compatibility are implemented and tested. The required live follow-up was not performed because the first bounded staging field-reuse request had an unverifiable outcome. No success marker is issued.

## Implemented

- Operator v4 preserves the accepted human copy and removes visible WNC reference/work-hash markers. Legacy v1/v2/v3 contracts and replay keys remain unchanged.
- Supabase action/attempt journals supply exact master/subtask GIDs, semantic obligations, parent bindings and provider scope. No title or description matching adopts an identity. Exact content copies are duplicate evidence only; distinct already-bound obligations may legitimately have identical human wording.
- All bound objects are checked for identity, scope, parent and content before any task write. Human edits, missing identities, unbound exact copies and ambiguous attempts require reconciliation. RENT is retained in the provider binding and checked for drift.
- Rich notes verify exact visible text and named Google Doc link targets/labels while allowing provider HTML serialization changes.
- The staging worker refreshes already-bound, explicitly enrolled operator-v4 cases from governed canonical state. Google runs before Asana; existing journals and leases enforce idempotency. Actual persisted action success is checked before proceeding. An ambiguous outcome fences subsequent polls. No manual proposal-update action is required while the authorized staging gates are active.
- Existing field IDs/options are audited and mapped conservatively. Primary contact is a human-validated canonical contact fact, with the registered verified conversation POC as fallback. It never imports an Asana contact edit. Refreshments do not imply a drink package; staffing/package tags require explicit requests. Asana tags never create availability, supplier, booking or commercial confirmation.
- Redundant change-review copy is cleaned. Completed/superseded work retains its canonical and provider history. The native operator-view cleanup and live historical-row hiding remain unverified because task integration did not run.

## Existing field audit

Reference: Rentals 2026 (`1212669866280530`). Dedicated staging project: `1217642260793817`. Workspace: `1208455784737302`.

| Field | Existing ID | Selected meanings |
| --- | --- | --- |
| RENT | 1212662125912127 | Existing read-only `RENT` custom-ID allocator |
| Room | 1212669866280539 | Studio: 1212669866280540; Whole space: 1212669866280542 |
| Event Type | 1212669866280544 | Exact known category mappings only; unsupported event types blank |
| Client & Ownership | 1212669866280551 | Verified primary-contact email; missing blank |
| Add ons | 1212669866280553 | Existing Catering, Drink package, Tech required and Staff option IDs; explicit requested scope only |

Full definitions/options: [field_audit.json](field_audit.json).

Asana documents that custom IDs are read-only and are allocated incrementally when an existing ID field is reused in a project. No alternative case-ID-derived allocator was introduced. Sources: [Asana custom fields](https://developers.asana.com/docs/custom-fields-guide), [Asana ID fields](https://help.asana.com/s/article/id-custom-fields).

## Bounded live attempt and stop

1. Deployed `d1dc5e402abd57a87023688552e88d018eb4bbab` to staging only.
2. Opened only the global real-provider, Asana and Google staging gates. All Outlook gates remained OFF. There were zero operator-v4 actions/enrolled cases, so the worker had no provider work to execute.
3. At 2026-10-11 13:34:31 UTC, attempted **one** existing RENT-field attachment through `/api/operator/asana-field-reuse`. The hosted boundary returned HTTP 500 `UNEXPECTED_SERVER_ERROR`; Render recorded `ProjectionFailure` without the underlying normalized provider reason. Its exact provider outcome cannot be established from that response. The durable local start artifact prevents a blind retry.
4. Stopped provider mutations immediately. No retry, remaining field attachments, rental-task projection, Google write or synthetic follow-up was attempted.
5. Read-only reconciliation found `custom_field_settings: []` on staging. This proves that no field attachment is visible, not the precise reason for the failure. The UI also provided no custom-field add/reuse controls. A billing/entitlement or permission cause is possible but **not established**. No upgrade, trial, purchase, scope expansion or credential change was performed.
6. Saved the three opened gates as OFF and redeployed the same staging artifact. Render deployment `dep-db5p1bbbc2fs739l3om0` is Live. Hosted health independently confirms **all seven gates disabled**. See [health_closed.json](health_closed.json).

The final local branch commit `1b853b3` additionally tightens drink-package/staffing semantics; it is pushed but not deployed after the stop. Its full suite passes.

## Verification

Latest Phase 8 suite with explicitly selected local PostgreSQL: **852 passed**, 28 existing collection warnings. [Test log](phase8_fields_final.log).

Network-free integration covers legacy transition, exact binding reuse, field removal/scope/contact changes, stable RENT, no duplicate task/document, replay without new attempts/mutations, human/provider drift, unbound-copy detection, distinct bound identical checks, and Google ambiguity preventing subsequent Asana mutations. These are test results, **not live certification claims**.

Read-only closure confirms case revisions remain: 598 = 7, 591 = 8, 593 = 8. There are **zero operator-v4 actions** in staging. Existing master/subtask and Google bindings are retained in [canonical_closed.json](canonical_closed.json).

Production was not deployed, configured or mutated. No Graph calls, sends, OpenAI calls, paid upgrades, rental-task mutations, proposal writes or canonical follow-up changes were performed by this integration attempt. The one Asana field-attachment request remains an uncertified setup attempt with no observed field attachment.

## Remaining before acceptance

- Establish the failed setup request's provider reason using safe diagnostic handling/read-only access evidence; do not blindly retry the durable started request.
- Verify a supported free path to reuse the existing fields, without creating duplicate fields/options or increasing billing.
- Finish the three live card examples and historical-view cleanup, then one bounded governed follow-up proving automatic updates of the same master/subtasks/Google Doc and stable RENT.
- Verify live reconciliation/replay, close all staging gates again, and issue the acceptance marker only after every required check succeeds.

![Gate-off staging deployment](staging_gate_off_deployment.png)
