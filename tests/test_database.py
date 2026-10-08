"""Tests for component lookup and invalid database inputs."""

import unittest
from dataclasses import replace

from petroflash.database import ComponentDatabase
from sample_data import methane


class TestComponentDatabase(unittest.TestCase):

    def setUp(self):
        self.component = methane()
        self.db = ComponentDatabase([self.component])

    def test_lookup_by_name_and_cas(self):
        self.assertEqual(len(self.db), 1)
        self.assertEqual(self.db.names(), ("methane",))
        self.assertIs(self.db.get(" METHANE "), self.component)
        self.assertIs(self.db.get("74-82-8"), self.component)
        self.assertEqual(
            self.db.select(["methane"]),
            (self.component,),
        )

    def test_rejects_invalid_cas(self):
        for cas_number in ("TEST-ID", "74-82-9"):
            with self.subTest(cas_number=cas_number):
                invalid = replace(
                    self.component,
                    cas_number=cas_number,
                )
                with self.assertRaises(ValueError):
                    ComponentDatabase([invalid])

    def test_rejects_duplicate_cas(self):
        with self.assertRaises(ValueError):
            ComponentDatabase([self.component, self.component])

    def test_rejects_duplicate_names(self):
        # Deliberately inconsistent fixture for identifier testing only.
        # This is not water data and must never enter the real database.
        conflicting = replace(
            self.component,
            name=" METHANE ",
            cas_number="7732-18-5",
        )
        with self.assertRaises(ValueError):
            ComponentDatabase([self.component, conflicting])

    def test_reports_missing_component(self):
        with self.assertRaises(KeyError):
            self.db.get("not-in-database")

    def test_rejects_repeated_selection(self):
        with self.assertRaises(ValueError):
            self.db.select(["methane", "74-82-8"])

    def test_rejects_empty_or_scalar_selection(self):
        with self.assertRaises(ValueError):
            self.db.select([])
        with self.assertRaises(TypeError):
            self.db.select("methane")

    def test_rejects_invalid_input_types_and_empty_keys(self):
        with self.assertRaises(TypeError):
            ComponentDatabase([123])
        with self.assertRaises(TypeError):
            self.db.get(None)
        with self.assertRaises(ValueError):
            self.db.get("   ")


if __name__ == "__main__":
    unittest.main()
