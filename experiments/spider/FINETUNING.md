# Spider 1.0 four-arm fine-tuning

This prepares four independent Qwen2.5-7B-Instruct QLoRA adapters. Each training
file begins with the same 7,000 original Spider 1.0 `train_spider.json` pairs.
The added rows are restricted to the 20 databases in `datasets/spider/schemas.json`:

| Arm | Original | Added | Total |
| --- | ---: | ---: | ---: |
| `original` | 7,000 | 0 | 7,000 |
| `paraphrase` | 7,000 | 1,030 | 8,030 |
| `ast` | 7,000 | 1,030 | 8,030 |
| `ast_paraphrase` | 7,000 | 1,030 | 8,030 |

These are four *separate* arms. The paraphrase input has 1,971 rows, but only
the 1,030 whose `source_index` occurs in both AST arms are included. The other
941 paraphrases remain in the source file and are not used for training.
This matches both augmentation count and source-example selection without
random sampling. `ast_paraphrase` contains paraphrases of the AST-mutated
questions and their mutated SQL, not the union of the other two augmentation
files. All three augmented arms share the same source indices. Each pair
is represented as a conversational prompt/completion: a fixed system instruction,
full database schema from `tables.json`, a question, and its SQL answer.
Training computes loss only on the SQL completion. Inference must reproduce
the same prompt and use the model chat template with `add_generation_prompt=True`.

## Prepare data (CPU, no model download)

From the repository root, with the official archive extracted and the three
augmentation files in `raw_data/spider_aumento_final/`:

```bash
python experiments/spider/prepare_finetuning.py \
  raw_data/spider_data raw_data/spider_aumento_final raw_data/spider_sft
```

The output contains `train_original.jsonl`, `train_paraphrase.jsonl`,
`train_ast.jsonl`, `train_ast_paraphrase.jsonl`, `dev.jsonl`, and `manifest.json`.
`dev.jsonl` is an evaluation input with the gold SQL and `db_id` as metadata;
it is **never** passed to `SFTTrainer`. The manifest records source and output
hashes and counts for reproducibility. Re-run after changing any input.
It also records the 1,030 matched source indices and the 941 excluded
paraphrases. If `raw_data/spider_sft/` was generated before this change,
rerun this command to overwrite the old `train_paraphrase.jsonl` and manifest
before submitting any jobs; verify the counts printed by the command.
Keep these third-party data and generated pairs outside Git (`raw_data/` is
ignored). Transfer the prepared directory to the cluster alongside the code.

## Build and stage the image

Build `infra/spider_finetune.def` with Apptainer on a machine permitted to fetch
the Docker base image and Python packages. Cluster installations may require
`--fakeroot` or building elsewhere and copying the resulting `.sif`:

```bash
apptainer build spider_finetune.sif infra/spider_finetune.def
```

The image pins the training libraries; PyTorch 2.5.1 comes from its CUDA 12.4
base image. On the compute node, the NVIDIA driver must support that CUDA
runtime. Download the chosen base model once into a shared `HF_HOME` cache
before submitting the array, if the compute nodes lack network access. A local
model snapshot can be passed via `--model` when running `finetune.py` directly.
The model download is roughly 15 GB; check actual image, cache, checkpoints,
and available disk before submission. 150 GB should provide room for one shared
cache and four small adapters if the output does not duplicate base weights.

## Submit on SLURM

Use absolute paths visible inside Apptainer. Set the variables in the
submission shell so SLURM exports them:

```bash
export SPIDER_REPO="$PWD"
export SPIDER_IMAGE="/absolute/path/spider_finetune.sif"
export SPIDER_DATA="/absolute/path/spider_sft"
export SPIDER_OUTPUT="/absolute/path/spider_runs"
export HF_HOME="/absolute/path/hf_cache"
export SPIDER_MAX_LENGTH=3072
sbatch infra/spider_finetune.sbatch
```

Before submitting a GPU job, check all four arms on a login or CPU node
using the same image and tokenizer (no model weights are loaded):

```bash
for arm in original paraphrase ast ast_paraphrase; do
  apptainer exec \
    --bind "$SPIDER_REPO:$SPIDER_REPO,$SPIDER_DATA:$SPIDER_DATA,$HF_HOME:$HF_HOME" \
    --env "HF_HOME=$HF_HOME" "$SPIDER_IMAGE" \
    python "$SPIDER_REPO/experiments/spider/finetune.py" \
      --data-dir "$SPIDER_DATA" --arm "$arm" \
      --output-dir "$SPIDER_OUTPUT/$arm" \
      --max-length "$SPIDER_MAX_LENGTH" --check-only
done
```

Each arm prints its maximum length and count exceeding the limit. If any
arm reports an excess, set `SPIDER_MAX_LENGTH` higher and rerun this check
on all arms. Use the same passing limit for all four training jobs.

The array uses one GPU at a time (`--array=0-3%1`), 16 CPU cores, and 64 GB RAM.
For reproducibility, set `SPIDER_MODEL_REVISION` to the downloaded model's
commit SHA before submission; the script records this value per arm.
It requests 24 hours **per arm**; adjust the time to the cluster queue after a
pilot. Some installations require a partition, account, or GPU constraint; add
those SLURM directives locally. If a job is interrupted, rerun an arm directly
with `--resume` and its existing output directory, or edit the array script to
pass `--resume`. Inspect the emitted `run_config.json` and logs for each arm.

The default configuration uses 4-bit NF4 QLoRA, bfloat16 compute, LoRA rank 16,
effective batch size 16 (batch 1 × accumulation 16), 2 epochs, learning rate
2e-4, maximum sequence length 3,072, and seed 42. In the first 7,000-row
original run, 82 examples exceeded 2,048 tokens and the longest had 2,694;
therefore 2,048 cannot be used without discarding or truncating answers. The
same `SPIDER_MAX_LENGTH` should be used for all four runs. The script checks all examples
before training and fails if a prompt plus answer exceeds the token limit,
because truncation could remove the SQL target. Raise `SPIDER_MAX_LENGTH` if needed;
longer sequences use more VRAM. The 48 GB L40S is the target resource, but
runtime and peak memory must be confirmed with a short GPU pilot. Keep the base
model, training parameters, prompt, and seed identical across the four arms.

## Study limitations

This run uses all generated labels without manual curation. The generator
checked SQL planning but not semantic fidelity or whether SQL answers were
nonempty; source Spider labels also contain some empty-answer cases. An
exploratory execution check on the 1,030 AST pairs returned zero rows for 146
mutated SQL queries and 36 source queries; this does not assess question/SQL
alignment or count aggregate rows containing NULL as empty. Record this
limitation in a paper and describe any later audit separately. Matching
augmentation counts and source indices removes those two particular
confounders, but does not guarantee that the three methods produce examples
of equal quality or token length. Report the natural yields (1,971 versus
1,030) as well as the matched-budget training comparison. Keep `dev.json`
untouched for final evaluation across
held-out databases; do not train on `train_others.json` or development data.

## Evaluate on held-out Spider development databases

First confirm all four training runs have `adapter/adapter_model.safetensors`,
`adapter/adapter_config.json`, and `trainer_state.json` with epoch 2.0. The
train loss and token accuracy in those files are **not** development metrics.

With the same Apptainer image and base-model cache used for training, generate
one SQL prediction for each of the 1,034 development examples. These prompts
come from `dev.jsonl` and contain the schema and question, **not the gold SQL**.
Generation is deterministic (`do_sample=False`), uses up to 512 new tokens,
and saves each batch to a separate per-arm `predictions.jsonl`. Repeating a job
resumes completed rows after checking the input hash, order, and settings.

```bash
cd ~/ast-driven-data-augmentation-algorithm
export SPIDER_REPO="$PWD"
export SPIDER_IMAGE="$SPIDER_REPO/spider_finetune.sif"  # adjust to your actual .sif path
export SPIDER_DATA="$SPIDER_REPO/raw_data/spider_sft"
export SPIDER_OUTPUT="$SPIDER_REPO/raw_data/spider_runs_matched"
export SPIDER_EVAL_OUTPUT="$SPIDER_REPO/raw_data/spider_eval_matched"
export HF_HOME="$HOME/.cache/huggingface"  # use the cache from training
mkdir -p "$SPIDER_EVAL_OUTPUT/logs"
EVAL_JOB=$(sbatch --parsable --export=ALL --array=0-3%1 \
  --output="$SPIDER_EVAL_OUTPUT/logs/spider-eval-%A_%a.out" infra/spider_evaluate.sbatch)
echo "$EVAL_JOB" | tee -a "$SPIDER_EVAL_OUTPUT/logs/job_ids.txt"
```

Check `squeue -j "$EVAL_JOB"`, `sacct -j "$EVAL_JOB" --format=JobID,State,ExitCode,Elapsed`,
and the logs. If GPU memory is insufficient, rerun with
`export SPIDER_EVAL_BATCH_SIZE=1` and submit failed array indices; the saved
predictions can be continued with another batch size. A small pilot can use
`predict.py --limit 10` with a **different** output directory before the full
array. Do not score a pilot as the complete development set.

Export evaluator input files and a diagnostic literal SQL comparison:

```bash
for arm in original paraphrase ast ast_paraphrase; do
  python experiments/spider/evaluate_predictions.py \
    --data-dir "$SPIDER_DATA" \
    --prediction-dir "$SPIDER_EVAL_OUTPUT/$arm" \
    --output-dir "$SPIDER_EVAL_OUTPUT/scores/$arm"
done
```

The printed `literal_sql_match_rate` compares single-line SQL strings exactly.
It is more restrictive than Spider's **exact set match**, which parses and
compares SQL structure. For the official Spider scores, obtain the upstream
[test-suite-sql-eval](https://github.com/taoyds/test-suite-sql-eval) evaluator
in a separate directory, install its `sqlparse` and `nltk` dependencies, and
download its **Spider test suite databases** from the link in its README. Keep
the evaluator and test suites outside this repository. With `EVALUATOR` set to
the downloaded evaluator directory and `SUITE_DB` set to the test suite
`database/` directory containing the Spider database folders, run:

```bash
for arm in original paraphrase ast ast_paraphrase; do
  python "$EVALUATOR/evaluation.py" \
    --gold "$SPIDER_EVAL_OUTPUT/scores/$arm/gold.txt" \
    --pred "$SPIDER_EVAL_OUTPUT/scores/$arm/pred.txt" \
    --etype all --db "$SUITE_DB" \
    --table "$SPIDER_REPO/raw_data/spider_data/tables.json" \
    > "$SPIDER_EVAL_OUTPUT/scores/$arm/official.txt" 2>&1
done
```

The official report contains Spider exact set match and test-suite execution
accuracy. This model predicts condition values; **do not** use `--plug_value`,
which would supply gold values during scoring. Keep the default `DISTINCT`
handling for comparability with the original exact set match. If the test suite
is not installed yet, the older
[Spider evaluator](https://github.com/taoyds/spider) can score exact set match
and execution on the original Spider SQLite databases (`--etype all`, with
`--db "$SPIDER_REPO/raw_data/spider_data/database"`). Label that latter
execution metric **single-database execution**, rather than test-suite accuracy.
Keep all four evaluations on the same 1,034 examples and evaluator settings.
