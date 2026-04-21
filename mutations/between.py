import random
import sqlglot
from sqlglot import exp
from schema_utils import get_col_info, get_table_name


def mutate_between(node, changelog, schema):
    if not isinstance(node, exp.Between):
        return node

    col_node = node.this
    if not isinstance(col_node, exp.Column):
        return node

    col_name = col_node.name
    table_name = get_table_name(col_node)
    col_info = get_col_info(schema, table_name, col_name)

    if not col_info or col_info["type"] != "number":
        return node

    min_val = col_info["min"]
    max_val = col_info["max"]

    values = sorted([random.randint(min_val, max_val), random.randint(min_val, max_val)])
    new_lower, new_upper = values[0], values[1]

    old_lower = node.args.get("low").sql()
    old_upper = node.args.get("high").sql()
    col_sql = col_node.sql()

    changelog.append({
        "old_line": f"{col_sql} BETWEEN {old_lower} AND {old_upper}",
        "new_line": f"{col_sql} BETWEEN {new_lower} AND {new_upper}",
    })

    return sqlglot.parse_one(f"{col_sql} BETWEEN {new_lower} AND {new_upper}", read="postgres")
