# PetroFlash boundary and critical-vicinity numerical stress tests

Same database properties and PR1976 settings; this is not experimental validation.

PASS: matching two-phase results. LIMITED: no sampling contradiction, not proof of stability.
FAIL: discrepancy. UNRESOLVED: solver/reference did not provide an accepted comparison.

| Case | Engine | Verdict | beta | max comparison error | seconds |
|---|---|---|---:|---:|---:|
| pressure_scan_T300_P60 | two_phase | PASS | 0.31649060222511594 | 3.463079323307028e-09 | 0.090526 |
| pressure_scan_T300_P80 | two_phase | PASS | 0.17939248291131094 | 1.0760476815141473e-08 | 0.101471 |
| pressure_scan_T300_P100 | single_phase_candidate | LIMITED | None | n/a | 0.041134 |
| pressure_scan_T300_P120 | single_phase_candidate | LIMITED | None | n/a | 0.039246 |
| pressure_scan_T300_P140 | single_phase_candidate | LIMITED | None | n/a | 0.034411 |
| pressure_scan_T300_P160 | single_phase_candidate | LIMITED | None | n/a | 0.030699 |
| pressure_scan_T350_P40 | two_phase | PASS | 0.6923072603380263 | 2.5226097877251163e-09 | 0.078058 |
| pressure_scan_T350_P60 | two_phase | PASS | 0.5436880569824325 | 2.0857813254338e-09 | 0.093100 |
| pressure_scan_T350_P80 | two_phase | PASS | 0.40739155057701737 | 5.727666119170749e-09 | 0.122620 |
| pressure_scan_T350_P100 | two_phase | PASS | 0.18590495590802902 | 9.512228671404444e-09 | 0.227659 |
| pressure_scan_T350_P120 | single_phase_candidate | LIMITED | None | n/a | 0.069868 |
| pressure_scan_T350_P140 | single_phase_candidate | LIMITED | None | n/a | 0.048018 |
| pressure_scan_T400_P20 | single_phase_candidate | LIMITED | None | n/a | 0.019880 |
| pressure_scan_T400_P40 | single_phase_candidate | LIMITED | None | n/a | 0.024262 |
| pressure_scan_T400_P60 | single_phase_candidate | LIMITED | None | n/a | 0.033291 |
| pressure_scan_T400_P80 | single_phase_candidate | LIMITED | None | n/a | 0.047072 |
| pressure_scan_T400_P100 | single_phase_candidate | LIMITED | None | n/a | 0.060119 |
| pressure_scan_T400_P120 | single_phase_candidate | LIMITED | None | n/a | 0.056982 |
| bubble_inside_eps0.01 | two_phase | PASS | 0.010000001794217894 | 1.7942186226332923e-09 | 0.058073 |
| dew_inside_eps0.01 | two_phase | PASS | 0.9899999999860647 | 1.0954921414452201e-09 | 0.057411 |
| bubble_outside_eps0.01 | single_phase_candidate | LIMITED | None | n/a | 0.020236 |
| dew_outside_eps0.01 | single_phase_candidate | LIMITED | None | n/a | 0.019730 |
| bubble_inside_eps0.0001 | two_phase | PASS | 0.00010000181038449796 | 1.8103857878147642e-09 | 0.057413 |
| dew_inside_eps0.0001 | two_phase | PASS | 0.9998999999994771 | 1.572456109766307e-09 | 0.056411 |
| bubble_outside_eps0.0001 | single_phase_candidate | LIMITED | None | n/a | 0.018806 |
| dew_outside_eps0.0001 | single_phase_candidate | LIMITED | None | n/a | 0.018969 |
| bubble_inside_eps1e-06 | two_phase | PASS | 1.0018105385256604e-06 | 1.8105405654216381e-09 | 0.057404 |
| dew_inside_eps1e-06 | two_phase | PASS | 0.9999989999996703 | 1.5783387652401615e-09 | 0.059045 |
| bubble_outside_eps1e-06 | single_phase_candidate | LIMITED | None | n/a | 0.018271 |
| dew_outside_eps1e-06 | single_phase_candidate | LIMITED | None | n/a | 0.019081 |
| bubble_inside_eps1e-08 | inconclusive | UNRESOLVED | None | n/a | 0.048389 |
| dew_inside_eps1e-08 | inconclusive | UNRESOLVED | None | n/a | 0.050687 |
| bubble_outside_eps1e-08 | single_phase_candidate | LIMITED | None | n/a | 0.019347 |
| dew_outside_eps1e-08 | single_phase_candidate | LIMITED | None | n/a | 0.018018 |

Counts: {'PASS': 12, 'LIMITED': 20, 'UNRESOLVED': 2}

Skipped: []

Binary pressure sweeps and composition-boundary distances down to 1e-8 of the tie-line width.
Pure methane root tests are near nominal critical data; no mixture critical point is located.
Root diagnostic counts: {'PASS': 9}
UNRESOLVED entries are retained; do not relax tolerances merely to obtain PASS.
Finite tests do not certify global stability, critical-region reliability or experimental accuracy.
Times are single-run measurements, not a rigorous speed benchmark.
