# Accepted governed drafting baseline

Closure date: 2026-10-03.

Accepted implementation: `7ef15d28bcad6bd8991510e6315ea1d32e12f54b`.

Acceptance marker: **WNC_GOVERNED_DRAFTING_STAGING_ACCEPTED**.

This record freezes the accepted architecture; it does not introduce a new architecture version.

## Architecture

Governed truth → deterministic normalization → Editorial Content Planner v3 → bounded ClientGenerationPayload → single LLM drafter → deterministic safety validation → deterministic required semantic realization → at most one bounded completeness correction → immutable DraftRevision → human review/edit → exact approval → execution.

The pending-action grouping projection sits after planner selection and before client writing. Original semantic obligations retain their individual identities and independent realization checks.

## Accepted behavior

- Missing years resolve deterministically to the next future calendar occurrence relative to the authoritative inbound/case timestamp. Explicit client years take precedence; later explicit corrections supersede inference. Provenance distinguishes inference from explicit client input.
- Governed authority and current-over-historical precedence remain authoritative.
- Known-no validation is scoped to the relevant topic and proposition.
- Editorial selection is deterministic and bounded.
- Compatible current-turn WNC-owned pending checks share one check/report-back writing instruction, while each original semantic meaning remains mandatory.
- A safe semantic omission permits at most one completeness correction against the same frozen contract and plan. Safety failures do not receive that retry.
- Draft revisions are immutable; human edits require successor revisions and fresh exact approval. Approval binds an exact action and revision.

Provider/model: **OpenAI / gpt-5.6-sol**, unchanged from the accepted acceptance evidence. No provider, model or deployment configuration is changed by this record.

## Acceptance evidence

The broad frozen baseline covered **21/21 persisted drafts across 13 scenarios**, with **17 A / 4 B / 0 C / 0 D**, zero unanswered required semantic items and zero material safety failures. Its sole remaining editorial defect was repeated pending-check promises in UAT-006/2.

The accepted implementation then passed the one authorized targeted UAT-006 run (two turns), closing that defect: three original changes independently realized, one consolidated check, one report-back promise, repetition flag zero, and no safety failures. The complete 21-turn model suite was not rerun for this final targeted change. Acceptance combines the broad baseline, full provider-free regressions, and targeted closure evidence.

- [Broad baseline and semantic-retry evidence](uat/required_realization/REQUIRED_REALIZATION_REPORT.md)
- [Targeted pending-check closure](uat/pending_check_consolidation/PENDING_CHECK_CONSOLIDATION_REPORT.md)
- [Acceptance status and measurements](uat/pending_check_consolidation/program_status.json)

No Outlook send, Graph mutation, real Asana execution, or production activity occurred during drafting acceptance. Staging Outlook remained draft-only, with its send gate disabled. There were no C/D drafting failures at closure.

## Freeze rule

Future changes to drafting, planning, realization or date semantics require an explicit new version and regression evidence. They must not silently change this baseline. Documentation updates alone do not create a new architecture version. Drafting prompt design, RAG architecture, authority hierarchy, model/provider, style and frozen drafting UAT are not reopened by Outlook execution certification.
