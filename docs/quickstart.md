# PetroFlash quick start

Run commands from the repository root in PowerShell.

## Setup on a new machine

1. Create the environment:

   `py -3.11 -m venv .venv`

2. Install recorded dependencies:

   `\.venv\Scripts\python.exe -m pip install -r requirements-win-py311.txt`

3. Install PetroFlash in editable mode:

   `\.venv\Scripts\python.exe -m pip install -e .`

If the default package index is unreachable, append this option to the pip
install command:

`--index-url https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple`

## Run the graphical interface

After editable installation, launch the desktop application with:

`\.venv\Scripts\python.exe -m petroflash.gui`

The GUI loads `data/components.json` from the repository root. To use a dataset
at another path, pass `--database PATH`. The material list supports search by
name or CAS and multiple selection. Selecting materials immediately displays
their four stored properties and provenance. Enter mole percentages, a
temperature, and absolute pressure, then press **محاسبهٔ فلش**. The interface
shows a result only when the engine accepts one.

The current GUI requires an explicit checkbox to use the assumption that every
binary interaction parameter is zero. No interaction-parameter dataset is
provided. Active non-hydrocarbon feeds are outside the current flash scope.
The package core remains dependency-free; the interface uses Python's Tkinter.

The installed GUI entry point is also available as `petroflash-gui` on Windows
after reinstalling the editable package with `python -m pip install -e .`.

## Run the command-line interface

`\.venv\Scripts\python.exe -m petroflash.cli --flash`

## Use the central database in Python

```python
from petroflash import ComponentDatabase

db = ComponentDatabase.from_file("data/components.json")
print(db.dataset_version, len(db), db.names())

methane = db.get("methane")
print(methane.critical_temperature.value)
print(methane.critical_temperature.unit)
print(methane.critical_temperature.source)
```

The JSON dataset is external to the installed package. Relative paths start
from the current working directory. Use an absolute dataset path when working
elsewhere.

## Run tests

`\.venv\Scripts\python.exe -m unittest discover -s tests -v`

## Current scope

- Package version: 0.1.0.
- Dataset version: 0.5.0, containing 26 components.
- CLI and Tkinter GUI support component selection, mole percentages, and TP
  flash input.
- The baseline flash is PR1976 vapor–liquid equilibrium for simple
  hydrocarbon feeds; it has no solid-phase model or global stability proof.
- Passing software or independent numerical checks does not establish
  experimental validation.
