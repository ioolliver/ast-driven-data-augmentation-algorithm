# Usage

## Install and run the example

Run these commands from a terminal:

```bash
git clone https://github.com/ioolliver/ast-driven-data-augmentation-algorithm.git
cd ast-driven-data-augmentation-algorithm
uv sync
cp .env.example .env
```

Python 3.12 or newer and uv are required. On PowerShell, use
`Copy-Item .env.example .env` for the last command. Commands below run from the
repository root. With `uv run`, manual virtual-environment activation is unnecessary.

Edit `.env` with your Bedrock credentials, then run:

```bash
uv run python examples/basic_usage.py
```

The example uses a fictional `schools` table, a Portuguese question, and a
custom schema with two allowed state values. It changes the filter from
`SP` (São Paulo) to `MG` (Minas Gerais) and asks the LLM to adapt the question.
It prints both pairs and does not write a dataset or connect to a database.
The schema deliberately offers just one alternative so the SQL change is easy
to inspect; the LLM's wording can vary.

The expected transformed SQL, apart from formatting, is:

```sql
SELECT name FROM schools WHERE state = 'MG';
```

Inspect whether the returned Portuguese question asks for school names in Minas
Gerais. This example demonstrates the pipeline; it does not validate generated
pairs by executing their SQL. A remote run can incur provider charges.

## Configure the backend

Configuration is read from environment variables and the repository's `.env`.
Existing environment variables take precedence. Restart the Python process after
changing backend selection or the Bedrock model.

### Amazon Bedrock (default)

The default model is `openai.gpt-oss-120b`, used for the final research
experiments on both datasets.

```dotenv
OPENAI_API_KEY=your-bedrock-api-key
OPENAI_BASE_URL=https://bedrock-mantle.us-east-1.api.aws/v1
BEDROCK_MODEL=openai.gpt-oss-120b
LOCAL_LLM=false
```

Use a Bedrock API key and a region where your account has access to the chosen
model. The `OPENAI_*` names refer to the OpenAI-compatible client interface;
they do not mean that an OpenAI platform key should be used.

`BEDROCK_MODEL` can select another model supported by your Bedrock endpoint.
The remote backend currently validates that the endpoint is a
`bedrock-mantle.<region>.api.aws/v1` URL. Arbitrary OpenAI-compatible providers
are not supported by changing the URL alone.

Missing credentials or endpoint produce a configuration error. Invalid credentials,
model access, network failures, and service limits can also prevent generation.
Keep credentials in your local environment; do not include them in issues or examples.

### Local Hugging Face inference

The existing local backend can be selected with:

```dotenv
LOCAL_LLM=true
LOCAL_LLM_MODEL=Qwen/Qwen3.5-4B-Instruct
LOCAL_LLM_4BIT=true
LOCAL_LLM_THINKING=false
```

The model identifier above is the current implementation default, not the model
used for the final experiments. Choose a model available to your account and
supported by your installed Transformers version and hardware.

Local inference needs additional packages in the same environment:

```bash
uv pip install transformers accelerate bitsandbytes torch
uv run python examples/basic_usage.py
```

These optional packages are not pinned by the project's core lockfile. Use a
PyTorch build and quantization setup compatible with your GPU. The 4-bit path
requires compatible hardware; no specific GPU or model combination is guaranteed
by this example.

| Variable | Default | Purpose |
|---|---|---|
| `LOCAL_LLM_MAX_NEW_TOKENS` | `512` | Generation length limit |
| `LOCAL_LLM_TEMPERATURE` | `0.2` | Sampling temperature |
| `LOCAL_LLM_TOP_P` | `0.9` | Nucleus sampling threshold |
| `LOCAL_LLM_4BIT` | `true` | Enable 4-bit loading |
| `LOCAL_LLM_THINKING` | `false` | Request non-thinking output where supported |

The local model is loaded lazily and reused. Its loader uses
`trust_remote_code=True`, so choose a model whose repository code you trust.
For local batches, use `--max-workers 1`.

## Python API

Until the planned package migration, import from the repository root:

```python
from augmentor import (
    create_random_variation,
    create_paraphrase_only_variation,
    create_random_variation_with_paraphrasing,
)
from examples.basic_usage import SCHEMA, QUESTION, SQL

new_question, new_sql = create_random_variation(SCHEMA, QUESTION, SQL)
```

Each function returns `(question, sql)`:

| Function | Arguments | Behavior |
|---|---|---|
| `create_random_variation` | schema, question, sql | Apply AST transformations and adapt the question |
| `create_paraphrase_only_variation` | question, sql | Paraphrase the question, preserving the SQL string |
| `create_random_variation_with_paraphrasing` | schema, question, sql | Apply AST transformations, adapt and rephrase the question |

AST methods skip the LLM when no semantic mutation is recorded. Equivalent SQL
rewrites may still change formatting or structure. The prompt currently requests
Portuguese questions. The core parser and serializer use the PostgreSQL dialect.

## Batch augmentation

During repository reorganization, the batch scripts remain under `data/`.
Run either command from the repository root:

```bash
uv run python data/geo_dataset/compare_augmentation_methods.py --output-dir runs/atlas-sql-br-example --max-workers 5
uv run python data/censo_escolar_dataset/compare_augmentation_methods.py --output-dir runs/censobench-example --max-workers 5
```

Each command runs all three strategies and writes separate JSON/XLSX pairs for
each method. Use a fresh output directory per experiment to preserve earlier
results. These commands process the full dataset and make multiple LLM calls;
they are not required for the minimal example.

Use `--input` to select a compatible source dataset. Geo input uses the
`question`/`sql_code` source contract; Censo input uses a `queries` array with
`pergunta_nl`/`sql` fields. Their scripts supply dataset-specific schemas.
Consult each script's `--help` before adapting the batch.

The scripts preserve source order and stop on a failed generation. Outputs from
previously completed methods can remain if a later method fails. For local
inference replace `--max-workers 5` with `--max-workers 1`.

Generating new pairs and recomputing metrics on preserved pairs are separate
operations. Random mutations and LLM generation mean a new run need not reproduce
the exact research outputs.

## Offline verification

The focused tests exercise the example and LLM client using simulated responses:

```bash
uv run python -m unittest discover -s tests -p 'test_basic_usage.py'
uv run python -m unittest discover -s tests -p 'test_llm.py'
```

They do not call Bedrock or download a local model. A passing mocked test does not
verify live provider access or the quality of real LLM responses.
