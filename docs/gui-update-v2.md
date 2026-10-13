# GUI v2 update

Apply `petroflash-gui-v2.zip` in the repository root (not inside `src`). Close the
old GUI first. This update replaces only the two GUI modules and their tests,
and adds this note. It does not replace the thermodynamic engine or dataset.

```powershell
Expand-Archive -LiteralPath .\petroflash-gui-v2.zip -DestinationPath . -Force
.\.venv\Scripts\python.exe -m petroflash.gui
```

## Changes

- The horizontal scrollbar is below the property table, rather than over it.
- Fonts and row heights are increased; numeric results and provenance use LTR
  text with separate Persian labels to avoid mixed-direction ordering.
- Every selected component displays identity (name, CAS, formula) and its four
  stored properties. Selecting a property shows all recorded metadata below.
- The model field is disabled with `Peng-Robinson (PR1976)` preselected. The
  model-to-engine mapping contains only an implemented model.
- The old checkbox was consent to an all-zero `kij` assumption, not an option
  to enable/disable physical interactions. The GUI now displays that assumption
  permanently and includes it in each successful calculation report.

## Screenshot case reproduced

Dataset 0.5.0; engine and independent reference from commit
`4f30a9fae9115773687762b5df2a4b17ad4de8ef`.
Feed: ethane 30 mol%, n-butane 20 mol%, isobutane 50 mol%.
Temperature: -10 C = 263.15 K. All `kij = 0`.

| Absolute pressure (bar) | Engine status | Vapor mole fraction | Independent PR check |
|---|---|---|---|
| 100 | single_phase_candidate | Not assigned | 263 sampled compositions found no negative TPD; one admissible feed root, Z=0.36888891 |
| 5 | two_phase | 0.05665814210 | Independent beta=0.05665814183 |
| 2 | two_phase | 0.49398360402 | Independent beta=0.49398360471 |

Finite stability searches/sampling do not certify global stability. The 100 bar
case is physically consistent with compressed liquid; the current engine does
not assign a liquid/vapor label or beta to a single-phase candidate. No
experimental validation is claimed.

## Verification limits

Eight tests cover property metadata, result formatting, the overlapping-scrollbar
regression, the disabled model selector, and real-engine calculations at 100
and 2 bar. Layout tests capture widget geometry without rendering a native
window; Windows visual rendering still needs verification on the user's machine.
