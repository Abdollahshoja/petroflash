"""Interactive feed input with optional PR1976 feed-property diagnostics."""

import argparse

from .conditions import TPConditions
from .database import ComponentDatabase
from .mixture import Mixture
from .pr_fugacity import mixture_pr_log_fugacity
from .pr_mixing import mixture_pr_parameters, zero_kij
from .pr_roots import solve_pr_roots


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


def confirm_zero_kij():
    """Require explicit consent to a model assumption for this run."""
    print("\nPR1976 feed-property calculation.")
    print("No binary interaction dataset is supplied in this mode.")
    while True:
        choice = input("Use the assumption that ALL kij = 0? [yes/no]: ").strip().casefold()
        if choice in ("yes", "y"):
            return True
        if choice in ("no", "n"):
            return False
        print("Choose yes or no.")


def print_pr_feed(mixture, conditions, *, kij):
    """Evaluate each admissible feed root, without selecting an equilibrium phase."""
    parameters = mixture_pr_parameters(mixture, conditions, kij=kij)
    roots = solve_pr_roots(A=parameters.A, B=parameters.B)
    # Compute every result before displaying a successful calculation.
    results = tuple(mixture_pr_log_fugacity(mixture, conditions, kij=kij, z=z)
                    for z in roots.admissible_roots)
    print("\nPR1976 properties at the OVERALL FEED composition:")
    print(f"a_m = {parameters.a_m:.12g} Pa m^6/mol^2")
    print(f"b_m = {parameters.b_m:.12g} m^3/mol")
    print(f"A = {parameters.A:.12g}; B = {parameters.B:.12g}")
    print("Distinct real roots:", roots.real_roots)
    print("Roots satisfying Z>B:", roots.admissible_roots)
    print("Scaled polynomial residuals:", roots.scaled_residuals)
    for result in results:
        print(f"\nZ = {result.z:.12g}")
        print(f"{'Component':<20} {'ln(phi)':>16}")
        for component, value in zip(mixture.components, result.ln_phi):
            print(f"{component.name:<20} {value:>16.10g}")
        print(f"g_residual/(RT) = {result.g_residual_rt:.12g}")
    print("\nPhase stability has NOT been tested; no vapor fraction is calculated.")
    print("These results are feed-property diagnostics, not a flash result.")


def main():
    parser = argparse.ArgumentParser(
        description="Read PetroFlash feed/TP inputs and optionally calculate PR feed properties."
    )
    parser.add_argument("--database", default="data/components.json",
                        help="Path to the component JSON database.")
    parser.add_argument("--pr", action="store_true",
                        help="Calculate PR1976 feed properties after explicit zero-kij confirmation.")
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
        mixture.components, mixture.mole_percentages, mixture.mole_fractions
    ):
        print(f"{component.name:<20} {percentage:>12.6f} {fraction:>16.8f}")
    print(f"\nTemperature: {conditions.temperature_k:.8g} K")
    print(f"Absolute pressure: {conditions.pressure_pa:.8g} Pa")
    if not args.pr:
        print("Feed and TP conditions are ready. Flash calculation is not implemented yet.")
        return
    try:
        if not confirm_zero_kij():
            print("PR calculation skipped. Supply validated interactions through the Python API.")
            return
        print("Model assumption for this run: ALL kij = 0; not validated pair data.")
        print_pr_feed(mixture, conditions, kij=zero_kij(len(mixture.components)))
    except (EOFError, KeyboardInterrupt):
        print("\nInput cancelled.")
    except (TypeError, ValueError, ArithmeticError) as error:
        parser.exit(1, f"PR calculation error: {error}\n")


if __name__ == "__main__":
    main()
