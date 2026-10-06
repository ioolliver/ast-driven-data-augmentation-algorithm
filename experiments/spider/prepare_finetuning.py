"""Prepare four reproducible Spider 1.0 SFT arms without modifying labels."""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


SYSTEM = "Translate the question into one SQLite SQL query using the provided database schema. Output SQL only."
METHODS = ("paraphrase", "ast", "ast_paraphrase")
ARMS = ("original", *METHODS)


def read_jsonl(path):
    with path.open(encoding="utf-8") as stream:
        for line_no, line in enumerate(stream, 1):
            if line.strip():
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{path}:{line_no}: {exc}") from exc


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def identifier(name):
    return '"' + name.replace('"', '""') + '"'


def schema_text(entry):
    tables = entry["table_names_original"]
    columns = entry["column_names_original"]
    types = entry["column_types"]
    by_table = [[] for _ in tables]
    for index, (table_index, name) in enumerate(columns):
        if table_index >= 0:
            by_table[table_index].append(f"{identifier(name)} {types[index].upper()}")
    lines = [f"CREATE TABLE {identifier(table)} ({', '.join(by_table[i])});"
             for i, table in enumerate(tables)]
    for source, target in entry["foreign_keys"]:
        source_table, source_column = columns[source]
        target_table, target_column = columns[target]
        lines.append(f"FOREIGN KEY {identifier(tables[source_table])}.{identifier(source_column)} "
                     f"REFERENCES {identifier(tables[target_table])}.{identifier(target_column)}")
    return "\n".join(lines)


def example(db_id, question, sql, schemas):
    if db_id not in schemas or not question.strip() or not sql.strip():
        raise ValueError(f"Invalid pair or unknown schema: {db_id}")
    return {
        "prompt": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": f"Database schema:\n{schemas[db_id]}\n\nQuestion: {question}\nSQL:"},
        ],
        "completion": [{"role": "assistant", "content": sql.strip()}],
    }


def write_jsonl(path, rows):
    with path.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")


def prepare(spider_dir, augmentation_dir, output_dir):
    train_path = spider_dir / "train_spider.json"
    dev_path = spider_dir / "dev.json"
    tables_path = spider_dir / "tables.json"
    selected_path = Path(__file__).resolve().parents[2] / "datasets/spider/schemas.json"
    # The custom schemas hold eligibility metadata; only their database IDs are used here.
    selected = set(json.loads(selected_path.read_text(encoding="utf-8")))
    if len(selected) != 20:
        raise ValueError(f"Expected 20 selected databases, got {len(selected)}")
    train = json.loads(train_path.read_text(encoding="utf-8"))
    dev = json.loads(dev_path.read_text(encoding="utf-8"))
    if len(train) != 7000:
        raise ValueError(f"Expected exactly 7000 original Spider train rows, got {len(train)}")
    if not selected <= {row["db_id"] for row in train}:
        raise ValueError("Selected databases are not all in the training set")
    if {row["db_id"] for row in dev} & {row["db_id"] for row in train}:
        raise ValueError("Train and dev database IDs overlap")
    tables = {row["db_id"]: schema_text(row) for row in json.loads(tables_path.read_text(encoding="utf-8"))}
    needed = {row["db_id"] for row in train + dev}
    if not needed <= tables.keys():
        raise ValueError(f"Missing table schemas for {sorted(needed - tables.keys())}")

    original = [example(row["db_id"], row["question"], row["query"], tables) for row in train]
    generated = {}
    for method in METHODS:
        path = augmentation_dir / f"{method}.jsonl"
        rows = {}
        for row in read_jsonl(path):
            index = row["source_index"]
            if not isinstance(index, int) or isinstance(index, bool) or not 0 <= index < len(train):
                raise ValueError(f"{path}: invalid source_index {index!r}")
            source = train[index]
            if row["method"] != method or row["db_id"] != source["db_id"] or row["db_id"] not in selected:
                raise ValueError(f"{path}: method/database mismatch at source_index {index}")
            if row["source_question"] != source["question"] or row["source_sql"] != source["query"]:
                raise ValueError(f"{path}: original pair mismatch at source_index {index}")
            if index in rows:
                raise ValueError(f"{path}: duplicate source_index {index}")
            if method == "paraphrase" and row["query"] != source["query"]:
                raise ValueError(f"{path}: paraphrase changed SQL at source_index {index}")
            rows[index] = example(row["db_id"], row["question"], row["query"], tables)
        generated[method] = rows
    selected_indices = {i for i, row in enumerate(train) if row["db_id"] in selected}
    if set(generated["paraphrase"]) != selected_indices:
        raise ValueError("Paraphrase must cover every original row from the selected databases")
    if set(generated["ast"]) != set(generated["ast_paraphrase"]):
        raise ValueError("AST arms have different source indices")
    for index in generated["ast"]:
        if generated["ast"][index]["completion"] != generated["ast_paraphrase"][index]["completion"]:
            raise ValueError(f"AST SQL differs at source_index {index}")

    output_dir.mkdir(parents=True, exist_ok=True)
    counts = {}
    for arm in ARMS:
        extras = generated.get(arm, {})
        rows = original + [extras[index] for index in sorted(extras)]
        write_jsonl(output_dir / f"train_{arm}.jsonl", rows)
        counts[arm] = {"original": len(original), "augmented": len(extras), "total": len(rows)}
    write_jsonl(output_dir / "dev.jsonl", [
        {"db_id": row["db_id"], "question": row["question"], "query": row["query"],
         "prompt": example(row["db_id"], row["question"], row["query"], tables)["prompt"]}
        for row in dev
    ])
    manifest = {
        "split": "Spider 1.0 train_spider.json; dev.json reserved for evaluation",
        "selected_db_ids": sorted(selected),
        "train_database_count": len({row["db_id"] for row in train}),
        "dev_database_count": len({row["db_id"] for row in dev}),
        "dev_examples": len(dev),
        "counts": counts,
        "augmented_by_database": {method: dict(sorted(Counter(train[i]["db_id"] for i in generated[method]).items())) for method in METHODS},
        "input_sha256": {str(path.name): digest(path) for path in (train_path, dev_path, tables_path, selected_path, *(augmentation_dir / f"{m}.jsonl" for m in METHODS))},
        "output_sha256": {path.name: digest(path) for path in sorted(output_dir.glob("*.jsonl"))},
        "note": "Generated labels were retained without manual curation; SQL executability does not establish question/SQL alignment or nonempty answers.",
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spider_dir", type=Path, help="Extracted Spider 1.0 directory")
    parser.add_argument("augmentation_dir", type=Path, help="Directory with the three generated JSONL files")
    parser.add_argument("output_dir", type=Path, help="Output directory (e.g. raw_data/spider_sft)")
    args = parser.parse_args()
    manifest = prepare(args.spider_dir, args.augmentation_dir, args.output_dir)
    print(json.dumps(manifest["counts"], indent=2))
    print(f"Development: {manifest['dev_examples']} rows; manifest: {args.output_dir / 'manifest.json'}")


if __name__ == "__main__":
    main()
