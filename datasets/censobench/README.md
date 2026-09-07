# CensoBench temporal dataset

This directory contains the temporal Text-to-SQL input used in the final
intrinsic evaluation.

| Path | Role |
|---|---|
| `original_dataset.json` | 107 original Portuguese question–SQL pairs |
| `schema.py` | Augmentation metadata derived for the experiment |
| `raw_schema/` | Source table-schema descriptions used during preparation |

The pairs cover Brazilian School Census questions at four difficulty levels: 46
easy, 30 medium, 8 hard, and 23 very hard. The JSON uses a top-level `queries`
array with `pergunta_nl`, `sql`, and `complexidade` fields.

Generated pairs and evaluation reports live under
[`results/censobench/`](../../results/censobench/). The repository's MIT license
applies to the original project code; it does not relicense source data.
