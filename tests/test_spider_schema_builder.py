"""Offline schema profiling contracts using disposable SQLite databases."""
import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "spider_schema_builder", ROOT / "experiments/spider/build_schemas.py"
)
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


class SpiderSchemaBuilderTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.names = ["record_id", "parent_ref", "low", "high", "fractional", "day", "timestamp", "category", "empty", "large_domain"]
        self.types = ["number", "number", "number", "number", "number", "time", "time", "text", "number", "text"]
        self.source = {
            "db_id": "toy", "table_names_original": ["measurements"],
            "table_names": ["measurements"],
            "column_names_original": [[-1, "*"]] + [[0, name] for name in self.names],
            "column_names": [[-1, "*"]] + [[0, name.replace("_", " ")] for name in self.names],
            "column_types": ["text"] + self.types,
            "primary_keys": [1], "foreign_keys": [[2, 1]],
        }
        self.tables = self.root / "tables.json"
        self.tables.write_text(json.dumps([self.source]))
        folder = self.root / "database/toy"
        folder.mkdir(parents=True)
        connection = sqlite3.connect(folder / "toy.sqlite")
        connection.execute("CREATE TABLE measurements(record_id INTEGER, parent_ref INTEGER, low REAL, high INTEGER, fractional REAL, day TEXT, timestamp TEXT, category TEXT, empty REAL, large_domain TEXT)")
        connection.executemany(
            "INSERT INTO measurements VALUES(?,?,?,?,?,?,?,?,?,?)",
            [(i, i + 10, 1.2 if i % 2 else 4.8, 20 + i, 0.2 if i % 2 else 0.8,
              "2020-01-01" if i % 2 else "2021-02-28", "2020-01-01 12:30:00",
              "A" if i % 2 else "B", None, f"label-{i}") for i in range(70)],
        )
        connection.commit()
        connection.close()

    def build(self, **kwargs):
        catalog, report = builder.build_catalog([self.tables], self.root, **kwargs)
        columns = {c["name"]: c for c in catalog["toy"]["tables"][0]["columns"]}
        return catalog, columns, report

    def test_ranges_are_observed_inward_integer_bounds_and_keys_are_protected(self):
        _, columns, report = self.build()
        self.assertEqual((columns["low"]["min"], columns["low"]["max"]), (2, 4))
        self.assertEqual((columns["high"]["min"], columns["high"]["max"]), (20, 89))
        for name in ("record_id", "parent_ref", "fractional", "empty"):
            self.assertEqual(columns[name]["type"], "number")
            self.assertNotIn("min", columns[name])
            self.assertNotIn("max", columns[name])
        self.assertEqual(report["profiled_columns"], len(self.names))
        self.assertTrue(columns["parent_ref"]["provenance"]["key"])

    def test_dates_only_support_valid_iso_days(self):
        _, columns, _ = self.build()
        self.assertEqual(columns["day"]["type"], "date")
        self.assertEqual((columns["day"]["min"], columns["day"]["max"]), ("2020-01-01", "2021-02-28"))
        self.assertEqual(columns["timestamp"]["type"], "string")
        self.assertNotIn("min", columns["timestamp"])
        connection = sqlite3.connect(self.root / "database/toy/toy.sqlite")
        connection.execute("UPDATE measurements SET day='2020-02-31' WHERE record_id=0")
        connection.commit()
        connection.close()
        self.assertEqual(self.build()[1]["day"]["type"], "string")

    def test_enums_contain_only_complete_small_observed_domains(self):
        _, columns, _ = self.build()
        self.assertEqual([e["value"] for e in columns["category"]["enums"]], ["A", "B"])
        self.assertEqual(columns["large_domain"]["type"], "string")
        self.assertNotIn("enums", columns["large_domain"])
        self.assertNotIn("enums", columns["empty"])

    def test_curated_annotations_survive_and_unsafe_values_are_revalidated(self):
        existing = {"toy": {"review_note": "keep this", "tables": [{"name": "measurements", "columns": [
            {"name": "category", "type": "enum", "description": "Reviewed category", "enums": [
                {"value": "A", "description": "Alpha", "value_group": "letters"},
                {"value": "invented", "description": "Never observed"},
            ]},
            {"name": "low", "type": "number", "min": 3, "max": 4, "semantic_group": "measures"},
        ]}]}}
        catalog, columns, _ = self.build(existing=existing)
        self.assertEqual(catalog["toy"]["review_note"], "keep this")
        self.assertEqual(columns["category"]["description"], "Reviewed category")
        self.assertEqual(columns["category"]["enums"][0]["description"], "Alpha")
        self.assertEqual(columns["category"]["enums"][0]["value_group"], "letters")
        self.assertEqual([e["value"] for e in columns["category"]["enums"]], ["A", "B"])
        self.assertEqual(columns["low"]["min"], 3)
        self.assertEqual(columns["low"]["semantic_group"], "measures")
        self.assertEqual(columns["low"]["provenance"]["bounds"], "reviewed_intersection")
        self.assertTrue(columns["category"]["provenance"]["curated"])
        # The input catalog is never mutated by the merge.
        self.assertEqual(existing["toy"]["tables"][0]["columns"][1]["min"], 3)

    def test_missing_database_reports_absence_without_inventing_ranges(self):
        (self.root / "database/toy/toy.sqlite").unlink()
        _, columns, report = self.build()
        self.assertEqual(report["missing_databases"], ["toy"])
        self.assertEqual(report["profiled_columns"], 0)
        self.assertEqual(columns["high"]["type"], "number")
        self.assertNotIn("min", columns["high"])
        self.assertNotIn("enums", columns["category"])
        self.assertFalse(columns["high"]["provenance"]["profiled"])
        self.assertEqual(columns["high"]["provenance"]["source_type"], "number")

    def test_groups_accept_case_insensitive_original_identifiers(self):
        _, columns, report = self.build(groups={"toy": {"MEASUREMENTS": {"measures": ["LOW", "high"]}}})
        self.assertEqual(columns["low"]["semantic_group"], "measures")
        self.assertEqual(columns["high"]["semantic_group"], "measures")
        self.assertEqual(report["semantic_group_columns"], 2)
        self.assertNotIn("semantic_group", columns["fractional"])

    def test_invalid_reviewed_groups_fail_instead_of_silently_skipping(self):
        cases = [
            {"absent": {}},
            {"toy": {"absent": {"g": ["low", "high"]}}},
            {"toy": {"measurements": {"g": ["low"]}}},
            {"toy": {"measurements": {"g": ["low", "absent"]}}},
            {"toy": {"measurements": {"g": ["low", "LOW"]}}},
            {"toy": {"measurements": {"g": ["low", "high"], "h": ["high", "fractional"]}}},
        ]
        for groups in cases:
            with self.subTest(groups=groups), self.assertRaises(ValueError):
                self.build(groups=groups)

    def test_reviewed_database_groups_clear_removed_annotations_only_in_reviewed_db(self):
        catalog, _, _ = self.build()
        catalog["toy"]["tables"][0]["columns"][2]["semantic_group"] = "unsafe"
        untouched = {"tables": [{"name": "t", "columns": [{"name": "c", "semantic_group": "keep"}]}]}
        catalog["unreviewed"] = untouched
        builder.apply_semantic_groups(catalog, {"toy": {}})
        self.assertNotIn("semantic_group", catalog["toy"]["tables"][0]["columns"][2])
        self.assertEqual(untouched["tables"][0]["columns"][0]["semantic_group"], "keep")
        for name in ("record_id", "parent_ref"):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "Key column"):
                self.build(groups={"toy": {"measurements": {"unsafe": [name, "low"]}}})

    def test_value_groups_are_disjoint_reviewed_partitions_of_observed_enums(self):
        annotation = {"toy": {"measurements": {"category": {
            "groups": {"first": ["A"], "second": ["B"]},
            "value_group_labels": {"first": "First category", "second": "Second category"},
        }}}}
        _, columns, _ = self.build(value_groups=annotation)
        self.assertEqual([e["value_group"] for e in columns["category"]["enums"]], ["first", "second"])
        self.assertEqual(columns["category"]["value_group_labels"]["first"], "First category")
        for invalid_members in (["invented"], ["A"]):
            annotation["toy"]["measurements"]["category"]["groups"]["second"] = invalid_members
            with self.subTest(members=invalid_members), self.assertRaisesRegex(ValueError, "Absent/duplicate"):
                self.build(value_groups=annotation)
        annotation["toy"]["measurements"]["category"]["groups"]["second"] = ["B"]
        annotation["toy"]["measurements"]["category"]["value_group_labels"].pop("second")
        with self.assertRaisesRegex(ValueError, "labeled groups"):
            self.build(value_groups=annotation)

    def test_generated_provenance_is_stable_and_observed_bounds_can_expand(self):
        initial, _, _ = self.build()
        rebuilt, _, _ = self.build(existing=initial)
        self.assertEqual(initial, rebuilt)
        self.assertFalse(initial["toy"]["tables"][0]["columns"][2]["provenance"]["curated"])
        connection = sqlite3.connect(self.root / "database/toy/toy.sqlite")
        connection.execute("UPDATE measurements SET low=100 WHERE record_id=0")
        connection.commit()
        connection.close()
        _, columns, _ = self.build(existing=initial)
        self.assertEqual(columns["low"]["max"], 100)
        self.assertEqual(columns["low"]["provenance"]["bounds"], "observed")

    def test_quoted_identifiers_are_data_not_executable_sql(self):
        table = 'odd"; DROP TABLE measurements; --'
        column = 'value"; DROP TABLE measurements; --'
        connection = sqlite3.connect(self.root / "database/toy/toy.sqlite")
        connection.execute(f"CREATE TABLE {builder.quote_identifier(table)} ({builder.quote_identifier(column)} INTEGER)")
        connection.executemany(f"INSERT INTO {builder.quote_identifier(table)} VALUES(?)", [(3,), (8,)])
        self.assertEqual(builder._profile(connection, table, column, "number", False), {"type": "number", "min": 3, "max": 8})
        self.assertEqual(connection.execute("SELECT COUNT(*) FROM measurements").fetchone()[0], 70)
        connection.close()

    def test_duplicate_conflicting_metadata_fails_and_rebuild_is_deterministic(self):
        first = self.build()[0]
        self.assertEqual(first, self.build()[0])
        other = self.root / "other_tables.json"
        changed = dict(self.source, table_names_original=["different"])
        other.write_text(json.dumps([changed]))
        with self.assertRaisesRegex(ValueError, "Conflicting"):
            builder.build_catalog([self.tables, other], self.root)


if __name__ == "__main__":
    unittest.main()
