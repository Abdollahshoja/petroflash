"""Regression checks for the selected central dataset.

These verify the accepted dataset contract, not experimental accuracy.
"""

import unittest
from pathlib import Path

from petroflash.database import ComponentDatabase


EXPECTED_COMPONENTS = {
    "methane": "74-82-8",
    "ethane": "74-84-0",
    "propane": "74-98-6",
    "n-butane": "106-97-8",
    "isobutane": "75-28-5",
    "n-pentane": "109-66-0",
    "isopentane": "78-78-4",
    "n-hexane": "110-54-3",
    "nitrogen": "7727-37-9",
    "carbon dioxide": "124-38-9",
    "hydrogen sulfide": "7783-06-4",
    "water": "7732-18-5",
}


class TestCentralDataset(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        cls.db = ComponentDatabase.from_file(
            root / "data" / "components.json"
        )

    def test_dataset_identity_and_inventory(self):
        self.assertEqual(self.db.dataset_version, "0.2.0")
        self.assertEqual(len(self.db), 12)
        self.assertEqual(set(self.db.names()), set(EXPECTED_COMPONENTS))

        for name, cas_number in EXPECTED_COMPONENTS.items():
            with self.subTest(name=name):
                self.assertEqual(self.db.get(name).cas_number, cas_number)
                self.assertIs(self.db.get(name), self.db.get(cas_number))

    def test_selected_source_policy(self):
        eos_fields = (
            "critical_temperature",
            "critical_pressure",
            "acentric_factor",
        )

        for name in EXPECTED_COMPONENTS:
            component = self.db.get(name)

            for field in eos_fields:
                with self.subTest(name=name, field=field):
                    record = getattr(component, field)
                    self.assertEqual(record.source, "chemicals 1.5.2")
                    self.assertEqual(record.method, "HEOS")

            with self.subTest(name=name, field="molar_mass"):
                self.assertEqual(
                    component.molar_mass.source,
                    "chemicals 1.5.2",
                )
                self.assertEqual(
                    component.molar_mass.method,
                    "identifiers.search_chemical metadata",
                )

    def test_mass_units_and_isomer_identity(self):
        methane = self.db.get("methane")
        water = self.db.get("water")

        self.assertEqual(methane.formula, "CH4")
        self.assertEqual(water.formula, "H2O")
        self.assertEqual(methane.molar_mass.unit, "kg/mol")
        self.assertEqual(water.molar_mass.unit, "kg/mol")
        self.assertAlmostEqual(
            methane.molar_mass.value, 0.01604246, places=10
        )
        self.assertAlmostEqual(
            water.molar_mass.value, 0.01801528, places=10
        )

        normal = self.db.get("n-butane")
        branched = self.db.get("isobutane")
        self.assertEqual(normal.formula, branched.formula)
        self.assertNotEqual(normal.cas_number, branched.cas_number)
        self.assertNotEqual(
            normal.critical_temperature.value,
            branched.critical_temperature.value,
        )


if __name__ == "__main__":
    unittest.main()
