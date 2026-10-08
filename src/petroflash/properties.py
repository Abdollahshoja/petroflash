"""Traceable pure-component property records.

Uncertainty, when supplied, is absolute and uses the same unit as value.
Its interpretation and coverage must be documented in notes.
"""

from dataclasses import dataclass
from enum import Enum
from math import isfinite
from numbers import Real


class DataKind(str, Enum):
    """Classification of the evidence behind a property value."""

    EXPERIMENTAL = "experimental"
    EVALUATED = "evaluated"
    ESTIMATED = "estimated"


@dataclass(frozen=True, slots=True)
class PropertyRecord:
    """An immutable property value with explicit provenance."""

    value: float
    unit: str
    source: str
    reference: str
    method: str
    data_kind: DataKind
    uncertainty: float | None = None
    notes: str = ""

    def __post_init__(self) -> None:
        self._validate_number("value", self.value)

        for field_name in ("unit", "source", "reference", "method"):
            text = getattr(self, field_name)
            if not isinstance(text, str) or not text.strip():
                raise ValueError(f"{field_name} must be a non-empty string.")

        if not isinstance(self.data_kind, DataKind):
            raise TypeError("data_kind must be a DataKind member.")

        if not isinstance(self.notes, str):
            raise TypeError("notes must be a string.")

        if self.uncertainty is not None:
            self._validate_number("uncertainty", self.uncertainty)
            if self.uncertainty < 0:
                raise ValueError("uncertainty cannot be negative.")
            if not self.notes.strip():
                raise ValueError(
                    "Document the uncertainty definition in notes."
                )

    @staticmethod
    def _validate_number(name: str, value: Real) -> None:
        if isinstance(value, bool) or not isinstance(value, Real):
            raise TypeError(f"{name} must be a real number.")
        if not isfinite(value):
            raise ValueError(f"{name} must be finite.")
