import importlib
import os
import unittest
from types import SimpleNamespace
from unittest.mock import call, patch


def load_llm_module():
    from ast_augmentation import llm

    return importlib.reload(llm)


class RemoteLLMTest(unittest.TestCase):
    def test_paraphrase_prompt_preserves_meaning_and_requests_only_the_question(self):
        llm = load_llm_module()

        prompt = llm.get_paraphrase_prompt("Qual e o total de escolas?")

        self.assertIn("Qual e o total de escolas?", prompt)
        self.assertIn("preserving its exact meaning", prompt)
        self.assertIn("Return only the paraphrased question in Portuguese", prompt)

    def test_adaptation_and_paraphrase_use_sequential_llm_calls(self):
        llm = load_llm_module()
        changelog = [{"old_line": "SUM(valor)", "new_line": "AVG(valor)"}]
        adaptation_prompt = llm.get_llm_prompt(
            "What is the total?", "SELECT SUM(valor)", "SELECT AVG(valor)",
            changelog, language="English",
        )
        with patch.object(
            llm, "send_to_llm", side_effect=["What is the average?", "Give the mean."]
        ) as send:
            result = llm.adapt_query(
                "What is the total?", "SELECT SUM(valor)", "SELECT AVG(valor)",
                changelog, paraphrase=True, language="English",
            )

        self.assertEqual(result, "Give the mean.")
        self.assertNotIn("paraphrase", adaptation_prompt.lower())
        self.assertEqual(send.call_args_list, [
            call(adaptation_prompt),
            call(llm.get_paraphrase_prompt("What is the average?", language="English")),
        ])
        self.assertNotIn("What is the total?", send.call_args_list[1].args[0])

    def test_ast_only_uses_one_llm_call(self):
        llm = load_llm_module()
        with patch.object(llm, "send_to_llm", return_value="Pergunta adaptada") as send:
            result = llm.adapt_query("Original", "SELECT 1", "SELECT 2", [])
        self.assertEqual(result, "Pergunta adaptada")
        send.assert_called_once()

    def test_sequential_paraphrase_preserves_default_language(self):
        llm = load_llm_module()
        with patch.object(llm, "send_to_llm", side_effect=["Adaptada", "Reformulada"]) as send:
            result = llm.adapt_query("Original", "SELECT 1", "SELECT 2", [], paraphrase=True)
        self.assertEqual(result, "Reformulada")
        self.assertIn("(PORTUGUESE)", send.call_args_list[0].args[0])
        self.assertEqual(send.call_args_list[1], call(llm.get_paraphrase_prompt("Adaptada")))

    def test_adaptation_failure_does_not_start_paraphrasing(self):
        llm = load_llm_module()
        with patch.object(llm, "send_to_llm", side_effect=RuntimeError("adaptation failed")) as send:
            with self.assertRaisesRegex(RuntimeError, "adaptation failed"):
                llm.adapt_query("Original", "SELECT 1", "SELECT 2", [], paraphrase=True)
        send.assert_called_once()

    def test_paraphrase_failure_is_propagated(self):
        llm = load_llm_module()
        with patch.object(
            llm, "send_to_llm", side_effect=["Adaptada", RuntimeError("paraphrase failed")]
        ) as send:
            with self.assertRaisesRegex(RuntimeError, "paraphrase failed"):
                llm.adapt_query("Original", "SELECT 1", "SELECT 2", [], paraphrase=True)
        self.assertEqual(send.call_count, 2)

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
