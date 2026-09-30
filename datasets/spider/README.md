# Spider 1.0 augmentation pilot

This pilot selects eight **training databases** from the official Spider 1.0
archive: `hr_1`, `bike_1`, `movie_1`, `soccer_2`, `college_2`, `wine_1`,
`manufactory_1`, and `dorm_1`. Together they have 864 original question–SQL
rows (about 429 distinct SQL strings). The selection covers eight database
settings, not a claim of eight independently labeled semantic domains.

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

`schemas.json` contains 47 curated columns across the eight databases. Values
for enum alternatives came from the corresponding SQLite files. Numeric
bounds were reviewed against the data, with the anomalous wine year 2066
excluded from the configured range. We intentionally omitted identifiers,
foreign keys and uncertain cross-column substitutions. This metadata is for
*semantic augmentation* and is not a replacement for the full table schema
that a downstream Text-to-SQL model will receive.

## Offline audit

From the repository root after `uv sync`:

```bash
uv run python experiments/spider/audit.py raw_data/spider_data
```

With seed 42, 468/864 examples had a semantic change, and all 468 generated
SQL strings passed SQLite `EXPLAIN QUERY PLAN` using their own databases.
The other 396 are ineligible under this conservative configuration and must
not be counted as new AST examples. Planning a SQL statement proves neither
that it returns useful rows nor that the adapted question is aligned with it.
Review a sample of final LLM outputs before fine-tuning.

## Generate the three arms

Configure the LLM as described in [the usage guide](../../docs/usage.md).
The generation command makes remote LLM calls and can incur charges. For a
small pilot, use a fresh output directory:

```bash
uv run python experiments/spider/generate.py raw_data/spider_data \
  --output-dir raw_data/spider_pilot --limit 10
```

Omit `--limit` for the selected training subset. The script emits separate
JSONL files for `paraphrase`, `ast`, and `ast_paraphrase`. Each line has the
source index and database ID, original pair, method, and generated pair.
The AST and AST-plus-paraphrase arms share the **same mutated SQL** for each
source example. SQL that fails SQLite planning is skipped before an LLM call.
Use `--methods` to select arms, `--seed` to choose a mutation seed, and a new
output directory for every run. Files are written first with a `.tmp` suffix
and renamed when an arm finishes; a provider error leaves the current arm
incomplete for inspection. No model fine-tuning is performed by this command.

For a downstream comparison, use the same original training rows in all
arms; add only the generated rows of each respective method. Report both
actual augmentation yield and a size-matched comparison, because there are
more paraphrase-eligible examples than AST-eligible examples. Keep evaluation
on the untouched official development set and reserve test for the final run.
