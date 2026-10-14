"""Public input validation must not depend on cache history."""

import unittest

from petroflash.pr_phase import (
    evaluate_pr_phase,
    _evaluate_pr_phase_cached,
)
from petroflash.pr_mixing import (
    pr_mixture_parameters,
    _pure_and_kij_basis,
)


class TestCacheValidation(unittest.TestCase):
    def setUp(self):
        self.clear_caches()
        self.valid = dict(
            mole_fractions=(1.0,),
            a_t=(1.0,),
            b=(0.00004,),
            kij=((0.0,),),
            temperature_k=300.0,
            pressure_pa=100000.0,
        )

    @staticmethod
    def clear_caches():
        _evaluate_pr_phase_cached.cache_clear()
        _pure_and_kij_basis.cache_clear()

    def tearDown(self):
        self.clear_caches()

    def test_phase_rejects_booleans_with_cold_and_warm_cache(self):
        invalid_inputs = (
            ("mole_fractions", (True,)),
            ("a_t", (True,)),
            ("kij", ((False,),)),
        )
        for field, value in invalid_inputs:
            for warm in (False, True):
                with self.subTest(field=field, warm_cache=warm):
                    self.clear_caches()
                    if warm:
                        evaluate_pr_phase(**self.valid)

                    invalid = dict(self.valid)
                    invalid[field] = value

                    with self.assertRaises(TypeError):
                        evaluate_pr_phase(**invalid)

    def test_mixing_rejects_boolean_at_with_cold_and_warm_cache(self):
        for warm in (False, True):
            with self.subTest(warm_cache=warm):
                self.clear_caches()
                if warm:
                    pr_mixture_parameters(**self.valid)

                invalid = dict(self.valid, a_t=(True,))
                with self.assertRaises(TypeError):
                    pr_mixture_parameters(**invalid)


if __name__ == "__main__":
    unittest.main()
