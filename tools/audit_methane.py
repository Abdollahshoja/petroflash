"""Inspect methane property values before selecting database records."""

import json
from importlib.metadata import version
from pathlib import Path

from chemicals.critical import Tc, Tc_methods, Pc, Pc_methods
from chemicals.acentric import omega, omega_methods


def main():
    cas_number = "74-82-8"

    properties = (
        ("critical_temperature", "K", Tc_methods, Tc),
        ("critical_pressure", "Pa", Pc_methods, Pc),
        ("acentric_factor", "1", omega_methods, omega),
    )

    report = {
        "component": "methane",
        "cas_number": cas_number,
        "chemicals_version": version("chemicals"),
        "status": "candidate data; not approved database records",
        "properties": {},
    }

    for name, unit, list_methods, get_value in properties:
        rows = []
        print(f"\n{name} [{unit}]")
        print("-" * 45)

        for method in list_methods(cas_number):
            value = get_value(cas_number, method=method)
            value = None if value is None else float(value)

            rows.append({"method": method, "value": value})
            print(f"{method:<20} {value}")

        report["properties"][name] = {
            "unit": unit,
            "candidates": rows,
        }

    project_root = Path(__file__).resolve().parents[1]
    output = project_root / "docs" / "data-audit-methane.json"
    output.parent.mkdir(parents=True, exist_ok=True)

    output.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        ) + "\n",
        encoding="utf-8",
    )

    print(f"\nReport saved to: {output}")


if __name__ == "__main__":
    main()
