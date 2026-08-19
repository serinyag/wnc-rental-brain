from __future__ import annotations

import importlib
import os
import sys
import unittest
from unittest.mock import patch

from tools.phase_08_workflow.test_console_service import TestConsoleError


class WsgiEntrypointTests(unittest.TestCase):
    def test_import_exposes_wsgi_application_without_starting_server(self) -> None:
        with patch("tools.phase_08_workflow.test_console.make_server") as make_server:
            sys.modules.pop("tools.phase_08_workflow.wsgi", None)
            module = importlib.import_module("tools.phase_08_workflow.wsgi")

        self.assertTrue(callable(module.application))
        make_server.assert_not_called()

    def test_staging_import_requires_basic_auth_configuration(self) -> None:
        with (
            patch.dict(
                os.environ,
                {
                    "APP_ENV": "staging",
                    "DATABASE_URL": "postgresql://postgres:postgres@127.0.0.1:54322/postgres",
                },
                clear=True,
            ),
            patch("tools.runtime_environment.load_env_value", side_effect=lambda name: os.environ.get(name)),
            patch("tools.phase_08_workflow.test_console.make_server") as make_server,
        ):
            sys.modules.pop("tools.phase_08_workflow.wsgi", None)
            with self.assertRaises(TestConsoleError):
                importlib.import_module("tools.phase_08_workflow.wsgi")

        make_server.assert_not_called()


if __name__ == "__main__":
    unittest.main()
