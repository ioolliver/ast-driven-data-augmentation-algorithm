# Spider 1.0 full custom-schema catalog

`schemas.json` describes **all 206 released database IDs**, rather than the
historical 20-database augmentation pilot. This includes 140 main training
DBs, six additional `train_others` DBs, 20 development DBs and 40 test DBs.
These are database settings, not independently annotated semantic domains.
The Spider paper's 200 databases exclude the six additional DBs.

**Generation reads only `train_spider.json`: 7,000 examples from 140 DBs.**
Catalog coverage does not enable development/test augmentation or include
`train_others`. Evaluation questions and gold SQL were not used to curate
held-out metadata. Preserve held-out splits for evaluation.

## Metadata and curation

| Resource | Coverage |
| --- | ---: |
| Tables / columns | 1,056 / 5,288 |
| Reviewed semantic groups | 355 across 126 DBs |
| Columns with `semantic_group` | 929 |
| Text columns with observed enum alternatives | 1,724 |
| Numeric columns with observed integer bounds | 858 |
| Columns with exact ISO-day date ranges | 18 |
| Columns with reviewed enum value groups | 15 (44 value groups) |

Four parallel reviewers inspected the original table and column metadata;
additional review covered the 40 test schemas and ambiguous SQLite values.
`semantic_groups.json` records table-local related alternatives, such as
start/end dates, minimum/maximum temperatures, person-name components and
same-unit sports measurements. `curation_notes.json` gives a rationale for
every DB, including the 80 without safe column peers. Groups express
**different meaningful questions**, not SQL equivalence. Identifiers,
foreign keys, unrelated measures and ambiguous unit combinations are excluded.
A second review removed misleading pairs such as order status versus item
condition. No group was manufactured merely to cover a database.

`value_groups.json` and `value_group_notes.json` separately describe observed
categorical partitions, such as weekdays/weekends and countries by continent.
Labels state the intended interpretation (including Northern Hemisphere
meteorological seasons). These annotations activate the existing value-group
mutation only when an `IN` predicate exactly matches a configured group.

Enums contain complete observed non-null text domains with 2–64 values and
at most 120 characters per value. Larger/free-text domains remain strings.
Numeric thresholds use finite observed values rounded inward to integer
bounds, matching the current sampler. Previously reviewed bounds are
intersected with observed bounds, rather than expanded to include outliers.
Only exact `YYYY-MM-DD` columns receive date ranges; timestamps and mixed
representations remain strings. Primary/foreign keys and identifier-like
columns have no enum or range mutation metadata. Per-column `provenance`
records the source type, key status, profiling and reviewed bounds.

The schema is augmentation metadata, not a replacement for the complete DDL
in a model prompt. Observed ranges are not domain constraints: sparse numeric
intervals can still yield empty answers, and enumerated text need not be a
true closed category. Review final question–SQL labels before training.

## Rebuild from the original distribution

Get Spider 1.0 from the [official project](https://yale-lily.github.io/spider/).
No benchmark question files or SQLite databases are checked into this repo.
Extract outside Git or under ignored `raw_data/`. For full metadata coverage,
use the archive's `test_tables.json` (206 IDs) and arrange its SQLite files as
`database/<db_id>/<db_id>.sqlite`. Some distributions name that directory
`test_database`; rename/link it to `database` before the command below.

```bash
uv sync
uv run python experiments/spider/build_schemas.py raw_data/spider_data \
  --tables raw_data/spider_data/test_tables.json \
  --report raw_data/spider_schema_profile.json
```

The builder profiles SQLite read-only, applies the reviewed JSON annotations,
retains existing descriptions/reviewed bounds and reports missing databases
and profiling errors. It never invents values when a DB is unavailable.
The committed catalog was profiled against all 206 DBs with zero missing
files or profiling errors. `coverage.json` records source checksums, counts
and the training audit. Rebuilding with a different database release may
change observed domains; keep the source release fixed for a study.

## Offline training audit

```bash
uv run python experiments/spider/audit.py raw_data/spider_data \
  --seed 42 --output raw_data/spider_audit.json
uv run python experiments/spider/audit.py raw_data/spider_data \
  --seed 42 --without-semantic-groups \
  --output raw_data/spider_audit_without_groups.json
```

With seed 42, the full catalog changes 3,333/7,000 rows; 975 rows include a
column substitution. SQLite planning succeeds for 3,332. The sole failure is
`assets_maintenance`, source index 3153: the **source query also fails** because
`Ref_Company_Types` does not exist. The generator rejects this row before an
LLM call. No mutation-only planning failure was observed in this run.

Disabling semantic groups gives 2,781 changed/plannable rows. Both commands
consume a shared random stream differently, so this is a descriptive coverage
comparison, not a controlled downstream-effect estimate. Planning proves
neither useful result rows nor question–SQL alignment. No new LLM generation,
fine-tuning or downstream evaluation was performed for this catalog expansion.

## Generate new training arms

Configure the LLM as in [the usage guide](../../docs/usage.md). Generation makes
remote calls and may incur charges. Use a **new output directory** when
changing schemas; previous pilot checkpoints have a different selection.
Start with a small run:

```bash
uv run python experiments/spider/generate.py raw_data/spider_data \
  --output-dir raw_data/spider_full --limit 10
```

Review those labels, then use a fresh directory for a full run without
`--limit`. `--methods`, `--seed`, `--max-workers` and `--progress-every` retain
their existing behavior. AST and AST-plus-paraphrase share the same mutated
SQL per source example. Existing/checkpoint rows are checked before reuse;
keep the same seed, schemas and source data when resuming.

Prepare matched-budget fine-tuning data after all three generation methods
finish:

```bash
uv run python experiments/spider/prepare_finetuning.py \
  raw_data/spider_data raw_data/spider_full raw_data/spider_sft_full
```

All four arms start with the same 7,000 originals. Augmented arms add only
source indices shared by the AST arms and paraphrase. The preparation script
infers the run's DB scope from its complete paraphrase file, validates the
source pairs and emits actual counts/hashes in a manifest. Historical
20-database runs remain supported; their 1,030 added rows / 8,030 total rows
are historical results, not counts for this expanded catalog. See the
[training runbook](../../experiments/spider/FINETUNING.md) for configuration.

Spider is third-party material; the repository's MIT license does not
relicense its data or model weights. Cite the original Spider authors as well
as this project's [WTAG/SBBD paper](../../CITATION.cff).
