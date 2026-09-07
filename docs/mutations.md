# Transformations

The pipeline first applies semantic mutations, records each semantic change, and
then applies guarded equivalent rewrites. A transformation is probabilistic and
only runs when its AST shape and schema requirements match.

## Semantic mutation families

| Family | Implementation | Main requirement |
|---|---|---|
| Binary value | `mutations/binary.py` | Equality predicate with a supported binary value |
| Enum equality | `mutations/enum_eq.py` | Enum column and another configured value |
| Aggregate function | `mutations/agg.py` | Supported `SUM`, `AVG`, `MIN`, or `MAX` expression |
| Threshold shift | `mutations/threshold_shift.py` | Numeric/date comparison with configured bounds |
| BETWEEN range | `mutations/between.py` | Literal interval and compatible column metadata |
| Equivalent column | `mutations/equivalent_column.py` | Another column in the same `semantic_group` |
| Value group | `mutations/value_group.py` | Configured enum groups used by an `IN` predicate |
| Text pattern | `mutations/text_pattern.py` | Supported `LIKE` or `ILIKE` pattern |
| PostGIS | `mutations/postgis.py` | Supported spatial AST and geometry metadata |

These operations intentionally change the requested information. Their changelog
entries are supplied to the LLM so it can update the natural-language question.

## Equivalent rewrites

| Rewrite | Implementation | Guarded form |
|---|---|---|
| `BETWEEN` to comparisons | `rewrites/between_comparisons.py` | Simple literal bounds |
| `DISTINCT` to `GROUP BY` | `rewrites/distinct_group_by.py` | Simple projections without conflicting clauses |
| `INNER JOIN` to `IN` subquery | `rewrites/join_in_subquery.py` | Conservative single-join shape using primary-table projections |

Equivalent rewrites do not enter the semantic changelog. They are conservative
syntactic alternatives, not general-purpose SQL equivalence proofs. The tests
include execution checks for their supported shapes, including duplicate and
`NULL` cases.

Mutation order is defined in `src/ast_augmentation/augmentor.py`: semantic column
replacement runs first, other semantic operators run second, and equivalent
rewrites run last.
