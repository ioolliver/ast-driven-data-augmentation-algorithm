import random
from sqlglot import exp
from ..schema_utils import get_col_info, get_table_name, string_literal_value


def mutate_value_group(node, changelog, schema):
    if not isinstance(node, exp.In):
        return node

    col_node = node.this
    if not isinstance(col_node, exp.Column):
        return node

    col_name = col_node.name
    table_name = get_table_name(col_node, schema)
    col_info = get_col_info(schema, table_name, col_name)

    if not col_info or col_info.get("type") != "enum":
        return node

    groups = {}
    for enum_opt in col_info.get("enums", []):
        group = enum_opt.get("value_group")
        if group:
            groups.setdefault(group, []).append(enum_opt["value"])

    if not groups:
        return node

    expressions = node.args.get("expressions", [])
    values = [string_literal_value(e, schema) for e in expressions]
    # Never match only a literal subset of a mixed identifier/subquery list.
    if not values or any(value is None for value in values):
        return node
    current_values = {value.upper() for value in values}

    if not current_values:
        return node

    matched_group = next(
        (name for name, vals in groups.items() if current_values == {v.upper() for v in vals}),
        None,
    )

    if matched_group is None:
        return node

    available_targets = [g for g in groups if g != matched_group]
    if not available_targets:
        return node

    target_group = random.choice(available_targets)
    target_values = groups[target_group]

    labels = col_info.get("value_group_labels", {})
    col_sql = col_node.sql()
    old_vals_str = ", ".join(f"'{v}'" for v in groups[matched_group])
    new_vals_str = ", ".join(f"'{v}'" for v in target_values)

    changelog.append({
        "old_line": f"{col_sql} IN ({old_vals_str})",
        "new_line": f"{col_sql} IN ({new_vals_str})",
        "tip": f"Região alterada de '{labels.get(matched_group, matched_group)}' para '{labels.get(target_group, target_group)}'",
    })

    node.set("expressions", [exp.Literal.string(v) for v in target_values])
    return node
