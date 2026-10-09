"""Bracketed real roots of the PR cubic, without phase classification.

Derivative turning points divide the cubic into monotone intervals.
Numerically ambiguous nearly repeated roots raise an explicit error.
"""

from dataclasses import dataclass
from math import isfinite, sqrt
from sys import float_info

from .pr_pure import _number


class PRRootError(ArithmeticError):
    """Root isolation or convergence is unreliable in floating-point arithmetic."""


@dataclass(frozen=True, slots=True)
class PRRoots:
    """Distinct real roots; admissible means Z>B, not thermodynamically stable."""

    real_roots: tuple[float, ...]
    admissible_roots: tuple[float, ...]
    scaled_residuals: tuple[float, ...]


def _coefficients(A, B):
    A = _number(A, 'A')
    B = _number(B, 'B')
    if A < 0 or B < 0:
        raise ValueError('A and B must be nonnegative.')
    try:
        c2 = B - 1
        c1 = A - 2*B - 3*B**2
        c0 = -A*B + B**2 + B**3
    except OverflowError:
        raise PRRootError('Cubic coefficients exceed the numerical range.') from None
    if not all(isfinite(v) for v in (c2, c1, c0)):
        raise PRRootError('Cubic coefficients exceed the numerical range.')
    return B, c2, c1, c0


def _evaluate(z, c2, c1, c0):
    value = ((z + c2)*z + c1)*z + c0
    scale = ((abs(z) + abs(c2))*abs(z) + abs(c1))*abs(z) + abs(c0)
    if not isfinite(value) or not isfinite(scale):
        raise PRRootError('Polynomial evaluation exceeds the numerical range.')
    return value, max(1.0, scale)


def pr_cubic_residual(z, *, A, B):
    """Signed polynomial residual; no claim that z is a valid root."""
    z = _number(z, 'z')
    _, c2, c1, c0 = _coefficients(A, B)
    return _evaluate(z, c2, c1, c0)[0]


def solve_pr_roots(*, A, B, max_iterations=200):
    """Isolate and bisect every distinct real root; retain those with Z>B.

    A=B=0 is accepted as the ideal-gas limiting polynomial. Nearly tangent
    turning points with nonzero residual within 64 eps of evaluation scale
    are rejected, rather than silently merging or inventing close roots.
    This baseline intentionally does not promise near-critical robustness.
    """
    if isinstance(max_iterations, bool) or not isinstance(max_iterations, int):
        raise TypeError('max_iterations must be an integer.')
    if max_iterations < 1:
        raise ValueError('max_iterations must be positive.')
    B, c2, c1, c0 = _coefficients(A, B)
    bound = 1 + max(abs(c2), abs(c1), abs(c0))
    d = c2*c2 - 3*c1
    if not isfinite(bound) or not isfinite(d):
        raise PRRootError('Root isolation exceeds the numerical range.')
    turns = []
    if d >= 0:
        s = sqrt(d)
        turns = sorted(set(((-c2-s)/3, (-c2+s)/3)))
    # An exact zero constant implies an exact root at zero; isolate it
    # explicitly instead of spending iterations bisecting toward zero.
    points = sorted(set([-bound, *turns, bound] + ([0.0] if c0 == 0 else [])))
    values = [_evaluate(z, c2, c1, c0) for z in points]
    for turning_point in turns:
        value, _ = _evaluate(turning_point, c2, c1, c0)
        az = abs(turning_point)
        local_scale = max(
            float_info.min,
            ((az + abs(c2))*az + abs(c1))*az + abs(c0)
        )
        if value != 0 and abs(value)/local_scale <= 64*float_info.epsilon:
            raise PRRootError('Nearly repeated roots are numerically ambiguous; '
                              'a specialized critical-region solver is required.')
    roots = [z for z, (v, _) in zip(points, values) if v == 0]
    for i in range(len(points)-1):
        lo, hi = points[i:i+2]
        flo, fhi = values[i][0], values[i+1][0]
        if flo == 0 or fhi == 0 or (flo > 0) == (fhi > 0):
            continue
        for _ in range(max_iterations):
            mid = lo + (hi-lo)/2
            fm, _ = _evaluate(mid, c2, c1, c0)
            if fm == 0 or mid == lo or mid == hi:
                roots.append(mid)
                break
            if (fm > 0) == (flo > 0):
                lo, flo = mid, fm
            else:
                hi, fhi = mid, fm
        else:
            raise PRRootError('PR cubic bisection did not converge.')
    roots = tuple(sorted(set(roots)))
    residuals = tuple(abs(v)/scale for v, scale in
                      (_evaluate(z, c2, c1, c0) for z in roots))
    if not roots or any(r > 128*float_info.epsilon for r in residuals):
        raise PRRootError('Computed roots fail the scaled residual check.')
    admissible = tuple(z for z in roots if z > B)
    if not admissible:
        raise PRRootError('No root satisfies Z>B.')
    return PRRoots(roots, admissible, residuals)
