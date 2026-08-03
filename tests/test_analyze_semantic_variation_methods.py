import importlib.util
import tempfile
import unittest
from pathlib import Path


def load_methods_analyzer_module():
    module_path = (
        Path(__file__).resolve().parents[1]
        / "data"
        / "censo_escolar_dataset"
        / "analyze_semantic_variation_methods.py"
    )
    spec = importlib.util.spec_from_file_location(
        "analyze_censo_semantic_variation_methods", module_path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeAnalyzer:
    DEFAULT_MODEL_ID = "test-model"
    DEFAULT_BATCH_SIZE = 8

    def __init__(self):
        self.loaded_embedders = []
        self.analysis_calls = []

    def load_embedder(self, model_id, device=None):
        embedder = object()
        self.loaded_embedders.append((model_id, device, embedder))
        return embedder

    def run_analysis(self, **kwargs):
        self.analysis_calls.append(kwargs)
        kwargs["scores_output_path"].write_text("scores", encoding="utf-8")
        kwargs["report_output_path"].write_text("workbook", encoding="utf-8")
        return {"dataset_label": kwargs["dataset_label"]}


class AnalyzeSemanticVariationMethodsTest(unittest.TestCase):
    def test_runs_all_methods_with_one_shared_embedder_and_separate_outputs(self):
        module = load_methods_analyzer_module()
        analyzer = FakeAnalyzer()

        with tempfile.TemporaryDirectory() as tmp_dir:
            results_dir = Path(tmp_dir)
            for method in module.METHODS:
                module.paths_for_method(results_dir, method.key).input_path.write_text(
                    "[]", encoding="utf-8"
                )

            outputs = module.run_all_analyses(
                results_dir=results_dir,
                model_id="custom-model",
                batch_size=4,
                device="cpu",
                analyzer=analyzer,
            )

            self.assertEqual(set(outputs), {method.key for method in module.METHODS})
            self.assertEqual(len(analyzer.loaded_embedders), 1)
            self.assertEqual(analyzer.loaded_embedders[0][:2], ("custom-model", "cpu"))
            shared_embedder = analyzer.loaded_embedders[0][2]
            self.assertEqual(len(analyzer.analysis_calls), 3)

            for method, call in zip(
                module.METHODS, analyzer.analysis_calls, strict=True
            ):
                paths = module.paths_for_method(results_dir, method.key)
                self.assertEqual(call["input_path"], paths.input_path)
                self.assertEqual(call["scores_output_path"], paths.scores_output_path)
                self.assertEqual(call["report_output_path"], paths.report_output_path)
                self.assertIs(call["embedder"], shared_embedder)
                self.assertEqual(call["batch_size"], 4)
                self.assertEqual(call["device"], "cpu")
                self.assertIn(method.label, call["dataset_label"])
                self.assertTrue(paths.scores_output_path.exists())
                self.assertTrue(paths.report_output_path.exists())

    def test_validates_every_input_before_loading_the_embedder(self):
        module = load_methods_analyzer_module()
        analyzer = FakeAnalyzer()

        with tempfile.TemporaryDirectory() as tmp_dir:
            results_dir = Path(tmp_dir)
            first_method = module.METHODS[0]
            module.paths_for_method(
                results_dir, first_method.key
            ).input_path.write_text("[]", encoding="utf-8")

            with self.assertRaisesRegex(
                FileNotFoundError,
                "algorithm_only.*algorithm_with_paraphrasing",
            ):
                module.run_all_analyses(
                    results_dir=results_dir,
                    analyzer=analyzer,
                )

        self.assertEqual(analyzer.loaded_embedders, [])
        self.assertEqual(analyzer.analysis_calls, [])

    def test_rejects_non_positive_batch_size_before_loading_the_embedder(self):
        module = load_methods_analyzer_module()
        analyzer = FakeAnalyzer()

        with tempfile.TemporaryDirectory() as tmp_dir:
            results_dir = Path(tmp_dir)
            for method in module.METHODS:
                module.paths_for_method(results_dir, method.key).input_path.write_text(
                    "[]", encoding="utf-8"
                )

            with self.assertRaisesRegex(
                ValueError, "batch_size must be greater than zero"
            ):
                module.run_all_analyses(
                    results_dir=results_dir,
                    batch_size=0,
                    analyzer=analyzer,
                )

        self.assertEqual(analyzer.loaded_embedders, [])


if __name__ == "__main__":
    unittest.main()
