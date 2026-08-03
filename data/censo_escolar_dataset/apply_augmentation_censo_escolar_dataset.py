import argparse
import importlib.util
import json
import logging
import sys
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from pathlib import Path


LOGGER = logging.getLogger(__name__)
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
INPUT_DATASET_PATH = SCRIPT_DIR / "original_dataset.json"
MIXED_OUTPUT_PATH = SCRIPT_DIR / "censo_escolar_dataset_augmented.json"
CHANGED_ONLY_OUTPUT_PATH = SCRIPT_DIR / "censo_escolar_dataset_augmented_only.json"
SCHEMA_MODULE_PATH = SCRIPT_DIR / "schema.py"
DEFAULT_MAX_WORKERS = 5


def load_queries(dataset_path):
    with dataset_path.open(encoding="utf-8") as file_obj:
        payload = json.load(file_obj)

    if not isinstance(payload, dict):
        raise ValueError("Input dataset must be a JSON object.")

    queries = payload.get("queries")
    if not isinstance(queries, list):
        raise ValueError("Input dataset field queries must be a JSON array.")
    if not queries:
        raise ValueError("Input dataset must contain at least one query.")

    for index, query in enumerate(queries):
        _validate_query(query, index)

    return queries


def _validate_query(query, index):
    if not isinstance(query, dict):
        raise ValueError(f"Query at index {index} must be a JSON object.")

    for field in ("id", "pergunta_nl", "sql", "complexidade"):
        if field not in query:
            raise ValueError(
                f"Query at index {index} is missing required field: {field}"
            )

    if not isinstance(query["pergunta_nl"], str):
        raise ValueError(
            f"Query at index {index} field pergunta_nl must be a string."
        )
    if not isinstance(query["sql"], str):
        raise ValueError(f"Query at index {index} field sql must be a string.")

    complexity = query["complexidade"]
    if not isinstance(complexity, dict):
        raise ValueError(
            f"Query at index {index} field complexidade must be a JSON object."
        )
    if "nivel" not in complexity:
        raise ValueError(
            f"Query at index {index} is missing required field: complexidade.nivel"
        )
    if not isinstance(complexity["nivel"], str):
        raise ValueError(
            f"Query at index {index} field complexidade.nivel must be a string."
        )


def write_json(output_path, payload):
    with output_path.open("w", encoding="utf-8") as file_obj:
        json.dump(payload, file_obj, ensure_ascii=False, indent=2)
        file_obj.write("\n")


def augment_query(query, augment_pair):
    query_identifier = f"id={query['id']}"
    question = query["pergunta_nl"]
    sql = query["sql"]
    level = query["complexidade"]["nivel"]

    try:
        changed_question, changed_sql = augment_pair(question, sql)
    except Exception as exc:
        raise RuntimeError(
            f"Failed to augment query {query_identifier}: {exc}"
        ) from exc

    return (
        {
            "question": question,
            "level": level,
            "sql_code": sql,
            "augmented": False,
        },
        {
            "question": changed_question,
            "level": level,
            "sql_code": changed_sql,
            "augmented": True,
        },
        {
            "original_question": question,
            "original_sql": sql,
            "changed_question": changed_question,
            "changed_sql": changed_sql,
            "level": level,
        },
    )


def log_progress(completed_count, succeeded_count, failed_count, total_count):
    completion_percentage = (
        (completed_count / total_count) * 100 if total_count else 100.0
    )
    LOGGER.info(
        "Progress: completed=%d/%d (%.1f%%) succeeded=%d failed=%d",
        completed_count,
        total_count,
        completion_percentage,
        succeeded_count,
        failed_count,
    )


def augment_queries(queries, augment_pair, max_workers, progress_callback=None):
    if max_workers <= 0:
        raise ValueError("max_workers must be greater than zero")

    total_count = len(queries)
    completed_count = 0
    succeeded_count = 0
    failed_count = 0
    results = [None] * total_count
    next_index = 0
    executor = ThreadPoolExecutor(max_workers=max_workers)
    in_flight = {}

    def submit_next_query():
        nonlocal next_index
        if next_index >= total_count:
            return False
        future = executor.submit(augment_query, queries[next_index], augment_pair)
        in_flight[future] = next_index
        next_index += 1
        return True

    try:
        for _ in range(min(max_workers, total_count)):
            submit_next_query()

        while in_flight:
            completed, _ = wait(in_flight, return_when=FIRST_COMPLETED)
            for future in completed:
                index = in_flight.pop(future)
                try:
                    results[index] = future.result()
                except Exception:
                    completed_count += 1
                    failed_count += 1
                    if progress_callback:
                        progress_callback(
                            completed_count,
                            succeeded_count,
                            failed_count,
                            total_count,
                        )
                    raise
                completed_count += 1
                succeeded_count += 1
                if progress_callback:
                    progress_callback(
                        completed_count,
                        succeeded_count,
                        failed_count,
                        total_count,
                    )
            for _ in completed:
                submit_next_query()
    except Exception:
        for future in in_flight:
            future.cancel()
        executor.shutdown(wait=True, cancel_futures=True)
        raise
    else:
        executor.shutdown(wait=True)

    return results


def build_augmented_outputs(
    queries,
    augment_pair,
    max_workers=DEFAULT_MAX_WORKERS,
    progress_callback=None,
):
    mixed_rows = []
    changed_rows = []

    for original_row, augmented_row, changed_row in augment_queries(
        queries,
        augment_pair,
        max_workers=max_workers,
        progress_callback=progress_callback,
    ):
        mixed_rows.extend([original_row, augmented_row])
        changed_rows.append(changed_row)

    return mixed_rows, changed_rows


def load_schema():
    spec = importlib.util.spec_from_file_location(
        "censo_escolar_schema_module", SCHEMA_MODULE_PATH
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.censo_escolar_schema


def build_augmenter(schema):
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))

    from augmentor import create_random_variation

    def augment_pair(question, sql):
        return create_random_variation(schema, question, sql)

    return augment_pair


def run_batch(
    dataset_path=INPUT_DATASET_PATH,
    mixed_output_path=MIXED_OUTPUT_PATH,
    changed_only_output_path=CHANGED_ONLY_OUTPUT_PATH,
    schema=None,
    augment_pair=None,
    max_workers=DEFAULT_MAX_WORKERS,
):
    queries = load_queries(dataset_path)
    LOGGER.info(
        "Starting augmentation batch: queries=%d max_workers=%d input=%s",
        len(queries),
        max_workers,
        dataset_path,
    )
    active_schema = schema if schema is not None else load_schema()
    active_augment_pair = (
        augment_pair if augment_pair is not None else build_augmenter(active_schema)
    )

    try:
        mixed_rows, changed_rows = build_augmented_outputs(
            queries,
            active_augment_pair,
            max_workers=max_workers,
            progress_callback=log_progress,
        )
    except Exception:
        LOGGER.exception("Augmentation batch stopped after a failed query.")
        raise

    write_json(mixed_output_path, mixed_rows)
    write_json(changed_only_output_path, changed_rows)
    LOGGER.info(
        "Wrote augmentation outputs: augmented_pairs=%d mixed_output=%s changed_output=%s",
        len(changed_rows),
        mixed_output_path,
        changed_only_output_path,
    )

    return mixed_rows, changed_rows


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    parser = argparse.ArgumentParser(
        description="Apply one augmentation to each Censo Escolar dataset query."
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=DEFAULT_MAX_WORKERS,
        help=(
            "Maximum simultaneous augmentation requests "
            f"(default: {DEFAULT_MAX_WORKERS})."
        ),
    )
    args = parser.parse_args()
    run_batch(max_workers=args.max_workers)


if __name__ == "__main__":
    main()
