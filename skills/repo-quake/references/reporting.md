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
