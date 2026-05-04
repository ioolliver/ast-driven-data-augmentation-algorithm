# CLAUDE.md

This file provides guidance to Codex when working with code in this repository.

## Project Overview

This is an **AST-driven SQL data augmentation tool** that generates semantic variations of SQL queries and their natural language descriptions. The tool uses SQL Abstract Syntax Tree (AST) transformations combined with LLM-based query adaptation to create training data for machine learning models.

**Key purpose:** Given an original SQL query + natural language description + schema, generate semantically equivalent query pairs with different SQL and adapted natural language descriptions.

## Folder Structure

```
.
├── main.py                        # Entry point: schema data, test queries, run loop
├── augmentor.py                   # Orchestrator: create_random_variation
├── llm.py                         # LLM layer: prompting, Gemini call, format_changelog
├── schema_utils.py                # Schema helpers: get_col_info, get_table_name
├── mutations/
│   ├── __init__.py                # Re-exports all mutate_* functions
│   ├── between.py                 # mutate_between — BETWEEN range randomization
│   ├── enum_eq.py                 # mutate_enum — enum equality value swap
│   ├── agg.py                     # mutate_agg — aggregate function swap (SUM/AVG/MIN/MAX)
│   ├── threshold_shift.py         # mutate_threshold_shift — inequality operator + value shift
│   ├── equivalent_column.py       # mutate_equivalent_column — semantic group column swap
│   ├── value_group.py             # mutate_value_group — IN clause value group swap
│   └── binary.py                  # mutate_binary — binary column value flip (0 ↔ 1)
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
   - Each mutation appends changes to a `changelog` list for LLM context

2. **Schema Utilities** (`schema_utils.py`)
   - `get_col_info`: Resolves column metadata from schema by table + column name
   - `get_table_name`: Extracts real table name from an AST column node, resolving aliases

3. **LLM Layer** (`llm.py`)
   - `format_changelog`: Formats changelog list into readable diff string
   - `get_llm_prompt`: Builds the full prompt with original/modified SQL and changelog
   - `send_to_llm`: Calls Google Gemini API using `GEMINI_KEY` from `.env`
   - `adapt_query`: Composes the above to return an adapted natural language query

4. **Orchestrator** (`augmentor.py`)
   - `create_random_variation`: Parses SQL → two-pass AST transform → adapted query
   - Pass 1: column swaps (`mutate_equivalent_column`) so subsequent mutations see updated columns
   - Pass 2: all remaining mutations applied together

5. **Entry Point** (`main.py`)
   - Holds hardcoded schema definition and test queries
   - Loops over query pairs, calls `create_random_variation`, prints results

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
LLM adapts query_text based on changelog
  ↓
Output: (adapted_query, modified_sql)
```

### Schema Format

Schema is a dictionary with `tables` array. Each table has:
- `name`: table identifier
- `columns`: array of column definitions with:
  - `name`: column identifier
  - `type`: "string", "number", or "enum"
  - For "number": `min`, `max` (numeric bounds)
  - For "enum": `enums` (array of `{value, description}` objects)

## Current Limitations & Constraints

- **Portuguese language hardcoded**: Queries adapted specifically for Portuguese language
- **Single schema mutation**: No support for WHERE clause expansion, JOIN modifications, or subquery generation
- **No error handling**: Missing validation for missing schema columns, invalid node types, or LLM failures
- **Gemini API dependency**: Requires valid `GEMINI_KEY` in `.env`

## Dependencies

- **sqlglot**: SQL parsing and AST manipulation (postgres dialect)
- **google-genai**: Gemini API client (`gemini-3.1-flash-lite-preview`)
- **python-dotenv**: Loads `GEMINI_KEY` from `.env`
- **random**: For random selection in mutations

## Key Design Decisions

1. **Changelog-driven LLM context**: Instead of just showing before/after SQL, explicitly list what changed to make LLM adaptation more accurate
2. **AST transformation pattern**: Using sqlglot's `transform()` method to recursively visit and modify nodes rather than manual tree walking
3. **Node copying in mutations**: `mutate_agg` explicitly copies node arguments to avoid shared AST references across modifications
4. **Type-safe mutations**: Each mutation checks column type before applying (e.g., only mutate_between on numeric columns)

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

## Documentation Maintenance

**Important:** When adding new features or mutations:
1. Always update `README.md` with:
   - New dependencies (if added to `pyproject.toml`)
   - New mutation types in the "Tipos de Mutações Suportadas" section
   - Updated setup/usage instructions if affected
2. Always update `CLAUDE.md` with:
   - Architecture changes (new components, modified data flow)
   - New dependencies and design decisions
   - Updated extension points and limitations
   - Any new constraints or requirements

Keep these files in sync so future developers can quickly understand the codebase without deep code reading.
