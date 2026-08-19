from __future__ import annotations

import unittest

from tools.phase_05_chunking.generate_pilot import _wrap_supabase_json_query


class SupabaseQueryWrapperTests(unittest.TestCase):
    def test_select_queries_are_wrapped_as_subqueries(self) -> None:
        wrapped = _wrap_supabase_json_query("select 1 as value;")

        self.assertIn("from (\nselect 1 as value\n) as t;", wrapped)
        self.assertNotIn("with __query_result as", wrapped)

    def test_select_with_cte_queries_stay_top_level(self) -> None:
        wrapped = _wrap_supabase_json_query("with sample as (select 1 as value) select value from sample;")

        self.assertTrue(wrapped.startswith("with sample as (select 1 as value),\n__query_result as (\nselect value from sample\n)"))
        self.assertIn("from __query_result;", wrapped)

    def test_insert_returning_queries_stay_top_level(self) -> None:
        wrapped = _wrap_supabase_json_query("insert into demo values (1) returning id;")

        self.assertTrue(wrapped.startswith("with __query_result as (\ninsert into demo values (1) returning id\n)"))
        self.assertIn("from __query_result;", wrapped)

    def test_update_returning_queries_stay_top_level(self) -> None:
        wrapped = _wrap_supabase_json_query("update demo set value = 2 returning id;")

        self.assertTrue(wrapped.startswith("with __query_result as (\nupdate demo set value = 2 returning id\n)"))
        self.assertIn("from __query_result;", wrapped)

    def test_insert_returning_cte_queries_stay_top_level(self) -> None:
        wrapped = _wrap_supabase_json_query(
            "with unset_current as (update demo set active = false returning id) insert into demo(id) values (1) returning id;"
        )

        self.assertTrue(
            wrapped.startswith(
                "with unset_current as (update demo set active = false returning id),\n"
                "__query_result as (\ninsert into demo(id) values (1) returning id\n)"
            )
        )
        self.assertIn("from __query_result;", wrapped)


if __name__ == "__main__":
    unittest.main()
