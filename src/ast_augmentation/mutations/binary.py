from sqlglot import exp
from ..schema_utils import get_col_info, get_table_name, string_literal_value


BINARY_LABELS = {0: "Não", 1: "Sim"}


def mutate_binary(node, changelog, schema):
    if not isinstance(node, exp.EQ):
        return node

    for col_node, val_node in ((node.left, node.right), (node.right, node.left)):
        if not isinstance(col_node, exp.Column):
            continue
        table_name = get_table_name(col_node, schema)
        col_info = get_col_info(schema, table_name, col_node.name)
        if not col_info and not schema.get("case_insensitive_identifiers"):
            col_info = get_col_info(schema, None, col_node.name)
        if not col_info or col_info.get("type") not in ("binary", "boolean"):
            continue
        if isinstance(val_node, exp.Boolean):
            current_value = int(val_node.this)
        elif isinstance(val_node, exp.Literal) and val_node.is_number and val_node.this in ("0", "1"):
            current_value = int(val_node.this)
        else:
            value = string_literal_value(val_node, schema)
            if value not in ("0", "1"):
                continue
            current_value = int(value)
        break
    else:
        return node

    new_value = 1 - current_value
    old_sql = node.sql(dialect=schema.get("dialect", "postgres"))
    if isinstance(val_node, exp.Boolean):
        replacement = exp.Boolean(this=bool(new_value))
    elif isinstance(val_node, exp.Column) or val_node.is_string:
        replacement = exp.Literal.string(str(new_value))
    else:
        replacement = exp.Literal.number(new_value)
    val_node.replace(replacement)
    labels = {0: "No", 1: "Yes"} if schema.get("language") == "English" else BINARY_LABELS
    changelog.append({
        "old_line": f"{old_sql} -- ({labels[current_value]})",
        "new_line": f"{node.sql(dialect=schema.get('dialect', 'postgres'))} -- ({labels[new_value]})",
    })
    return node
