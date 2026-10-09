"""TPD identities, ideal limit, support restriction and PR integration."""

import unittest
from math import log
from types import SimpleNamespace

from petroflash.tpd import (tangent_plane_distance, evaluate_pr_tpd,
                           evaluate_mixture_pr_tpd)
from petroflash.pr_phase import evaluate_pr_phase
from petroflash.pr_mixing import zero_kij
from petroflash.conditions import TPConditions


class TestTPD(unittest.TestCase):
    def value(self, **changes):
        args = dict(reference_mole_fractions=(0.4, 0.6), trial_mole_fractions=(0.4, 0.6),
                    reference_ln_phi=(0, 0), trial_ln_phi=(0, 0))
        args.update(changes)
        return tangent_plane_distance(**args)

    def test_reference_identity_and_ideal_kl(self):
        self.assertEqual(self.value(reference_ln_phi=(-1, 2), trial_ln_phi=(-1, 2)), 0)
        v = self.value(trial_mole_fractions=(0.7, 0.3))
        expected = 0.7*log(0.7/0.4)+0.3*log(0.3/0.6)
        self.assertAlmostEqual(v, expected, places=14)
        self.assertGreater(v, 0)

    def test_negative_value_is_retained(self):
        # Synthetic coefficients check arithmetic; not a real-mixture benchmark.
        self.assertEqual(self.value(trial_ln_phi=(-1, -1)), -1)

    def test_zero_fractions_and_support_restriction(self):
        self.assertAlmostEqual(self.value(trial_mole_fractions=(1, 0)), log(1/0.4))
        self.assertEqual(self.value(reference_mole_fractions=(1, 0),
                                   trial_mole_fractions=(1, 0)), 0)
        with self.assertRaises(ValueError):
            self.value(reference_mole_fractions=(1, 0), trial_mole_fractions=(0.9, 0.1))

    def test_invalid_vectors(self):
        for changes in (dict(trial_mole_fractions=(0.1, 0.1)),
            dict(reference_mole_fractions=()), dict(trial_mole_fractions=(1,)),
            dict(trial_mole_fractions=(-0.1, 1.1)), dict(reference_ln_phi=(0,)),
            dict(trial_ln_phi=(0, float('inf')))):
            with self.assertRaises(ValueError):
                self.value(**changes)
        with self.assertRaises(TypeError):
            self.value(trial_ln_phi=(True, 0))

    def test_pr_same_composition_compares_all_roots(self):
        args = dict(a_t=(0.8,), b=(3e-5,), kij=zero_kij(1),
                    temperature_k=300, pressure_pa=1e5)
        reference = evaluate_pr_phase(mole_fractions=(1,), **args)
        self.assertEqual(len(reference.candidates), 3)
        best = reference.preferred_candidates[0]
        q = evaluate_pr_tpd(reference_mole_fractions=(1,), trial_mole_fractions=(1,),
                            reference_ln_phi=best.ln_phi, **args)
        self.assertAlmostEqual(q.minimum_tpd, 0, places=13)
        worst = max(reference.candidates, key=lambda s: s.g_residual_rt)
        r = evaluate_pr_tpd(reference_mole_fractions=(1,), trial_mole_fractions=(1,),
                            reference_ln_phi=worst.ln_phi, **args)
        self.assertLess(r.minimum_tpd, 0)
        self.assertEqual(len(q.tpd_values), 3)

    def test_feed_adapter_and_index_validation(self):
        c = SimpleNamespace(critical_temperature=SimpleNamespace(value=200),
            critical_pressure=SimpleNamespace(value=4e6), acentric_factor=SimpleNamespace(value=0))
        mix = SimpleNamespace(components=(c,), mole_fractions=(1.0,))
        args = dict(trial_mole_fractions=(1,), kij=zero_kij(1))
        q = evaluate_mixture_pr_tpd(mix, TPConditions(300, 1e6), **args)
        self.assertAlmostEqual(q.minimum_tpd, 0, places=13)
        with self.assertRaises(ValueError):
            evaluate_mixture_pr_tpd(mix, TPConditions(300, 1e6), reference_root_index=99, **args)
        with self.assertRaises(TypeError):
            evaluate_mixture_pr_tpd(mix, TPConditions(300, 1e6), reference_root_index=True, **args)


if __name__ == '__main__':
    unittest.main()
