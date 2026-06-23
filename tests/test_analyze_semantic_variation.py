import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


def load_analysis_module():
    module_path = (
        Path(__file__).resolve().parents[1]
        / "data"
        / "geo_dataset"
        / "analyze_semantic_variation.py"
    )
    spec = importlib.util.spec_from_file_location("semantic_variation_script", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeEmbedder:
    def __init__(self, embeddings):
        self.embeddings = embeddings
        self.calls = []

    def encode(self, texts, **kwargs):
        self.calls.append((texts, kwargs))
        return [self.embeddings[text] for text in texts]


class AnalyzeSemanticVariationTest(unittest.TestCase):
    def setUp(self):
        self.rows = [
            {
                "original_question": "Pergunta igual",
                "original_sql": "SELECT 1",
                "changed_question": "Pergunta igual",
                "changed_sql": "SELECT 1",
                "level": "Facíl",
            },
            {
                "original_question": "Onde está a escola?",
                "original_sql": "SELECT urbano",
                "changed_question": "Onde está a biblioteca?",
                "changed_sql": "SELECT rural",
                "level": "Médio",
            },
        ]
        self.embeddings = {
            "Pergunta igual": [1.0, 0.0],
            "SELECT 1": [1.0, 0.0],
            "Onde está a escola?": [1.0, 0.0],
            "Onde está a biblioteca?": [0.0, 1.0],
            "SELECT urbano": [1.0, 0.0],
            "SELECT rural": [-1.0, 0.0],
        }

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

    def test_score_rows_calculates_bounded_sql_question_and_combined_scores(self):
        module = load_analysis_module()
        embedder = FakeEmbedder(self.embeddings)

        scored_rows = module.score_rows(self.rows, embedder, batch_size=2)

        self.assertEqual(scored_rows[0]["row_index"], 0)
        self.assertAlmostEqual(scored_rows[0]["sql_variation_score"], 0.0)
        self.assertAlmostEqual(scored_rows[0]["question_variation_score"], 0.0)
        self.assertAlmostEqual(scored_rows[0]["combined_variation_score"], 0.0)
        self.assertAlmostEqual(scored_rows[1]["sql_similarity"], -1.0)
        self.assertAlmostEqual(scored_rows[1]["sql_variation_score"], 1.0)
        self.assertAlmostEqual(scored_rows[1]["question_variation_score"], 1.0)
        self.assertAlmostEqual(scored_rows[1]["combined_variation_score"], 1.0)
        self.assertEqual(len(embedder.calls), 4)
        self.assertEqual(embedder.calls[0][1]["task"], "text-matching")
        self.assertTrue(embedder.calls[0][1]["normalize_embeddings"])
        self.assertEqual(embedder.calls[0][1]["batch_size"], 2)

    def test_rejects_transformers_5_for_default_jina_model(self):
        module = load_analysis_module()

        with patch.object(module.importlib_metadata, "version", return_value="5.9.0"):
            with self.assertRaisesRegex(
                RuntimeError, "transformers==4.57.6.*Restart the runtime"
            ):
                module.validate_embedding_runtime(module.DEFAULT_MODEL_ID)

    def test_summarize_scores_includes_percentiles_levels_unchanged_and_bands(self):
        module = load_analysis_module()
        scored_rows = module.score_rows(
            self.rows, FakeEmbedder(self.embeddings), batch_size=2
        )

        summary = module.summarize_scores(scored_rows)

        self.assertEqual(summary["overall"]["combined"]["count"], 2)
        self.assertAlmostEqual(summary["overall"]["combined"]["average"], 0.5)
        self.assertAlmostEqual(summary["overall"]["combined"]["median"], 0.5)
        self.assertAlmostEqual(summary["overall"]["combined"]["p75"], 0.75)
        self.assertEqual(summary["unchanged_text"]["sql"], 1)
        self.assertEqual(summary["unchanged_text"]["question"], 1)
        self.assertIn("Facíl", summary["by_level"])
        self.assertEqual(summary["by_level"]["Médio"]["combined"]["max"], 1.0)
        self.assertEqual(summary["bands"]["combined"]["[0.0, 0.1)"], 1)
        self.assertEqual(summary["bands"]["combined"]["[0.9, 1.0]"], 1)

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
                model_id="jinaai/jina-embeddings-v3",
                batch_size=2,
                embedder=FakeEmbedder(self.embeddings),
                generated_at="2026-05-27T12:00:00+00:00",
            )

            written_payload = json.loads(scores_path.read_text(encoding="utf-8"))
            report = report_path.read_text(encoding="utf-8")

        self.assertEqual(payload, written_payload)
        self.assertEqual(written_payload["metadata"]["row_count"], 2)
        self.assertEqual(written_payload["rows"][0]["level"], "Facíl")
        self.assertIn("# Geo Dataset Semantic Variation Report", report)
        self.assertIn("jinaai/jina-embeddings-v3", report)
        self.assertIn("CC BY-NC 4.0", report)
        self.assertIn("## Overall Statistics", report)
        self.assertIn("## Statistics By Level", report)
        self.assertIn("embedding-based heuristic", report)


if __name__ == "__main__":
    unittest.main()
