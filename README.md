# AST-Driven Data Augmentation for Text-to-SQL

Generate new question–SQL pairs through controlled changes to SQL abstract syntax trees (ASTs), guided by domain metadata. An LLM adapts the original question using the transformed SQL and an explicit mutation changelog.

[Paper](https://sol.sbc.org.br/index.php/sbbd_estendido/article/view/44122) · [Quick start](#quick-start) · [Results](#intrinsic-evaluation) · [Documentation](#documentation) · [Citation](#citation)

## Overview

Text-to-SQL datasets require aligned natural-language questions and SQL queries. Paraphrasing increases linguistic variety while keeping the original SQL and intent. This project explores semantic variation: changing what a query asks for, then adapting its question accordingly.

The method takes an existing question–SQL pair and a **custom schema** containing eligible columns, valid values, ranges, and semantic relationships. SQLGlot performs the AST transformations; the LLM expresses the resulting changes in natural language.

This repository contains the augmentation method and intrinsic evaluation developed during an undergraduate research project at the University of São Paulo (USP). It may receive further research extensions. **Downstream fine-tuning and model evaluation are outside the current scope.**

The experiments use Brazilian Portuguese questions. The implementation targets PostgreSQL/PostGIS; support for other SQL dialects has not been established by this evaluation.

## How it works

1. **Parse the SQL** into an AST.
2. **Apply compatible semantic mutations**, constrained by the custom schema, and record their changes.
3. **Apply guarded equivalent rewrites** to add structural variety without changing the semantics produced by the mutations.
4. **Generate the transformed SQL** and ask an LLM to adapt the question using the original pair, transformed query, and semantic changelog.

Equivalent rewrites do not enter the semantic changelog. If no semantic mutation occurs, the original question is retained without an LLM call.

### Augmentation strategies

| Strategy | SQL | Question |
|---|---|---|
| Paraphrase only | Preserved exactly | Rephrased without changing its meaning |
| AST augmentation | Transformed by the AST pipeline | Adapted to reflect the semantic changes |
| AST + paraphrase | Transformed by the same AST pipeline | Adapted and explicitly rephrased |

AST augmentation uses an LLM for question adaptation; “AST” does not mean that the entire pair is generated without an LLM.

### Supported transformations

Nine semantic mutation families are included:

| Family | Transformation |
|---|---|
| Binary value | Flip a binary value in an equality predicate |
| Enum equality | Replace a categorical value with another allowed value |
| Aggregate function | Change an aggregation among `SUM`, `AVG`, `MIN`, and `MAX` |
| Threshold shift | Change a supported comparison operator and numeric/date threshold |
| BETWEEN range | Change interval bounds within configured limits |
| Equivalent column | Replace a column with another in its semantic group |
| Value group | Replace an `IN` value set with another configured group |
| Text pattern | Change a supported `LIKE`/`ILIKE` pattern relation |
| PostGIS | Transform supported spatial operations and distance/buffer parameters |

“Equivalent column” refers to a configured semantic group, not to query equivalence: replacing the selected attribute can change the requested information.

Three additional **equivalent rewrites** cover guarded forms of `DISTINCT → GROUP BY`, `BETWEEN → inclusive comparisons`, and `INNER JOIN → IN subquery`. They apply only when their implementation guards match, rather than to arbitrary queries.

See [mutation details](docs/mutations.md) and the [custom schema guide](docs/custom-schema.md) for applicability conditions and examples.

## Quick start

Requires **Python 3.12+**, [uv](https://docs.astral.sh/uv/), and credentials for the configured remote LLM backend.

```bash
git clone https://github.com/ioolliver/ast-driven-data-augmentation-algorithm.git
cd ast-driven-data-augmentation-algorithm
uv sync
cp .env.example .env
```

Configure `.env` for the research backend, **GPT-OSS-120B via Amazon Bedrock**:

```dotenv
OPENAI_API_KEY=your-bedrock-api-key
OPENAI_BASE_URL=https://bedrock-mantle.us-east-1.api.aws/v1
BEDROCK_MODEL=openai.gpt-oss-120b
```

Use the Bedrock region and model access available to your account. These `OPENAI_*` variables configure the OpenAI-compatible Bedrock client; the key is a Bedrock credential.

Run the minimal example:

```bash
uv run python examples/basic_usage.py
```

The example provides a small custom schema and one question–SQL pair, then displays the transformed pair. Generation may incur provider charges and may vary between runs.

The research configuration above is the default setup documented here. Backend configuration and local inference are covered in the [usage guide](docs/usage.md). Changing a model or provider does not reproduce the research configuration.

## Datasets

The final intrinsic evaluation used two Portuguese Text-to-SQL datasets related to the Brazilian School Census:

| Dataset | Focus | Original pairs | Documentation |
|---|---|---:|---|
| Temporal dataset (CensoBench) | Educational indicators and temporal queries | 107 | [Dataset guide](datasets/censobench/README.md) |
| AtlasSQL-BR | Geospatial queries with PostGIS | 980 | [Dataset guide](datasets/atlas_sql_br/README.md) |

Both span four difficulty levels. AtlasSQL-BR contributes 245 original pairs per level. The temporal set contains 46 easy, 30 medium, 8 hard, and 23 very hard pairs.

The dataset guides describe provenance, source formats, schemas, preparation steps, and artifact roles. Please also acknowledge the original dataset authors when using their data.

## Intrinsic evaluation

The final comparison evaluated paraphrase-only, AST, and AST-plus-paraphrase augmentation on both datasets.

**Mean question embedding variation**, measured with `jina-embeddings-v3`:

| Dataset | Paraphrase only | AST | AST + paraphrase |
|---|---:|---:|---:|
| Temporal dataset | 1.9% | 26.9% | 27.3% |
| AtlasSQL-BR | 2.0% | 15.6% | 16.8% |

Question variation is the cosine distance between original and augmented question embeddings, clipped to `[0, 1]` and expressed as a percentage.

**Mean SQL component variation** for AST augmentation was **29.8%** on the temporal dataset and **11.3%** on AtlasSQL-BR. Component matching measures the proportion of changed normalized AST components. SQL embedding distance is not used as the SQL result reported here.

These metrics quantify variation. **They do not establish execution correctness, question–SQL alignment, or an improvement in downstream Text-to-SQL accuracy.**

GPT-OSS-120B through Amazon Bedrock generated the final experimental outputs for both datasets. Gemini was used in earlier tests on smaller sets of pairs. The WTAG paper reports an earlier, preliminary evaluation; the table above summarizes the expanded final evaluation and should not be read as a transcription of the paper's results.

See the [results index](results/README.md) for detailed artifacts and the [reproduction guide](docs/reproduction.md) for experimental settings. Recomputing metrics from preserved pairs and generating new pairs with an LLM are separate workflows; new generation is not guaranteed to recover identical outputs.

## Documentation

| Goal | Guide |
|---|---|
| Use the API, configure a backend, or run augmentation in batches | [Usage](docs/usage.md) |
| Prepare metadata for a new database | [Custom schema](docs/custom-schema.md) |
| Understand mutation and rewrite conditions | [Transformations](docs/mutations.md) |
| Reproduce the intrinsic evaluation | [Reproduction](docs/reproduction.md) |
| Find detailed evaluation outputs | [Results](results/README.md) |
| Relate research stages to publications and artifacts | [Publications](docs/publications.md) |
| Run tests or extend the implementation | [Development](docs/development.md) |

### Repository layout

| Directory | Contents |
|---|---|
| `src/ast_augmentation/` | Core augmentation, LLM integration, utilities, and shared evaluation |
| `src/ast_augmentation/mutations/` | Semantic mutation implementations |
| `src/ast_augmentation/rewrites/` | Guarded equivalent rewrites |
| `datasets/` | Dataset inputs, custom schemas, and provenance documentation |
| `experiments/` | Intrinsic evaluation scripts and configurations |
| `results/` | Preserved evaluation artifacts |
| `examples/` | Minimal usage examples |
| `docs/` | Detailed user and developer guides |
| `infra/` | Container and GPU environment configuration |
| `tests/` | Automated tests |

## Limitations and future work

- Preparing the custom schema requires domain knowledge and manual effort.
- Variation depends on the supported mutation families and the constructs in the input SQL; some queries may receive no semantic changes.
- AST manipulation and schema constraints do not prove that every generated query executes correctly or produces an informative result.
- LLM adaptation can omit changes or introduce inconsistencies. Generated pairs have not undergone exhaustive human validation.
- Evaluation covers two Portuguese datasets and compares against a paraphrasing baseline; broader generalization remains untested.
- Downstream training benefits have not been demonstrated.

Future work includes execution and alignment validation, broader mutation coverage, assistance with custom schema construction, and downstream Text-to-SQL evaluation.

## Citation

If you use this code, method, or experimental artifacts in research, **please cite our WTAG/SBBD 2026 paper**:

**Isaque Oliveira do Nascimento and Kelly Rosa Braghetto.**  
*SQL-Guided Semantic Variation for Data Augmentation in Text-to-SQL.*  
Anais Estendidos do XLI Simpósio Brasileiro de Bancos de Dados, 2026.

[Read the paper](https://sol.sbc.org.br/index.php/sbbd_estendido/article/view/44122)

```bibtex
@inproceedings{nascimento2026sqlguided,
  author    = {Isaque Oliveira do Nascimento and Kelly Rosa Braghetto},
  title     = {{SQL-Guided Semantic Variation for Data Augmentation in Text-to-SQL}},
  booktitle = {Anais Estendidos do XLI Simpósio Brasileiro de Bancos de Dados},
  year      = {2026},
  publisher = {Sociedade Brasileira de Computação},
  url       = {https://sol.sbc.org.br/index.php/sbbd_estendido/article/view/44122}
}
```

Machine-readable citation information is available in [CITATION.cff](CITATION.cff).

## Authors and acknowledgments

Developed by **Isaque Oliveira do Nascimento**, under the supervision of **Prof. Kelly Rosa Braghetto**, at the University of São Paulo (USP), Instituto de Matemática, Estatística e Ciência da Computação.

Contact: [isaque.nascimento@usp.br](mailto:isaque.nascimento@usp.br). For questions about the implementation, please [open an issue](https://github.com/ioolliver/ast-driven-data-augmentation-algorithm/issues).

This work was developed with a CNPq-PIBIC undergraduate research scholarship and was partially supported by FAPESP (grants **2023/00779-0** and **2023/18026-8**) and CNPq (grant **420623/2023-0**).

## License

The original project code is released under the [MIT License](LICENSE). Third-party datasets, models, and dependencies remain subject to their respective licenses and terms; the MIT license does not relicense those materials.

Academic citation is requested in the [Citation](#citation) section. This request does not add conditions to the MIT License.
