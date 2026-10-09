# PetroFlash binary numerical verification

Same database properties and PR1976 settings; this is not experimental validation.

PASS: matching two-phase results. LIMITED: no grid contradiction, not proof of stability.
FAIL: discrepancy. UNRESOLVED: solver/reference did not provide an accepted comparison.

| Case | Engine | Verdict | beta | max comparison error | seconds |
|---|---|---|---:|---:|---:|
| T250_P1_z0.5_k0 | two_phase | PASS | 0.8309869027525565 | 7.305778204624858e-11 | 0.107044 |
| T250_P5_z0.5_k0 | two_phase | PASS | 0.5262662249342611 | 6.530354035305663e-11 | 0.088825 |
| T250_P20_z0.5_k0 | two_phase | PASS | 0.4160636163287563 | 1.2855053133087324e-09 | 0.062321 |
| T250_P50_z0.5_k0 | two_phase | PASS | 0.1962083051657828 | 1.8701463155856857e-09 | 0.069073 |
| T250_P100_z0.5_k0 | single_phase_candidate | LIMITED | None | n/a | 0.030253 |
| T300_P1_z0.5_k0 | single_phase_candidate | LIMITED | None | n/a | 0.024720 |
| T300_P20_z0.5_k0 | two_phase | PASS | 0.543962596786514 | 3.766416067918499e-10 | 0.079167 |
| T300_P80_z0.5_k0 | two_phase | PASS | 0.17939248291077092 | 1.0759936858173447e-08 | 0.094186 |
| T450_P1_z0.5_k0 | single_phase_candidate | LIMITED | None | n/a | 0.017209 |
| T450_P200_z0.5_k0 | single_phase_candidate | LIMITED | None | n/a | 0.029732 |
| T250_P20_z0.1_k0 | single_phase_candidate | LIMITED | None | n/a | 0.018204 |
| T250_P20_z0.9_k0 | two_phase | PASS | 0.9117197875104921 | 2.2704879643065112e-10 | 0.059260 |
| T350_P50_z0.5_k0 | two_phase | PASS | 0.6108766875840956 | 2.811014310211135e-09 | 0.128262 |
| T250_P20_z0.5_k0.03 | two_phase | PASS | 0.43017629343830777 | 2.8946364749593556e-10 | 0.071381 |
| near_bubble_inside | two_phase | PASS | 0.0001000018105514755 | 1.8036338816516864e-09 | 0.056474 |
| near_dew_inside | two_phase | PASS | 0.9998999999994567 | 1.5724957447282861e-09 | 0.056335 |
| bubble_outside | single_phase_candidate | LIMITED | None | n/a | 0.019077 |
| dew_outside | single_phase_candidate | LIMITED | None | n/a | 0.018405 |

Counts: {'PASS': 11, 'LIMITED': 7}

Skipped: []

Boundary cases vary feed composition at fixed T/P along a reference binary tie-line.
The campaign does not establish critical-region or multicomponent reliability.
Times are single-run measurements, not a rigorous speed benchmark.
