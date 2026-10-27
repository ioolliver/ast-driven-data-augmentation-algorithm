"""Validate predictions and export Spider evaluator inputs in development order."""

import argparse
import json
import re
from pathlib import Path

from predict import sha256
from prepare_finetuning import read_jsonl


def single_line(sql):
    # Evaluators read one SQL statement per line; leave other whitespace untouched.
    return re.sub(r"[\r\n]+", " ", sql).strip()


def export(data_dir, prediction_dir, output_dir):
    dev_path = data_dir / "dev.jsonl"
    manifest = json.loads((data_dir / "manifest.json").read_text(encoding="utf-8"))
    config = json.loads((prediction_dir / "prediction_config.json").read_text(encoding="utf-8"))
    if sha256(dev_path) != manifest["output_sha256"]["dev.jsonl"] or config["dev_sha256"] != sha256(dev_path):
        raise ValueError("Development data differs from preparation/inference")
    dev = list(read_jsonl(dev_path))
    predictions = list(read_jsonl(prediction_dir / "predictions.jsonl"))
    if config["examples"] != manifest["dev_examples"] or len(predictions) != len(dev):
        raise ValueError(f"Full development set required: {len(predictions)}/{len(dev)} predictions")

    gold_lines = []
    predicted_lines = []
    literal_matches = 0
    for index, (row, prediction) in enumerate(zip(dev, predictions)):
        if prediction.get("index") != index or prediction.get("db_id") != row["db_id"]:
            raise ValueError(f"Predictions not aligned at row {index}")
        gold = single_line(row["query"])
        sql = single_line(prediction["prediction"])
        if "\t" in gold or "\t" in sql:
            raise ValueError(f"Tab found in SQL at row {index}")
        gold_lines.append(f"{gold}\t{row['db_id']}\n")
        predicted_lines.append(f"{sql}\n")
        literal_matches += sql == gold

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "gold.txt").write_text("".join(gold_lines), encoding="utf-8")
    (output_dir / "pred.txt").write_text("".join(predicted_lines), encoding="utf-8")
    result = {"arm": config["arm"], "examples": len(dev),
              "literal_sql_match": literal_matches, "literal_sql_match_rate": literal_matches / len(dev),
              "note": "Literal SQL string match is diagnostic; use the official evaluator for Spider exact set match and test-suite accuracy."}
    (output_dir / "literal_match.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    print(f"Spider input files: {output_dir / 'gold.txt'} and {output_dir / 'pred.txt'}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", required=True, type=Path)
    parser.add_argument("--prediction-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    export(args.data_dir, args.prediction_dir, args.output_dir)


if __name__ == "__main__":
    main()
