import argparse
import json
import logging
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

LOGGER = logging.getLogger(__name__)
SCRIPT_DIR = Path(__file__).resolve().parent
INPUT_DATASET_PATH = SCRIPT_DIR / "geo_dataset_augmented_only.json"
SCORES_OUTPUT_PATH = SCRIPT_DIR / "geo_dataset_component_matching_scores.json"
REPORT_OUTPUT_PATH = SCRIPT_DIR / "geo_dataset_component_matching_report.md"
SQL_DIALECT = "postgres"
SCORE_FORMULA = "changed_component_count / component_total"
REQUIRED_FIELDS = (
    "original_question",
    "original_sql",
    "changed_question",
    "changed_sql",
    "level",
)
BAND_LABELS = tuple(
    [f"[{index / 10:.1f}, {(index + 1) / 10:.1f})" for index in range(9)]
    + ["[0.9, 1.0]"]
)
COMPARISON_OPERATORS = {
    exp.EQ: "=",
    exp.NEQ: "<>",
    exp.GT: ">",
    exp.GTE: ">=",
    exp.LT: "<",
    exp.LTE: "<=",
}
COMPARISON_OPERATOR_TYPES = tuple(COMPARISON_OPERATORS)


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


def _format_number(value):
    return f"{value:.6f}"


def _normalize_sql(node):
    if node is None:
        return ""
    if isinstance(node, exp.Identifier):
        return node.name.lower()
    if isinstance(node, exp.Table):
        return node.name.lower()
    if isinstance(node, exp.Column):
        return node.sql(dialect=SQL_DIALECT, normalize=True).lower()
    if isinstance(node, exp.Literal):
        if node.is_string:
            return str(node.this)
        return str(node.this).lower()
    return node.sql(dialect=SQL_DIALECT, normalize=True).lower()


def _function_name(node):
    if isinstance(node, exp.Anonymous):
        return str(node.this).lower()
    return node.sql_name().lower()


def _function_args(node):
    expressions = list(node.expressions or [])
    for arg_name in ("this", "expression"):
        arg = node.args.get(arg_name)
        if isinstance(arg, exp.Expression):
            expressions.insert(0 if arg_name == "this" else len(expressions), arg)
    return expressions


def _add_component(components, family, key, value):
    components[key] = {
        "family": family,
        "key": key,
        "value": value,
    }


def _flatten_logical_and(node):
    if isinstance(node, exp.And):
        return _flatten_logical_and(node.this) + _flatten_logical_and(node.expression)
    return [node]


def _extract_projection_components(tree, components):
    for index, expression in enumerate(tree.expressions or []):
        if isinstance(expression, exp.AggFunc):
            value = _normalize_sql(expression.this)
        else:
            value = _normalize_sql(expression)
        _add_component(components, "select", f"select:{index}", value)


def _extract_table_components(tree, components):
    from_expression = tree.args.get("from_") or tree.args.get("from")
    if from_expression and from_expression.this:
        _add_component(
            components,
            "table",
            "table:0",
            _normalize_sql(from_expression.this),
        )

    for index, join in enumerate(tree.args.get("joins") or [], start=1):
        _add_component(
            components,
            "table",
            f"table:{index}",
            _normalize_sql(join.this),
        )


def _extract_aggregation_components(tree, components):
    for index, aggregation in enumerate(tree.find_all(exp.AggFunc)):
        _add_component(
            components,
            "aggregation",
            f"aggregation:{index}:function",
            _function_name(aggregation),
        )
        _add_component(
            components,
            "aggregation",
            f"aggregation:{index}:arg",
            _normalize_sql(aggregation.this),
        )


def _extract_function_components(node, components, prefix):
    function_nodes = [
        child
        for child in node.find_all(exp.Func)
        if not isinstance(child, exp.AggFunc)
    ]
    for function_index, function in enumerate(function_nodes):
        base_key = f"{prefix}:function:{function_index}"
        _add_component(
            components,
            "spatial_function",
            f"{base_key}:name",
            _function_name(function),
        )
        for arg_index, arg in enumerate(_function_args(function)):
            _add_component(
                components,
                "spatial_function",
                f"{base_key}:arg:{arg_index}",
                _normalize_sql(arg),
            )


def _extract_predicate_components(predicate, components, prefix):
    if isinstance(predicate, COMPARISON_OPERATOR_TYPES):
        _add_component(
            components,
            "predicate",
            f"{prefix}:left",
            _normalize_sql(predicate.this),
        )
        _add_component(
            components,
            "predicate",
            f"{prefix}:operator",
            COMPARISON_OPERATORS[type(predicate)],
        )
        _add_component(
            components,
            "predicate",
            f"{prefix}:right",
            _normalize_sql(predicate.expression),
        )
    elif isinstance(predicate, exp.Between):
        _add_component(
            components,
            "predicate",
            f"{prefix}:left",
            _normalize_sql(predicate.this),
        )
        _add_component(components, "predicate", f"{prefix}:operator", "BETWEEN")
        _add_component(
            components,
            "predicate",
            f"{prefix}:low",
            _normalize_sql(predicate.args.get("low")),
        )
        _add_component(
            components,
            "predicate",
            f"{prefix}:high",
            _normalize_sql(predicate.args.get("high")),
        )
    elif isinstance(predicate, exp.In):
        _add_component(
            components,
            "predicate",
            f"{prefix}:left",
            _normalize_sql(predicate.this),
        )
        _add_component(components, "predicate", f"{prefix}:operator", "IN")
        values = tuple(_normalize_sql(value) for value in predicate.expressions or [])
        _add_component(components, "predicate", f"{prefix}:values", values)
    elif isinstance(predicate, (exp.Like, exp.ILike)):
        _add_component(
            components,
            "predicate",
            f"{prefix}:left",
            _normalize_sql(predicate.this),
        )
        _add_component(components, "predicate", f"{prefix}:operator", predicate.key.upper())
        _add_component(
            components,
            "predicate",
            f"{prefix}:right",
            _normalize_sql(predicate.expression),
        )
    elif isinstance(predicate, exp.Is):
        _add_component(
            components,
            "predicate",
            f"{prefix}:left",
            _normalize_sql(predicate.this),
        )
        _add_component(components, "predicate", f"{prefix}:operator", "IS")
        _add_component(
            components,
            "predicate",
            f"{prefix}:right",
            _normalize_sql(predicate.expression),
        )
    else:
        _add_component(components, "predicate", f"{prefix}:expression", _normalize_sql(predicate))

    _extract_function_components(predicate, components, prefix)


def _extract_where_components(tree, components):
    where = tree.args.get("where")
    if not where:
        return

    for index, predicate in enumerate(_flatten_logical_and(where.this)):
        _extract_predicate_components(predicate, components, f"where:{index}")


def _extract_join_components(tree, components):
    for join_index, join in enumerate(tree.args.get("joins") or []):
        side = str(join.args.get("side") or "INNER").upper()
        kind = str(join.args.get("kind") or "").upper()
        join_type = " ".join(part for part in (side, kind) if part).strip()
        _add_component(
            components,
            "join",
            f"join:{join_index}:type",
            join_type,
        )
        _add_component(
            components,
            "join",
            f"join:{join_index}:table",
            _normalize_sql(join.this),
        )

        on_expression = join.args.get("on")
        if not on_expression:
            continue
        if isinstance(on_expression, exp.Func):
            _extract_function_components(on_expression, components, f"join:{join_index}")
            continue
        for predicate_index, predicate in enumerate(_flatten_logical_and(on_expression)):
            _extract_predicate_components(
                predicate,
                components,
                f"join:{join_index}:predicate:{predicate_index}",
            )


def _extract_group_components(tree, components):
    group = tree.args.get("group")
    if not group:
        return

    for index, expression in enumerate(group.expressions or []):
        _add_component(
            components,
            "group_by",
            f"group_by:{index}",
            _normalize_sql(expression),
        )


def _extract_order_components(tree, components):
    order = tree.args.get("order")
    if not order:
        return

    for index, ordered in enumerate(order.expressions or []):
        _add_component(
            components,
            "order_by",
            f"order_by:{index}:expression",
            _normalize_sql(ordered.this),
        )
        direction = "DESC" if ordered.args.get("desc") else "ASC"
        _add_component(
            components,
            "order_by",
            f"order_by:{index}:direction",
            direction,
        )


def _extract_limit_components(tree, components):
    limit = tree.args.get("limit")
    if not limit:
        return

    _add_component(
        components,
        "limit",
        "limit:0",
        _normalize_sql(limit.args.get("expression")),
    )


def extract_components(sql):
    tree = sqlglot.parse_one(sql, read=SQL_DIALECT)
    components = {}
    _extract_projection_components(tree, components)
    _extract_table_components(tree, components)
    _extract_aggregation_components(tree, components)
    _extract_join_components(tree, components)
    _extract_where_components(tree, components)
    _extract_group_components(tree, components)
    _extract_order_components(tree, components)
    _extract_limit_components(tree, components)
    return components


def compare_sql_components(original_sql, changed_sql):
    original_components = extract_components(original_sql)
    changed_components = extract_components(changed_sql)
    return _compare_component_maps(original_components, changed_components)


def _extract_row_components(row, index, field):
    try:
        return extract_components(row[field])
    except ParseError as exc:
        raise ValueError(f"Row {index} {field} could not be parsed: {exc}") from exc


def _compare_component_maps(original_components, changed_components):
    all_keys = sorted(set(original_components) | set(changed_components))
    changed = []

    for key in all_keys:
        original = original_components.get(key)
        new = changed_components.get(key)
        original_value = original["value"] if original else None
        new_value = new["value"] if new else None
        if original_value == new_value:
            continue

        component = original or new
        changed.append(
            {
                "family": component["family"],
                "key": key,
                "original": original_value,
                "changed": new_value,
            }
        )

    component_total = len(all_keys)
    changed_count = len(changed)
    score = changed_count / component_total if component_total else 0.0
    return {
        "component_total": component_total,
        "changed_component_count": changed_count,
        "component_matching_score": score,
        "changed_components": changed,
    }


def score_rows(rows):
    scored_rows = []
    for index, row in enumerate(rows):
        original_components = _extract_row_components(row, index, "original_sql")
        changed_components = _extract_row_components(row, index, "changed_sql")
        comparison = _compare_component_maps(original_components, changed_components)

        scored_rows.append({**row, "row_index": index, **comparison})

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


def summarize_scores(scored_rows):
    if not scored_rows:
        raise ValueError("Cannot summarize an empty collection of scored rows.")

    rows_by_level = defaultdict(list)
    for row in scored_rows:
        rows_by_level[row["level"]].append(row)

    scores = [row["component_matching_score"] for row in scored_rows]
    changed_families = Counter(
        component["family"]
        for row in scored_rows
        for component in row["changed_components"]
    )

    return {
        "overall": calculate_distribution(scores),
        "by_level": {
            level: calculate_distribution(
                [row["component_matching_score"] for row in level_rows]
            )
            for level, level_rows in rows_by_level.items()
        },
        "bands": calculate_bands(scores),
        "unchanged_sql": sum(
            row["changed_component_count"] == 0 for row in scored_rows
        ),
        "changed_component_families": dict(changed_families.most_common()),
    }


def _distribution_table(distribution):
    return [
        "| Count | Min | Max | Average | Median | Std Dev | P25 | P75 | P90 | P95 |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        "| {count} | {min} | {max} | {average} | {median} | {std} | {p25} | "
        "{p75} | {p90} | {p95} |".format(
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
        ),
    ]


def _extreme_rows_table(rows):
    lines = [
        "| Row Index | Level | Components | Changed | Score |",
        "| ---: | --- | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| {row_index} | {level} | {total} | {changed} | {score} |".format(
                row_index=row["row_index"],
                level=row["level"],
                total=row["component_total"],
                changed=row["changed_component_count"],
                score=_format_number(row["component_matching_score"]),
            )
        )
    return lines


def build_report(metadata, summary, scored_rows):
    sorted_rows = sorted(
        scored_rows,
        key=lambda row: (row["component_matching_score"], row["row_index"]),
    )
    lowest_rows = sorted_rows[:10]
    highest_rows = list(reversed(sorted_rows[-10:]))
    lines = [
        "# Geo Dataset Component Matching Report",
        "",
        "## Method",
        "",
        f"- Generated at: `{metadata['generated_at']}`",
        f"- Input: `{metadata['input_path']}`",
        f"- Rows analyzed: `{metadata['row_count']}`",
        f"- SQL dialect: `{metadata['sql_dialect']}`",
        f"- Score formula: `{metadata['score_formula']}`",
        "",
        "`component_matching_score` is the share of normalized SQL AST component slots "
        "that changed between the original and augmented SQL.",
        "",
        "## Overall Statistics",
        "",
        *_distribution_table(summary["overall"]),
        "",
        "## Unchanged SQL",
        "",
        f"- Rows with no component changes: `{summary['unchanged_sql']}`",
        "",
        "## Statistics By Level",
        "",
    ]

    for level, distribution in summary["by_level"].items():
        lines.extend([f"### {level}", "", *_distribution_table(distribution), ""])

    lines.extend(
        [
            "## Score Band Distribution",
            "",
            "| Score Band | Rows |",
            "| --- | ---: |",
        ]
    )
    for label in BAND_LABELS:
        lines.append(f"| {label} | {summary['bands'][label]} |")

    lines.extend(
        [
            "",
            "## Most Frequently Changed Component Families",
            "",
            "| Component Family | Changed Count |",
            "| --- | ---: |",
        ]
    )
    for family, count in summary["changed_component_families"].items():
        lines.append(f"| {family} | {count} |")

    if not summary["changed_component_families"]:
        lines.append("| none | 0 |")

    lines.extend(
        [
            "",
            "## Lowest Component Scores",
            "",
            *_extreme_rows_table(lowest_rows),
            "",
            "## Highest Component Scores",
            "",
            *_extreme_rows_table(highest_rows),
            "",
            "## Limitations",
            "",
            "This score is a structural-change heuristic over normalized SQL AST "
            "components. It is interpretable, but it does not prove SQL correctness, "
            "behavioral equivalence, or natural-language alignment.",
            "",
        ]
    )
    return "\n".join(lines)


def run_analysis(
    input_path=INPUT_DATASET_PATH,
    scores_output_path=SCORES_OUTPUT_PATH,
    report_output_path=REPORT_OUTPUT_PATH,
    generated_at=None,
):
    rows = load_rows(input_path)
    scored_rows = score_rows(rows)
    summary = summarize_scores(scored_rows)
    metadata = {
        "generated_at": generated_at
        or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "input_path": str(input_path),
        "row_count": len(rows),
        "sql_dialect": SQL_DIALECT,
        "score_formula": SCORE_FORMULA,
    }
    payload = {"metadata": metadata, "statistics": summary, "rows": scored_rows}
    report = build_report(metadata, summary, scored_rows)

    write_json(scores_output_path, payload)
    report_output_path.write_text(report, encoding="utf-8")
    LOGGER.info(
        "Wrote component matching analysis: rows=%d scores=%s report=%s",
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
        description=(
            "Score structural SQL component changes between original and augmented "
            "geo dataset pairs."
        )
    )
    parser.add_argument("--input", type=Path, default=INPUT_DATASET_PATH)
    parser.add_argument("--scores-output", type=Path, default=SCORES_OUTPUT_PATH)
    parser.add_argument("--report-output", type=Path, default=REPORT_OUTPUT_PATH)
    args = parser.parse_args()
    run_analysis(
        input_path=args.input,
        scores_output_path=args.scores_output,
        report_output_path=args.report_output,
    )


if __name__ == "__main__":
    main()
