import sqlite3
import unittest

import sqlglot

from ast_augmentation.mutations.equivalent_column import mutate_equivalent_column


class SpiderSemanticColumnSafetyTest(unittest.TestCase):
    def setUp(self):
        self.schema = {
            "dialect": "sqlite",
            "sqlite_double_quoted_literals": True,
            "case_insensitive_identifiers": True,
            "tables": [{"name": "people", "columns": [
                {"name": "first_name", "type": "string", "semantic_group": "names"},
                {"name": "last_name", "type": "string", "semantic_group": "names"},
                {"name": "height", "type": "number", "semantic_group": "dimensions"},
                {"name": "width", "type": "number", "semantic_group": "dimensions"},
            ]}],
        }

    def mutate(self, query, schema=None):
        changes = []
        ast = sqlglot.parse_one(query, read="sqlite")
        result = ast.transform(
            lambda node: mutate_equivalent_column(node, changes, schema or self.schema)
        )
        return result.sql(dialect="sqlite"), changes

    def test_nested_and_double_quoted_predicates_keep_original_domains(self):
        predicates = [
            'first_name != "Alice"',
            'first_name < "Z"',
            "LOWER(first_name) = 'alice'",
            "first_name BETWEEN 'A' AND 'Z'",
            "LOWER(first_name) LIKE 'a%'",
            "first_name IN ('Alice', 'Bob')",
            "ABS(height) > 2",
            "height + 1 > width",
            "first_name IS NOT NULL",
        ]
        for predicate in predicates:
            with self.subTest(predicate=predicate):
                query = f"SELECT COUNT(*) FROM people WHERE {predicate}"
                result, changes = self.mutate(query)
                self.assertEqual(result, sqlglot.parse_one(query, read="sqlite").sql(dialect="sqlite"))
                self.assertEqual(changes, [])

    def test_join_predicates_with_wrapped_columns_remain_unchanged(self):
        query = (
            "SELECT COUNT(*) FROM people p JOIN people q "
            "ON LOWER(p.first_name) = LOWER(q.last_name)"
        )
        result, changes = self.mutate(query)
        self.assertEqual(result, sqlglot.parse_one(query, read="sqlite").sql(dialect="sqlite"))
        self.assertEqual(changes, [])

    def test_grouping_key_is_preserved_but_aggregate_argument_can_change(self):
        result, changes = self.mutate(
            "SELECT FIRST_NAME, SUM(height) FROM people "
            "GROUP BY first_name HAVING COUNT(*) > 1 ORDER BY first_name"
        )
        self.assertIn("FIRST_NAME, SUM(width)", result)
        self.assertIn("GROUP BY first_name", result)
        self.assertIn("ORDER BY first_name", result)
        self.assertEqual(len(changes), 1)
        with sqlite3.connect(":memory:") as connection:
            connection.execute("CREATE TABLE people(first_name TEXT, last_name TEXT, height REAL, width REAL)")
            connection.executemany("INSERT INTO people VALUES (?, ?, ?, ?)", [
                ("Alice", "Jones", 1, 3), ("Alice", "Smith", 2, 4),
            ])
            self.assertEqual(connection.execute(result).fetchall(), [("Alice", 7)])

    def test_plain_projection_and_order_by_allow_alternatives(self):
        result, changes = self.mutate("SELECT first_name FROM people ORDER BY first_name")
        self.assertEqual(result, "SELECT last_name FROM people ORDER BY last_name")
        self.assertEqual(len(changes), 2)

    def test_arithmetic_in_projection_preserves_units(self):
        result, changes = self.mutate("SELECT height * 2 FROM people")
        self.assertEqual(result, "SELECT height * 2 FROM people")
        self.assertEqual(changes, [])

    def test_numeric_aggregate_does_not_use_textual_peer(self):
        self.schema["tables"][0]["columns"][3]["type"] = "string"
        result, changes = self.mutate("SELECT SUM(height) FROM people")
        self.assertEqual(result, "SELECT SUM(height) FROM people")
        self.assertEqual(changes, [])
        result, changes = self.mutate("SELECT AVG(first_name) FROM people")
        self.assertEqual(result, "SELECT AVG(first_name) FROM people")
        self.assertEqual(changes, [])

    def test_legacy_non_spider_projection_behavior_is_preserved(self):
        self.schema.pop("sqlite_double_quoted_literals")
        result, changes = self.mutate("SELECT LOWER(first_name) FROM people WHERE height > 2")
        self.assertEqual(result, "SELECT LOWER(last_name) FROM people WHERE width > 2")
        self.assertEqual(len(changes), 2)


if __name__ == "__main__":
    unittest.main()
