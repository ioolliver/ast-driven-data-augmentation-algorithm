import sqlglot
from mutations import (
    mutate_between,
    mutate_enum,
    mutate_agg,
    mutate_threshold_shift,
    mutate_equivalent_column,
    mutate_value_group,
    mutate_binary,
    mutate_postgis,
)
from llm import adapt_query


def create_random_variation(schema, query, sql):
    changelog = []
    mutation_state = {}

    def mutate_operators(node):
        node = mutate_between(node, changelog, schema)
        node = mutate_enum(node, changelog, schema)
        node = mutate_agg(node, changelog, schema)
        node = mutate_threshold_shift(node, changelog, schema)
        node = mutate_equivalent_column(node, changelog, schema)
        node = mutate_value_group(node, changelog, schema)
        node = mutate_binary(node, changelog, schema)
        node = mutate_postgis(node, changelog, schema, mutation_state)
        return node

    ast = sqlglot.parse_one(sql, read="postgres")

    # Pass 1: column swaps first so operator mutations see the updated columns
    modified_ast = ast.transform(lambda n: mutate_equivalent_column(n, changelog, schema))
    # Pass 2: all remaining operator mutations
    modified_ast = modified_ast.transform(mutate_operators)

    sql_modified = modified_ast.sql(dialect="postgres", pretty=True)
    query_modified = adapt_query(query, sql, sql_modified, changelog)

    return (query_modified, sql_modified)
