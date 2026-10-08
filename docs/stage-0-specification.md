# Stage 0: Scientific and Software Specification

Status: Initial specification; implementation and validation pending.

## 1. Purpose and scope
PetroFlash will calculate nonreactive temperature-pressure equilibrium
for identified petroleum and natural-gas components using PR and SRK.

The initial solver supports one fluid phase or vapor-liquid equilibrium.
Multiple liquid phases, solids, hydrates, reactions, PC-SAFT,
asphaltene separation, and plus-fraction characterization are deferred.

No universal accuracy or convergence guarantee is claimed.
The validated domain will be established from documented test cases.

## 2. Inputs and units
Required inputs: component identifiers, overall composition, temperature,
pressure, EOS selection, and binary interaction parameter policy.

Internal units:
- Temperature: K
- Absolute pressure: Pa
- Amount: mol
- Molar volume: m3/mol
- Molar mass: kg/mol
- Mass density: kg/m3
- Energy: J/mol

Internal composition basis: mole fractions.
Mass fractions may be converted using component molar masses.

Inputs must be finite. Temperature and pressure must be positive.
Negative fractions, duplicate components, and zero total composition
are rejected.

Normalization must be explicitly requested or limited to documented
roundoff tolerance. Every applied normalization is reported.
Zero-composition components are excluded from logarithmic calculations
and restored in output vectors.

## 3. Component data
Identity is resolved using CAS numbers and unambiguous identifiers.
Required EOS data: critical temperature, critical pressure,
and acentric factor. Molar mass is required for density and conversion.

Each property records its value, unit, source, and data method.
Estimated properties are labeled. Missing data remain missing.
Selected data are stored locally with a reproducible version.

Water is permitted in the database. Its inclusion does not establish
validated general water-oil-gas equilibrium capability.

## 4. Equations of state
Initial variants: PR76 and SRK72 with their standard alpha functions.
Any later alpha variant must have a separate documented identifier.

Classical quadratic attraction and linear covolume mixing rules:
a_mix = sum_i sum_j x_i*x_j*sqrt(a_i*a_j)*(1-k_ij)
b_mix = sum_i x_i*b_i

Initial interaction matrices are symmetric with zero diagonal.
Parameters are specific to the EOS and mixing-rule variant.

Missing interaction data are not silently replaced by zero.
Strict mode rejects missing required parameters.
Explicit zero assumptions are supported and recorded.

## 5. EOS root handling
Calculate and inspect all real cubic roots.
Check Z > B, polynomial residuals, and mechanical admissibility.
Use Gibbs comparisons where applicable to choose the reference state.

Do not replace failed root calculations with guessed volumes.
A single cubic root does not by itself prove mixture phase stability.

## 6. Equilibrium strategy
Perform tangent-plane-distance stability analysis with multiple starts.
Use stability-informed initialization for vapor-liquid flash.

Solve Rachford-Rice with a bracketed, safeguarded method.
Iterate log K using fugacity equality, with controlled damping
and a documented fallback strategy.

Provide constrained Gibbs minimization as an alternative solution path.
The objective includes composition-dependent mixing contributions.
For fixed nonreactive component inventories at fixed T and P,
common reference contributions may be omitted consistently.

Preserve nonnegative phase amounts and component balances.
Local optimization success does not certify a global minimum.
Report stability as inconclusive when the evidence is insufficient.

## 7. Special cases
At pure-component saturation, T and P alone do not determine
the vapor fraction. Report this degeneracy explicitly.

Handle phase-boundary limits, trace components, and K near unity.
Avoid arbitrary vapor/liquid labels in ambiguous single-fluid states.

If a supported VLE solution is unstable toward an additional liquid
phase, report an unsupported equilibrium rather than accepted VLE.

## 8. Result contract
A result records:
- Phase status, convergence status, and explanatory diagnostics.
- Present phase fractions and compositions.
- Z, molar volume, and EOS-derived density for each present phase.
- Fugacity coefficients and K values where defined.
- Balance and equilibrium residuals.
- Stability findings and Gibbs comparisons.
- Iteration counts and solution methods.
- Input units, normalization, and parameter assumptions.
- Database, software, and solver-setting versions.

Absent phase properties are not populated with invented values.
Unconverged iterates are identified as diagnostic data.

## 9. Verification and validation
Verification checks equations, units, balances, limiting behavior,
and agreement with independent implementations of the same model.

Comparison requires identical pure-component data, alpha functions,
mixing rules, and interaction parameters.

Validation uses documented experimental data.
Agreement between software packages is not experimental validation.
Parameter-fitting data are separated from independent validation data.

Initial numerical targets for well-conditioned two-phase cases:
- Maximum absolute component balance residual: 1e-10.
- Maximum absolute log fugacity ratio for active components: 1e-8.

Trace-component, near-critical, root, and stability tolerances
will be documented separately with scaling and test evidence.
These numerical tolerances do not imply experimental accuracy.

## 10. Architecture and environment
Use separate modules for components, database, mixtures, interactions,
EOS, mixing rules, stability, flash, Gibbs optimization, and results.

Keep computational logic in the package.
Use Jupyter notebooks for examples and instruction.

Initial development environment: Python 3.11 in a project-local venv.
Record resolved dependency versions once dependencies are installed.
Review applicable licenses before reusing code or redistributing data.

## 11. Stage 0 completion criteria
- Scope, units, EOS variants, and data policies are documented.
- Input and result contracts are defined.
- Verification and validation are distinguished.
- Local environment is isolated and excluded from version control.
- Specification and environment setup are committed and pushed.

Stage 0 completion does not mean the solver is implemented or validated.
