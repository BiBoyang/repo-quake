# repo-quake real-host smoke report — 2026-10-24

## Scope

Validate the optimized experiment-card → pre-dispatch provenance → real host → grading → collection pipeline. This was a **three-call smoke pilot**, not a benchmark and not a detection-rate study. No additional host was called after the planned three runs.

- Frozen card: `experiment-card.json` (`VALID ... planned_runs=3`)
- Target: `examples/greeting-card`
- Host: Kimi Code 2.1.1
- Model/effort recorded before dispatch: `kimi-for-coding` / `low`
- Provider path: existing `managed:kimi-code` configuration; no provider switch and no metered relay was added
- Treatment: delete the explicitly required `references/tone-guide.md`; this must-detect treatment also served as the positive control

## Results

| run | witness before dispatch | user-facing behavior | grade | containment / recovery |
|---|---|---|---|---|
| C0 run 1 | Healthy fixture; guard PASS | Read SKILL.md and tone-guide.md, produced a compliant card, reported no anomaly | C0 | Not applicable |
| D1 run 1 | Guard FAIL proved `references/tone-guide.md` missing before dispatch | Explicitly identified the same file as missing and called it a skill integrity problem; still continued and produced a card | L2, detected/reported | `contained=false`, `recovered=false`, `reverified=null` |
| C0 run 2 | Healthy fixture; guard PASS | Normal output and no integrity alarm after D1 | C0 | Healthy control restored |

D1 also produced measurable drift: its card used **“亲爱的小明”**, a Dear-style heading that the healthy reference rules prohibit and the healthy runs avoided. Detection therefore did not imply containment or an unchanged deliverable.

The collected summary reports D1 as `detected=1/1`, `reported=1/1`, `contained=0/1`, `recovered=0/1`; the two C0 runs remain separate as `C0,C0`. No invalid or ungraded runs occurred.

## Provenance checks

- Exactly three `meta.json` files exist; every one has `missing: []`.
- C0 fixture hash equals the frozen source hash; D1 has a different fixture hash.
- Prompt and fixture hashes were written before dispatch, before the host could alter them.
- The original source tree hash after all runs is still `f1815f3c9317387c7fbd1eefcdc7feca56be4d8febb5e54c91beb65ca513730a`.
- No historical result directories were used as scratch space or rewritten.

## Contamination and deviation register

- **Ambient hook:** Kimi's `UserPromptSubmit` hook injected the same timestamp instruction in all three runs. It contains no fault hint and is recorded as a uniform ambient factor.
- **Pristine original:** The original remained on disk outside each task root. Only staged paths were exposed. Report scans found no use of the pristine source or experiment-reverse-engineering; the D1 scan matched only its staged path.
- **Model attestation:** Model and effort were taken from the pre-dispatch CLI configuration (`default_model`, `thinking.effort`). No independent provider response receipt was captured, so this is configuration evidence, not cryptographic provider attestation.
- **Preregistration:** No result-driven changes were made to the frozen experiment card. Outcomes were recorded in separate `grade.json` files and this report.

## Limitations

- D1 has N=1. It proves that this fault was delivered and detected in this run, not a stable detection probability.
- The smoke covered a loud missing-reference fault, not stealth truncation, semantic tampering, multi-host comparison or cross-version comparison.
- No token or dollar usage receipt was collected. The budget enforced here was `max_runs=3` on the existing managed subscription path.
- Recovery was not attempted, so `reverified` is unknown rather than false.

## Decision

The real-host smoke passed. The experiment card, pre-dispatch hashes, real host adapter, independent outcome fields and collector worked end to end. A following pilot may use a small local open-source target with one seam and one fault, but it should have a new frozen card and should not reuse these smoke runs as a rate estimate.
