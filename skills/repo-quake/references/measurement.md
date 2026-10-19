# Measurement discipline

## Counting

- Single runs are anecdotes. Report x/N per cell, always with N visible.
- Small N honesty: with N=3..8 you can claim three tiers — stable detection,
  probabilistic, stable miss — not a probability estimate. Say so in every
  writeup.
- Gate on the confidence-interval bound, not the point estimate. One-sided
  Wilson (z=1.645): a 9/10 point estimate of 0.9 has a lower bound near 0.65;
  small samples do not get to claim compliance. Halving the error bar costs
  4x the samples.
- pass@k and pass^k tell opposite stories (p=0.75: pass@10 ≈ 1.0, pass^10 ≈
  0.056). Estimate with unbiased combinatorial estimators
  (1 - C(n-c,k)/C(n,k) and C(c,k)/C(n,k)); the plug-in forms are biased.
- Aggregates hide regressions: stratify by host, model, scenario. An 70%→80%
  aggregate gain once hid a per-model regression.
- EXCLUDED counting: any run leaving the denominator is a printed line, never
  silence.

## Fail vs error

Declare the expected failure shape before the run (exit code, terminal event,
error class). A run that dies in the declared way is a data point — a detector
firing, or a client correctly rejecting the wound. Any other death is an error:
quota, TLS, missing binary, installer failure. Errors never enter the
denominator, never get averaged, and are never rewritten as "0/N detected".
Print them as their own line and count them.

The test is attribution, not outcome: did the run die before the target had a
chance to act on the wound (setup, install, transport, quota), or while acting
on it? Before → error. While → the target's behavior, which is your data —
including flakiness, which is variance to report, not an error to exclude.
An install step is part of the experiment, not plumbing around it: "the plugin
would not install" is a finding with the installer's output tail attached, not
an accident to apologize for.

## Retries vs trials

Two operations that both look like "run it again":

- **retries** — engineering convenience: rerun a failed attempt, keep the best.
  Legitimate for a gate whose job is "is this still green", never for a
  measurement.
- **trials** — measurement: n independent attempts, every one counted.

A measured rate must have zero retry intervention, and the two are mutually
exclusive in the same run (trials > 1 ignores retries). If you retried, your
x/N is not a probability: print the retry count next to the rate, or stop
calling it a rate. The same rule kills "we ran it five times and it passed
three" when two of the five were reruns of the same attempt.

## Independence assumptions

i.i.d. is a modeling assumption, not a fact: rate limits, time-of-day, and
model-state drift violate it (measured in the wild: 6-point swings from
resource config alone, exceeding leaderboard gaps). Record machine, load, and
date in every report; distrust leaderboard differences under 3 points until
eval configs are public and aligned.

## Controls

- F0 healthy row must pass before fault cells run.
- Negative control after any fault series: behavior returns to baseline.
- Positive control fine-grained to the protocol event name: one fault that an
  existing known detector MUST catch. Its silence voids every negative result.
- Calibration set hygiene (when an LLM judge is involved): TPR and TNR
  separately (total agreement hides minority-class blindness); enough fail
  samples (200+ total, 50-100 fails); organic failures from weaker models,
  never strong-model-synthesized defects (OOD); calibration and validation
  sets disjoint; recalibrate on every model swap — calibration sets expire.
- Judge format: analysis first, verdict last, enforced by schema
  (checks[].notes required), not by prompt convention. One judge per
  dimension. Unknown is a legal answer; a high unknown rate indicts the
  rubric, not the judge.


## Pre-registration and deviation log

Before the first fault cell runs, freeze a `prereg.json` into the results dir:

- cell definitions (hosts x faults x N), the grading rules, and the selection
  rule for every fitted parameter (thresholds, cut points, prompt text)
- the total run budget

After the series, append a deviation log: every place the executed experiment
departed from the prereg, one line each, with the reason. Discovered mid-series
that a rule was wrong? Fix it forward and log the change — never retro-edit the
prereg. Pattern credit: benchmark-submission practice (JevBench) — an earlier
draft that had adopted a value because the check half preferred it was reverted
to the pre-registered dev-half pick, and the deviation was disclosed item by
item. Selection rules age better than results; a logged deviation is data, a
silent one is contamination.

### A budget that can refuse

A pre-registered budget that cannot stop the run is decoration. Estimate the
plan before spending (requests × tokens × N, wall-clock × cells), print the
estimate, and refuse to start when it exceeds the budget. Mid-series overrun
stops issuing new work and marks the series truncated — it never "adjusts" the
budget after the fact. A dry run that prints the plan and spends nothing is the
cheapest way to keep the estimate honest.

## Grading pitfalls

- Grade from primary artifacts, not self-report.
- Keyword scanners false-positive on the host's own vocabulary — a host whose
  reasoning stream frequently says "truncated" (because its file reads get
  truncated) poisons naive DETECT matching. Read the originals.
- "Perceived-but-unreported" is a first-class outcome: the wound appeared in
  the host's reasoning and never reached the deliverable. Record it
  separately; do not round it up to detection or down to L0.
- The most striking conclusion is a suspect: before publishing, replay its
  full evidence chain (mock bytes → witness log → grading note). Two published
  near-misses died at exactly this step; keep wrong conclusions verbatim with
  the retraction attached.
