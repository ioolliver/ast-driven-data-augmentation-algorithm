"""Generate Spider development SQL with one trained adapter (GPU required)."""

import argparse
import hashlib
import json
from pathlib import Path

from prepare_finetuning import ARMS, read_jsonl


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--runs-dir", type=Path, required=True)
    parser.add_argument("--arm", choices=ARMS, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--max-new-tokens", type=int, default=512)
    parser.add_argument("--limit", type=int, help="Use a separate output directory for a pilot")
    args = parser.parse_args()
    if args.batch_size < 1 or args.max_new_tokens < 1 or (args.limit is not None and args.limit < 1):
        parser.error("batch-size, max-new-tokens and limit must be positive")

    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    dev_path = args.data_dir / "dev.jsonl"
    manifest = json.loads((args.data_dir / "manifest.json").read_text(encoding="utf-8"))
    if sha256(dev_path) != manifest["output_sha256"]["dev.jsonl"]:
        raise ValueError("dev.jsonl differs from the preparation manifest")
    dev = list(read_jsonl(dev_path))
    if len(dev) != manifest["dev_examples"]:
        raise ValueError("Development row count differs from manifest")
    if args.limit is not None:
        dev = dev[:args.limit]
    run = json.loads((args.runs_dir / args.arm / "run_config.json").read_text(encoding="utf-8"))
    adapter = args.runs_dir / args.arm / "adapter"
    if run["arm"] != args.arm or run["input_sha256"] != manifest["output_sha256"][f"train_{args.arm}.jsonl"]:
        raise ValueError("Adapter run does not match this prepared dataset")
    if not (adapter / "adapter_model.safetensors").is_file():
        raise FileNotFoundError(f"Final adapter missing: {adapter}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    predictions_path = args.output_dir / "predictions.jsonl"
    config = {
        "arm": args.arm, "model": run["model"], "model_revision": run["model_revision"],
        "adapter": str(adapter.resolve()), "dev_sha256": sha256(dev_path),
        "examples": len(dev), "max_new_tokens": args.max_new_tokens,
    }
    config_path = args.output_dir / "prediction_config.json"
    if config_path.exists():
        if json.loads(config_path.read_text(encoding="utf-8")) != config:
            raise ValueError("Existing predictions use a different configuration or dataset")
    elif predictions_path.exists():
        raise ValueError("Predictions exist without prediction_config.json")
    else:
        config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

    existing = list(read_jsonl(predictions_path)) if predictions_path.exists() else []
    if len(existing) > len(dev):
        raise ValueError("Existing predictions exceed requested development rows")
    for index, prediction in enumerate(existing):
        if prediction.get("index") != index or prediction.get("db_id") != dev[index]["db_id"]:
            raise ValueError(f"Prediction mismatch at row {index}")
    print(f"{args.arm}: {len(existing)}/{len(dev)} predictions already saved", flush=True)
    if len(existing) == len(dev):
        return
    if not torch.cuda.is_available():
        raise RuntimeError("Inference requires a CUDA GPU")

    tokenizer = AutoTokenizer.from_pretrained(adapter, padding_side="left")
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        run["model"], revision=run["model_revision"], torch_dtype=torch.bfloat16,
        device_map={"": torch.cuda.current_device()},
        quantization_config=BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
        ),
    )
    model = PeftModel.from_pretrained(model, adapter)
    model.eval()
    model.config.use_cache = True

    with predictions_path.open("a", encoding="utf-8") as out, torch.inference_mode():
        for start in range(len(existing), len(dev), args.batch_size):
            batch = dev[start:start + args.batch_size]
            prompts = [tokenizer.apply_chat_template(row["prompt"], tokenize=False,
                                                      add_generation_prompt=True) for row in batch]
            inputs = tokenizer(prompts, padding=True, return_tensors="pt").to(model.device)
            generated = model.generate(**inputs, max_new_tokens=args.max_new_tokens,
                                       do_sample=False, pad_token_id=tokenizer.pad_token_id)
            prefix = inputs["input_ids"].shape[1]
            for index, row, tokens in zip(range(start, start + len(batch)), batch, generated):
                sql = tokenizer.decode(tokens[prefix:], skip_special_tokens=True).strip()
                out.write(json.dumps({"index": index, "db_id": row["db_id"],
                                      "prediction": sql}, ensure_ascii=False) + "\n")
            out.flush()
            print(f"{args.arm}: {min(start + len(batch), len(dev))}/{len(dev)}", flush=True)


if __name__ == "__main__":
    main()
