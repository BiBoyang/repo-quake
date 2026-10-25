# Reporting and the upstream loop

The point of the methodology is not the matrix; it is the bug report an
upstream maintainer can verify in five minutes.

## Issue quality

- Minimal repro: the fewest commands that show the behavior, self-contained.
- Environment block: versions, OS, date — pinned, not "latest".
- Expected vs actual, in one sentence each.
- Inline evidence: paste the command output; do not make the maintainer clone
  anything to believe you.
- Evidence quality does not guarantee conclusion correctness — it guarantees
  correction speed. That is still worth it.

## The public repro is a deliverable

A maintainer receives the issue body, not your harness. Extract the exact code
block you will publish and run it in a clean, minimal environment. Paste its
actual output beside expected and actual behavior. Keep the issue self-contained:
do not cite an evidence repository that is not public yet, and distinguish npm
runtime evidence from main-source inspection. When linking source, record main
HEAD and the file's last-change commit separately rather than calling one the
other.

## Publication writes are uncertain commits

A timeout may mean the write never arrived, or that it committed and the response
was lost. Do not guess and do not blind-retry:

1. Query a unique dedupe key (for an issue, its exact title) before creating.
2. Retry only within a bounded budget, and only after the duplicate check says
   the operation is still needed. An alternate API is justified after the same
   dedupe check, not as a way to create a second copy.
3. Read back title, body, labels, state and head. A create response is not proof
   that optional fields such as labels took effect.
4. Permission denial is a boundary, not a transient error. Record the maintainer
   action needed; never switch APIs to bypass it.
5. After pushing, independently compare local and remote SHA. If the read-back
   fails, the push is unverified until a separate read succeeds.

## Upstream contribution preflight

Read `CONTRIBUTING`, issue/PR templates and repository agent instructions before
implementing the fix. Check whether a fix PR needs an existing issue, changeset,
docs, a particular runtime, benchmark A/B, fresh-context review, or a maintainer
label. Branch and benchmark from the authoritative `upstream/main`, not a possibly
stale fork `origin/main`. A reviewer that did not run tests is not a replacement
for the author's executed verification; keep the two evidence sets separate.

## Fix suggestions are hypotheses

An issue's proposed fix is a sketch written before reading the fix site. When
the PR reveals the sketch wrong (e.g. the graceful-kill ladder you suggested
already exists, and the real gap is elsewhere), the PR description carries an
explicit "Correction vs. the issue sketch" section: what was already
implemented, what the real gap is. Maintainers see an honest investigation
trail, not a flip-flop.

## Retraction

A false report corrected publicly in the same venue costs one embarrassment
and buys a credibility trail: your history speaks for you the next time you
file. Write the correction more carefully than the original — name the exact
commands that misled you (e.g. "the mtime I stat'ed was iteration-1's; the
rerun wrote iteration-2").

## Failure modes this catalog has actually produced

- Timeout kills adapter → artifacts vanish → framework synthesizes minimal
  results (skill-up #263/#265)
- Symlinked source → zero files installed → silent success (skill-up #253/#257)
- Merge-state CI vs bare-branch local → "platform difference" misdiagnosis
  (skill-up #265 CI)
- Silent truncation acceptance in main agent path (kimi-code #4012)
- Zero-detection examiner matrix → integrity checks moved into the CLI layer
  (skill-up #280/#281)
- Validator blind spots confirmed at code level, upstreamed
  (anthropics/skills#1949, microsoft/eval-guide#16)

## Disclosure file

Every experiment phase ships a disclosure next to its report — fill
`disclosure-template.md`. Minimum contents: what was accessed (and what was
never touched), which numbers are estimates vs official measurements, the hash
manifest (target version, fixtures, prompts, calibration), the deviation log,
the contamination register. The disclosure is what lets a reader trust the
report without rerunning it.

## Freezing the behavior after you file

The issue is not the end of the loop; the case is. Once the report is out, turn
the minimal repro into a pinned regression case that runs on every new target
version, and freeze the CURRENT behavior in it — including the defect level you
just described. Header the case with the level it pins: `F4 length truncation:
detected but no user-facing sentence — L1 status quo, not an endorsement`.

Pinning the defect rather than the fix makes the case red in both directions —
but only if you pin both halves. The detection assertion catches regression
(L1 → L0: the exit code and terminal event stop matching). For improvement
(L1 → L2: a user-visible notice appears) you need a negative assertion on what
the fix would add, e.g. `output_not_contains: <the notice an L2 fix prints>`.
Without that half the case catches regression only, and on the day upstream
fixes it the gate stays green while the pinned defect quietly becomes stale
documentation. A green run then means "same as the version we investigated",
never "upstream approves". Behavior fixation is not behavior endorsement — write
that inside the case, because the next reader reads green as praise.

Pin every spec in the case (`@x.y.z` or `#sha`). An unpinned case measures
"latest", and the red it produces when upstream publishes is your own fault.
After a version bump, re-run the whole pack once and re-baseline by hand; a gate
that re-baselines itself measures nothing.

## When a finding becomes a gate

A finding has two lives: one report, then maybe a gate that runs forever. The
second life has its own failure mode — alarms stop being read long before they
stop being printed.

- Warn only on change versus a known baseline, and only when it increases. A
  signal that fires every run is not a signal; it is wallpaper, and it will
  still be wallpaper on the day it matters.
- Never put a known-flaky case into the baseline. It hides the next flaky one;
  keep it visible as its own informational line instead.
- Treat a target version change as information, not a warning: the first full
  run after an upgrade is exactly when you want the eye, and a standing yellow
  for "version differs" spends it before you get there.
- Aggregate identical error signatures (error code + top application frame).
  The same signature twice across cells is not two case failures; it is one
  shared-state accident — concurrency, disk, a healing routine. Route it to the
  target, not to the case.
- A case that only passes on retry is evidence about the target's reliability
  even when its assertions are green. Report it; do not let the retry wash it.

Pattern credit: this section, the fail-vs-error split, the retries/trials
distinction and the refusable budget were generalized from `dsh-eval-harness`, a
DSH plugin regression gate that had to encode the same calls in code.

## Posting gate

No public artifact (issue, PR, blog post, repo push, disclosure-file example)
goes out until every box is checked:

- [ ] the upstream loop is opened FIRST for any third-party finding — the issue
      is filed before the public writeup exists, and the writeup links the
      issue, never the reverse
- [ ] every number re-checked against its primary source (logs, transcripts,
      mock bytes) — nothing added beyond those sources
- [ ] the most striking conclusion re-verified end to end
- [ ] sample sizes and caveats stated wherever a number appears
- [ ] contamination register reviewed; affected cells annotated, not hidden
- [ ] exact public repro code extracted and run in a clean environment
- [ ] public writes deduped and read back; permission boundaries recorded
- [ ] local and remote revision verified, and upstream base provenance checked

Learned the hard way, both directions: a benchmark submission that refused to
open its issue before the repo was public (JevBench practice), and an unfiled
third-party spike report that briefly escaped into a public repo here and had
to be force-pushed out (2026-10-15). The gate is cheap; the retraction is not.

## What not to do

- Do not file from a single run.
- Do not file a negative claim ("X does not detect Y") without delivery proof.
- Do not let the most striking number in your report be the one you did not
  re-verify.
- Do not silently update a wrong claim in-place; annotate the correction so
  the trail stays readable.
- Do not retry a public write before dedupe, and do not treat a timeout as proof
  of either success or failure.
- Do not call fork `origin/main` the upstream baseline without checking its SHA.
