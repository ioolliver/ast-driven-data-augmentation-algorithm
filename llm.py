import os
from dotenv import load_dotenv
import google.genai as genai

load_dotenv()


def format_changelog(changelog):
    return "\n".join([
        f"- Changed from: `{change['old_line']}` -> To: `{change['new_line']}{(' - ' + change['tip']) if 'tip' in change else ''}`"
        for change in changelog
    ])


def get_llm_prompt(query, sql, sql_modified, changelog):
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

Return only the new query text. Make sure that the adapted text makes sense in the portuguese language.

"""


def send_to_llm(prompt):
    api_key = os.environ.get("GEMINI_KEY")
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-preview", contents=prompt
    )
    return response.text


def adapt_query(query, sql, sql_modified, changelog):
    prompt = get_llm_prompt(query, sql, sql_modified, changelog)
    return send_to_llm(prompt)
