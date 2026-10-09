"""Interactive selection of feed components and mole percentages."""

import argparse

from .conditions import TPConditions
from .database import ComponentDatabase
from .mixture import Mixture


def read_mixture(database):
    """Read user choices and return a validated Mixture."""
    print("\nAvailable components:")
    for name in database.names():
        component = database.get(name)
        print(f"  {component.name} | CAS: {component.cas_number}")

    while True:
        text = input(
            "\nEnter component names or CAS numbers, separated by commas: "
        )
        identifiers = [item.strip() for item in text.split(",")]

        try:
            components = database.select(identifiers)
        except (TypeError, ValueError, KeyError) as error:
            print(f"Selection error: {error}")
            continue
        break

    while True:
        percentages = []
        for component in components:
            while True:
                text = input(f"Mole percent of {component.name}: ")
                try:
                    value = float(text)
                except ValueError:
                    print("Enter a number, using a decimal point if needed.")
                    continue

                if not 0 <= value <= 100:
                    print("Enter a finite percentage between 0 and 100.")
                    continue

                percentages.append(value)
                break

        try:
            return Mixture(components, percentages)
        except ValueError as error:
            print(f"Composition error: {error}")
            print("Enter all percentages again; their sum must be 100.")


def read_conditions():
    """Read explicit units and positive absolute TP conditions."""
    while True:
        unit = input("Temperature unit [K/C]: ").strip().upper()
        if unit not in ("K", "C"):
            print("Choose K or C.")
            continue
        try:
            value = float(input(f"Temperature [{unit}]: "))
            temperature = TPConditions.from_units(
                value, 1, temperature_unit=unit, pressure_unit="Pa"
            ).temperature_k
        except ValueError as error:
            print(f"Temperature error: {error}")
            continue
        break

    print("Pressure must be ABSOLUTE, not gauge pressure.")
    while True:
        unit = input("Absolute pressure unit [Pa/bar]: ").strip().lower()
        if unit not in ("pa", "bar"):
            print("Choose Pa or bar; gauge units are not accepted.")
            continue
        try:
            value = float(input(f"Absolute pressure [{unit}]: "))
            return TPConditions.from_units(
                temperature, value, temperature_unit="K", pressure_unit=unit
            )
        except ValueError as error:
            print(f"Pressure error: {error}")


def main():
    parser = argparse.ArgumentParser(
        description="Select PetroFlash feed components and mole percentages."
    )
    parser.add_argument(
        "--database",
        default="data/components.json",
        help="Path to the component JSON database.",
    )
    args = parser.parse_args()

    try:
        database = ComponentDatabase.from_file(args.database)
    except (OSError, TypeError, ValueError, KeyError) as error:
        parser.exit(1, f"Database error: {error}\n")

    try:
        mixture = read_mixture(database)
        conditions = read_conditions()
    except (EOFError, KeyboardInterrupt):
        print("\nInput cancelled.")
        return

    print("\nValidated overall feed composition:")
    print(f"{'Component':<20} {'Mole %':>12} {'Mole fraction':>16}")
    for component, percentage, fraction in zip(
        mixture.components,
        mixture.mole_percentages,
        mixture.mole_fractions,
    ):
        print(f"{component.name:<20} {percentage:>12.6f} {fraction:>16.8f}")

    print(f"\nTemperature: {conditions.temperature_k:.8g} K")
    print(f"Absolute pressure: {conditions.pressure_pa:.8g} Pa")
    print("Feed and TP conditions are ready. Flash calculation is not implemented yet.")


if __name__ == "__main__":
    main()
