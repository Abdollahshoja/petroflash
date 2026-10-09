# PetroFlash boundary and critical-vicinity numerical stress tests

Same database properties and PR1976 settings; this is not experimental validation.

PASS: matching two-phase results. LIMITED: no sampling contradiction, not proof of stability.
FAIL: discrepancy. UNRESOLVED: solver/reference did not provide an accepted comparison.

| Case | Engine | Verdict | beta | max comparison error | seconds |
|---|---|---|---:|---:|---:|
| pressure_scan_T300_P60 | two_phase | PASS | 0.3164906022248033 | 3.4627666845032934e-09 | 0.090316 |
| pressure_scan_T300_P80 | two_phase | PASS | 0.17939248291077092 | 1.0759936802662295e-08 | 0.101109 |
| pressure_scan_T300_P100 | single_phase_candidate | LIMITED | None | n/a | 0.043643 |
| pressure_scan_T300_P120 | single_phase_candidate | LIMITED | None | n/a | 0.039158 |
| pressure_scan_T300_P140 | single_phase_candidate | LIMITED | None | n/a | 0.042630 |
| pressure_scan_T300_P160 | single_phase_candidate | LIMITED | None | n/a | 0.032715 |
| pressure_scan_T350_P40 | two_phase | PASS | 0.6923072603385663 | 2.5220697752459387e-09 | 0.077135 |
| pressure_scan_T350_P60 | two_phase | PASS | 0.5436880569814093 | 2.0868045069732943e-09 | 0.091555 |
| pressure_scan_T350_P80 | two_phase | PASS | 0.4073915505759942 | 5.727725405080264e-09 | 0.123924 |
| pressure_scan_T350_P100 | two_phase | PASS | 0.18590495591342915 | 9.511877174794847e-09 | 0.234630 |
| pressure_scan_T350_P120 | single_phase_candidate | LIMITED | None | n/a | 0.070972 |
| pressure_scan_T350_P140 | single_phase_candidate | LIMITED | None | n/a | 0.048486 |
| pressure_scan_T400_P20 | single_phase_candidate | LIMITED | None | n/a | 0.019908 |
| pressure_scan_T400_P40 | single_phase_candidate | LIMITED | None | n/a | 0.024945 |
| pressure_scan_T400_P60 | single_phase_candidate | LIMITED | None | n/a | 0.032404 |
| pressure_scan_T400_P80 | single_phase_candidate | LIMITED | None | n/a | 0.047370 |
| pressure_scan_T400_P100 | single_phase_candidate | LIMITED | None | n/a | 0.058378 |
| pressure_scan_T400_P120 | single_phase_candidate | LIMITED | None | n/a | 0.055399 |
| bubble_inside_eps0.01 | two_phase | PASS | 0.010000001794196578 | 1.7941973063512195e-09 | 0.057778 |
| dew_inside_eps0.01 | two_phase | PASS | 0.9899999999860256 | 1.0961642704643282e-09 | 0.056857 |
| bubble_outside_eps0.01 | single_phase_candidate | LIMITED | None | n/a | 0.018654 |
| dew_outside_eps0.01 | single_phase_candidate | LIMITED | None | n/a | 0.019127 |
| bubble_inside_eps0.0001 | two_phase | PASS | 0.0001000018105514755 | 1.8105527653576679e-09 | 0.056716 |
| dew_inside_eps0.0001 | two_phase | PASS | 0.9998999999994567 | 1.5729522129248608e-09 | 0.055705 |
| bubble_outside_eps0.0001 | single_phase_candidate | LIMITED | None | n/a | 0.019199 |
| dew_outside_eps0.0001 | single_phase_candidate | LIMITED | None | n/a | 0.019703 |
| bubble_inside_eps1e-06 | inconclusive | UNRESOLVED | None | n/a | 0.046059 |
| dew_inside_eps1e-06 | inconclusive | UNRESOLVED | None | n/a | 0.048842 |
| bubble_outside_eps1e-06 | single_phase_candidate | LIMITED | None | n/a | 0.019677 |
| dew_outside_eps1e-06 | single_phase_candidate | LIMITED | None | n/a | 0.018683 |
| bubble_inside_eps1e-08 | inconclusive | UNRESOLVED | None | n/a | 0.049374 |
| dew_inside_eps1e-08 | inconclusive | UNRESOLVED | None | n/a | 0.049727 |
| bubble_outside_eps1e-08 | single_phase_candidate | LIMITED | None | n/a | 0.018931 |
| dew_outside_eps1e-08 | single_phase_candidate | LIMITED | None | n/a | 0.018734 |

Counts: {'PASS': 10, 'LIMITED': 20, 'UNRESOLVED': 4}

Skipped: []

Binary pressure sweeps and composition-boundary distances down to 1e-8 of the tie-line width.
Pure methane root tests are near nominal critical data; no mixture critical point is located.
Root diagnostic counts: {'PASS': 9}
UNRESOLVED entries are retained; do not relax tolerances merely to obtain PASS.
Finite tests do not certify global stability, critical-region reliability or experimental accuracy.
Times are single-run measurements, not a rigorous speed benchmark.
