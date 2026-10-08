"""Component contract tests using synthetic, nonphysical fixtures."""

import unittest
from dataclasses import FrozenInstanceError, replace

from petroflash.components import Component
from petroflash.properties import DataKind, PropertyRecord


class TestComponent(unittest.TestCase):

    def record(self, value, unit):
        return PropertyRecord(
            value=value,
            unit=unit,
            source="Synthetic test fixture",
            reference="Internal software test; not physical data",
            method="Synthetic value",
            data_kind=DataKind.ESTIMATED,
        )

    def make_component(self):
        return Component(
            name="Synthetic component",
            cas_number="TEST-ID",
            formula="TEST",
            critical_temperature=self.record(300.0, "K"),
            critical_pressure=self.record(4.0e6, "Pa"),
            acentric_factor=self.record(0.1, "1"),
            molar_mass=self.record(0.030, "kg/mol"),
        )

    def test_preserves_property_record(self):
        record = self.record(350.0, "K")
        component = replace(
            self.make_component(),
            critical_temperature=record,
        )
        self.assertIs(component.critical_temperature, record)
        self.assertEqual(
            component.critical_temperature.source,
            "Synthetic test fixture",
        )

    def test_component_is_immutable(self):
        component = self.make_component()
        with self.assertRaises(FrozenInstanceError):
            component.name = "Changed"

    def test_rejects_empty_identity(self):
        component = self.make_component()
        for field in ("name", "cas_number", "formula"):
            for value in ("", "   ", None):
                with self.subTest(field=field, value=value):
                    with self.assertRaises(ValueError):
                        replace(component, **{field: value})

    def test_requires_property_records(self):
        component = self.make_component()
        fields = (
            "critical_temperature",
            "critical_pressure",
            "acentric_factor",
            "molar_mass",
        )
        for field in fields:
            with self.subTest(field=field):
                with self.assertRaises(TypeError):
                    replace(component, **{field: 100.0})

    def test_rejects_incorrect_units(self):
        component = self.make_component()
        wrong_units = {
            "critical_temperature": "degC",
            "critical_pressure": "bar",
            "acentric_factor": "Pa",
            "molar_mass": "g/mol",
        }
        for field, unit in wrong_units.items():
            bad_record = replace(getattr(component, field), unit=unit)
            with self.subTest(field=field, unit=unit):
                with self.assertRaises(ValueError):
                    replace(component, **{field: bad_record})

    def test_requires_positive_physical_properties(self):
        component = self.make_component()
        fields = (
            "critical_temperature",
            "critical_pressure",
            "molar_mass",
        )
        for field in fields:
            for value in (0.0, -1.0):
                bad_record = replace(
                    getattr(component, field),
                    value=value,
                )
                with self.subTest(field=field, value=value):
                    with self.assertRaises(ValueError):
                        replace(component, **{field: bad_record})

    def test_accepts_negative_acentric_factor(self):
        component = replace(
            self.make_component(),
            acentric_factor=self.record(-0.1, "1"),
        )
        self.assertEqual(component.acentric_factor.value, -0.1)


if __name__ == "__main__":
    unittest.main()
