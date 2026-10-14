"""PR1976 log fugacity coefficients for a specified composition and root.

No root is labelled liquid/vapor or globally stable here. For mixture
fugacity use f_i = x_i * phi_i * absolute_pressure, not phi_i * pressure.
"""

from dataclasses import dataclass
from math import fsum, isfinite, log, log1p, sqrt

from .pr_mixing import PRMixtureParameters, pr_mixture_parameters
from .pr_pure import R, _number, component_pr_parameters
from .pr_roots import pr_cubic_residual


@dataclass(frozen=True, slots=True)
class PRFugacity:
    """All fields dimensionless; g_residual_rt = sum_i x_i ln(phi_i)."""

    z: float
    ln_phi: tuple[float, ...]
    g_residual_rt: float


def pr_log_fugacity(*, mole_fractions, a_t, b, kij,
                    temperature_k, pressure_pa, z, parameters=None):
    """Validate inputs and supplied mixture parameters before evaluating ln(phi).

    Supplied parameters must exactly match the current mixture calculation.
    Internal phase evaluation uses a separate prevalidated fast path.
    """
    x, aa, bb = tuple(mole_fractions), tuple(a_t), tuple(b)
    kk = tuple(tuple(row) for row in kij)
    q = pr_mixture_parameters(mole_fractions=x, a_t=aa, b=bb, kij=kk,
                             temperature_k=temperature_k, pressure_pa=pressure_pa)
    if parameters is not None:
        if not isinstance(parameters, PRMixtureParameters):
            raise TypeError('parameters must be PRMixtureParameters.')
        if parameters != q:
            raise ValueError('parameters do not match the current composition and TP.')
    return _pr_log_fugacity_prevalidated(
        mole_fractions=x, b=bb, temperature_k=temperature_k, z=z, parameters=q)


def _pr_log_fugacity_prevalidated(*, mole_fractions, b, temperature_k,
                                z, parameters):
    """Internal path: caller supplies parameters from this exact phase state.

    Preserve root and numerical checks while avoiding repeated mixing.
    """
    x, bb = tuple(mole_fractions), tuple(b)
    t = _number(temperature_k, 'temperature_k', positive=True)
    z = _number(z, 'z')
    q = parameters
    if z <= q.B:
        raise ValueError('Fugacity requires Z>B.')
    # Scale the polynomial check in the same way as the root module.
    c2 = q.B-1
    c1 = q.A-2*q.B-3*q.B*q.B
    c0 = -q.A*q.B+q.B*q.B+q.B**3
    scale = max(1.0, ((abs(z)+abs(c2))*abs(z)+abs(c1))*abs(z)+abs(c0))
    if abs(pr_cubic_residual(z, A=q.A, B=q.B))/scale > 1e-12:
        raise ValueError('Z does not satisfy the cubic for this composition and TP.')
    try:
        s2 = sqrt(2.0)
        log_ratio = log1p(2*s2*q.B/(z+(1-s2)*q.B))
        attraction = q.a_m/(q.b_m*R*t) * log_ratio/(2*s2)
        log_z_minus_b = log1p((z-1)-q.B) if abs(z-1-q.B) < 0.5 else log(z-q.B)
        values = tuple(
            (float(bb[i])/q.b_m)*(z-1) - log_z_minus_b
            - attraction*(2*q.a_row_sums[i]/q.a_m-float(bb[i])/q.b_m)
            for i in range(len(x)))
        g = fsum(float(x[i])*values[i] for i in range(len(x)))
    except (OverflowError, ZeroDivisionError, ValueError):
        raise ValueError('Fugacity evaluation exceeds the numerical range.') from None
    if not all(isfinite(v) for v in (*values, g)):
        raise ValueError('Fugacity coefficients must be finite.')
    return PRFugacity(z, values, g)


def mixture_pr_log_fugacity(mixture, conditions, *, kij, z):
    """Adapter using overall feed composition; trial phases need their own x/y."""
    pure = tuple(component_pr_parameters(c, conditions) for c in mixture.components)
    return pr_log_fugacity(mole_fractions=mixture.mole_fractions,
        a_t=tuple(q.a_t for q in pure), b=tuple(q.b for q in pure), kij=kij,
        temperature_k=conditions.temperature_k, pressure_pa=conditions.pressure_pa, z=z)

