import importlib.util
import json
import tempfile
import threading
import time
import unittest
from pathlib import Path


def load_apply_censo_dataset_module():
    module_path = (
        Path(__file__).resolve().parents[1]
        / "data"
        / "censo_escolar_dataset"
        / "apply_augmentation_censo_escolar_dataset.py"
    )
    spec = importlib.util.spec_from_file_location(
        "apply_censo_dataset_script", module_path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_query(query_id, question=None, sql=None, level="Fácil"):
    return {
        "id": query_id,
        "pergunta_nl": question or f"Pergunta {query_id}",
        "sql": sql or f"SELECT {query_id}",
        "classificacao_tematica": {
            "tema_principal": "Matrículas",
            "subtema": "Contagem",
            "tema_transversal": None,
        },
        "complexidade": {
            "nivel": level,
            "score_total": 1,
            "pontuacao_por_criterio": {"joins": 0},
        },
        "metadados_estruturais": {"joins": {"num_joins": 0}},
    }


class ApplyAugmentationCensoEscolarDatasetTest(unittest.TestCase):
    def test_build_augmented_outputs_returns_reduced_mixed_and_changed_rows(self):
        module = load_apply_censo_dataset_module()
        queries = [
            build_query(10, level="Fácil"),
            build_query(11, level="Média"),
        ]

        def fake_augment(question, sql):
            return (f"{question} mudada", f"{sql} -- changed")

        mixed_rows, changed_rows = module.build_augmented_outputs(
            queries, fake_augment
        )

        self.assertEqual(
            mixed_rows,
            [
                {
                    "question": "Pergunta 10",
                    "level": "Fácil",
                    "sql_code": "SELECT 10",
                    "augmented": False,
                },
                {
                    "question": "Pergunta 10 mudada",
                    "level": "Fácil",
                    "sql_code": "SELECT 10 -- changed",
                    "augmented": True,
                },
                {
                    "question": "Pergunta 11",
                    "level": "Média",
                    "sql_code": "SELECT 11",
                    "augmented": False,
                },
                {
                    "question": "Pergunta 11 mudada",
                    "level": "Média",
                    "sql_code": "SELECT 11 -- changed",
                    "augmented": True,
                },
            ],
        )
        self.assertEqual(
            changed_rows,
            [
                {
                    "original_question": "Pergunta 10",
                    "original_sql": "SELECT 10",
                    "changed_question": "Pergunta 10 mudada",
                    "changed_sql": "SELECT 10 -- changed",
                    "level": "Fácil",
                },
                {
                    "original_question": "Pergunta 11",
                    "original_sql": "SELECT 11",
                    "changed_question": "Pergunta 11 mudada",
                    "changed_sql": "SELECT 11 -- changed",
                    "level": "Média",
                },
            ],
        )

    def test_load_queries_validates_the_censo_source_contract(self):
        module = load_apply_censo_dataset_module()

        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = Path(tmp_dir) / "input.json"
            module.write_json(input_path, {"dataset_info": {}, "queries": [{}]})

            with self.assertRaisesRegex(
                ValueError, "Query at index 0 is missing required field: id"
            ):
                module.load_queries(input_path)

    def test_build_augmented_outputs_limits_concurrency_and_preserves_order(self):
        module = load_apply_censo_dataset_module()
        queries = [build_query(index) for index in range(6)]
        active_calls = 0
        highest_active_calls = 0
        lock = threading.Lock()

        def fake_augment(question, sql):
            nonlocal active_calls, highest_active_calls
            with lock:
                active_calls += 1
                highest_active_calls = max(highest_active_calls, active_calls)
            time.sleep(0.02)
            with lock:
                active_calls -= 1
            return (f"{question} mudada", f"{sql} -- changed")

        _, changed_rows = module.build_augmented_outputs(
            queries, fake_augment, max_workers=2
        )

        self.assertGreater(highest_active_calls, 1)
        self.assertLessEqual(highest_active_calls, 2)
        self.assertEqual(
            [row["original_question"] for row in changed_rows],
            [query["pergunta_nl"] for query in queries],
        )

    def test_build_augmented_outputs_rejects_non_positive_worker_limit(self):
        module = load_apply_censo_dataset_module()

        with self.assertRaisesRegex(
            ValueError, "max_workers must be greater than zero"
        ):
            module.build_augmented_outputs(
                [], lambda question, sql: None, max_workers=0
            )

    def test_augmentation_failure_includes_query_id(self):
        module = load_apply_censo_dataset_module()

        def fake_augment(question, sql):
            raise RuntimeError("llm offline")

        with self.assertRaisesRegex(
            RuntimeError, "Failed to augment query id=99: llm offline"
        ):
            module.build_augmented_outputs([build_query(99)], fake_augment)

    def test_run_batch_logs_progress_and_writes_outputs(self):
        module = load_apply_censo_dataset_module()
        payload = {
            "dataset_info": {"nome": "CensoBench", "total_queries": 2},
            "queries": [build_query(1), build_query(2, level="Média")],
        }

        def fake_augment(question, sql):
            return (f"{question} mudada", f"{sql} -- changed")

        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = Path(tmp_dir) / "input.json"
            mixed_output_path = Path(tmp_dir) / "mixed.json"
            changed_output_path = Path(tmp_dir) / "changed.json"
            module.write_json(input_path, payload)

            with self.assertLogs(module.LOGGER, level="INFO") as logs:
                module.run_batch(
                    dataset_path=input_path,
                    mixed_output_path=mixed_output_path,
                    changed_only_output_path=changed_output_path,
                    schema={},
                    augment_pair=fake_augment,
                    max_workers=2,
                )

            with mixed_output_path.open(encoding="utf-8") as file_obj:
                self.assertEqual(len(json.load(file_obj)), 4)
            with changed_output_path.open(encoding="utf-8") as file_obj:
                self.assertEqual(len(json.load(file_obj)), 2)

        output = "\n".join(logs.output)
        self.assertIn("Starting augmentation batch: queries=2 max_workers=2", output)
        self.assertIn("completed=2/2", output)
        self.assertIn("succeeded=2 failed=0", output)
        self.assertIn("Wrote augmentation outputs: augmented_pairs=2", output)

    def test_run_batch_stops_without_writing_partial_outputs(self):
        module = load_apply_censo_dataset_module()
        payload = {
            "dataset_info": {"nome": "CensoBench", "total_queries": 1},
            "queries": [build_query(99)],
        }

        def fake_augment(question, sql):
            raise RuntimeError("llm offline")

        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = Path(tmp_dir) / "input.json"
            mixed_output_path = Path(tmp_dir) / "mixed.json"
            changed_output_path = Path(tmp_dir) / "changed.json"
            module.write_json(input_path, payload)

            with self.assertLogs(module.LOGGER, level="INFO") as logs:
                with self.assertRaisesRegex(
                    RuntimeError, "Failed to augment query id=99"
                ):
                    module.run_batch(
                        dataset_path=input_path,
                        mixed_output_path=mixed_output_path,
                        changed_only_output_path=changed_output_path,
                        schema={},
                        augment_pair=fake_augment,
                        max_workers=1,
                    )

            self.assertFalse(mixed_output_path.exists())
            self.assertFalse(changed_output_path.exists())

        output = "\n".join(logs.output)
        self.assertIn("completed=1/1", output)
        self.assertIn("succeeded=0 failed=1", output)
        self.assertIn("Augmentation batch stopped after a failed query.", output)


if __name__ == "__main__":
    unittest.main()
