import sqlglot
from mutations import (
    mutate_between,
    mutate_enum,
    mutate_agg,
    mutate_threshold_shift,
    mutate_equivalent_column,
    mutate_value_group,
    mutate_binary,
    mutate_text_pattern,
    mutate_distance_threshold,
    mutate_postgis,
    rewrite_between_as_comparisons,
    rewrite_distinct_as_group_by,
)
from llm import adapt_query, paraphrase_query


def _create_sql_variation(schema, sql):
    semantic_changelog = []
    mutation_state = {}

    def mutate_operators(node):
        node = mutate_between(node, semantic_changelog, schema)
        node = mutate_enum(node, semantic_changelog, schema)
        node = mutate_agg(node, semantic_changelog, schema)
        node = mutate_threshold_shift(node, semantic_changelog, schema)
        node = mutate_value_group(node, semantic_changelog, schema)
        node = mutate_binary(node, semantic_changelog, schema)
        node = mutate_text_pattern(node, semantic_changelog, schema)
        node = mutate_distance_threshold(
            node, semantic_changelog, schema, mutation_state
        )
        node = mutate_postgis(node, semantic_changelog, schema, mutation_state)
        return node

    def rewrite_equivalent_expressions(node):
        node = rewrite_distinct_as_group_by(node)
        node = rewrite_between_as_comparisons(node)
        return node

    ast = sqlglot.parse_one(sql, read="postgres")

    # Pass 1: column swaps first so operator mutations see the updated columns
    modified_ast = ast.transform(
        lambda n: mutate_equivalent_column(n, semantic_changelog, schema)
    )
    # Pass 2: all remaining operator mutations
    modified_ast = modified_ast.transform(mutate_operators)
    # Pass 3: structural rewrites preserve the semantics produced by the first passes
    modified_ast = modified_ast.transform(rewrite_equivalent_expressions)

    sql_modified = modified_ast.sql(dialect="postgres", pretty=True)
    return sql_modified, semantic_changelog


def create_paraphrase_only_variation(query, sql):
    return paraphrase_query(query), sql


def create_random_variation(schema, query, sql):
    sql_modified, semantic_changelog = _create_sql_variation(schema, sql)
    if not semantic_changelog:
        return (query, sql_modified)

    query_modified = adapt_query(query, sql, sql_modified, semantic_changelog)

    return (query_modified, sql_modified)


def create_random_variation_with_paraphrasing(schema, query, sql):
    sql_modified, semantic_changelog = _create_sql_variation(schema, sql)
    if not semantic_changelog:
        return (query, sql_modified)

    query_modified = adapt_query(
        query,
        sql,
        sql_modified,
        semantic_changelog,
        paraphrase=True,
    )

    return (query_modified, sql_modified)
