"""Build the selected central dataset from chemicals 1.5.2."""

import json
import sys
import tempfile
from dataclasses import asdict
from importlib.metadata import version
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from chemicals.critical import Tc, Pc
from chemicals.acentric import omega
from chemicals.identifiers import search_chemical

from petroflash.components import Component
from petroflash.database import ComponentDatabase
from petroflash.properties import DataKind, PropertyRecord
# Dataset inventory is explicit; the historical coverage audit has its own scope.
COMPONENTS = (('methane', '74-82-8'), ('ethane', '74-84-0'), ('propane', '74-98-6'), ('n-butane', '106-97-8'), ('isobutane', '75-28-5'), ('n-pentane', '109-66-0'), ('isopentane', '78-78-4'), ('n-hexane', '110-54-3'), ('nitrogen', '7727-37-9'), ('carbon dioxide', '124-38-9'), ('hydrogen sulfide', '7783-06-4'), ('water', '7732-18-5'), ('n-heptane', '142-82-5'), ('n-octane', '111-65-9'), ('n-nonane', '111-84-2'), ('n-decane', '124-18-5'), ('n-undecane', '1120-21-4'), ('n-dodecane', '112-40-3'), ('n-hexadecane', '544-76-3'))


def record(value, unit, method, reference, notes):
    if value is None:
        raise ValueError(f"Missing required value: {method}, {unit}")

    return PropertyRecord(
        value=float(value),
        unit=unit,
        source="chemicals 1.5.2",
        reference=reference,
        method=method,
        data_kind=DataKind.EVALUATED,
        notes=notes,
    )


def build_component(name, cas_number):
    metadata = search_chemical(cas_number)

    if metadata.CASs != cas_number:
        raise ValueError(f"Unexpected CAS mapping for {cas_number}")

    critical_ref = (
        "https://chemicals.readthedocs.io/chemicals.critical.html"
    )
    acentric_ref = (
        "https://chemicals.readthedocs.io/chemicals.acentric.html"
    )
    metadata_ref = (
        "https://chemicals.readthedocs.io/chemicals.identifiers.html"
    )
    selection_note = (
        "Fixed HEOS selection; no fallback to another method. "
        "EVALUATED is the project's reference-data classification."
    )

    return Component(
        name=name,
        cas_number=cas_number,
        formula=metadata.formula,
        critical_temperature=record(
            Tc(cas_number, method="HEOS"),
            "K", "HEOS", critical_ref, selection_note,
        ),
        critical_pressure=record(
            Pc(cas_number, method="HEOS"),
            "Pa", "HEOS", critical_ref, selection_note,
        ),
        acentric_factor=record(
            omega(cas_number, method="HEOS"),
            "1", "HEOS", acentric_ref, selection_note,
        ),
        molar_mass=record(
            metadata.MW / 1000.0,
            "kg/mol",
            "identifiers.search_chemical metadata",
            metadata_ref,
            "Tabulated metadata MW converted from g/mol to kg/mol; "
            "not a HEOS property. EVALUATED denotes selected reference data.",
        ),
    )


def main():
    if version("chemicals") != "1.5.2":
        raise RuntimeError("This builder requires chemicals==1.5.2.")

    components = [
        build_component(name, cas_number)
        for name, cas_number in COMPONENTS
    ]
    ComponentDatabase(components)

    document = {
        "schema_version": 1,
        "dataset_version": "0.4.0",
        "description": (
            "19 components from chemicals 1.5.2: "
            "HEOS Tc/Pc/omega and metadata molar mass; no fallback."
        ),
        "components": [asdict(component) for component in components],
    }

    output = ROOT / "data" / "components.json"
    output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".json",
        dir=output.parent,
        delete=False,
    ) as stream:
        temporary = Path(stream.name)
        try:
            json.dump(document, stream, indent=2, allow_nan=False)
            stream.write("\n")
        except Exception:
            stream.close()
            temporary.unlink(missing_ok=True)
            raise

    try:
        loaded = ComponentDatabase.from_file(temporary)
        for component in components:
            if loaded.get(component.cas_number) != component:
                raise ValueError("Data changed during JSON round trip.")

        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)

    print(f"Dataset: {loaded.dataset_version}")
    print(f"Components: {len(loaded)}")
    print(f"{'Name':<20} {'Formula':<10} {'MW [kg/mol]':>14}")

    for component in components:
        print(
            f"{component.name:<20} {component.formula:<10} "
            f"{component.molar_mass.value:>14.8f}"
        )

    print(f"\nSaved: {output}")


if __name__ == "__main__":
    main()
