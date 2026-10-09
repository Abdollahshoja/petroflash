"""Algebraic limits and scaling checks, not experimental validation."""

import unittest
from dataclasses import FrozenInstanceError
from types import SimpleNamespace

from petroflash.pr_pure import R, component_pr_parameters, pr_pure_parameters


class TestPRPure(unittest.TestCase):
    def params(self, **changes):
        inputs = dict(temperature_k=300.0, pressure_pa=1e6,
                      critical_temperature_k=200.0,
                      critical_pressure_pa=4e6, acentric_factor=0.0)
        inputs.update(changes)
        return pr_pure_parameters(**inputs)

    def test_critical_point_dimensionless_constants(self):
        q = self.params(temperature_k=200, pressure_pa=4e6)
        self.assertEqual(q.alpha, 1.0)
        self.assertEqual(q.a_t, q.a_c)
        self.assertAlmostEqual(q.A, 0.45724, places=14)
        self.assertAlmostEqual(q.B, 0.07780, places=14)

    def test_pressure_scaling(self):
        q, r = self.params(), self.params(pressure_pa=2e6)
        self.assertEqual(q.a_t, r.a_t)
        self.assertEqual(q.b, r.b)
        self.assertAlmostEqual(r.A, 2*q.A)
        self.assertAlmostEqual(r.B, 2*q.B)

    def test_zero_omega_and_temperature_response(self):
        cold = self.params(temperature_k=50)
        self.assertEqual(cold.m, 0.37464)
        self.assertAlmostEqual(cold.alpha, 1.18732**2, places=14)
        self.assertAlmostEqual(cold.b, 0.07780*R*200/4e6, places=14)
        self.assertGreater(cold.a_t, self.params().a_t)
        self.assertEqual(cold.b, self.params().b)

    def test_negative_omega_and_immutable_result(self):
        q = self.params(acentric_factor=-0.1)
        self.assertAlmostEqual(q.m, 0.2177148)
        with self.assertRaises(FrozenInstanceError):
            q.b = 0

    def test_invalid_inputs_and_numerical_overflow(self):
        for field in ("temperature_k", "pressure_pa",
                      "critical_temperature_k", "critical_pressure_pa",
                      "acentric_factor"):
            for value in (True, "300", None):
                with self.subTest(field=field, value=value):
                    with self.assertRaises(TypeError):
                        self.params(**{field: value})
            for value in (float("nan"), float("inf"), -float("inf")):
                with self.assertRaises(ValueError):
                    self.params(**{field: value})
            if field != "acentric_factor":
                for value in (0, -1):
                    with self.assertRaises(ValueError):
                        self.params(**{field: value})
        with self.assertRaises(ValueError):
            self.params(critical_temperature_k=1e308)

    def test_component_adapter(self):
        component = SimpleNamespace(
            critical_temperature=SimpleNamespace(value=200.0),
            critical_pressure=SimpleNamespace(value=4e6),
            acentric_factor=SimpleNamespace(value=0.0))
        conditions = SimpleNamespace(temperature_k=300.0, pressure_pa=1e6)
        self.assertEqual(component_pr_parameters(component, conditions), self.params())


if __name__ == "__main__":
    unittest.main()
