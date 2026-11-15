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

Refusal pattern worth copying into targets you design: refuse loudly, with the
measured cost attached (a benchmark adapter refuses nf4 quantization and states
the measured ~12-point capability loss as the reason; over-length inputs get a
typed 422, "scored wrong, not an infrastructure error"). A refusal that carries
its evidence is a feature; a silent fallback is a wound.

## §stream — protocol / streaming layer

Standard faults (truncation-detection-benchmark lineage):

| fault | protocol shape |
|---|---|
| F0 | healthy full stream (control row) |
| F1 | mid-stream TCP FIN (graceful close, chunked body left unterminated), no terminator |
| F2 | all content sent, terminator event missing, stream closes normally |
| F3 | half an SSE event (invalid JSON) then FIN |
| F4 | finish_reason=length / max_tokens termination |
| F5 | think-only: reasoning burns the budget, zero content (doubles as positive control against clients with empty-response retry) |
| F6 | F2 with half the content: half the content, then a complete HTTP body (terminating chunk sent), no terminator event |
| FLONG | a partial longer than the viewport (≥150 numbered lines at a slow frame interval, ~150 ms), then FIN — for display witnesses; see the alternate-screen lesson below |

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
- "always" must mean always: a client that exhausts its streaming retries may
  fall back to `stream:false`; fail those requests too, and never let a
  non-streaming request consume a once-fault
- a continuation mode is a hypothesis about the server, not a fact: when the
  last message is role=assistant carrying a partial, answer only the
  remainder — but keep it dialect-specific (Kimi's Partial Mode requires
  `partial=True` on that message), log the decision per request, and run the
  restart branch alongside it
- alternate-screen TUIs (`ESC[?1049h`) make tmux history identical to the
  visible screen: a final capture cannot rule out content above it, and
  `ESC[3J` tells you nothing there. Record the raw byte stream
  (`tmux pipe-pane`) and look inside the app (scroll, or its transcript view)
  before concluding that anything was retracted
- retry notices can live for one second: read them from the raw bytes, not
  from the final screen
- trigger mid-run captures on markers only the failed attempt emits, and
  timestamp them against the mock log; a capture taken after the retry started
  witnesses nothing
- size a "no retry" quiet window from the measured maximum gap between
  attempts (gaps of 33–40 s were observed), or use the client's own end state
- strip whitespace before counting markers; terminal wrapping splits them

Mock fidelity: calibrate the mock against a captured real stream, and treat the
capture as the only step allowed to touch the network. Keep provenance next to
the fixture — endpoint, protocol dialect, capture date, request parameters —
because a mock that drifts from the real dialect hides exactly the errors the
experiment is meant to find. Delivery proof belongs in the report per request
(port, fault id, event count, bytes, whether the terminal witness arrived, how
the stream was closed); an empty delivery array is itself a signal — the client
never reached the mock.

Typical findings to hunt: detection exists but is never translated to a
user-visible sentence; deterministic faults share one retry policy with
transient faults; transcripts keep no tombstone (failed attempt and retry
attempt serialize identically); a missing-terminator stream normalized to a
fabricated `end_turn`, which also bypasses any truncation-triggered recovery
net (observed 2026-10: all three wire protocols of one CLI, upstream issue
filed); the screen and the conversation fork after a retry (the failed
attempt's partial stays on screen or in stdout while the stored context drops
it — or the reverse: kept in context, then the server restarts, so both
duplicate); a retry that sends the partial back for continuation without the
provider's documented prefill flag (check the retry request body — the outcome
then rests on undocumented server behavior).

Recording retry-display outcomes. The labels below are grading notes, not a new
vocabulary: the ledger records only the five observation fields
(`ledger/SCHEMA.md`). Record a field only when its witness exists.

| outcome | witness it needs | five-field record |
|---|---|---|
| not shown — output buffered until complete, the partial never reached screen or stdout | no partial markers in stdout/stderr; a clean retry in the mock log | detected, contained, recovered |
| retracted — shown, then gone; the retry carried nothing | a mid capture keyed to failed-attempt-only markers and timestamped; the final display; an in-app view for alternate-screen apps | detected, contained, recovered |
| fork — the partial stays on screen, the conversation drops it | the final display, plus the next request or the stored context | detected, recovered; contained ✗, reported ✗ |
| continued — the retry carried the partial, the display reads once | the retry body; the mock's continuation log; the final display | detected, recovered, contained — only as good as the continue-branch hypothesis |
| duplicate — the retry carried the partial, the server restarted | the retry body, the final display, the stored context | detected, recovered; contained ✗ |
| accepted partial — no retry, the partial treated as complete, no notice | a single request; final display = partial; the stored stop reason | detected ✗, reported ✗ |
| reported failure — no recovery, an error shown | the notice (raw bytes or final screen); the request ladder | detected, reported; recovered ✗ |

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
- Gate every keystroke into an interactive subject: send keys only when the
  input box is on screen and no prompt would consume the key (update, migrate,
  trust, login, API-key confirmation). Second launches are where update and
  migration prompts appear. Calibrate the gate's patterns against saved screen
  fixtures — a gate that misreads a confirmation prompt as "ready" is worse
  than none. Where a client cannot disable its update check, rely on hashing
  the executed binary before and after (invariant 11).
- Start subjects from an allowlist (`env -i` plus explicit variables);
  otherwise they inherit the experimenter's environment, down to identifying
  themselves as the experimenter's own host app.
- Redact copies, never the evidence: a cleanup script that rewrites raw
  artifacts in place (scrubbing IDs, re-serializing request bodies) destroys
  the archive the playbook protects. Audit with
  `skills/repo-quake/scripts/audit_artifacts.py`, then redact what you publish.

## §extension — plugin / extension lifecycle

For targets that install third-party code rather than only running their own:
the package manager, the mount step, and the version resolver are all seams.

| seam | wound | witness |
|---|---|---|
| installer | package not installable, build hook blocked, lifecycle script fails | installer exit code + output tail, recorded as a case-level error (not a crashed run) |
| version resolution | unpinned spec resolves to latest; an upstream publish changes the target mid-series | resolved version/hash in every cell's meta; pinned spec in every case |
| post-install build | `prepare` / `postinstall` suppressed by the package manager's policy → installed but broken | installed tree diffed against the package manifest |
| mount / enable | plugin present but never loaded, or loaded after the step that needed it | load log or config dump — never an exit code |

Rules that keep this surface honest:

- An install failure is a finding, not an accident: keep the spec, the command,
  and the installer's output tail attached to that cell.
- Declaring a plugin for mounting authorizes arbitrary code execution on the
  machine running the experiment. Say so in the report, and only do it for
  source you would run by hand. The isolation level is sized by that sentence,
  not by the task's intent.
- A version bump is not a re-run, it is a new experiment: re-baseline by hand
  and keep the old numbers labeled with their version.
