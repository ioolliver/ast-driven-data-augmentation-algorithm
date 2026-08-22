import json
import tempfile
import unittest
from pathlib import Path


from benchmark.inference import load_inference_context, tokenize_for_inference


class BenchmarkInferenceTest(unittest.TestCase):
    def test_loads_only_completed_experiments_with_an_adapter(self):
        with tempfile.TemporaryDirectory() as directory:
            experiment = Path(directory)
            (experiment / "adapter").mkdir()
            (experiment / "run_manifest.json").write_text(
                json.dumps(
                    {
                        "status": "complete",
                        "model": {
                            "id": "Qwen/Qwen3.5-9B",
                            "revision": "main",
                            "resolved_revision": "model-commit-sha",
                        },
                    }
                ),
                encoding="utf-8",
            )
            (experiment / "effective_config.yaml").write_text(
                "quantization:\n  load_in_4bit: true\n"
                "generation:\n  max_new_tokens: 32\n",
                encoding="utf-8",
            )
            (experiment / "schema.json").write_text(
                json.dumps(
                    {
                        "tables": [
                            {
                                "name": "items",
                                "columns": [{"name": "id", "type": "number"}],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            context = load_inference_context(experiment)

        self.assertEqual(context.model_id, "Qwen/Qwen3.5-9B")
        self.assertEqual(context.model_revision, "model-commit-sha")
        self.assertIn("items(id:number)", context.schema_text)
        self.assertEqual(context.max_new_tokens, 32)

    def test_requests_the_qwen_non_thinking_chat_template(self):
        class FakeBatch(dict):
            def to(self, device):
                self["device"] = device
                return self

        class FakeTokenizer:
            def __init__(self):
                self.kwargs = None

            def apply_chat_template(self, messages, **kwargs):
                self.kwargs = kwargs
                return FakeBatch(input_ids=[[1, 2, 3]])

        tokenizer = FakeTokenizer()

        inputs = tokenize_for_inference(
            tokenizer,
            [{"role": "user", "content": "Pergunta"}],
            device="cuda:0",
        )

        self.assertFalse(tokenizer.kwargs["enable_thinking"])
        self.assertTrue(tokenizer.kwargs["add_generation_prompt"])
        self.assertEqual(inputs["device"], "cuda:0")


if __name__ == "__main__":
    unittest.main()
