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
│   ├── analysis_dataset.py        # Shared analyzer row loader for flat and censo query-shaped augmented pairs
│   ├── censo_escolar_dataset/
│   │   ├── original_dataset.json  # CensoBench source rows in dataset_info + queries format
│   │   ├── schema.py              # Schema dedicated to Censo Escolar mutations
│   │   ├── analyze_semantic_variation.py   # Censo wrapper over the shared embedding analyzer
│   │   └── analyze_component_matching.py   # Censo wrapper over the shared SQL component analyzer
│   └── geo_dataset/
│       ├── geo_base_dataset.json   # 980 base_dataset rows processed by the batch
│       ├── geodataset_schema.py   # Schema dedicated to the geospatial dataset batch
│       ├── apply_augmentation_geo_dataset.py  # Bounded-concurrency batch writer
│       ├── analyze_semantic_variation.py      # Embedding-based score/report generator
│       └── analyze_component_matching.py      # SQL AST component matching report
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
│   ├── postgis.py                 # PostGIS function and distance-threshold mutations
│   ├── distinct_group_by.py       # DISTINCT-to-GROUP-BY equivalent rewrite
│   └── between_comparisons.py     # BETWEEN-to-comparisons equivalent rewrite
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
   - `distinct_group_by.py`: Rewrites simple `SELECT DISTINCT` column projections as an equivalent `GROUP BY`
   - `between_comparisons.py`: Rewrites a column `BETWEEN` literal bounds as inclusive `>=` and `<=` comparisons
   - Semantic mutations append changes to a changelog for LLM context; equivalent rewrites do not

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
   - `create_random_variation`: Parses SQL → three-pass AST transform → adapted query
   - Pass 1: column swaps (`mutate_equivalent_column`) so subsequent mutations see updated columns
   - Pass 2: all remaining mutations applied together
   - Pass 3: forward-only equivalent rewrites applied to the semantics produced by the first two passes
   - Maintains a per-query `mutation_state` dictionary so repeated PostGIS radii/distances are changed consistently across a query
   - Returns the original natural-language query without an LLM call when no semantic mutation adds an entry to `semantic_changelog`, even if an equivalent rewrite changes the SQL structure

5. **Entry Point** (`main.py`)
   - Holds hardcoded schema definition and test queries
   - Loops over query pairs, calls `create_random_variation`, prints results

6. **Geo Dataset Batch Script** (`data/geo_dataset/apply_augmentation_geo_dataset.py`)
   - Loads `data/geo_dataset/geo_base_dataset.json`, restricted to `source == "base_dataset"`
   - Applies `create_random_variation` once per dataset row with at most five concurrent requests by default
   - Logs completed, succeeded, and failed request counts as each remote call finishes
   - Writes a mixed original+augmented dataset and an augmented-only change mapping

7. **Semantic Variation Analysis** (`data/geo_dataset/analyze_semantic_variation.py`)
   - Loads `data/geo_dataset/geo_dataset_augmented_only.json`
   - Uses `jinaai/jina-embeddings-v3` with the symmetric `text-matching` task on Colab/T4
   - Calculates clipped cosine variation scores independently for SQL and question text plus their equal-weight mean
   - Writes row-level scores as JSON and aggregate statistics as Markdown

8. **Component Matching Analysis** (`data/geo_dataset/analyze_component_matching.py`)
   - Loads `data/geo_dataset/geo_dataset_augmented_only.json`
   - Parses original and changed SQL with SQLGlot using the Postgres dialect
   - Extracts normalized AST component slots for projections, aggregations, tables, joins, predicates, literals, grouping, ordering, limits, and PostGIS function arguments
   - Computes `changed_component_count / component_total` and writes row-level changed components plus aggregate statistics as JSON and Markdown

9. **Shared Analysis Dataset Loader** (`data/analysis_dataset.py`)
   - Validates the flat augmented-pair contract used by the geo batch: `original_question`, `original_sql`, `changed_question`, `changed_sql`, and `level`
   - Also normalizes Censo Escolar `{"queries": [...]}` rows once each query has `changed_question` and `changed_sql`, deriving `level` from `complexidade.nivel`
   - Fails loudly when the raw Censo Escolar source file is used before augmentation, because semantic/component variation metrics require original/changed pairs

10. **Censo Escolar Analysis Wrappers** (`data/censo_escolar_dataset/analyze_*.py`)
   - Reuse the geo analyzer implementations and scoring logic with Censo-specific default paths and report titles
   - Default input is `data/censo_escolar_dataset/censo_escolar_dataset_augmented_only.json`
   - Component matching defaults to SQLGlot `bigquery` because CensoBench declares Standard SQL and includes BigQuery functions such as `SAFE_DIVIDE`
   - Write Censo-specific score/report artifacts under `data/censo_escolar_dataset/`

### Data Flow

```
Input: schema + query_text + sql
  ↓
Parse SQL → AST
  ↓
Apply semantic mutation passes → collect semantic changelog
  ↓
Apply equivalent structural rewrites without changing the changelog
  ↓
Generate modified SQL from AST
  ↓
If semantic changelog is empty: preserve query_text without an LLM call
Otherwise: LLM adapts query_text based on semantic changelog
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

Semantic variation report flow:

```
Input: geo_dataset_augmented_only.json or censo_escolar_dataset_augmented_only.json
  ↓
Normalize augmented rows through data/analysis_dataset.py
  ↓
Embed original/changed SQL and original/changed questions with Jina v3
  ↓
Compute score = clip(1 - cosine_similarity, 0, 1)
  ↓
Write geo_dataset_semantic_variation_scores.json
  ↓
Write geo_dataset_semantic_variation_report.md
```

Component matching report flow:

```
Input: geo_dataset_augmented_only.json or censo_escolar_dataset_augmented_only.json
  ↓
Normalize augmented rows through data/analysis_dataset.py
  ↓
Parse original/changed SQL with SQLGlot
  ↓
Extract normalized SQL component slots
  ↓
Compute score = changed_component_count / component_total
  ↓
Write geo_dataset_component_matching_scores.json
  ↓
Write geo_dataset_component_matching_report.md
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
- **Embedding scores are heuristic**: General-purpose semantic distances cannot prove whether a SQL mutation is behaviorally equivalent or different
- **Jina license constraint**: The default semantic-analysis model is licensed `CC BY-NC 4.0` and is selected for non-commercial analysis
- **Analysis requires augmented pairs**: `data/censo_escolar_dataset/original_dataset.json` is a source dataset only. The analysis wrappers require a censo augmented-pair file with `changed_question` and `changed_sql`.
- **Equivalent rewrites are intentionally conservative**: `DISTINCT` rewriting supports only plain column projections, and `BETWEEN` rewriting supports only a column with literal bounds.

## Dependencies

- **sqlglot**: SQL parsing and AST manipulation (postgres dialect)
- **openai**: OpenAI-compatible client for Amazon Bedrock Chat Completions (`openai.gpt-oss-120b`)
- **python-dotenv**: Loads Bedrock endpoint and API key configuration from `.env`
- **transformers / accelerate / torch / bitsandbytes**: Optional local LLM dependencies for `local-llm.py`, installed in the Colab runtime rather than required for default Bedrock mode
- **numpy**: Vector math, clipping, percentiles, and aggregate statistics for geo dataset analysis scripts
- **sentence-transformers / einops**: Optional embedding-model dependencies for `analyze_semantic_variation.py`, installed in the Colab runtime rather than required for augmentation
- **random**: For random selection in mutations

## Key Design Decisions

1. **Changelog-driven LLM context**: Instead of just showing before/after SQL, explicitly list what changed to make LLM adaptation more accurate
2. **AST transformation pattern**: Using sqlglot's `transform()` method to recursively visit and modify nodes rather than manual tree walking
3. **Node copying in mutations**: `mutate_agg` explicitly copies node arguments to avoid shared AST references across modifications
4. **Type-safe mutations**: Each mutation checks column type before applying (e.g., only mutate_between on numeric columns)
5. **Semantic-changing mutations remain primary**: Prefer mutations that deliberately change query intent in a bounded, schema-aware way. Forward-only equivalent rewrites run afterward as secondary structural diversity.
6. **Coordinated PostGIS values**: Repeated spatial radii or distance thresholds in a single SQL query should be mutated to the same replacement value through shared per-query state.
7. **Lazy local LLM loading**: `local-llm.py` imports and loads heavy Hugging Face dependencies only when local mode is used, keeping normal Bedrock imports lightweight.
8. **No exposed chain-of-thought**: Local Qwen calls default to `LOCAL_LLM_THINKING=false` and strip `<think>...</think>` blocks before returning text to the augmentation pipeline.
9. **Dataset batch outputs are reduced views**: The geospatial batch writer emits only the fields needed for training and change tracking instead of copying all source metadata into the derived artifacts.
10. **Bedrock through OpenAI compatibility**: Remote adaptation uses `openai.gpt-oss-120b` on an explicitly configured `bedrock-mantle` OpenAI-compatible endpoint.
11. **Bounded dataset concurrency**: The geospatial batch exposes `--max-workers` with a default of `5`; it limits outstanding paid LLM requests and reconstructs outputs in source order.
12. **Local batch execution remains sequential**: When `LOCAL_LLM=true`, invoke the geospatial batch with `--max-workers 1` because the local model instance is shared within the process.
13. **Batch failure visibility**: The geospatial batch logs progress on each completed request and stops on the first failed request rather than writing incomplete output files.
14. **Semantic no-op fast path**: If the semantic mutation passes produce an empty `semantic_changelog`, `create_random_variation` preserves the original natural-language query and skips LLM adaptation, even when the equivalent pass changes the SQL.
15. **Conservative text-pattern mutation**: `LIKE` and `ILIKE` mutations change only simple outer-wildcard shape; patterns containing `_`, escaping, or internal `%` are preserved.
16. **Embedding-based variation report**: The geo analysis scores SQL and question pairs separately using `clip(1 - cosine_similarity, 0, 1)` and reports an equal-weight combined score without treating it as formal SQL equivalence checking.
17. **Long-context multilingual embedding model**: Semantic analysis defaults to `jinaai/jina-embeddings-v3` with `text-matching` because it handles Portuguese and long SQL text on a Colab T4; this default is restricted to non-commercial use by its license.
18. **Component matching is structural and interpretable**: The geo component analyzer compares normalized SQL AST slots and reports changed components. It complements the embedding report but does not prove SQL correctness, behavioral equivalence, or natural-language alignment.
19. **Analyzer row loading is shared**: Geo and Censo analysis entry points share `data/analysis_dataset.py` so validation, censo query normalization, and raw-source failure behavior stay consistent across embedding and component reports.
20. **Censo analysis wrappers reuse scoring logic**: Censo Escolar scripts import the existing geo analyzers instead of copying scoring code, keeping dataset-specific defaults separate from the algorithms.
21. **Equivalent rewrites are isolated from LLM context**: `DISTINCT`-to-`GROUP BY` and `BETWEEN`-to-comparisons run only after semantic mutations and never add changelog entries.

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

To add an equivalent structural rewrite:
1. Create a focused `rewrite_<feature>(node)` function under `mutations/`
2. Return the original node when the conservative equivalence guards do not match
3. Export it from `mutations/__init__.py` and call it in the orchestrator's third pass
4. Do not append equivalent rewrites to `semantic_changelog`

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
