import argparse
import importlib.util
import logging
from pathlib import Path


LOGGER = logging.getLogger(__name__)
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
DATASET_DIR = REPO_ROOT / "datasets" / "censobench"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "results" / "censobench" / "augmentation_methods"
INPUT_DATASET_PATH = DATASET_DIR / "original_dataset.json"
DEFAULT_MAX_WORKERS = 5
BATCH_MODULE_PATH = SCRIPT_DIR / "augment.py"
SCHEMA_MODULE_PATH = DATASET_DIR / "schema.py"
from ast_augmentation.evaluation.methods import METHODS, write_augmented_workbook


def load_batch_module():
    spec = importlib.util.spec_from_file_location(
        "censo_escolar_augmentation_batch", BATCH_MODULE_PATH
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_schema():
    spec = importlib.util.spec_from_file_location(
        "censo_escolar_comparison_schema", SCHEMA_MODULE_PATH
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.censo_escolar_schema


def build_method_augmenters(schema):
    from ast_augmentation import (
        create_paraphrase_only_variation,
        create_random_variation,
        create_random_variation_with_paraphrasing,
    )

    def algorithm_only(question, sql):
        return create_random_variation(schema, question, sql)

    def algorithm_with_paraphrasing(question, sql):
        return create_random_variation_with_paraphrasing(schema, question, sql)

    return {
        "paraphrase_only": create_paraphrase_only_variation,
        "algorithm_only": algorithm_only,
        "algorithm_with_paraphrasing": algorithm_with_paraphrasing,
    }


def add_query_ids(queries, changed_rows):
    return [
        {
            "id": query["id"],
            "original_question": changed_row["original_question"],
            "original_sql": changed_row["original_sql"],
            "changed_question": changed_row["changed_question"],
            "changed_sql": changed_row["changed_sql"],
            "level": changed_row["level"],
        }
        for query, changed_row in zip(queries, changed_rows, strict=True)
    ]


def _output_paths(output_dir, method_key):
    filename = f"censo_escolar_{method_key}_augmented"
    return output_dir / f"{filename}.json", output_dir / f"{filename}.xlsx"


def run_comparison(
    dataset_path=INPUT_DATASET_PATH,
    output_dir=DEFAULT_OUTPUT_DIR,
    schema=None,
    method_augmenters=None,
    max_workers=DEFAULT_MAX_WORKERS,
):
    if max_workers <= 0:
        raise ValueError("max_workers must be greater than zero")

    batch = load_batch_module()
    queries = batch.load_queries(dataset_path)
    if method_augmenters is None:
        active_schema = schema if schema is not None else load_schema()
        active_augmenters = build_method_augmenters(active_schema)
    else:
        active_augmenters = method_augmenters

    missing_methods = [
        method.key for method in METHODS if method.key not in active_augmenters
    ]
    if missing_methods:
        raise ValueError(
            "Missing augmenters for methods: " + ", ".join(missing_methods)
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {}

    for method in METHODS:
        augment_pair = active_augmenters[method.key]

        LOGGER.info(
            "Starting method: key=%s label=%s queries=%d max_workers=%d",
            method.key,
            method.label,
            len(queries),
            max_workers,
        )
        try:
            _, changed_rows = batch.build_augmented_outputs(
                queries,
                augment_pair,
                max_workers=max_workers,
                progress_callback=batch.log_progress,
            )
        except Exception as exc:
            raise RuntimeError(
                f"Augmentation method {method.key} failed: {exc}"
            ) from exc

        augmented_rows = add_query_ids(queries, changed_rows)
        json_path, workbook_path = _output_paths(output_dir, method.key)
        batch.write_json(json_path, augmented_rows)
        write_augmented_workbook(workbook_path, augmented_rows)
        outputs[method.key] = (json_path, workbook_path)
        LOGGER.info(
            "Completed method: key=%s augmented_pairs=%d json=%s xlsx=%s",
            method.key,
            len(augmented_rows),
            json_path,
            workbook_path,
        )

    return outputs


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    parser = argparse.ArgumentParser(
        description=(
            "Run the three Censo Escolar augmentation methods and write a separate "
            "JSON and XLSX file for each method."
        )
    )
    parser.add_argument("--input", type=Path, default=INPUT_DATASET_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--max-workers",
        type=int,
        default=DEFAULT_MAX_WORKERS,
        help=(
            "Maximum simultaneous LLM requests within each method "
            f"(default: {DEFAULT_MAX_WORKERS})."
        ),
    )
    args = parser.parse_args()
    run_comparison(
        dataset_path=args.input,
        output_dir=args.output_dir,
        max_workers=args.max_workers,
    )


if __name__ == "__main__":
    main()
