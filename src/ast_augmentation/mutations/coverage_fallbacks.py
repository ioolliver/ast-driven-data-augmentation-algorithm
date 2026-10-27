"""One additional mutation when the primary pipeline has no semantic change.

Enabled explicitly through coverage_fallbacks schema metadata. These rules do
not loosen column-role, join, grouping, or identifier-resolution guards.
"""
from decimal import Decimal, InvalidOperation
import random

from sqlglot import exp

from ..schema_utils import get_col_info, get_table_name
from .enum_eq import mutate_enum

COMPARISONS = (exp.EQ, exp.NEQ, exp.GT, exp.GTE, exp.LT, exp.LTE)


def _in_predicate(node):
    # A containing outer WHERE does not authorize a SELECT-list or JOIN change
    # inside its subquery. Stop at the current query's scope boundary.
    parent = node.parent
    while parent is not None:
        if isinstance(parent, (exp.Where, exp.Having)):
            return True
        if isinstance(parent, (exp.Select, exp.Join)):
            return False
        parent = parent.parent
    return False


def _record(node, replacement, changelog, schema, tip, family):
    dialect = schema.get('dialect', 'postgres')
    changelog.append({'old_line': node.sql(dialect=dialect),
                      'new_line': replacement.sql(dialect=dialect), 'tip': tip,
                      'mutation': family})
    return replacement


def mutate_order_direction(node, changelog, schema):
    if not isinstance(node, exp.Order) or not node.expressions:
        return node
    # Change the first sorting criterion, retaining tie breakers and LIMIT.
    # Window ordering controls analytic computations, not result ranking.
    if not isinstance(node.parent, (exp.Select, exp.Union, exp.Intersect, exp.Except)):
        return node
    first = node.expressions[0]
    if not isinstance(first, exp.Ordered):
        return node
    replacement = node.copy()
    replacement.expressions[0].set('desc', not bool(first.args.get('desc')))
    return _record(node, replacement, changelog, schema,
                   'Reverse the first ORDER BY direction; retain other sort keys and LIMIT.',
                   'order_direction')


def mutate_count_threshold(node, changelog, schema):
    if not isinstance(node, COMPARISONS):
        return node
    # COUNT thresholds represent a nonnegative count, not a base-column domain.
    # Keep them in predicates; never mutate a join condition or scalar output.
    if not _in_predicate(node):
        return node
    for count, value, key in ((node.left, node.right, 'expression'),
                              (node.right, node.left, 'this')):
        if not isinstance(count, exp.Count) or not isinstance(value, exp.Literal) or value.is_string:
            continue
        try:
            number = Decimal(value.this)
        except InvalidOperation:
            continue
        if not number.is_finite() or number < 0 or number != number.to_integral_value():
            continue
        replacement = node.copy()
        replacement.set(key, exp.Literal.number(str(int(number) + 1)))
        return _record(node, replacement, changelog, schema,
                       'Increase the count threshold by one; keep the comparison and counted expression.',
                       'count_threshold')
    return node


def mutate_numeric_equality(node, changelog, schema):
    if not isinstance(node, (exp.EQ, exp.NEQ)):
        return node
    if not _in_predicate(node):
        return node
    for column, value, key in ((node.left, node.right, 'expression'),
                               (node.right, node.left, 'this')):
        if not isinstance(column, exp.Column) or not isinstance(value, exp.Literal) or value.is_string:
            continue
        info = get_col_info(schema, get_table_name(column, schema), column.name)
        if not info or info.get('type') != 'number' or 'min' not in info or 'max' not in info:
            continue
        try:
            old = Decimal(value.this)
            low, high = Decimal(str(info['min'])), Decimal(str(info['max']))
        except InvalidOperation:
            continue
        if not all(v.is_finite() for v in (old, low, high)) or low > high:
            continue
        if low != low.to_integral_value() or high != high.to_integral_value():
            continue
        low, high = int(low), int(high)
        # Sample without rejection, excluding the old value if it is an integer
        # in range. The existing catalog exposes bounds, not observed numbers.
        if old == old.to_integral_value() and low <= old <= high:
            if low == high:
                continue
            new = random.randint(low, high - 1)
            if new >= old:
                new += 1
        else:
            new = random.randint(low, high)
        replacement = node.copy()
        replacement.set(key, exp.Literal.number(str(new)))
        return _record(node, replacement, changelog, schema,
                       'Replace the numeric literal within schema bounds, preserving the comparison. '
                       'Bounds do not guarantee an observed value or a nonempty answer.',
                       'numeric_equality')
    return node


def mutate_enum_inequality(node, changelog, schema):
    if not isinstance(node, exp.NEQ) or not _in_predicate(node):
        return node
    result = mutate_enum(node, changelog, schema, allow_neq=True)
    if changelog:
        changelog[-1]["mutation"] = "enum_inequality"
    return result


def apply_coverage_fallback(ast, changelog, schema):
    """Try families in priority order and stop after one actual change."""
    for mutation in (mutate_order_direction, mutate_count_threshold,
                     mutate_numeric_equality, mutate_enum_inequality):
        for node in list(ast.walk()):
            replacement = mutation(node, changelog, schema)
            if changelog:
                if node is ast:
                    return replacement
                if replacement is not node:
                    node.replace(replacement)
                return ast
    return ast
