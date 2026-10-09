"""Classical quadratic-a / linear-b PR mixing for one specified phase.

All vectors and both kij axes must use the same component order.
This module does not decide phase stability or perform a flash.
"""

from dataclasses import dataclass
from math import fsum, isfinite, sqrt

from .pr_pure import R, _number, component_pr_parameters


@dataclass(frozen=True, slots=True)
class PRMixtureParameters:
    """a_m, a_ij, a_row_sums: Pa m^6/mol^2; b_m: m^3/mol; A/B: 1."""

    a_m: float
    b_m: float
    A: float
    B: float
    a_ij: tuple[tuple[float, ...], ...]
    a_row_sums: tuple[float, ...]


def zero_kij(component_count):
    """Explicit zero-interaction assumption, not a database lookup."""
    if isinstance(component_count, bool) or not isinstance(component_count, int):
        raise TypeError("component_count must be an integer.")
    if component_count < 1:
        raise ValueError("component_count must be positive.")
    return tuple((0.0,) * component_count for _ in range(component_count))


def pr_mixture_parameters(*, mole_fractions, a_t, b, kij,
                          temperature_k, pressure_pa):
    """Mix dimensional pure parameters evaluated at this same temperature.

    Fractions sum to one within 1e-10 and are never silently normalized.
    kij must be finite, exactly symmetric, with an exactly zero diagonal.
    Negative kij is allowed; no arbitrary fitted-coefficient range is imposed.
    Nonpositive resulting attraction is outside the current solver scope.
    """
    t = _number(temperature_k, "temperature_k", positive=True)
    p = _number(pressure_pa, "pressure_pa", positive=True)
    x = tuple(_number(v, "mole_fraction") for v in mole_fractions)
    aa = tuple(_number(v, "a_t") for v in a_t)
    bb = tuple(_number(v, "b", positive=True) for v in b)
    n = len(x)
    if not n or len(aa) != n or len(bb) != n:
        raise ValueError("Nonempty composition, a_t and b must have equal lengths.")
    if any(v < 0 or v > 1 for v in x):
        raise ValueError("Each mole fraction must lie in [0, 1].")
    if abs(fsum(x) - 1) > 1e-10:
        raise ValueError("Mole fractions must sum to one; no normalization performed.")
    if any(v < 0 for v in aa):
        raise ValueError("Pure a_t must be nonnegative.")
    kk = tuple(tuple(_number(v, "kij") for v in row) for row in kij)
    if len(kk) != n or any(len(row) != n for row in kk):
        raise ValueError("kij must be an n-by-n matrix in component order.")
    for i in range(n):
        if kk[i][i] != 0:
            raise ValueError("kij diagonal must be zero.")
        for j in range(i):
            if kk[i][j] != kk[j][i]:
                raise ValueError("kij must be symmetric; no averaging performed.")
    try:
        roots = tuple(sqrt(v) for v in aa)
        aij = tuple(tuple(roots[i] * roots[j] * (1 - kk[i][j])
                          for j in range(n)) for i in range(n))
        rows = tuple(fsum(x[j] * aij[i][j] for j in range(n)) for i in range(n))
        am = fsum(x[i] * rows[i] for i in range(n))
        bm = fsum(x[i] * bb[i] for i in range(n))
        A = am * p / (R * t)**2
        B = bm * p / (R * t)
    except (OverflowError, ZeroDivisionError, ValueError):
        raise ValueError("Mixture parameters exceed the numerical range.") from None
    values = (am, bm, A, B, *rows, *(v for row in aij for v in row))
    if not all(isfinite(v) for v in values) or min(am, bm, A, B) <= 0:
        raise ValueError("Mixture parameters must be finite with positive a_m/b_m/A/B.")
    return PRMixtureParameters(am, bm, A, B, aij, rows)


def mixture_pr_parameters(mixture, conditions, *, kij):
    """Evaluate pure PR1976 parameters in mixture order, then mix at feed z.

    For liquid/vapor trial phases call pr_mixture_parameters with their x/y,
    rather than reusing the overall feed composition.
    """
    pure = tuple(component_pr_parameters(c, conditions) for c in mixture.components)
    return pr_mixture_parameters(
        mole_fractions=mixture.mole_fractions,
        a_t=tuple(q.a_t for q in pure), b=tuple(q.b for q in pure), kij=kij,
        temperature_k=conditions.temperature_k, pressure_pa=conditions.pressure_pa)
