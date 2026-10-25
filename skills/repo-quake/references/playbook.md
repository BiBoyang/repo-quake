# The eight-step playbook (expanded)

## Step 0 — Freeze the experiment card

Use `examples/experiment-card.json` and `scripts/validate_card.py` to freeze the
claim, task, host/model/effort, arms, controls, witness, rubric, invalid rules,
budget, isolation and ethics before the first paid run. The card's planned run count
must fit its budget. Store the validated card beside the results and treat later
changes as disclosed deviations or a new experiment.

## Step 1 — Select the target

Read source before writing any fault. You are looking for **trust seams** —
places where the code assumes something it never verifies:

- completeness assumptions (parsers that silently fall back to defaults)
- single-attempt success assumptions (no retry, no tombstone, no user signal)
- shared-state healing (setup routines that "repair" a directory at startup)
- assertions bound to a field's current name rather than its responsibility

Selection criteria for a good first target: you can run it locally; it accepts
a local/mock endpoint or a fixture file; its failure surface is user-visible or
log-visible (so detection is decidable); and upstream is alive enough to take an
issue. See `target-catalog.md`.

Deliverable of this step: a one-paragraph target brief + a list of candidate
seams, each with the file:line evidence.

## Step 2 — Design the fault menu

Rules:

- Every fault simulates a **real accident class** (truncated download, lost
  file in sync, half-written disk, config drift) — not an adversarial fantasy.
- Every fault gets a **path-reachability pre-check**: trace the task's execution
  path and confirm it must read/execute the wounded artifact. Phase 2 lesson:
  four wounds scored 0/64 because one was redundant (self-describing filenames),
  one conditional, one future-tense, one a weak "see X" reference. Redundancy
  rescues hosts; redundancy in the target is data, not an excuse.
- Vary wound position, not just wound size. Detection is not dose-response:
  60% main-file cut that blocks the path detected 8/8; an 85% cut that only
  removed the tail index detected 1/3.
- Include F0 (healthy) as the control row and at least one must-detect fault as
  the positive control.

## Step 3 — Deterministic injection

- Faults are parameters (URL query > header > control plane), switchable at
  runtime, with **once semantics built into the fault source**: "only the next
  request matching X carries the fault". External set→wait→reset windows are
  always wider than the race — the client's retry is faster than your polling,
  and auxiliary requests (title generation, token counting) will steal the
  fault unless once has match/avoid substrings.
- Keep protocol invariants intact when building the wound: you are testing
  "truncation", not "self-contradictory data" — the latter triggers a
  different error path.
- The mock's dialect must match the real API to the event name. Verify against
  captured real traffic or source, never intuition.
- Preflight the fault's semantic identity as well as its transport: error type
  and code, required constructor options, injection point, timing and occurrence
  count. A side effect without the intended error semantics is a different cell.

## Step 4 — Witness layer

Two components, both deterministic and zero-token:

1. **Mechanical checker** (guard): hard checks (missing file, dead reference,
   empty required field) vs warnings (truncation signatures). State its blind
   spots in writing (e.g. skill-guard cannot see a stealth cut whose tail looks
   complete; template files ending in comments look normal).
2. **Delivery proof**: per-request log of bytes actually written, full event
   sequence, whether the terminator was sent, how the stream closed. Symmetric
   request-side capture. This is what separates "no reaction" from "fault never
   arrived". Include the fault type/code and required parameters, not only the
   resulting click or write; an effect alone does not prove which fault arrived.

Calibrate the witness against fixtures including a deliberately bad sample —
the witness itself needs tests (a witness with false positives drowns real
wounds: skill-guard once flagged 9 errors on a pristine target because it could
not tell real references from illustrative examples in prose).

**Hash manifest.** Version pinning says which release you ran; content hashing
says which bytes. Record sha256 for the target binary/image, every fixture,
every prompt, and every calibration file — per cell where cheap (prompt sha256
per item is one line of code and kills a whole class of "which text did we
actually send" disputes).

## Step 5 — Baseline, negative control, positive control

In order, all before the first fault cell:

- Healthy baseline: the task completes, artifacts look right.
- Negative control (C0): untouched copy through the whole pipeline → no
  witness alert, no host report. Proves the pipeline has no residue.
- Positive control: one fault that MUST be caught by an existing known path
  (e.g. think-only truncation that forces a retry; a syntax-breaking cut).
  If the positive control is silent, the injection chain is broken and every
  negative result in the matrix is void.

## Step 6 — Run the matrix

- Cells = hosts × faults × N. State the run budget before starting; stop and
  report when exhausted.
- Exclusion counting: every report carries `EXCLUDED: N run(s)` for runs that
  left the denominator (env failure, quota). Never silent.
- Stratify aggregates: an aggregate pass-rate gain can hide a per-model
  regression.
- Keep witness artifacts, dispatch artifacts, and the host-visible staging tree
  in separate roots; hash-name everything the host can see.
- Per-cell meta carries: target version, host version, model, effort level,
  prompt sha256, fixture sha256, witness verdict, timestamp. Hashes are captured
  before dispatch so they describe the bytes actually delivered, not any host-side
  edits. A cell you cannot re-key from its meta is a cell you cannot defend.

## Step 7 — Grade and appeal

- L0–L3 per run; drift vs baseline; perceived-but-unreported in notes.
- Invalid and ungraded runs have separate counts and no metric denominator. New
  runs may record reported/contained/recovered/reverified as independent optional
  booleans; each gets its own denominator and unknown count, never backfilled.
- Grade from primary artifacts (transcript, deliverable), not from the host's
  self-report alone.
- Do not let the grader strengthen the frozen rubric. If an extra assertion is
  wrong, preserve the initial output and adjudicate separately. Fixture repair
  uses a new frozen card; grader repair does not automatically mean a new run.
  See `failure-attribution.md`.
- **Appeal step, mandatory**: pick the single most striking conclusion and
  re-verify its entire evidence chain — mock bytes, witness logs, grading
  notes. Both published near-misses in the series (a false-negative codex cell,
  a false "no artifacts written" issue) died at exactly this step.
- Preserve wrong conclusions verbatim with the retraction attached; the
  overturn process is worth more than the conclusion.

## Step 8 — Close the loop

See `reporting.md`. The short version: minimal repro, environment block,
expected-vs-actual, inline evidence that does not require repo access; and the
courage to post "this was a false report, please close" when wrong.

### Archive without mutating the evidence

Before committing a run directory, audit it:

```bash
python3 skills/repo-quake/scripts/audit_artifacts.py <experiment-directory>
```

The audit rejects symlinks by file type (an ignore rule for `node_modules/` does
not cover a same-named symlink), runtime-only directories, browser/PID files,
and high-confidence credential shapes (first 4 MiB per file). It never deletes anything. Keep raw logs
byte-for-byte; if their natural EOF blank lines or progress-output trailing
spaces trip `git diff --check`, use a scoped `.gitattributes` whitespace rule
instead of normalizing the evidence.
