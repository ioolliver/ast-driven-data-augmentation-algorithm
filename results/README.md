# Results index

This directory preserves generated question–SQL pairs and intrinsic evaluation
artifacts from the first research iteration.

| Directory | Contents |
|---|---|
| `censobench/` | Temporal-dataset augmented pairs, scores, and reports |
| `atlas_sql_br/` | Geospatial-dataset augmented pairs, scores, and reports |
| `*/augmentation_methods/` | Side-by-side outputs for the three augmentation strategies |

JSON files retain machine-readable pairs and metric summaries. XLSX and Markdown
files are human-readable reports. Filenames were preserved where possible so
published analysis references remain traceable.

The headline results and metric caveats are summarized in the repository README.
See [`docs/reproduction.md`](../docs/reproduction.md) to recompute metrics or
generate a new run. New LLM generations are non-deterministic and should be
written to a separate output directory rather than overwriting these artifacts.
