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
