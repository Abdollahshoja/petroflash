# CMU documented EOSFlash feed: independent software comparison

Source (accessed 2026-10-10):
https://kitchingroup.cheme.cmu.edu/differentiable-flowsheets/docs/unit-operations-chemical.html
Section: EOSFlash (Non-Ideal).

The source supplies an example feed and explicit critical properties, but no
numerical phase-split answer in that example. Outputs here are newly computed,
not quoted CMU results. We do not run or certify Difflow in this comparison.
Feed flows 40/30/30 are converted to mole fractions 0.4/0.3/0.3.
T=250 K, P=2e6 Pa. Components: methane, ethane, propane.
Tc=[190.6,305.4,369.8] K; Pc=[4.6e6,4.9e6,4.2e6] Pa;
omega=[0.011,0.099,0.152]. Explicit comparison assumption: all kij=0.
No central component database is changed.

Third-party reference: Thermo 0.6.0 FlashVL / PRMIX:
https://thermo.readthedocs.io/thermo.flash.html
https://thermo.readthedocs.io/_modules/thermo/eos_mix.html

Two reference runs are recorded:
- Unmodified Thermo: PR coefficients 0.4572355289213822, 0.07779607390388846.
- Explicit validation-only PRMIX subclass: coefficients 0.45724, 0.07780,
  matching PetroFlash. Alpha, mixing and third-party flash solver remain Thermo.
  Cached coefficient products are set consistently, and computed pure a(T), b
  are checked against PetroFlash. No production engine changes are made.

Install optional validation dependency:
`python -m pip install thermo==0.6.0`
Run from repository root:
`python tools/benchmark_web_cmu.py`

Output is a timestamped JSON report under validation-results/web-cmu.
PASS requires matched-model beta, x, y and Z differences <=2e-6,
fugacity residuals <=1e-8, material balances <=1e-10, and matching pure parameters.
The default-coefficient comparison is a sensitivity, not a same-model PASS.
The report records software version, source hashes, full inputs and results.
Only this optional validation script requires Thermo.

Development run: PetroFlash beta=0.5110807401666193;
Thermo aligned beta=0.5110807389030703;
Thermo default beta=0.5110400104445743.
These are numerical checks, not experimental validation or a global stability
certificate. They neither establish nor rule out an error in the Whitson book.
The full user repository test suite must still be run on the user's checkout.
