import unittest
from unittest.mock import patch

import sqlglot

from mutations.postgis import mutate_postgis


def apply_postgis_mutation(sql, schema=None):
    changelog = []
    state = {}
    ast = sqlglot.parse_one(sql, read="postgres")
    modified = ast.transform(lambda node: mutate_postgis(node, changelog, schema or {}, state))
    return modified.sql(dialect="postgres"), changelog, state


class PostGISMutationTest(unittest.TestCase):
    def test_buffer_radius_is_coordinated_for_repeated_radius(self):
        sql = """
        SELECT
          AVG(ST_Area(ST_Intersection(
            ST_Buffer(e.geometry::geography, 300)::geometry,
            ST_Buffer(c.geometry::geography, 300)::geometry
          )::geography) / 1000000.0) AS area_media_km2
        FROM public.escola e
        INNER JOIN public.cras c ON c.cd_mun = e.cd_mun
        WHERE ST_Intersects(
          ST_Buffer(e.geometry::geography, 300)::geometry,
          ST_Buffer(c.geometry::geography, 300)::geometry
        )
        """

        with patch("mutations.postgis.random.randint", return_value=700):
            modified_sql, changelog, state = apply_postgis_mutation(sql)

        self.assertEqual(state["postgis_buffer_radius_by_old"]["300"], 700)
        self.assertEqual(modified_sql.count("ST_BUFFER"), 2)
        self.assertIn("ST_DWITHIN", modified_sql)
        self.assertEqual(modified_sql.count(", 700)"), 3)
        self.assertNotIn("ST_BUFFER(CAST(e.geometry AS GEOGRAPHY), 300)", modified_sql)
        self.assertNotIn("ST_BUFFER(CAST(c.geometry AS GEOGRAPHY), 300)", modified_sql)
        self.assertTrue(any("Raio de ST_Buffer alterado" in change.get("tip", "") for change in changelog))

    def test_dwithin_distance_argument_is_mutated(self):
        sql = """
        SELECT *
        FROM public.escola e
        WHERE ST_DWithin(
          e.geometry::geography,
          ST_Boundary(p.geometry)::geography,
          10000
        )
        """
        schema = {
            "tables": [
                {
                    "name": "escola",
                    "columns": [
                        {
                            "name": "geometry",
                            "type": "geometry",
                            "distance_min_m": 100,
                            "distance_max_m": 5000,
                        }
                    ],
                }
            ]
        }

        with patch("mutations.postgis.random.randint", return_value=2500):
            modified_sql, changelog, state = apply_postgis_mutation(sql, schema)

        self.assertEqual(state["postgis_distance_by_old"]["10000"], 2500)
        self.assertIn("ST_DWITHIN", modified_sql)
        self.assertIn(", 2500)", modified_sql)
        self.assertNotIn(", 10000)", modified_sql)
        self.assertTrue(any("Distância de ST_DWithin alterada" in change.get("tip", "") for change in changelog))

    def test_intersection_can_change_to_union(self):
        sql = "SELECT ST_Area(ST_Intersection(a.geometry, b.geometry)) FROM a JOIN b ON TRUE"

        with patch("mutations.postgis.random.choice", return_value="ST_Union"):
            modified_sql, changelog, _ = apply_postgis_mutation(sql)

        self.assertIn("ST_UNION(a.geometry, b.geometry)", modified_sql)
        self.assertNotIn("ST_INTERSECTION", modified_sql)
        self.assertTrue(any("Operação espacial alterada" in change.get("tip", "") for change in changelog))

    def test_intersection_can_change_to_difference_preserving_argument_order(self):
        sql = "SELECT ST_Intersection(a.geometry, b.geometry) FROM a JOIN b ON TRUE"

        with patch("mutations.postgis.random.choice", return_value="ST_Difference"):
            modified_sql, _, _ = apply_postgis_mutation(sql)

        self.assertIn("ST_DIFFERENCE(a.geometry, b.geometry)", modified_sql)
        self.assertNotIn("ST_DIFFERENCE(b.geometry, a.geometry)", modified_sql)

    def test_intersects_buffer_pair_rewrites_to_dwithin_for_strict_pattern(self):
        sql = """
        SELECT *
        FROM public.escola e
        JOIN public.cras c ON ST_Intersects(
          ST_Buffer(e.geometry::geography, 300)::geometry,
          ST_Buffer(c.geometry::geography, 300)::geometry
        )
        """

        with patch("mutations.postgis.random.randint", return_value=900):
            modified_sql, changelog, _ = apply_postgis_mutation(sql)

        self.assertIn("ST_DWITHIN", modified_sql)
        self.assertNotIn("ST_INTERSECTS", modified_sql)
        self.assertIn("CAST(e.geometry AS GEOGRAPHY)", modified_sql)
        self.assertIn("CAST(c.geometry AS GEOGRAPHY)", modified_sql)
        self.assertIn(", 900)", modified_sql)
        self.assertTrue(any("ST_Intersects com buffers reescrito" in change.get("tip", "") for change in changelog))

    def test_intersects_rewrite_does_not_apply_to_non_buffer_pattern(self):
        sql = "SELECT * FROM a JOIN b ON ST_Intersects(a.geometry, b.geometry)"

        modified_sql, changelog, state = apply_postgis_mutation(sql)

        self.assertIn("ST_INTERSECTS(a.geometry, b.geometry)", modified_sql)
        self.assertEqual(changelog, [])
        self.assertEqual(state, {})

    def test_unsupported_postgis_and_non_postgis_sql_are_unchanged(self):
        unsupported_sql = "SELECT ST_Centroid(geometry) FROM escola"
        regular_sql = "SELECT * FROM escola WHERE cd_entidade = 1"

        unsupported_modified, unsupported_changelog, _ = apply_postgis_mutation(unsupported_sql)
        regular_modified, regular_changelog, _ = apply_postgis_mutation(regular_sql)

        self.assertIn("ST_CENTROID(geometry)", unsupported_modified)
        self.assertEqual(unsupported_changelog, [])
        self.assertEqual(regular_modified, "SELECT * FROM escola WHERE cd_entidade = 1")
        self.assertEqual(regular_changelog, [])


if __name__ == "__main__":
    unittest.main()
