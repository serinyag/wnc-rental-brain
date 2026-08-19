# Staging S1B Environment And Safety Hardening

S1B makes the portable Test Console environment-aware and fail-closed before any external staging resources are created.

## APP_ENV

Supported values:

- `local`
- `staging`
- `production`

Behavior:

- Missing `APP_ENV` defaults to implicit `local` only for existing developer workflows.
- Any non-local bind without an explicit `APP_ENV` is rejected at startup.
- `APP_ENV=production` is refused for the Test Console in S1B because no approved production auth boundary exists yet.

## Environment Rules

### Local

- Mutable test clock is enabled.
- Clock routes and controls are available.
- Docker database fallback is allowed when `DATABASE_URL` is absent.
- Fake providers remain the default.

### Staging

- `DATABASE_URL` is required.
- HTTP Basic Auth is required for all Test Console routes except `GET /healthz`.
- Mutable test clock creation is disabled; the runtime always uses `SystemClock`.
- Clock mutation routes fail closed.
- Docker database fallback is disabled.
- Real providers remain optional and disabled by default.
- If real providers are enabled, staging allowlists and provider credentials must already be configured.

### Production

- Test Console startup is refused in S1B.
- Bootstrap helpers also refuse `APP_ENV=production`.

## Staging Authentication

Required variables:

- `STAGING_BASIC_AUTH_USERNAME`
- `STAGING_BASIC_AUTH_PASSWORD`

Security notes:

- Credentials are compared with constant-time checks.
- Authorization headers are not logged.
- Missing staging auth configuration causes startup failure.

## Provider Safety

Staging allowlists:

- `STAGING_ALLOWED_EMAIL_RECIPIENTS`
- `STAGING_ALLOWED_EMAIL_DOMAINS`
- `STAGING_ALLOWED_ASANA_PROJECT_GIDS`

Rules:

- `WORKFLOW_TEST_CONSOLE_ALLOW_REAL_PROVIDERS=false` keeps Outlook and Asana fake.
- If real Outlook is enabled in staging, Microsoft credentials, sender mailbox, and an email allowlist must exist.
- If real Asana is enabled in staging, token, workspace, default/target project, and a project allowlist must exist.

## Health Endpoint

`GET /healthz` returns a safe JSON payload with:

- application status
- database connectivity status
- Phase 5 bootstrap status
- Phase 6 bootstrap status
- provider configuration status

Notes:

- No secrets are returned.
- No Outlook or Asana network calls are made.
- Phase 5 warns when only FTS fallback is available.
- Phase 6 fails when the active approved historical model or embedding coverage is incomplete.

## Bootstrap And Reset Guards

The following DB-writing entrypoints now require an environment-safe boundary:

- `python3 -m tools.phase_05_chunking.generate_pilot --load-db`
- `python3 -m tools.phase_05_chunking.generate_bulk --load-db`
- `python3 -m tools.phase_05_search.generate_embeddings`
- `python3 -m tools.phase_06_search.generate_embeddings`

Guard behavior:

- `APP_ENV=production` is refused.
- `APP_ENV=staging` requires `DATABASE_URL`.
- Docker fallback remains local-only.

## Migration Impact

- Database migration: none
- Workflow semantics changed: none
- Business-rule changes: none
