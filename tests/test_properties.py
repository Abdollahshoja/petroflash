"""Behavioral tests using synthetic records, not physical reference data."""

import unittest
from dataclasses import FrozenInstanceError

from petroflash.properties import DataKind, PropertyRecord


class TestPropertyRecord(unittest.TestCase):

    def make_record(self, **changes):
        fields = {
            "value": 200.0,
            "unit": "K",
            "source": "Synthetic test fixture",
            "reference": "Internal test case; not physical data",
            "method": "Synthetic value",
            "data_kind": DataKind.EVALUATED,
        }
        fields.update(changes)
        return PropertyRecord(**fields)

    def test_valid_record_preserves_value_and_provenance(self):
        record = self.make_record()
        self.assertEqual(record.value, 200.0)
        self.assertEqual(record.unit, "K")
        self.assertEqual(record.source, "Synthetic test fixture")
        self.assertIsNone(record.uncertainty)

    def test_record_is_immutable(self):
        record = self.make_record()
        with self.assertRaises(FrozenInstanceError):
            record.value = 250.0

    def test_rejects_nonfinite_values(self):
        for value in (float("nan"), float("inf"), -float("inf")):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    self.make_record(value=value)

    def test_rejects_nonnumeric_and_boolean_values(self):
        for value in ("200", None, True, 1 + 2j):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    self.make_record(value=value)

    def test_requires_units_and_provenance(self):
        for field in ("unit", "source", "reference", "method"):
            for value in ("", "   ", None):
                with self.subTest(field=field, value=value):
                    with self.assertRaises(ValueError):
                        self.make_record(**{field: value})

    def test_requires_explicit_data_kind(self):
        with self.assertRaises(TypeError):
            self.make_record(data_kind="evaluated")

    def test_accepts_negative_generic_property(self):
        record = self.make_record(value=-0.1, unit="1")
        self.assertEqual(record.value, -0.1)

    def test_accepts_documented_uncertainty(self):
        record = self.make_record(
            uncertainty=0.5,
            notes="Synthetic standard uncertainty; coverage factor k=1.",
        )
        self.assertEqual(record.uncertainty, 0.5)

    def test_rejects_invalid_uncertainty(self):
        for uncertainty in (-0.5, float("nan"), float("inf")):
            with self.subTest(uncertainty=uncertainty):
                with self.assertRaises(ValueError):
                    self.make_record(
                        uncertainty=uncertainty,
                        notes="Synthetic uncertainty.",
                    )

    def test_requires_uncertainty_definition(self):
        with self.assertRaises(ValueError):
            self.make_record(uncertainty=0.5)

    def test_rejects_nontext_notes(self):
        with self.assertRaises(TypeError):
            self.make_record(notes=None)


if __name__ == "__main__":
    unittest.main()
