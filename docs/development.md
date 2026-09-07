# Development

## Setup and tests

```bash
uv sync
uv run python -m unittest discover -s tests -v
```

The project uses a `src` layout. Import public functions from `ast_augmentation`;
do not add repository-root path manipulation to scripts or tests.

## Responsibilities

- `src/ast_augmentation/mutations/`: semantic SQL changes that produce changelog entries.
- `src/ast_augmentation/rewrites/`: guarded semantics-preserving SQL rewrites.
- `src/ast_augmentation/evaluation/`: reusable dataset, scoring, and workbook code.
- `datasets/`: immutable source/prepared inputs and their schema metadata.
- `experiments/`: dataset-specific command-line orchestration.
- `results/`: preserved generated pairs, scores, and reports.

Add focused unit tests for each AST shape and for cases that must be skipped.
Equivalent rewrites should include execution-based tests where practical. Never
exercise a live LLM in the unit suite; patch the client or inject an augmenter.

When adding a new mutation, keep schema lookup in `schema_utils.py`, return the
original node when requirements do not match, and append a precise changelog only
for semantic changes. Keep provider-specific behavior in `llm.py` or a dedicated
backend module rather than in AST transformations.
