import json


REQUIRED_ANALYSIS_FIELDS = (
    "original_question",
    "original_sql",
    "changed_question",
    "changed_sql",
    "level",
)


def load_augmented_rows(dataset_path):
    with dataset_path.open(encoding="utf-8") as file_obj:
        payload = json.load(file_obj)

    rows = _extract_rows(payload)
    if not rows:
        raise ValueError("Input dataset must contain at least one row.")

    normalized_rows = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"Row {index} must be a JSON object.")
        normalized_rows.append(_normalize_row(row, index))

    return normalized_rows


def _extract_rows(payload):
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and "queries" in payload:
        rows = payload["queries"]
        if not isinstance(rows, list):
            raise ValueError("Input dataset field queries must be a JSON array.")
        return rows
    raise ValueError("Input dataset must be a JSON array or an object with queries.")


def _normalize_row(row, index):
    if _has_censo_source_fields(row):
        return _normalize_censo_query(row, index)

    for field in REQUIRED_ANALYSIS_FIELDS:
        if field not in row:
            raise ValueError(f"Row {index} is missing required field: {field}")
        if not isinstance(row[field], str):
            raise ValueError(f"Row {index} field {field} must be a string.")
    return dict(row)


def _has_censo_source_fields(row):
    return "pergunta_nl" in row or "sql" in row or "complexidade" in row


def _normalize_censo_query(row, index):
    required_source_fields = ("pergunta_nl", "sql", "complexidade")
    for field in required_source_fields:
        if field not in row:
            raise ValueError(f"Row {index} is missing censo field: {field}")

    for field in ("changed_question", "changed_sql"):
        if field not in row:
            raise ValueError(f"Row {index} is missing augmented censo field: {field}")

    complexity = row["complexidade"]
    if not isinstance(complexity, dict):
        raise ValueError(f"Row {index} field complexidade must be a JSON object.")
    if "nivel" not in complexity:
        raise ValueError(f"Row {index} is missing censo field: complexidade.nivel")

    normalized = {
        "original_question": row["pergunta_nl"],
        "original_sql": row["sql"],
        "changed_question": row["changed_question"],
        "changed_sql": row["changed_sql"],
        "level": complexity["nivel"],
    }
    if "id" in row:
        normalized["id"] = row["id"]

    for field in REQUIRED_ANALYSIS_FIELDS:
        if not isinstance(normalized[field], str):
            raise ValueError(f"Row {index} field {field} must be a string.")

    return normalized
