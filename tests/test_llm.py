import importlib.util
import os
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


def load_llm_module():
    module_path = Path(__file__).resolve().parents[1] / "llm.py"
    spec = importlib.util.spec_from_file_location("llm_script", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RemoteLLMTest(unittest.TestCase):
    def test_send_to_llm_uses_bedrock_chat_completions(self):
        llm = load_llm_module()
        llm.LOCAL_LLM = False
        llm.BEDROCK_MODEL = "openai.gpt-oss-120b"
        captured = {}

        class FakeCompletions:
            def create(self, **kwargs):
                captured["completion"] = kwargs
                return SimpleNamespace(
                    choices=[
                        SimpleNamespace(
                            message=SimpleNamespace(content="Pergunta adaptada")
                        )
                    ]
                )

        class FakeOpenAI:
            def __init__(self, **kwargs):
                captured["client"] = kwargs
                self.chat = SimpleNamespace(completions=FakeCompletions())

        llm.OpenAI = FakeOpenAI
        with patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "bedrock-token",
                "OPENAI_BASE_URL": "https://bedrock-mantle.sa-east-1.api.aws/v1",
            },
        ):
            response = llm.send_to_llm("Prompt SQL")

        self.assertEqual(response, "Pergunta adaptada")
        self.assertEqual(
            captured["client"],
            {
                "api_key": "bedrock-token",
                "base_url": "https://bedrock-mantle.sa-east-1.api.aws/v1",
            },
        )
        self.assertEqual(
            captured["completion"],
            {
                "model": "openai.gpt-oss-120b",
                "messages": [{"role": "user", "content": "Prompt SQL"}],
            },
        )

    def test_send_to_llm_requires_bedrock_configuration(self):
        llm = load_llm_module()
        llm.LOCAL_LLM = False

        with patch.dict(
            os.environ, {"OPENAI_API_KEY": "", "OPENAI_BASE_URL": ""}, clear=False
        ):
            with self.assertRaisesRegex(
                RuntimeError, "OPENAI_API_KEY and OPENAI_BASE_URL"
            ):
                llm.send_to_llm("Prompt SQL")

    def test_send_to_llm_rejects_non_bedrock_mantle_endpoint(self):
        llm = load_llm_module()
        llm.LOCAL_LLM = False
        llm.OpenAI = lambda **kwargs: self.fail("client should not be created")

        with patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "wrong-provider-token",
                "OPENAI_BASE_URL": "https://api.openai.com/v1",
            },
        ):
            with self.assertRaisesRegex(RuntimeError, "bedrock-mantle"):
                llm.send_to_llm("Prompt SQL")


if __name__ == "__main__":
    unittest.main()
