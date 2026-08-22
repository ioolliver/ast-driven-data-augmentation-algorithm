import argparse
import importlib.util
import logging
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
GEO_ANALYZER_PATH = REPO_ROOT / "data" / "geo_dataset" / "analyze_semantic_variation.py"
INPUT_DATASET_PATH = SCRIPT_DIR / "censo_escolar_dataset_augmented_only.json"
SCORES_OUTPUT_PATH = SCRIPT_DIR / "censo_escolar_dataset_semantic_variation_scores.json"
REPORT_OUTPUT_PATH = SCRIPT_DIR / "censo_escolar_variacao_semantica_analise.xlsx"
DATASET_LABEL = "Censo Escolar Dataset"


def load_geo_analyzer():
    spec = importlib.util.spec_from_file_location(
        "geo_semantic_variation_analyzer", GEO_ANALYZER_PATH
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_analysis(
    input_path=INPUT_DATASET_PATH,
    scores_output_path=SCORES_OUTPUT_PATH,
    report_output_path=REPORT_OUTPUT_PATH,
    model_id=None,
    batch_size=None,
    device=None,
):
    analyzer = load_geo_analyzer()
    return analyzer.run_analysis(
        input_path=input_path,
        scores_output_path=scores_output_path,
        report_output_path=report_output_path,
        model_id=model_id or analyzer.DEFAULT_MODEL_ID,
        batch_size=batch_size or analyzer.DEFAULT_BATCH_SIZE,
        device=device,
        dataset_label=DATASET_LABEL,
    )


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    analyzer = load_geo_analyzer()
    parser = argparse.ArgumentParser(
        description=(
            "Score semantic variation between original and augmented Censo Escolar pairs."
        )
    )
    parser.add_argument("--input", type=Path, default=INPUT_DATASET_PATH)
    parser.add_argument("--scores-output", type=Path, default=SCORES_OUTPUT_PATH)
    parser.add_argument("--report-output", type=Path, default=REPORT_OUTPUT_PATH)
    analyzer.add_model_argument(parser)
    parser.add_argument("--batch-size", type=int, default=analyzer.DEFAULT_BATCH_SIZE)
    parser.add_argument(
        "--device",
        default=None,
        help="SentenceTransformer device such as cuda or cpu; defaults to auto detection.",
    )
    args = parser.parse_args()
    analyzer.run_analysis(
        input_path=args.input,
        scores_output_path=args.scores_output,
        report_output_path=args.report_output,
        model_id=args.model,
        batch_size=args.batch_size,
        device=args.device,
        dataset_label=DATASET_LABEL,
    )


if __name__ == "__main__":
    main()
