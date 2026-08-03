from sqlglot import exp

"""
Antes:

SELECT *
FROM escolas
WHERE numero_alunos BETWEEN 100 AND 500;

Depois:

SELECT *
FROM escolas
WHERE numero_alunos >= 100
AND numero_alunos <= 500;
"""

def rewrite_between_as_comparisons(node):
    if not isinstance(node, exp.Between):
        return node

    column = node.this
    lower_bound = node.args.get("low")
    upper_bound = node.args.get("high")
    if not (
        isinstance(column, exp.Column)
        and isinstance(lower_bound, exp.Literal)
        and isinstance(upper_bound, exp.Literal)
    ):
        return node

    lower_comparison = exp.GTE(
        this=column.copy(),
        expression=lower_bound.copy(),
    )
    upper_comparison = exp.LTE(
        this=column.copy(),
        expression=upper_bound.copy(),
    )
    comparisons = exp.and_(lower_comparison, upper_comparison)
    return exp.Paren(this=comparisons)
