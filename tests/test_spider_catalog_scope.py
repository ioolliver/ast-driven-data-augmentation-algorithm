import json
from pathlib import Path
import tempfile
import unittest

import sqlglot

from ast_augmentation.mutations.between import mutate_between
from experiments.spider.generate import prepare_rows
from experiments.spider.prepare_finetuning import prepare, METHODS


class SpiderCatalogScopeTest(unittest.TestCase):
    def test_catalog_has_all_databases_and_reviewed_notes(self):
        root = Path(__file__).parents[1] / 'datasets/spider'
        catalog = json.loads((root / 'schemas.json').read_text())
        groups = json.loads((root / 'semantic_groups.json').read_text())
        notes = json.loads((root / 'curation_notes.json').read_text())
        self.assertEqual(len(catalog), 206)
        self.assertEqual(set(catalog), set(groups))
        self.assertEqual(set(catalog), set(notes))
        for db, schema in catalog.items():
            self.assertEqual(schema['dialect'], 'sqlite')
            self.assertTrue(notes[db])
            for table in schema['tables']:
                for column in table['columns']:
                    self.assertTrue(column['description'])
                    self.assertIn(column['type'], ('string', 'number', 'date', 'enum', 'boolean'))
                    if column['provenance']['key']:
                        self.assertNotIn('semantic_group', column, (db, column['name']))
                        self.assertNotIn('enums', column)
                        self.assertNotIn('min', column)

    def test_heldout_catalog_entries_are_not_generation_seeds(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            train = [{'db_id': 'hr_1', 'question': 'Training?', 'query': 'SELECT 1'}]
            (root / 'train_spider.json').write_text(json.dumps(train))
            # Both IDs have metadata, but only the training file may be read.
            (root / 'dev.json').write_text(json.dumps([{'db_id': 'concert_singer'}]))
            (root / 'test.json').write_text('invalid JSON must not be read')
            self.assertEqual(prepare_rows(root), list(enumerate(train)))

    def test_between_without_profiled_bounds_skips_safely(self):
        for kind in ('number', 'date'):
            schema = {'tables': [{'name': 't', 'columns': [{'name': 'id', 'type': kind}]}]}
            node = sqlglot.parse_one('SELECT id FROM t WHERE id BETWEEN 1 AND 2').find(sqlglot.exp.Between)
            changes = []
            self.assertIs(mutate_between(node, changes, schema), node)
            self.assertEqual(changes, [])

    def test_finetuning_accepts_run_scope_with_heldout_catalog_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data, aug, out = root / 'data', root / 'aug', root / 'out'
            data.mkdir(); aug.mkdir()
            train = [{'db_id': 'hr_1', 'question': f'Question {i}', 'query': 'SELECT 1'} for i in range(7000)]
            (data / 'train_spider.json').write_text(json.dumps(train))
            (data / 'dev.json').write_text(json.dumps([{'db_id': 'concert_singer', 'question': 'Held out?', 'query': 'SELECT 1'}]))
            tables = [{'db_id': db, 'table_names_original': ['t'],
                       'column_names_original': [[-1, '*'], [0, 'x']],
                       'column_types': ['text', 'number'], 'foreign_keys': [], 'primary_keys': []}
                      for db in ('hr_1', 'concert_singer')]
            (data / 'tables.json').write_text(json.dumps(tables))
            for method in METHODS:
                indices = range(7000) if method == 'paraphrase' else [0]
                rows = [dict(source_index=i, db_id='hr_1', method=method,
                             source_question=train[i]['question'], source_sql='SELECT 1',
                             question='Adapted?', query='SELECT 1' if method == 'paraphrase' else 'SELECT 2')
                        for i in indices]
                (aug / f'{method}.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in rows))
            manifest = prepare(data, aug, out)
            self.assertEqual(manifest['selected_db_ids'], ['hr_1'])
            self.assertEqual(manifest['counts']['ast']['total'], 7001)
            # A partial paraphrase run must still be rejected.
            path = aug / 'paraphrase.jsonl'
            path.write_text(path.read_text().splitlines()[0] + '\n')
            with self.assertRaisesRegex(ValueError, 'every original row'):
                prepare(data, aug, out)


if __name__ == '__main__':
    unittest.main()
