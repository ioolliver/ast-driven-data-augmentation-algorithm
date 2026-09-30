import unittest
from unittest.mock import patch

from ast_augmentation import create_paraphrase_only_variation, create_random_variation
from ast_augmentation.llm import get_llm_prompt, get_paraphrase_prompt


class SpiderConfigurationTest(unittest.TestCase):
    def test_english_question_generation_and_sqlite_dialect(self):
        schema = {
            "dialect": "sqlite",
            "language": "English",
            "case_insensitive_identifiers": True,
            "tables": [{
                "name": "Movie",
                "columns": [{
                    "name": "director", "type": "enum",
                    "enums": [
                        {"value": "Steven Spielberg", "description": "Steven Spielberg"},
                        {"value": "James Cameron", "description": "James Cameron"},
                    ],
                }],
            }],
        }
        with patch("ast_augmentation.augmentor.adapt_query", return_value="Cameron movies") as adapt:
            question, sql = create_random_variation(
                schema,
                "Which movies did Steven Spielberg direct?",
                "SELECT title FROM movie WHERE director = 'Steven Spielberg'",
            )
        self.assertEqual(question, "Cameron movies")
        self.assertIn("James Cameron", sql)
        self.assertEqual(adapt.call_args.kwargs, {"language": "English"})

    def test_unknown_source_enum_value_is_not_mutated(self):
        schema = {"dialect": "sqlite", "tables": [{
            "name": "Movie", "columns": [{
                "name": "director", "type": "enum",
                "enums": [{"value": "A"}, {"value": "B"}],
            }],
        }]}
        with patch("ast_augmentation.augmentor.adapt_query") as adapt:
            question, sql = create_random_variation(
                schema, "Unknown director", "SELECT title FROM Movie WHERE director = 'C'"
            )
        self.assertEqual(question, "Unknown director")
        self.assertIn("director = 'C'", sql)
        adapt.assert_not_called()

    def test_english_paraphrase_prompt(self):
        self.assertIn("in English", get_paraphrase_prompt("Original", language="English"))
        self.assertIn("(ENGLISH)", get_llm_prompt("Q", "SQL", "SQL2", [], language="English"))
        with patch("ast_augmentation.augmentor.paraphrase_query", return_value="Paraphrased") as fn:
            create_paraphrase_only_variation("Original", "SELECT 1", language="English")
        fn.assert_called_once_with("Original", language="English")


if __name__ == "__main__":
    unittest.main()
