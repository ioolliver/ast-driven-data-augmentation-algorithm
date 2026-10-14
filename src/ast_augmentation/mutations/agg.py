import random
from sqlglot import exp
from ..schema_utils import get_col_info, get_table_name


AGGREGATORS = (exp.Sum, exp.Avg, exp.Min, exp.Max)


def mutate_agg(node, changelog, schema):
    if not isinstance(node, AGGREGATORS):
        return node

    old_sql = node.sql()
    current_type = type(node)

    choices = AGGREGATORS
    if schema.get("restrict_aggregates"):
        argument = node.this
        if isinstance(argument, exp.Column):
            info = get_col_info(schema, get_table_name(argument), argument.name)
            if not info or info.get("type") != "number":
                choices = (exp.Min, exp.Max)
        elif not (isinstance(argument, exp.Literal) and argument.is_number):
            return node

    alternatives = [a for a in choices if a != current_type]
    if current_type not in choices or not alternatives:
        return node

    args_copy = {
        k: v.copy() if hasattr(v, "copy") else v
        for k, v in node.args.items()
    }

    new_aggregator_class = random.choice(alternatives)
    new_node = new_aggregator_class(**args_copy)

    changelog.append({"old_line": old_sql, "new_line": new_node.sql()})

    return new_node
