# DISCLOSURE — phase3: metacodes stream-truncation spike (2026-10-15)

*A worked example of `skills/repo-quake/references/disclosure-template.md`,
filled for the phase-3 spike. The finding is public as
[metask-ai/metacodes#269](https://github.com/metask-ai/metacodes/issues/269).*

Spike: does metacodes 0.5.0 notice truncated/missing-terminator streams on its
three wire protocols? Local mock provider, headless `-p`, `--state-dir`
isolation.

**Estimate vs official.** Every number here is a direct observation from our own
runs (class a). JevBench-style "official scorer" does not exist for this probe;
the behavior claims were additionally confirmed at source level (0.5.1-dev).

## 1. Access and contact

- Touched: the public 0.5.0 release binary (sha256-verified), public source
  tree, a local mock on 127.0.0.1.
- Never touched: any metask production endpoint, any real provider, any
  credential. All cells ran against the mock only.
- Isolation: `--state-dir` scratch root; read-only target. Worst inducible
  behavior was local file reads — sandbox-level isolation not required.

## 2. Hash manifest

| artifact | sha256 / revision |
|---|---|
| metacodes binary (0.5.0 aarch64-macos tarball) | `beecc5fc…facb39` (matches release page) |
| source read | 0.5.1-dev tree, commit `4e826ce` (tarball) |
| mock | truncation-detection-benchmark `mock.mjs`, 395 lines |
| prompt | `runners/prompt.txt` from the same repo |
| provider config | `/tmp/quake-recon/mc-state/config.json` (3 channels) |

## 3. Pre-registration and deviations

No prereg file (spike, lesson learned — phase 4 will carry one). Deviations from
the ch05 matrix procedure:

- N=1 per cell (F2-cc and F2-resp later raised to N=2); a spike, reported as
  existence, not rates.
- `--record` cassette produced empty directories; witness evidence fell back to
  mock-side byte logs entirely. Unresolved.
- One extra plain-stdout F4 run added mid-spike to check user-visible
  duplication (not in the original cell plan).

## 4. Integrity statements

1. No cell dropped after grading; the aborted first run (mock not yet running,
   `ConnectionRefused`) is excluded from rates and stated here.
2. Environment failure (that same run) excluded and counted: 1.
3. Contamination register: the host's `~/.agents/skills` listings entered the
   system prompt via the documented personal tier (uniform across cells; the
   prompt requested pure text with no tool use, so fault semantics were
   unaffected).
4. Witness blind spot: none known for this fault set; the mock's delivery log is
   byte-level and was the primary witness.

## 7. Posting gate record

- [x] Upstream loop opened first: issue #269 filed 2026-10-15, before any public
      writeup. (An earlier draft report was accidentally pushed and removed the
      same night; the lesson is now the posting-gate checklist in
      `references/reporting.md`.)
- [x] Numbers re-checked against mock byte logs and transcripts.
- [x] Most striking claim (F2 silent acceptance) re-verified: mock bytes →
      three wires consistent → code-line confirmation.
- [x] N=1/N=2 caveats stated wherever a result is mentioned.
- [x] Contamination register reviewed (above).
