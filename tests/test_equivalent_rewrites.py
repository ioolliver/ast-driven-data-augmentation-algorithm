import sqlite3
import unittest

import sqlglot
from sqlglot import exp

from mutations.between_comparisons import rewrite_between_as_comparisons
from mutations.distinct_group_by import rewrite_distinct_as_group_by


def apply_equivalent_rewrites(sql):
    tree = sqlglot.parse_one(sql, read="postgres")

    def rewrite(node):
        node = rewrite_distinct_as_group_by(node)
        node = rewrite_between_as_comparisons(node)
        return node

    return tree.transform(rewrite)


class DistinctAsGroupByTest(unittest.TestCase):
    def test_rewrites_plain_and_aliased_columns_while_preserving_other_clauses(self):
        tree = apply_equivalent_rewrites(
            """
            SELECT DISTINCT school.state, school.city AS municipality
            FROM school
            WHERE school.active = 1
            ORDER BY school.state
            LIMIT 5
            """
        )

        select = tree.find(exp.Select)
        self.assertIsNone(select.args.get("distinct"))
        self.assertEqual(
            [expression.sql() for expression in select.args["group"].expressions],
            ["school.state", "school.city"],
        )
        self.assertEqual(select.expressions[1].alias, "municipality")
        self.assertIsNotNone(select.args.get("where"))
        self.assertIsNotNone(select.args.get("order"))
        self.assertEqual(select.args["limit"].expression.this, "5")

    def test_skips_non_simple_distinct_queries(self):
        queries = (
            "SELECT DISTINCT ON (a) a, b FROM t ORDER BY a",
            "SELECT DISTINCT * FROM t",
            "SELECT DISTINCT LOWER(a) FROM t",
            "SELECT DISTINCT COUNT(a) FROM t",
            "SELECT DISTINCT a FROM t GROUP BY a",
            "SELECT DISTINCT a FROM t HAVING COUNT(*) > 1",
        )

        for sql in queries:
            with self.subTest(sql=sql):
                original = sqlglot.parse_one(sql, read="postgres")
                rewritten = original.transform(rewrite_distinct_as_group_by)
                self.assertEqual(rewritten.sql(), original.sql())


class BetweenAsComparisonsTest(unittest.TestCase):
    def test_rewrites_numeric_and_string_literal_bounds(self):
        tree = apply_equivalent_rewrites(
            """
            SELECT t.score
            FROM t
            WHERE t.score BETWEEN 10 AND 20
              AND t.created_at BETWEEN '2025-01-01' AND '2025-12-31'
            """
        )

        self.assertIsNone(tree.find(exp.Between))
        where_sql = tree.args["where"].sql()
        self.assertIn("t.score >= 10 AND t.score <= 20", where_sql)
        self.assertIn(
            "t.created_at >= '2025-01-01' AND t.created_at <= '2025-12-31'",
            where_sql,
        )

    def test_preserves_not_around_rewritten_between(self):
        tree = apply_equivalent_rewrites(
            "SELECT t.score FROM t WHERE t.score NOT BETWEEN 10 AND 20"
        )

        self.assertIsNone(tree.find(exp.Between))
        self.assertIn(
            "NOT (t.score >= 10 AND t.score <= 20)",
            tree.args["where"].sql(),
        )

    def test_skips_non_simple_between_predicates(self):
        queries = (
            "SELECT score FROM t WHERE score + 1 BETWEEN 10 AND 20",
            "SELECT score FROM t WHERE score BETWEEN minimum_score AND maximum_score",
        )

        for sql in queries:
            with self.subTest(sql=sql):
                original = sqlglot.parse_one(sql, read="postgres")
                rewritten = original.transform(rewrite_between_as_comparisons)
                self.assertEqual(rewritten.sql(), original.sql())


class EquivalentRewriteExecutionTest(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.execute(
            """
            CREATE TABLE records (
                row_id INTEGER,
                region TEXT,
                city TEXT,
                score INTEGER
            )
            """
        )
        self.connection.executemany(
            "INSERT INTO records VALUES (?, ?, ?, ?)",
            (
                (1, "SE", "São Paulo", 10),
                (2, "SE", "São Paulo", 20),
                (3, "SE", "Rio de Janeiro", 15),
                (4, None, None, None),
                (5, None, None, 9),
                (6, "S", "Curitiba", 21),
            ),
        )

    def tearDown(self):
        self.connection.close()

    def assert_queries_return_same_rows(self, original_sql):
        rewritten_sql = apply_equivalent_rewrites(original_sql).sql(
            dialect="postgres"
        )
        original_rows = self.connection.execute(original_sql).fetchall()
        rewritten_rows = self.connection.execute(rewritten_sql).fetchall()
        self.assertCountEqual(rewritten_rows, original_rows)

    def test_distinct_and_group_by_are_equivalent_for_duplicates_and_nulls(self):
        self.assert_queries_return_same_rows(
            "SELECT DISTINCT region, city FROM records"
        )

    def test_between_and_comparisons_are_equivalent_for_bounds_and_nulls(self):
        self.assert_queries_return_same_rows(
            "SELECT row_id FROM records WHERE score BETWEEN 10 AND 20"
        )


if __name__ == "__main__":
    unittest.main()
