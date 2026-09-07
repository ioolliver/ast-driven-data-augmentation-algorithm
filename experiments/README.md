# Experiments

These entry points connect dataset-specific formats and schemas to the reusable
`ast_augmentation` package. Run commands from the repository root after `uv sync`.

| Dataset | Generate three strategies | Analyze semantic variation |
|---|---|---|
| CensoBench | `experiments/censobench/compare_methods.py` | `experiments/censobench/analyze_semantic_variation_methods.py` |
| AtlasSQL-BR | `experiments/atlas_sql_br/compare_methods.py` | `experiments/atlas_sql_br/analyze_semantic_variation_methods.py` |

Single-strategy augmentation is available through each dataset's `augment.py`.
AtlasSQL-BR component comparison is orchestrated by
`analyze_component_matching_methods.py`; the CensoBench directory contains a
single-file component analysis wrapper. Use `--help` for input and output options.

By default, generated artifacts are written beneath `results/<dataset>/`. For a
new exploratory run, pass a separate output directory so preserved research
artifacts are not overwritten.
