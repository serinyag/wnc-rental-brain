FROM quay.io/oauth2-proxy/oauth2-proxy:v7.15.0 AS auth
FROM python:3.13-slim-bookworm
COPY --from=auth /bin/oauth2-proxy /usr/local/bin/oauth2-proxy
WORKDIR /app
COPY docs/production_pilot_remediation/deployment/requirements.lock /app/docs/production_pilot_remediation/deployment/requirements.lock
RUN pip install --no-cache-dir -r docs/production_pilot_remediation/deployment/requirements.lock
COPY tools /app/tools
COPY supabase/migrations /app/supabase/migrations
COPY supabase/seed.sql /app/supabase/seed.sql
COPY docs/production_pilot_remediation/MIGRATION_LEDGER.json /app/docs/production_pilot_remediation/MIGRATION_LEDGER.json
COPY pyproject.toml README.md /app/
RUN groupadd --gid 1000 render-secrets && useradd --uid 10001 --create-home --groups render-secrets wnc
USER wnc
ENV APP_ENV=production PYTHONUNBUFFERED=1
CMD ["python", "-m", "tools.production_runtime.supervisor"]
