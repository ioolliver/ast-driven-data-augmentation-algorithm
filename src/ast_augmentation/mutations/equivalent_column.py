import random
from sqlglot import exp
from ..schema_utils import get_col_info, get_table_name


def _spider_column_context_is_safe(node, schema):
    """Keep column-role changes away from value domains and grouping keys."""
    ancestor = node.parent
    select = None
    while ancestor is not None:
        if isinstance(ancestor, exp.Select):
            select = ancestor
            break
        if isinstance(ancestor, (
            exp.Where, exp.Having, exp.Join, exp.Predicate,
            exp.Add, exp.Sub, exp.Mul, exp.Div, exp.Mod,
        )):
            return False
        ancestor = ancestor.parent

    # Each occurrence is transformed independently. Replacing only a projected
    # occurrence of a GROUP BY key would detach it from its grouping expression.
    group = select.args.get("group") if select is not None else None
    if group is not None:
        fold = schema.get("case_insensitive_identifiers", False)
        name = node.name.casefold() if fold else node.name
        if any(
            (column.name.casefold() if fold else column.name) == name
            for column in group.find_all(exp.Column)
        ):
            return False
    return True


def mutate_equivalent_column(node, changelog, schema):
    if not isinstance(node, exp.Column):
        return node

    spider_sql = schema.get("sqlite_double_quoted_literals", False)
    if spider_sql and not _spider_column_context_is_safe(node, schema):
        return node

    parent = node.parent
    if isinstance(parent, exp.EQ) and isinstance(parent.left, exp.Column) and isinstance(parent.right, exp.Column):
        return node
    # A replacement column would retain a literal from the old value domain.
    # This can produce syntactically valid but nonsensical Spider examples.
    if isinstance(parent, (exp.EQ, exp.NEQ)) and (
        isinstance(parent.left, exp.Literal) or isinstance(parent.right, exp.Literal)
    ):
        return node
    if isinstance(parent, (exp.In, exp.Like, exp.ILike, exp.Add, exp.Sub, exp.Mul, exp.Div)):
        return node

    col_name = node.name
    table_name = get_table_name(node, schema)
    col_info = get_col_info(schema, table_name, col_name)

    if not col_info or "semantic_group" not in col_info:
        return node

    semantic_group = col_info["semantic_group"]
    case_insensitive = schema.get("case_insensitive_identifiers", False)
    same = (lambda a, b: a.casefold() == b.casefold()) if case_insensitive else (lambda a, b: a == b)
    peer_columns = [
        c
        for table in schema.get("tables", [])
        if table_name and same(table["name"], table_name)
        for c in table.get("columns", [])
        if c.get("semantic_group") == semantic_group and not same(c["name"], col_name)
    ]

    if spider_sql:
        ancestor = node.parent
        while ancestor is not None and not isinstance(ancestor, exp.Select):
            if isinstance(ancestor, (exp.Sum, exp.Avg)):
                if col_info.get("type") != "number":
                    return node
                peer_columns = [c for c in peer_columns if c.get("type") == "number"]
                break
            ancestor = ancestor.parent

    if not peer_columns:
        return node

    new_col_info = random.choice(peer_columns)
    new_col_name = new_col_info["name"]

    changelog.append({
        "old_line": f"Coluna: {col_name} -- ({col_info.get('description', col_name)})",
        "new_line": f"Coluna: {new_col_name} -- ({new_col_info.get('description', new_col_name)})",
    })

    node.set("this", exp.to_identifier(new_col_name))
    return node
