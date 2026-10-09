"""Bracketed Rachford-Rice solution for supplied, fixed K values."""

from math import fsum, isfinite
from numbers import Real


def _numbers(values, name):
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{name} must be a collection of numbers.")
    result = []
    for value in values:
        if isinstance(value, bool) or not isinstance(value, Real):
            raise TypeError(f"{name} entries must be real numbers.")
        try:
            value = float(value)
        except OverflowError:
            raise ValueError(f"{name} entry is too large.") from None
        if not isfinite(value):
            raise ValueError(f"{name} entries must be finite.")
        result.append(value)
    return tuple(result)


def solve_rachford_rice(z, k_values, *, residual_tolerance=1e-12):
    """Return vapor fraction in [0, 1] for fixed K, without normalization.

    residual_tolerance controls the absolute RR residual (default 1e-12).
    A missing bracket is NOT a thermodynamic single-phase classification.
    Raises ValueError for invalid input, degeneracy, or no physical root;
    raises RuntimeError if the residual tolerance is not reached.
    """
    residual_tolerance = _numbers([residual_tolerance], "residual_tolerance")[0]
    if residual_tolerance <= 0:
        raise ValueError("residual_tolerance must be positive.")
    z = _numbers(z, "z")
    k_values = _numbers(k_values, "K")
    if not z or len(z) != len(k_values):
        raise ValueError("z and K must have equal, nonzero lengths.")
    if any(value < 0 or value > 1 for value in z):
        raise ValueError("Mole fractions must lie in [0, 1].")
    if abs(fsum(z) - 1.0) > 1e-10:
        raise ValueError("Mole fractions must sum to one within 1e-10.")
    if any(value <= 0 for value in k_values):
        raise ValueError("K values must be positive.")
    active = [(zi, ki) for zi, ki in zip(z, k_values) if zi > 0]
    if all(ki == 1.0 for zi, ki in active):
        raise ValueError("Degenerate K values: vapor fraction is undetermined.")

    def residual(beta):
        terms = []
        for zi, ki in active:
            # Algebraically equivalent forms avoid cancellation at endpoints
            # and overflow from large K values in the interior.
            if ki >= 1:
                ratio = (1 - 1 / ki) / (beta + (1 - beta) / ki)
            else:
                ratio = (ki - 1) / ((1 - beta) + beta * ki)
            terms.append(zi * ratio)
        return fsum(terms)

    lower, upper = 0.0, 1.0
    f_lower, f_upper = residual(lower), residual(upper)
    if f_lower < 0 or f_upper > 0:
        raise ValueError("No root in [0, 1] for the supplied K values.")
    if f_lower == 0:
        return lower
    if f_upper == 0:
        return upper
    for _ in range(100):
        beta = (lower + upper) / 2
        value = residual(beta)
        if abs(value) <= residual_tolerance:
            return beta
        if beta == lower or beta == upper:
            break
        if value > 0:
            lower = beta
        else:
            upper = beta
    raise RuntimeError("Rachford-Rice residual tolerance was not reached.")
