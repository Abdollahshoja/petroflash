"""CLI opt-in, explicit interaction assumption and calculation failure handling."""

import io
import unittest
from contextlib import redirect_stdout, redirect_stderr
from types import SimpleNamespace
from unittest.mock import patch

from petroflash import cli
from petroflash.conditions import TPConditions
from petroflash.pr_roots import PRRootError


class TestCLIPR(unittest.TestCase):
    def setUp(self):
        component = SimpleNamespace(name='synthetic-component',
            critical_temperature=SimpleNamespace(value=200),
            critical_pressure=SimpleNamespace(value=4e6),
            acentric_factor=SimpleNamespace(value=0))
        self.mixture = SimpleNamespace(components=(component,),
            mole_percentages=(100,), mole_fractions=(1.0,))
        self.conditions = TPConditions(300, 1e6)

    def invoke(self, argv, answers=()):
        out = io.StringIO()
        with patch('sys.argv', ['petroflash.cli', *argv]), \
             patch.object(cli.ComponentDatabase, 'from_file', return_value=object()), \
             patch.object(cli, 'read_mixture', return_value=self.mixture), \
             patch.object(cli, 'read_conditions', return_value=self.conditions), \
             patch('builtins.input', side_effect=answers), redirect_stdout(out):
            cli.main()
        return out.getvalue()

    def test_default_preserves_input_only_mode(self):
        with patch.object(cli, 'print_pr_feed') as calculation:
            output = self.invoke([])
            calculation.assert_not_called()
        self.assertIn('Validated overall feed composition', output)
        self.assertIn('Flash calculation is not implemented yet', output)

    def test_pr_mode_retries_then_evaluates_real_engine(self):
        output = self.invoke(['--pr'], ['maybe', ' YES '])
        self.assertIn('Choose yes or no', output)
        self.assertIn('ALL kij = 0', output)
        self.assertIn('synthetic-component', output)
        self.assertIn('ln(phi)', output)
        self.assertIn('g_residual/(RT)', output)
        self.assertIn('not a flash result', output)

    def test_declining_assumption_skips_engine(self):
        with patch.object(cli, 'print_pr_feed') as calculation:
            output = self.invoke(['--pr'], ['no'])
            calculation.assert_not_called()
        self.assertIn('PR calculation skipped', output)

    def test_eof_at_assumption_cancels(self):
        output = self.invoke(['--pr'], [EOFError()])
        self.assertIn('Input cancelled', output)

    def test_calculation_failure_exits_with_error(self):
        errors = io.StringIO()
        with patch.object(cli, 'print_pr_feed', side_effect=PRRootError('test ambiguity')), \
             redirect_stderr(errors), self.assertRaises(SystemExit) as caught:
            self.invoke(['--pr'], ['yes'])
        self.assertEqual(caught.exception.code, 1)
        self.assertIn('PR calculation error: test ambiguity', errors.getvalue())


if __name__ == '__main__':
    unittest.main()
