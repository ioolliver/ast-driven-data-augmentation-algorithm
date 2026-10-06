# Spider 1.0 four-arm fine-tuning

This prepares four independent Qwen2.5-7B-Instruct QLoRA adapters. Each training
file begins with the same 7,000 original Spider 1.0 `train_spider.json` pairs.
The added rows are restricted to the 20 databases in `datasets/spider/schemas.json`:

| Arm | Original | Added | Total |
| --- | ---: | ---: | ---: |
| `original` | 7,000 | 0 | 7,000 |
| `paraphrase` | 7,000 | 1,971 | 8,971 |
| `ast` | 7,000 | 1,030 | 8,030 |
| `ast_paraphrase` | 7,000 | 1,030 | 8,030 |

These are four *separate* arms. `ast_paraphrase` contains paraphrases of the
AST-mutated questions and their mutated SQL, not the union of the other two
augmentation files. The AST arms share their SQL and source indices. Each pair
is represented as a conversational prompt/completion: a fixed system instruction,
full database schema from `tables.json`, a question, and its SQL answer.
Training computes loss only on the SQL completion. Inference must reproduce
the same prompt and use the model chat template with `add_generation_prompt=True`.

## Prepare data (CPU, no model download)

From the repository root, with the official archive extracted and the three
augmentation files in `raw_data/spider_generated/`:

```bash
python experiments/spider/prepare_finetuning.py \
  raw_data/spider_data raw_data/spider_generated raw_data/spider_sft
```

The output contains `train_original.jsonl`, `train_paraphrase.jsonl`,
`train_ast.jsonl`, `train_ast_paraphrase.jsonl`, `dev.jsonl`, and `manifest.json`.
`dev.jsonl` is an evaluation input with the gold SQL and `db_id` as metadata;
it is **never** passed to `SFTTrainer`. The manifest records source and output
hashes and counts for reproducibility. Re-run after changing any input.
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
sbatch infra/spider_finetune.sbatch
```

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
2e-4, maximum sequence length 2,048, and seed 42. The script checks all examples
before training and fails if a prompt plus answer exceeds the token limit,
because truncation could remove the SQL target. Raise `--max-length` if needed;
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
limitation in a paper and describe any later audit separately. The arms differ
in size, so a performance difference cannot by itself isolate augmentation
*method* from added example count. Report the natural-yield comparison and
consider a prespecified size-matched follow-up using exactly 1,030 generated
rows per nonbaseline arm. Keep `dev.json` untouched for final evaluation across
held-out databases; do not train on `train_others.json` or development data.
