"""Stability flag routes through explicit assumptions and the actual engine."""

import io
import unittest
from contextlib import redirect_stdout
from types import SimpleNamespace as S
from unittest.mock import patch

from petroflash import cli
from petroflash.conditions import TPConditions


class TestCLIStability(unittest.TestCase):
    def invoke(self, answer):
        cs = tuple(S(name=n, critical_temperature=S(value=t), critical_pressure=S(value=p),
                     acentric_factor=S(value=o)) for n, t, p, o in (
            ('methane', 190.56, 4599200, .01142), ('n-butane', 425.12, 3796000, .2)))
        mix = S(components=cs, mole_fractions=(.5, .5), mole_percentages=(50, 50))
        output = io.StringIO()
        with patch('sys.argv', ['petroflash.cli', '--stability']), \
             patch.object(cli.ComponentDatabase, 'from_file', return_value=object()), \
             patch.object(cli, 'read_mixture', return_value=mix), \
             patch.object(cli, 'read_conditions', return_value=TPConditions(250, 2e6)), \
             patch('builtins.input', return_value=answer), redirect_stdout(output):
            cli.main()
        return output.getvalue()

    def test_stability_flag_runs_real_engine(self):
        text = self.invoke('yes')
        self.assertIn('MULTI-START TPD SEARCH', text)
        self.assertIn('Status: unstable', text)
        self.assertIn('Wilson vapor-like', text)
        self.assertIn('No equilibrium phase compositions or vapor fraction', text)

    def test_declining_does_not_run_stability(self):
        with patch.object(cli, 'search_pr_stability') as search:
            output = self.invoke('no')
        search.assert_not_called()
        self.assertIn('PR calculation skipped', output)


if __name__ == '__main__':
    unittest.main()
