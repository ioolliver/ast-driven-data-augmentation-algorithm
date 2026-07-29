import argparse
import importlib.util
import logging
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
GEO_ANALYZER_PATH = REPO_ROOT / "data" / "geo_dataset" / "analyze_component_matching.py"
INPUT_DATASET_PATH = SCRIPT_DIR / "censo_escolar_dataset_augmented_only.json"
SCORES_OUTPUT_PATH = SCRIPT_DIR / "censo_escolar_dataset_component_matching_scores.json"
REPORT_OUTPUT_PATH = SCRIPT_DIR / "censo_escolar_dataset_component_matching_report.md"
DATASET_LABEL = "Censo Escolar Dataset"
SQL_DIALECT = "bigquery"


def load_geo_analyzer():
    spec = importlib.util.spec_from_file_location(
        "geo_component_matching_analyzer", GEO_ANALYZER_PATH
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_analysis(
    input_path=INPUT_DATASET_PATH,
    scores_output_path=SCORES_OUTPUT_PATH,
    report_output_path=REPORT_OUTPUT_PATH,
    sql_dialect=SQL_DIALECT,
):
    analyzer = load_geo_analyzer()
    return analyzer.run_analysis(
        input_path=input_path,
        scores_output_path=scores_output_path,
        report_output_path=report_output_path,
        dataset_label=DATASET_LABEL,
        sql_dialect=sql_dialect,
    )


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    parser = argparse.ArgumentParser(
        description=(
            "Score structural SQL component changes between original and augmented "
            "Censo Escolar pairs."
        )
    )
    parser.add_argument("--input", type=Path, default=INPUT_DATASET_PATH)
    parser.add_argument("--scores-output", type=Path, default=SCORES_OUTPUT_PATH)
    parser.add_argument("--report-output", type=Path, default=REPORT_OUTPUT_PATH)
    parser.add_argument("--sql-dialect", default=SQL_DIALECT)
    args = parser.parse_args()
    run_analysis(
        input_path=args.input,
        scores_output_path=args.scores_output,
        report_output_path=args.report_output,
        sql_dialect=args.sql_dialect,
    )


if __name__ == "__main__":
    main()
