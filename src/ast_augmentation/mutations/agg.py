import random
from sqlglot import exp


AGGREGATORS = (exp.Sum, exp.Avg, exp.Min, exp.Max)


def mutate_agg(node, changelog, schema):
    if not isinstance(node, AGGREGATORS):
        return node

    old_sql = node.sql()
    current_type = type(node)

    args_copy = {
        k: v.copy() if hasattr(v, "copy") else v
        for k, v in node.args.items()
    }

    new_aggregator_class = random.choice([a for a in AGGREGATORS if a != current_type])
    new_node = new_aggregator_class(**args_copy)

    changelog.append({"old_line": old_sql, "new_line": new_node.sql()})

    return new_node
