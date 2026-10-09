"""Regression for Gibbs acceptance near phase appearance; no external packages."""
import unittest
from types import SimpleNamespace as S
from petroflash.conditions import TPConditions
from petroflash.flash import flash_tp, _gibbs_assessment
from petroflash.rachford_rice import solve_rachford_rice


class TestFlashBoundary(unittest.TestCase):
    def solve(self, epsilon, dew=False):
        # Independent PR1976 simultaneous fugacity solution for these exact data.
        x, y = 0.1642320714807604, 0.9712431055926647
        z = y-epsilon*(y-x) if dew else x+epsilon*(y-x)
        components = tuple(S(name=n,formula=f,critical_temperature=S(value=t),
            critical_pressure=S(value=p),acentric_factor=S(value=o)) for n,f,t,p,o in (
            ('methane','CH4',190.564,4599200,.01142),
            ('n-butane','C4H10',425.125,3796000,.201)))
        mixture=S(components=components,mole_fractions=(z,1-z))
        return flash_tp(mixture,TPConditions(250,2e6),kij=((0,0),(0,0)))

    def test_small_vapor_fraction_resolved(self):
        q=self.solve(1e-6)
        self.assertEqual(q.status,'two_phase')
        self.assertAlmostEqual(q.beta,1e-6,delta=3e-9)
        self.assertLess(q.gibbs_change_rt,-q.gibbs_resolution_rt)
        self.assertLess(q.normalization_residual,2e-14)

    def test_small_liquid_fraction_resolved(self):
        q=self.solve(1e-6,dew=True)
        self.assertEqual(q.status,'two_phase')
        self.assertAlmostEqual(1-q.beta,1e-6,delta=3e-9)
        self.assertLess(q.gibbs_change_rt,-q.gibbs_resolution_rt)

    def test_extreme_bubble_boundary_remains_unresolved(self):
        q=self.solve(1e-8)
        self.assertEqual(q.status,'inconclusive')
        self.assertIsNone(q.beta)
        self.assertTrue(any('Gibbs decrease is numerically unresolved' in s for s in q.attempts))

    def test_extreme_dew_boundary_remains_unresolved(self):
        q=self.solve(1e-8,dew=True)
        self.assertEqual(q.status,'inconclusive')
        self.assertIsNone(q.beta)
        self.assertTrue(any('Gibbs_resolution_RT=' in s for s in q.attempts))

    def test_gibbs_increase_and_identity_are_not_decreases(self):
        z=(.5,.5)
        delta,resolution=_gibbs_assessment(z,z,z,.5,(0,0),(1,1),(1,1))
        self.assertGreater(delta,resolution)
        delta,resolution=_gibbs_assessment(z,z,z,.5,(0,0),(0,0),(0,0))
        self.assertLessEqual(abs(delta),resolution)

    def test_rr_tolerance_validation_and_exact_root(self):
        self.assertAlmostEqual(solve_rachford_rice((.5,.5),(2,.5),residual_tolerance=1e-14),.5)
        for value in (0,-1,float('nan'),True):
            with self.subTest(value=value), self.assertRaises((TypeError,ValueError)):
                solve_rachford_rice((.5,.5),(2,.5),residual_tolerance=value)

if __name__=='__main__':
    unittest.main()
