from sqlglot import exp


def get_col_info(schema, table_name, col_name):
    # Spider preserves mixed-case names in its catalog while its SQLite SQL
    # often spells unquoted names in lowercase. Keep PostgreSQL's default
    # case-sensitive schema metadata lookup unchanged.
    fold = schema.get("case_insensitive_identifiers", False)
    target_table = table_name.casefold() if fold and table_name else table_name
    target_column = col_name.casefold() if fold else col_name
    for table in schema.get("tables", []):
        table_name_in_schema = table["name"].casefold() if fold else table["name"]
        if target_table is None or table_name_in_schema == target_table:
            for column in table.get("columns", []):
                column_name_in_schema = column["name"].casefold() if fold else column["name"]
                if column_name_in_schema == target_column:
                    return column
    return None


def _legacy_table_name(node):
    table_name = node.table
    select_node = node.find_ancestor(exp.Select)

    if not table_name:
        from_clause = _get_from_clause(select_node)
        if from_clause:
            table_name = from_clause.this.name

    if select_node:
        sources = []
        from_clause = _get_from_clause(select_node)
        if from_clause:
            sources.append(from_clause.this)
        for join in select_node.args.get("joins", []):
            sources.append(join.this)

        for source in sources:
            if source.alias == table_name:
                return source.name
    return table_name


def _get_from_clause(select_node):
    if not select_node:
        return None
    return select_node.args.get("from_") or select_node.args.get("from")


def _sources(select):
    from_clause = _get_from_clause(select)
    return ([from_clause.this] if from_clause else []) + [
        join.this for join in select.args.get("joins", [])
    ]


def _cte_names(select):
    names = set()
    ancestor = select
    while ancestor is not None:
        with_clause = ancestor.args.get("with_")
        if with_clause:
            names.update(cte.alias_or_name.casefold() for cte in with_clause.expressions)
        ancestor = ancestor.parent
    return names


def _outer_select(select):
    # Derived tables and CTE definitions do not inherit ordinary FROM bindings.
    parent = select.parent
    if isinstance(parent, exp.CTE):
        return None
    if isinstance(parent, exp.Subquery) and isinstance(parent.parent, (exp.From, exp.Join)):
        return None
    return select.find_ancestor(exp.Select)


def _projection_alias(node, select):
    # ORDER BY/GROUP BY/HAVING can reference computed output aliases rather
    # than identically named base columns. Do not infer their lineage here.
    for expression in select.expressions:
        if isinstance(expression, exp.Alias) and expression.alias.casefold() == node.name.casefold():
            if not any(part is node for part in expression.this.walk()):
                return True
    return False


def get_table_name(node, schema=None):
    """Resolve Spider columns from visible sources; skip ambiguity/derived lineage.

    Metadata-free callers and case-sensitive research schemas retain the legacy
    lookup. A failed schema-aware resolution returns an empty name, not None:
    None intentionally means a global metadata search to get_col_info callers.
    """
    if not schema or not schema.get("case_insensitive_identifiers"):
        return _legacy_table_name(node)
    select = node.find_ancestor(exp.Select)
    tables = {table["name"].casefold(): table for table in schema.get("tables", [])}
    while select is not None:
        sources = _sources(select)
        ctes = _cte_names(select)
        if node.table:
            matches = [source for source in sources if source.alias_or_name.casefold() == node.table.casefold()]
            if matches:
                source = matches[0]
                if len(matches) != 1 or not isinstance(source, exp.Table) or source.name.casefold() in ctes:
                    return ""
                table = tables.get(source.name.casefold())
                if table and get_col_info(schema, table["name"], node.name):
                    return table["name"]
                return ""
        else:
            if _projection_alias(node, select):
                return ""
            candidates = []
            for source in sources:
                if not isinstance(source, exp.Table) or source.name.casefold() in ctes:
                    return ""
                table = tables.get(source.name.casefold())
                if table is None:
                    return ""
                if get_col_info(schema, table["name"], node.name):
                    candidates.append(table["name"])
            if candidates:
                return candidates[0] if len(candidates) == 1 else ""
        select = _outer_select(select)
    return ""


def string_literal_value(node, schema):
    """Read a string, guarding SQLite's double-quoted-string fallback.

    SQLGlot parses a double-quoted value as a column. Only opt-in SQLite schemas
    may reinterpret it, and known columns, aliases or unknown source lineage
    take precedence over the legacy string interpretation.
    """
    if isinstance(node, exp.Literal) and node.is_string:
        return node.this
    if not (schema.get("sqlite_double_quoted_literals") and isinstance(node, exp.Column)
            and not node.table and node.this.args.get("quoted")):
        return None
    select = node.find_ancestor(exp.Select)
    if select is None:
        if any(column["name"].casefold() == node.name.casefold()
               for table in schema.get("tables", []) for column in table.get("columns", [])):
            return None
    while select is not None:
        if _projection_alias(node, select):
            return None
        ctes = _cte_names(select)
        for source in _sources(select):
            if not isinstance(source, exp.Table) or source.name.casefold() in ctes:
                return None
            table = next((table for table in schema.get("tables", [])
                          if table["name"].casefold() == source.name.casefold()), None)
            if table is None or any(column["name"].casefold() == node.name.casefold()
                                    for column in table.get("columns", [])):
                return None
        select = _outer_select(select)
    return node.name
