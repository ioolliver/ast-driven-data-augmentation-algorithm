# Repository guidelines

## Purpose

This repository implements schema-guided SQL AST augmentation for Text-to-SQL.
Semantic mutations change the requested information and produce a changelog; an
LLM uses that changelog to adapt the natural-language question. Conservative
equivalent rewrites add structural SQL variation without entering the changelog.

Downstream fine-tuning and model benchmarking are outside this iteration.

## Layout

- `src/ast_augmentation/`: installable Python package and public API.
- `src/ast_augmentation/mutations/`: nine semantic mutation families.
- `src/ast_augmentation/rewrites/`: three guarded equivalent rewrites.
- `src/ast_augmentation/evaluation/`: reusable scoring and reporting utilities.
- `datasets/`: source/prepared inputs, schema metadata, and provenance notes.
- `experiments/`: dataset-specific augmentation and analysis commands.
- `results/`: preserved generated pairs, scores, and reports.
- `examples/`: minimal executable usage.
- `docs/`: user, reproduction, and development guides.
- `infra/`: optional analysis-environment configuration.
- `tests/`: offline unit and integration tests.

## Development workflow

Use Python 3.12+ and uv:

```bash
uv sync
uv run python -m unittest discover -s tests -v
```

The project uses a `src` layout. Import through `ast_augmentation`; do not insert
the repository root into `sys.path`. Keep scripts runnable from the repository
root after `uv sync`.

## Design rules

- Mutations must return the original node when their schema or AST requirements
  do not match.
- Semantic mutations append accurate old/new SQL fragments and useful context to
  the changelog. Equivalent rewrites never do.
- Schema metadata constrains allowed values and ranges; do not invent domain
  values inside mutation code.
- Keep dataset-specific paths and formats in `experiments/` and reusable logic in
  the package.
- Keep provider calls isolated from AST transformation logic.
- Do not call a live LLM in tests. Patch the provider or inject an augmenter.
- Add skip-case tests as well as success-case tests for every AST transformation.
- Use execution-based equivalence tests for rewrites when practical.

## Data and results

Treat files under `datasets/` as inputs and files under `results/` as preserved
research artifacts. New exploratory runs should use a separate output directory.
The MIT license covers the original project code and does not relicense third-party
datasets or models.

## Documentation

Keep public behavior synchronized across `README.md`, `docs/usage.md`, and the
dataset/result indexes. Cite the WTAG/SBBD 2026 paper through `CITATION.cff` when
describing scholarly use. Do not add unpublished internal reports or submissions
to the repository without explicit permission.
