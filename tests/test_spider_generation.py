import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from experiments.spider import generate as module


class SpiderGenerationTest(unittest.TestCase):
    def test_shared_ast_sql_and_train_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "train_spider.json").write_text(json.dumps([
                {"db_id": "selected", "question": "Original?", "query": "SELECT 1"},
                {"db_id": "excluded", "question": "Ignore?", "query": "SELECT 2"},
            ]))
            (root / "dev.json").write_text(json.dumps([
                {"db_id": "selected", "question": "Holdout?", "query": "SELECT 3"}
            ]))
            with (
                patch.dict(module.SCHEMAS, {"selected": {"dialect": "sqlite"}}, clear=True),
                patch.object(module, "_create_sql_variation", return_value=("SELECT 4", [{"old_line": "1", "new_line": "4"}])),
                patch.object(module, "sqlite_valid", return_value=True),
                patch.object(module, "paraphrase_query", return_value="Paraphrased?"),
                patch.object(module, "adapt_query", return_value="Adapted?"),
            ):
                module.generate(root, root / "output")
            outputs = {}
            for method in module.METHODS:
                lines = (root / "output" / f"{method}.jsonl").read_text().splitlines()
                self.assertEqual(len(lines), 1)
                outputs[method] = json.loads(lines[0])
                self.assertEqual(outputs[method]["source_index"], 0)
            self.assertEqual(outputs["ast"]["query"], outputs["ast_paraphrase"]["query"])
            self.assertEqual(outputs["paraphrase"]["query"], "SELECT 1")


if __name__ == "__main__":
    unittest.main()
