"""Check HEOS coverage without changing the central database."""

import json
from importlib.metadata import version
from pathlib import Path

from chemicals.critical import Tc_methods, Pc_methods
from chemicals.acentric import omega_methods


COMPONENTS = (
    ("methane", "74-82-8"),
    ("ethane", "74-84-0"),
    ("propane", "74-98-6"),
    ("n-butane", "106-97-8"),
    ("isobutane", "75-28-5"),
    ("n-pentane", "109-66-0"),
    ("isopentane", "78-78-4"),
    ("n-hexane", "110-54-3"),
    ("nitrogen", "7727-37-9"),
    ("carbon dioxide", "124-38-9"),
    ("hydrogen sulfide", "7783-06-4"),
    ("water", "7732-18-5"),
)


def main():
    checks = (
        ("Tc", Tc_methods),
        ("Pc", Pc_methods),
        ("omega", omega_methods),
    )
    rows = []

    print(f"{'Component':<20} {'Tc':<8} {'Pc':<8} {'omega':<8}")
    print("-" * 48)

    for name, cas_number in COMPONENTS:
        available = {
            label: "HEOS" in methods(cas_number)
            for label, methods in checks
        }

        rows.append({
            "name": name,
            "cas_number": cas_number,
            "HEOS_available": available,
        })

        flags = [
            "OK" if available[label] else "MISSING"
            for label, _ in checks
        ]
        print(
            f"{name:<20} {flags[0]:<8} "
            f"{flags[1]:<8} {flags[2]:<8}"
        )

    report = {
        "chemicals_version": version("chemicals"),
        "selected_method": "HEOS",
        "scope": "Availability of Tc, Pc and omega only",
        "components": rows,
    }

    root = Path(__file__).resolve().parents[1]
    output = root / "docs" / "heos-coverage.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"\nReport saved to: {output}")


if __name__ == "__main__":
    main()
