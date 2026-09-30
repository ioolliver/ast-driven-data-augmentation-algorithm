"""Generate Spider training augmentations; never reads dev or test examples."""
import argparse
import json
import random
import sqlite3
from pathlib import Path

from ast_augmentation.augmentor import _create_sql_variation
from ast_augmentation.llm import adapt_query, paraphrase_query

SCHEMAS = json.loads((Path(__file__).parents[2] / 'datasets/spider/schemas.json').read_text())
METHODS = ('paraphrase', 'ast', 'ast_paraphrase')


def prepare_rows(data_root, limit=None):
    originals = json.loads((data_root / 'train_spider.json').read_text(encoding='utf-8'))
    selected = [(index, row) for index, row in enumerate(originals) if row['db_id'] in SCHEMAS]
    return selected[:limit] if limit is not None else selected


def sqlite_valid(data_root, db_id, sql):
    database = data_root / 'database' / db_id / f'{db_id}.sqlite'
    if not database.is_file():
        raise FileNotFoundError(database)
    with sqlite3.connect(f'file:{database.resolve()}?mode=ro', uri=True) as connection:
        try:
            connection.execute('EXPLAIN QUERY PLAN ' + sql).fetchall()
        except sqlite3.Error:
            return False
    return True


def generate(data_root, output_dir, methods=METHODS, limit=None, seed=42):
    selected = prepare_rows(data_root, limit)
    if not selected:
        raise ValueError('No selected training examples found')
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {method: output_dir / f'{method}.jsonl' for method in methods}
    for path in paths.values():
        if path.exists() or path.with_suffix('.jsonl.tmp').exists():
            raise FileExistsError(f'Use a fresh output directory: {path}')
    random.seed(seed)
    # One AST change per original is shared by both AST arms.
    ast_rows = {}
    if any(method in methods for method in ('ast', 'ast_paraphrase')):
        for index, row in selected:
            schema = SCHEMAS[row['db_id']]
            sql, changelog = _create_sql_variation(schema, row['query'])
            if changelog and sqlite_valid(data_root, row['db_id'], sql):
                ast_rows[index] = (sql, changelog)
    for method, path in paths.items():
        tmp = path.with_suffix('.jsonl.tmp')
        with tmp.open('x', encoding='utf-8') as stream:
            for index, row in selected:
                question, sql, db = row['question'], row['query'], row['db_id']
                if method == 'paraphrase':
                    new_question = paraphrase_query(question, language='English')
                    new_sql = sql
                else:
                    if index not in ast_rows:
                        continue
                    new_sql, changelog = ast_rows[index]
                    new_question = adapt_query(
                        question, sql, new_sql, changelog,
                        paraphrase=(method == 'ast_paraphrase'), language='English',
                    )
                stream.write(json.dumps({
                    'source_index': index, 'db_id': db, 'method': method,
                    'source_question': question, 'source_sql': sql,
                    'question': new_question, 'query': new_sql,
                }, ensure_ascii=False) + '\n')
        tmp.rename(path)
        print(f'{method}: {path}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('data_root', type=Path, help='Extracted spider_data directory')
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--methods', nargs='+', choices=METHODS, default=list(METHODS))
    parser.add_argument('--limit', type=int, help='Run a small prefix of selected training examples')
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()
    if args.limit is not None and args.limit <= 0:
        parser.error('--limit must be positive')
    generate(args.data_root, args.output_dir, tuple(dict.fromkeys(args.methods)), args.limit, args.seed)


if __name__ == '__main__':
    main()
