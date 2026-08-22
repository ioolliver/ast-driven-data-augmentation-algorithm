import argparse
import importlib.util
import logging
import sys
from pathlib import Path
from typing import NamedTuple


LOGGER = logging.getLogger(__name__)
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_RESULTS_DIR = SCRIPT_DIR / "augmentation_method_results"
ANALYZER_PATH = SCRIPT_DIR / "analyze_component_matching.py"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from data.augmentation_methods import METHODS


class AnalysisPaths(NamedTuple):
    input_path: Path
    scores_output_path: Path
    report_output_path: Path


def load_analyzer():
    spec = importlib.util.spec_from_file_location(
        "geo_methods_component_matching_analyzer", ANALYZER_PATH
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def paths_for_method(results_dir, method_key):
    base_name = f"geo_dataset_{method_key}_augmented"
    return AnalysisPaths(
        input_path=results_dir / f"{base_name}.json",
        scores_output_path=results_dir / f"{base_name}_component_matching_scores.json",
        report_output_path=results_dir / f"{base_name}_component_matching.xlsx",
    )


def _validate_inputs(results_dir):
    missing_inputs = [
        (method, paths_for_method(results_dir, method.key).input_path)
        for method in METHODS
        if not paths_for_method(results_dir, method.key).input_path.is_file()
    ]
    if not missing_inputs:
        return

    missing_details = ", ".join(
        f"{method.key}: {input_path}" for method, input_path in missing_inputs
    )
    raise FileNotFoundError(
        "Missing augmented datasets for methods: " + missing_details
    )


def run_all_analyses(results_dir=DEFAULT_RESULTS_DIR, analyzer=None):
    results_dir = Path(results_dir)
    _validate_inputs(results_dir)
    active_analyzer = analyzer if analyzer is not None else load_analyzer()
    outputs = {}

    for method in METHODS:
        paths = paths_for_method(results_dir, method.key)
        LOGGER.info(
            "Starting component matching analysis: method=%s input=%s",
            method.key,
            paths.input_path,
        )
        payload = active_analyzer.run_analysis(
            input_path=paths.input_path,
            scores_output_path=paths.scores_output_path,
            report_output_path=paths.report_output_path,
            dataset_label=f"Geo Dataset - {method.label}",
            sql_dialect=active_analyzer.SQL_DIALECT,
        )
        outputs[method.key] = {"paths": paths, "payload": payload}
        LOGGER.info(
            "Completed component matching analysis: method=%s scores=%s xlsx=%s",
            method.key,
            paths.scores_output_path,
            paths.report_output_path,
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
            "Run component matching analysis for all three Geo Dataset augmentation "
            "methods."
        )
    )
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    args = parser.parse_args()
    run_all_analyses(results_dir=args.results_dir)


if __name__ == "__main__":
    main()
