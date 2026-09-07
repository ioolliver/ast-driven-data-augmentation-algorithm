# AtlasSQL-BR geospatial dataset

This directory contains the prepared geospatial Text-to-SQL input used in the
final intrinsic evaluation.

| Path | Role |
|---|---|
| `original_dataset.json` | Original imported dataset representation |
| `cleared_dataset.json` | Cleaned intermediate representation |
| `geo_base_dataset.json` | 980 prepared source pairs used by the experiments |
| `schema.py` | SQL and PostGIS augmentation metadata |

The prepared set contains 245 Portuguese question–SQL pairs at each of four
difficulty levels. Rows use `question`, `sql_code`, `level`, and provenance
fields. See the [AtlasSQL-BR dataset page](https://huggingface.co/datasets/datafromlopes/atlas-sql-br)
for the upstream dataset.

Generated pairs and evaluation reports live under
[`results/atlas_sql_br/`](../../results/atlas_sql_br/). Acknowledgment and license
requirements from the upstream dataset remain applicable.
