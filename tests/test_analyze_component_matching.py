import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


def load_analysis_module():
    module_path = (
        Path(__file__).resolve().parents[1]
        / "data"
        / "geo_dataset"
        / "analyze_component_matching.py"
    )
    spec = importlib.util.spec_from_file_location("component_matching_script", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AnalyzeComponentMatchingTest(unittest.TestCase):
    def setUp(self):
        self.rows = [
            {
                "original_question": "Pergunta igual",
                "original_sql": "SELECT AVG(salary) FROM employee WHERE city = 'SP'",
                "changed_question": "Pergunta igual",
                "changed_sql": "select avg(salary) from employee where city = 'SP'",
                "level": "Facil",
            },
            {
                "original_question": "Media em SP",
                "original_sql": (
                    "SELECT SUM(salary) FROM employee "
                    "WHERE city = 'SP' AND salary > 1000"
                ),
                "changed_question": "Media no RJ",
                "changed_sql": (
                    "SELECT AVG(salary) FROM employee "
                    "WHERE city = 'RJ' AND salary <= 2500"
                ),
                "level": "Medio",
            },
        ]

    def test_load_rows_rejects_missing_required_field_with_row_context(self):
        module = load_analysis_module()

        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = Path(tmp_dir) / "input.json"
            input_path.write_text(
                json.dumps([{"original_sql": "SELECT 1"}]), encoding="utf-8"
            )

            with self.assertRaisesRegex(
                ValueError, "Row 0 is missing required field: original_question"
            ):
                module.load_rows(input_path)

    def test_identical_sql_ignores_formatting_and_case_only_differences(self):
        module = load_analysis_module()

        result = module.compare_sql_components(
            "SELECT AVG(salary) FROM employee WHERE city = 'SP'",
            "select avg(salary) from employee where city = 'SP'",
        )

        self.assertEqual(result["component_matching_score"], 0.0)
        self.assertEqual(result["changed_component_count"], 0)
        self.assertGreater(result["component_total"], 0)
        self.assertEqual(result["changed_components"], [])

    def test_detects_aggregate_literal_operator_and_threshold_changes(self):
        module = load_analysis_module()

        result = module.compare_sql_components(
            "SELECT SUM(salary) FROM employee WHERE city = 'SP' AND salary > 1000",
            "SELECT AVG(salary) FROM employee WHERE city = 'RJ' AND salary <= 2500",
        )
        changed_keys = {component["key"] for component in result["changed_components"]}

        self.assertIn("aggregation:0:function", changed_keys)
        self.assertIn("where:0:right", changed_keys)
        self.assertIn("where:1:operator", changed_keys)
        self.assertIn("where:1:right", changed_keys)
        self.assertEqual(result["changed_component_count"], 4)
        self.assertGreater(result["component_matching_score"], 0)

    def test_detects_between_like_and_postgis_distance_changes(self):
        module = load_analysis_module()

        result = module.compare_sql_components(
            """
            SELECT e.cd_entidade
            FROM municipio m
            JOIN escola e ON ST_DWithin(m.geometry, e.geometry, 5000)
            WHERE m.area_km2 BETWEEN 300 AND 1500
              AND m.nm_mun ILIKE 'Nova%'
            """,
            """
            SELECT e.cd_entidade
            FROM municipio AS m
            JOIN escola AS e ON ST_DWithin(m.geometry, e.geometry, 3000)
            WHERE m.area_km2 BETWEEN 400 AND 2000
              AND m.nm_mun ILIKE '%Nova'
            """,
        )
        changed_keys = {component["key"] for component in result["changed_components"]}

        self.assertIn("join:0:function:0:arg:2", changed_keys)
        self.assertIn("where:0:low", changed_keys)
        self.assertIn("where:0:high", changed_keys)
        self.assertIn("where:1:right", changed_keys)

    def test_invalid_sql_raises_row_indexed_parse_error(self):
        module = load_analysis_module()

        with self.assertRaisesRegex(ValueError, "Row 0 original_sql could not be parsed"):
            module.score_rows(
                [
                    {
                        "original_question": "Invalida",
                        "original_sql": "SELECT FROM",
                        "changed_question": "Invalida",
                        "changed_sql": "SELECT 1",
                        "level": "Facil",
                    }
                ]
            )

    def test_run_analysis_writes_utf8_scores_and_markdown_report(self):
        module = load_analysis_module()

        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = Path(tmp_dir) / "input.json"
            scores_path = Path(tmp_dir) / "scores.json"
            report_path = Path(tmp_dir) / "report.md"
            input_path.write_text(
                json.dumps(self.rows, ensure_ascii=False), encoding="utf-8"
            )

            payload = module.run_analysis(
                input_path=input_path,
                scores_output_path=scores_path,
                report_output_path=report_path,
                generated_at="2026-06-23T12:00:00+00:00",
            )

            written_payload = json.loads(scores_path.read_text(encoding="utf-8"))
            report = report_path.read_text(encoding="utf-8")

        self.assertEqual(payload, written_payload)
        self.assertEqual(written_payload["metadata"]["row_count"], 2)
        self.assertEqual(written_payload["rows"][0]["level"], "Facil")
        self.assertIn("# Geo Dataset Component Matching Report", report)
        self.assertIn("component_matching_score", report)
        self.assertIn("## Most Frequently Changed Component Families", report)
        self.assertIn("structural-change heuristic", report)
        self.assertEqual(payload["statistics"]["overall"]["count"], 2)
        self.assertEqual(payload["statistics"]["unchanged_sql"], 1)


if __name__ == "__main__":
    unittest.main()
