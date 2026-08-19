from __future__ import annotations

import unittest
from unittest.mock import patch

from tools.runtime_environment import (
    APP_ENV_ENV,
    AppEnvironment,
    AppRuntimeConfig,
    RuntimeConfigurationError,
    validate_bootstrap_environment,
    validate_test_console_startup,
)


class RuntimeEnvironmentTests(unittest.TestCase):
    def test_from_env_defaults_to_implicit_local_when_app_env_is_absent(self) -> None:
        with patch("tools.runtime_environment.load_env_value", return_value=None):
            runtime = AppRuntimeConfig.from_env()

        self.assertEqual(runtime.app_env, AppEnvironment.LOCAL)
        self.assertFalse(runtime.app_env_explicit)
        self.assertTrue(runtime.allows_docker_db_fallback())
        self.assertTrue(runtime.allows_mutable_test_clock())

    def test_invalid_app_env_is_rejected(self) -> None:
        with patch("tools.runtime_environment.load_env_value", side_effect=lambda name: "qa" if name == APP_ENV_ENV else None):
            with self.assertRaises(RuntimeConfigurationError):
                AppRuntimeConfig.from_env()

    def test_non_local_bind_requires_explicit_app_env(self) -> None:
        with self.assertRaises(RuntimeConfigurationError):
            validate_test_console_startup(
                runtime=AppRuntimeConfig.local_default(),
                host="0.0.0.0",
                allow_non_local_bind=True,
                allow_real_providers=False,
            )

        validate_test_console_startup(
            runtime=AppRuntimeConfig(app_env=AppEnvironment.LOCAL, app_env_explicit=True),
            host="0.0.0.0",
            allow_non_local_bind=True,
            allow_real_providers=False,
        )

    def test_staging_requires_database_and_basic_auth(self) -> None:
        with self.assertRaises(RuntimeConfigurationError):
            validate_test_console_startup(
                runtime=AppRuntimeConfig(
                    app_env=AppEnvironment.STAGING,
                    app_env_explicit=True,
                ),
                host="0.0.0.0",
                allow_non_local_bind=False,
                allow_real_providers=False,
            )

        validate_test_console_startup(
            runtime=AppRuntimeConfig(
                app_env=AppEnvironment.STAGING,
                app_env_explicit=True,
                database_url="postgresql://staging-db",
                staging_basic_auth_username="stage-user",
                staging_basic_auth_password="stage-pass",
            ),
            host="0.0.0.0",
            allow_non_local_bind=False,
            allow_real_providers=False,
        )

    def test_staging_real_providers_require_allowlists_and_credentials(self) -> None:
        runtime = AppRuntimeConfig(
            app_env=AppEnvironment.STAGING,
            app_env_explicit=True,
            database_url="postgresql://staging-db",
            staging_basic_auth_username="stage-user",
            staging_basic_auth_password="stage-pass",
        )
        with self.assertRaises(RuntimeConfigurationError):
            validate_test_console_startup(
                runtime=runtime,
                host="0.0.0.0",
                allow_non_local_bind=False,
                allow_real_providers=True,
            )

    def test_email_and_asana_allowlists_are_environment_scoped(self) -> None:
        runtime = AppRuntimeConfig(
            app_env=AppEnvironment.STAGING,
            app_env_explicit=True,
            database_url="postgresql://staging-db",
            staging_basic_auth_username="stage-user",
            staging_basic_auth_password="stage-pass",
            staging_allowed_email_recipients=("approved@example.com",),
            staging_allowed_email_domains=("allowed.test",),
            staging_allowed_asana_project_gids=("project-123",),
        )

        self.assertTrue(runtime.is_email_recipient_allowed("approved@example.com"))
        self.assertTrue(runtime.is_email_recipient_allowed("another@allowed.test"))
        self.assertFalse(runtime.is_email_recipient_allowed("other@example.com"))
        self.assertTrue(runtime.is_asana_project_allowed("project-123"))
        self.assertFalse(runtime.is_asana_project_allowed("project-999"))

    def test_bootstrap_environment_refuses_production_and_requires_staging_database(self) -> None:
        with self.assertRaises(RuntimeConfigurationError):
            validate_bootstrap_environment(
                operation_name="Phase 5 embedding generation",
                runtime=AppRuntimeConfig(
                    app_env=AppEnvironment.PRODUCTION,
                    app_env_explicit=True,
                ),
            )

        with self.assertRaises(RuntimeConfigurationError):
            validate_bootstrap_environment(
                operation_name="Phase 5 embedding generation",
                runtime=AppRuntimeConfig(
                    app_env=AppEnvironment.STAGING,
                    app_env_explicit=True,
                ),
            )

        resolved = validate_bootstrap_environment(
            operation_name="Phase 5 embedding generation",
            runtime=AppRuntimeConfig(
                app_env=AppEnvironment.STAGING,
                app_env_explicit=True,
                database_url="postgresql://staging-db",
            ),
        )

        self.assertEqual(resolved.app_env, AppEnvironment.STAGING)


if __name__ == "__main__":
    unittest.main()
