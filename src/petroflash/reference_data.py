"""Initial selected reference data.

This module provides the first real component.
A general external-data repository will replace this small seed module.
"""

from .components import Component
from .properties import DataKind, PropertyRecord


def methane() -> Component:
    """Build methane using the documented initial data selection."""

    critical_reference = (
        "https://chemicals.readthedocs.io/chemicals.critical.html"
    )
    acentric_reference = (
        "https://chemicals.readthedocs.io/chemicals.acentric.html"
    )
    coolprop_reference = (
        "https://coolprop.org/fluid_properties/fluids/Methane.html"
    )

    return Component(
        name="methane",
        cas_number="74-82-8",
        formula="CH4",
        critical_temperature=PropertyRecord(
            value=190.564,
            unit="K",
            source="chemicals 1.5.2",
            reference=critical_reference,
            method="HEOS",
            data_kind=DataKind.EVALUATED,
            notes="Selected from the local methane data audit.",
        ),
        critical_pressure=PropertyRecord(
            value=4599200.0,
            unit="Pa",
            source="chemicals 1.5.2",
            reference=critical_reference,
            method="HEOS",
            data_kind=DataKind.EVALUATED,
            notes="Selected from the local methane data audit.",
        ),
        acentric_factor=PropertyRecord(
            value=0.01142,
            unit="1",
            source="chemicals 1.5.2",
            reference=acentric_reference,
            method="HEOS",
            data_kind=DataKind.EVALUATED,
            notes="Selected from the local methane data audit.",
        ),
        molar_mass=PropertyRecord(
            value=0.0160428,
            unit="kg/mol",
            source="CoolProp methane fluid documentation",
            reference=coolprop_reference,
            method="Tabulated reference molar mass",
            data_kind=DataKind.EVALUATED,
            notes=(
                "Retrieved 2026-10-08. Uses the molar-mass convention "
                "reported by this source; not extracted from chemicals."
            ),
        ),
    )
