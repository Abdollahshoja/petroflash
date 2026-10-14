"""Regression checks for supplied PR mixture parameters."""
import unittest
from unittest.mock import patch
from petroflash.pr_mixing import pr_mixture_parameters
from petroflash.pr_roots import solve_pr_roots
from petroflash.pr_fugacity import pr_log_fugacity
from petroflash.pr_phase import evaluate_pr_phase, _evaluate_pr_phase_cached

class TestFugacityParameters(unittest.TestCase):
    def setUp(self):
        _evaluate_pr_phase_cached.cache_clear()
        self.args = dict(mole_fractions=(0.4, 0.6), a_t=(0.8, 1.2),
                         b=(0.00004, 0.00006), kij=((0.0, 0.02), (0.02, 0.0)),
                         temperature_k=300.0, pressure_pa=100000.0)
        self.q = pr_mixture_parameters(**self.args)
        self.z = solve_pr_roots(A=self.q.A, B=self.q.B).admissible_roots[-1]

    def tearDown(self):
        _evaluate_pr_phase_cached.cache_clear()

    def test_matching_parameters_preserve_result(self):
        expected = pr_log_fugacity(**self.args, z=self.z)
        actual = pr_log_fugacity(**self.args, z=self.z, parameters=self.q)
        self.assertEqual(actual, expected)
        generated = dict(self.args)
        for field in ('mole_fractions', 'a_t', 'b'):
            generated[field] = iter(generated[field])
        generated['kij'] = (iter(row) for row in self.args['kij'])
        self.assertEqual(pr_log_fugacity(**generated, z=self.z, parameters=self.q), expected)

    def test_mismatched_parameters_are_rejected(self):
        changes = dict(pressure_pa=200000.0, temperature_k=310.0,
                       mole_fractions=(0.6, 0.4), a_t=(0.9, 1.2),
                       b=(0.00005, 0.00006), kij=((0.0, 0.03), (0.03, 0.0)))
        for field, value in changes.items():
            with self.subTest(field=field), self.assertRaises(ValueError):
                pr_log_fugacity(**dict(self.args, **{field: value}),
                                z=self.z, parameters=self.q)

    def test_supplied_parameters_do_not_bypass_validation(self):
        for field, value in (('pressure_pa', -1.0), ('pressure_pa', True),
                             ('mole_fractions', (True, 0.0)),
                             ('kij', ((False, 0.02), (0.02, 0.0)))):
            with self.subTest(field=field, value=value):
                with self.assertRaises((TypeError, ValueError)):
                    pr_log_fugacity(**dict(self.args, **{field: value}),
                                    z=self.z, parameters=self.q)
        with self.assertRaises(TypeError):
            pr_log_fugacity(**self.args, z=self.z, parameters=object())

    def test_phase_reuses_mixing_parameters(self):
        with patch('petroflash.pr_phase.pr_mixture_parameters',
                   wraps=pr_mixture_parameters) as mixing:
            result = evaluate_pr_phase(**self.args)
            self.assertEqual(mixing.call_count, 1)
        for state in result.candidates:
            self.assertEqual(state, pr_log_fugacity(**self.args, z=state.z))

if __name__ == '__main__':
    unittest.main()
