import importlib.util
import os
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DEFAULT_BEDROCK_MODEL = "anthropic.claude-sonnet-4-6"
BEDROCK_MODEL = os.environ.get("BEDROCK_MODEL", DEFAULT_BEDROCK_MODEL)


def format_changelog(changelog):
    return "\n".join(
        [
            f"- Changed from: `{change['old_line']}` -> To: `{change['new_line']}{(' - ' + change['tip']) if 'tip' in change else ''}`"
            for change in changelog
        ]
    )


def get_llm_prompt(query, sql, sql_modified, changelog, paraphrase=False):
    paraphrase_instruction = ""
    if paraphrase:
        paraphrase_instruction = (
            "Also paraphrase the question: do not merely replace the parts affected "
            "by the SQL changes. Rephrase its wording while preserving its meaning.\n"
        )

    return f"""
You will receive an original SQL query and an updated version of it. Your task is to adapt the query in natural language to match the new SQL changes.

# ORIGINAL SQL

{sql}

# ORIGINAL QUERY

{query}

---------

# NEW SQL

{sql_modified}

# SQL CHANGELOG

use the changelog below to help you know exactly what changed in the query.

{format_changelog(changelog)}

# TASK

{paraphrase_instruction}Return only the new query text. Make sure that the adapted text makes sense in the target language (PORTUGUESE). It must be a natural language question.

"""


def get_paraphrase_prompt(query):
    return f"""
Paraphrase the question below in Portuguese while preserving its exact meaning.
Do not add or remove filters, values, entities, or any other information.

# ORIGINAL QUESTION

{query}

# TASK

Return only the paraphrased question in Portuguese, without explanations or answers.
"""


LOCAL_LLM = os.environ.get("LOCAL_LLM", "").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
_LOCAL_LLM_MODULE = None


def _send_to_local_llm(prompt):
    global _LOCAL_LLM_MODULE

    if _LOCAL_LLM_MODULE is not None:
        return _LOCAL_LLM_MODULE.send_to_local_llm(prompt)

    module_path = Path(__file__).with_name("local-llm.py")
    spec = importlib.util.spec_from_file_location("local_llm", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _LOCAL_LLM_MODULE = module
    return module.send_to_local_llm(prompt)


def _send_to_bedrock(prompt):
    api_key = os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL")
    if not api_key or not base_url:
        raise RuntimeError(
            "Set OPENAI_API_KEY and OPENAI_BASE_URL for the Amazon Bedrock "
            "OpenAI-compatible endpoint."
        )

    parsed_base_url = urlparse(base_url)
    is_mantle_host = (
        parsed_base_url.hostname is not None
        and parsed_base_url.hostname.startswith("bedrock-mantle.")
        and parsed_base_url.hostname.endswith(".api.aws")
    )
    if not is_mantle_host or parsed_base_url.path.rstrip("/") != "/v1":
        raise RuntimeError(
            "OPENAI_BASE_URL must point to an Amazon Bedrock bedrock-mantle "
            "endpoint ending in /v1."
        )

    client = OpenAI(api_key=api_key, base_url=base_url)
    response = client.chat.completions.create(
        model=BEDROCK_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("Amazon Bedrock returned an empty model response.")
    return content


def send_to_llm(prompt):
    if LOCAL_LLM:
        return _send_to_local_llm(prompt)
    return _send_to_bedrock(prompt)


def paraphrase_query(query):
    return send_to_llm(get_paraphrase_prompt(query))


def adapt_query(query, sql, sql_modified, changelog, *, paraphrase=False):
    prompt = get_llm_prompt(
        query,
        sql,
        sql_modified,
        changelog,
        paraphrase=paraphrase,
    )
    return send_to_llm(prompt)
