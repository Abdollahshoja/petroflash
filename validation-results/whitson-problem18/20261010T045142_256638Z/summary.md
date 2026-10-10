# Whitson Appendix B Problem 18

Published calculated results, not experimental data. Exact F conversion for main cases.
Printed input properties; explicit Eq.4.22 for omega > 0.4; no volume translation.
BOOK_DIFFERENCE is retained at the printed output precision; no fitted inputs.

| psia | numerical | published comparison | book beta | engine beta | absolute beta difference |
|---:|---|---|---:|---:|---:|
| 500 | PASS | BOOK_DIFFERENCE | 0.853401 | 0.8534289109891589 | 2.791098915888579e-05 |
| 1500 | PASS | BOOK_DIFFERENCE | 0.566844 | 0.5669826998141048 | 0.00013869981410474796 |

Possible sources of book differences include rounded or undocumented input settings;
the current evidence does not identify a unique cause. See temperature/alpha sensitivities in JSON.
Matching an independent implementation of the same model does not establish experimental accuracy.
