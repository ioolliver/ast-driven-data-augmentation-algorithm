# Spider 1.0 augmentation subset

This subset selects 20 **training databases** from the official Spider 1.0
archive: `hr_1`, `bike_1`, `movie_1`, `soccer_2`, `college_2`, `wine_1`,
`manufactory_1`, `dorm_1`, `store_1`, `music_1`, `hospital_1`, `flight_1`,
`network_2`, `game_1`, `allergy_1`, `loan_1`, `driving_school`,
`department_store`, `customers_and_addresses`, and `apartment_rentals`.
Together they have 1,971 original question–SQL rows (983 distinct SQL strings).
These are 20 database settings, not independently labeled semantic domains.

The downloaded archive is third-party material and is not checked into this
repository. Get `spider_data.zip` from the [official Spider site](https://yale-lily.github.io/spider/),
then extract it outside the repository or under an ignored `raw_data/` folder.
The resulting directory must contain `train_spider.json` and
`database/<db_id>/<db_id>.sqlite`. The archive also has `train_others.json`,
which this pilot deliberately excludes, and separate `dev.json` / `test.json`
files, which must never be used as augmentation seeds.

The official archive's `tables.json` has 166 database IDs: 140 from the main
Spider training set, six from `train_others`, and 20 development databases.
`test_tables.json` additionally contains 40 test databases (206 IDs in all).
The original Spider publication reports 200 databases across 138 domains; its
main training, development and test sets account for the 200, while the six
`train_others` databases are additional. A database ID is not a published
domain-category annotation.

`schemas.json` contains 185 curated columns across the 20 databases. Enum
alternatives came from the corresponding SQLite files. Numeric bounds were
reviewed against the data; implausible outliers were excluded where noted in
the curation. Identifiers and foreign keys were omitted. Selected compatible
columns share a `semantic_group` within their table, such as the three
`bike_1.weather` measures. The column mutation skips predicates with literal
equality, membership, text patterns, and arithmetic to avoid retaining a value
from the wrong column's domain. Spider's double-quoted categorical values are
accepted only when they match a configured enum, and SUM/AVG are restricted to
known numeric columns. This metadata is for
*semantic augmentation* and is not a replacement for the full table schema
that a downstream Text-to-SQL model will receive.

## Offline audit

From the repository root after `uv sync`:

```bash
uv run python experiments/spider/audit.py raw_data/spider_data
```

With seed 42, 1,030/1,971 examples had a semantic change, and all 1,030 generated
SQL strings passed SQLite `EXPLAIN QUERY PLAN` using their own databases.
The other 941 are ineligible under this conservative configuration and must
not be counted as new AST examples. Planning a SQL statement proves neither
that it returns useful rows nor that the adapted question is aligned with it.
Review a sample of final LLM outputs before fine-tuning.

## Generate the three arms

Configure the LLM as described in [the usage guide](../../docs/usage.md).
The generation command makes remote LLM calls and can incur charges. For a
small pilot:

```bash
uv run python experiments/spider/generate.py raw_data/spider_data \
  --output-dir raw_data/spider_pilot --limit 10
```

Omit `--limit` for the selected training subset. The script emits separate
JSONL files for `paraphrase`, `ast`, and `ast_paraphrase`. Each line has the
source index and database ID, original pair, method, and generated pair.
The AST and AST-plus-paraphrase arms share the **same mutated SQL** for each
source example. SQL that fails SQLite planning is skipped before an LLM call.
Use `--methods` to select arms and `--seed` to choose a mutation seed. For a
concurrent Bedrock run that reuses the same output directory, including an
existing completed `paraphrase.jsonl`:

```bash
uv run python experiments/spider/generate.py raw_data/spider_data \
  --output-dir raw_data/spider_pilot --max-workers 4 --progress-every 10
```

`--max-workers` defaults to 1. Start with a small value and adjust it to your
Bedrock account's request and token limits; local inference should use 1.
The script logs preparation and progress per method. It checks existing JSONL
rows against the selected source data and AST seed, skips completed methods,
and appends missing results to `.jsonl.tmp` checkpoints after interrupted
runs. Final files are ordered by `source_index`; a completed `paraphrase.jsonl`
is not modified when resuming the AST arms. If a provider call fails, rerun
the same command and output directory to resume. Keep the same seed and input
dataset for a resumed run. No model fine-tuning is performed by this command.

For a downstream comparison, use the same original training rows in all
arms; add only the generated rows of each respective method. Report both
actual augmentation yield and a size-matched comparison, because there are
more paraphrase-eligible examples than AST-eligible examples. Keep evaluation
on the untouched official development set and reserve test for the final run.

## Downstream fine-tuning data

The four arms and a held-out development input are prepared by
[`experiments/spider/prepare_finetuning.py`](../../experiments/spider/prepare_finetuning.py).
Each arm starts with all 7,000 rows of `train_spider.json`, in their original
order. Only the respective augmentation file contributes additional rows, all
from the 20 databases above. The selected custom schemas determine eligibility;
the model prompts use the complete Spider `tables.json` schemas, including
foreign-key links. The script validates source indices, original labels,
database membership, and consistency between the two AST arms, then writes a
manifest with counts and SHA-256 digests. It does not repair generated labels.

The training counts are 7,000 (original), 8,971 (+paraphrase), 8,030 (+AST),
and 8,030 (+AST and paraphrase). The untouched `dev.json` contains 1,034
examples from separate databases. Do not use it for training, checkpoint
selection, or repeated hyperparameter tuning. SQL planning during augmentation
did not validate useful answers or alignment between a generated question and
its SQL. An exploratory execution check on the 1,030 AST rows found 146 mutated
queries returning zero rows, versus 36 source queries returning zero rows on
the same databases; this is a *row-count diagnostic*, not a correctness score.
We retained these labels without manual curation. A paper should disclose this
check, the actual yield per arm, and the label-quality limitation.

See [the cluster runbook](../../experiments/spider/FINETUNING.md) for the
reproduction commands and training configuration.
