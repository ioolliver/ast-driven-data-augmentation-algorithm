import copy
import random
import sqlite3
import unittest
from unittest.mock import patch

import sqlglot
from sqlglot import exp

from ast_augmentation.augmentor import _create_sql_variation
from ast_augmentation.mutations.between import mutate_between
from ast_augmentation.mutations.coverage_fallbacks import (
    mutate_count_threshold, mutate_numeric_equality, mutate_order_direction,
)


class CoverageFallbackTest(unittest.TestCase):
    def setUp(self):
        random.seed(42)
        self.schema = {'dialect': 'sqlite', 'case_insensitive_identifiers': True,
                       'sqlite_double_quoted_literals': True, 'coverage_fallbacks': True,
                       'tables': [{'name': 't', 'columns': [
                           {'name': 'x', 'type': 'number', 'min': 1, 'max': 4},
                           {'name': 'kind', 'type': 'enum',
                            'enums': [{'value': 'A'}, {'value': "B's"}]},
                           {'name': 'id', 'type': 'number'},
                       ]}]}

    def run_sql(self, sql):
        with sqlite3.connect(':memory:') as con:
            con.executescript('CREATE TABLE t(id INTEGER, x INTEGER, kind TEXT);')
            con.executemany('INSERT INTO t VALUES(?,?,?)',
                            [(1, 1, 'A'), (2, 2, 'A'), (3, 3, "B's"), (4, 4, "B's")])
            return con.execute(sql).fetchall()

    def test_order_direction_changes_top_result_and_retains_tiebreaker(self):
        query = 'SELECT id FROM t ORDER BY x DESC, id ASC LIMIT 1'
        result, changes = _create_sql_variation(self.schema, query)
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0]['mutation'], 'order_direction')
        ast = sqlglot.parse_one(result, read='sqlite')
        self.assertFalse(ast.args['order'].expressions[0].args['desc'])
        self.assertFalse(ast.args['order'].expressions[1].args['desc'])
        self.assertEqual(self.run_sql(query), [(4,)])
        self.assertEqual(self.run_sql(result), [(1,)])

    def test_window_order_is_not_result_order(self):
        query = 'SELECT ROW_NUMBER() OVER (ORDER BY x) FROM t'
        _, changes = _create_sql_variation(self.schema, query)
        self.assertEqual(changes, [])
        ast = sqlglot.parse_one(query)
        node = ast.find(exp.Order)
        self.assertIs(mutate_order_direction(node, [], self.schema), node)

    def test_count_threshold_preserves_group_and_operator(self):
        query = 'SELECT kind FROM t GROUP BY kind HAVING COUNT(*) >= 2'
        result, changes = _create_sql_variation(self.schema, query)
        self.assertEqual(changes[0]['mutation'], 'count_threshold')
        self.assertIn('COUNT(*) >= 3', result)
        self.assertEqual(len(self.run_sql(query)), 2)
        self.assertEqual(self.run_sql(result), [])

    def test_reversed_and_distinct_count_threshold(self):
        result, changes = _create_sql_variation(
            self.schema, 'SELECT kind FROM t GROUP BY kind HAVING 1 < COUNT(DISTINCT id)')
        self.assertIn('2 < COUNT(DISTINCT id)', result)
        self.assertEqual(len(changes), 1)

    def test_count_skips_calculated_fractional_and_string_thresholds(self):
        for predicate in ['COUNT(*) > 1.5', "COUNT(*) > '2'", 'COUNT(*) > (1+1)']:
            node = sqlglot.parse_one('SELECT kind FROM t GROUP BY kind HAVING ' + predicate).find(exp.GT)
            changes = []
            self.assertIs(mutate_count_threshold(node, changes, self.schema), node)
            self.assertEqual(changes, [])

    def test_numeric_equality_uses_bounds_and_changes_result(self):
        query = 'SELECT id FROM t WHERE x = 2'
        result, changes = _create_sql_variation(self.schema, query)
        number = int(sqlglot.parse_one(result).find(exp.EQ).right.this)
        self.assertIn(number, [1, 3, 4])
        self.assertEqual(changes[0]['mutation'], 'numeric_equality')
        self.assertNotEqual(self.run_sql(result), self.run_sql(query))

    def test_numeric_neq_and_reversed_operands_keep_operator(self):
        for predicate in ['2 != x', '2 = x', 'x != 2']:
            result, changes = _create_sql_variation(self.schema, 'SELECT id FROM t WHERE ' + predicate)
            self.assertEqual(len(changes), 1)
            self.assertEqual(bool(sqlglot.parse_one(result).find(exp.NEQ)), '!=' in predicate)
            self.assertNotEqual(self.run_sql(result), self.run_sql('SELECT id FROM t WHERE ' + predicate))

    def test_numeric_skips_missing_bounds_ambiguous_and_subquery(self):
        for query in ['SELECT id FROM t WHERE id = 2',
                      'SELECT a.id FROM t a JOIN t b ON a.id=b.id WHERE x=2',
                      'SELECT id FROM t WHERE x=(SELECT id FROM t LIMIT 1)',
                      'SELECT id FROM t a JOIN t b ON a.x=2',
                      'SELECT id FROM t WHERE EXISTS (SELECT x=2 FROM t)',
                      'SELECT id FROM t WHERE EXISTS (SELECT id FROM t a JOIN t b ON a.x=2)']:
            _, changes = _create_sql_variation(self.schema, query)
            self.assertEqual(changes, [], query)

    def test_singleton_numeric_range_is_not_logged_as_change(self):
        schema = copy.deepcopy(self.schema)
        schema['tables'][0]['columns'][0].update(min=2, max=2)
        _, changes = _create_sql_variation(schema, 'SELECT id FROM t WHERE x=2')
        self.assertEqual(changes, [])

    def test_enum_neq_preserves_negation_and_escapes_values(self):
        query = 'SELECT id FROM t WHERE kind != "A"'
        result, changes = _create_sql_variation(self.schema, query)
        self.assertEqual(changes[0]['mutation'], 'enum_inequality')
        self.assertIsNotNone(sqlglot.parse_one(result).find(exp.NEQ))
        self.assertEqual(self.run_sql(result), [(1,), (2,)])
        self.assertNotEqual(self.run_sql(query), self.run_sql(result))

    def test_enum_neq_skips_unknown_value_and_real_quoted_column(self):
        for predicate in ["kind != 'missing'", 'kind != "x"']:
            _, changes = _create_sql_variation(self.schema, 'SELECT id FROM t WHERE ' + predicate)
            self.assertEqual(changes, [])

    def test_fallback_is_opt_in_and_does_not_compound_existing_changes(self):
        schema = copy.deepcopy(self.schema)
        schema.pop('coverage_fallbacks')
        _, changes = _create_sql_variation(schema, 'SELECT id FROM t ORDER BY x')
        self.assertEqual(changes, [])
        result, changes = _create_sql_variation(self.schema, "SELECT id FROM t WHERE kind='A' ORDER BY x")
        self.assertEqual(len(changes), 1)
        self.assertNotIn('mutation', changes[0])
        self.assertFalse(sqlglot.parse_one(result).args['order'].expressions[0].args['desc'])

    def test_between_identical_draw_uses_alternative_or_skips_fixed_domain(self):
        for kind, low, high in [('number', 1, 4), ('date', '2026-01-01', '2026-01-01')]:
            schema = {'tables': [{'name': 't', 'columns': [
                {'name': 'x', 'type': kind, 'min': low, 'max': high}]}]}
            bounds = '1.0 AND 4' if kind == 'number' else "'2026-01-01' AND '2026-01-01'"
            node = sqlglot.parse_one('SELECT x FROM t WHERE x BETWEEN ' + bounds).find(exp.Between)
            changes = []
            with patch('ast_augmentation.mutations.between.random.randint', side_effect=([1, 4] if kind == 'number' else [0, 0])):
                result = mutate_between(node, changes, schema)
            if kind == 'number':
                self.assertIsNot(result, node)
                self.assertNotEqual(changes[0]['old_line'], changes[0]['new_line'])
            else:
                self.assertIs(result, node)
                self.assertEqual(changes, [])

    def test_negative_singleton_between_is_not_a_change(self):
        schema = {'tables': [{'name': 't', 'columns': [
            {'name': 'x', 'type': 'number', 'min': -1, 'max': -1}]}]}
        node = sqlglot.parse_one('SELECT x FROM t WHERE x BETWEEN -1 AND -1').find(exp.Between)
        changes = []
        self.assertIs(mutate_between(node, changes, schema), node)
        self.assertEqual(changes, [])


if __name__ == '__main__':
    unittest.main()
