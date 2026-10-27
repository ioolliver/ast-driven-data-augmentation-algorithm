import copy
import sqlite3
import unittest
from unittest.mock import patch

import sqlglot
from sqlglot import exp

from ast_augmentation.augmentor import _create_sql_variation
from ast_augmentation.mutations.binary import mutate_binary
from ast_augmentation.mutations.value_group import mutate_value_group
from ast_augmentation.schema_utils import get_table_name, string_literal_value


class SpiderLookupLiteralBooleanTest(unittest.TestCase):
    def setUp(self):
        self.schema = {
            'dialect': 'sqlite', 'case_insensitive_identifiers': True,
            'sqlite_double_quoted_literals': True, 'restrict_aggregates': True,
            'tables': [
                {'name': 'films', 'columns': [
                    {'name': 'id', 'type': 'number'},
                    {'name': 'title', 'type': 'string'},
                    {'name': 'status', 'type': 'enum', 'enums': [{'value': 'Open'}, {'value': 'Closed'}]},
                ]},
                {'name': 'estimates', 'columns': [
                    {'name': 'film_id', 'type': 'number'},
                    {'name': 'high', 'type': 'number', 'min': 1, 'max': 100, 'semantic_group': 'estimates'},
                    {'name': 'low', 'type': 'number', 'min': 1, 'max': 100, 'semantic_group': 'estimates'},
                    {'name': 'status', 'type': 'enum', 'enums': [{'value': 'Draft'}, {'value': 'Final'}]},
                    {'name': 'active', 'type': 'boolean'},
                ]},
            ],
        }

    def resolve(self, query, name, table=None):
        ast = sqlglot.parse_one(query, read='sqlite')
        column = next(c for c in ast.find_all(exp.Column)
                      if c.name == name and (table is None or c.table == table))
        return get_table_name(column, self.schema)

    def test_unique_unqualified_column_from_join(self):
        self.assertEqual(self.resolve('SELECT high FROM films f JOIN estimates e ON f.id=e.film_id', 'high'), 'estimates')

    def test_case_insensitive_alias_and_table_lookup(self):
        self.assertEqual(self.resolve('SELECT t2.HIGH FROM films T1 JOIN estimates T2 ON T1.id=T2.film_id', 'HIGH'), 'estimates')

    def test_ambiguous_or_absent_unqualified_column_is_not_guessed(self):
        for name in ('status', 'missing'):
            self.assertEqual(self.resolve(f'SELECT {name} FROM films f JOIN estimates e ON f.id=e.film_id', name), '')

    def test_self_join_is_ambiguous_without_qualification(self):
        self.assertEqual(self.resolve('SELECT high FROM estimates a JOIN estimates b ON a.film_id=b.film_id', 'high'), '')

    def test_correlated_qualified_column_uses_outer_binding(self):
        query = 'SELECT id FROM films f WHERE EXISTS (SELECT film_id FROM estimates e WHERE e.film_id=f.id)'
        self.assertEqual(self.resolve(query, 'id', 'f'), 'films')

    def test_local_alias_shadows_outer_alias(self):
        query = 'SELECT id FROM films f WHERE EXISTS (SELECT high FROM estimates f WHERE f.status=\'Draft\')'
        self.assertEqual(self.resolve(query, 'status', 'f'), 'estimates')

    def test_derived_and_cte_columns_are_not_treated_as_base_columns(self):
        queries = [
            'SELECT high FROM (SELECT high FROM estimates) d',
            'WITH estimates AS (SELECT title AS high FROM films) SELECT high FROM estimates',
            'SELECT high FROM films f JOIN (SELECT high FROM estimates) d ON 1=1',
        ]
        for query in queries:
            self.assertEqual(self.resolve(query, 'high'), '', query)

    def test_projection_alias_is_not_a_same_named_base_column(self):
        query = 'SELECT COUNT(*) AS high FROM estimates ORDER BY high'
        self.assertEqual(self.resolve(query, 'high'), '')
        result, changes = _create_sql_variation(self.schema, query)
        self.assertFalse(changes)
        self.assertIn('ORDER BY', result)

    def test_legacy_lookup_keeps_case_sensitive_behavior(self):
        query = 'SELECT t2.high FROM films T1 JOIN estimates T2 ON T1.id=T2.film_id'
        ast = sqlglot.parse_one(query, read='sqlite')
        column = next(c for c in ast.find_all(exp.Column) if c.name == 'high')
        self.assertEqual(get_table_name(column), 't2')
        schema = copy.deepcopy(self.schema)
        schema['case_insensitive_identifiers'] = False
        self.assertEqual(get_table_name(column, schema), 't2')

    def test_join_column_swap_executes_against_correct_table(self):
        query = 'SELECT t1.title FROM films T1 JOIN estimates T2 ON T1.id=T2.film_id ORDER BY high DESC LIMIT 1'
        result, changes = _create_sql_variation(self.schema, query)
        self.assertEqual(len(changes), 1)
        self.assertIn('low', result)
        with sqlite3.connect(':memory:') as con:
            con.executescript("CREATE TABLE films(id INTEGER, title TEXT, status TEXT); CREATE TABLE estimates(film_id INTEGER, high INTEGER, low INTEGER, status TEXT, active INTEGER); INSERT INTO films VALUES(1,'A','Open'),(2,'B','Closed'); INSERT INTO estimates VALUES(1,100,1,'Draft',0),(2,50,10,'Final',1);")
            self.assertEqual(con.execute(query).fetchall(), [('A',)])
            self.assertEqual(con.execute(result).fetchall(), [('B',)])

    def test_unqualified_enum_and_threshold_in_join_use_own_metadata(self):
        for query in [
            'SELECT id FROM films f JOIN estimates e ON f.id=e.film_id WHERE high > 10',
            'SELECT id FROM films f JOIN estimates e ON f.id=e.film_id WHERE e.status = "Draft"',
        ]:
            result, changes = _create_sql_variation(self.schema, query)
            self.assertTrue(changes)
            if 'Draft' in query:
                self.assertIn("'Final'", result)

    def test_ambiguous_boolean_does_not_fall_back_to_first_table(self):
        self.schema['tables'][0]['columns'].append({'name': 'active', 'type': 'boolean'})
        _, changes = _create_sql_variation(self.schema, 'SELECT f.id FROM films f JOIN estimates e ON f.id=e.film_id WHERE active=0')
        self.assertFalse(changes)

    def test_double_quoted_like_is_mutated_and_single_quoted(self):
        query = 'SELECT title FROM films WHERE title LIKE "%Scanner%"'
        with patch('ast_augmentation.mutations.text_pattern.random.choice', return_value='prefix'):
            result, changes = _create_sql_variation(self.schema, query)
        self.assertIn("LIKE 'Scanner%'", result)
        self.assertEqual(len(changes), 1)
        with sqlite3.connect(':memory:') as con:
            con.executescript("CREATE TABLE films(title TEXT); INSERT INTO films VALUES('Scanner A'),('A Scanner');")
            self.assertEqual(len(con.execute(query).fetchall()), 2)
            self.assertEqual(con.execute(result).fetchall(), [('Scanner A',)])

    def test_real_double_quoted_columns_and_qualified_identifiers_remain_columns(self):
        self.schema['tables'][0]['columns'].append({'name': 'Open', 'type': 'string'})
        for predicate in ['title LIKE "Open"', 'status = "Open"', 'title LIKE f."Open"']:
            _, changes = _create_sql_variation(self.schema, f'SELECT title FROM films f WHERE {predicate}')
            self.assertFalse(changes, predicate)

    def test_double_quoted_literal_requires_opt_in_and_known_sources(self):
        for query, opt_in in [('SELECT title FROM films WHERE title LIKE "%A%"', False),
                              ('SELECT title FROM unknown WHERE title LIKE "%A%"', True),
                              ('SELECT title FROM (SELECT title FROM films) d WHERE title LIKE "%A%"', True)]:
            schema = copy.deepcopy(self.schema)
            schema['sqlite_double_quoted_literals'] = opt_in
            _, changes = _create_sql_variation(schema, query)
            self.assertFalse(changes)

    def test_correlated_identifier_is_not_reinterpreted_as_string(self):
        ast = sqlglot.parse_one('SELECT title FROM films f WHERE EXISTS (SELECT film_id FROM estimates e WHERE e.status="title")', read='sqlite')
        value = next(c for c in ast.find_all(exp.Column) if c.name == 'title' and c.this.args.get('quoted'))
        self.assertIsNone(string_literal_value(value, self.schema))

    def test_double_quoted_value_groups_and_mixed_identifier_list(self):
        info = self.schema['tables'][0]['columns'][2]
        info['enums'] = [{'value': 'Open', 'value_group': 'open'}, {'value': 'Closed', 'value_group': 'closed'}]
        for expression, expected in [('status IN ("Open")', True), ('status IN (\'Open\', title)', False)]:
            ast = sqlglot.parse_one('SELECT title FROM films WHERE ' + expression, read='sqlite')
            changes = []
            result = ast.transform(lambda n: mutate_value_group(n, changes, self.schema))
            self.assertEqual(bool(changes), expected)
            if expected:
                self.assertIn("IN ('Closed')", result.sql(dialect='sqlite'))

    def test_boolean_and_legacy_binary_values_toggle(self):
        for kind in ('boolean', 'binary'):
            for value, expected in [('0', '1'), ('1', '0'), ('TRUE', 'FALSE'), ('FALSE', 'TRUE'), ("'0'", "'1'"), ('"0"', "'1'")]:
                with self.subTest(kind=kind, value=value):
                    schema = copy.deepcopy(self.schema)
                    schema['tables'][1]['columns'][-1]['type'] = kind
                    ast = sqlglot.parse_one('SELECT active FROM estimates WHERE active = ' + value, read='sqlite')
                    changes = []
                    result = ast.transform(lambda n: mutate_binary(n, changes, schema))
                    self.assertEqual(len(changes), 1)
                    self.assertIn('active = ' + expected, result.sql(dialect='sqlite'))

    def test_reversed_double_quoted_enum_and_boolean_values(self):
        for query, expected in [
            ('SELECT title FROM films WHERE "Open"=status', "status = 'Closed'"),
            ('SELECT active FROM estimates WHERE "0"=active', "'1' = active"),
        ]:
            result, changes = _create_sql_variation(self.schema, query)
            self.assertTrue(changes)
            self.assertIn(expected, result)

    def test_native_boolean_changelog_preserves_original_sql(self):
        ast = sqlglot.parse_one('SELECT active FROM estimates WHERE TRUE=active', read='sqlite')
        changes = []
        ast.transform(lambda n: mutate_binary(n, changes, self.schema))
        self.assertIn('TRUE = active', changes[0]['old_line'])
        self.assertIn('FALSE = active', changes[0]['new_line'])

    def test_invalid_boolean_values_skip_without_exceptions(self):
        for value in ["'yes'", '2', '-1', '1.5', 'NULL', '(SELECT 1)']:
            ast = sqlglot.parse_one('SELECT active FROM estimates WHERE active=' + value, read='sqlite')
            changes = []
            ast.transform(lambda n: mutate_binary(n, changes, self.schema))
            self.assertFalse(changes, value)

    def test_reversed_boolean_predicate_preserves_orientation_and_executes(self):
        result, changes = _create_sql_variation(self.schema, 'SELECT film_id FROM estimates WHERE 0=active')
        self.assertTrue(changes)
        self.assertIn('1 = active', result)
        with sqlite3.connect(':memory:') as con:
            con.executescript('CREATE TABLE estimates(film_id INTEGER, active INTEGER); INSERT INTO estimates VALUES(1,0),(2,1);')
            self.assertEqual(con.execute(result).fetchall(), [(2,)])


if __name__ == '__main__':
    unittest.main()
