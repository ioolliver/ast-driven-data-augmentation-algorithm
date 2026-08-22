import argparse
import importlib.util
import logging
import sys
from pathlib import Path


LOGGER = logging.getLogger(__name__)
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
INPUT_DATASET_PATH = SCRIPT_DIR / "geo_base_dataset.json"
DEFAULT_OUTPUT_DIR = SCRIPT_DIR / "augmentation_method_results"
DEFAULT_MAX_WORKERS = 5
BATCH_MODULE_PATH = SCRIPT_DIR / "apply_augmentation_geo_dataset.py"
SCHEMA_MODULE_PATH = SCRIPT_DIR / "geodataset_schema.py"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from data.augmentation_methods import METHODS, write_augmented_workbook


def load_batch_module():
    spec = importlib.util.spec_from_file_location(
        "geo_dataset_augmentation_batch", BATCH_MODULE_PATH
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_schema():
    spec = importlib.util.spec_from_file_location(
        "geo_dataset_comparison_schema", SCHEMA_MODULE_PATH
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.geo_dataset_schema


def build_method_augmenters(schema):
    from augmentor import (
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


def add_row_ids(dataset_rows, changed_rows):
    return [
        {
            "id": dataset_row["id"],
            "original_question": changed_row["original_question"],
            "original_sql": changed_row["original_sql"],
            "changed_question": changed_row["changed_question"],
            "changed_sql": changed_row["changed_sql"],
            "level": changed_row["level"],
        }
        for dataset_row, changed_row in zip(dataset_rows, changed_rows, strict=True)
    ]


def _output_paths(output_dir, method_key):
    filename = f"geo_dataset_{method_key}_augmented"
    return output_dir / f"{filename}.json", output_dir / f"{filename}.xlsx"


def run_comparison(
    dataset_path=INPUT_DATASET_PATH,
    output_dir=DEFAULT_OUTPUT_DIR,
    schema=None,
    method_augmenters=None,
    max_workers=DEFAULT_MAX_WORKERS,
    skip_paraphrase_only=False,
):
    if max_workers <= 0:
        raise ValueError("max_workers must be greater than zero")

    batch = load_batch_module()
    dataset_rows = batch.load_dataset(dataset_path)
    if method_augmenters is None:
        active_schema = schema if schema is not None else load_schema()
        active_augmenters = build_method_augmenters(active_schema)
    else:
        active_augmenters = method_augmenters

    active_methods = tuple(
        method
        for method in METHODS
        if not (skip_paraphrase_only and method.key == "paraphrase_only")
    )
    missing_methods = [
        method.key for method in active_methods if method.key not in active_augmenters
    ]
    if missing_methods:
        raise ValueError(
            "Missing augmenters for methods: " + ", ".join(missing_methods)
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {}

    if skip_paraphrase_only:
        LOGGER.info("Skipping method: key=paraphrase_only")

    for method in active_methods:
        LOGGER.info(
            "Starting method: key=%s label=%s rows=%d max_workers=%d",
            method.key,
            method.label,
            len(dataset_rows),
            max_workers,
        )
        try:
            _, changed_rows = batch.build_augmented_outputs(
                dataset_rows,
                active_augmenters[method.key],
                max_workers=max_workers,
                progress_callback=batch.log_progress,
            )
        except Exception as exc:
            raise RuntimeError(
                f"Augmentation method {method.key} failed: {exc}"
            ) from exc

        augmented_rows = add_row_ids(dataset_rows, changed_rows)
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
            "Run the three Geo Dataset augmentation methods and write a separate "
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
    parser.add_argument(
        "--skip-paraphrase-only",
        action="store_true",
        help=(
            "Skip the paraphrase-only method and generate only algorithm_only "
            "and algorithm_with_paraphrasing. Existing paraphrase outputs are "
            "left untouched."
        ),
    )
    args = parser.parse_args()
    run_comparison(
        dataset_path=args.input,
        output_dir=args.output_dir,
        max_workers=args.max_workers,
        skip_paraphrase_only=args.skip_paraphrase_only,
    )


if __name__ == "__main__":
    main()
