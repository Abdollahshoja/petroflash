"""User-selected components and validated overall mole percentages."""

from dataclasses import dataclass
from math import fsum, isclose, isfinite
from numbers import Real

from .components import Component
from .database import ComponentDatabase


@dataclass(frozen=True, slots=True)
class Mixture:
    """Overall feed composition, independent of temperature and pressure.

    Mole percentages must sum to 100 within 1e-8 percentage points.
    Values are preserved without automatic normalization.
    Zero-content components are retained in their original positions.
    """

    components: tuple[Component, ...]
    mole_percentages: tuple[float, ...]

    def __post_init__(self) -> None:
        if isinstance(self.components, (str, bytes)):
            raise TypeError("components must be a collection of Component objects.")
        if isinstance(self.mole_percentages, (str, bytes)):
            raise TypeError("mole_percentages must be a collection of numbers.")

        components = tuple(self.components)
        raw_values = tuple(self.mole_percentages)

        if not components:
            raise ValueError("Select at least one component.")

        if not all(isinstance(item, Component) for item in components):
            raise TypeError("Every component must be a Component object.")

        identifiers = [item.cas_number for item in components]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("The same component was selected more than once.")

        if len(components) != len(raw_values):
            raise ValueError(
                "The number of percentages must match the number of components."
            )

        values = []
        for value in raw_values:
            if isinstance(value, bool) or not isinstance(value, Real):
                raise TypeError("Each mole percentage must be a real number.")
            if not 0 <= value <= 100:
                raise ValueError("Each mole percentage must be between 0 and 100.")

            number = float(value)
            if not isfinite(number):
                raise ValueError("Mole percentages must be finite.")
            values.append(number)

        total = fsum(values)
        if not isclose(total, 100.0, rel_tol=0.0, abs_tol=1e-8):
            raise ValueError(
                f"Mole percentages must sum to 100; received {total:.12g}."
            )

        object.__setattr__(self, "components", components)
        object.__setattr__(self, "mole_percentages", tuple(values))

    @classmethod
    def from_mole_percentages(cls, database, identifiers, percentages):
        """Resolve user-selected names or CAS numbers using the database."""
        if not isinstance(database, ComponentDatabase):
            raise TypeError("database must be a ComponentDatabase.")
        return cls(
            components=database.select(identifiers),
            mole_percentages=percentages,
        )

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(component.name for component in self.components)

    @property
    def mole_fractions(self) -> tuple[float, ...]:
        """Overall feed mole fractions z_i, in component order."""
        return tuple(value / 100.0 for value in self.mole_percentages)
