from __future__ import annotations

import io
import json
import unittest
from urllib.error import HTTPError

from tools.phase_08_workflow.operator_harness import (
    OperatorHarnessClient,
    OperatorHarnessConfig,
    OperatorHarnessError,
    _basic_auth_header_value,
    _join_url,
    _parse_question_prompts,
)


class _FakeResponse:
    def __init__(self, body: str) -> None:
        self._body = body.encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def read(self) -> bytes:
        return self._body


class OperatorHarnessTests(unittest.TestCase):
    def test_basic_auth_header_value_builds_token(self) -> None:
        header = _basic_auth_header_value("stage-user", "stage-pass")

        self.assertTrue(header.startswith("Basic "))

    def test_basic_auth_header_value_requires_both_values(self) -> None:
        with self.assertRaises(OperatorHarnessError):
            _basic_auth_header_value("stage-user", None)

    def test_join_url_normalizes_slashes(self) -> None:
        self.assertEqual(_join_url("https://example.test/", "/api/operator/cases"), "https://example.test/api/operator/cases")

    def test_parse_question_prompts_accepts_repeated_pairs(self) -> None:
        prompts = _parse_question_prompts(["11=How many guests?", "12=Which room?"])

        self.assertEqual(prompts, {11: "How many guests?", 12: "Which room?"})

    def test_request_sends_json_and_basic_auth(self) -> None:
        captured: dict[str, object] = {}

        def opener(request, timeout, context):
            captured["url"] = request.full_url
            captured["method"] = request.get_method()
            captured["authorization"] = request.get_header("Authorization")
            captured["content_type"] = request.get_header("Content-type")
            captured["timeout"] = timeout
            captured["context"] = context
            captured["body"] = request.data.decode("utf-8") if request.data else None
            return _FakeResponse(json.dumps({"ok": True}))

        client = OperatorHarnessClient(
            OperatorHarnessConfig(
                base_url="https://stage.example.test",
                username="stage-user",
                password="stage-pass",
                timeout_seconds=12.5,
            ),
            opener=opener,
        )

        payload = client.request("POST", "/api/operator/cases/1/inquiry-waiting", {})

        self.assertEqual(payload, {"ok": True})
        self.assertEqual(captured["url"], "https://stage.example.test/api/operator/cases/1/inquiry-waiting")
        self.assertEqual(captured["method"], "POST")
        self.assertEqual(captured["timeout"], 12.5)
        self.assertEqual(captured["content_type"], "application/json; charset=utf-8")
        self.assertTrue(str(captured["authorization"]).startswith("Basic "))
        self.assertEqual(captured["body"], "{}")

    def test_request_raises_structured_http_error(self) -> None:
        def opener(request, timeout, context):
            del request, timeout, context
            raise HTTPError(
                url="https://stage.example.test/api/operator/cases",
                code=401,
                msg="Unauthorized",
                hdrs=None,
                fp=io.BytesIO(
                    json.dumps(
                        {
                            "ok": False,
                            "error": {
                                "failure_code": "AUTHENTICATION_REQUIRED",
                                "message": "Authentication required.",
                            },
                        }
                    ).encode("utf-8")
                ),
            )

        client = OperatorHarnessClient(
            OperatorHarnessConfig(
                base_url="https://stage.example.test",
                username="stage-user",
                password="stage-pass",
            ),
            opener=opener,
        )

        with self.assertRaisesRegex(OperatorHarnessError, "AUTHENTICATION_REQUIRED"):
            client.list_cases()

    def test_request_raises_clean_timeout_error(self) -> None:
        def opener(request, timeout, context):
            del request, timeout, context
            raise TimeoutError("timed out")

        client = OperatorHarnessClient(
            OperatorHarnessConfig(
                base_url="https://stage.example.test",
                username="stage-user",
                password="stage-pass",
                timeout_seconds=5.0,
            ),
            opener=opener,
        )

        with self.assertRaisesRegex(OperatorHarnessError, "timed out after 5 seconds"):
            client.list_cases()

    def test_create_task_surface_action_posts_expected_payload(self) -> None:
        captured: dict[str, object] = {}

        def opener(request, timeout, context):
            captured["url"] = request.full_url
            captured["method"] = request.get_method()
            captured["body"] = request.data.decode("utf-8") if request.data else None
            captured["timeout"] = timeout
            captured["context"] = context
            return _FakeResponse(json.dumps({"ok": True}))

        client = OperatorHarnessClient(
            OperatorHarnessConfig(
                base_url="https://stage.example.test",
                username="stage-user",
                password="stage-pass",
            ),
            opener=opener,
        )

        payload = client.create_task_surface_action(
            rental_case_id=6,
            summary="[STAGING TEST] WNC Rental Brain Asana Adapter Validation",
            reason="Synthetic staging validation only.",
            task_kind="asana_staging_validation",
            project_gid_override="project-123",
            context_lines=["Synthetic only."],
            external_test_reference="s6-asana-001",
        )

        self.assertEqual(payload, {"ok": True})
        self.assertEqual(captured["url"], "https://stage.example.test/api/operator/cases/6/task-surface-actions")
        self.assertEqual(captured["method"], "POST")
        self.assertIn('"project_gid_override": "project-123"', str(captured["body"]))


if __name__ == "__main__":
    unittest.main()
