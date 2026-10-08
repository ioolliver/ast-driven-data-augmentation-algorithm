"""Generate Spider training augmentations; never reads dev or test examples."""
import argparse
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
import json
import os
import random
import sqlite3
import time
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


def _existing_rows(path, method, expected):
    """Read completed/checkpoint rows and reject incompatible runs."""
    if not path.exists():
        return {}
    existing = {}
    with path.open(encoding='utf-8') as stream:
        for line_number, line in enumerate(stream, 1):
            try:
                result = json.loads(line)
                index = result['source_index']
            except (ValueError, KeyError, TypeError) as exc:
                raise ValueError(f'{path}:{line_number}: invalid JSONL; repair this line before resuming') from exc
            if type(index) is not int or index not in expected or index in existing:
                raise ValueError(f'{path}:{line_number}: unexpected or duplicate source_index {index!r}')
            row, ast_sql = expected[index]
            if (
                result.get('method') != method
                or result.get('db_id') != row['db_id']
                or result.get('source_question') != row['question']
                or result.get('source_sql') != row['query']
                or result.get('query') != (row['query'] if method == 'paraphrase' else ast_sql)
                or not isinstance(result.get('question'), str)
                or not result['question'].strip()
            ):
                raise ValueError(f'{path}:{line_number}: does not match this dataset, method or AST seed')
            existing[index] = result
    return existing


def _discard_incomplete_tail(path):
    """A terminated write may leave an unfinished final JSONL line."""
    if not path.exists():
        return
    with path.open('rb+') as stream:
        stream.seek(0, 2)
        size = stream.tell()
        if not size:
            return
        stream.seek(-1, 2)
        if stream.read(1) == b'\n':
            return
        stream.seek(0)
        content = stream.read()
        last_complete = content.rfind(b'\n') + 1
        stream.truncate(last_complete)
        print(f'Removed incomplete trailing line from {path}', flush=True)


def _generate_one(method, index, row, ast_rows):
    question, sql, db = row['question'], row['query'], row['db_id']
    if method == 'paraphrase':
        new_question = paraphrase_query(question, language='English')
        new_sql = sql
    else:
        new_sql, changelog = ast_rows[index]
        new_question = adapt_query(
            question, sql, new_sql, changelog,
            paraphrase=(method == 'ast_paraphrase'), language='English',
        )
    if not isinstance(new_question, str) or not new_question.strip():
        raise ValueError('LLM returned an empty question')
    return {
        'source_index': index, 'db_id': db, 'method': method,
        'source_question': question, 'source_sql': sql,
        'question': new_question, 'query': new_sql,
    }


def _run_method(method, path, selected, ast_rows, max_workers, progress_every):
    tmp = path.with_suffix('.jsonl.tmp')
    eligible = [(i, row) for i, row in selected if method == 'paraphrase' or i in ast_rows]
    expected = {i: (row, ast_rows[i][0] if i in ast_rows else None) for i, row in eligible}
    if path.exists() and tmp.exists():
        # A crash just after the final atomic rename can leave the checkpoint.
        if len(_existing_rows(path, method, expected)) == len(eligible):
            tmp.unlink()
        else:
            raise FileExistsError(f'Both {path} and {tmp} exist; keep only the intended checkpoint')
    checkpoint = path if path.exists() else tmp
    if checkpoint == tmp:
        _discard_incomplete_tail(tmp)
    existing = _existing_rows(checkpoint, method, expected)
    total = len(eligible)
    if len(existing) == total and path.exists():
        print(f'{method}: already complete ({total}/{total}); skipping {path}', flush=True)
        return
    if path.exists():
        path.rename(tmp)
    pending = [(i, row) for i, row in eligible if i not in existing]
    print(f'{method}: {len(existing)}/{total} complete; {len(pending)} LLM calls, '
          f'{max_workers} worker(s)', flush=True)

    completed = len(existing)
    started = time.monotonic()
    with tmp.open('a', encoding='utf-8') as stream:
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            iterator = iter(pending)
            active = {}

            def submit_next():
                try:
                    index, row = next(iterator)
                except StopIteration:
                    return False
                future = pool.submit(_generate_one, method, index, row, ast_rows)
                active[future] = index
                return True

            for _ in range(min(max_workers * 2, len(pending))):
                submit_next()
            while active:
                done, _ = wait(active, return_when=FIRST_COMPLETED)
                for future in done:
                    index = active.pop(future)
                    try:
                        result = future.result()
                    except Exception as exc:
                        for remaining in active:
                            remaining.cancel()
                        raise RuntimeError(f'{method}: source_index {index} failed; '
                                           f'rerun with the same output directory to resume') from exc
                    stream.write(json.dumps(result, ensure_ascii=False) + '\n')
                    stream.flush()
                    completed += 1
                    if completed % progress_every == 0 or completed == total:
                        elapsed = time.monotonic() - started
                        rate = (completed - len(existing)) / max(elapsed, 0.001)
                        remaining = (total - completed) / rate if rate else 0
                        print(f'{method}: {completed}/{total} ({completed / total:.1%}); '
                              f'{rate:.2f} rows/s; ETA {remaining / 60:.1f} min', flush=True)
                    submit_next()

    # Checkpoints can finish out of order. Final files follow source order.
    final_rows = _existing_rows(tmp, method, expected)
    if len(final_rows) != total:
        raise ValueError(f'{method}: expected {total} rows but checkpoint has {len(final_rows)}')
    staging = path.with_suffix('.jsonl.finalizing')
    with staging.open('w', encoding='utf-8') as stream:
        for index, _ in eligible:
            stream.write(json.dumps(final_rows[index], ensure_ascii=False) + '\n')
    os.replace(staging, path)
    tmp.unlink()
    print(f'{method}: complete -> {path}', flush=True)


def generate(data_root, output_dir, methods=METHODS, limit=None, seed=42,
             max_workers=1, progress_every=25):
    if max_workers < 1 or progress_every < 1:
        raise ValueError('max_workers and progress_every must be positive')
    selected = prepare_rows(data_root, limit)
    if not selected:
        raise ValueError('No selected training examples found')
    output_dir.mkdir(parents=True, exist_ok=True)
    random.seed(seed)
    # One AST change per original is shared by both AST arms.
    ast_rows = {}
    if any(method in methods for method in ('ast', 'ast_paraphrase')):
        print(f'Preparing AST changes for {len(selected)} training rows...', flush=True)
        for index, row in selected:
            schema = SCHEMAS[row['db_id']]
            sql, changelog = _create_sql_variation(schema, row['query'])
            if changelog and sqlite_valid(data_root, row['db_id'], sql):
                ast_rows[index] = (sql, changelog)
        print(f'AST preparation: {len(ast_rows)} eligible rows', flush=True)
    for method in methods:
        _run_method(method, output_dir / f'{method}.jsonl', selected, ast_rows,
                    max_workers, progress_every)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('data_root', type=Path, help='Extracted spider_data directory')
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--methods', nargs='+', choices=METHODS, default=list(METHODS))
    parser.add_argument('--limit', type=int, help='Run a small prefix of selected training examples')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--max-workers', type=int, default=1,
                        help='Concurrent LLM requests (default: 1; use 1 for local inference)')
    parser.add_argument('--progress-every', type=int, default=25,
                        help='Print a progress line after this many completed examples')
    args = parser.parse_args()
    if args.limit is not None and args.limit <= 0:
        parser.error('--limit must be positive')
    if args.max_workers <= 0 or args.progress_every <= 0:
        parser.error('--max-workers and --progress-every must be positive')
    generate(args.data_root, args.output_dir, tuple(dict.fromkeys(args.methods)),
             args.limit, args.seed, args.max_workers, args.progress_every)


if __name__ == '__main__':
    main()
