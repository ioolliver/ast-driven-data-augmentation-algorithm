import json
import tempfile
import unittest
from pathlib import Path


from benchmark.data import load_augmented_rows, prepare_dataset


def make_rows(count=10):
    levels = ("Fácil", "Média")
    return [
        {
            "id": index,
            "level": levels[index % len(levels)],
            "original_question": f"Pergunta original {index}",
            "original_sql": f"SELECT {index}",
            "changed_question": f"Pergunta aumentada {index}",
            "changed_sql": f"SELECT {index + 100}",
        }
        for index in range(1, count + 1)
    ]


class PrepareDatasetTest(unittest.TestCase):
    def test_reserves_original_rows_by_id_before_expanding_training_pairs(self):
        with tempfile.TemporaryDirectory() as directory:
            dataset_path = Path(directory) / "augmented.json"
            dataset_path.write_text(
                json.dumps(make_rows(), ensure_ascii=False), encoding="utf-8"
            )

            prepared = prepare_dataset(
                dataset_path,
                holdout_percentage=20,
                seed=42,
                training_view="original-and-augmented",
            )

        held_out_ids = {row["id"] for row in prepared.held_out_queries}
        training_ids = {row["source_id"] for row in prepared.training_examples}

        self.assertEqual(len(held_out_ids), 2)
        self.assertTrue(held_out_ids.isdisjoint(training_ids))
        self.assertEqual(len(prepared.training_examples), 16)
        self.assertTrue(
            all(row["variant"] == "original" for row in prepared.held_out_queries)
        )

    def test_uses_the_same_split_for_different_augmentation_methods(self):
        with tempfile.TemporaryDirectory() as directory:
            first_path = Path(directory) / "paraphrase.json"
            second_path = Path(directory) / "algorithm.json"
            first_rows = make_rows(25)
            second_rows = make_rows(25)
            for row in second_rows:
                row["changed_question"] += " pelo algoritmo"
                row["changed_sql"] += " /* algorithm */"
            first_path.write_text(json.dumps(first_rows), encoding="utf-8")
            second_path.write_text(json.dumps(second_rows), encoding="utf-8")

            first = prepare_dataset(
                first_path,
                holdout_percentage=20,
                seed=7,
                training_view="original-and-augmented",
            )
            second = prepare_dataset(
                second_path,
                holdout_percentage=20,
                seed=7,
                training_view="original-and-augmented",
            )

        self.assertEqual(first.held_out_ids, second.held_out_ids)

    def test_original_only_view_never_adds_augmented_examples(self):
        with tempfile.TemporaryDirectory() as directory:
            dataset_path = Path(directory) / "augmented.json"
            dataset_path.write_text(json.dumps(make_rows()), encoding="utf-8")

            prepared = prepare_dataset(
                dataset_path,
                holdout_percentage=20,
                seed=42,
                training_view="original-only",
            )

        self.assertEqual(len(prepared.training_examples), 8)
        self.assertTrue(
            all(row["variant"] == "original" for row in prepared.training_examples)
        )

    def test_rejects_duplicate_ids_with_actionable_context(self):
        rows = make_rows(2)
        rows[1]["id"] = rows[0]["id"]
        with tempfile.TemporaryDirectory() as directory:
            dataset_path = Path(directory) / "augmented.json"
            dataset_path.write_text(json.dumps(rows), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "duplicate id 1"):
                load_augmented_rows(dataset_path)

    def test_rejects_invalid_holdout_percentage(self):
        with tempfile.TemporaryDirectory() as directory:
            dataset_path = Path(directory) / "augmented.json"
            dataset_path.write_text(json.dumps(make_rows()), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "greater than 0"):
                prepare_dataset(
                    dataset_path,
                    holdout_percentage=100,
                    seed=42,
                    training_view="original-and-augmented",
                )


if __name__ == "__main__":
    unittest.main()
