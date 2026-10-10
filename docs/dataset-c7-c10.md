# Dataset 0.3.0: C7-C10 extension

Adds n-heptane, n-octane, n-nonane and n-decane to the original 12 records.
All original records and their order are preserved. New records are appended.
Schema remains 1. Dataset version becomes 0.3.0; application version is unchanged.

Values were extracted from chemicals 1.5.2, explicitly selecting HEOS for Tc,
Pc and omega. Molecular mass comes from identifiers metadata, converted to kg/mol.
No fallback, estimated replacement, kij or uncertainty value is invented.
EVALUATED retains the project's selected-reference-data classification; it does
not certify experimental accuracy of each value or accuracy of PR for these fluids.

Provider documentation (accessed 2026-10-10):
https://chemicals.readthedocs.io/chemicals.critical.html
https://chemicals.readthedocs.io/chemicals.acentric.html
https://chemicals.readthedocs.io/chemicals.identifiers.html
HEOS is an upstream collection drawing on REFPROP and other fundamental EOS;
this extraction does not constitute a direct REFPROP calculation or a per-fluid
primary-literature audit. The provider/version/method are retained in each record.

Use the supplied JSON directly. Runtime does not require chemicals 1.5.2.
The optional builder still deliberately requires chemicals==1.5.2 to reproduce
this source selection. The preceding Thermo offline installation used chemicals
1.5.0: running the builder there will stop with a version error. No rebuild is
needed to use this delivery. Prefer a separate build environment when rebuilding.

The builder now owns an explicit 16-component inventory rather than importing
it from the older coverage-audit script. Existing coverage reports remain
historical 12-component reports; they are not represented as 16-component audits.
The new audit is docs/data-audit-c7-c10.json. A test checks builder/data agreement.

Validation performed during preparation:
- All 12 previous records preserved exactly as decoded JSON records.
- All prior numerical properties checked against chemicals 1.5.2.
- New identities, CAS checksums, formulas, selected values, units and provenance.
- Three new standalone regression tests passed.
The full repository and its loader are not present in the preparation workspace;
the full test suite and builder round trip must be verified on the user's checkout.
Expected suite count is 134 if the preceding baseline remains 131.

From repository root:
    .\.venv\Scripts\python.exe -m unittest discover -s tests -v
    .\.venv\Scripts\python.exe -c "from petroflash import ComponentDatabase; d=ComponentDatabase.from_file('data/components.json'); print(d.dataset_version, len(d)); print(d.select(['n-heptane','n-octane','n-nonane','n-decane']))"

The CLI loads this dataset, so new names become selectable without a CLI edit.
PR1976 remains the default alpha policy, including for omega above 0.4.
WHITSON_PROBLEM18 is a specific benchmark option, not an automatic rule for
new heavy components. No new mixture kij values or experimental flash validation
are supplied by this dataset expansion.

Suggested commit summary:
    data: extend central component dataset with C7-C10 n-alkanes
Select only the six files supplied in this archive. Exclude delivery ZIPs,
offline wheel directories and unrelated working-tree changes.
