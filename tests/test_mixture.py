"""Tests for user-defined feed compositions."""

import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

from petroflash import ComponentDatabase
from petroflash.mixture import Mixture


ROOT = Path(__file__).resolve().parents[1]


class TestMixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = ComponentDatabase.from_file(ROOT / "data/components.json")

    def make(self, values):
        return Mixture.from_mole_percentages(
            self.db, ["methane", "ethane"], values
        )

    def test_preserves_component_order_and_converts_percentages(self):
        mixture = Mixture.from_mole_percentages(
            self.db, ["ethane", "methane"], [25, 75]
        )
        self.assertEqual(mixture.names, ("ethane", "methane"))
        self.assertEqual(mixture.mole_percentages, (25.0, 75.0))
        self.assertEqual(mixture.mole_fractions, (0.25, 0.75))
        self.assertIs(mixture.components[0], self.db.get("ethane"))

    def test_accepts_pure_component_and_zero_content(self):
        pure = Mixture.from_mole_percentages(
            self.db, ["methane"], [100]
        )
        self.assertEqual(pure.mole_fractions, (1.0,))
        self.assertEqual(self.make([100, 0]).mole_fractions, (1.0, 0.0))

    def test_rejects_invalid_values(self):
        for values in (
            [-1, 101], [101, -1], [float("nan"), 50],
            [float("inf"), 0], [float("-inf"), 100],
        ):
            with self.subTest(values=values):
                with self.assertRaises(ValueError):
                    self.make(values)

        for values in ([True, 99], ["50", 50], [None, 100]):
            with self.subTest(values=values):
                with self.assertRaises(TypeError):
                    self.make(values)

    def test_rejects_wrong_total_and_length(self):
        for values in ([40, 50], [60, 50], [0, 0], [100], [20, 30, 50]):
            with self.subTest(values=values):
                with self.assertRaises(ValueError):
                    self.make(values)

    def test_rejects_duplicate_unknown_and_empty_selection(self):
        methane_cas = self.db.get("methane").cas_number
        with self.assertRaises(ValueError):
            Mixture.from_mole_percentages(
                self.db, ["methane", methane_cas], [50, 50]
            )
        with self.assertRaises(KeyError):
            Mixture.from_mole_percentages(
                self.db, ["not-a-component"], [100]
            )
        with self.assertRaises(ValueError):
            Mixture.from_mole_percentages(self.db, [], [])

    def test_copies_input_and_is_immutable(self):
        values = [70, 30]
        mixture = self.make(values)
        values[0] = 10
        self.assertEqual(mixture.mole_percentages, (70.0, 30.0))
        with self.assertRaises(FrozenInstanceError):
            mixture.mole_percentages = (50.0, 50.0)

    def test_tolerance_does_not_normalize_input(self):
        values = [50.0, 50.0 + 1e-9]
        mixture = self.make(values)
        self.assertEqual(mixture.mole_percentages, tuple(values))
        self.assertEqual(
            mixture.mole_fractions, tuple(value / 100 for value in values)
        )
        with self.assertRaises(ValueError):
            self.make([50.0, 50.0 + 1e-6])

    def test_direct_constructor_also_validates(self):
        methane = self.db.get("methane")
        with self.assertRaises(ValueError):
            Mixture((methane, methane), (50, 50))
        with self.assertRaises(TypeError):
            Mixture(("methane",), (100,))
        with self.assertRaises(TypeError):
            Mixture((methane,), "100")


if __name__ == "__main__":
    unittest.main()
