# Dataset 0.4.0: available HEOS records within C11-C20

Adds n-undecane (1120-21-4), n-dodecane (112-40-3) and n-hexadecane
(544-76-3) to dataset 0.3.0. All 16 prior records and order are preserved.
The dataset now has 19 records. Schema remains 1.
This is partial C11-C20 coverage, not a claim that all n-alkanes through C20 exist.

Provider: chemicals 1.5.2. Tc/Pc/omega are selected explicitly from HEOS;
molar mass is identifiers metadata converted to kg/mol. EVALUATED is the
existing project's selected-reference classification. Uncertainty remains
unknown (null); no numerical uncertainty is invented.

| Component | Tc K | Pc Pa | omega | MW kg/mol |
|---|---:|---:|---:|---:|
| n-undecane |638.8|1990400|0.539|0.15630826|
| n-dodecane |658.1|1817000|0.574|0.17033484|
| n-hexadecane |722.1|1479850|0.749|0.22644116|

For C13, C14, C15, C17, C18, C19 and C20 the provider has no HEOS values for
all three selected properties. These components are not loaded into the
operational dataset. Available alternative method names are recorded for
all ten requested substances in docs/data-audit-c11-c20.json. Their presence
is not approval of those values or evidence that every source is experimental.

Documentation, accessed 2026-10-10:
https://chemicals.readthedocs.io/chemicals.critical.html
https://chemicals.readthedocs.io/chemicals.acentric.html
https://chemicals.readthedocs.io/chemicals.identifiers.html
For a future explicit policy extension, evaluate IUPAC critical-property
compilations (including Ambrose and Tsonopoulos, Normal Alkanes,
https://doi.org/10.1021/je00019a001) and a separately justified source for omega.
Do not use the provider's automatic default as an undocumented fallback.
This delivery introduces no such policy change.

Use the ready JSON without rebuilding or changing installed dependencies.
The optional builder deliberately requires chemicals==1.5.2. The preceding
Thermo offline environment has chemicals 1.5.0 and will fail that version gate;
use a separate build environment if rebuilding. Runtime JSON loading does not
require that provider version. No CLI changes are needed for new names.

The original PR1976 quadratic alpha remains the default, including for these
higher omega values. WHITSON_PROBLEM18 remains an explicitly selected book
benchmark mode. Neither record availability nor software tests validate PR1976
predictions for these compounds. No melting-point data or solid-phase model is
added. At sufficiently low temperatures heavy n-alkanes may form solids;
use the present VLE solver only where neglect of solids is justified.
No kij data or fitted alpha parameters are supplied.

Preparation checks: three new standalone tests passed, the previous C7-C10
standalone regression tests also passed against the expanded JSON, all original
16 records were preserved, and builder inventory matches dataset order.
Full loader/integration tests need the user's complete repository. Expected
suite count: 137 if the preceding baseline is 134.

From repository root:
    .\.venv\Scripts\python.exe -m unittest discover -s tests -v
    .\.venv\Scripts\python.exe -c "from petroflash import ComponentDatabase; d=ComponentDatabase.from_file('data/components.json'); print(d.dataset_version, len(d)); print(d.names())"

Historical coverage reports retain their original scope; the new audit is a
separate C11-C20 coverage report. The Persian learning guide is updated only
when explicitly requested.

Commit only the six files in this delivery, excluding delivery archives:
    data: add available HEOS C11-C20 records and document coverage gaps
