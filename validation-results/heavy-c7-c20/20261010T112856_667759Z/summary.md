# PetroFlash heavy-hydrocarbon numerical verification

Same database properties and PR1976 settings; this is not experimental validation.

PASS: matching two-phase results. LIMITED: no sampling contradiction, not proof of stability.
FAIL: discrepancy. UNRESOLVED: solver/reference did not provide an accepted comparison.

| Case | Engine | Verdict | beta | max comparison error | seconds |
|---|---|---|---:|---:|---:|
| light_C7_C10_T350_P10 | two_phase | PASS | 0.6066131925690321 | 3.7709280142905754e-11 | 0.105029 |
| light_C7_C10_T400_P30 | two_phase | PASS | 0.5954790757533743 | 1.953158745848782e-10 | 0.100583 |
| light_C7_C10_T450_P80 | two_phase | PASS | 0.5328410214654298 | 6.729867774168952e-10 | 0.120395 |
| light_C13_C20_T350_P10 | two_phase | PASS | 0.5799699856314788 | 1.136457664085988e-10 | 0.124998 |
| light_C13_C20_T400_P30 | two_phase | PASS | 0.5463310677373769 | 4.8721249257255295e-11 | 0.156333 |
| light_C13_C20_T450_P80 | two_phase | PASS | 0.45117444931870665 | 3.565303052788238e-10 | 0.178165 |
| broad_C1_C20_T350_P10 | two_phase | PASS | 0.6136272497049795 | 1.2848611063986937e-12 | 0.689770 |
| broad_C1_C20_T400_P30 | two_phase | PASS | 0.5752659509632494 | 2.0511370379949767e-11 | 0.490601 |
| broad_C1_C20_T450_P80 | two_phase | PASS | 0.46068296899058225 | 1.6254436685514406e-10 | 0.597720 |
| trace_C20_T350_P10 | two_phase | PASS | 0.7326093380516383 | 1.2743028854345084e-11 | 0.092647 |
| trace_C20_T400_P30 | two_phase | PASS | 0.7523874242983624 | 1.7116918993309582e-10 | 0.112275 |
| trace_C20_T450_P80 | two_phase | PASS | 0.7858182529383271 | 8.133312912050883e-10 | 0.208541 |
| broad_C1_C20_synthetic_kij | two_phase | PASS | 0.6172073998279188 | 5.7973625899876424e-12 | 1.006784 |
| broad_C1_C20_reversed_order | two_phase | PASS | 0.6136272497049795 | 1.2850831510036187e-12 | 0.681618 |

Counts: {'PASS': 14}

Skipped: []

Positive feed fractions; three and eight components, trace C20, synthetic kij and order reversal. Fixed-seed TPD sampling.
Finite tests do not certify global stability, critical-region reliability or experimental accuracy.
Times are single-run measurements, not a rigorous speed benchmark.
