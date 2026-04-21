from sqlglot import exp
from schema_utils import get_col_info, get_table_name


BINARY_LABELS = {0: "Não", 1: "Sim"}


def mutate_binary(node, changelog, schema):
    if not isinstance(node, exp.EQ):
        return node

    if isinstance(node.left, exp.Column):
        col_node, val_node = node.left, node.right
    elif isinstance(node.right, exp.Column):
        col_node, val_node = node.right, node.left
    else:
        return node

    if not isinstance(val_node, exp.Literal):
        return node

    col_name = col_node.name
    table_name = get_table_name(col_node)
    col_info = get_col_info(schema, table_name, col_name) or get_col_info(schema, None, col_name)

    if not col_info or col_info.get("type") != "binary":
        return node

    current_value = int(val_node.this)
    if current_value not in (0, 1):
        return node

    new_value = 1 - current_value
    col_sql = col_node.sql()

    changelog.append({
        "old_line": f"{col_sql} = {current_value} -- ({BINARY_LABELS[current_value]})",
        "new_line": f"{col_sql} = {new_value} -- ({BINARY_LABELS[new_value]})",
    })

    val_node.replace(exp.Literal.number(new_value))
    return node
