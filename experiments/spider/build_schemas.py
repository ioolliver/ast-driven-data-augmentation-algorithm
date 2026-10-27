"""Build Spider custom schemas from original metadata and observed SQLite values.

No benchmark rows or database files are copied into the output. Semantic groups
are reviewed inputs, never inferred from shared SQL types. Rebuild in place to
retain the descriptions and annotations of the existing curated catalog.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import date
import json
import math
from pathlib import Path
import re
import sqlite3


REPO_ROOT = Path(__file__).resolve().parents[2]
MAX_ENUM_VALUES = 64
MAX_ENUM_LENGTH = 120


def quote_identifier(name):
    return '"' + name.replace('"', '""') + '"'


def _key_indices(source):
    keys = set(source.get("primary_keys", []))
    for pair in source.get("foreign_keys", []):
        keys.update(pair)
    return keys


def _is_identifier(name):
    """Also protect identifiers missing a declared Spider key constraint."""
    return bool(re.search(r"(?:^|_)id$|^id_|_ids$", name, re.IGNORECASE)) or name.casefold() == "id"


def _database_path(data_root, db_id):
    for path in (
        data_root / "database" / db_id / f"{db_id}.sqlite",
        data_root / db_id / f"{db_id}.sqlite",
        data_root / f"{db_id}.sqlite",
    ):
        if path.is_file():
            return path
    return None


def _base_type(source_type):
    return {"number": "number", "boolean": "boolean"}.get(source_type, "string")


def _profile(connection, table, column, source_type, key):
    """Only return mutation metadata supported by actual non-null values.

    Numeric mutations currently sample integer thresholds, so bounds are rounded
    inward. Empty/fraction-only intervals intentionally have no range. Dates
    require an exact ISO day: timestamp truncation would change literal semantics.
    """
    result = {"type": _base_type(source_type)}
    if key:
        return result
    sql = f"SELECT DISTINCT {quote_identifier(column)} FROM {quote_identifier(table)} WHERE {quote_identifier(column)} IS NOT NULL"
    cursor = connection.execute(sql)
    if source_type == "number":
        low, high, count = None, None, 0
        for (value,) in cursor:
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                return result
            low = value if low is None else min(low, value)
            high = value if high is None else max(high, value)
            count += 1
        if count and math.ceil(low) <= math.floor(high):
            result.update(min=math.ceil(low), max=math.floor(high))
        return result
    # Fetch at most one value beyond the enum cap. Larger domains must not be
    # mistaken for a complete enumeration, nor scanned into a large output file.
    values = [row[0] for row in cursor.fetchmany(MAX_ENUM_VALUES + 1)]
    if not values:
        return result
    if source_type == "time":
        if len(values) > MAX_ENUM_VALUES:
            # Date ranges need a full scan even for high-cardinality columns.
            values.extend(row[0] for row in cursor)
        if all(isinstance(v, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", v) for v in values):
            try:
                parsed = [date.fromisoformat(v) for v in values]
            except ValueError:
                return result
            return {"type": "date", "min": min(parsed).isoformat(), "max": max(parsed).isoformat()}
        return result
    if source_type not in ("text", "others") or not 2 <= len(values) <= MAX_ENUM_VALUES:
        return result
    if not all(isinstance(v, str) and v.strip() and len(v) <= MAX_ENUM_LENGTH for v in values):
        return result
    result.update(type="enum", enums=[{"value": v, "description": v} for v in sorted(values)])
    return result


def _load_sources(table_paths):
    sources = {}
    for path in table_paths:
        for source in json.loads(Path(path).read_text(encoding="utf-8")):
            db_id = source["db_id"]
            if db_id in sources and source != sources[db_id]:
                raise ValueError(f"Conflicting Spider metadata for {db_id}")
            sources[db_id] = source
    return sources


def _merge_observations(column, observed):
    bounds_origin = "observed" if "min" in observed else None
    # Reviewed bounds may deliberately exclude implausible source outliers.
    # Keep their intersection with observed support rather than expanding them.
    reviewed_bounds = "provenance" not in column or column.get("provenance", {}).get("bounds") == "reviewed_intersection"
    if reviewed_bounds and column.get("type") == observed.get("type") and all(k in column and k in observed for k in ("min", "max")):
        try:
            old_low, old_high = column["min"], column["max"]
            if observed["type"] == "number":
                valid = all(isinstance(v, (int, float)) and math.isfinite(v) for v in (old_low, old_high))
                if valid:
                    old_low, old_high = math.ceil(old_low), math.floor(old_high)
            else:
                valid = all(isinstance(v, str) and date.fromisoformat(v).isoformat() == v for v in (old_low, old_high))
            if valid:
                lower, upper = max(old_low, observed["min"]), min(old_high, observed["max"])
                if lower <= upper:
                    observed = dict(observed, min=lower, max=upper)
                    bounds_origin = "reviewed_intersection"
        except (TypeError, ValueError, OverflowError):
            pass
    # Existing enum descriptions/value groups survive when the value is real.
    old_options = {e["value"]: e for e in column.get("enums", [])}
    for field in ("type", "min", "max", "enums"):
        column.pop(field, None)
    column.update(observed)
    if "enums" in observed:
        column["enums"] = [deepcopy(old_options.get(e["value"], e)) for e in observed["enums"]]
    return bounds_origin


def apply_semantic_groups(catalog, groups):
    """Validate reviewed, table-local groups before adding any annotations."""
    assignments = []
    for db_id, tables in groups.items():
        if db_id not in catalog:
            raise ValueError(f"Semantic group database is absent: {db_id}")
        available = {t["name"].casefold(): t for t in catalog[db_id]["tables"]}
        for table_name, table_groups in tables.items():
            table = available.get(table_name.casefold())
            if table is None:
                raise ValueError(f"Semantic group table is absent: {db_id}.{table_name}")
            columns = {c["name"].casefold(): c for c in table["columns"]}
            seen = set()
            for group_name, members in table_groups.items():
                if not isinstance(group_name, str) or not group_name or not isinstance(members, list) or len(members) < 2:
                    raise ValueError(f"Group must have a name and at least two columns: {db_id}.{table_name}.{group_name}")
                for member in members:
                    column = columns.get(member.casefold())
                    if column is None or member.casefold() in seen:
                        raise ValueError(f"Absent/duplicate semantic group column: {db_id}.{table_name}.{member}")
                    if column.get("provenance", {}).get("key"):
                        raise ValueError(f"Key column cannot enter semantic group: {db_id}.{table_name}.{member}")
                    seen.add(member.casefold())
                    assignments.append((column, group_name))
    # A reviewed database entry is authoritative, including an empty mapping.
    # Do this only after every supplied group passes validation.
    for db_id in groups:
        for table in catalog[db_id]["tables"]:
            for column in table["columns"]:
                column.pop("semantic_group", None)
    for column, group_name in assignments:
        column["semantic_group"] = group_name


def apply_value_groups(catalog, metadata):
    """Apply reviewed partitions of observed enums without inventing values."""
    assignments = []
    for db_id, tables in metadata.items():
        if db_id not in catalog:
            raise ValueError(f"Value group database is absent: {db_id}")
        available = {t["name"].casefold(): t for t in catalog[db_id]["tables"]}
        for table_name, columns in tables.items():
            table = available.get(table_name.casefold())
            if table is None:
                raise ValueError(f"Value group table is absent: {db_id}.{table_name}")
            available_columns = {c["name"].casefold(): c for c in table["columns"]}
            for column_name, annotation in columns.items():
                column = available_columns.get(column_name.casefold())
                location = f"{db_id}.{table_name}.{column_name}"
                if column is None or column.get("type") != "enum" or column.get("provenance", {}).get("key") or not column.get("provenance", {}).get("profiled"):
                    raise ValueError(f"Value groups require a non-key observed enum: {location}")
                groups = annotation.get("groups", {})
                labels = annotation.get("value_group_labels", {})
                if len(groups) < 2 or set(labels) != set(groups) or not all(isinstance(v, str) and v.strip() for v in labels.values()):
                    raise ValueError(f"Value groups require at least two labeled groups: {location}")
                values = {e["value"] for e in column["enums"]}
                seen = set()
                for name, members in groups.items():
                    if not isinstance(name, str) or not name or not isinstance(members, list) or not members:
                        raise ValueError(f"Value group must have a name and values: {location}")
                    for value in members:
                        if value not in values or value in seen:
                            raise ValueError(f"Absent/duplicate value group member: {location}: {value!r}")
                        seen.add(value)
                assignments.append((column, groups, labels))
    for column, groups, labels in assignments:
        for option in column["enums"]:
            option.pop("value_group", None)
        for name, members in groups.items():
            for option in column["enums"]:
                if option["value"] in members:
                    option["value_group"] = name
        column["value_group_labels"] = deepcopy(labels)


def build_catalog(table_paths, data_root, existing=None, groups=None, *, value_groups=None):
    """Return deterministic catalog and a machine-readable provenance report."""
    sources = _load_sources(table_paths)
    existing = existing or {}
    catalog = {}
    report = {"databases": len(sources), "missing_databases": [], "profile_errors": [], "columns": 0, "profiled_columns": 0}
    for db_id, source in sorted(sources.items()):
        old = existing.get(db_id, {})
        schema = {k: deepcopy(v) for k, v in old.items() if k != "tables"}
        schema.update(dialect="sqlite", language="English", case_insensitive_identifiers=True, sqlite_double_quoted_literals=True, restrict_aggregates=True, coverage_fallbacks=True)
        schema["provenance"] = {"metadata": "Spider tables.json", "profile": "SQLite observed non-null values"}
        schema["tables"] = []
        old_tables = {t["name"].casefold(): t for t in old.get("tables", [])}
        keys = _key_indices(source)
        path = _database_path(Path(data_root), db_id)
        connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True) if path else None
        if connection is None:
            report["missing_databases"].append(db_id)
        try:
            for table_index, table_name in enumerate(source["table_names_original"]):
                previous = old_tables.get(table_name.casefold(), {})
                table = {k: deepcopy(v) for k, v in previous.items() if k != "columns"}
                table.update(name=table_name, description=previous.get("description", source.get("table_names", source["table_names_original"])[table_index]), columns=[])
                old_columns = {c["name"].casefold(): c for c in previous.get("columns", [])}
                for index, (owner, name) in enumerate(source["column_names_original"]):
                    if owner != table_index:
                        continue
                    report["columns"] += 1
                    source_type = source["column_types"][index]
                    key = index in keys or _is_identifier(name)
                    column = deepcopy(old_columns.get(name.casefold(), {}))
                    column.update(name=name, description=column.get("description", source.get("column_names", source["column_names_original"])[index][1]))
                    provenance = {"metadata": "Spider tables.json", "source_type": source_type, "column_index": index, "key": key, "profiled": False, "curated": column.get("provenance", {}).get("curated", bool(column.get("type")))}
                    if connection is not None:
                        try:
                            bounds_origin = _merge_observations(column, _profile(connection, table_name, name, source_type, key))
                            if bounds_origin:
                                provenance["bounds"] = bounds_origin
                            provenance["profiled"] = True
                            report["profiled_columns"] += 1
                        except sqlite3.Error as exc:
                            report["profile_errors"].append({"db_id": db_id, "table": table_name, "column": name, "error": str(exc)})
                            _merge_observations(column, {"type": _base_type(source_type)})
                    elif not column.get("type"):
                        column["type"] = _base_type(source_type)
                    if key:
                        column.pop("min", None)
                        column.pop("max", None)
                        column.pop("enums", None)
                        column["type"] = _base_type(source_type)
                    column["provenance"] = provenance
                    table["columns"].append(column)
                schema["tables"].append(table)
        finally:
            if connection is not None:
                connection.close()
        catalog[db_id] = schema
    apply_semantic_groups(catalog, groups or {})
    apply_value_groups(catalog, value_groups or {})
    report["semantic_group_columns"] = sum("semantic_group" in c for s in catalog.values() for t in s["tables"] for c in t["columns"])
    return catalog, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data_root", type=Path)
    parser.add_argument("--tables", type=Path, action="append", help="Spider tables.json files (repeat for test_tables.json)")
    parser.add_argument("--output", type=Path, default=REPO_ROOT / "datasets/spider/schemas.json")
    parser.add_argument("--groups", type=Path, default=REPO_ROOT / "datasets/spider/semantic_groups.json")
    parser.add_argument("--value-groups", type=Path, default=REPO_ROOT / "datasets/spider/value_groups.json")
    parser.add_argument("--report", type=Path, help="Optional JSON profiling report")
    args = parser.parse_args()
    table_paths = args.tables or [args.data_root / "tables.json"]
    existing = json.loads(args.output.read_text(encoding="utf-8")) if args.output.exists() else {}
    if not args.groups.is_file():
        parser.error(f"Semantic groups file does not exist: {args.groups}")
    groups = json.loads(args.groups.read_text(encoding="utf-8"))
    value_groups = json.loads(args.value_groups.read_text(encoding="utf-8")) if args.value_groups.is_file() else {}
    catalog, report = build_catalog(table_paths, args.data_root, existing, groups, value_groups=value_groups)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(catalog, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
