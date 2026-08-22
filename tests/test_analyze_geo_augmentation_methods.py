import importlib.util
import tempfile
import unittest
from pathlib import Path


def load_module(filename, module_name):
    module_path = (
        Path(__file__).resolve().parents[1]
        / "data"
        / "geo_dataset"
        / filename
    )
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeSemanticAnalyzer:
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
        return {"dataset_label": kwargs["dataset_label"]}


class FakeComponentAnalyzer:
    SQL_DIALECT = "postgres"

    def __init__(self):
        self.analysis_calls = []

    def run_analysis(self, **kwargs):
        self.analysis_calls.append(kwargs)
        return {"dataset_label": kwargs["dataset_label"]}


class AnalyzeGeoAugmentationMethodsTest(unittest.TestCase):
    def test_semantic_analysis_reuses_one_embedder_for_all_methods(self):
        module = load_module(
            "analyze_semantic_variation_methods.py",
            "analyze_geo_semantic_variation_methods",
        )
        analyzer = FakeSemanticAnalyzer()

        with tempfile.TemporaryDirectory() as tmp_dir:
            results_dir = Path(tmp_dir)
            self._write_all_inputs(module, results_dir)

            outputs = module.run_all_analyses(
                results_dir=results_dir,
                model_id="custom-model",
                batch_size=4,
                device="cpu",
                analyzer=analyzer,
            )

        self.assertEqual(set(outputs), {method.key for method in module.METHODS})
        self.assertEqual(len(analyzer.loaded_embedders), 1)
        shared_embedder = analyzer.loaded_embedders[0][2]
        self.assertEqual(len(analyzer.analysis_calls), 3)
        for method, call in zip(module.METHODS, analyzer.analysis_calls, strict=True):
            self.assertIs(call["embedder"], shared_embedder)
            self.assertEqual(call["batch_size"], 4)
            self.assertEqual(call["device"], "cpu")
            self.assertIn(method.label, call["dataset_label"])
            self.assertEqual(call["report_output_path"].suffix, ".xlsx")

    def test_semantic_analysis_validates_all_inputs_before_loading_model(self):
        module = load_module(
            "analyze_semantic_variation_methods.py",
            "analyze_geo_semantic_variation_methods_missing",
        )
        analyzer = FakeSemanticAnalyzer()

        with tempfile.TemporaryDirectory() as tmp_dir:
            with self.assertRaisesRegex(FileNotFoundError, "paraphrase_only"):
                module.run_all_analyses(
                    results_dir=Path(tmp_dir), analyzer=analyzer
                )

        self.assertEqual(analyzer.loaded_embedders, [])
        self.assertEqual(analyzer.analysis_calls, [])

    def test_component_analysis_runs_all_methods_with_postgres_dialect(self):
        module = load_module(
            "analyze_component_matching_methods.py",
            "analyze_geo_component_matching_methods",
        )
        analyzer = FakeComponentAnalyzer()

        with tempfile.TemporaryDirectory() as tmp_dir:
            results_dir = Path(tmp_dir)
            self._write_all_inputs(module, results_dir)

            outputs = module.run_all_analyses(
                results_dir=results_dir, analyzer=analyzer
            )

        self.assertEqual(set(outputs), {method.key for method in module.METHODS})
        self.assertEqual(len(analyzer.analysis_calls), 3)
        for method, call in zip(module.METHODS, analyzer.analysis_calls, strict=True):
            self.assertEqual(call["sql_dialect"], "postgres")
            self.assertIn(method.label, call["dataset_label"])
            self.assertEqual(call["report_output_path"].suffix, ".xlsx")

    def test_component_analysis_validates_all_inputs_before_writing_outputs(self):
        module = load_module(
            "analyze_component_matching_methods.py",
            "analyze_geo_component_matching_methods_missing",
        )
        analyzer = FakeComponentAnalyzer()

        with tempfile.TemporaryDirectory() as tmp_dir:
            with self.assertRaisesRegex(FileNotFoundError, "algorithm_only"):
                module.run_all_analyses(
                    results_dir=Path(tmp_dir), analyzer=analyzer
                )

        self.assertEqual(analyzer.analysis_calls, [])

    @staticmethod
    def _write_all_inputs(module, results_dir):
        for method in module.METHODS:
            module.paths_for_method(results_dir, method.key).input_path.write_text(
                "[]", encoding="utf-8"
            )


if __name__ == "__main__":
    unittest.main()
