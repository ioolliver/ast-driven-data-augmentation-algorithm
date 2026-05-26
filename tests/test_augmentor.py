import unittest
from unittest.mock import patch

from sqlglot import exp

from augmentor import create_random_variation


class CreateRandomVariationTest(unittest.TestCase):
    def test_returns_original_query_without_calling_llm_when_no_mutation_applies(self):
        query = "Mostre o valor constante"

        with patch("augmentor.adapt_query") as adapt_query:
            query_modified, sql_modified = create_random_variation(
                {"tables": []},
                query,
                "SELECT 1",
            )

        self.assertEqual(query_modified, query)
        self.assertEqual(sql_modified, "SELECT\n  1")
        adapt_query.assert_not_called()

    def test_calls_llm_when_a_mutation_is_recorded(self):
        with patch("augmentor.adapt_query", return_value="Pergunta adaptada") as adapt_query:
            query_modified, sql_modified = create_random_variation(
                {"tables": []},
                "Calcule a soma",
                "SELECT SUM(1)",
            )

        self.assertEqual(query_modified, "Pergunta adaptada")
        self.assertNotEqual(sql_modified, "SELECT\n  SUM(1)")
        self.assertTrue(adapt_query.call_args.args[3])

    def test_mutates_numeric_predicate_for_aliased_primary_from_table(self):
        schema = {
            "tables": [
                {
                    "name": "municipio",
                    "columns": [
                        {"name": "area_km2", "type": "number", "min": 0, "max": 160000}
                    ],
                }
            ]
        }

        with (
            patch("augmentor.adapt_query", return_value="Pergunta adaptada") as adapt_query,
            patch("mutations.threshold_shift.random.choice", return_value=exp.LTE),
            patch("mutations.threshold_shift.random.randint", return_value=500),
        ):
            query_modified, sql_modified = create_random_variation(
                schema,
                "Municipios com area maior que 2.000 km2",
                "SELECT m.area_km2 FROM municipio m WHERE m.area_km2 > 2000",
            )

        self.assertEqual(query_modified, "Pergunta adaptada")
        self.assertIn("m.area_km2 <= 500", sql_modified)
        self.assertEqual(
            adapt_query.call_args.args[3],
            [{"old_line": "m.area_km2 > 2000", "new_line": "m.area_km2 <= 500"}],
        )


if __name__ == "__main__":
    unittest.main()
