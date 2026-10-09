"""Multi-start outcomes, independent negative witnesses and failed searches."""

import unittest
from dataclasses import FrozenInstanceError
from types import SimpleNamespace as S
from unittest.mock import patch

from petroflash.conditions import TPConditions
from petroflash.pr_mixing import zero_kij
from petroflash.stability import search_pr_stability
from petroflash.tpd import evaluate_mixture_pr_tpd


def fixture():
    # Rounded synthetic fixture properties; not an experimental benchmark.
    cs = tuple(S(name=n, critical_temperature=S(value=t), critical_pressure=S(value=p),
                 acentric_factor=S(value=o)) for n, t, p, o in (
        ('methane', 190.56, 4599200, .01142), ('n-butane', 425.12, 3796000, .2)))
    return S(components=cs, mole_fractions=(.5, .5))


class TestStability(unittest.TestCase):
    def test_negative_witness_recomputed_independently(self):
        mix, tp = fixture(), TPConditions(250, 2e6)
        q = search_pr_stability(mix, tp, kij=zero_kij(2))
        self.assertEqual(q.status, 'unstable')
        self.assertLess(q.minimum_tpd, -0.8)
        witness = evaluate_mixture_pr_tpd(mix, tp, kij=zero_kij(2),
            trial_mole_fractions=q.witness_composition)
        self.assertAlmostEqual(q.minimum_tpd, witness.minimum_tpd, places=12)
        self.assertTrue(all(s.converged for s in q.starts))
        # A separate grid also detects a negative trial without iteration.
        grid = tuple(evaluate_mixture_pr_tpd(mix, tp, kij=zero_kij(2),
            trial_mole_fractions=(x, 1-x)).minimum_tpd for x in (.1, .3, .7, .9, .99))
        self.assertLess(min(grid), 0)

    def test_no_negative_outcome_is_not_named_stable(self):
        q = search_pr_stability(fixture(), TPConditions(450, 1e5), kij=zero_kij(2))
        self.assertEqual(q.status, 'no_negative_tpd_found')
        self.assertTrue(all(s.converged for s in q.starts))
        self.assertGreaterEqual(q.minimum_tpd, -q.tpd_tolerance)
        with self.assertRaises(FrozenInstanceError):
            q.status = 'stable'

    def test_iteration_limit_and_numerical_failure_are_inconclusive(self):
        mix, tp = fixture(), TPConditions(450, 1e5)
        q = search_pr_stability(mix, tp, kij=zero_kij(2), max_iterations=1)
        self.assertEqual(q.status, 'inconclusive')
        self.assertTrue(any(not s.converged for s in q.starts))
        from petroflash import stability
        real = stability.evaluate_pr_phase
        count = 0
        def fail_trials(**args):
            nonlocal count
            count += 1
            if count == 1:
                return real(**args)
            raise ArithmeticError('injected root failure')
        with patch.object(stability, 'evaluate_pr_phase', side_effect=fail_trials):
            r = search_pr_stability(mix, tp, kij=zero_kij(2))
        self.assertEqual(r.status, 'inconclusive')
        self.assertIsNone(r.minimum_tpd)
        self.assertTrue(all('injected root failure' in s.reason for s in r.starts))

    def test_zero_support_and_permutation(self):
        mix, tp = fixture(), TPConditions(250, 2e6)
        q = search_pr_stability(mix, tp, kij=zero_kij(2))
        rev = S(components=tuple(reversed(mix.components)), mole_fractions=(.5, .5))
        r = search_pr_stability(rev, tp, kij=zero_kij(2))
        self.assertEqual(q.status, r.status)
        self.assertAlmostEqual(q.minimum_tpd, r.minimum_tpd, places=10)
        zero = S(components=mix.components, mole_fractions=(1.0, 0.0))
        r = search_pr_stability(zero, TPConditions(450, 1e5), kij=zero_kij(2))
        self.assertEqual(r.status, 'no_negative_tpd_found')
        self.assertTrue(all(s.witness_composition[1] == 0 for s in r.starts))

    def test_negative_sample_overrides_iteration_failure(self):
        q = search_pr_stability(fixture(), TPConditions(250, 2e6), kij=zero_kij(2),
                                max_iterations=1)
        self.assertEqual(q.status, 'unstable')
        self.assertLess(q.minimum_tpd, -q.tpd_tolerance)
        self.assertTrue(any(not s.converged for s in q.starts))

    def test_invalid_controls(self):
        for args in (dict(damping=0), dict(damping=1.1), dict(max_iterations=0),
                     dict(stationarity_tolerance=0), dict(tpd_tolerance=float('nan'))):
            with self.assertRaises(ValueError):
                search_pr_stability(fixture(), TPConditions(300, 1e6), kij=zero_kij(2), **args)
        with self.assertRaises(TypeError):
            search_pr_stability(fixture(), TPConditions(300, 1e6), kij=zero_kij(2),
                                max_iterations=True)


if __name__ == '__main__':
    unittest.main()
