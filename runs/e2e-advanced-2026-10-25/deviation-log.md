# Deviation log

## V2 initial attempt used an empty cache directory

The first V2 attempt used `cache-V2`, which contained no recording. Its `no-entry` result cannot answer whether a changed control invalidates an existing replay. That attempt is marked **invalid setup**, not product evidence.

The corrected V2 run uses `cache-H`, which contains the healthy V1 recordings. Logs for the invalid attempt are preserved as `V2-invalid-setup.*` and are excluded from the conclusion.

## U1 was deferred to respect the run budget

The original card allowed eight executions and included U1. The corrected V2 attempt adds one extra run, so U1 is deferred to a separate future card rather than silently exceeding the budget. U1 is not claimed in this report.

Final execution count, including the invalid setup attempt: **8** (H×3, V2-invalid-setup×1, V2-corrected×1, V3×1, N×2).

## V3 initial attempt reused a cache overwritten by V2

The first V3 attempt reused `cache-H` after V2 had saved a new `Finish Upgrade v2` recording. That no longer represents the V1 baseline required for an end-state mismatch test, so the attempt is **invalid setup**, not a product failure.

A fresh `cache-V3` is being created solely from V1 before the corrected V3 run. The invalid attempt is preserved as `V3-invalid-setup.*` and excluded from the conclusion.

## N and U1 are deferred

Two setup corrections would otherwise exceed `max_runs=8`. N and U1 are deferred to a separate future experiment. Final execution count, including both invalid setup attempts: **8** (H×3, invalid-V2×1, corrected-V2×1, invalid-V3×1, V3-baseline×1, corrected-V3×1).
