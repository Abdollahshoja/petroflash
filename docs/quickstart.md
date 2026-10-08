# PetroFlash quick start

Run commands from the repository root in PowerShell.

## Setup on a new machine

1. Create the environment:
   py -3.11 -m venv .venv

2. Install recorded dependencies:
   .\.venv\Scripts\python.exe -m pip install -r requirements-win-py311.txt

3. Install PetroFlash in editable mode:
   .\.venv\Scripts\python.exe -m pip install -e .

If the default package index is unreachable, append this option
to the pip install command:
--index-url https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple

## Use the central database in Python

    from petroflash import ComponentDatabase

    db = ComponentDatabase.from_file("data/components.json")
    print(db.names())

    methane = db.get("methane")
    print(methane.critical_temperature.value)
    print(methane.critical_temperature.unit)
    print(methane.critical_temperature.source)

    selected = db.select(["methane", "ethane", "propane"])

The JSON dataset is external to the installed package.
Relative paths start from the current working directory.
Use an absolute dataset path when working elsewhere.

## Run tests

    .\.venv\Scripts\python.exe -m unittest discover -s tests -v

## Current scope

- Package version: 0.1.0.
- Dataset version: 0.2.0, containing 12 components.
- Latest confirmed test run: 35 passing tests.
- Component lookup and validated JSON loading are implemented.
- Mixture composition, interaction parameters and flash solvers are pending.
- Passing software tests does not establish experimental validation.

See learning-guide-fa.md for the Persian development tutorial.
