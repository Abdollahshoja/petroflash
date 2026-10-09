"""SI, unit conversion and invalid-input tests."""
import unittest
from dataclasses import FrozenInstanceError
from petroflash.conditions import TPConditions


class TestTPConditions(unittest.TestCase):
    def test_preserves_si_values(self):
        item = TPConditions(300, 100000)
        self.assertEqual((item.temperature_k, item.pressure_pa), (300., 100000.))

    def test_converts_celsius_and_absolute_bar(self):
        item = TPConditions.from_units(25, 10, temperature_unit='C', pressure_unit='bar')
        self.assertAlmostEqual(item.temperature_k, 298.15)
        self.assertEqual(item.pressure_pa, 1000000)
        item = TPConditions.from_units(-40, .1, temperature_unit=' c ', pressure_unit=' BAR ')
        self.assertAlmostEqual(item.temperature_k, 233.15)
        self.assertEqual(item.pressure_pa, 10000)

    def test_rejects_invalid_values(self):
        for value in (0, -1, float('nan'), float('inf'), float('-inf')):
            for name in ('temperature_k', 'pressure_pa'):
                data = dict(temperature_k=300, pressure_pa=100000)
                data[name] = value
                with self.subTest(value=value, name=name), self.assertRaises(ValueError):
                    TPConditions(**data)
        for temperature in (-273.15, -300):
            with self.assertRaises(ValueError):
                TPConditions.from_units(temperature, 1, temperature_unit='C', pressure_unit='bar')
        with self.assertRaises(ValueError):
            TPConditions.from_units(25, 1e308, temperature_unit='C', pressure_unit='bar')

    def test_rejects_invalid_types(self):
        for value in (True, '300', None, 1+2j):
            with self.subTest(value=value), self.assertRaises(TypeError):
                TPConditions(value, 100000)
            with self.subTest(value=value), self.assertRaises(TypeError):
                TPConditions.from_units(25, value, temperature_unit='C', pressure_unit='bar')

    def test_explicit_units_and_gauge_rejection(self):
        for tu, pu in (('F', 'bar'), ('C', 'barg'), ('K', 'psig'), ('', 'Pa')):
            with self.subTest(tu=tu, pu=pu), self.assertRaises(ValueError):
                TPConditions.from_units(25, 1, temperature_unit=tu, pressure_unit=pu)
        with self.assertRaises(TypeError):
            TPConditions.from_units(25, 1, temperature_unit=None, pressure_unit='bar')
        item = TPConditions.from_units(300, 100000, temperature_unit='K', pressure_unit='Pa')
        self.assertEqual(item, TPConditions(300, 100000))

    def test_is_immutable(self):
        item = TPConditions(300, 100000)
        with self.assertRaises(FrozenInstanceError):
            item.pressure_pa = 200000


if __name__ == '__main__':
    unittest.main()
