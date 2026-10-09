"""Flash regression, independent binary reference, balances and failure paths."""

import unittest
from dataclasses import FrozenInstanceError, replace
from math import fsum, log
from types import SimpleNamespace as S
from unittest.mock import patch

from petroflash.conditions import TPConditions
from petroflash.flash import flash_tp
from petroflash.pr_mixing import zero_kij
from petroflash.pr_fugacity import mixture_pr_log_fugacity


def fixture():
    # Fixed rounded property fixture; not an experimental validation dataset.
    cs = tuple(S(name=n, formula=f, critical_temperature=S(value=t),
        critical_pressure=S(value=p), acentric_factor=S(value=o))
        for n, f, t, p, o in (
            ('methane', 'CH4', 190.56, 4599200, .01142),
            ('n-butane', 'C4H10', 425.12, 3796000, .2)))
    return S(components=cs, mole_fractions=(.5, .5))


class TestFlash(unittest.TestCase):
    def test_binary_independent_reference_and_balances(self):
        mix, tp = fixture(), TPConditions(250, 2e6)
        q = flash_tp(mix, tp, kij=zero_kij(2))
        self.assertEqual(q.status, 'two_phase')
        # Independent NumPy polynomial roots + SciPy simultaneous chemical
        # potential solve, with the same fixture and constants, gave:
        self.assertAlmostEqual(q.beta, 0.4160563614095882, delta=2e-8)
        self.assertAlmostEqual(q.liquid_composition[0], 0.16432500890981508, delta=2e-8)
        self.assertAlmostEqual(q.vapor_composition[0], 0.9711267363318565, delta=2e-8)
        x, y = q.liquid_composition, q.vapor_composition
        self.assertAlmostEqual(fsum(x), 1, places=10)
        self.assertAlmostEqual(fsum(y), 1, places=10)
        for zi, xi, yi in zip(mix.mole_fractions, x, y):
            self.assertAlmostEqual((1-q.beta)*xi+q.beta*yi, zi, places=10)
        phases = [S(components=mix.components, mole_fractions=c) for c in (x, y)]
        l = mixture_pr_log_fugacity(phases[0], tp, kij=zero_kij(2), z=q.liquid_z)
        v = mixture_pr_log_fugacity(phases[1], tp, kij=zero_kij(2), z=q.vapor_z)
        for i in range(2):
            self.assertLess(abs(log(x[i])+l.ln_phi[i]-log(y[i])-v.ln_phi[i]), 1e-8)
        self.assertLess(q.gibbs_change_rt, 0)
        self.assertTrue(all(s.status == 'no_negative_tpd_found' for s in q.phase_stability))
        with self.assertRaises(FrozenInstanceError):
            q.beta = 0

    def test_nonzero_kij_and_permutation(self):
        mix, tp, kk = fixture(), TPConditions(250, 2e6), ((0, .03), (.03, 0))
        a = flash_tp(mix, tp, kij=kk)
        rev = S(components=tuple(reversed(mix.components)), mole_fractions=(.5, .5))
        b = flash_tp(rev, tp, kij=kk)
        self.assertEqual(a.status, 'two_phase')
        self.assertEqual(b.status, 'two_phase')
        self.assertAlmostEqual(a.beta, b.beta, places=8)
        for x, y in zip(a.liquid_composition, reversed(b.liquid_composition)):
            self.assertAlmostEqual(x, y, places=8)

    def test_zero_component_preserved(self):
        mix = fixture()
        extra = S(name='inactive water', formula='H2O',
            critical_temperature=S(value=647), critical_pressure=S(value=22e6),
            acentric_factor=S(value=.34))
        augmented = S(components=(*mix.components, extra), mole_fractions=(.5, .5, 0))
        q = flash_tp(augmented, TPConditions(250, 2e6), kij=zero_kij(3))
        self.assertEqual(q.status, 'two_phase')
        self.assertEqual(q.liquid_composition[2], 0)
        self.assertEqual(q.vapor_composition[2], 0)
        self.assertEqual(augmented.mole_fractions, (.5, .5, 0))

    def test_single_phase_candidate_has_no_invented_beta(self):
        q = flash_tp(fixture(), TPConditions(450, 1e5), kij=zero_kij(2))
        self.assertEqual(q.status, 'single_phase_candidate')
        self.assertIsNone(q.beta)
        self.assertIsNone(q.liquid_composition)
        self.assertIsNone(q.vapor_composition)

    def test_iteration_failure_has_no_partial_solution(self):
        q = flash_tp(fixture(), TPConditions(250, 2e6), kij=zero_kij(2), max_iterations=1)
        self.assertEqual(q.status, 'inconclusive')
        self.assertIsNone(q.beta)
        self.assertTrue(any('iteration limit' in reason for reason in q.attempts))

    def test_inconclusive_feed_search_stops_flash(self):
        q = flash_tp(fixture(), TPConditions(450, 1e5), kij=zero_kij(2), stability_max_iterations=1)
        self.assertEqual(q.status, 'inconclusive')
        self.assertIsNone(q.beta)

    def test_failed_postcheck_cannot_be_accepted(self):
        from petroflash import flash
        real = flash.search_pr_stability
        count = 0
        def fail_post(*args, **kwargs):
            nonlocal count
            count += 1
            result = real(*args, **kwargs)
            return result if count == 1 else replace(result, status='inconclusive')
        with patch.object(flash, 'search_pr_stability', side_effect=fail_post):
            q = flash_tp(fixture(), TPConditions(250, 2e6), kij=zero_kij(2))
        self.assertEqual(q.status, 'inconclusive')
        self.assertIsNone(q.beta)

    def test_invalid_controls_and_unsupported_active_component(self):
        for args in (dict(max_iterations=0), dict(stability_max_iterations=0),
                     dict(fugacity_tolerance=float('nan'))):
            with self.assertRaises(ValueError):
                flash_tp(fixture(), TPConditions(250, 2e6), kij=zero_kij(2), **args)
        with self.assertRaises(TypeError):
            flash_tp(fixture(), TPConditions(250, 2e6), kij=zero_kij(2), max_iterations=True)
        mix = fixture()
        mix.components[0].formula = 'H2O'
        with self.assertRaisesRegex(ValueError, 'hydrocarbon'):
            flash_tp(mix, TPConditions(250, 2e6), kij=zero_kij(2))


if __name__ == '__main__':
    unittest.main()
