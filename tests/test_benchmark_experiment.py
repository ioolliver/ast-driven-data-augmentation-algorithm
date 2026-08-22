import json
import tempfile
import unittest
from pathlib import Path


from benchmark.artifacts import (
    CompletedExperimentError,
    initialize_experiment,
    mark_experiment_complete,
    mark_experiment_failed,
)
from benchmark.config import DEFAULT_CONFIG_PATH, load_config
from benchmark.data import prepare_dataset
from benchmark.prompting import build_training_record
from benchmark.runtime import validate_training_lengths
from benchmark.training import _resolve_checkpoint

from tests.test_benchmark_data import make_rows


class BenchmarkConfigTest(unittest.TestCase):
    def test_default_config_contains_reproducible_qlora_defaults(self):
        config = load_config(DEFAULT_CONFIG_PATH)

        self.assertEqual(config["model"]["id"], "Qwen/Qwen3.5-9B")
        self.assertTrue(config["quantization"]["load_in_4bit"])
        self.assertEqual(config["quantization"]["quant_type"], "nf4")
        self.assertEqual(config["training"]["max_length"], 8192)
        self.assertEqual(config["split"]["holdout_percentage"], 20)

    def test_rejects_an_invalid_training_length(self):
        config = load_config(DEFAULT_CONFIG_PATH)
        config["training"]["max_length"] = 0
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.yaml"
            import yaml

            path.write_text(yaml.safe_dump(config), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "max_length"):
                load_config(path)


class BenchmarkArtifactsTest(unittest.TestCase):
    def test_writes_reproducible_inputs_and_never_reuses_a_completed_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dataset_path = root / "dataset.json"
            schema_path = root / "schema.json"
            output_path = root / "experiment"
            dataset_path.write_text(json.dumps(make_rows()), encoding="utf-8")
            schema_path.write_text(
                json.dumps(
                    {
                        "tables": [
                            {
                                "name": "items",
                                "columns": [{"name": "id", "type": "number"}],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            prepared = prepare_dataset(
                dataset_path,
                holdout_percentage=20,
                seed=42,
                training_view="original-and-augmented",
            )
            config = load_config(DEFAULT_CONFIG_PATH)
            records = [
                build_training_record("items(id:number)", row["question"], row["sql"])
                for row in prepared.training_examples
            ]

            manifest = initialize_experiment(
                output_path=output_path,
                dataset_path=dataset_path,
                schema_path=schema_path,
                schema=json.loads(schema_path.read_text()),
                prepared=prepared,
                training_records=records,
                config=config,
                resume=False,
            )
            mark_experiment_complete(output_path, {"train_loss": 1.25})

            held_out = json.loads(
                (output_path / "held_out_queries.json").read_text(encoding="utf-8")
            )
            completed_manifest = json.loads(
                (output_path / "run_manifest.json").read_text(encoding="utf-8")
            )

            self.assertEqual(manifest["status"], "running")
            self.assertEqual(len(held_out), 2)
            self.assertEqual(completed_manifest["status"], "complete")
            self.assertTrue((output_path / "training_examples.jsonl").is_file())
            first_training_example = json.loads(
                (output_path / "training_examples.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()[0]
            )
            self.assertIn("prompt", first_training_example)
            self.assertIn("completion", first_training_example)

            with self.assertRaises(CompletedExperimentError):
                initialize_experiment(
                    output_path=output_path,
                    dataset_path=dataset_path,
                    schema_path=schema_path,
                    schema=json.loads(schema_path.read_text()),
                    prepared=prepared,
                    training_records=records,
                    config=config,
                    resume=True,
                )

    def test_can_restart_an_incomplete_experiment_without_a_checkpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dataset_path = root / "dataset.json"
            schema_path = root / "schema.json"
            output_path = root / "experiment"
            dataset_path.write_text(json.dumps(make_rows()), encoding="utf-8")
            schema = {
                "tables": [
                    {
                        "name": "items",
                        "columns": [{"name": "id", "type": "number"}],
                    }
                ]
            }
            schema_path.write_text(json.dumps(schema), encoding="utf-8")
            prepared = prepare_dataset(
                dataset_path,
                holdout_percentage=20,
                seed=42,
                training_view="original-and-augmented",
            )
            config = load_config(DEFAULT_CONFIG_PATH)
            records = [
                build_training_record("items(id:number)", row["question"], row["sql"])
                for row in prepared.training_examples
            ]
            initialize_experiment(
                output_path=output_path,
                dataset_path=dataset_path,
                schema_path=schema_path,
                schema=schema,
                prepared=prepared,
                training_records=records,
                config=config,
                resume=False,
            )
            mark_experiment_failed(output_path, "temporary failure")

            resumed = initialize_experiment(
                output_path=output_path,
                dataset_path=dataset_path,
                schema_path=schema_path,
                schema=schema,
                prepared=prepared,
                training_records=records,
                config=config,
                resume=True,
            )

        self.assertEqual(resumed["status"], "running")
        self.assertNotIn("error", resumed)


class BenchmarkCheckpointTest(unittest.TestCase):
    def test_latest_checkpoint_can_restart_from_scratch_when_none_was_written(self):
        with tempfile.TemporaryDirectory() as directory:
            checkpoint = _resolve_checkpoint(
                "latest", Path(directory), lambda _: None
            )

        self.assertIsNone(checkpoint)


class BenchmarkRuntimeTest(unittest.TestCase):
    def test_reports_source_ids_that_would_be_truncated(self):
        class FakeTokenizer:
            def apply_chat_template(self, messages, **kwargs):
                sql = messages[-1]["content"]
                return list(range(12 if "too long" in sql else 5))

        records = [
            {
                "prompt": [{"role": "user", "content": "question"}],
                "completion": [{"role": "assistant", "content": "too long"}],
            }
        ]
        examples = [{"source_id": "row-9", "variant": "augmented"}]

        with self.assertRaisesRegex(ValueError, "row-9.*12 tokens.*maximum is 10"):
            validate_training_lengths(FakeTokenizer(), records, examples, max_length=10)


if __name__ == "__main__":
    unittest.main()
