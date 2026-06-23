import argparse
import json
import logging
from collections import defaultdict
from datetime import datetime, timezone
from importlib import metadata as importlib_metadata
from pathlib import Path

import numpy as np

LOGGER = logging.getLogger(__name__)
SCRIPT_DIR = Path(__file__).resolve().parent
INPUT_DATASET_PATH = SCRIPT_DIR / "geo_dataset_augmented_only.json"
SCORES_OUTPUT_PATH = SCRIPT_DIR / "geo_dataset_semantic_variation_scores.json"
REPORT_OUTPUT_PATH = SCRIPT_DIR / "geo_dataset_semantic_variation_report.md"
DEFAULT_MODEL_ID = "jinaai/jina-embeddings-v3"
DEFAULT_BATCH_SIZE = 16
EMBEDDING_TASK = "text-matching"
MODEL_LICENSE = "CC BY-NC 4.0"
SCORE_FORMULA = "clip(1 - cosine_similarity(original, changed), 0, 1)"
REQUIRED_FIELDS = (
    "original_question",
    "original_sql",
    "changed_question",
    "changed_sql",
    "level",
)
COMPARISONS = (
    ("sql", "sql_variation_score"),
    ("question", "question_variation_score"),
    ("combined", "combined_variation_score"),
)
BAND_LABELS = tuple(
    [f"[{index / 10:.1f}, {(index + 1) / 10:.1f})" for index in range(9)]
    + ["[0.9, 1.0]"]
)


def load_rows(dataset_path):
    with dataset_path.open(encoding="utf-8") as file_obj:
        rows = json.load(file_obj)

    if not isinstance(rows, list):
        raise ValueError("Input dataset must be a JSON array.")
    if not rows:
        raise ValueError("Input dataset must contain at least one row.")

    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"Row {index} must be a JSON object.")
        for field in REQUIRED_FIELDS:
            if field not in row:
                raise ValueError(f"Row {index} is missing required field: {field}")
            if not isinstance(row[field], str):
                raise ValueError(f"Row {index} field {field} must be a string.")

    return rows


def write_json(output_path, payload):
    with output_path.open("w", encoding="utf-8") as file_obj:
        json.dump(payload, file_obj, ensure_ascii=False, indent=2)
        file_obj.write("\n")


def validate_embedding_runtime(model_id):
    if model_id != DEFAULT_MODEL_ID:
        return

    try:
        transformers_version = importlib_metadata.version("transformers")
    except importlib_metadata.PackageNotFoundError:
        return

    if int(transformers_version.split(".", 1)[0]) >= 5:
        raise RuntimeError(
            f"{DEFAULT_MODEL_ID} is not compatible with the installed transformers "
            f"{transformers_version} runtime. Install "
            '"sentence-transformers==3.1.0" "transformers==4.57.6" einops "numpy<2". '
            "Restart the runtime before running the analysis again."
        )


def load_embedder(model_id, device=None):
    validate_embedding_runtime(model_id)
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError(
            "Semantic variation analysis requires sentence-transformers and einops. "
            'Install a Jina-compatible stack with: pip install "sentence-transformers==3.1.0" '
            '"transformers==4.57.6" einops "numpy<2".'
        ) from exc

    model_kwargs = {"trust_remote_code": True}
    if device:
        model_kwargs["device"] = device
    return SentenceTransformer(model_id, **model_kwargs)


def cosine_similarities(first_vectors, second_vectors):
    first = np.asarray(first_vectors, dtype=np.float64)
    second = np.asarray(second_vectors, dtype=np.float64)
    if first.shape != second.shape:
        raise ValueError("Embedding matrices must have matching dimensions.")
    if first.ndim != 2:
        raise ValueError("Embedding matrices must be two-dimensional.")

    first_norms = np.linalg.norm(first, axis=1)
    second_norms = np.linalg.norm(second, axis=1)
    if np.any(first_norms == 0) or np.any(second_norms == 0):
        raise ValueError("Embedding vectors cannot have zero magnitude.")

    dot_products = np.sum(first * second, axis=1)
    similarities = dot_products / (first_norms * second_norms)
    return np.clip(similarities, -1.0, 1.0)


def variation_scores(similarities):
    return np.clip(1.0 - similarities, 0.0, 1.0)


def _encode_field(rows, field, embedder, batch_size):
    return embedder.encode(
        [row[field] for row in rows],
        batch_size=batch_size,
        task=EMBEDDING_TASK,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=True,
    )


def score_rows(rows, embedder, batch_size=DEFAULT_BATCH_SIZE):
    embeddings = {
        field: _encode_field(rows, field, embedder, batch_size)
        for field in (
            "original_sql",
            "changed_sql",
            "original_question",
            "changed_question",
        )
    }
    sql_similarities = cosine_similarities(
        embeddings["original_sql"], embeddings["changed_sql"]
    )
    question_similarities = cosine_similarities(
        embeddings["original_question"], embeddings["changed_question"]
    )
    sql_scores = variation_scores(sql_similarities)
    question_scores = variation_scores(question_similarities)
    combined_scores = (sql_scores + question_scores) / 2
    scored_rows = []

    for index, row in enumerate(rows):
        scored_rows.append(
            {
                **row,
                "row_index": index,
                "sql_similarity": float(sql_similarities[index]),
                "sql_variation_score": float(sql_scores[index]),
                "question_similarity": float(question_similarities[index]),
                "question_variation_score": float(question_scores[index]),
                "combined_variation_score": float(combined_scores[index]),
            }
        )

    return scored_rows


def calculate_distribution(values):
    score_values = np.asarray(values, dtype=np.float64)
    if score_values.size == 0:
        raise ValueError("Cannot calculate statistics for an empty score collection.")

    return {
        "count": int(score_values.size),
        "min": float(np.min(score_values)),
        "max": float(np.max(score_values)),
        "average": float(np.mean(score_values)),
        "median": float(np.median(score_values)),
        "standard_deviation": float(np.std(score_values)),
        "p25": float(np.percentile(score_values, 25)),
        "p75": float(np.percentile(score_values, 75)),
        "p90": float(np.percentile(score_values, 90)),
        "p95": float(np.percentile(score_values, 95)),
    }


def calculate_bands(values):
    bands = {label: 0 for label in BAND_LABELS}
    for value in values:
        band_index = min(int(value * 10), 9)
        bands[BAND_LABELS[band_index]] += 1
    return bands


def _distributions_for_rows(scored_rows):
    return {
        comparison: calculate_distribution([row[field] for row in scored_rows])
        for comparison, field in COMPARISONS
    }


def summarize_scores(scored_rows):
    if not scored_rows:
        raise ValueError("Cannot summarize an empty collection of scored rows.")

    rows_by_level = defaultdict(list)
    for row in scored_rows:
        rows_by_level[row["level"]].append(row)

    return {
        "overall": _distributions_for_rows(scored_rows),
        "by_level": {
            level: _distributions_for_rows(level_rows)
            for level, level_rows in rows_by_level.items()
        },
        "unchanged_text": {
            "sql": sum(
                row["original_sql"] == row["changed_sql"] for row in scored_rows
            ),
            "question": sum(
                row["original_question"] == row["changed_question"]
                for row in scored_rows
            ),
        },
        "bands": {
            comparison: calculate_bands([row[field] for row in scored_rows])
            for comparison, field in COMPARISONS
        },
    }


def _format_number(value):
    return f"{value:.6f}"


def _distribution_table(distributions):
    lines = [
        "| Comparison | Count | Min | Max | Average | Median | Std Dev | P25 | P75 | P90 | P95 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for comparison, _ in COMPARISONS:
        distribution = distributions[comparison]
        lines.append(
            "| {name} | {count} | {min} | {max} | {average} | {median} | "
            "{std} | {p25} | {p75} | {p90} | {p95} |".format(
                name=comparison.title(),
                count=distribution["count"],
                min=_format_number(distribution["min"]),
                max=_format_number(distribution["max"]),
                average=_format_number(distribution["average"]),
                median=_format_number(distribution["median"]),
                std=_format_number(distribution["standard_deviation"]),
                p25=_format_number(distribution["p25"]),
                p75=_format_number(distribution["p75"]),
                p90=_format_number(distribution["p90"]),
                p95=_format_number(distribution["p95"]),
            )
        )
    return lines


def _extreme_rows_table(rows):
    lines = [
        "| Row Index | Level | SQL Score | Question Score | Combined Score |",
        "| ---: | --- | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| {row_index} | {level} | {sql} | {question} | {combined} |".format(
                row_index=row["row_index"],
                level=row["level"],
                sql=_format_number(row["sql_variation_score"]),
                question=_format_number(row["question_variation_score"]),
                combined=_format_number(row["combined_variation_score"]),
            )
        )
    return lines


def build_report(metadata, summary, scored_rows):
    sorted_rows = sorted(
        scored_rows, key=lambda row: (row["combined_variation_score"], row["row_index"])
    )
    lowest_rows = sorted_rows[:10]
    highest_rows = list(reversed(sorted_rows[-10:]))
    lines = [
        "# Geo Dataset Semantic Variation Report",
        "",
        "## Method",
        "",
        f"- Generated at: `{metadata['generated_at']}`",
        f"- Input: `{metadata['input_path']}`",
        f"- Rows analyzed: `{metadata['row_count']}`",
        f"- Embedding model: `{metadata['model_id']}`",
        f"- Embedding task: `{metadata['embedding_task']}`",
        f"- Score formula: `{metadata['score_formula']}`",
        f"- Model license: `{metadata['model_license']}` (non-commercial use).",
        "",
        "A score of `0` represents no detected semantic variation in embedding space; "
        "a score of `1` represents maximum variation under the clipped cosine metric.",
        "",
        "## Overall Statistics",
        "",
        *_distribution_table(summary["overall"]),
        "",
        "## Unchanged Text",
        "",
        "| Comparison | Exact Unchanged Rows |",
        "| --- | ---: |",
        f"| SQL | {summary['unchanged_text']['sql']} |",
        f"| Question | {summary['unchanged_text']['question']} |",
        "",
        "## Statistics By Level",
        "",
    ]

    for level, distributions in summary["by_level"].items():
        lines.extend([f"### {level}", "", *_distribution_table(distributions), ""])

    lines.extend(
        [
            "## Score Band Distribution",
            "",
            "| Score Band | SQL | Question | Combined |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for label in BAND_LABELS:
        lines.append(
            f"| {label} | {summary['bands']['sql'][label]} | "
            f"{summary['bands']['question'][label]} | "
            f"{summary['bands']['combined'][label]} |"
        )

    lines.extend(
        [
            "",
            "## Lowest Combined Scores",
            "",
            *_extreme_rows_table(lowest_rows),
            "",
            "## Highest Combined Scores",
            "",
            *_extreme_rows_table(highest_rows),
            "",
            "## Limitations",
            "",
            "This score is an embedding-based heuristic for variation strength. It does "
            "not prove SQL behavioral equivalence or difference: a change to an operator, "
            "literal, join, or spatial predicate can be logically decisive even when the "
            "embedding distance is small.",
            "",
        ]
    )
    return "\n".join(lines)


def run_analysis(
    input_path=INPUT_DATASET_PATH,
    scores_output_path=SCORES_OUTPUT_PATH,
    report_output_path=REPORT_OUTPUT_PATH,
    model_id=DEFAULT_MODEL_ID,
    batch_size=DEFAULT_BATCH_SIZE,
    device=None,
    embedder=None,
    generated_at=None,
):
    if batch_size <= 0:
        raise ValueError("batch_size must be greater than zero.")
    rows = load_rows(input_path)
    active_embedder = embedder or load_embedder(model_id, device=device)
    scored_rows = score_rows(rows, active_embedder, batch_size=batch_size)
    summary = summarize_scores(scored_rows)
    metadata = {
        "generated_at": generated_at
        or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "input_path": str(input_path),
        "row_count": len(rows),
        "model_id": model_id,
        "embedding_task": EMBEDDING_TASK,
        "score_formula": SCORE_FORMULA,
        "model_license": MODEL_LICENSE,
        "requested_device": device or "auto",
        "batch_size": batch_size,
    }
    payload = {"metadata": metadata, "statistics": summary, "rows": scored_rows}
    report = build_report(metadata, summary, scored_rows)

    write_json(scores_output_path, payload)
    report_output_path.write_text(report, encoding="utf-8")
    LOGGER.info(
        "Wrote semantic variation analysis: rows=%d scores=%s report=%s",
        len(rows),
        scores_output_path,
        report_output_path,
    )
    return payload


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    parser = argparse.ArgumentParser(
        description="Score semantic variation between original and augmented geo pairs."
    )
    parser.add_argument("--input", type=Path, default=INPUT_DATASET_PATH)
    parser.add_argument("--scores-output", type=Path, default=SCORES_OUTPUT_PATH)
    parser.add_argument("--report-output", type=Path, default=REPORT_OUTPUT_PATH)
    parser.add_argument("--model", default=DEFAULT_MODEL_ID)
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument(
        "--device",
        default=None,
        help="SentenceTransformer device such as cuda or cpu; defaults to auto detection.",
    )
    args = parser.parse_args()
    run_analysis(
        input_path=args.input,
        scores_output_path=args.scores_output,
        report_output_path=args.report_output,
        model_id=args.model,
        batch_size=args.batch_size,
        device=args.device,
    )


if __name__ == "__main__":
    main()
