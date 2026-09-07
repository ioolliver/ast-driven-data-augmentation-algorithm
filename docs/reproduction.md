# Reproducing the intrinsic evaluation

The preserved results and generating new pairs are separate workflows. Recompute
metrics from the committed pairs when exact LLM outputs are not required.

## Environment

```bash
uv sync
```

Semantic-variation scoring additionally requires a compatible PyTorch,
Transformers, and Sentence Transformers environment. The container definition in
`infra/semantic_variation.def` records the GPU-oriented analysis environment.

## Generate augmentation variants

Configure the backend as described in [Usage](usage.md), then run:

```bash
uv run python experiments/censobench/compare_methods.py
uv run python experiments/atlas_sql_br/compare_methods.py
```

Each script produces separate artifacts for paraphrase-only, AST-only, and
AST-plus-paraphrase strategies. The final study used `openai.gpt-oss-120b` via
Amazon Bedrock. Mutation selection and model generation are non-deterministic,
so a new run is not expected to reproduce the committed text byte for byte.

## Recompute metrics

```bash
uv run python experiments/censobench/analyze_semantic_variation_methods.py
uv run python experiments/atlas_sql_br/analyze_semantic_variation_methods.py
uv run python experiments/atlas_sql_br/analyze_component_matching_methods.py
```

The CensoBench component wrapper can be run for a selected pair file with
`experiments/censobench/analyze_component_matching.py`. Use `--help` on every
script to override inputs, outputs, model, device, batch size, or worker count.

Question semantic variation uses clipped cosine distance with
`jinaai/jina-embeddings-v3` by default. SQL component variation compares
normalized AST components; it is not an execution-correctness metric.

## Verification

```bash
uv run python -m unittest discover -s tests -v
```

The automated tests use mocked LLM responses and do not require network access.
