"""Root structure and EOS residual checks, not a phase stability test."""

import unittest
from dataclasses import FrozenInstanceError

from petroflash.pr_roots import PRRootError, pr_cubic_residual, solve_pr_roots


class TestPRRoots(unittest.TestCase):
    def test_ideal_gas_limit(self):
        q = solve_pr_roots(A=0, B=0)
        self.assertEqual(q.real_roots, (0.0, 1.0))
        self.assertEqual(q.admissible_roots, (1.0,))

    def test_exact_double_root(self):
        # At B=0 and A=1/4 the polynomial is Z*(Z-1/2)^2.
        q = solve_pr_roots(A=0.25, B=0)
        self.assertEqual(q.real_roots, (0.0, 0.5))
        self.assertEqual(q.admissible_roots, (0.5,))

    def test_three_roots_and_vieta(self):
        A, B = 0.1, 0.01
        q = solve_pr_roots(A=A, B=B)
        self.assertEqual(len(q.real_roots), 3)
        self.assertEqual(len(q.admissible_roots), 3)
        x, y, z = q.real_roots
        self.assertAlmostEqual(x+y+z, 1-B, places=13)
        self.assertAlmostEqual(x*y+x*z+y*z, A-2*B-3*B*B, places=13)
        self.assertAlmostEqual(x*y*z, A*B-B*B-B**3, places=13)
        self.assertLess(max(q.scaled_residuals), 1e-13)

    def test_one_root_and_original_eos(self):
        # User's feed A/B, all kij=0. This is not a phase classification.
        A, B = 1.872908966716874, 0.22347437618761656
        q = solve_pr_roots(A=A, B=B)
        self.assertEqual(len(q.real_roots), 1)
        z = q.admissible_roots[0]
        self.assertGreater(z, B)
        self.assertAlmostEqual(1/(z-B)-A/(z*z+2*B*z-B*B), 1, places=12)
        self.assertLess(abs(pr_cubic_residual(z, A=A, B=B)), 1e-13)

    def test_excludes_nonphysical_roots(self):
        # With A=0, the EOS reduces to Z=1+B; extra cubic roots are artifacts.
        q = solve_pr_roots(A=0, B=0.1)
        self.assertEqual(len(q.real_roots), 3)
        self.assertEqual(len(q.admissible_roots), 1)
        self.assertAlmostEqual(q.admissible_roots[0], 1.1, places=13)
        with self.assertRaises(FrozenInstanceError):
            q.real_roots = ()

    def test_invalid_inputs_and_iteration_limit(self):
        for value in (float('nan'), float('inf'), -1):
            for key in ('A', 'B'):
                args = dict(A=0.1, B=0.01); args[key] = value
                with self.assertRaises(ValueError):
                    solve_pr_roots(**args)
        for value in (True, '1', None):
            with self.assertRaises(TypeError):
                solve_pr_roots(A=value, B=0.01)
        with self.assertRaises(TypeError):
            solve_pr_roots(A=0.1, B=0.01, max_iterations=True)
        with self.assertRaises(ValueError):
            solve_pr_roots(A=0.1, B=0.01, max_iterations=0)
        with self.assertRaises(PRRootError):
            solve_pr_roots(A=0.1, B=0.01, max_iterations=1)
        with self.assertRaises(PRRootError):
            solve_pr_roots(A=1e308, B=1e308)

    def test_nearly_repeated_roots_report_ambiguity(self):
        with self.assertRaisesRegex(PRRootError, 'Nearly repeated'):
            solve_pr_roots(A=0.25+1e-15, B=0)


if __name__ == '__main__':
    unittest.main()
