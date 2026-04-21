from sqlglot import exp


def get_col_info(schema, table_name, col_name):
    for table in schema.get("tables", []):
        if not table_name or table["name"] == table_name:
            for column in table.get("columns", []):
                if column["name"] == col_name:
                    return column
    return None


def get_table_name(node):
    table_name = node.table
    if not table_name:
        select_node = node.find_ancestor(exp.Select)
        if select_node and select_node.args.get("from"):
            table_name = select_node.args["from"].this.name

    select_node = node.find_ancestor(exp.Select)
    if select_node:
        sources = []
        from_clause = select_node.args.get("from")
        if from_clause:
            sources.append(from_clause.this)
        for join in select_node.args.get("joins", []):
            sources.append(join.this)

        for source in sources:
            if source.alias == table_name:
                return source.name
    return table_name
