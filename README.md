# PetroFlash GUI patch

This is an overlay patch for the `stage-2-mixture` PetroFlash checkout. It adds
a Tkinter GUI that calls the existing `flash_tp` calculation path, displays the
four properties stored for each selected material with their provenance, and
collects mole percentages, temperature, and absolute pressure.

## Apply on Windows PowerShell

From the root of the PetroFlash repository, extract this archive into the
current directory and allow it to replace the included `pyproject.toml` and
`docs/quickstart.md` with the versions in this patch. Then reinstall editable
mode and run the GUI:

```powershell
Expand-Archive -Path .\petroflash-gui-step.zip -DestinationPath . -Force
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m petroflash.gui
```

The dataset defaults to `data/components.json`; pass `--database PATH` to use
another file. The user must explicitly confirm the all-zero `kij` assumption
for each calculation. The GUI does not add new thermodynamic capabilities; its
results are subject to the existing engine's scope and limitations.

## Checks performed for this patch

- Python syntax compilation for `gui.py` and `gui_helpers.py`.
- Four headless unit tests for property provenance and accepted-result display.
- A native Tk window and a full flash against the actual project checkout were
  not run in this workspace.
