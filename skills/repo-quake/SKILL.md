---
name: repo-quake
description: "Fault-injection + measurement-discipline methodology for attacking open-source projects / 对开源项目做故障注入与评测以产出真实 bug. Use when the user asks to: 爆破/评测/体检 an open-source project; find real bugs in a CLI/agent/framework via controlled fault injection; design a wound matrix, mock provider, or witness layer for some target; turn eval results into upstream issues/PRs. For SKILL.md-layer integrity experiments specifically, use the bundled skill-quake skill (`skills/skill-quake/`)."
---

# repo-quake

Generalized fault-injection methodology for one question: **pick an open-source
project, find where it silently breaks, and prove it with evidence an upstream
maintainer cannot dismiss.** Born from a 7-part eval series and three phases of
live experiments (see `docs/phase*-report.md`). The bundled `skill-quake` skill
is the file/skill-layer specialization; this skill is the umbrella method.

## The one-screen model

Detection of any wound is a product of three factors (phase-1p unified formula):

**detection = reaches-the-eyes (harness supplies) × willing-to-report (model
supplies) × blocks-the-path (task structure supplies)**

Each factor has killed detection independently in live runs: hosts that never
opened the wounded file (E3 kimi 7/8), hosts that noticed in their reasoning but
never reported (perceived-but-unreported, E3 cells), and wounds that were simply
not on the task's path (0/64 in phase 2). Design your experiment so each factor
is either forced, measured, or honestly recorded as a confound.

The second law: **every piece of your evidence needs its own witness.** Faults
need delivery proof; detections need positive controls; negative conclusions
need byte-level evidence that the signal was actually sent; and your most
striking conclusion is a suspect, not a finding, until it survives review.

## Methodology invariants (never violate)

Inherit all eight from the skill-quake specialization, generalized:

1. **The experimenter never hosts a run.** Fresh zero-context hosts only.
2. **Neutral prompts only.** No hint that anything might be wrong. The final
   "report anomalies honestly" sentence appears in baseline runs too.
3. **Mutate copies, never the source.**
4. **Witness before and after.** A deterministic checker runs on every mutated
   copy; its output lives next to the run's report — and outside the host's reach.
5. **Single runs are anecdotes.** Report x/N per cell. N=1 proves existence only.
6. **Negative control.** Rerun the untouched baseline after any fault series.
   Optionally pair with a positive control (a must-detect fault) to prove the
   detection channel is alive — make the positive control as fine-grained as the
   protocol event name, not just "some obvious breakage".
7. **Opaque paths, invisible artifacts.** No host-visible path encodes the fault
   type; witness/prompt/meta files live in a separate tree the host cannot read.
   (Both halves of this rule were learned from hosts that reverse-engineered the
   experiment — one from path names, one from a guard.json in the staging tree.)
8. **No pristine original within reach.** A detection aided by diffing against an
   undamaged copy on the same machine does not count.

Plus the generalization layer:

9. **Isolation is sized by the worst behavior the task can induce, not by the
   task's intent.** An agent under test that "should only read files" once
   installed a crontab entry on the experimenter's real machine. Fake HOME,
   sandboxed runtime, or container — default to the strongest you can afford.
10. **Environment failures are not data.** A run blocked by scaffolding
    (permissions, quota, network) is archived for audit and excluded from
    detection rates. Mark absent cells N/A rather than inventing numbers.
11. **Pin and record versions.** Target version, host version, model, effort
    level, and test date go in every cell's meta. An update prompt that replaces
    the pinned binary mid-matrix is a real observed accident.

## The eight-step playbook

Full per-step checklists: `references/playbook.md`.

1. **Select the target.** Read source for trust seams: where completeness is
   assumed, where single-attempt success is assumed, where shared state is
   healed, where assertions bind to fields instead of responsibilities.
   `references/target-catalog.md` lists ten seam patterns with priors.
2. **Design the fault menu.** Every fault simulates a real accident class, and
   every fault gets a **path-reachability pre-check**: will the task's execution
   path necessarily read/execute the wounded file? (Phase 2: four wounds, 0/64
   detection — all four were redundant/future/optional paths. Designing a
   blocking wound is harder than it looks.)
3. **Build deterministic injection.** Faults as parameters; once-semantics
   built INTO the fault source (external set-wait-reset windows are always
   wider than the race). Never depend on real network weather.
4. **Build the witness layer.** Deterministic mechanical checker (zero-token)
   + delivery proof (byte-level log of what was actually sent). The witness
   states its own blind spots honestly; calibrate it against fixtures.
5. **Baseline first.** Healthy run → negative control → positive control.
   All three pass before any fault cell runs.
6. **Run the matrix.** x/N per cell; exclusion counting (the denominator never
   shrinks silently); stratify aggregates by host/model/scenario.
7. **Grade and appeal.** L0–L3 detection levels; drift vs baseline; record
   "perceived-but-unreported" separately. Before publishing, treat the most
   striking conclusion as a suspect: re-verify its evidence chain end to end.
8. **Close the loop upstream.** Minimal repro + inline evidence; fix-suggestion
   sketches are hypotheses, not promises — correct them explicitly in the PR;
   if you were wrong, retract publicly in the same venue.
   `references/reporting.md`.

## Attack surfaces and their tooling

| surface | core weapon | mature tooling |
|---|---|---|
| files / supply chain | integrity fault injection; witness = mechanical guard | `skills/skill-quake` + `bin/skill-guard` |
| protocol / stream | mock provider trilogy: protocol endpoints + fault-as-parameter + delivery proof | `references/fault-catalog.md` §stream |
| behavior / contrast | with/without control, in-domain smuggling, adversarial pressure | `references/fault-catalog.md` §behavior |
| concurrency / timing | real re-runs (replay physically erases races), retry history, stderr tails | `references/fault-catalog.md` §concurrency |
| env / config | "which code did CI actually test", worst-induced-behavior isolation | `references/fault-catalog.md` §env |

## Grading

Detection levels: **L0** no sign / **L1** signal exists but misattributed or
user-invisible / **L2** explicitly names the right file AND the right damage /
**L3** names it and refuses or recovers. Record drift vs baseline separately,
and always record **perceived-but-unreported** (evidence in the run's reasoning
trace, absent from the deliverable) — it is operationally the most dangerous
form. Grading is judgment; that is why it lives here and not in the witness.

## Anti-self-deception checklist (the discipline that pays)

- A negative conclusion ("the tool didn't notice") must ship with positive
  delivery proof at protocol-event-name granularity. "No reaction" and "fault
  never arrived" are separated by bytes you must show.
- A mock's authority is inversely proportional to the tested client's
  strictness: the more tolerant the client, the deeper your dialect errors hide.
- `strings` absence ≠ code absence (inlined matches never reach rodata; search
  for handler-evidence strings, not event names).
- Request count is not retry evidence (auxiliary requests exist).
- Merge-clean ≠ semantically compatible; CI red + local green → first ask
  "which code did CI actually build".
- Your grading keywords can false-positive on the host's own vocabulary
  (a CLI whose reasoning stream says "truncated" a lot). Calibrate the judge
  against fixtures like anything else.

## References

- `references/playbook.md` — the eight steps, expanded with checklists
- `references/fault-catalog.md` — five attack surfaces: standard faults, witness
  design, cut-point rules, observed lessons
- `references/target-catalog.md` — ten high-value trust seams with priors
- `references/measurement.md` — statistics, controls, judge calibration,
  pre-registration and deviation logs
- `references/reporting.md` — upstream issues, PRs, public retraction,
  disclosure files, the posting gate
- `references/disclosure-template.md` — per-phase disclosure file to fill;
  `examples/disclosure-phase3-metacodes.md` is a filled instance
- Bundled specialization: `skills/skill-quake/` — the file/skill-layer specialization with
  ready-made mutation scripts and host adapters
