# Disclosure template

Fill one of these per experiment phase, next to the phase report. Delete the
guidance lines (italic) as you go. Sections marked **[benchmark]** apply only to
leaderboard/benchmark submissions; everything else is universal.

---

# DISCLOSURE — <experiment / entry name> (<date>)

*One sentence: what was measured, against which target and version.*

**Estimate vs official.** *Label every number as one of: (a) direct observation
from our own runs; (b) local estimate from a re-implementation; (c) official /
organizer-measured. If (b) disagrees with (c) anywhere, (c) is right and the
estimate moves. State that rule here.*

## 1. Access and contact

- What the experiment touched: *fixtures, public artifacts, local builds.*
- What it never touched: *sealed/private sets, production endpoints, third-party
  infra. State the absence explicitly — "no access, never read" is a claim that
  must be made, not assumed.*
- Isolation level used, and why it was sufficient for the worst inducible
  behavior.

## 2. Hash manifest

*Content addressing for everything the conclusions depend on:*

| artifact | sha256 / revision | note |
|---|---|---|
| target binary / image / source pin | | |
| fixtures / mutated copies recipe | | |
| prompts | | *per-item sha256 where cheap* |
| calibration / config files | | |
| witness / checker version | | |

## 3. Pre-registration and deviations

- Link the prereg (cell definitions, grading rules, fitted-parameter selection
  rules, budget), frozen before the first fault cell.
- Deviation log: one line per departure from the prereg, with the reason.
  *A logged deviation is data; a silent one is contamination.*
- Correction lineage, when present: invalid setup -> new frozen card with its own
  budget; grader error -> preserved initial output plus separate adjudication.
  Never erase either history.

## 4. Integrity statements

*Answer each with a sentence, not a checkmark:*

1. No item/cell was selected, dropped, or re-labeled after grading began —
   or it is listed in the deviation log.
2. Environment failures were excluded and counted, never silently dropped.
3. Contamination register: *hooks, ambient configs, visible-path leaks, memory
   effects — each with affected cells and the handling.*
4. Witness blind spots known at time of writing: *e.g. "stealth cuts with clean
   tails pass the guard".*

## 5. [benchmark] Sealed-set and training statements

- Sealed items accessed? *Expected answer: no. If any indirect statistic was
  used, name it.*
- Training on open items? *If yes: exactly which items, for what (calibration /
  model choice / fitting), with the split and the pre-registered rule.*
- Relation to other entries/rows from the same org: *shared weights, prompts,
  calibration, code paths — or none.*

## 6. [benchmark] Prior work

*What family the method belongs to, nearest neighbors, what is actually new —
stated as differences, not novelty claims. What was NOT used (code, prompts,
calibration values), said out loud.*

## 7. Posting gate (all boxes before anything goes public)

- [ ] Upstream loop opened first for every third-party finding (issue link here)
- [ ] Every number re-checked against its primary source
- [ ] Most striking conclusion re-verified end to end
- [ ] Sample sizes and caveats next to every number
- [ ] Contamination register reviewed; affected cells annotated, not hidden
- [ ] Repository/artifacts public before the issue or writeup that cites them
- [ ] Exact public repro extracted and run in a clean environment
- [ ] Public writes deduped and read back; permission limits and remote SHA recorded
