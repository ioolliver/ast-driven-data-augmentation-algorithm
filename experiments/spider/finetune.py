"""Fine-tune one Spider arm with QLoRA; run inside the GPU Apptainer image."""

import argparse
import json
from pathlib import Path

ARMS = ("original", "paraphrase", "ast", "ast_paraphrase")
DEFAULT_MODEL = "Qwen/Qwen2.5-7B-Instruct"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--arm", choices=ARMS, required=True)
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Model ID or local snapshot directory")
    parser.add_argument("--model-revision", default=None, help="Pinned Hugging Face commit SHA for reproducibility")
    parser.add_argument("--max-length", type=int, default=2048)
    parser.add_argument("--epochs", type=float, default=2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--gradient-accumulation", type=int, default=16)
    parser.add_argument("--learning-rate", type=float, default=2e-4)
    parser.add_argument("--resume", action="store_true", help="Resume latest checkpoint of this arm")
    args = parser.parse_args()

    import torch
    from datasets import load_dataset
    from peft import LoraConfig, prepare_model_for_kbit_training
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from trl import SFTConfig, SFTTrainer

    if not torch.cuda.is_available() or not torch.cuda.is_bf16_supported():
        raise RuntimeError("This configuration requires a CUDA GPU with bfloat16 support")
    manifest = json.loads((args.data_dir / "manifest.json").read_text(encoding="utf-8"))
    data_path = args.data_dir / f"train_{args.arm}.jsonl"
    if not data_path.is_file():
        raise FileNotFoundError(data_path)
    dataset = load_dataset("json", data_files=str(data_path), split="train")
    if len(dataset) != manifest["counts"][args.arm]["total"]:
        raise ValueError("Training row count differs from preparation manifest")
    tokenizer = AutoTokenizer.from_pretrained(args.model, revision=args.model_revision)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    # TRL truncates from the right; that could erase the SQL answer. Fail explicitly.
    lengths = [len(tokenizer.apply_chat_template(row["prompt"] + row["completion"], tokenize=True))
               for row in dataset]
    longest = max(lengths)
    if longest > args.max_length:
        raise ValueError(f"{sum(n > args.max_length for n in lengths)} examples exceed "
                         f"--max-length {args.max_length} (maximum {longest}); raise the limit")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "run_config.json").write_text(json.dumps({
        "arm": args.arm, "model": args.model, "model_revision": args.model_revision, "seed": args.seed,
        "epochs": args.epochs, "max_length": args.max_length,
        "batch_size": args.batch_size, "gradient_accumulation": args.gradient_accumulation,
        "learning_rate": args.learning_rate, "examples": len(dataset),
        "longest_example_tokens": longest,
        "input_sha256": manifest["output_sha256"][data_path.name],
    }, indent=2) + "\n", encoding="utf-8")
    model = AutoModelForCausalLM.from_pretrained(
        args.model, revision=args.model_revision, torch_dtype=torch.bfloat16,
        device_map={"": torch.cuda.current_device()},
        quantization_config=BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                                              bnb_4bit_use_double_quant=True,
                                              bnb_4bit_compute_dtype=torch.bfloat16),
    )
    model.config.use_cache = False
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True,
                                             gradient_checkpointing_kwargs={"use_reentrant": False})
    trainer = SFTTrainer(
        model=model,
        processing_class=tokenizer,
        train_dataset=dataset,
        peft_config=LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05,
                               bias="none", task_type="CAUSAL_LM", target_modules="all-linear"),
        args=SFTConfig(
            output_dir=str(args.output_dir), seed=args.seed, data_seed=args.seed,
            max_length=args.max_length, completion_only_loss=True,
            per_device_train_batch_size=args.batch_size,
            gradient_accumulation_steps=args.gradient_accumulation,
            num_train_epochs=args.epochs, learning_rate=args.learning_rate,
            lr_scheduler_type="cosine", warmup_ratio=0.03,
            bf16=True, gradient_checkpointing=True,
            gradient_checkpointing_kwargs={"use_reentrant": False},
            optim="paged_adamw_8bit", logging_steps=25,
            save_strategy="epoch", save_total_limit=1,
            report_to="none", packing=False, remove_unused_columns=True,
        ),
    )
    trainer.train(resume_from_checkpoint=args.resume or None)
    trainer.save_model(str(args.output_dir / "adapter"))
    tokenizer.save_pretrained(str(args.output_dir / "adapter"))
    trainer.save_state()


if __name__ == "__main__":
    main()
