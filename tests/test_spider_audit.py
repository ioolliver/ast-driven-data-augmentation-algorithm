import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments.spider.audit import audit, _schema_connection


class SpiderAuditTest(unittest.TestCase):
    def test_schema_only_distinguishes_source_failure_and_does_not_need_databases(self):
        schema = {'dialect': 'sqlite', 'coverage_fallbacks': True, 'tables': [
            {'name': 't', 'columns': [{'name': 'x', 'type': 'number'}]}]}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rows = [{'db_id': 'toy', 'query': query} for query in (
                'SELECT x FROM t ORDER BY x',
                'SELECT x FROM missing ORDER BY x',
                'SELECT x FROM t',
            )]
            (root / 'train_spider.json').write_text(json.dumps(rows))
            with patch('experiments.spider.audit.SCHEMAS', {'toy': schema}), contextlib.redirect_stdout(io.StringIO()):
                report = audit(root, schema_only=True)
        self.assertEqual(report['validation_mode'], 'empty_schema_planning')
        self.assertEqual(report['total'], {'total': 3, 'changed': 2, 'schema_plannable': 1,
                                          'schema_unplannable': 1, 'source_invalid': 1, 'unchanged': 1})
        self.assertEqual(report['fallback_families'], {'order_direction': 2})
        self.assertNotIn('sqlite_valid', report['total'])

    def test_schema_only_supports_sqlite_sequence_and_quoted_identifiers(self):
        schema = {'tables': [
            {'name': 'sqlite_sequence', 'columns': [{'name': 'name'}, {'name': 'seq'}]},
            {'name': 'a"b', 'columns': [{'name': 'c"d'}]},
        ]}
        con = _schema_connection(schema)
        try:
            con.execute('EXPLAIN QUERY PLAN SELECT name,seq FROM sqlite_sequence')
            con.execute('EXPLAIN QUERY PLAN SELECT "c""d" FROM "a""b"')
        finally:
            con.close()


if __name__ == '__main__':
    unittest.main()
