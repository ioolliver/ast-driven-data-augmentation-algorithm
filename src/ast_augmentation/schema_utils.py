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


def get_table_name(node):
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
