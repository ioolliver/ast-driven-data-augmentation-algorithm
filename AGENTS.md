# CLAUDE.md

This file provides guidance to Codex when working with code in this repository.

## Project Overview

This is an **AST-driven SQL data augmentation tool** that generates semantic variations of SQL queries and their natural language descriptions. The tool uses SQL Abstract Syntax Tree (AST) transformations combined with LLM-based query adaptation to create training data for machine learning models.

**Key purpose:** Given an original SQL query + natural language description + schema, generate controlled semantic variations with different SQL and adapted natural language descriptions. Mutations should intentionally change the query semantics programmatically, while the LLM layer updates the natural language query to match the modified SQL.

## Folder Structure

```
.
├── main.py                        # Entry point: schema data, test queries, run loop
├── augmentor.py                   # Orchestrator: create_random_variation
├── llm.py                         # LLM layer: prompting, Bedrock call, format_changelog
├── local-llm.py                   # Optional local Hugging Face LLM runner for Colab/GPU
├── data/
│   └── geo_dataset/
│       ├── geo_base_dataset.json   # 980 base_dataset rows processed by the batch
│       ├── geodataset_schema.py   # Schema dedicated to the geospatial dataset batch
│       └── apply_augmentation_geo_dataset.py  # Bounded-concurrency batch writer
├── schema_utils.py                # Schema helpers: get_col_info, get_table_name
├── mutations/
│   ├── __init__.py                # Re-exports all mutate_* functions
│   ├── between.py                 # mutate_between — BETWEEN range randomization
│   ├── enum_eq.py                 # mutate_enum — enum equality value swap
│   ├── agg.py                     # mutate_agg — aggregate function swap (SUM/AVG/MIN/MAX)
│   ├── threshold_shift.py         # mutate_threshold_shift — inequality operator + value shift
│   ├── equivalent_column.py       # mutate_equivalent_column — semantic group column swap
│   ├── value_group.py             # mutate_value_group — IN clause value group swap
│   ├── binary.py                  # mutate_binary — binary column value flip (0 ↔ 1)
│   ├── text_pattern.py            # mutate_text_pattern — LIKE/ILIKE pattern-shape mutation
│   └── postgis.py                 # PostGIS function and distance-threshold mutations
├── pyproject.toml
├── uv.lock
├── .python-version
├── .env.example
├── .gitignore
├── CLAUDE.md
└── README.md
```

## Architecture

### Core Components

1. **Mutations** (`mutations/`)
   - Each file is a single-responsibility mutation function
   - `between.py`: Randomizes BETWEEN clause bounds within schema min/max
   - `enum_eq.py`: Swaps enum equality value for another available enum
   - `agg.py`: Swaps aggregate function (SUM ↔ AVG ↔ MIN ↔ MAX)
   - `threshold_shift.py`: Randomizes inequality threshold and operator
   - `equivalent_column.py`: Replaces a column with a peer from the same semantic group
   - `value_group.py`: Swaps an IN clause's value group (e.g. Norte → Sudeste)
   - `binary.py`: Flips a binary column value (0 → 1 or 1 → 0)
   - `text_pattern.py`: Mutates simple `LIKE`/`ILIKE` pattern shape among exact, starts-with, ends-with, and contains semantics without schema metadata
   - `postgis.py`: Mutates PostGIS functions such as `ST_Buffer`, `ST_DWithin`, direct `ST_Distance(...)` thresholds, `ST_Intersection`, and strict `ST_Intersects(ST_Buffer(...), ST_Buffer(...))` patterns
   - Each mutation appends changes to a `changelog` list for LLM context

2. **Schema Utilities** (`schema_utils.py`)
   - `get_col_info`: Resolves column metadata from schema by table + column name
   - `get_table_name`: Extracts real table name from an AST column node, resolving aliases

3. **LLM Layer** (`llm.py`)
   - `format_changelog`: Formats changelog list into readable diff string
   - `get_llm_prompt`: Builds the full prompt with original/modified SQL and changelog
   - `send_to_llm`: Calls Amazon Bedrock OpenAI-compatible Chat Completions using `OPENAI_API_KEY` and `OPENAI_BASE_URL`, or delegates to local mode when `LOCAL_LLM=true`
   - `local-llm.py`: Exposes `send_to_local_llm(prompt)` for Hugging Face text-generation models such as Qwen 3.5 4B in Google Colab/T4
   - `adapt_query`: Composes the above to return an adapted natural language query

4. **Orchestrator** (`augmentor.py`)
   - `create_random_variation`: Parses SQL → two-pass AST transform → adapted query
   - Pass 1: column swaps (`mutate_equivalent_column`) so subsequent mutations see updated columns
   - Pass 2: all remaining mutations applied together
   - Maintains a per-query `mutation_state` dictionary so repeated PostGIS radii/distances are changed consistently across a query
   - Returns the original natural-language query without an LLM call when no mutation adds an entry to `changelog`

5. **Entry Point** (`main.py`)
   - Holds hardcoded schema definition and test queries
   - Loops over query pairs, calls `create_random_variation`, prints results

6. **Geo Dataset Batch Script** (`data/geo_dataset/apply_augmentation_geo_dataset.py`)
   - Loads `data/geo_dataset/geo_base_dataset.json`, restricted to `source == "base_dataset"`
   - Applies `create_random_variation` once per dataset row with at most five concurrent requests by default
   - Logs completed, succeeded, and failed request counts as each remote call finishes
   - Writes a mixed original+augmented dataset and an augmented-only change mapping

### Data Flow

```
Input: schema + query_text + sql
  ↓
Parse SQL → AST
  ↓
Transform AST (apply mutations) → collect changelog
  ↓
Generate modified SQL from AST
  ↓
If changelog is empty: preserve query_text without an LLM call
Otherwise: LLM adapts query_text based on changelog
  ↓
Output: (adapted_query, modified_sql)
```

Batch dataset flow:

```
Input dataset JSON
  ↓
For each row: call create_random_variation(schema, question, sql_code) once
with bounded concurrent requests while retaining input order
  ↓
Write geo_dataset_augmented.json
  ↓
Write geo_dataset_augmented_only.json
```

### Schema Format

Schema is a dictionary with `tables` array. Each table has:
- `name`: table identifier
- `columns`: array of column definitions with:
  - `name`: column identifier
  - `type`: "string", "number", or "enum"
  - For "number": `min`, `max` (numeric bounds)
  - For "enum": `enums` (array of `{value, description}` objects)
  - For "geometry" (optional): `geometry_type`, `srid`, `metric_srid`, `spatial_role`, `distance_min_m`, `distance_max_m`, `buffer_min_m`, `buffer_max_m`

Geometry metadata is recommended but not required. PostGIS mutations fall back to safe defaults when geometry metadata is absent:
- `distance_min_m`: 100
- `distance_max_m`: 5000
- `buffer_min_m`: 100
- `buffer_max_m`: 3000

## Current Limitations & Constraints

- **Portuguese language hardcoded**: Queries adapted specifically for Portuguese language
- **Single schema mutation**: No support for WHERE clause expansion, JOIN modifications, or subquery generation
- **No error handling**: Missing validation for missing schema columns, invalid node types, or LLM failures
- **LLM backend required for mutated queries**: Bedrock mode requires a Bedrock API key and OpenAI-compatible base URL; local mode requires Colab/GPU inference dependencies and a Hugging Face model available to `transformers`

## Dependencies

- **sqlglot**: SQL parsing and AST manipulation (postgres dialect)
- **openai**: OpenAI-compatible client for Amazon Bedrock Chat Completions (`openai.gpt-oss-120b`)
- **python-dotenv**: Loads Bedrock endpoint and API key configuration from `.env`
- **transformers / accelerate / torch / bitsandbytes**: Optional local LLM dependencies for `local-llm.py`, installed in the Colab runtime rather than required for default Bedrock mode
- **random**: For random selection in mutations

## Key Design Decisions

1. **Changelog-driven LLM context**: Instead of just showing before/after SQL, explicitly list what changed to make LLM adaptation more accurate
2. **AST transformation pattern**: Using sqlglot's `transform()` method to recursively visit and modify nodes rather than manual tree walking
3. **Node copying in mutations**: `mutate_agg` explicitly copies node arguments to avoid shared AST references across modifications
4. **Type-safe mutations**: Each mutation checks column type before applying (e.g., only mutate_between on numeric columns)
5. **Semantic-changing mutations**: Prefer mutations that deliberately change query intent in a bounded, schema-aware way over rewrites that preserve exact semantics. Equivalent rewrites are useful only as implementation helpers or secondary diversity, not as the main augmentation objective.
6. **Coordinated PostGIS values**: Repeated spatial radii or distance thresholds in a single SQL query should be mutated to the same replacement value through shared per-query state.
7. **Lazy local LLM loading**: `local-llm.py` imports and loads heavy Hugging Face dependencies only when local mode is used, keeping normal Bedrock imports lightweight.
8. **No exposed chain-of-thought**: Local Qwen calls default to `LOCAL_LLM_THINKING=false` and strip `<think>...</think>` blocks before returning text to the augmentation pipeline.
9. **Dataset batch outputs are reduced views**: The geospatial batch writer emits only the fields needed for training and change tracking instead of copying all source metadata into the derived artifacts.
10. **Bedrock through OpenAI compatibility**: Remote adaptation uses `openai.gpt-oss-120b` on an explicitly configured `bedrock-mantle` OpenAI-compatible endpoint.
11. **Bounded dataset concurrency**: The geospatial batch exposes `--max-workers` with a default of `5`; it limits outstanding paid LLM requests and reconstructs outputs in source order.
12. **Local batch execution remains sequential**: When `LOCAL_LLM=true`, invoke the geospatial batch with `--max-workers 1` because the local model instance is shared within the process.
13. **Batch failure visibility**: The geospatial batch logs progress on each completed request and stops on the first failed request rather than writing incomplete output files.
14. **No-op mutation fast path**: If the AST passes produce an empty `changelog`, `create_random_variation` preserves the original natural-language query and skips LLM adaptation.
15. **Conservative text-pattern mutation**: `LIKE` and `ILIKE` mutations change only simple outer-wildcard shape; patterns containing `_`, escaping, or internal `%` are preserved.

## Extension Points for Future Mutations

To add a new mutation type:
1. Create `mutations/<feature>.py` with a `mutate_<feature>(node, changelog, schema)` function that:
   - Checks `isinstance(node, exp.<TargetNodeType>)`
   - Validates schema constraints (if needed)
   - Records old/new lines to `changelog`
   - Returns modified node (or original if no mutation applies)
2. Export it from `mutations/__init__.py`
3. Import and call it inside `mutate_operators()` in `augmentor.py`
4. Update schema format in `main.py` if new column metadata is needed

Examples of potential mutations:
- LIMIT clause modifications
- JOIN condition swaps
- GROUP BY additions/removals
- Subquery generation/inlining
- Window function introduction
- Additional PostGIS mutations such as centroid/point-on-surface swaps, validity filters, area-shape wrappers, and SRID-aware transforms

## Documentation Maintenance

**Important:** When adding new features or mutations:
1. Always update `README.md` with:
   - New dependencies (if added to `pyproject.toml`)
   - New mutation types in the "Tipos de Mutações Suportadas" section
   - Updated setup/usage instructions if affected
2. Always update `AGENTS.md` with:
   - Architecture changes (new components, modified data flow)
   - New dependencies and design decisions
   - Updated extension points and limitations
   - Any new constraints or requirements

Keep these files in sync so future developers can quickly understand the codebase without deep code reading.
