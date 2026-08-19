from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from tools.phase_05_search.semantic_common import load_env_value


APP_ENV_ENV = "APP_ENV"
DATABASE_URL_ENV = "DATABASE_URL"
STAGING_BASIC_AUTH_USERNAME_ENV = "STAGING_BASIC_AUTH_USERNAME"
STAGING_BASIC_AUTH_PASSWORD_ENV = "STAGING_BASIC_AUTH_PASSWORD"
STAGING_ALLOWED_EMAIL_RECIPIENTS_ENV = "STAGING_ALLOWED_EMAIL_RECIPIENTS"
STAGING_ALLOWED_EMAIL_DOMAINS_ENV = "STAGING_ALLOWED_EMAIL_DOMAINS"
STAGING_ALLOWED_ASANA_PROJECT_GIDS_ENV = "STAGING_ALLOWED_ASANA_PROJECT_GIDS"

MICROSOFT_TENANT_ID_ENV = "MICROSOFT_TENANT_ID"
MICROSOFT_CLIENT_ID_ENV = "MICROSOFT_CLIENT_ID"
MICROSOFT_CLIENT_SECRET_ENV = "MICROSOFT_CLIENT_SECRET"
OUTLOOK_SENDER_MAILBOX_ENV = "OUTLOOK_SENDER_MAILBOX"

ASANA_ACCESS_TOKEN_ENV = "ASANA_ACCESS_TOKEN"
ASANA_WORKSPACE_GID_ENV = "ASANA_WORKSPACE_GID"
ASANA_DEFAULT_PROJECT_GID_ENV = "ASANA_DEFAULT_PROJECT_GID"

LOCAL_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})


class RuntimeConfigurationError(RuntimeError):
    pass


class AppEnvironment(str, Enum):
    LOCAL = "local"
    STAGING = "staging"
    PRODUCTION = "production"

    @classmethod
    def parse(cls, raw_value: str | None) -> tuple[AppEnvironment, bool]:
        normalized = _normalize_optional_text(raw_value)
        if normalized is None:
            return cls.LOCAL, False
        lowered = normalized.lower()
        for member in cls:
            if member.value == lowered:
                return member, True
        raise RuntimeConfigurationError(
            f"{APP_ENV_ENV} must be one of: local, staging, production."
        )


@dataclass(frozen=True)
class BasicAuthCredentials:
    username: str
    password: str


@dataclass(frozen=True)
class AppRuntimeConfig:
    app_env: AppEnvironment = AppEnvironment.LOCAL
    app_env_explicit: bool = False
    database_url: str | None = None
    staging_basic_auth_username: str | None = None
    staging_basic_auth_password: str | None = None
    staging_allowed_email_recipients: tuple[str, ...] = ()
    staging_allowed_email_domains: tuple[str, ...] = ()
    staging_allowed_asana_project_gids: tuple[str, ...] = ()

    @classmethod
    def local_default(cls) -> AppRuntimeConfig:
        return cls()

    @classmethod
    def from_env(cls) -> AppRuntimeConfig:
        app_env, explicit = AppEnvironment.parse(load_env_value(APP_ENV_ENV))
        return cls(
            app_env=app_env,
            app_env_explicit=explicit,
            database_url=_normalize_optional_text(load_env_value(DATABASE_URL_ENV)),
            staging_basic_auth_username=_normalize_optional_text(load_env_value(STAGING_BASIC_AUTH_USERNAME_ENV)),
            staging_basic_auth_password=_normalize_optional_text(load_env_value(STAGING_BASIC_AUTH_PASSWORD_ENV)),
            staging_allowed_email_recipients=_parse_recipient_allowlist(load_env_value(STAGING_ALLOWED_EMAIL_RECIPIENTS_ENV)),
            staging_allowed_email_domains=_parse_domain_allowlist(load_env_value(STAGING_ALLOWED_EMAIL_DOMAINS_ENV)),
            staging_allowed_asana_project_gids=_parse_generic_allowlist(load_env_value(STAGING_ALLOWED_ASANA_PROJECT_GIDS_ENV)),
        )

    @property
    def is_local(self) -> bool:
        return self.app_env is AppEnvironment.LOCAL

    @property
    def is_staging(self) -> bool:
        return self.app_env is AppEnvironment.STAGING

    @property
    def is_production(self) -> bool:
        return self.app_env is AppEnvironment.PRODUCTION

    def allows_docker_db_fallback(self) -> bool:
        return self.is_local

    def allows_mutable_test_clock(self) -> bool:
        return self.is_local

    def requires_basic_auth(self) -> bool:
        return self.is_staging

    def basic_auth_credentials(self) -> BasicAuthCredentials | None:
        if not self.requires_basic_auth():
            return None
        if self.staging_basic_auth_username is None or self.staging_basic_auth_password is None:
            return None
        return BasicAuthCredentials(
            username=self.staging_basic_auth_username,
            password=self.staging_basic_auth_password,
        )

    def email_allowlist_count(self) -> int:
        return len(self.staging_allowed_email_recipients) + len(self.staging_allowed_email_domains)

    def is_email_recipient_allowed(self, recipient_email: str) -> bool:
        normalized_email = _normalize_optional_text(recipient_email)
        if normalized_email is None:
            return False
        lowered_email = normalized_email.lower()
        if lowered_email in self.staging_allowed_email_recipients:
            return True
        _, _, domain = lowered_email.partition("@")
        if not domain:
            return False
        return domain in self.staging_allowed_email_domains

    def is_asana_project_allowed(self, project_gid: str) -> bool:
        normalized_gid = _normalize_optional_text(project_gid)
        if normalized_gid is None:
            return False
        return normalized_gid in self.staging_allowed_asana_project_gids


def is_local_host(host: str) -> bool:
    return host in LOCAL_HOSTS


def validate_test_console_startup(
    *,
    runtime: AppRuntimeConfig,
    host: str,
    allow_non_local_bind: bool,
    allow_real_providers: bool,
) -> None:
    if runtime.is_production:
        raise RuntimeConfigurationError(
            "APP_ENV=production is not supported for Test Console startup in S1B. "
            "Approved production auth and runtime policy are still pending."
        )

    host_is_local = is_local_host(host)
    if not host_is_local and not runtime.app_env_explicit:
        raise RuntimeConfigurationError(
            f"{APP_ENV_ENV} must be explicitly set before using a non-local bind."
        )

    if runtime.is_local:
        if not host_is_local and not allow_non_local_bind:
            raise RuntimeConfigurationError(
                f"Non-local bind {host!r} is not allowed without WORKFLOW_TEST_CONSOLE_ALLOW_NON_LOCAL_BIND=true."
            )
        return

    if runtime.database_url is None:
        raise RuntimeConfigurationError(
            f"{DATABASE_URL_ENV} is required when {APP_ENV_ENV}={runtime.app_env.value}."
        )

    if runtime.is_staging and runtime.basic_auth_credentials() is None:
        raise RuntimeConfigurationError(
            f"{STAGING_BASIC_AUTH_USERNAME_ENV} and {STAGING_BASIC_AUTH_PASSWORD_ENV} are required when "
            f"{APP_ENV_ENV}=staging."
        )

    if runtime.is_staging and allow_real_providers:
        validate_staging_real_provider_configuration(runtime)


def validate_staging_real_provider_configuration(runtime: AppRuntimeConfig) -> None:
    if not runtime.is_staging:
        return
    outlook_requested = _outlook_real_provider_requested(runtime)
    asana_requested = _asana_real_provider_requested(runtime)
    if not outlook_requested and not asana_requested:
        raise RuntimeConfigurationError(
            "Staging real provider mode requires real Outlook or real Asana configuration."
        )
    if outlook_requested:
        _validate_staging_outlook_configuration(runtime)
    if asana_requested:
        _validate_staging_asana_configuration(runtime)


def validate_bootstrap_environment(
    *,
    operation_name: str,
    runtime: AppRuntimeConfig | None = None,
) -> AppRuntimeConfig:
    resolved_runtime = runtime or AppRuntimeConfig.from_env()
    if resolved_runtime.is_production:
        raise RuntimeConfigurationError(
            f"{operation_name} is disabled when {APP_ENV_ENV}=production."
        )
    if resolved_runtime.is_staging and resolved_runtime.database_url is None:
        raise RuntimeConfigurationError(
            f"{operation_name} requires {DATABASE_URL_ENV} when {APP_ENV_ENV}=staging."
        )
    return resolved_runtime


def _require_env_values(*names: str) -> None:
    missing = [name for name in names if _normalize_optional_text(load_env_value(name)) is None]
    if missing:
        joined = ", ".join(missing)
        raise RuntimeConfigurationError(
            f"Missing required environment configuration: {joined}."
        )


def _any_env_values(*names: str) -> bool:
    return any(_normalize_optional_text(load_env_value(name)) is not None for name in names)


def _outlook_real_provider_requested(runtime: AppRuntimeConfig) -> bool:
    if runtime.staging_allowed_email_recipients or runtime.staging_allowed_email_domains:
        return True
    return _any_env_values(
        MICROSOFT_TENANT_ID_ENV,
        MICROSOFT_CLIENT_ID_ENV,
        MICROSOFT_CLIENT_SECRET_ENV,
        OUTLOOK_SENDER_MAILBOX_ENV,
    )


def _asana_real_provider_requested(runtime: AppRuntimeConfig) -> bool:
    if runtime.staging_allowed_asana_project_gids:
        return True
    return _any_env_values(
        ASANA_ACCESS_TOKEN_ENV,
        ASANA_WORKSPACE_GID_ENV,
        ASANA_DEFAULT_PROJECT_GID_ENV,
    )


def _validate_staging_outlook_configuration(runtime: AppRuntimeConfig) -> None:
    if not runtime.staging_allowed_email_recipients and not runtime.staging_allowed_email_domains:
        raise RuntimeConfigurationError(
            "Staging real Outlook execution requires STAGING_ALLOWED_EMAIL_RECIPIENTS "
            "or STAGING_ALLOWED_EMAIL_DOMAINS."
        )
    _require_env_values(
        MICROSOFT_TENANT_ID_ENV,
        MICROSOFT_CLIENT_ID_ENV,
        MICROSOFT_CLIENT_SECRET_ENV,
        OUTLOOK_SENDER_MAILBOX_ENV,
    )


def _validate_staging_asana_configuration(runtime: AppRuntimeConfig) -> None:
    if not runtime.staging_allowed_asana_project_gids:
        raise RuntimeConfigurationError(
            "Staging real Asana execution requires STAGING_ALLOWED_ASANA_PROJECT_GIDS."
        )
    _require_env_values(
        ASANA_ACCESS_TOKEN_ENV,
        ASANA_WORKSPACE_GID_ENV,
        ASANA_DEFAULT_PROJECT_GID_ENV,
    )


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed or None


def _parse_generic_allowlist(raw_value: str | None) -> tuple[str, ...]:
    normalized_values: list[str] = []
    seen: set[str] = set()
    for item in _split_allowlist(raw_value):
        if item in seen:
            continue
        seen.add(item)
        normalized_values.append(item)
    return tuple(normalized_values)


def _parse_recipient_allowlist(raw_value: str | None) -> tuple[str, ...]:
    normalized_values: list[str] = []
    seen: set[str] = set()
    for item in _split_allowlist(raw_value):
        lowered = item.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        normalized_values.append(lowered)
    return tuple(normalized_values)


def _parse_domain_allowlist(raw_value: str | None) -> tuple[str, ...]:
    normalized_values: list[str] = []
    seen: set[str] = set()
    for item in _split_allowlist(raw_value):
        lowered = item.lower().lstrip("@")
        if not lowered:
            continue
        if lowered in seen:
            continue
        seen.add(lowered)
        normalized_values.append(lowered)
    return tuple(normalized_values)


def _split_allowlist(raw_value: str | None) -> tuple[str, ...]:
    normalized = _normalize_optional_text(raw_value)
    if normalized is None:
        return ()
    items = []
    for candidate in normalized.replace(";", ",").replace("\n", ",").split(","):
        trimmed = candidate.strip()
        if trimmed:
            items.append(trimmed)
    return tuple(items)
