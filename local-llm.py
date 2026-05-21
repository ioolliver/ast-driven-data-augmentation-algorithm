import os
import re


DEFAULT_MODEL_ID = "Qwen/Qwen3.5-4B-Instruct"
DEFAULT_MAX_NEW_TOKENS = 512
DEFAULT_TEMPERATURE = 0.2
DEFAULT_TOP_P = 0.9
DEFAULT_ENABLE_THINKING = False

_TEXT_GENERATORS = {}


def _env_flag(name, default):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _load_transformers():
    try:
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            BitsAndBytesConfig,
            pipeline,
        )
    except ImportError as exc:
        raise RuntimeError(
            "Local LLM mode requires transformers, accelerate, torch, and bitsandbytes. "
            "In Colab, install them before calling send_to_local_llm."
        ) from exc

    return AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, pipeline


def _get_text_generator(model_id, use_4bit):
    cache_key = (model_id, use_4bit)
    if cache_key in _TEXT_GENERATORS:
        return _TEXT_GENERATORS[cache_key]

    AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, pipeline = _load_transformers()

    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    model_kwargs = {
        "device_map": "auto",
        "trust_remote_code": True,
    }

    if use_4bit:
        model_kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype="float16",
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
        )
    else:
        model_kwargs["torch_dtype"] = "auto"

    model = AutoModelForCausalLM.from_pretrained(model_id, **model_kwargs)
    generator = pipeline("text-generation", model=model, tokenizer=tokenizer)
    generator.tokenizer = tokenizer
    _TEXT_GENERATORS[cache_key] = generator
    return generator


def _strip_thinking(text):
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)

    if "<think>" not in text.lower():
        return text.strip()

    lines = []
    inside_thinking = False
    for line in text.splitlines():
        lower_line = line.lower()
        if "<think>" in lower_line:
            inside_thinking = True
            continue
        if "</think>" in lower_line:
            inside_thinking = False
            continue
        if not inside_thinking:
            lines.append(line)

    if lines:
        return "\n".join(lines).strip()

    return text.rsplit("<think>", 1)[-1].strip()


def _build_model_input(prompt, model_id, use_4bit, enable_thinking=DEFAULT_ENABLE_THINKING):
    generator = _get_text_generator(model_id, use_4bit)
    tokenizer = getattr(generator, "tokenizer", None)

    if tokenizer and getattr(tokenizer, "chat_template", None):
        kwargs = {
            "tokenize": False,
            "add_generation_prompt": True,
        }

        try:
            return tokenizer.apply_chat_template(
                [{"role": "user", "content": prompt}],
                enable_thinking=enable_thinking,
                **kwargs,
            )
        except TypeError:
            return tokenizer.apply_chat_template(
                [{"role": "user", "content": prompt}],
                **kwargs,
            )

    return prompt


def _extract_text(result):
    if isinstance(result, list) and result:
        item = result[0]
        if isinstance(item, dict):
            return item.get("generated_text", "")
        return str(item)

    if isinstance(result, dict):
        return result.get("generated_text", "")

    return str(result)


def send_to_local_llm(
    prompt,
    model_id=None,
    max_new_tokens=None,
    temperature=None,
    top_p=None,
    use_4bit=None,
    enable_thinking=None,
):
    """Run the adaptation prompt against a local Hugging Face text-generation model."""
    model_id = model_id or os.environ.get("LOCAL_LLM_MODEL", DEFAULT_MODEL_ID)
    max_new_tokens = max_new_tokens or int(
        os.environ.get("LOCAL_LLM_MAX_NEW_TOKENS", DEFAULT_MAX_NEW_TOKENS)
    )
    temperature = (
        temperature
        if temperature is not None
        else float(os.environ.get("LOCAL_LLM_TEMPERATURE", DEFAULT_TEMPERATURE))
    )
    top_p = (
        top_p
        if top_p is not None
        else float(os.environ.get("LOCAL_LLM_TOP_P", DEFAULT_TOP_P))
    )
    use_4bit = _env_flag("LOCAL_LLM_4BIT", True) if use_4bit is None else use_4bit
    enable_thinking = (
        _env_flag("LOCAL_LLM_THINKING", DEFAULT_ENABLE_THINKING)
        if enable_thinking is None
        else enable_thinking
    )

    model_input = _build_model_input(prompt, model_id, use_4bit, enable_thinking)
    generator = _get_text_generator(model_id, use_4bit)
    tokenizer = getattr(generator, "tokenizer", None)
    generator_kwargs = {
        "max_new_tokens": max_new_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "do_sample": temperature > 0,
        "return_full_text": True,
    }
    pad_token_id = getattr(tokenizer, "eos_token_id", None)
    if pad_token_id is not None:
        generator_kwargs["pad_token_id"] = pad_token_id

    result = generator(
        model_input,
        **generator_kwargs,
    )

    generated_text = _extract_text(result)
    if generated_text.startswith(model_input):
        generated_text = generated_text[len(model_input):]

    return _strip_thinking(generated_text)
