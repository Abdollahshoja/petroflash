"""User-input conversion, recovery and cancellation tests."""
import unittest
from unittest.mock import patch
from petroflash.cli import read_conditions


class TestCLIConditions(unittest.TestCase):
    def test_celsius_and_absolute_bar(self):
        with patch('builtins.input', side_effect=['C', '25', 'bar', '10']), patch('builtins.print'):
            item = read_conditions()
        self.assertAlmostEqual(item.temperature_k, 298.15)
        self.assertEqual(item.pressure_pa, 1000000)

    def test_invalid_input_recovers(self):
        answers = ['F', 'K', 'abc', 'K', '0', 'C', '-40',
                   'barg', 'bar', 'nan', 'Pa', '-1', 'bar', '2']
        with patch('builtins.input', side_effect=answers), patch('builtins.print'):
            item = read_conditions()
        self.assertAlmostEqual(item.temperature_k, 233.15)
        self.assertEqual(item.pressure_pa, 200000)

    def test_eof_propagates_to_main_handler(self):
        with patch('builtins.input', side_effect=EOFError):
            with self.assertRaises(EOFError):
                read_conditions()


if __name__ == '__main__':
    unittest.main()
