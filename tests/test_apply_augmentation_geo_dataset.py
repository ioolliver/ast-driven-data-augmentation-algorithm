import importlib.util
import json
import tempfile
import threading
import time
import unittest
from pathlib import Path


def load_apply_geo_dataset_module():
    module_path = (
        Path(__file__).resolve().parents[1]
        / "data"
        / "geo_dataset"
        / "apply_augmentation_geo_dataset.py"
    )
    spec = importlib.util.spec_from_file_location("apply_geo_dataset_script", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ApplyAugmentationGeoDatasetTest(unittest.TestCase):
    def test_build_augmented_outputs_returns_mixed_and_changesets(self):
        module = load_apply_geo_dataset_module()
        dataset = [
            {
                "id": 10,
                "question": "Pergunta original 1",
                "level": "Facil",
                "sql_code": "SELECT 1",
            },
            {
                "id": 11,
                "question": "Pergunta original 2",
                "level": "Medio",
                "sql_code": "SELECT 2",
            },
        ]

        def fake_augment(question, sql_code):
            return (f"{question} mudada", f"{sql_code} -- changed")

        mixed_rows, changed_rows = module.build_augmented_outputs(dataset, fake_augment)

        self.assertEqual(
            mixed_rows,
            [
                {
                    "question": "Pergunta original 1",
                    "level": "Facil",
                    "sql_code": "SELECT 1",
                    "augmented": False,
                },
                {
                    "question": "Pergunta original 1 mudada",
                    "level": "Facil",
                    "sql_code": "SELECT 1 -- changed",
                    "augmented": True,
                },
                {
                    "question": "Pergunta original 2",
                    "level": "Medio",
                    "sql_code": "SELECT 2",
                    "augmented": False,
                },
                {
                    "question": "Pergunta original 2 mudada",
                    "level": "Medio",
                    "sql_code": "SELECT 2 -- changed",
                    "augmented": True,
                },
            ],
        )
        self.assertEqual(
            changed_rows,
            [
                {
                    "original_question": "Pergunta original 1",
                    "original_sql": "SELECT 1",
                    "changed_question": "Pergunta original 1 mudada",
                    "changed_sql": "SELECT 1 -- changed",
                    "level": "Facil",
                },
                {
                    "original_question": "Pergunta original 2",
                    "original_sql": "SELECT 2",
                    "changed_question": "Pergunta original 2 mudada",
                    "changed_sql": "SELECT 2 -- changed",
                    "level": "Medio",
                },
            ],
        )

    def test_build_augmented_outputs_raises_row_context_on_failure(self):
        module = load_apply_geo_dataset_module()
        dataset = [
            {
                "id": 99,
                "question": "Falha",
                "level": "Dificil",
                "sql_code": "SELECT boom",
            }
        ]

        def fake_augment(question, sql_code):
            raise RuntimeError("llm offline")

        with self.assertRaisesRegex(
            RuntimeError, "Failed to augment row id=99: llm offline"
        ):
            module.build_augmented_outputs(dataset, fake_augment)

    def test_build_augmented_outputs_limits_concurrency_and_preserves_order(self):
        module = load_apply_geo_dataset_module()
        dataset = [
            {
                "id": index,
                "question": f"Pergunta {index}",
                "level": "Facil",
                "sql_code": f"SELECT {index}",
            }
            for index in range(6)
        ]
        active_calls = 0
        highest_active_calls = 0
        lock = threading.Lock()

        def fake_augment(question, sql_code):
            nonlocal active_calls, highest_active_calls
            with lock:
                active_calls += 1
                highest_active_calls = max(highest_active_calls, active_calls)
            time.sleep(0.02)
            with lock:
                active_calls -= 1
            return (f"{question} mudada", f"{sql_code} -- changed")

        _, changed_rows = module.build_augmented_outputs(
            dataset, fake_augment, max_workers=2
        )

        self.assertGreater(highest_active_calls, 1)
        self.assertLessEqual(highest_active_calls, 2)
        self.assertEqual(
            [row["original_question"] for row in changed_rows],
            [row["question"] for row in dataset],
        )

    def test_build_augmented_outputs_rejects_non_positive_worker_limit(self):
        module = load_apply_geo_dataset_module()

        with self.assertRaisesRegex(ValueError, "max_workers must be greater than zero"):
            module.build_augmented_outputs([], lambda question, sql_code: None, max_workers=0)

    def test_run_batch_logs_progress_and_written_outputs(self):
        module = load_apply_geo_dataset_module()
        dataset = [
            {
                "id": 1,
                "question": "Pergunta 1",
                "level": "Facil",
                "sql_code": "SELECT 1",
            },
            {
                "id": 2,
                "question": "Pergunta 2",
                "level": "Medio",
                "sql_code": "SELECT 2",
            },
        ]

        def fake_augment(question, sql_code):
            return (f"{question} mudada", f"{sql_code} -- changed")

        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = Path(tmp_dir) / "input.json"
            mixed_output_path = Path(tmp_dir) / "mixed.json"
            changed_output_path = Path(tmp_dir) / "changed.json"
            module.write_json(input_path, dataset)

            with self.assertLogs(module.LOGGER, level="INFO") as logs:
                module.run_batch(
                    dataset_path=input_path,
                    mixed_output_path=mixed_output_path,
                    changed_only_output_path=changed_output_path,
                    schema={},
                    augment_pair=fake_augment,
                    max_workers=2,
                )

        output = "\n".join(logs.output)
        self.assertIn("Starting augmentation batch: rows=2 max_workers=2", output)
        self.assertIn("completed=2/2", output)
        self.assertIn("succeeded=2 failed=0", output)
        self.assertIn("Wrote augmentation outputs: augmented_pairs=2", output)

    def test_run_batch_logs_failed_row_before_stopping(self):
        module = load_apply_geo_dataset_module()
        dataset = [
            {
                "id": 99,
                "question": "Falha",
                "level": "Dificil",
                "sql_code": "SELECT boom",
            }
        ]

        def fake_augment(question, sql_code):
            raise RuntimeError("llm offline")

        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = Path(tmp_dir) / "input.json"
            module.write_json(input_path, dataset)

            with self.assertLogs(module.LOGGER, level="INFO") as logs:
                with self.assertRaisesRegex(RuntimeError, "Failed to augment row id=99"):
                    module.run_batch(
                        dataset_path=input_path,
                        mixed_output_path=Path(tmp_dir) / "mixed.json",
                        changed_only_output_path=Path(tmp_dir) / "changed.json",
                        schema={},
                        augment_pair=fake_augment,
                        max_workers=1,
                    )

        output = "\n".join(logs.output)
        self.assertIn("completed=1/1", output)
        self.assertIn("succeeded=0 failed=1", output)
        self.assertIn("Augmentation batch stopped after a failed row.", output)

    def test_write_json_preserves_utf8_content(self):
        module = load_apply_geo_dataset_module()
        payload = [{"question": "São Paulo", "augmented": False}]

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "saida.json"
            module.write_json(output_path, payload)

            with output_path.open(encoding="utf-8") as file_obj:
                self.assertEqual(json.load(file_obj), payload)


if __name__ == "__main__":
    unittest.main()
