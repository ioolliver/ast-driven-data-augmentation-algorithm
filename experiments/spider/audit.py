"""Offline audit of the selected Spider training subset (no LLM calls)."""
import argparse
import collections
import json
import random
import sqlite3
from pathlib import Path

from ast_augmentation.augmentor import _create_sql_variation

SCHEMAS = json.loads((Path(__file__).parents[2] / 'datasets/spider/schemas.json').read_text())


def audit(data_root, *, seed=42):
    random.seed(seed)
    rows = json.loads((data_root / 'train_spider.json').read_text())
    counts = collections.defaultdict(collections.Counter)
    for row in rows:
        db = row['db_id']
        if db not in SCHEMAS:
            continue
        counts[db]['total'] += 1
        try:
            sql, changes = _create_sql_variation(SCHEMAS[db], row['query'])
            if not changes:
                counts[db]['unchanged'] += 1
                continue
            counts[db]['changed'] += 1
            connection = sqlite3.connect(
                f'file:{data_root}/database/{db}/{db}.sqlite?mode=ro', uri=True
            )
            try:
                connection.execute('EXPLAIN QUERY PLAN ' + sql).fetchall()
                counts[db]['sqlite_valid'] += 1
            except sqlite3.Error:
                counts[db]['sqlite_invalid'] += 1
            finally:
                connection.close()
        except Exception as exc:
            counts[db]['error'] += 1
            if counts[db]['error'] <= 3:
                print(db, 'ERROR', row['query'], type(exc).__name__, str(exc)[:180])
    for db in SCHEMAS:
        print(db, dict(counts[db]))
    total = collections.Counter()
    for counter in counts.values():
        total.update(counter)
    print('TOTAL', dict(total))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('data_root', type=Path)
    args = parser.parse_args()
    audit(args.data_root)
