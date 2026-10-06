#!/bin/bash
#SBATCH --job-name=spider-sft
#SBATCH --array=0-3%1
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --time=24:00:00
#SBATCH --output=spider-sft-%A_%a.out

set -euo pipefail

: "${SPIDER_REPO:?Set SPIDER_REPO to the repository directory}"
: "${SPIDER_IMAGE:?Set SPIDER_IMAGE to the absolute .sif path}"
: "${SPIDER_DATA:?Set SPIDER_DATA to the prepared data directory}"
: "${SPIDER_OUTPUT:?Set SPIDER_OUTPUT to an output directory}"
: "${HF_HOME:?Set HF_HOME to a persistent model cache directory}"

arms=(original paraphrase ast ast_paraphrase)
arm="${arms[$SLURM_ARRAY_TASK_ID]}"
mkdir -p "$SPIDER_OUTPUT" "$HF_HOME"
extra_args=()
if [[ -n "${SPIDER_MODEL_REVISION:-}" ]]; then
    extra_args+=(--model-revision "$SPIDER_MODEL_REVISION")
fi

apptainer exec --nv \
    --bind "$SPIDER_REPO:$SPIDER_REPO,$SPIDER_DATA:$SPIDER_DATA,$SPIDER_OUTPUT:$SPIDER_OUTPUT,$HF_HOME:$HF_HOME" \
    --env "HF_HOME=$HF_HOME" \
    "$SPIDER_IMAGE" \
    python "$SPIDER_REPO/experiments/spider/finetune.py" \
        --data-dir "$SPIDER_DATA" --arm "$arm" \
        --output-dir "$SPIDER_OUTPUT/$arm" "${extra_args[@]}"
