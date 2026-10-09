"""Analytic mixing cases, permutation invariance and invalid inputs."""

import unittest
from dataclasses import FrozenInstanceError
from types import SimpleNamespace

from petroflash.pr_mixing import (mixture_pr_parameters,
                                 pr_mixture_parameters, zero_kij)
from petroflash.pr_pure import component_pr_parameters


class TestPRMixing(unittest.TestCase):
    def mix(self, **changes):
        args = dict(mole_fractions=[0.25, 0.75], a_t=[1.0, 4.0],
                    b=[1e-5, 3e-5], kij=[[0.0, 0.2], [0.2, 0.0]],
                    temperature_k=300, pressure_pa=1e6)
        args.update(changes)
        return pr_mixture_parameters(**args)

    def test_analytic_binary(self):
        q = self.mix()
        self.assertAlmostEqual(q.a_m, 2.9125)
        self.assertAlmostEqual(q.b_m, 2.5e-5)
        self.assertEqual(q.a_ij, ((1.0, 1.6), (1.6, 4.0)))
        self.assertAlmostEqual(q.a_row_sums[0], 1.45)
        self.assertAlmostEqual(q.a_row_sums[1], 3.4)
        self.assertAlmostEqual(self.mix(kij=zero_kij(2)).a_m, 3.0625)
        self.assertGreater(self.mix(kij=[[0, -0.2], [-0.2, 0]]).a_m, q.a_m)

    def test_pure_limit_and_zero_component(self):
        q = self.mix(mole_fractions=[1.0, 0.0])
        r = self.mix(mole_fractions=[1.0], a_t=[1.0], b=[1e-5], kij=zero_kij(1))
        self.assertEqual((q.a_m, q.b_m, q.A, q.B), (r.a_m, r.b_m, r.A, r.B))

    def test_permutation_and_pressure_scaling(self):
        q = self.mix()
        r = self.mix(mole_fractions=[0.75, 0.25], a_t=[4, 1], b=[3e-5, 1e-5])
        self.assertAlmostEqual(q.a_m, r.a_m)
        self.assertAlmostEqual(q.b_m, r.b_m)
        self.assertEqual(q.a_row_sums, tuple(reversed(r.a_row_sums)))
        r = self.mix(pressure_pa=2e6)
        self.assertEqual(q.a_m, r.a_m)
        self.assertEqual(q.b_m, r.b_m)
        self.assertAlmostEqual(2*q.A, r.A)
        self.assertAlmostEqual(2*q.B, r.B)

    def test_invalid_inputs(self):
        for changes in (
            dict(mole_fractions=[]), dict(mole_fractions=[0.2, 0.3]),
            dict(mole_fractions=[-0.1, 1.1]), dict(a_t=[1]), dict(a_t=[-1, 4]),
            dict(b=[0, 1]), dict(kij=[[0, 0.2], [0.3, 0]]),
            dict(kij=[[1, 0], [0, 0]]), dict(kij=[[0]]),
            dict(kij=[[0, float('nan')], [float('nan'), 0]]),
            dict(temperature_k=0), dict(pressure_pa=float('inf')),
            dict(a_t=[0, 0]), dict(kij=[[0, 100], [100, 0]]),
            dict(pressure_pa=1e308),
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.mix(**changes)
        with self.assertRaises(TypeError):
            self.mix(mole_fractions=[True, 0])
        with self.assertRaises(TypeError):
            self.mix(kij=[[0, False], [False, 0]])
        with self.assertRaises(TypeError):
            zero_kij(True)
        with self.assertRaises(ValueError):
            zero_kij(0)

    def test_inputs_copied_and_no_normalization(self):
        matrix = [[0, 0.2], [0.2, 0]]
        q = self.mix(kij=matrix)
        matrix[0][1] = 0.9
        self.assertEqual(q.a_ij[0][1], 1.6)
        with self.assertRaises(FrozenInstanceError):
            q.a_m = 1
        r = self.mix(mole_fractions=[0.25, 0.75 + 5e-11])
        self.assertGreater(r.a_m, q.a_m)

    def test_mixture_adapter(self):
        component = SimpleNamespace(critical_temperature=SimpleNamespace(value=200),
            critical_pressure=SimpleNamespace(value=4e6),
            acentric_factor=SimpleNamespace(value=0))
        mixture = SimpleNamespace(components=(component,), mole_fractions=(1.0,))
        conditions = SimpleNamespace(temperature_k=300, pressure_pa=1e6)
        q = mixture_pr_parameters(mixture, conditions, kij=zero_kij(1))
        pure = component_pr_parameters(component, conditions)
        self.assertAlmostEqual(q.a_m, pure.a_t)
        self.assertAlmostEqual(q.b_m, pure.b)
        self.assertAlmostEqual(q.A, pure.A)
        self.assertAlmostEqual(q.B, pure.B)


if __name__ == '__main__':
    unittest.main()
