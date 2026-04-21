import random
import sqlglot
from sqlglot import exp
from schema_utils import get_col_info, get_table_name


def mutate_enum(node, changelog, schema):
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
    col_info = get_col_info(schema, table_name, col_name)

    if not col_info or col_info.get("type") != "enum":
        return node

    current_value = val_node.this
    old_description = current_value
    available_enums = []

    for enum_opt in col_info["enums"]:
        if enum_opt["value"] == current_value:
            old_description = enum_opt.get("description", current_value)
        else:
            available_enums.append(enum_opt)

    if not available_enums:
        return node

    new_enum = random.choice(available_enums)
    new_value = new_enum["value"]
    new_description = new_enum.get("description", new_value)
    col_sql = col_node.sql()

    changelog.append({
        "old_line": f"{col_sql} = '{current_value}' -- ({old_description})",
        "new_line": f"{col_sql} = '{new_value}' -- ({new_description})",
    })

    return sqlglot.parse_one(f"{col_sql} = '{new_value}'", read="postgres")
