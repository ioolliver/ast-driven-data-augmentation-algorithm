"""Generate one augmented pair using the configured LLM backend."""

import sys

from ast_augmentation import create_random_variation


SCHEMA = {
    "tables": [
        {
            "name": "schools",
            "columns": [
                {"name": "name", "type": "string"},
                {
                    "name": "state",
                    "type": "enum",
                    "enums": [
                        {"value": "SP", "description": "São Paulo"},
                        {"value": "MG", "description": "Minas Gerais"},
                    ],
                },
            ],
        }
    ]
}
QUESTION = "Quais são os nomes das escolas no estado de São Paulo?"
SQL = "SELECT name FROM schools WHERE state = 'SP';"


def main():
    print("Original question:", QUESTION)
    print("Original SQL:", SQL)
    print()
    try:
        question, sql = create_random_variation(SCHEMA, QUESTION, SQL)
    except RuntimeError as exc:
        print(f"Augmentation failed: {exc}", file=sys.stderr)
        print("See docs/usage.md for backend setup.", file=sys.stderr)
        return 1

    print("Augmented question:", question)
    print("Augmented SQL:")
    print(sql)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
