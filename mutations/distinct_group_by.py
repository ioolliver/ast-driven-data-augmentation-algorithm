from sqlglot import exp


def rewrite_distinct_as_group_by(node):
    if not isinstance(node, exp.Select):
        return node

    distinct = node.args.get("distinct")
    if (
        not isinstance(distinct, exp.Distinct)
        or distinct.args.get("on")
        or node.args.get("group")
        or node.args.get("having")
    ):
        return node

    grouping_expressions = []
    for projection in node.expressions:
        if isinstance(projection, exp.Alias):
            expression = projection.this
        else:
            expression = projection

        if not isinstance(expression, exp.Column):
            return node
        grouping_expressions.append(expression.copy())

    node.set("distinct", None)
    node.set("group", exp.Group(expressions=grouping_expressions))
    return node
