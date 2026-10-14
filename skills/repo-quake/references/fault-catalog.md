# Fault catalog by attack surface

## §files — file / supply-chain layer

Standard faults (from skill-quake's fault menu):

| fault | simulates | cut-point rule |
|---|---|---|
| truncate-main (60% / 85%) | truncated download/sync | cut at a whole line/sentence boundary, no marker; 60% should remove required steps, 85% only tail matter |
| delete-ref | file lost in copy | pick a file the main text explicitly references |
| truncate-attachment | half-written disk | cut at a dangling heading for the loud variant; at a clean boundary for the stealth variant |
| blank-frontmatter | generation/edit accident | empty the metadata fields a loader depends on |

Witness: mechanical guard (existence, parse, dead references, truncation
signatures). Known blind spot: stealth cuts with clean tails pass; template
files ending in comments look normal. Defense against tampering needs a
known-good hash manifest (v2 territory).

Loader layer is part of this surface: empty-metadata probes show loaders either
silently drop the entry or degrade it to a zombie (directory-name fallback).
Both are silent; both are reportable.

For SKILL.md targets use `skills/skill-quake` (ready-made mutate.sh, host
adapters, grading rubric).

## §stream — protocol / streaming layer

Standard faults (truncation-detection-benchmark lineage):

| fault | protocol shape |
|---|---|
| F0 | healthy full stream (control row) |
| F1 | clean mid-stream TCP FIN, no terminator |
| F2 | all content sent, terminator event missing, stream closes normally |
| F3 | half an SSE event (invalid JSON) then FIN |
| F4 | finish_reason=length / max_tokens termination |
| F5 | think-only: reasoning burns the budget, zero content (doubles as positive control against clients with empty-response retry) |

Tooling: a single-file mock provider (~400 lines, zero deps) with three layers —
protocol endpoints hand-written to real API shape; fault-as-parameter with
built-in once semantics; byte-level delivery proof per request.

Lessons burned in:
- once must be internal, with match/avoid substrings to pin the main request
  (auxiliary requests steal faults)
- protocol invariants stay intact inside the wound (done-event text == delta
  concatenation)
- dialect must match the real API to the event name (response.incomplete is a
  distinct event, not a status field on response.completed)
- client tolerance hides your dialect errors — the stricter the client, the
  more honest your mock must be

Typical findings to hunt: detection exists but is never translated to a
user-visible sentence; deterministic faults share one retry policy with
transient faults; transcripts keep no tombstone (failed attempt and retry
attempt serialize identically).

## §behavior — behavior / contrast layer

Standard designs:

- **with/without control**: the "without" must be enforced, not defaulted —
  host skill auto-discovery, user-level hooks, global AGENTS.md are all
  contamination. Pin every ambient knob explicitly.
- **in-domain smuggling**: the main request sits inside the target's trigger
  domain and smuggles one item it declares "not for". Pure out-of-domain
  requests measure the bare model and prove nothing.
- **adversarial pressure**: "production is on fire, skip the questions" is the
  only effective developer of red-line rules.
- **trigger negatives**: eval sets must include cases that should NOT trigger;
  teams that only test positives optimize into always-on agents.

Presence verification before any full run: the intervention actually entered
the system under test — direct evidence (installed files, load logs), never
exit codes. Assertions can pass on an experiment that never happened
(symlinked skill dirs → zero files selected → three full rounds of noise
dressed as signal).

## §concurrency — concurrency / timing layer

Weapon: real re-runs. Replay freezes tool observations and flattens timing;
TOCTOU physically does not exist in a replay. Real re-runs are expensive and
flaky but are the only way to see races.

Prerequisites without which crashes are wasted: concurrent + isolated
execution; retry history recorded; stderr tails captured.

Prime target pattern: shared-state "healing" routines — setup code that
repairs a shared directory/symlink farm at startup. Authors typically guard
creation (EEXIST branch) and leave read+delete naked (lstat → readlink →
unlink with no locking). Also: a losing racer's unlink can delete the winner's
fresh link — half-healed state, no error raised.

Verification: stress units in process-starts (e.g. 16-way × 3 rounds = 48
starts, 23 crashes pre-fix, 0 post-fix, then 24-way × 4 rounds as insurance).

## §env — environment / config layer

- CI red + local green → first question is "which code did CI build", not
  "what differs between platforms". GitHub pull_request builds the merge state
  (branch ⊕ latest main); a PR opened after an upstream semantic change is
  already testing it.
- merge-clean ≠ semantically compatible: bind assertions to a field's
  responsibility, not its name, when the field is on the upstream's active
  refactor surface.
- Isolation level is sized by the worst behavior the task can induce. An
  agent told to "write a cleanup script" under environment:none will install
  a real crontab on your machine.
- Pin versions in writing; isolate HOME with pre-seeded one-time dialogs;
  beware update prompts that replace the pinned binary mid-matrix.
