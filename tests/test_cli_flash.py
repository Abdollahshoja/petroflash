"""Interactive flash routing, refusal and incomplete-result exit status."""

import io
import unittest
from contextlib import redirect_stdout, redirect_stderr
from dataclasses import replace
from types import SimpleNamespace as S
from unittest.mock import patch

from petroflash import cli
from petroflash.conditions import TPConditions


class TestCLIFlash(unittest.TestCase):
    def invoke(self, answer):
        cs = tuple(S(name=n, formula=f, critical_temperature=S(value=t),
            critical_pressure=S(value=p), acentric_factor=S(value=o))
            for n, f, t, p, o in (('methane', 'CH4', 190.56, 4599200, .01142),
                                  ('n-butane', 'C4H10', 425.12, 3796000, .2)))
        mix = S(components=cs, mole_fractions=(.5, .5), mole_percentages=(50, 50))
        output = io.StringIO()
        with patch('sys.argv', ['petroflash.cli', '--flash']), \
             patch.object(cli.ComponentDatabase, 'from_file', return_value=object()), \
             patch.object(cli, 'read_mixture', return_value=mix), \
             patch.object(cli, 'read_conditions', return_value=TPConditions(250, 2e6)), \
             patch('builtins.input', return_value=answer), redirect_stdout(output):
            cli.main()
        return output.getvalue()

    def test_interactive_flash_uses_real_engine(self):
        text = self.invoke('yes')
        self.assertIn('Status: two_phase', text)
        self.assertIn('Vapor mole fraction beta:', text)
        self.assertIn('Max |ln(f_liquid/f_vapor)|:', text)
        self.assertNotIn('Phase stability has NOT been tested', text)

    def test_refusing_assumption_skips_flash(self):
        with patch.object(cli, 'flash_tp') as calculate:
            text = self.invoke('no')
        calculate.assert_not_called()
        self.assertIn('PR calculation skipped', text)

    def test_inconclusive_result_exits_nonzero(self):
        real = cli.flash_tp
        def incomplete(*args, **kwargs):
            kwargs['max_iterations'] = 1
            return real(*args, **kwargs)
        errors = io.StringIO()
        with patch.object(cli, 'flash_tp', side_effect=incomplete), \
             redirect_stderr(errors), self.assertRaises(SystemExit) as caught:
            self.invoke('yes')
        self.assertEqual(caught.exception.code, 1)
        self.assertIn('no phase split accepted', errors.getvalue())


if __name__ == '__main__':
    unittest.main()
