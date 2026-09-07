import contextlib
import io
import os
from pathlib import Path
import runpy
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from ast_augmentation import llm


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "basic_usage.py"


class BasicUsageTest(unittest.TestCase):
    def test_example_transforms_sql_and_passes_changelog_to_llm(self):
        question = "Quais são os nomes das escolas no estado de Minas Gerais?"
        output = io.StringIO()
        response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=question))]
        )
        with patch.object(llm, "LOCAL_LLM", False), patch.object(
            llm, "OpenAI"
        ) as client, patch.dict(os.environ, {
            "OPENAI_API_KEY": "test-token",
            "OPENAI_BASE_URL": "https://bedrock-mantle.us-east-1.api.aws/v1",
        }), contextlib.redirect_stdout(output):
            client.return_value.chat.completions.create.return_value = response
            with self.assertRaises(SystemExit) as exit_context:
                runpy.run_path(str(EXAMPLE), run_name="__main__")

        self.assertEqual(exit_context.exception.code, 0)
        completion = client.return_value.chat.completions.create
        completion.assert_called_once()
        prompt = completion.call_args.kwargs["messages"][0]["content"]
        self.assertIn("SQL CHANGELOG", prompt)
        self.assertIn("Minas Gerais", prompt)
        self.assertIn("state = 'MG'", prompt)
        self.assertIn("Augmented question: " + question, output.getvalue())
        self.assertIn("state = 'MG'", output.getvalue())
        self.assertIn("state = 'SP'", output.getvalue())

    def test_direct_script_reports_missing_credentials_without_network(self):
        env = os.environ.copy()
        env.update(OPENAI_API_KEY="", OPENAI_BASE_URL="", LOCAL_LLM="false")
        # A blank variable is not overwritten by a local .env file.
        result = subprocess.run(
            [sys.executable, str(EXAMPLE)],
            cwd=ROOT, env=env, capture_output=True, text=True, timeout=20,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("OPENAI_API_KEY and OPENAI_BASE_URL", result.stderr)
        self.assertIn("docs/usage.md", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_research_model_is_default_but_can_be_overridden(self):
        from test_llm import load_llm_module

        with patch("dotenv.load_dotenv"), patch.dict(os.environ, {}, clear=True):
            self.assertEqual(load_llm_module().BEDROCK_MODEL, "openai.gpt-oss-120b")
        with patch("dotenv.load_dotenv"), patch.dict(
            os.environ, {"BEDROCK_MODEL": "another-model"}, clear=True
        ):
            self.assertEqual(load_llm_module().BEDROCK_MODEL, "another-model")


if __name__ == "__main__":
    unittest.main()
