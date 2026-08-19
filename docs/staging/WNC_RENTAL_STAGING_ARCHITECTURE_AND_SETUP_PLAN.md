# WNC Rental Brain - Staging Architecture And Setup Plan

Date:

- Saturday, August 15, 2026

Repository:

- `/Users/serinya/Documents/WNC Rental Automation`

Current readiness marker:

- `READY_FOR_STAGING_PREPARATION`

Scope:

- planning only
- repository inspection only
- no staging provisioning
- no deployment
- no Microsoft, Supabase, Asana, DNS, or hosting resource creation
- no new Phase 8 feature work

## 1. Executive Summary

The current deployable application is the Phase 8 Rental Workflow Test Console. It is a custom threaded WSGI application started by `python3 -m tools.phase_08_workflow.test_console`, bound locally to `127.0.0.1:8765` by default, and backed by direct SQL helpers that currently shell out to `docker exec ... psql` against a local Supabase container.

The local sandbox is functionally green, but the current runtime is not staging-ready yet. The two biggest blockers are:

1. the database path is still local-Docker-only
2. the application assumes localhost-grade trust, including no authentication and a mutable test clock being available by default

The recommended first staging shape is:

- one access-restricted Python web service
- one separate staging Supabase project
- real system time
- fake providers first
- synthetic RentalCases only
- no public internet exposure without authentication

The recommended first milestone is not real Outlook or real Asana. It is a safe fake-provider staging deployment that proves the app can run off Serinya's laptop with a real remote database and production-like hosting.

The most important repository work before any external setup is:

1. replace the local `docker exec psql` query path with an environment-aware remote database path using `DATABASE_URL`
2. add a real dependency manifest and staging start/deploy entrypoint
3. add `APP_ENV` and fail-closed staging safety controls for auth, clock, and provider allowlists
4. add health/startup validation and a safe bootstrap/reset workflow

## 2. Current Local Architecture

### Current server shape

| Item | Live finding |
| --- | --- |
| Current application server | The Test Console itself is the current application server. |
| Python entry point | `tools.phase_08_workflow.test_console` |
| Start command used in local validation | `python3 -u -m tools.phase_08_workflow.test_console --port 8765` |
| Default bind host | `127.0.0.1` |
| Default bind port | `8765` |
| HTTP stack | Custom WSGI app using `wsgiref.simple_server.make_server(...)` plus `ThreadingMixIn` |
| Framework class | Not Flask, FastAPI, or ASGI; it is a custom WSGI callable |
| Persistent process required | Yes |
| Background worker required today | No |
| Background scheduling required today | No; follow-up evaluation is operator-triggered |
| Built-in health endpoint | No |
| Built-in authentication | No |

### Current runtime flow

The local sandbox currently supports this end-to-end inquiry path:

```text
simulated inbound inquiry
-> structured observations
-> Inquiry Intake
-> current facts + OpenQuestions
-> Inquiry Waiting / Follow-Up
-> structured client-information WorkflowAction
-> response drafting
-> human edit
-> exact-revision approval
-> simulated send
-> ExecutionAttempt
-> WorkflowEvents
```

### Current local validation baseline

Recent authoritative local gate documentation records:

- Phase 8: `186 PASS`
- Phase 7: `127 PASS`
- Phase 5 chunking: `29 PASS`
- Phase 5 search: `24 PASS`
- Phase 6: `6 PASS`
- Drafting DB: `11 / 11 PASS`
- Waiting DB: `7 / 7 PASS`
- Full Supabase: `43 files / 1077 PASS`

Observed local state from the final gate:

- migrations: `38`
- Supabase DB test files: `43`
- Phase 8 Python test files present: `54`
- Phase 5 current chunk sets: `22`
- Phase 5 current chunks: `525`
- searchable current chunks: `492`
- Phase 6 historical search units: `112`
- Phase 6 historical embeddings missing: `0`

### Current provider and clock behavior

| Concern | Live finding |
| --- | --- |
| Default provider mode | Deterministic fake adapters via `build_default_fake_execution_registry(...)` |
| Real provider enable flag | `WORKFLOW_TEST_CONSOLE_ALLOW_REAL_PROVIDERS` |
| Real email adapter | Outlook / Microsoft Graph |
| Real task adapter | Asana |
| Test clock implementation | `MutableTestClock` layered over `SystemClock` |
| Test clock persistence | Not persistent; it is in-memory only |
| Case persistence through restart | Yes, because case state is in the database |
| Clock persistence through restart | No; restart returns to real/current time |

Important nuance:

- the local validation docs correctly proved that case state persists through restart
- the simulated clock itself does not persist through restart
- the current code still constructs a mutable clock by default, so staging would expose test clock controls unless explicitly disabled

### Current database access shape

The live query path is still local-only:

- `tools.phase_05_chunking.generate_pilot.find_local_db_container()` runs `docker ps`
- `tools.phase_05_chunking.generate_pilot.run_supabase_query(...)` runs `docker exec -i <supabase_db_container> psql ...`

This query helper is reused broadly across:

- Phase 5 chunking and search tooling
- Phase 6 retrieval and embedding tooling
- Phase 7 wrappers and adapters
- Phase 8 orchestration repositories and the Test Console service

This is the single biggest staging blocker.

### Dependency and packaging inspection

Observed repository state:

- no `pyproject.toml`
- no `requirements.txt`
- no `package.json`
- no `Dockerfile`
- no `docker-compose.yml`
- no deployment manifest
- no `.openai/hosting.json`

Observed third-party Python imports in the live repo:

- `certifi`
- `docx` / `python-docx`
- `openpyxl`

Observed test tooling in documentation and repo usage:

- `pytest`
- `unittest`

This means the repository is not yet packaged in a way a staging platform can reproducibly install without additional repository work.

### Documentation drift worth noting

The top-level `README.md` still describes the repository primarily as Phase 7-complete and says downstream workflow surfaces are not yet built. That is no longer a fully accurate deployment guide because the Phase 8 Test Console and provider adapters now exist. The staging plan in this document should therefore be treated as the current deployment truth source.

## 3. Staging Objectives

The staging goal is:

> Run the current WNC Rental Brain application outside Serinya's laptop in a production-like but safe environment.

Staging should eventually support:

- deployed Python application
- separate remote staging Supabase
- real system time
- dedicated staging mailbox
- real Microsoft Graph outbound later
- real Asana outbound later
- synthetic RentalCases only
- test recipients only
- no production data
- no production credentials

Staging is not yet intended to support:

- production client traffic
- Outlook inbound webhook handling
- autonomous background workflow infrastructure
- open internet access without auth
- production mailbox or production Asana project use

## 4. Local Vs Staging Vs Production Comparison

| Dimension | Local | Staging | Production |
| --- | --- | --- | --- |
| Purpose | safe development and remediation | safe production-like validation | real business operation |
| App surface | Test Console | restricted Test Console or same operator surface | later operator-facing app surface |
| Database | local Supabase CLI + Docker | separate hosted Supabase project | separate production Supabase project |
| Time source | real time plus simulated clock allowed | real system time only | real system time only |
| Providers | fake by default | fake first, then staged real provider enablement | real providers |
| Data | local fixtures and synthetic cases | synthetic staging cases only | approved live business data |
| Access | localhost | authenticated restricted access | full production auth/security |
| Reset tolerance | high | medium; resettable | low |
| External refs | local fake refs allowed | staging-only external refs | production-only external refs |

## 5. Application Deployment Requirements

The current application needs the following from a staging host:

- Python 3.13-compatible runtime
- one persistent web process
- support for a WSGI application or command-based Python process
- outbound HTTPS to:
  - Supabase / Postgres
  - OpenAI
  - Microsoft Graph
  - Asana
- environment secret injection
- log streaming
- HTTPS
- restart support
- configurable port binding
- health check path
- ability to restrict staging access

Additional deployment-hardening needs discovered during inspection:

- a production-grade WSGI server should replace the current `wsgiref.simple_server` serving path for staging
- a dependency manifest must be added before any PaaS deployment
- the app must stop depending on local Docker for database access

Recommended runtime hardening before staging:

- keep the existing `TestConsoleApp` business logic
- add an importable WSGI entrypoint
- serve it with `gunicorn` or `waitress`
- keep the current module start command only for local development

### Should the Test Console itself be deployed?

Yes.

Reason:

- it is the current application server
- there is no separate production-like operator web app in the repository yet
- it is the only complete end-to-end surface for Phase 8 workflow validation

But it should be deployed only if:

- staging access is authenticated
- simulated clock controls are disabled
- staging remains synthetic-data-only
- real providers remain disabled until later milestones

Background process assessment:

- no separate worker is required for the first staging milestone
- no cron/scheduler is required for the first milestone
- manual operator-triggered follow-up evaluation is sufficient initially

## 6. Environment And Configuration Model

### Current live configuration model

Live env loading today is ad hoc:

- some code reads `os.environ` directly
- provider and OpenAI configuration uses `load_env_value(...)`
- `load_env_value(...)` searches the live shell, then `.env.local`, then `.env`
- no explicit `APP_ENV` exists

Observed live environment variables and switches:

- `SUPABASE_ACCESS_TOKEN`
- `SUPABASE_DB_PASSWORD`
- `SUPABASE_PROJECT_REF`
- `OPENAI_API_KEY`
- `DATABASE_URL`
- `ASANA_ACCESS_TOKEN`
- `ASANA_WORKSPACE_GID`
- `ASANA_DEFAULT_PROJECT_GID`
- `ASANA_TEST_PROJECT_GID`
- `ASANA_API_BASE_URL`
- `ASANA_TIMEOUT_SECONDS`
- `MICROSOFT_TENANT_ID`
- `MICROSOFT_CLIENT_ID`
- `MICROSOFT_CLIENT_SECRET`
- `OUTLOOK_SENDER_MAILBOX`
- `MICROSOFT_GRAPH_BASE_URL`
- `MICROSOFT_AUTHORITY_BASE_URL`
- `OUTLOOK_TIMEOUT_SECONDS`
- `WORKFLOW_TEST_CONSOLE_HOST`
- `WORKFLOW_TEST_CONSOLE_PORT`
- `WORKFLOW_TEST_CONSOLE_ALLOW_NON_LOCAL_BIND`
- `WORKFLOW_TEST_CONSOLE_ALLOW_REAL_PROVIDERS`
- code-supported but not templated: `WORKFLOW_TEST_CONSOLE_QUERY_TIMEOUT_SECONDS`
- code-supported but not templated: `WORKFLOW_TEST_CONSOLE_WORKFLOW_EVENT_LIMIT`
- code-supported but not templated: `OPENAI_ANSWER_MODEL`

Important inspection findings:

- `DATABASE_URL` exists in env templates but is not used by the current runtime
- `ASANA_TEST_PROJECT_GID` exists in env templates but is not used by the current adapter
- there is no current environment discriminator such as `APP_ENV`

### Recommended environment model

Recommended required environment marker:

```text
APP_ENV=local
APP_ENV=staging
APP_ENV=production
```

Recommended behavior by environment:

| Setting | Local | Staging | Production |
| --- | --- | --- | --- |
| file-based `.env` fallback | allowed | discouraged | discouraged |
| mutable test clock | allowed | forbidden | forbidden |
| fake providers | default | default in Milestone 1 | forbidden for real workflows |
| real provider enablement | optional | gated and allowlisted | controlled by production config |
| local bind requirement | yes | no | no |
| auth required | no | yes | yes |
| destructive test controls | allowed selectively | disabled or tightly scoped | disabled |

### Ad hoc assumptions that should be removed

The following assumptions are currently environment-blind and should become explicit:

- local database container discovery via `docker ps`
- SQL execution via `docker exec ... psql`
- mutable clock availability by default
- localhost-only trust instead of authentication
- non-local bind being controlled only by one boolean flag
- provider safety being controlled only by `WORKFLOW_TEST_CONSOLE_ALLOW_REAL_PROVIDERS`

## 7. Local-Only Dependencies Requiring Replacement

| Current Local Dependency | Why It Exists | Can It Run In Staging? | Required Staging Replacement |
| --- | --- | ---: | --- |
| Supabase CLI local stack | local database/test workflow | No | hosted staging Supabase project |
| Docker Desktop | local Supabase containers | No | none for runtime; hosted Supabase instead |
| `docker ps` container discovery | find local DB container name | No | direct Postgres connection via `DATABASE_URL` |
| `docker exec ... psql` | shared raw SQL runner for all phases | No | Python Postgres client path, preferably `psycopg`, using `DATABASE_URL` |
| `wsgiref.simple_server` | local lightweight serving | Not recommended | production-grade WSGI server such as `gunicorn` or `waitress` |
| `.env.local` files | local developer secret storage | No | platform-managed environment secrets |
| mutable `MutableTestClock` | deterministic local time control | No | force `SystemClock` in staging |
| localhost bind default | protect unauthenticated console | No | authenticated non-local deployment plus explicit bind host |
| fake email adapter | safe local execution | Yes, for Milestone 1 only | keep for Milestone 1; later gated real Outlook |
| fake Asana adapter | safe local execution | Yes, for Milestone 1 only | keep for Milestone 1; later gated real Asana |
| test evidence injection controls | manual local scenario creation | Yes, but only with auth and synthetic data | keep only for restricted staging operator flows |
| administrative console controls | full local operator control | Partially | keep case-level controls; disable clock and unsafe reset/purge controls |
| repo-local source files under `sources/phase-01-03/` | Phase 5 chunk generation reads controlled source files | Yes, but only in bootstrap job context | run bootstrap from a repo checkout or package the source corpus into the bootstrap job |
| `tools/setup_local_env.py` | local `.env.local` bootstrap | No | platform secret entry or future deployment script |

Additional local-only issue:

- absolute `/Users/serinya/...` paths were found in documentation links, but not in the runtime code path
- runtime bootstrap logic uses repo-relative paths, which is portable if the staging bootstrap job runs from the repository checkout

## 8. Staging Supabase Plan

### What staging Supabase must contain

The staging Supabase project must eventually contain:

- full migration chain (`38` migrations at inspection time)
- seeded Phase 4 current deterministic rules
- seeded controlled catalogue and governance records
- seeded Phase 6 historical case corpus
- Phase 8 workflow schema, functions, and persistence surfaces
- Phase 5 current chunk sets and chunks
- Phase 5 embedding model registry and embeddings
- Phase 6 historical embedding model registry and embeddings
- runtime-created staging RentalCases, facts, follow-ups, drafts, approvals, execution attempts, and workflow events

### Data classification

| Data category | Examples | Source of truth |
| --- | --- | --- |
| migration-managed | schemas, tables, DB functions, triggers, pgTAP surfaces | `supabase/migrations/` |
| seed-managed | Phase 4 rule truth, controlled source catalogue, Phase 6 historical case records and source metadata | `supabase/seed.sql` |
| generated/bootstrap data | Phase 5 chunk sets/chunks, Phase 5 embeddings, Phase 6 embeddings | Python bootstrap commands |
| runtime operational data | RentalCases, observations, open questions, follow-ups, actions, drafts, execution attempts | application runtime |

### Staging acceptance baseline

Staging should not rely only on "DB is reachable." It should verify knowledge and workflow readiness:

- migrations applied successfully
- seed data present
- Phase 5 current chunk corpus present
- Phase 5 embeddings present for active current-search inputs
- Phase 6 current historical embeddings present
- workflow tables functional
- DB smoke queries succeed without local Docker

Recommended first acceptance targets:

- counts are non-zero for all required bootstrap surfaces
- missing Phase 6 embeddings = `0`
- staging bootstrap output matches the local baseline materially, even if IDs differ

## 9. Phase 5 Bootstrap

### Live repository commands discovered

Current local restore commands:

```bash
npx -y supabase@latest db reset --local --yes
python3 -m tools.phase_05_chunking.generate_bulk --load-db
python3 -m tools.phase_05_search.generate_embeddings
```

### Inspection findings

For `python3 -m tools.phase_05_chunking.generate_bulk --load-db`:

- it is deterministic and content-hash aware
- it checks existing current chunk sets before reloading
- it reads repository source files from `sources/phase-01-03/`
- it requires deterministic parsers backed by:
  - `python-docx`
  - `openpyxl`
- it currently writes through `run_supabase_query(...)`
- that means it still assumes local Docker-backed SQL execution today

For `python3 -m tools.phase_05_search.generate_embeddings`:

- it uses `OPENAI_API_KEY`
- it registers or updates a model row idempotently
- it skips already-current embeddings by `(chunk_id, model_id, input_hash)`
- inserts are `on conflict do nothing`
- it is safe to rerun
- it also depends on the same local-only SQL runner today

### Staging recommendation

Phase 5 bootstrap should remain a one-off administrative/bootstrap step, not an application startup action.

Required repository work before safe staging use:

1. replace `run_supabase_query(...)` with a backend that supports remote Postgres via `DATABASE_URL`
2. add a dependency manifest so the bootstrap runtime can install parser packages reproducibly
3. add a safe staging bootstrap command or script that does not implicitly target production

### Phase 5 staging posture

Recommended staging behavior:

- migrations + seed first
- run Phase 5 chunk generation against staging DB from a checked-out repo
- run Phase 5 embeddings against staging DB using staging OpenAI credentials
- validate that searchable current chunk coverage is complete before deploying or enabling the app

## 10. Phase 6 Bootstrap

### Live repository command discovered

Current local restore command:

```bash
python3 -m tools.phase_06_search.generate_embeddings
```

### Inspection findings

The Phase 6 bootstrap command:

- uses `OPENAI_API_KEY` directly
- registers a historical embedding model idempotently
- inserts historical embeddings `on conflict do nothing`
- reports coverage plus missing/stale source keys
- expects seeded historical search inputs already to exist
- currently depends on the same local-only SQL runner

Important distinction:

- the Phase 6 historical case corpus itself is seed-managed
- the Phase 6 embeddings are generated/bootstrap data

### Staging recommendation

Phase 6 bootstrap is safe as a rerunnable one-off administrative task once the DB access layer is remote-safe.

Required before safe staging use:

1. remote DB support via `DATABASE_URL`
2. staging OpenAI key
3. staging-safe bootstrap wrapper or documented command sequence

Recommended staging order:

```text
migrations
-> seed data
-> Phase 5 chunk generation
-> Phase 5 embeddings
-> Phase 6 embeddings
-> knowledge validation
```

## 11. Microsoft / Outlook Requirements

### Live adapter findings

The Outlook adapter currently reads:

- `MICROSOFT_TENANT_ID`
- `MICROSOFT_CLIENT_ID`
- `MICROSOFT_CLIENT_SECRET`
- `OUTLOOK_SENDER_MAILBOX`
- `MICROSOFT_GRAPH_BASE_URL`
- `MICROSOFT_AUTHORITY_BASE_URL`
- `OUTLOOK_TIMEOUT_SECONDS`

The adapter behavior observed in code:

- uses application credentials, not delegated user login
- obtains a token directly from the Microsoft authority endpoint
- creates drafts under `/users/{sender_mailbox}/messages`
- sends the draft
- verifies sent-message state
- only supports new outbound messages
- only supports one recipient
- rejects cc, bcc, attachments, and reply-mode flows

### Staging external requirements

Based on the inspected code, staging Microsoft setup will require:

- one Microsoft Entra app registration
- one client secret
- admin consent for the application permissions needed to create/send/verify messages
- one dedicated staging sender mailbox

Likely permission inference from the endpoints used:

- `Mail.Send`
- `Mail.ReadWrite`

This permission list is an inference from the live code paths and should be confirmed during the later Microsoft setup task.

### Shared mailbox vs dedicated mailbox

The code addresses `/users/{sender_mailbox}` rather than `/me`, so it can theoretically work with a shared mailbox or a dedicated user mailbox as long as Graph application permissions can access it.

Recommendation:

- prefer a dedicated staging mailbox first
- a shared mailbox is acceptable only if WNC's Microsoft admin confirms Graph app access is configured correctly

### Recommended staging mailbox posture

- mailbox name example: `rental-automation-staging@...`
- no forwarding to real client workflows
- no reuse of a production rental mailbox
- no inbound automation requirement yet

### What Serinya must later bring back

- `MICROSOFT_TENANT_ID`
- `MICROSOFT_CLIENT_ID`
- `MICROSOFT_CLIENT_SECRET`
- `OUTLOOK_SENDER_MAILBOX`
- confirmation that admin consent was granted
- confirmation whether the mailbox is dedicated or shared

## 12. Asana Requirements

### Live adapter findings

The Asana adapter currently reads:

- `ASANA_ACCESS_TOKEN`
- `ASANA_WORKSPACE_GID`
- `ASANA_DEFAULT_PROJECT_GID`
- `ASANA_API_BASE_URL`
- `ASANA_TIMEOUT_SECONDS`

Important inspection finding:

- `ASANA_TEST_PROJECT_GID` exists in env templates and docs but is not used by the live adapter

The adapter:

- authenticates with a bearer token
- requires a workspace GID
- uses a default project GID when the action payload does not supply one
- allows a payload override via `task_surface_project_id`
- optionally accepts section and assignee IDs from the action payload

### Staging external requirements

Staging Asana setup will require:

- one staging-capable Asana token
- one workspace GID
- one dedicated staging project GID
- optional section IDs later if task placement needs structure
- optional assignee IDs later if staging workflows assign tasks

Recommended project naming:

- `WNC Rental Automation - STAGING`

### Safety implication discovered in code

Because the live adapter allows `task_surface_project_id` in the action payload, staging safety must not rely on `ASANA_DEFAULT_PROJECT_GID` alone. The staging runtime should also validate that any project override belongs to an explicit staging allowlist.

### What Serinya must later bring back

- `ASANA_ACCESS_TOKEN`
- `ASANA_WORKSPACE_GID`
- `ASANA_DEFAULT_PROJECT_GID`
- optional section IDs if wanted
- optional assignee IDs if wanted

## 13. OpenAI Requirements

### Features that use OpenAI

Confirmed by inspection:

- Phase 5 embedding generation uses `OPENAI_API_KEY`
- Phase 6 embedding generation uses `OPENAI_API_KEY`
- Phase 7 live bounded answer generation uses `OPENAI_API_KEY`
- Phase 7 live answer model can be overridden by `OPENAI_ANSWER_MODEL`

Current default models in code:

- embedding model: `text-embedding-3-small`
- answer model: `gpt-5.6`

### Staging recommendation

Use a separate staging OpenAI key or project if possible.

Reasons:

- isolates cost tracking
- prevents accidental cross-environment usage confusion
- simplifies later secret rotation

### Required values

- `OPENAI_API_KEY`
- optional `OPENAI_ANSWER_MODEL`

### Important scope note

The current fake-provider Test Console flow does not itself prove that every staging operator action will need live OpenAI at runtime. However, OpenAI is definitely required for the corpus bootstrap commands and any future live Phase 7 answer generation, so it should be treated as part of the staging environment plan.

## 14. Secrets And Configuration Inventory

### Existing live variables

| Variable | Purpose | Secret? | Local value type | Staging source | Required before deploy? | Status |
| --- | --- | ---: | --- | --- | --- | --- |
| `DATABASE_URL` | primary remote Postgres connection for the future staging-safe SQL runner | Yes | Postgres connection string | staging Supabase connection details | Yes | templated today, not wired |
| `OPENAI_API_KEY` | embeddings and live answer generation | Yes | API key | OpenAI staging project/key | Needed before bootstrap | wired |
| `OPENAI_ANSWER_MODEL` | optional answer model override | No | model code | repository config choice | No | code-supported, not templated |
| `SUPABASE_ACCESS_TOKEN` | Supabase CLI/admin operations | Yes | user/project token | Supabase account | Needed for remote CLI/admin tasks, not app runtime | templated |
| `SUPABASE_PROJECT_REF` | identify staging Supabase project | No | project ref | staging Supabase project | Needed for CLI/admin tasks | templated |
| `SUPABASE_DB_PASSWORD` | database admin/password workflows | Yes | password | staging Supabase project | Needed for DB/admin/bootstrap workflows | templated |
| `ASANA_ACCESS_TOKEN` | Asana API auth | Yes | bearer token | Asana staging token | No for Milestone 1; yes before real Asana | wired |
| `ASANA_WORKSPACE_GID` | Asana workspace target | No | GID string | Asana workspace | No for Milestone 1; yes before real Asana | wired |
| `ASANA_DEFAULT_PROJECT_GID` | default Asana project target | No | GID string | staging Asana project | No for Milestone 1; yes before real Asana | wired |
| `ASANA_TEST_PROJECT_GID` | candidate test project marker | No | GID string | staging Asana project | No | templated only, currently unused |
| `ASANA_API_BASE_URL` | Asana endpoint override | No | URL | default is fine | No | wired |
| `ASANA_TIMEOUT_SECONDS` | Asana timeout | No | integer seconds | env tuning | No | wired |
| `MICROSOFT_TENANT_ID` | Microsoft tenant selection | No | tenant ID | WNC Microsoft 365 admin | No for Milestone 1; yes before real Outlook | wired |
| `MICROSOFT_CLIENT_ID` | Graph app ID | No | client ID | Microsoft app registration | No for Milestone 1; yes before real Outlook | wired |
| `MICROSOFT_CLIENT_SECRET` | Graph app secret | Yes | secret string | Microsoft app registration | No for Milestone 1; yes before real Outlook | wired |
| `OUTLOOK_SENDER_MAILBOX` | sender mailbox identity | No | email address | dedicated staging mailbox | No for Milestone 1; yes before real Outlook | wired |
| `MICROSOFT_GRAPH_BASE_URL` | Graph API override | No | URL | default is fine | No | wired |
| `MICROSOFT_AUTHORITY_BASE_URL` | authority endpoint override | No | URL | default is fine | No | wired |
| `OUTLOOK_TIMEOUT_SECONDS` | Outlook timeout | No | integer seconds | env tuning | No | wired |
| `WORKFLOW_TEST_CONSOLE_HOST` | bind host | No | hostname/IP | hosting env | Yes | wired |
| `WORKFLOW_TEST_CONSOLE_PORT` | bind port | No | integer | hosting env / platform port | Yes | wired |
| `WORKFLOW_TEST_CONSOLE_ALLOW_NON_LOCAL_BIND` | allow non-local bind | No | boolean | staging deploy config | Yes | wired |
| `WORKFLOW_TEST_CONSOLE_ALLOW_REAL_PROVIDERS` | allow real provider execution | No | boolean | staging deploy config | Yes | wired |
| `WORKFLOW_TEST_CONSOLE_QUERY_TIMEOUT_SECONDS` | DB query timeout | No | float seconds | deploy tuning | No | code-supported, not templated |
| `WORKFLOW_TEST_CONSOLE_WORKFLOW_EVENT_LIMIT` | max workflow events to render | No | integer | deploy tuning | No | code-supported, not templated |

### Proposed new variables before staging

| Variable | Purpose | Secret? | Staging source | Required before deploy? |
| --- | --- | ---: | --- | --- |
| `APP_ENV` | explicit environment detection | No | deploy config | Yes |
| `STAGING_BASIC_AUTH_USERNAME` | staging console auth | Yes | deploy config | Yes if staging is web-accessible |
| `STAGING_BASIC_AUTH_PASSWORD` | staging console auth | Yes | deploy config | Yes if staging is web-accessible |
| `STAGING_ALLOWED_EMAIL_RECIPIENTS` | explicit Outlook recipient allowlist | No | deploy config | Required before real Outlook |
| `STAGING_ALLOWED_EMAIL_DOMAINS` | secondary domain-level send guard | No | deploy config | Optional but recommended before real Outlook |
| `STAGING_ALLOWED_ASANA_PROJECT_GIDS` | allowed Asana project targets | No | deploy config | Required before real Asana |

Supabase URL / anon key note:

- the current Python runtime does not use a Supabase REST URL or anon key
- the current app talks directly to Postgres
- therefore the critical staging runtime variable is `DATABASE_URL`, not a browser-exposed Supabase key

## 15. Access Control Recommendation

The current app has no authentication and relies on localhost binding as its safety boundary. That is insufficient for staging.

Minimum recommended staging access control:

1. app-level HTTP basic auth
2. HTTPS-only hosting
3. no anonymous internet exposure

Recommended first staging access posture:

- application protected by basic auth
- optional platform IP restriction if the hosting vendor supports it cleanly
- no public index without credentials

Why this is the simplest appropriate approach:

- the current app is a server-rendered operator console, not a public website
- it contains administrative workflow controls
- it may eventually hold client-like test data and governed historical data
- adding full user auth before first staging is heavier than necessary
- basic auth is sufficient for Milestone 1 if everything else is staging-only

## 16. Data And Confidentiality Posture

### Staging data rules

Non-negotiable staging rules:

- no production Supabase credentials
- no production Outlook mailbox
- no production Asana project
- no production client email recipients
- synthetic RentalCases only
- reserved test email recipients only
- no uncontrolled upload of real WNC client correspondence

### Phase 5 posture

Phase 5 governed knowledge is repository-approved operational/business knowledge. It is not public data, but it is already intentionally preserved in the repository and local database bootstrap flow.

Recommendation:

- treat Phase 5 data as internal business knowledge
- allow it in staging if staging access is restricted

### Phase 6 posture

The Phase 6 historical corpus is more sensitive.

Repository evidence shows:

- `9` historical precedents are present
- commercial sensitivity is mostly `MEDIUM` to `HIGH`
- some cases confirm personal information
- some cases are marked `restricted`
- the documentation explicitly warns that raw historical evidence would be more sensitive than the curated narrative

This creates a real staging data-governance decision:

- a private, access-restricted staging environment may be acceptable for the currently governed Phase 6 corpus if WNC explicitly approves that posture
- a public or weakly protected staging environment is not acceptable for this corpus

Recommended planning stance:

- do not silently move the current Phase 6 corpus into cloud staging without explicit approval
- if approval is uncertain, either:
  - keep Milestone 1 staging private and access-restricted, or
  - create a sanitized staging historical corpus later

This document does not make a legal determination; it flags the repository-evidenced sensitivity clearly.

## 17. Logging And Observability

### Current logging posture

The current server already logs:

- request method
- path
- HTTP status
- failure code
- request duration

The service layer also logs some route-level timing and query count details.

### Recommended staging logging additions

Add or standardize:

- request ID
- `rental_case_id`
- `workflow_action_id`
- `execution_attempt_id`
- normalized failure code
- stage timings
- provider mode

Do not log by default:

- secrets
- auth headers
- provider tokens
- full email bodies
- full raw inbound evidence text unless explicitly needed in a protected debug mode

### Recommended initial observability tooling

For first staging:

- platform logs are sufficient
- no mandatory external monitoring tool is required before Milestone 1

Later:

- add lightweight error monitoring before real Outlook is enabled if desired

### Health check strategy

Recommended future health endpoints/checks:

- application health:
  - process is running
  - routing stack can answer a simple request
- database health:
  - staging DB reachable through the staging-safe query path
- knowledge health:
  - Phase 5 current chunk corpus exists
  - Phase 5 embeddings exist for active current-search inputs
- historical health:
  - Phase 6 active historical embedding model exists
  - Phase 6 coverage is complete enough for the supported runtime
- provider configuration health:
  - show configured vs unconfigured safely
  - do not perform real provider side effects

Recommended first staging endpoint:

- `/healthz`

Recommended health result policy:

- fail if the web process or DB is unavailable
- fail if required bootstrap knowledge surfaces are missing
- warn, but do not necessarily fail, when a later-stage provider is intentionally disabled

### Startup validation

Recommended fail-fast startup validation for staging:

- `APP_ENV` is present and valid
- bind host rules are compatible with the environment
- database is reachable
- required schema version is present
- Phase 5 corpus exists
- Phase 5 embeddings exist
- Phase 6 active model exists
- provider flags are internally consistent with allowlists
- simulated clock is not enabled when `APP_ENV=staging`

## 18. Provider Safety Controls

### Current live provider control

The live runtime has one main provider gate:

- `WORKFLOW_TEST_CONSOLE_ALLOW_REAL_PROVIDERS`

That is necessary but not sufficient for staging safety.

### Recommended staging provider sequence

| Stage | `WORKFLOW_TEST_CONSOLE_ALLOW_REAL_PROVIDERS` | Outlook | Asana | Required extra guard |
| --- | --- | --- | --- | --- |
| Milestone 1 | `false` | fake | fake | none beyond auth |
| Milestone 2 | `true` | fake | real | Asana project allowlist |
| Milestone 3 | `true` | real | real | Outlook recipient allowlist + Asana project allowlist |

### Required technical safety rules

Recommended fail-closed enforcement:

- if `APP_ENV=staging` and real providers are enabled:
  - Outlook sends must be rejected unless the recipient is allowlisted
  - Asana creates must be rejected unless the project GID is allowlisted
- if `APP_ENV=production` and fake providers are still configured:
  - startup should fail

Cross-environment external references should be forbidden conceptually:

- staging-created provider references should remain staging-only
- production references should never be imported into staging workflows

### Simulated clock behavior in staging

Required staging behavior:

- system clock only
- no visible clock advance/set/reset controls
- no mutable `MutableTestClock` instance
- any attempt to invoke clock-control routes should fail closed

The current live code does not yet enforce this. It must be added before staging.

## 19. Bootstrap And Reset Plan

### Recommended conceptual bootstrap sequence

The first safe staging bootstrap sequence should be:

```text
create empty staging Supabase
-> apply migrations
-> load seed data
-> run Phase 5 chunk bootstrap
-> run Phase 5 embedding bootstrap
-> run Phase 6 embedding bootstrap
-> run DB / knowledge health validation
-> deploy application
-> create synthetic staging cases
-> run smoke tests
```

### Why deploy after bootstrap

The current repository does not yet have startup validation. If the app is deployed before the corpus bootstrap succeeds, it may start in a misleading partially functional state. It is safer to bootstrap the staging DB first, then deploy the app with health checks that verify the environment is complete.

### Recommended reset strategy for early staging

Early staging can be safely reset by:

```text
wipe staging DB
-> reapply migrations
-> reload seed data
-> rerun Phase 5 bootstrap
-> rerun Phase 5 embeddings
-> rerun Phase 6 embeddings
-> recreate synthetic staging cases
```

Hard boundary:

- any reset tooling must be staging-specific and must not be able to target production implicitly

### Local bootstrap reproducibility recommendation

A reproducible local bootstrap script is now worthwhile.

Recommendation:

- create a local bootstrap/reset command during staging implementation, before first staging deployment

Reason:

- local restore now depends on several manual steps
- the staging bootstrap should mirror the same sequence
- reducing manual drift locally will make staging preparation safer

### Staging bootstrap automation recommendation

Also create a separate staging bootstrap command or script during staging implementation.

It should eventually:

- require `APP_ENV=staging`
- require `DATABASE_URL`
- refuse to run against production
- run knowledge bootstrap in the correct order
- print coverage/health summaries

## 20. Smoke-Test Plan

### Milestone 1: fake-provider staging smoke test

Sequence:

```text
health check
-> create synthetic inquiry
-> inject synthetic evidence
-> run Inquiry Intake
-> run Inquiry Waiting
-> evaluate follow-ups
-> generate draft
-> human edit
-> approve exact revision
-> fake send
-> reload and verify persisted state
```

Success criteria:

- no direct SQL needed
- all operations succeed through the deployed UI/routes
- persisted case state survives service restart
- no simulated clock controls are available
- fake provider references persist correctly

Failure criteria:

- any route still depends on local Docker
- provider execution escapes the fake path
- stage cannot persist case state
- missing corpus or embedding state breaks ordinary flow

### Milestone 2: real Asana smoke test

Sequence:

```text
start from a staging-safe case
-> trigger governed internal task action
-> execute action in real mode
-> verify task lands in staging Asana project
-> verify external reference is persisted
```

Success criteria:

- task created only in allowlisted staging project
- external reference stored cleanly
- no cross-project leakage

### Milestone 3: real Outlook smoke test

Sequence:

```text
approved staging draft
-> execute action in real mode
-> send from staging mailbox
-> deliver only to allowlisted test recipient
-> persist external message reference
```

Success criteria:

- message sent from staging mailbox only
- recipient matches explicit allowlist
- external reference persisted cleanly

### Outlook inbound remains later

Real Outlook inbound should remain out of scope for first staging.

It adds:

- webhook/subscription transport
- inbound message identity handling
- additional external event complexity

### Background scheduling and n8n assessment

Recommendation for first staging:

- keep follow-up evaluation manual
- do not add a worker queue yet
- do not add n8n yet

Reason:

- the current app already exposes operator-triggered follow-up evaluation
- the first staging objective is safe off-laptop execution, not automation breadth
- n8n is more likely to be useful later for Outlook inbound events or scheduled triggers than for the first outbound test

## 21. Hosting Recommendation

### Requirements-first candidate comparison

| Candidate | Compatibility | Complexity | Cost class | Secrets/logs | Microsoft/Supabase connectivity | Deployment friction |
| --- | --- | --- | --- | --- | --- | --- |
| Render web service | High | Low | Low | Good | Standard outbound HTTPS works | Low once dependency manifest exists |
| Railway | High | Low | Low | Good | Standard outbound HTTPS works | Low once dependency manifest exists |
| Azure App Service / Container Apps | High | Moderate | Moderate | Strong | Especially comfortable if WNC wants Microsoft-native access patterns later | Higher than needed for first staging |

### Recommended default

Recommended default hosting shape:

- Render web service
- one web process
- environment-managed secrets
- HTTPS
- app-level basic auth

Why Render is the best default fit right now:

- the app is one small persistent Python web process
- no worker is required yet
- no container is required yet
- outbound HTTPS to Supabase, OpenAI, Microsoft Graph, and Asana is straightforward
- logs and env management are simple
- cost is usually low

### Alternative options

Use Railway if:

- Serinya prefers a very lightweight deploy workflow and simple environment management

Use Azure App Service or Container Apps if:

- WNC already operates comfortably in Azure
- built-in Microsoft-aligned access patterns are more important than setup simplicity

### Containerization decision

Recommendation:

```text
do not containerize yet
```

Reasoning:

- the current app is simple enough to run directly on a Python PaaS
- current Docker usage exists because local Supabase CLI depends on Docker, not because the application requires container-specific behavior
- the bigger blockers are dependency packaging, remote DB access, auth, and safety controls
- containerization can follow later if reproducibility or platform portability becomes painful

## 22. CI/CD Recommendation

### Migration strategy

For the first staging rollout, the simplest safe migration strategy is:

- one controlled manual staging migration/bootstrap run
- executed intentionally against the staging project only
- not yet auto-run on every deploy

Reason:

- the repository does not yet have a staging-safe remote DB runner
- staging bootstrap involves generated corpora, not migrations alone
- the first rollout should be explicit and observable

Recommended future shape:

- manual or scripted staging bootstrap from a controlled operator machine or one-off job
- later promote to CI/CD only after the staging bootstrap path is proven safe

### CI recommendation

Recommendation:

```text
useful before real-provider staging, but not a hard prerequisite before the first fake-provider staging deployment
```

Reasoning:

- the repository already has strong manual local validation coverage
- the immediate blocker is environment/deployment hardening, not test absence
- a minimal CI pass becomes much more valuable once deployment files, startup validation, and bootstrap scripts exist

Recommended minimal CI once added:

- `python3 -m pytest tools/phase_08_workflow/tests -q`
- `python3 -m pytest tools/phase_07_reasoning/tests -q`
- `python3 -m pytest tools/phase_05_chunking/tests -q`
- `python3 -m pytest tools/phase_05_search/tests -q`
- `python3 -m pytest tools/phase_06_search/tests -q`
- `npx -y supabase@latest test db --local`
- dependency/install sanity

## 23. Codex Vs Serinya Responsibility Matrix

| Task | Codex | Serinya / External | Needs input from Serinya? | Order |
| --- | ---: | ---: | ---: | ---: |
| Add dependency manifest and deployable WSGI entrypoint | Yes | No | No | 1 |
| Replace local Docker SQL runner with `DATABASE_URL`-based remote-safe query execution | Yes | No | No | 2 |
| Add `APP_ENV`, staging auth, clock restrictions, and provider safety guards | Yes | No | No | 3 |
| Add health checks and startup validation | Yes | No | No | 4 |
| Add local/staging bootstrap scripts and reset protections | Yes | No | No | 5 |
| Create staging Supabase project | No | Yes | No | 6 |
| Create hosting project/account | No | Yes | Possibly | 7 |
| Create Microsoft staging mailbox and app registration | No | Yes | Yes | 8 |
| Grant Microsoft admin consent | No | Yes | Yes | 9 |
| Create Asana staging project and token | No | Yes | Yes | 10 |
| Create separate staging OpenAI key/project if desired | No | Yes | Yes | 11 |
| Return all IDs/secrets/config values to Codex | No | Yes | No | 12 |
| Configure staging secrets and perform first fake-provider deploy | Yes | Yes | Yes | 13 |
| Run staging bootstrap and smoke tests | Yes | Yes | Yes | 14 |
| Enable real Asana staging | Yes | Yes | Yes | 15 |
| Enable real Outlook outbound staging | Yes | Yes | Yes | 16 |

## 24. External Setup Checklist For Serinya

This checklist is written as a non-DevOps handoff.

### 1. Create a staging Supabase project

Where to go:

- Supabase dashboard

What to create:

- one brand-new project only for staging

Suggested name:

- `wnc-rental-brain-staging`

What not to do:

- do not reuse the local project
- do not connect this to any production client data

What to copy back afterward:

- project ref
- database password
- connection string / Postgres URL
- any required access token for CLI/admin work

### 2. Create a staging hosting project

Where to go:

- the chosen hosting platform account

What to create:

- one web service for this repo

Suggested name:

- `wnc-rental-brain-staging`

What not to do:

- do not expose it publicly without auth
- do not add production DNS

What to copy back afterward:

- service URL
- how secrets are entered
- any platform-specific start/health check settings that need to be filled in

### 3. Ask the Microsoft 365 admin to create a staging mailbox

Where to go:

- WNC Microsoft 365 / Entra admin area

What to create:

- one dedicated staging sender mailbox if possible

Suggested name:

- `rental-automation-staging`

What not to do:

- do not reuse the production rental mailbox
- do not enable forwarding to real clients

What to copy back afterward:

- exact mailbox email address
- whether it is a dedicated mailbox or shared mailbox

### 4. Ask the Microsoft 365 admin to create an app registration

Where to go:

- Microsoft Entra app registrations

What to create:

- one app registration only for staging automation

What not to do:

- do not reuse a production app registration if it can be avoided

What to copy back afterward:

- tenant ID
- client ID
- client secret
- confirmation that admin consent was granted

### 5. Create a staging Asana project

Where to go:

- Asana workspace used for internal ops

What to create:

- one dedicated staging project

Suggested name:

- `WNC Rental Automation - STAGING`

What not to do:

- do not point staging to a live production operations project

What to copy back afterward:

- workspace GID
- project GID
- optional section IDs if desired

### 6. Create or choose an Asana token

Where to go:

- Asana developer/app token area

What to create:

- one token allowed to create tasks in the staging project

What not to do:

- do not use a token that can silently post into production projects if avoidable

What to copy back afterward:

- the token value

### 7. Create a staging OpenAI key if desired

Where to go:

- OpenAI project/account used for WNC work

What to create:

- a separate staging key or project if possible

What not to do:

- do not share a personal key casually across environments if it can be separated

What to copy back afterward:

- `OPENAI_API_KEY`
- any chosen answer-model override if different from default

## 25. Ordered Staging Rollout

| Step | Objective | Owner | Acceptance gate | Hard stop |
| --- | --- | --- | --- | --- |
| `S0` | freeze staging architecture | Codex | this plan accepted | no provisioning yet |
| `S1` | repository hardening for off-laptop runtime | Codex | remote-safe DB path, auth, env model, health checks designed and implemented | do not use live external providers yet |
| `S2` | create external staging resources | Serinya / external admins | staging Supabase, host shell, mailbox, app registration, Asana project exist | no production resources reused |
| `S3` | configure secrets and deploy fake-provider staging app | Codex + Serinya | app boots, auth works, health passes | real providers remain disabled |
| `S4` | bootstrap staging knowledge state | Codex + Serinya | Phase 5/6 validation passes on staging DB | stop if corpus/embedding coverage incomplete |
| `S5` | run fake-provider end-to-end staging validation | Codex + Serinya | full synthetic inquiry journey passes | stop if any direct SQL/manual DB repair is needed |
| `S6` | enable real Asana only | Codex + Serinya | staging task created in allowlisted project | stop if tasks can escape project allowlist |
| `S7` | enable real Outlook outbound | Codex + Serinya | one allowlisted test email sent and referenced | stop if arbitrary recipients are possible |
| `S8` | revalidate the inquiry MVP in staging | Codex + Serinya | current app behaves safely with real providers | stop if access, logging, or data boundaries fail |
| `S9` | decide whether Outlook inbound is worth adding | Serinya + Codex | explicit decision recorded | do not build inbound by default |

## 26. Known Unknowns

The repository inspection could not answer these external questions:

- Who administers WNC Microsoft 365?
- Can that admin create a dedicated staging mailbox and app registration?
- Does the current Asana workspace allow creation of a staging project?
- Which hosting vendor/account does Serinya prefer or already control?
- Does WNC approve placing the current governed Phase 6 historical corpus in a private cloud staging environment?
- Is a separate staging OpenAI project/key desired?

Recommended default if these remain unanswered:

- use Render
- use a dedicated staging Supabase project
- use fake providers first
- keep staging private/authenticated
- do not enable real Outlook until allowlists exist

## 27. Risks

Highest-risk issues discovered:

1. The runtime still depends on `docker exec ... psql` for nearly all database-backed functionality.
2. The default service clock is still mutable, so simulated clock controls would exist in staging unless explicitly disabled.
3. The current server has no authentication and relies on localhost for safety.
4. The repository has no dependency manifest or production deployment entrypoint.
5. The current real-provider flag is too coarse by itself; there are no allowlists today.
6. The Asana adapter allows project override through payload, so default-project config alone is not a sufficient staging guard.
7. The Phase 6 corpus contains commercially sensitive and sometimes PI-bearing historical narratives, so staging data placement needs explicit approval.

Secondary risks:

- `DATABASE_URL` exists but is not yet wired, which can create false confidence
- `ASANA_TEST_PROJECT_GID` exists in templates but is unused, which can create false confidence
- `README.md` lags the current Phase 8 runtime reality

## 28. Hard Boundaries

This plan assumes the following non-negotiable boundaries:

- staging database must be separate from production
- staging credentials must be separate from production
- staging mailbox must be separate from production
- staging Asana project must be separate from production
- staging recipients must be explicitly allowlisted
- simulated clock must not operate in staging
- no public anonymous console access
- no production client data in early staging
- no automatic staging reset command may target production

No provisioning performed during this task:

- external accounts created: `0`
- cloud resources created: `0`
- deployments made: `0`
- DNS changes: `0`
- Microsoft app registrations created: `0`
- Asana projects created: `0`
- Supabase projects created: `0`
- secrets created or rotated: `0`

## 29. Immediate Next Action

The recommended immediate next action is a controlled Codex repository-hardening task before any external setup.

That task should cover:

1. add a dependency manifest and deployable WSGI entrypoint
2. replace the local Docker SQL runner with an environment-aware `DATABASE_URL` path
3. add `APP_ENV`
4. disable mutable test clock behavior outside local
5. add staging auth, provider allowlists, health checks, and startup validation

Reason:

- external resources should not be created until the application can actually run safely off-laptop
- the local-Docker DB dependency is the main architectural blocker
- staging safety must be fail-closed before any real mailbox or real Asana project is connected

Documentation path:

- [WNC_RENTAL_STAGING_ARCHITECTURE_AND_SETUP_PLAN.md](/Users/serinya/Documents/WNC%20Rental%20Automation/docs/staging/WNC_RENTAL_STAGING_ARCHITECTURE_AND_SETUP_PLAN.md)
