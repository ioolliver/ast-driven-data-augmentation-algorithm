import random
from sqlglot import exp
from ..schema_utils import get_col_info, get_table_name


def mutate_enum(node, changelog, schema):
    if not isinstance(node, exp.EQ):
        return node

    if isinstance(node.left, exp.Column):
        col_node, val_node = node.left, node.right
    elif isinstance(node.right, exp.Column):
        col_node, val_node = node.right, node.left
    else:
        return node

    col_name = col_node.name
    table_name = get_table_name(col_node)
    col_info = get_col_info(schema, table_name, col_name)

    if not col_info or col_info.get("type") != "enum":
        return node

    if isinstance(val_node, exp.Literal) and val_node.is_string:
        current_value = val_node.this
    elif (
        schema.get("sqlite_double_quoted_literals")
        and isinstance(val_node, exp.Column)
        and not val_node.table
        and val_node.this.args.get("quoted")
    ):
        # Spider uses SQLite's legacy double-quoted string syntax. sqlglot
        # parses these as identifiers; accept only known values for this enum.
        current_value = val_node.name
    else:
        return node
    if current_value not in {option["value"] for option in col_info["enums"]}:
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
