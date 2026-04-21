import random
from sqlglot import exp
from schema_utils import get_col_info, get_table_name
from date_utils import random_date


INEQ_CLASSES = (exp.GT, exp.LT, exp.GTE, exp.LTE)


def mutate_threshold_shift(node, changelog, schema):
    if not isinstance(node, INEQ_CLASSES):
        return node

    if isinstance(node.left, exp.Column) and not isinstance(node.right, exp.Column):
        col_node = node.left
        is_right_literal = True
    elif isinstance(node.right, exp.Column) and not isinstance(node.left, exp.Column):
        col_node = node.right
        is_right_literal = False
    else:
        return node

    col_name = col_node.name
    table_name = get_table_name(col_node)
    col_info = get_col_info(schema, table_name, col_name)

    if not col_info or col_info.get("type") not in ("number", "date") or "min" not in col_info or "max" not in col_info:
        return node

    new_operator_class = random.choice([cls for cls in INEQ_CLASSES if not isinstance(node, cls)])

    if col_info["type"] == "number":
        new_val = random.randint(col_info["min"], col_info["max"])
        new_val_node = exp.Literal.number(str(new_val))
    else:
        new_date = random_date(col_info["min"], col_info["max"]).isoformat()
        new_val_node = exp.Literal.string(new_date)

    if is_right_literal:
        new_node = new_operator_class(this=col_node.copy(), expression=new_val_node)
    else:
        new_node = new_operator_class(this=new_val_node, expression=col_node.copy())

    changelog.append({"old_line": node.sql(), "new_line": new_node.sql()})

    return new_node
