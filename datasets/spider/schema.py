"""Reviewed Spider 1.0 metadata for the selected training databases."""

import json
from pathlib import Path


SCHEMAS = json.loads(Path(__file__).with_name("schemas.json").read_text(encoding="utf-8"))


def get_schema(db_id):
    """Return a fresh schema so a caller cannot mutate the shared catalog."""
    return json.loads(json.dumps(SCHEMAS[db_id]))
