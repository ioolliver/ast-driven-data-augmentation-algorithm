from sqlglot import exp

"""
SELECT DISTINCT a.nome
  FROM alunos AS a
  JOIN matriculas AS m
    ON a.id_aluno = m.id_aluno
  WHERE a.ativo = 1

vira:

SELECT DISTINCT a.nome
FROM alunos AS a
WHERE a.ativo = 1
AND a.id_aluno IN (
    SELECT m.id_aluno
    FROM matriculas AS m
)
"""

_UNSUPPORTED_SELECT_CLAUSES = (
    "into",
    "operation_modifiers",
    "laterals",
    "connect",
    "pivots",
    "prewhere",
    "group",
    "having",
    "qualify",
    "windows",
    "distribute",
    "sort",
    "cluster",
    "order",
    "limit",
    "offset",
    "locks",
    "sample",
    "settings",
    "format",
    "options",
)


def rewrite_join_as_in_subquery(node):
    if not isinstance(node, exp.Select):
        return node

    distinct = node.args.get("distinct")
    joins = node.args.get("joins") or []
    from_clause = node.args.get("from_") or node.args.get("from")
    if (
        not isinstance(distinct, exp.Distinct)
        or distinct.args.get("on")
        or len(joins) != 1
        or not from_clause
        or not isinstance(from_clause.this, exp.Table)
        or any(node.args.get(clause) for clause in _UNSUPPORTED_SELECT_CLAUSES)
    ):
        return node

    join = joins[0]
    if (
        not isinstance(join.this, exp.Table)
        or join.args.get("side")
        or join.args.get("kind") not in (None, "INNER")
        or join.args.get("method")
        or join.args.get("using")
        or join.args.get("global_")
        or join.args.get("hint")
        or join.args.get("match_condition")
        or join.args.get("directed")
        or join.args.get("expressions")
        or join.args.get("pivots")
    ):
        return node

    primary_table = from_clause.this
    joined_table = join.this
    primary_alias = primary_table.alias_or_name
    joined_alias = joined_table.alias_or_name
    if not primary_alias or not joined_alias or primary_alias == joined_alias:
        return node

    join_columns = _get_join_columns(
        join.args.get("on"),
        primary_alias,
        joined_alias,
    )
    if not join_columns:
        return node
    primary_join_column, joined_join_column = join_columns

    if not _projects_only_primary_table_columns(node, primary_alias):
        return node

    where = node.args.get("where")
    if where and not _references_only_table(where, primary_alias):
        return node

    subquery = exp.select(joined_join_column.copy()).from_(joined_table.copy())
    membership = exp.In(
        this=primary_join_column.copy(),
        query=exp.Subquery(this=subquery),
    )

    rewritten = node.copy()
    rewritten.set("joins", [])
    if where:
        membership = exp.and_(where.this.copy(), membership)
    rewritten.set("where", exp.Where(this=membership))
    return rewritten


def _get_join_columns(on, primary_alias, joined_alias):
    if not isinstance(on, exp.EQ):
        return None

    left = on.this
    right = on.expression
    if not isinstance(left, exp.Column) or not isinstance(right, exp.Column):
        return None

    if left.table == primary_alias and right.table == joined_alias:
        return left, right
    if right.table == primary_alias and left.table == joined_alias:
        return right, left
    return None


def _projects_only_primary_table_columns(select, primary_alias):
    for projection in select.expressions:
        expression = (
            projection.this if isinstance(projection, exp.Alias) else projection
        )
        if not isinstance(expression, exp.Column) or expression.table != primary_alias:
            return False
    return bool(select.expressions)


def _references_only_table(expression, table_alias):
    if expression.find(exp.Subquery):
        return False
    return all(
        column.table == table_alias
        for column in expression.find_all(exp.Column)
    )
