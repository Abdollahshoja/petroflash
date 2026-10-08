"""Pure-component identity and properties required by cubic EOS models."""

from dataclasses import dataclass

from .properties import PropertyRecord


@dataclass(frozen=True, slots=True)
class Component:
    """A pure component with explicit property units and provenance.

    Identity fields must be non-empty. CAS validity and agreement between
    CAS, name, and formula are checked separately by the database layer.
    """

    name: str
    cas_number: str
    formula: str
    critical_temperature: PropertyRecord
    critical_pressure: PropertyRecord
    acentric_factor: PropertyRecord
    molar_mass: PropertyRecord

    def __post_init__(self) -> None:
        for field_name in ("name", "cas_number", "formula"):
            text = getattr(self, field_name)
            if not isinstance(text, str) or not text.strip():
                raise ValueError(
                    f"{field_name} must be a non-empty string."
                )

        self.require_cubic_properties()

    def require_cubic_properties(self) -> None:
        """Validate record types, exact SI units, and physical signs."""

        requirements = (
            ("critical_temperature", "K", True),
            ("critical_pressure", "Pa", True),
            ("acentric_factor", "1", False),
            ("molar_mass", "kg/mol", True),
        )

        for field_name, expected_unit, must_be_positive in requirements:
            record = getattr(self, field_name)

            if not isinstance(record, PropertyRecord):
                raise TypeError(
                    f"{field_name} must be a PropertyRecord."
                )

            if record.unit != expected_unit:
                raise ValueError(
                    f"{field_name} requires unit {expected_unit!r}; "
                    f"received {record.unit!r}."
                )

            if must_be_positive and record.value <= 0:
                raise ValueError(
                    f"{field_name} must be greater than zero."
                )
