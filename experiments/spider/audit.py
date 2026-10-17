"""Offline audit of Spider training mutations (no LLM calls or held-out rows)."""
import argparse
import collections
import json
import random
import sqlite3
from pathlib import Path

from ast_augmentation.augmentor import _create_sql_variation

SCHEMAS = json.loads((Path(__file__).parents[2] / 'datasets/spider/schemas.json').read_text())


def audit(data_root, *, seed=42, without_semantic_groups=False):
    random.seed(seed)
    schemas = json.loads(json.dumps(SCHEMAS))
    if without_semantic_groups:
        for schema in schemas.values():
            for table in schema['tables']:
                for column in table['columns']:
                    column.pop('semantic_group', None)
    rows = json.loads((data_root / 'train_spider.json').read_text())
    counts = collections.defaultdict(collections.Counter)
    failures = []
    for index, row in enumerate(rows):
        db = row['db_id']
        if db not in schemas:
            continue
        counts[db]['total'] += 1
        try:
            sql, changes = _create_sql_variation(schemas[db], row['query'])
            if not changes:
                counts[db]['unchanged'] += 1
                continue
            counts[db]['changed'] += 1
            if any(change['old_line'].startswith('Coluna:') for change in changes):
                counts[db]['column_swap_rows'] += 1
            connection = sqlite3.connect(
                f'file:{data_root}/database/{db}/{db}.sqlite?mode=ro', uri=True
            )
            try:
                connection.execute('EXPLAIN QUERY PLAN ' + sql).fetchall()
                counts[db]['sqlite_valid'] += 1
            except sqlite3.Error as exc:
                counts[db]['sqlite_invalid'] += 1
                try:
                    connection.execute('EXPLAIN QUERY PLAN ' + row['query']).fetchall()
                except sqlite3.Error:
                    category = 'source_invalid'
                else:
                    category = 'mutation_invalid'
                counts[db][category] += 1
                failures.append({'source_index': index, 'db_id': db,
                                 'category': category, 'error': str(exc)})
            finally:
                connection.close()
        except Exception as exc:
            counts[db]['error'] += 1
            if counts[db]['error'] <= 3:
                print(db, 'ERROR', row['query'], type(exc).__name__, str(exc)[:180])
    for db in sorted(counts):
        print(db, dict(counts[db]))
    total = collections.Counter()
    for counter in counts.values():
        total.update(counter)
    print('TOTAL', dict(total))
    return {'seed': seed, 'split': 'train_spider.json',
            'semantic_groups_enabled': not without_semantic_groups,
            'catalog_databases': len(schemas), 'training_databases': len(counts),
            'failures': failures, 'total': dict(total), 'by_database': {db: dict(c) for db, c in sorted(counts.items())}}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('data_root', type=Path)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--without-semantic-groups', action='store_true')
    parser.add_argument('--output', type=Path, help='Save machine-readable audit counts')
    args = parser.parse_args()
    report = audit(args.data_root, seed=args.seed,
                   without_semantic_groups=args.without_semantic_groups)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
