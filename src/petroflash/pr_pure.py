"""Original Peng-Robinson (1976) pure-component parameters in SI units.

No mixing, root selection, stability analysis or flash is performed here.
"""

from dataclasses import dataclass
from math import isfinite, sqrt
from numbers import Real

R = 8.31446261815324  # Pa m^3 / (mol K)


def _number(value, name, *, positive=False):
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real number, not a boolean.")
    try:
        value = float(value)
    except (OverflowError, ValueError):
        raise ValueError(f"{name} must be finite.") from None
    if not isfinite(value) or (positive and value <= 0):
        raise ValueError(f"{name} must be finite" +
                         (" and positive." if positive else "."))
    return value


@dataclass(frozen=True, slots=True)
class PRPureParameters:
    """a_c and a_t: Pa m^6/mol^2; b: m^3/mol; remaining fields dimensionless."""

    m: float
    alpha: float
    a_c: float
    a_t: float
    b: float
    A: float
    B: float


def pr_pure_parameters(*, temperature_k, pressure_pa,
                       critical_temperature_k, critical_pressure_pa,
                       acentric_factor):
    """Calculate PR1976 parameters; pressure is absolute.

    Inputs must use the stated SI units. Negative acentric factors are allowed.
    The original quadratic m correlation is used for every supplied omega;
    this function does not silently switch to PR1978 or a fitted alpha model.
    """
    t = _number(temperature_k, "temperature_k", positive=True)
    p = _number(pressure_pa, "pressure_pa", positive=True)
    tc = _number(critical_temperature_k, "critical_temperature_k", positive=True)
    pc = _number(critical_pressure_pa, "critical_pressure_pa", positive=True)
    omega = _number(acentric_factor, "acentric_factor")
    try:
        m = 0.37464 + 1.54226 * omega - 0.26992 * omega**2
        alpha = (1 + m * (1 - sqrt(t / tc)))**2
        a_c = 0.45724 * (R * tc)**2 / pc
        a_t = a_c * alpha
        b = 0.07780 * R * tc / pc
        A = a_t * p / (R * t)**2
        B = b * p / (R * t)
    except (OverflowError, ZeroDivisionError):
        raise ValueError("PR parameters exceed the numerical range.") from None
    values = (m, alpha, a_c, a_t, b, A, B)
    if not all(isfinite(v) for v in values) or min(a_c, b, B) <= 0:
        raise ValueError("PR parameters exceed the numerical range.")
    return PRPureParameters(*values)


def component_pr_parameters(component, conditions):
    """Adapter for a validated Component and TPConditions, preserving SI units."""
    return pr_pure_parameters(
        temperature_k=conditions.temperature_k,
        pressure_pa=conditions.pressure_pa,
        critical_temperature_k=component.critical_temperature.value,
        critical_pressure_pa=component.critical_pressure.value,
        acentric_factor=component.acentric_factor.value,
    )
