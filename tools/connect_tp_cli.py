"""Apply a guarded TP extension to the existing PetroFlash CLI."""
from pathlib import Path

path = Path('src/petroflash/cli.py')
text = path.read_text(encoding='utf-8-sig')
if 'def read_conditions(' in text:
    raise SystemExit('TP reader already exists. No changes made.')
function = '''def read_conditions():
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


'''
changes = (
    ('from .database import ComponentDatabase',
     'from .conditions import TPConditions\nfrom .database import ComponentDatabase'),
    ('def main():', function + 'def main():'),
    ('        mixture = read_mixture(database)',
     '        mixture = read_mixture(database)\n        conditions = read_conditions()'),
    ('    print("\\nFeed composition is ready. Flash calculation is not implemented yet.")',
     '    print(f"\\nTemperature: {conditions.temperature_k:.8g} K")\n'
     '    print(f"Absolute pressure: {conditions.pressure_pa:.8g} Pa")\n'
     '    print("Feed and TP conditions are ready. Flash calculation is not implemented yet.")'),
)
for old, new in changes:
    if text.count(old) != 1:
        raise SystemExit(f'Expected anchor missing or repeated: {old!r}. No changes made.')
    text = text.replace(old, new, 1)
compile(text, str(path), 'exec')
path.write_text(text, encoding='utf-8')
print('CLI now reads composition and explicit TP conditions.')
