"""Validated TP conditions and explicit input-unit conversion."""
from dataclasses import dataclass
from math import isfinite
from numbers import Real


def _real(value, name):
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real number.")
    try:
        value = float(value)
    except OverflowError:
        raise ValueError(f"{name} is too large.") from None
    if not isfinite(value):
        raise ValueError(f"{name} must be finite.")
    return value


@dataclass(frozen=True, slots=True)
class TPConditions:
    """Temperature in K and absolute pressure in Pa."""
    temperature_k: float
    pressure_pa: float

    def __post_init__(self):
        for name in ('temperature_k', 'pressure_pa'):
            value = _real(getattr(self, name), name)
            if value <= 0:
                raise ValueError(f"{name} must be greater than zero.")
            object.__setattr__(self, name, value)

    @classmethod
    def from_units(cls, temperature, pressure, *, temperature_unit, pressure_unit):
        """Accept K/C and Pa/bar; all pressure input MUST be absolute.

        Gauge-pressure units are intentionally rejected. No atmospheric
        pressure correction or unit inference is performed.
        """
        if not isinstance(temperature_unit, str) or not isinstance(pressure_unit, str):
            raise TypeError('Units must be strings.')
        tu = temperature_unit.strip().casefold()
        pu = pressure_unit.strip().casefold()
        if tu not in ('k', 'c'):
            raise ValueError('Temperature unit must be K or C.')
        if pu not in ('pa', 'bar'):
            raise ValueError('Absolute pressure unit must be Pa or bar.')
        temperature = _real(temperature, 'temperature')
        pressure = _real(pressure, 'pressure')
        if tu == 'c':
            temperature += 273.15
        if pu == 'bar':
            pressure *= 100000.0
        return cls(temperature, pressure)
