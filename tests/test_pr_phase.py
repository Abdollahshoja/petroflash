"""Fixed-composition Gibbs ranking, ties and adapter checks."""

import unittest
from dataclasses import FrozenInstanceError
from math import log, sqrt
from types import SimpleNamespace

from petroflash.pr_phase import evaluate_pr_phase, evaluate_mixture_pr_phase
from petroflash.pr_mixing import zero_kij
from petroflash.conditions import TPConditions


class TestPRPhase(unittest.TestCase):
    def pure(self, **changes):
        args = dict(mole_fractions=(1,), a_t=(0.8,), b=(3e-5,), kij=zero_kij(1),
                    temperature_k=300, pressure_pa=1e5)
        args.update(changes)
        return evaluate_pr_phase(**args)

    def test_three_roots_independent_gibbs_ranking(self):
        result = self.pure()
        self.assertEqual(len(result.candidates), 3)
        A, B = result.parameters.A, result.parameters.B
        reference = tuple(state.z-1-log(state.z-B)-A/(2*sqrt(2)*B)*log(
            (state.z+(1+sqrt(2))*B)/(state.z+(1-sqrt(2))*B))
            for state in result.candidates)
        index = min(range(3), key=lambda i: reference[i])
        self.assertEqual(result.preferred_indices, (index,))
        self.assertAlmostEqual(result.minimum_g_residual_rt, reference[index], places=12)
        # Retaining all roots matters: later flash iterations may track branches.
        self.assertEqual(tuple(s.z for s in result.candidates), result.roots.admissible_roots)

    def test_one_root_and_immutable_output(self):
        q = self.pure(a_t=(0.2,), pressure_pa=1e6)
        self.assertEqual(len(q.candidates), 1)
        self.assertEqual(q.preferred_indices, (0,))
        self.assertEqual(q.preferred_candidates, q.candidates)
        with self.assertRaises(FrozenInstanceError):
            q.minimum_g_residual_rt = 0

    def test_tolerance_reports_ties_without_arbitrary_choice(self):
        q = self.pure()
        spread = max(s.g_residual_rt for s in q.candidates)-q.minimum_g_residual_rt
        # Deliberately loose tolerance tests tie-reporting policy, not coexistence.
        r = self.pure(gibbs_tolerance=spread+1)
        self.assertEqual(r.preferred_indices, (0, 1, 2))
        self.assertEqual(len(r.preferred_candidates), 3)
        r = self.pure(gibbs_tolerance=0)
        self.assertEqual(len(r.preferred_candidates), 1)

    def test_generators_and_permutation(self):
        args = dict(mole_fractions=(0.4, 0.6), a_t=(0.2, 0.8), b=(2e-5, 5e-5),
                    kij=((0, 0.05), (0.05, 0)), temperature_k=300, pressure_pa=1e6)
        q = evaluate_pr_phase(**args)
        gen = dict(args)
        for name in ('mole_fractions', 'a_t', 'b'):
            gen[name] = iter(args[name])
        gen['kij'] = (iter(row) for row in args['kij'])
        self.assertEqual(q, evaluate_pr_phase(**gen))
        rev = dict(args)
        for name in ('mole_fractions', 'a_t', 'b'):
            rev[name] = tuple(reversed(args[name]))
        r = evaluate_pr_phase(**rev)
        self.assertAlmostEqual(q.minimum_g_residual_rt, r.minimum_g_residual_rt, places=13)
        self.assertEqual(q.preferred_indices, r.preferred_indices)
        for a, b in zip(q.candidates[0].ln_phi, reversed(r.candidates[0].ln_phi)):
            self.assertAlmostEqual(a, b, places=13)

    def test_invalid_tolerance_and_composition(self):
        for tol in (-1, float('inf'), float('nan')):
            with self.assertRaises(ValueError):
                self.pure(gibbs_tolerance=tol)
        with self.assertRaises(TypeError):
            self.pure(gibbs_tolerance=True)
        with self.assertRaises(ValueError):
            self.pure(mole_fractions=(0.5,))

    def test_adapter(self):
        c = SimpleNamespace(critical_temperature=SimpleNamespace(value=200),
            critical_pressure=SimpleNamespace(value=4e6),
            acentric_factor=SimpleNamespace(value=0))
        mixture = SimpleNamespace(components=(c,), mole_fractions=(1.0,))
        q = evaluate_mixture_pr_phase(mixture, TPConditions(300, 1e6), kij=zero_kij(1))
        self.assertEqual(q.preferred_indices, (0,))
        self.assertAlmostEqual(q.minimum_g_residual_rt, q.candidates[0].ln_phi[0])


if __name__ == '__main__':
    unittest.main()
