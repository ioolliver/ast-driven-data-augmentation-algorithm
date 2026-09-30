import random
from sqlglot import exp
from ..schema_utils import get_col_info, get_table_name


def mutate_equivalent_column(node, changelog, schema):
    if not isinstance(node, exp.Column):
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
    table_name = get_table_name(node)
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
