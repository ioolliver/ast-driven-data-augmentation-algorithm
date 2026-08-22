import json
import tempfile
import unittest
from pathlib import Path


from benchmark.prompting import (
    build_inference_messages,
    build_training_record,
    extract_sql_response,
)
from benchmark.schema import load_schema, render_schema


class BenchmarkPromptingTest(unittest.TestCase):
    def test_loads_and_renders_a_compact_schema(self):
        payload = {
            "tables": [
                {
                    "name": "escola",
                    "columns": [
                        {"name": "id", "type": "number"},
                        {
                            "name": "localizacao",
                            "type": "enum",
                            "enums": [
                                {"value": "1", "description": "Urbana"},
                                {"value": "2", "description": "Rural"},
                            ],
                        },
                    ],
                }
            ]
        }
        with tempfile.TemporaryDirectory() as directory:
            schema_path = Path(directory) / "schema.json"
            schema_path.write_text(json.dumps(payload), encoding="utf-8")

            schema = load_schema(schema_path)
            rendered = render_schema(schema)

        self.assertIn("escola(id:number, localizacao:enum)", rendered)
        self.assertIn("localizacao values: 1=Urbana; 2=Rural", rendered)

    def test_training_and_inference_share_the_same_prompt_contract(self):
        schema_text = "escola(id:number, nome:string)"
        question = "Liste as escolas"

        training = build_training_record(schema_text, question, "SELECT * FROM escola")
        inference = build_inference_messages(schema_text, question)

        self.assertEqual(training["prompt"], inference)
        self.assertEqual(
            training["completion"],
            [{"role": "assistant", "content": "SELECT * FROM escola"}],
        )
        self.assertIn(schema_text, inference[1]["content"])

    def test_extracts_only_sql_from_non_thinking_or_fenced_output(self):
        response = "<think>internal</think>\n```sql\nSELECT 1;\n```"

        self.assertEqual(extract_sql_response(response), "SELECT 1;")

    def test_committed_schema_snapshots_match_current_source_columns(self):
        import importlib.util

        cases = (
            (
                "data/geo_dataset/geodataset_schema.py",
                "geo_dataset_schema",
                "benchmark/schemas/geo.json",
            ),
            (
                "data/censo_escolar_dataset/schema.py",
                "censo_escolar_schema",
                "benchmark/schemas/censo_escolar.json",
            ),
        )
        repository_root = Path(__file__).resolve().parents[1]
        for source_name, variable_name, snapshot_name in cases:
            source_path = repository_root / source_name
            spec = importlib.util.spec_from_file_location(source_path.stem, source_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            source_schema = getattr(module, variable_name)
            snapshot = load_schema(repository_root / snapshot_name)

            source_columns = {
                table["name"]: [column["name"] for column in table["columns"]]
                for table in source_schema["tables"]
            }
            snapshot_columns = {
                table["name"]: [column["name"] for column in table["columns"]]
                for table in snapshot["tables"]
            }
            self.assertEqual(snapshot_columns, source_columns)


if __name__ == "__main__":
    unittest.main()
