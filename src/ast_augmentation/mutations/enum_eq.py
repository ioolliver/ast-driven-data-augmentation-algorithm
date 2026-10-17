import random
from sqlglot import exp
from ..schema_utils import get_col_info, get_table_name, string_literal_value


def mutate_enum(node, changelog, schema):
    if not isinstance(node, exp.EQ):
        return node

    for col_node, val_node in ((node.left, node.right), (node.right, node.left)):
        if not isinstance(col_node, exp.Column):
            continue
        table_name = get_table_name(col_node, schema)
        col_info = get_col_info(schema, table_name, col_node.name)
        if not col_info or col_info.get("type") != "enum":
            continue
        current_value = string_literal_value(val_node, schema)
        if current_value in {option["value"] for option in col_info["enums"]}:
            break
    else:
        return node
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

    return exp.EQ(this=col_node.copy(), expression=exp.Literal.string(str(new_value)))
