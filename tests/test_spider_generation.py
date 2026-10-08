import json
import tempfile
import time
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

    def test_skips_completed_paraphrases_and_resumes_ast_checkpoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'train_spider.json').write_text(json.dumps([
                {'db_id': 'selected', 'question': f'Question {i}?', 'query': f'SELECT {i}'}
                for i in range(3)
            ]))
            output = root / 'output'
            with (
                patch.dict(module.SCHEMAS, {'selected': {'dialect': 'sqlite'}}, clear=True),
                patch.object(module, '_create_sql_variation', side_effect=lambda schema, sql: (
                    sql + ' FROM t', [{'old_line': sql, 'new_line': sql + ' FROM t'}]
                )),
                patch.object(module, 'sqlite_valid', return_value=True),
                patch.object(module, 'paraphrase_query', side_effect=lambda q, **kw: 'P ' + q) as paraphrase,
                patch.object(module, 'adapt_query', side_effect=lambda q, *args, **kw: 'A ' + q) as adapt,
            ):
                module.generate(root, output, methods=('paraphrase',), max_workers=2, progress_every=1)
                original_bytes = (output / 'paraphrase.jsonl').read_bytes()
                module.generate(root, output, methods=('paraphrase', 'ast'), max_workers=2,
                                progress_every=1)
                self.assertEqual((output / 'paraphrase.jsonl').read_bytes(), original_bytes)
                self.assertEqual(paraphrase.call_count, 3)
                self.assertEqual(adapt.call_count, 3)

                ast_path = output / 'ast.jsonl'
                saved = ast_path.read_text().splitlines()[0]
                ast_path.unlink()
                (output / 'ast.jsonl.tmp').write_text(saved + '\n' + '{"partial":')
                module.generate(root, output, methods=('ast',), max_workers=2,
                                progress_every=1)
                self.assertEqual(adapt.call_count, 5)
                self.assertEqual([json.loads(line)['source_index'] for line in
                                  ast_path.read_text().splitlines()], [0, 1, 2])

    def test_parallel_completion_preserves_order_and_rejects_mismatched_seed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'train_spider.json').write_text(json.dumps([
                {'db_id': 'selected', 'question': f'Q {i}', 'query': f'SELECT {i}'}
                for i in range(4)
            ]))

            def slow_paraphrase(question, **kwargs):
                if question == 'Q 0':
                    time.sleep(0.03)
                return 'P ' + question

            with (
                patch.dict(module.SCHEMAS, {'selected': {}}, clear=True),
                patch.object(module, 'paraphrase_query', side_effect=slow_paraphrase),
            ):
                module.generate(root, root / 'output', methods=('paraphrase',),
                                max_workers=3, progress_every=2)
            path = root / 'output' / 'paraphrase.jsonl'
            self.assertEqual([json.loads(line)['source_index'] for line in
                              path.read_text().splitlines()], [0, 1, 2, 3])
            changed = json.loads(path.read_text().splitlines()[0])
            changed['source_sql'] = 'SELECT WRONG'
            lines = path.read_text().splitlines()
            lines[0] = json.dumps(changed)
            path.write_text('\n'.join(lines) + '\n')
            with patch.dict(module.SCHEMAS, {'selected': {}}, clear=True):
                with self.assertRaisesRegex(ValueError, 'does not match'):
                    module.generate(root, root / 'output', methods=('paraphrase',))

    def test_provider_error_leaves_resumable_checkpoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'train_spider.json').write_text(json.dumps([
                {'db_id': 'selected', 'question': f'Q {i}', 'query': f'SELECT {i}'}
                for i in range(3)
            ]))
            calls = []

            def fail_once(question, **kwargs):
                calls.append(question)
                if question == 'Q 1' and calls.count(question) == 1:
                    raise RuntimeError('temporary provider error')
                return 'P ' + question

            with (
                patch.dict(module.SCHEMAS, {'selected': {}}, clear=True),
                patch.object(module, 'paraphrase_query', side_effect=fail_once),
            ):
                with self.assertRaisesRegex(RuntimeError, 'source_index 1 failed'):
                    module.generate(root, root / 'output', methods=('paraphrase',),
                                    max_workers=1)
                checkpoint = root / 'output' / 'paraphrase.jsonl.tmp'
                self.assertTrue(checkpoint.is_file())
                self.assertFalse((root / 'output' / 'paraphrase.jsonl').exists())
                module.generate(root, root / 'output', methods=('paraphrase',),
                                max_workers=1)
            self.assertEqual(calls.count('Q 0'), 1)
            self.assertEqual(len((root / 'output' / 'paraphrase.jsonl').read_text().splitlines()), 3)


if __name__ == "__main__":
    unittest.main()
