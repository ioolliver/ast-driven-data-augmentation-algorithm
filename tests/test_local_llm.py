import importlib
import unittest


def load_local_llm_module():
    from ast_augmentation import local_llm

    return importlib.reload(local_llm)


class LocalLLMTest(unittest.TestCase):
    def test_send_to_local_llm_removes_qwen_thinking_block(self):
        local_llm = load_local_llm_module()

        def fake_generator(model_input, **kwargs):
            return [
                {
                    "generated_text": (
                        f"{model_input}<think>\nI should reason internally.\n</think>\n"
                        "Resposta final"
                    )
                }
            ]

        local_llm._get_text_generator = lambda model_id, use_4bit: fake_generator
        local_llm._build_model_input = lambda prompt, model_id, use_4bit, enable_thinking: prompt

        response = local_llm.send_to_local_llm("Prompt SQL")

        self.assertEqual(response, "Resposta final")

    def test_strip_thinking_removes_closed_think_block(self):
        local_llm = load_local_llm_module()

        response = local_llm._strip_thinking("<think>\ninternal\n</think>\nFinal answer")

        self.assertEqual(response, "Final answer")


if __name__ == "__main__":
    unittest.main()
