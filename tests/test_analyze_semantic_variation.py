import argparse
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


def load_censo_analysis_module():
    module_path = (
        Path(__file__).resolve().parents[1]
        / "data"
        / "censo_escolar_dataset"
        / "analyze_semantic_variation.py"
    )
    spec = importlib.util.spec_from_file_location(
        "censo_semantic_variation_script", module_path
    )
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

    def test_load_rows_normalizes_censo_query_dataset_shape(self):
        module = load_analysis_module()

        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = Path(tmp_dir) / "censo.json"
            input_path.write_text(
                json.dumps(
                    {
                        "queries": [
                            {
                                "id": 7,
                                "pergunta_nl": "Quantas escolas existem?",
                                "sql": "SELECT COUNT(*) FROM escola",
                                "changed_question": "Quantas escolas rurais existem?",
                                "changed_sql": (
                                    "SELECT COUNT(*) FROM escola "
                                    "WHERE tipo_localizacao = 'Rural'"
                                ),
                                "complexidade": {"nivel": "Fácil"},
                            }
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            rows = module.load_rows(input_path)

        self.assertEqual(
            rows,
            [
                {
                    "id": 7,
                    "original_question": "Quantas escolas existem?",
                    "original_sql": "SELECT COUNT(*) FROM escola",
                    "changed_question": "Quantas escolas rurais existem?",
                    "changed_sql": (
                        "SELECT COUNT(*) FROM escola WHERE tipo_localizacao = 'Rural'"
                    ),
                    "level": "Fácil",
                }
            ],
        )

    def test_load_rows_requires_augmented_fields_for_censo_query_dataset(self):
        module = load_analysis_module()

        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = Path(tmp_dir) / "censo.json"
            input_path.write_text(
                json.dumps(
                    {
                        "queries": [
                            {
                                "pergunta_nl": "Quantas escolas existem?",
                                "sql": "SELECT COUNT(*) FROM escola",
                                "complexidade": {"nivel": "Fácil"},
                            }
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                ValueError,
                "Row 0 is missing augmented censo field: changed_question",
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

    def test_resolves_qwen_and_accepts_jirai_as_a_jina_alias(self):
        module = load_analysis_module()

        qwen = module.resolve_model_config("qwen")
        jina = module.resolve_model_config("jirai")

        self.assertEqual(qwen.model_id, "Qwen/Qwen3-Embedding-4B")
        self.assertEqual(qwen.embedding_task, "symmetric text similarity")
        self.assertEqual(qwen.model_license, "Apache-2.0")
        self.assertEqual(jina, module.resolve_model_config("jina"))
        self.assertEqual(jina.model_id, "jinaai/jina-embeddings-v3")

    def test_model_parser_rejects_unknown_model_with_actionable_choices(self):
        module = load_analysis_module()

        with self.assertRaisesRegex(
            argparse.ArgumentTypeError, "Choose one of: jina, qwen"
        ):
            module.parse_model_choice("unknown")

    def test_model_argument_normalizes_jirai_alias(self):
        module = load_analysis_module()
        parser = argparse.ArgumentParser()
        module.add_model_argument(parser)

        args = parser.parse_args(["--model", "jirai"])

        self.assertEqual(args.model, "jina")

    def test_qwen_encoding_does_not_receive_the_jina_task_argument(self):
        module = load_analysis_module()
        embedder = FakeEmbedder(self.embeddings)

        module.score_rows(self.rows, embedder, batch_size=2, model="qwen")

        self.assertEqual(len(embedder.calls), 4)
        for _, encode_kwargs in embedder.calls:
            self.assertNotIn("task", encode_kwargs)
            self.assertTrue(encode_kwargs["normalize_embeddings"])

    def test_rejects_transformers_5_for_default_jina_model(self):
        module = load_analysis_module()

        with patch.object(module.importlib_metadata, "version", return_value="5.9.0"):
            with self.assertRaisesRegex(
                RuntimeError, "transformers==4.57.6.*Restart the runtime"
            ):
                module.validate_embedding_runtime(module.DEFAULT_MODEL_ID)

    def test_rejects_transformers_older_than_qwen_minimum(self):
        module = load_analysis_module()

        with patch.object(module.importlib_metadata, "version", return_value="4.50.3"):
            with self.assertRaisesRegex(RuntimeError, "transformers>=4.51.0"):
                module.validate_embedding_runtime("qwen")

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

    def test_run_analysis_uses_custom_dataset_label_in_report(self):
        module = load_analysis_module()

        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = Path(tmp_dir) / "input.json"
            scores_path = Path(tmp_dir) / "scores.json"
            report_path = Path(tmp_dir) / "report.md"
            input_path.write_text(
                json.dumps(self.rows, ensure_ascii=False), encoding="utf-8"
            )

            module.run_analysis(
                input_path=input_path,
                scores_output_path=scores_path,
                report_output_path=report_path,
                model_id="jinaai/jina-embeddings-v3",
                batch_size=2,
                embedder=FakeEmbedder(self.embeddings),
                generated_at="2026-05-27T12:00:00+00:00",
                dataset_label="Censo Escolar Dataset",
            )

            report = report_path.read_text(encoding="utf-8")

        self.assertIn("# Censo Escolar Dataset Semantic Variation Report", report)

    def test_run_analysis_records_qwen_model_metadata(self):
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
                model_id="qwen",
                batch_size=2,
                embedder=FakeEmbedder(self.embeddings),
                generated_at="2026-08-22T12:00:00+00:00",
            )
            report = report_path.read_text(encoding="utf-8")

        self.assertEqual(
            payload["metadata"]["model_id"], "Qwen/Qwen3-Embedding-4B"
        )
        self.assertEqual(
            payload["metadata"]["embedding_task"], "symmetric text similarity"
        )
        self.assertEqual(payload["metadata"]["model_license"], "Apache-2.0")
        self.assertIn("Qwen/Qwen3-Embedding-4B", report)
        self.assertNotIn("non-commercial use", report)

    def test_censo_wrapper_defaults_to_xlsx_report(self):
        module = load_censo_analysis_module()

        self.assertEqual(module.REPORT_OUTPUT_PATH.suffix, ".xlsx")


if __name__ == "__main__":
    unittest.main()
