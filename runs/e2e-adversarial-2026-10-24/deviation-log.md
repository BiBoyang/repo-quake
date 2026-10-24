# Deviation log

## D arm exceeded the preregistered run budget

- The frozen experiment card allowed `max_runs=8`: H×2, A×2, B×2, C×2.
- After those eight runs completed, two additional runs (D1/D2, corrupted cache entry) were executed, bringing the actual total to 10.
- This was not a provider overrun and did not involve real model calls, but it was still a budget/pre-registration deviation.
- The card was not edited after the fact. D is labeled **exploratory only** and is not used as evidence for the original confirmatory claim.
- H/A/B/C remain within the original budget and are reported separately. No further runs were started.
- Future additional arms must receive a new frozen card before dispatch, or the run must stop at the original budget.
