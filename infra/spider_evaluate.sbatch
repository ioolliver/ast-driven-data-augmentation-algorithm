#!/bin/bash
#SBATCH --job-name=spider-eval
#SBATCH --array=0-3%1
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=12:00:00
#SBATCH --output=spider-eval-%A_%a.out

set -euo pipefail
: "${SPIDER_REPO:?Set SPIDER_REPO to the repository directory}"
: "${SPIDER_IMAGE:?Set SPIDER_IMAGE to the absolute .sif path}"
: "${SPIDER_DATA:?Set SPIDER_DATA to the prepared data directory}"
: "${SPIDER_OUTPUT:?Set SPIDER_OUTPUT to the trained-adapter directory}"
: "${SPIDER_EVAL_OUTPUT:?Set SPIDER_EVAL_OUTPUT to a new prediction directory}"
: "${HF_HOME:?Set HF_HOME to the same cache used for training}"

arms=(original paraphrase ast ast_paraphrase)
arm="${arms[$SLURM_ARRAY_TASK_ID]}"
mkdir -p "$SPIDER_EVAL_OUTPUT" "$HF_HOME"
apptainer exec --nv \
    --bind "$SPIDER_REPO:$SPIDER_REPO,$SPIDER_DATA:$SPIDER_DATA,$SPIDER_OUTPUT:$SPIDER_OUTPUT,$SPIDER_EVAL_OUTPUT:$SPIDER_EVAL_OUTPUT,$HF_HOME:$HF_HOME" \
    --env "HF_HOME=$HF_HOME" "$SPIDER_IMAGE" \
    python "$SPIDER_REPO/experiments/spider/predict.py" \
        --data-dir "$SPIDER_DATA" --runs-dir "$SPIDER_OUTPUT" \
        --arm "$arm" --output-dir "$SPIDER_EVAL_OUTPUT/$arm" \
        --batch-size "${SPIDER_EVAL_BATCH_SIZE:-4}" \
        --max-new-tokens "${SPIDER_EVAL_MAX_NEW_TOKENS:-512}"
