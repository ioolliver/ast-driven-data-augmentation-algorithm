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

    def test_mutates_equivalent_column_only_once_across_passes(self):
        schema = {
            "tables": [
                {
                    "name": "t",
                    "columns": [
                        {"name": "a", "type": "string", "semantic_group": "group"},
                        {"name": "b", "type": "string", "semantic_group": "group"},
                    ],
                }
            ]
        }

        with patch("augmentor.adapt_query", return_value="Pergunta adaptada") as adapt_query:
            _, sql_modified = create_random_variation(
                schema,
                "Mostre a coluna",
                "SELECT t.a FROM t",
            )

        self.assertIn("t.b", sql_modified)
        self.assertNotIn("t.a", sql_modified)
        self.assertEqual(len(adapt_query.call_args.args[3]), 1)

    def test_mutates_text_pattern_without_schema_metadata(self):
        with patch("augmentor.adapt_query", return_value="Pergunta adaptada") as adapt_query:
            query_modified, sql_modified = create_random_variation(
                {"tables": []},
                "Municipios com nome iniciando por Sao",
                "SELECT m.nm_mun FROM municipio m WHERE m.nm_mun ILIKE 'Sao%'",
            )

        self.assertEqual(query_modified, "Pergunta adaptada")
        self.assertNotIn("ILIKE 'Sao%'", sql_modified)
        self.assertEqual(adapt_query.call_args.args[3][0]["old_line"], "m.nm_mun ILIKE 'Sao%'")

    def test_mutates_case_sensitive_like_pattern(self):
        with (
            patch("augmentor.adapt_query", return_value="Pergunta adaptada"),
            patch("mutations.text_pattern.random.choice", return_value="prefix"),
        ):
            _, sql_modified = create_random_variation(
                {"tables": []},
                "Bibliotecas contendo Municipal",
                "SELECT b.nm_bib FROM biblioteca b WHERE b.nm_bib LIKE '%Municipal%'",
            )

        self.assertIn("b.nm_bib LIKE 'Municipal%'", sql_modified)

    def test_mutates_st_distance_threshold_using_postgis_distance_range(self):
        schema = {
            "tables": [
                {
                    "name": "escola",
                    "columns": [
                        {
                            "name": "geometry",
                            "type": "geometry",
                            "distance_min_m": 100,
                            "distance_max_m": 20000,
                        }
                    ],
                }
            ]
        }

        with (
            patch("augmentor.adapt_query", return_value="Pergunta adaptada") as adapt_query,
            patch("mutations.postgis.random.randint", return_value=12000),
        ):
            query_modified, sql_modified = create_random_variation(
                schema,
                "Escolas a ate 5 km da fronteira",
                (
                    "SELECT e.cd_entidade FROM escola e "
                    "WHERE ST_Distance(e.geometry::geography, e.geometry::geography) <= 5000"
                ),
            )

        self.assertEqual(query_modified, "Pergunta adaptada")
        self.assertIn("ST_DISTANCE", sql_modified)
        self.assertIn("<= 12000", sql_modified)
        self.assertEqual(
            adapt_query.call_args.args[3],
            [
                {
                    "old_line": (
                        "ST_DISTANCE(CAST(e.geometry AS GEOGRAPHY), "
                        "CAST(e.geometry AS GEOGRAPHY)) <= 5000"
                    ),
                    "new_line": (
                        "ST_DISTANCE(CAST(e.geometry AS GEOGRAPHY), "
                        "CAST(e.geometry AS GEOGRAPHY)) <= 12000"
                    ),
                    "tip": "Limite de ST_Distance alterado de 5000 para 12000",
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
