"""Independent exact cases and a rounded Whitson Problem 15 benchmark."""

import unittest
from petroflash.rachford_rice import solve_rachford_rice


class TestRachfordRice(unittest.TestCase):
    def test_exact_binary_and_material_balance(self):
        z, k = (0.5, 0.5), (2.0, 0.5)
        beta = solve_rachford_rice(z, k)
        self.assertAlmostEqual(beta, 0.5, places=12)
        x = tuple(zi / (1 + beta * (ki - 1)) for zi, ki in zip(z, k))
        y = tuple(ki * xi for ki, xi in zip(k, x))
        self.assertAlmostEqual(sum(x), 1.0, places=12)
        self.assertAlmostEqual(sum(y), 1.0, places=12)
        for zi, xi, yi in zip(z, x, y):
            self.assertAlmostEqual((1 - beta) * xi + beta * yi, zi)

    def test_whitson_problem_15_rounded_table(self):
        beta = solve_rachford_rice((0.20, 0.32, 0.48), (9.208, 1.439, 0.358))
        # The printed beta=0.48242 does not solve the printed K dataset.
        # Verify the defining equation without claiming book reproduction.
        z, k = (0.20, 0.32, 0.48), (9.208, 1.439, 0.358)
        residual = sum(zi * (ki - 1) / (1 + beta * (ki - 1))
                       for zi, ki in zip(z, k))
        self.assertLess(abs(residual), 1e-12)
        self.assertTrue(0 < beta < 1)

    def test_endpoint_roots(self):
        self.assertAlmostEqual(solve_rachford_rice((0.5, 0.5), (1.5, 0.5)), 0, delta=1e-10)
        self.assertAlmostEqual(solve_rachford_rice((0.5, 0.5), (2, 2 / 3)), 1, delta=1e-10)

    def test_no_bracket_and_degeneracy(self):
        for k in ((2, 3), (0.2, 0.3), (1, 1)):
            with self.subTest(k=k), self.assertRaises(ValueError):
                solve_rachford_rice((0.5, 0.5), k)

    def test_zero_component_and_permutation(self):
        self.assertAlmostEqual(solve_rachford_rice((0, 0.5, 0.5), (100, 0.5, 2)), 0.5)

    def test_invalid_inputs(self):
        for z, k in (((), ()), ((1,), (1, 2)), ((-0.5, 1.5), (2, 0.5)),
                     ((0.4, 0.4), (2, 0.5)), ((0.5, 0.5), (0, 2)),
                     ((float('nan'), 0.5), (2, 0.5)),
                     ((0.5, 0.5), (float('inf'), 0.5))):
            with self.subTest(z=z, k=k), self.assertRaises(ValueError):
                solve_rachford_rice(z, k)
        with self.assertRaises(TypeError):
            solve_rachford_rice((True,), (2,))


if __name__ == '__main__':
    unittest.main()
