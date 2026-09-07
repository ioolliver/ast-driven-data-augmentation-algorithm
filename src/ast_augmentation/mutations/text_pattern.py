import random

from sqlglot import exp


PATTERN_CLASSES = (exp.Like, exp.ILike)
PATTERN_SHAPES = ("exact", "prefix", "suffix", "contains")
PATTERN_LABELS = {
    "exact": "igual a",
    "prefix": "inicia com",
    "suffix": "termina com",
    "contains": "contém",
}


def mutate_text_pattern(node, changelog, schema):
    if not isinstance(node, PATTERN_CLASSES):
        return node

    pattern_node = node.expression
    if not isinstance(pattern_node, exp.Literal) or not pattern_node.is_string:
        return node

    pattern = pattern_node.this
    parsed_pattern = _parse_simple_pattern(pattern)
    if not parsed_pattern:
        return node

    old_shape, value = parsed_pattern
    new_shape = random.choice([shape for shape in PATTERN_SHAPES if shape != old_shape])
    new_pattern = _format_pattern(value, new_shape)
    old_sql = node.sql(dialect="postgres")

    node.set("expression", exp.Literal.string(new_pattern))
    new_sql = node.sql(dialect="postgres")
    changelog.append({
        "old_line": old_sql,
        "new_line": new_sql,
        "tip": (
            f"Padrão textual alterado de '{PATTERN_LABELS[old_shape]}' "
            f"para '{PATTERN_LABELS[new_shape]}'"
        ),
    })
    return node


def _parse_simple_pattern(pattern):
    if not pattern or "_" in pattern or "\\" in pattern:
        return None

    starts_with_wildcard = pattern.startswith("%")
    ends_with_wildcard = pattern.endswith("%")
    start = 1 if starts_with_wildcard else 0
    end = -1 if ends_with_wildcard else None
    value = pattern[start:end]

    if not value or "%" in value:
        return None

    if starts_with_wildcard and ends_with_wildcard:
        return "contains", value
    if starts_with_wildcard:
        return "suffix", value
    if ends_with_wildcard:
        return "prefix", value
    return "exact", value


def _format_pattern(value, shape):
    if shape == "prefix":
        return f"{value}%"
    if shape == "suffix":
        return f"%{value}"
    if shape == "contains":
        return f"%{value}%"
    return value
