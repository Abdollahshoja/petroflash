"""Limits, Gibbs identity and independent numerical chemical potentials."""

import unittest
from dataclasses import FrozenInstanceError
from math import log, sqrt
from types import SimpleNamespace

from petroflash.pr_fugacity import pr_log_fugacity, mixture_pr_log_fugacity
from petroflash.pr_mixing import pr_mixture_parameters, zero_kij
from petroflash.pr_pure import component_pr_parameters
from petroflash.pr_roots import solve_pr_roots


class TestPRFugacity(unittest.TestCase):
    def state(self, *, x=(0.4, 0.6), aa=(0.2, 0.8), bb=(2e-5, 5e-5),
              kk=((0, 0.05), (0.05, 0)), p=1e6, root=-1):
        args = dict(mole_fractions=x, a_t=aa, b=bb, kij=kk,
                    temperature_k=300, pressure_pa=p)
        q = pr_mixture_parameters(**args)
        z = solve_pr_roots(A=q.A, B=q.B).admissible_roots[root]
        return pr_log_fugacity(**args, z=z), q

    def test_pure_component_formula(self):
        _, mix = self.state(x=(1,), aa=(0.8,), bb=(3e-5,), kk=zero_kij(1), p=1e5)
        roots = solve_pr_roots(A=mix.A, B=mix.B).admissible_roots
        self.assertEqual(len(roots), 3)
        for i in range(3):
            q, mix = self.state(x=(1,), aa=(0.8,), bb=(3e-5,),
                                kk=zero_kij(1), p=1e5, root=i)
            expected = q.z-1-log(q.z-mix.B)-mix.A/(2*sqrt(2)*mix.B)*log(
                (q.z+(1+sqrt(2))*mix.B)/(q.z+(1-sqrt(2))*mix.B))
            self.assertAlmostEqual(q.ln_phi[0], expected, places=12)
            self.assertEqual(q.g_residual_rt, q.ln_phi[0])

    def test_low_pressure_limit(self):
        q, _ = self.state(p=0.01)
        self.assertLess(max(abs(v) for v in q.ln_phi), 1e-8)

    def test_gibbs_identity(self):
        q, mix = self.state()
        expected = q.z-1-log(q.z-mix.B)-mix.A/(2*sqrt(2)*mix.B)*log(
            (q.z+(1+sqrt(2))*mix.B)/(q.z+(1-sqrt(2))*mix.B))
        self.assertAlmostEqual(q.g_residual_rt, expected, places=13)
        with self.assertRaises(FrozenInstanceError):
            q.z = 1

    def test_numerical_partial_molar_gibbs(self):
        # Differentiate n*g^R/(RT) independently, resolving Z after perturbation.
        # This checks the composition derivatives underlying individual ln(phi).
        def total_g(n):
            total = sum(n)
            x = tuple(v/total for v in n)
            _, mix = self.state(x=x)
            z = solve_pr_roots(A=mix.A, B=mix.B).admissible_roots[-1]
            g = z-1-log(z-mix.B)-mix.A/(2*sqrt(2)*mix.B)*log(
                (z+(1+sqrt(2))*mix.B)/(z+(1-sqrt(2))*mix.B))
            return total*g
        q, _ = self.state()
        h = 1e-5
        for i in range(2):
            plus, minus = [0.4, 0.6], [0.4, 0.6]
            plus[i] += h; minus[i] -= h
            derivative = (total_g(plus)-total_g(minus))/(2*h)
            self.assertAlmostEqual(derivative, q.ln_phi[i], places=8)

    def test_permutation_and_zero_fraction(self):
        q, _ = self.state()
        r, _ = self.state(x=(0.6, 0.4), aa=(0.8, 0.2), bb=(5e-5, 2e-5))
        for a, b in zip(q.ln_phi, reversed(r.ln_phi)):
            self.assertAlmostEqual(a, b, places=13)
        q, _ = self.state(x=(1, 0))
        r, _ = self.state(x=(1,), aa=(0.2,), bb=(2e-5,), kk=zero_kij(1))
        self.assertAlmostEqual(q.ln_phi[0], r.ln_phi[0], places=13)
        self.assertEqual(len(q.ln_phi), 2)

    def test_invalid_root_and_inputs(self):
        args = dict(mole_fractions=(0.4, 0.6), a_t=(0.2, 0.8), b=(2e-5, 5e-5),
                    kij=zero_kij(2), temperature_k=300, pressure_pa=1e6)
        for z in (0, -1, 1, float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                pr_log_fugacity(**args, z=z)
        with self.assertRaises(TypeError):
            pr_log_fugacity(**args, z=True)

    def test_real_interface_adapter(self):
        c = SimpleNamespace(critical_temperature=SimpleNamespace(value=200),
            critical_pressure=SimpleNamespace(value=4e6),
            acentric_factor=SimpleNamespace(value=0))
        tp = SimpleNamespace(temperature_k=300, pressure_pa=1e6)
        mix = SimpleNamespace(components=(c,), mole_fractions=(1.0,))
        pure = component_pr_parameters(c, tp)
        z = solve_pr_roots(A=pure.A, B=pure.B).admissible_roots[-1]
        result = mixture_pr_log_fugacity(mix, tp, kij=zero_kij(1), z=z)
        direct = pr_log_fugacity(mole_fractions=(1,), a_t=(pure.a_t,),
            b=(pure.b,), kij=zero_kij(1), temperature_k=300, pressure_pa=1e6, z=z)
        self.assertEqual(result, direct)


if __name__ == '__main__':
    unittest.main()
