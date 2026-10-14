"""Compare PR root Gibbs energies at one FIXED composition and TP.

Root preference here is not global mixture stability or a flash result.
All admissible candidates are retained for later branch-aware calculations.
"""

from dataclasses import dataclass
from functools import lru_cache

from .pr_fugacity import PRFugacity, pr_log_fugacity
from .pr_mixing import PRMixtureParameters, pr_mixture_parameters
from .pr_pure import _number, component_pr_parameters
from .pr_roots import PRRoots, solve_pr_roots


@dataclass(frozen=True, slots=True)
class PRPhaseEvaluation:
    """Fixed-composition root candidates; preferred_indices includes near ties."""

    parameters: PRMixtureParameters
    roots: PRRoots
    candidates: tuple[PRFugacity, ...]
    minimum_g_residual_rt: float
    preferred_indices: tuple[int, ...]
    gibbs_tolerance: float

    @property
    def preferred_candidates(self):
        return tuple(self.candidates[i] for i in self.preferred_indices)


@lru_cache(maxsize=2048)
def _evaluate_pr_phase_cached(mole_fractions, a_t, b, kij, temperature_k, pressure_pa, tol):
    """Cached core of evaluate_pr_phase; all inputs must be hashable."""
    args = dict(mole_fractions=mole_fractions, a_t=a_t, b=b, kij=kij,
                temperature_k=temperature_k, pressure_pa=pressure_pa)
    parameters = pr_mixture_parameters(**args)
    roots = solve_pr_roots(A=parameters.A, B=parameters.B)
    candidates = tuple(pr_log_fugacity(**args, z=z, parameters=parameters)
                       for z in roots.admissible_roots)
    minimum = min(state.g_residual_rt for state in candidates)
    preferred = tuple(i for i, state in enumerate(candidates)
                      if state.g_residual_rt-minimum <= tol)
    return PRPhaseEvaluation(parameters, roots, candidates, minimum, preferred, tol)


def evaluate_pr_phase(*, mole_fractions, a_t, b, kij, temperature_k,
                      pressure_pa, gibbs_tolerance=1e-10):
    """Evaluate all Z>B roots and identify minimum fixed-composition Gibbs.

    The ideal contribution is identical among roots at fixed x,T,P, so the
    residual Gibbs energy suffices for this comparison. It does NOT suffice
    for comparing phases with different compositions. TPD is still required.
    gibbs_tolerance is an absolute tolerance on dimensionless g^R/(RT).
    Pure a_t parameters must all be evaluated at the supplied temperature.
    """
    tol = _number(gibbs_tolerance, 'gibbs_tolerance')
    if tol < 0:
        raise ValueError('gibbs_tolerance must be nonnegative.')
    # Validate numbers before cache lookup: bools alias numeric keys.
    mf = tuple(_number(v, 'mole_fraction') for v in mole_fractions)
    aa = tuple(_number(v, 'a_t') for v in a_t)
    bb = tuple(_number(v, 'b', positive=True) for v in b)
    kk = tuple(tuple(_number(v, 'kij') for v in row) for row in kij)
    t = _number(temperature_k, 'temperature_k', positive=True)
    p = _number(pressure_pa, 'pressure_pa', positive=True)
    return _evaluate_pr_phase_cached(mf, aa, bb, kk, t, p, tol)


def evaluate_mixture_pr_phase(mixture, conditions, *, kij, gibbs_tolerance=1e-10):
    """Adapter for the validated feed objects; trial phases use their own x/y."""
    pure = tuple(component_pr_parameters(c, conditions) for c in mixture.components)
    return evaluate_pr_phase(mole_fractions=mixture.mole_fractions,
        a_t=tuple(q.a_t for q in pure), b=tuple(q.b for q in pure), kij=kij,
        temperature_k=conditions.temperature_k, pressure_pa=conditions.pressure_pa,
        gibbs_tolerance=gibbs_tolerance)
