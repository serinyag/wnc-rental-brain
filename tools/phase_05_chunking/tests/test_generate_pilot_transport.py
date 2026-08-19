from __future__ import annotations

import os
import subprocess
import unittest
from unittest.mock import patch

from tools.phase_05_chunking import generate_pilot
from tools.runtime_environment import AppEnvironment, AppRuntimeConfig, RuntimeConfigurationError


LOCAL_SUPABASE_DATABASE_URL = os.environ.get(
    "LOCAL_SUPABASE_DATABASE_URL",
    "postgresql://postgres:postgres@127.0.0.1:54322/postgres",
)
SCRATCH_TABLE = "public._portability_query_transport"


class SupabaseQueryTransportSelectionTests(unittest.TestCase):
    def test_database_url_absent_uses_legacy_docker_transport(self) -> None:
        with (
            patch("tools.phase_05_chunking.generate_pilot.load_env_value", return_value=None),
            patch("tools.phase_05_chunking.generate_pilot._run_local_docker_query", return_value={"rows": [{"value": 1}]}) as local_runner,
            patch("tools.phase_05_chunking.generate_pilot._run_direct_postgres_query") as direct_runner,
        ):
            result = generate_pilot.run_supabase_query("select 1 as value;", expect_json=True)

        self.assertEqual(result, {"rows": [{"value": 1}]})
        local_runner.assert_called_once_with("select 1 as value;", expect_json=True, timeout_seconds=None)
        direct_runner.assert_not_called()

    def test_database_url_present_uses_direct_transport(self) -> None:
        with (
            patch("tools.phase_05_chunking.generate_pilot.load_env_value", return_value=LOCAL_SUPABASE_DATABASE_URL),
            patch("tools.phase_05_chunking.generate_pilot._run_direct_postgres_query", return_value={"rows": [{"value": 1}]}) as direct_runner,
            patch("tools.phase_05_chunking.generate_pilot._run_local_docker_query") as local_runner,
        ):
            result = generate_pilot.run_supabase_query("select 1 as value;", expect_json=True)

        self.assertEqual(result, {"rows": [{"value": 1}]})
        direct_runner.assert_called_once_with(
            "select 1 as value;",
            expect_json=True,
            database_url=LOCAL_SUPABASE_DATABASE_URL,
            timeout_seconds=None,
        )
        local_runner.assert_not_called()

    def test_database_url_absent_in_staging_rejects_docker_fallback(self) -> None:
        with (
            patch("tools.phase_05_chunking.generate_pilot.load_env_value", return_value=None),
            patch(
                "tools.phase_05_chunking.generate_pilot.AppRuntimeConfig.from_env",
                return_value=AppRuntimeConfig(
                    app_env=AppEnvironment.STAGING,
                    app_env_explicit=True,
                ),
            ),
            patch("tools.phase_05_chunking.generate_pilot._run_local_docker_query") as local_runner,
        ):
            with self.assertRaises(RuntimeConfigurationError):
                generate_pilot.run_supabase_query("select 1 as value;", expect_json=True)

        local_runner.assert_not_called()

    def test_direct_transport_failure_does_not_fall_back_to_docker(self) -> None:
        direct_error = subprocess.CalledProcessError(
            returncode=1,
            cmd=["direct_postgres", "execute"],
            stderr="invalid DATABASE_URL configuration",
        )
        with (
            patch("tools.phase_05_chunking.generate_pilot.load_env_value", return_value=LOCAL_SUPABASE_DATABASE_URL),
            patch("tools.phase_05_chunking.generate_pilot._run_direct_postgres_query", side_effect=direct_error) as direct_runner,
            patch("tools.phase_05_chunking.generate_pilot._run_local_docker_query") as local_runner,
        ):
            with self.assertRaises(subprocess.CalledProcessError) as caught:
                generate_pilot.run_supabase_query("select 1 as value;", expect_json=True)

        self.assertIs(caught.exception, direct_error)
        direct_runner.assert_called_once()
        local_runner.assert_not_called()


class SupabaseQueryTransportParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            import psycopg
        except ModuleNotFoundError as exc:  # pragma: no cover - exercised in validation env
            raise unittest.SkipTest("psycopg is not installed") from exc

        cls.psycopg = psycopg
        try:
            cls.admin_connection = psycopg.connect(LOCAL_SUPABASE_DATABASE_URL, autocommit=True)
        except Exception as exc:  # pragma: no cover - environment-dependent
            raise unittest.SkipTest(f"local Supabase DATABASE_URL is unavailable: {exc}") from exc

        try:
            generate_pilot.find_local_db_container.cache_clear()
            generate_pilot.find_local_db_container()
        except Exception as exc:  # pragma: no cover - environment-dependent
            raise unittest.SkipTest(f"local Docker-backed Supabase transport is unavailable: {exc}") from exc

        cls._reset_schema()

    @classmethod
    def tearDownClass(cls) -> None:
        if not hasattr(cls, "admin_connection"):
            return
        with cls.admin_connection.cursor() as cursor:
            cursor.execute(f"drop table if exists {SCRATCH_TABLE};")
        cls.admin_connection.close()

    @classmethod
    def _reset_schema(cls) -> None:
        with cls.admin_connection.cursor() as cursor:
            cursor.execute(
                f"""
drop table if exists {SCRATCH_TABLE};
create table {SCRATCH_TABLE} (
  id bigserial primary key,
  label text,
  payload jsonb,
  flag boolean,
  created_at timestamptz default timezone('utc', now())
);
"""
            )

    def setUp(self) -> None:
        self._prepare_state()

    def _prepare_state(self, rows: tuple[tuple[str | None, str | None, bool | None], ...] = ()) -> None:
        with self.admin_connection.cursor() as cursor:
            cursor.execute(f"truncate table {SCRATCH_TABLE} restart identity;")
            for label, payload_literal, flag in rows:
                payload_sql = "null" if payload_literal is None else f"{generate_pilot.sql_text(payload_literal)}::jsonb"
                flag_sql = "null" if flag is None else ("true" if flag else "false")
                cursor.execute(
                    f"""
insert into {SCRATCH_TABLE} (label, payload, flag)
values (
  {generate_pilot.sql_text(label)},
  {payload_sql},
  {flag_sql}
);
""".strip()
                )

    def _run_mode(
        self,
        mode: str,
        sql: str,
        *,
        expect_json: bool = True,
        timeout_seconds: float | None = None,
    ):
        database_url = LOCAL_SUPABASE_DATABASE_URL if mode == "direct" else None
        with patch("tools.phase_05_chunking.generate_pilot.load_env_value", return_value=database_url):
            return generate_pilot.run_supabase_query(sql, expect_json=expect_json, timeout_seconds=timeout_seconds)

    def _assert_mode_parity(
        self,
        sql: str,
        *,
        expect_json: bool = True,
        seed_rows: tuple[tuple[str | None, str | None, bool | None], ...] = (),
    ) -> None:
        self._prepare_state(seed_rows)
        direct = self._run_mode("direct", sql, expect_json=expect_json)
        self._prepare_state(seed_rows)
        docker = self._run_mode("docker", sql, expect_json=expect_json)
        self.assertEqual(direct, docker)

    def test_direct_mode_uses_zero_docker_subprocess_calls(self) -> None:
        with (
            patch("tools.phase_05_chunking.generate_pilot.load_env_value", return_value=LOCAL_SUPABASE_DATABASE_URL),
            patch("tools.phase_05_chunking.generate_pilot.subprocess.run", side_effect=AssertionError("subprocess should not be used in direct mode")),
        ):
            result = generate_pilot.run_supabase_query("select 1 as value;", expect_json=True)

        self.assertEqual(result, {"rows": [{"value": 1}]})

    def test_select_shape_normalization_matches_between_transports(self) -> None:
        self._assert_mode_parity(
            """
select
  null::text as optional_text,
  true as active_flag,
  7::integer as quantity,
  '2026-08-15T10:00:00Z'::timestamptz as happened_at,
  jsonb_build_object('alpha', 1, 'beta', jsonb_build_array('x', 'y')) as payload,
  array['left', 'right']::text[] as tags
""".strip()
        )

    def test_multi_row_select_matches_between_transports(self) -> None:
        seed_rows = (
            ("first", '{"kind":"alpha"}', True),
            ("second", '{"kind":"beta"}', False),
        )
        self._assert_mode_parity(
            f"""
select
  label,
  payload,
  flag
from {SCRATCH_TABLE}
order by id;
""".strip(),
            seed_rows=seed_rows,
        )

    def test_zero_row_select_matches_between_transports(self) -> None:
        self._assert_mode_parity(
            f"select label from {SCRATCH_TABLE} where label = 'missing';",
        )

    def test_insert_returning_matches_between_transports(self) -> None:
        self._assert_mode_parity(
            f"""
insert into {SCRATCH_TABLE} (label, payload, flag)
values ('inserted', '{{"mode":"insert"}}'::jsonb, true)
returning label, payload, flag;
""".strip()
        )

    def test_update_returning_matches_between_transports(self) -> None:
        seed_rows = (("update-me", '{"mode":"before"}', False),)
        self._assert_mode_parity(
            f"""
update {SCRATCH_TABLE}
set payload = '{{"mode":"after"}}'::jsonb,
    flag = true
where label = 'update-me'
returning label, payload, flag;
""".strip(),
            seed_rows=seed_rows,
        )

    def test_delete_returning_matches_between_transports(self) -> None:
        seed_rows = (("delete-me", '{"mode":"delete"}', True),)
        self._assert_mode_parity(
            f"""
delete from {SCRATCH_TABLE}
where label = 'delete-me'
returning label, payload, flag;
""".strip(),
            seed_rows=seed_rows,
        )

    def test_with_insert_returning_matches_between_transports(self) -> None:
        self._assert_mode_parity(
            f"""
with existing as (
  select count(*)::integer as existing_count
  from {SCRATCH_TABLE}
)
insert into {SCRATCH_TABLE} (label, payload, flag)
select
  concat('with-insert-', existing_count),
  jsonb_build_object('existing_count', existing_count),
  true
from existing
returning label, payload, flag;
""".strip()
        )

    def test_timeout_semantics_match_between_transports(self) -> None:
        sql = "select pg_sleep(1);"

        with self.assertRaises(subprocess.TimeoutExpired):
            self._run_mode("direct", sql, expect_json=True, timeout_seconds=0.1)

        with self.assertRaises(subprocess.TimeoutExpired):
            self._run_mode("docker", sql, expect_json=True, timeout_seconds=0.1)


if __name__ == "__main__":
    unittest.main()
