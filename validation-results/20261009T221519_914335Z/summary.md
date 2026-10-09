# PetroFlash multicomponent numerical verification

Same database properties and PR1976 settings; this is not experimental validation.

PASS: matching two-phase results. LIMITED: no sampling contradiction, not proof of stability.
FAIL: discrepancy. UNRESOLVED: solver/reference did not provide an accepted comparison.

| Case | Engine | Verdict | beta | max comparison error | seconds |
|---|---|---|---:|---:|---:|
| ternary_T250_P20 | two_phase | PASS | 0.7241921876247943 | 2.2463275684003747e-10 | 0.094619 |
| ternary_T300_P20 | single_phase_candidate | LIMITED | None | n/a | 0.028560 |
| ternary_T300_P60 | single_phase_candidate | LIMITED | None | n/a | 0.052639 |
| ternary_T450_P1 | single_phase_candidate | LIMITED | None | n/a | 0.025647 |
| quaternary_T250_P20 | two_phase | PASS | 0.11382256931574375 | 6.551812148369862e-10 | 0.133436 |
| quaternary_T300_P20 | two_phase | PASS | 0.55250024011184 | 4.5055551511907765e-09 | 0.148952 |
| quaternary_T300_P60 | single_phase_candidate | LIMITED | None | n/a | 0.058153 |
| quaternary_T450_P1 | single_phase_candidate | LIMITED | None | n/a | 0.036015 |
| six_components_T250_P20 | two_phase | PASS | 0.3695735148357926 | 1.8144447055945534e-10 | 0.230165 |
| six_components_T300_P20 | two_phase | PASS | 0.566516586306534 | 7.284388647832429e-10 | 0.278692 |
| six_components_T300_P60 | two_phase | PASS | 0.26117639282529126 | 7.448205052718038e-09 | 0.316707 |
| six_components_T450_P1 | single_phase_candidate | LIMITED | None | n/a | 0.065158 |
| quaternary_nonzero_kij | two_phase | PASS | 0.12964476070828823 | 1.5513199058680982e-09 | 0.126763 |
| quaternary_reversed_order | two_phase | PASS | 0.11382256931574375 | 6.551813536148643e-10 | 0.124354 |

Counts: {'PASS': 8, 'LIMITED': 6}

Skipped: []

Positive feed fractions; 3, 4 and 6 hydrocarbon components. Fixed-seed TPD sampling.
Finite tests do not certify global stability, critical-region reliability or experimental accuracy.
Times are single-run measurements, not a rigorous speed benchmark.
