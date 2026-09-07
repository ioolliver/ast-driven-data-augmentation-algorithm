# Custom schema guide

The augmentation API receives a Python dictionary that describes which SQL
changes are valid for a database. This metadata is intentionally separate from
the database DDL: it records semantic choices, safe value domains, and mutation
bounds that cannot always be inferred from types alone.

## Shape

```python
schema = {
    "tables": [
        {
            "name": "schools",
            "columns": [
                {
                    "name": "state",
                    "description": "Brazilian state code",
                    "type": "enum",
                    "enums": [
                        {"value": "SP", "description": "São Paulo"},
                        {"value": "MG", "description": "Minas Gerais"},
                    ],
                },
                {
                    "name": "enrollment",
                    "description": "Number of enrolled students",
                    "type": "number",
                    "min": 0,
                    "max": 5000,
                    "semantic_group": "school_counts",
                },
            ],
        }
    ]
}
```

Every table needs `name` and `columns`. Every column needs `name`, `description`,
and `type`. The currently used types are `string`, `number`, `date`, `enum`,
`boolean`, and `geometry`.

## Optional metadata

| Field | Used for |
|---|---|
| `min`, `max` | Bounds for numeric and date range changes |
| `enums` | Allowed categorical replacements; entries contain `value` and `description` |
| `value_group` | Group membership on an enum entry |
| `value_group_labels` | Natural-language labels for enum groups |
| `semantic_group` | Candidate columns for semantic column replacement |
| `geometry_type` | Spatial geometry description |
| `distance_min_m`, `distance_max_m` | Bounds for distance predicates |
| `buffer_min_m`, `buffer_max_m` | Bounds for buffer changes |

Only put columns in the same `semantic_group` when substituting one for another
produces a meaningful new question. The term means related alternatives, not SQL
equivalence. Keep enum values in the representation used by the SQL literals.

## Validation checklist

- Match table and column names exactly as parsed from the SQL.
- Use realistic bounds that remain valid for the underlying domain.
- Give every enum value a description suitable for the target language.
- Review spatial units and SRIDs before configuring distance ranges.
- Test representative queries and inspect both the SQL and adapted question.

The research schemas are available in
[`datasets/censobench/schema.py`](../datasets/censobench/schema.py) and
[`datasets/atlas_sql_br/schema.py`](../datasets/atlas_sql_br/schema.py).
