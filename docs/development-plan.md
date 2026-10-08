# PetroFlash Development Plan

## Objective
Develop a modular, object-oriented Python package for petroleum-fluid
temperature-pressure flash calculations using Peng-Robinson and
Soave-Redlich-Kwong equations of state.

## Initial scope
- Documented pure-component database.
- Mixture composition and binary interaction parameter management.
- Single-phase and vapor-liquid equilibrium calculations.
- Phase stability analysis and fugacity-based flash calculations.
- Constrained Gibbs energy minimization.
- Explicit convergence diagnostics and reproducible results.

## Deferred scope
- Petroleum plus-fraction characterization.
- PC-SAFT.
- Asphaltene phase separation.
- Multiple liquid phases, solids, hydrates, and reactive equilibrium.

Water may be included in the database, but general water-oil-gas
equilibrium is outside the initial validated scope.

## Development stages
0. Define scientific assumptions, units, interfaces, and acceptance criteria.
1. Build the documented component database and component classes.
2. Implement mixture definitions and binary interaction parameter handling.
3. Implement and verify the Peng-Robinson equation of state.
4. Implement and verify the Soave-Redlich-Kwong equation of state.
5. Implement phase stability analysis.
6. Implement the temperature-pressure flash solver.
7. Implement constrained Gibbs energy minimization.
8. Complete verification, experimental validation, and robustness assessment.
9. Package the software and provide Jupyter examples and documentation.

Tests will accompany each implementation stage.

## Scientific requirements
- Use consistent internal SI units.
- Record property sources and database versions.
- Distinguish missing interaction parameters from explicitly assumed zeros.
- Report numerical failures without substituting unverified estimates.
- Check component balances, fugacity equality, and phase stability.
- Distinguish software verification from experimental validation.
- Document the validated operating domain and model limitations.
- Treat legacy code as background material, not as a reference solution.

## Reference resources
- Chemicals: https://github.com/CalebBell/chemicals
- Thermo: https://github.com/CalebBell/thermo
- ThermoPack: https://github.com/thermotools/thermopack
- NIST Chemistry WebBook: https://webbook.nist.gov/chemistry/

Record versions and review applicable licenses before reuse.

## Development workflow
- Record each coherent change in a descriptive commit.
- Push completed commits to GitHub.
- Introduce implementation changes through feature branches.
- Keep credentials, virtual environments, and temporary outputs out of Git.
- Record test evidence and known limitations with each milestone.

## Current status
Repository setup completed locally.
Development plan recorded before Stage 0 implementation.
Push access remains to be verified.
