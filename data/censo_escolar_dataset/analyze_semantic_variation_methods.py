import argparse
import importlib.util
import logging
from pathlib import Path
from typing import NamedTuple


LOGGER = logging.getLogger(__name__)
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_RESULTS_DIR = SCRIPT_DIR / "augmentation_method_results"
GEO_ANALYZER_PATH = (
    REPO_ROOT / "data" / "geo_dataset" / "analyze_semantic_variation.py"
)


class MethodConfig(NamedTuple):
    key: str
    label: str


class AnalysisPaths(NamedTuple):
    input_path: Path
    scores_output_path: Path
    report_output_path: Path


METHODS = (
    MethodConfig("paraphrase_only", "Question paraphrasing only"),
    MethodConfig("algorithm_only", "AST algorithm augmentation only"),
    MethodConfig(
        "algorithm_with_paraphrasing",
        "AST algorithm augmentation with question paraphrasing",
    ),
)


def load_analyzer():
    spec = importlib.util.spec_from_file_location(
        "censo_methods_semantic_variation_analyzer", GEO_ANALYZER_PATH
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def paths_for_method(results_dir, method_key):
    base_name = f"censo_escolar_{method_key}_augmented"
    return AnalysisPaths(
        input_path=results_dir / f"{base_name}.json",
        scores_output_path=(
            results_dir / f"{base_name}_semantic_variation_scores.json"
        ),
        report_output_path=(
            results_dir / f"{base_name}_semantic_variation.xlsx"
        ),
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
        f"{method.key}: {input_path}"
        for method, input_path in missing_inputs
    )
    raise FileNotFoundError(
        "Missing augmented datasets for methods: " + missing_details
    )


def run_all_analyses(
    results_dir=DEFAULT_RESULTS_DIR,
    model_id=None,
    batch_size=None,
    device=None,
    analyzer=None,
):
    results_dir = Path(results_dir)
    _validate_inputs(results_dir)

    active_analyzer = analyzer if analyzer is not None else load_analyzer()
    active_model_id = model_id or active_analyzer.DEFAULT_MODEL_ID
    active_batch_size = (
        active_analyzer.DEFAULT_BATCH_SIZE if batch_size is None else batch_size
    )
    if active_batch_size <= 0:
        raise ValueError("batch_size must be greater than zero")

    LOGGER.info(
        "Loading semantic variation model once for all methods: model=%s device=%s",
        active_model_id,
        device or "auto",
    )
    embedder = active_analyzer.load_embedder(active_model_id, device=device)
    outputs = {}

    for method in METHODS:
        paths = paths_for_method(results_dir, method.key)
        LOGGER.info(
            "Starting semantic variation analysis: method=%s input=%s",
            method.key,
            paths.input_path,
        )
        payload = active_analyzer.run_analysis(
            input_path=paths.input_path,
            scores_output_path=paths.scores_output_path,
            report_output_path=paths.report_output_path,
            model_id=active_model_id,
            batch_size=active_batch_size,
            device=device,
            embedder=embedder,
            dataset_label=f"Censo Escolar Dataset - {method.label}",
        )
        outputs[method.key] = {
            "paths": paths,
            "payload": payload,
        }
        LOGGER.info(
            "Completed semantic variation analysis: method=%s scores=%s xlsx=%s",
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
    analyzer = load_analyzer()
    parser = argparse.ArgumentParser(
        description=(
            "Run semantic variation analysis for all three Censo Escolar "
            "augmentation methods with one shared embedding model."
        )
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=DEFAULT_RESULTS_DIR,
        help="Directory containing the three augmented JSON files.",
    )
    analyzer.add_model_argument(parser)
    parser.add_argument("--batch-size", type=int, default=None)
    parser.add_argument(
        "--device",
        default=None,
        help="SentenceTransformer device such as cuda or cpu; defaults to auto detection.",
    )
    args = parser.parse_args()
    run_all_analyses(
        results_dir=args.results_dir,
        model_id=args.model,
        batch_size=args.batch_size,
        device=args.device,
        analyzer=analyzer,
    )


if __name__ == "__main__":
    main()
