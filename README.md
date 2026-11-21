# repo-quake

Fault-injection methodology and experiment workspace for one question: **pick an
open-source project, find where it silently breaks, and prove it with evidence an
upstream maintainer cannot dismiss.**

This repo is the umbrella and the source of truth. It absorbs and supersedes
[skill-quake](https://github.com/BiBoyang/skill-quake), which stays online as the
small self-contained bundle for the file/skill-layer experiment: the same guard,
skills and tests, without the experiment evidence. Method and code changes land
in this repo first; the bundle is refreshed from here when it needs to be.

## Two layers, deliberately separated

| layer | where | question | nature |
|---|---|---|---|
| foundation | `bin/skill-guard` | Is the artifact set intact? | deterministic CLI, CI-able, exit 0/1 |
| experiment | `skills/repo-quake/`, `skills/skill-quake/` | Does the host/system notice damage? | orchestration skills (judgment) |

The separation is the thesis: **the foundation only accepts or rejects; grading is
for judges.**

## The method in one paragraph

Detection = reaches-the-eyes × willing-to-report × blocks-the-path. Every piece of
evidence needs its own witness: faults need delivery proof, detections need
positive controls, negative conclusions need byte-level evidence, and the most
striking conclusion is a suspect until re-verified. Fresh zero-context hosts,
neutral prompts, mutated copies only, hash-named staging, x/N per cell, negative
controls — the full invariant list and the eight-step playbook live in
[`skills/repo-quake/SKILL.md`](skills/repo-quake/SKILL.md).

## Method articles and archive audit

- [`docs/detection-model.md`](docs/detection-model.md): the three-factor model
  applied to known evaluation failures, and the witness principle applied to the
  evaluation stack itself.
- [`docs/eval-evidence-guide.md`](docs/eval-evidence-guide.md): a Chinese,
  example-driven guide to failure attribution, independent outcomes and
  publication read-back.

Before archiving an experiment directory, run:

```bash
python3 skills/repo-quake/scripts/audit_artifacts.py <experiment-directory>
```

It reports symlinks, runtime-only trees and high-confidence credential shapes
without deleting or rewriting evidence.

## Experiment log

| phase | date | target | headline | report |
|---|---|---|---|---|
| 0 | 2026-09-30 | Vercel eve agent dir (self-made `targets/greeting-agent`) | setup only: target, witness, cut points E1–E3; cold probes show neither host's weights know vercel/eve | [notes](docs/phase0-notes.md) |
| 1 | 2026-10-01 | the same agent dir, kimi and codex | blocking wound (E2) 8/8 on both hosts; non-blocking: E1 0/8 on both, E3 kimi 0/8 vs codex 5/8 (codex opened the truncated file); detection = f(read, report, path) | [report](docs/phase1-report.md) |
| 1′ | 2026-10-01 | pydantic-ai greeter | loud faults 8/8, stealth 0/16; byte-level payload proof | [report](docs/phase1p-report.md) |
| 2 | 2026-10-02 | three examiner skills | 0/64: redundancy, conditionality and future-tense wounds don't block paths | [report](docs/phase2-report.md), [notes](docs/phase2-notes.md) |
| 3 | 2026-10-15 | metacodes 0.5.0, three wire protocols, local mock (spike) | a stream without its terminator is taken as `end_turn` on all three wires, so the `max_tokens` continuation never fires (cc 2/2, resp 2/2, anth 1/1); [#269](https://github.com/metask-ai/metacodes/issues/269), fixed by #272 | [disclosure](docs/phase3-disclosure.md) |
| 4 | 2026-11-15 | Claude Code, codex, Kimi Code: the screen after a mid-stream retry | Kimi Code takes a terminator-less stream as a finished turn (TUI 3/3, `-p` 3/3; [#4964](https://github.com/MoonshotAI/kimi-code/issues/4964)); Claude Code and codex end with one answer 18/18, codex showing both copies while it retries ([#47538](https://github.com/openai/codex/issues/47538#issuecomment-6905066983)) | [report](docs/phase4-report.md), [disclosure](docs/phase4-disclosure.md) |
| 5 | 2026-11-16 | re-tests with the phase-4 witness: metacodes, Claude Code and codex on length stops, deepseek-harness, skill-up fixes | metacodes' TUI keeps the dropped text or thinking above the retried answer with no notice (15/15), a trade-off [#465](https://github.com/metask-ai/metacodes/pull/465) documents; Claude Code still says nothing on a length stop (12/12), codex 0.169.0 now reports it; deepseek-harness still exits 1 with no message (18/18; [#13496](https://github.com/deepseek-ai/deepseek-harness/discussions/13496)); skill-up #253 and #263 fixed, #280 still reproduces | [report](docs/phase5-report.md), [disclosure](docs/phase5-disclosure.md) |
| 6 | 2026-11-21 | metacodes main 53b3e285: the TUI while a dependency stalls | four waits with no deadline of their own (`/v1/models` at start, the `/model` key list, an HTTP MCP DELETE and an HTTPS handshake at exit; 3/3 each); three bounded but silent ones (TinyKG 35 s, OTLP at `/exit`, ~15 s per Edit with a silent language server); 63 counted runs | [report](docs/phase6-report.md), [disclosure](docs/phase6-disclosure.md) |

Not numbered as phases:

- **Side experiments, 2026-10-24/25**: npm `e2e@0.21.3` replay and cache
  behavior (tester-army/e2e #1371, fixed by #1372), and an upstream-main
  regression of skill-up with a deterministic config-boundary check (#337, fixed
  by #338). See [`runs/README.md`](runs/README.md).
- **Prepared, never run**: the factorial probe kit (2026-10-30): wound
  path_relation × shell × model, 72/136/168 runs in three tiers, zero host calls
  so far. Card: [`witness/factorial/prereg/EXPERIMENT-CARD.md`](witness/factorial/prereg/EXPERIMENT-CARD.md).
- **Before this repository**: the skill-quake experiment (2026-09-25), with raw
  runs in [`runs/skill-quake-2026-09-25/`](runs/skill-quake-2026-09-25/) and its
  write-up in [`docs/skill-quake/`](docs/skill-quake/).

## Upstream outcomes

Every outcome below has a ledger entry, except kimi-code #4012, which predates
this repository. The states shown were read on 2026-11-21.

- alibaba/skill-up: [#253](https://github.com/alibaba/skill-up/issues/253)/[#257](https://github.com/alibaba/skill-up/pull/257)
  and [#263](https://github.com/alibaba/skill-up/issues/263)/[#265](https://github.com/alibaba/skill-up/pull/265),
  fixed; [#280](https://github.com/alibaba/skill-up/issues/280)/[#281](https://github.com/alibaba/skill-up/pull/281),
  PR merged on 2026-11-19, issue still open; [#337](https://github.com/alibaba/skill-up/issues/337)/[#338](https://github.com/alibaba/skill-up/pull/338), fixed.
- MoonshotAI/kimi-code: [#4964](https://github.com/MoonshotAI/kimi-code/issues/4964), open;
  [#4012](https://github.com/MoonshotAI/kimi-code/issues/4012) (2026-09-24, before this repository), open.
- openai/codex: [#47538](https://github.com/openai/codex/issues/47538#issuecomment-6905066983), a comment with a repro.
- deepseek-ai/deepseek-harness: [Discussions #13496](https://github.com/deepseek-ai/deepseek-harness/discussions/13496), a feature request.
- metask-ai/metacodes: [#269](https://github.com/metask-ai/metacodes/issues/269), fixed by
  [#272](https://github.com/metask-ai/metacodes/pull/272) (phase 3);
  [#666](https://github.com/metask-ai/metacodes/issues/666), [#667](https://github.com/metask-ai/metacodes/issues/667),
  [#668](https://github.com/metask-ai/metacodes/issues/668), [#669](https://github.com/metask-ai/metacodes/issues/669),
  [#670](https://github.com/metask-ai/metacodes/issues/670), [#671](https://github.com/metask-ai/metacodes/issues/671),
  [#672](https://github.com/metask-ai/metacodes/issues/672), open (phase 6, unassigned).
- tester-army/e2e: [#1371](https://github.com/tester-army/e2e/issues/1371)/[#1372](https://github.com/tester-army/e2e/pull/1372), fixed.
- anthropics/skills: [#1949](https://github.com/anthropics/skills/pull/1949), open PR;
  microsoft/eval-guide: [#16](https://github.com/microsoft/eval-guide/pull/16), open PR
  (drafts in [`docs/pr-drafts/`](docs/pr-drafts/)).

## Layout

| path | what is there |
|---|---|
| `bin/` | `skill-guard`, the deterministic integrity gate for Agent Skills, and `ledger-check`; stdlib-only Python |
| `skills/repo-quake/` | the methodology skill: playbook, references, and `scripts/` (`validate_card.py`, `card_gate.py`, `audit_artifacts.py`) |
| `skills/skill-quake/` | the file/skill-layer specialization: mutation scripts, host adapters, `write_meta.py` |
| `cards/` | the frozen experiment card of every counted matrix ([index](cards/README.md)) |
| `witness/` | instruments, one directory per family: `integrity/`, `factorial/`, `stream-retry/`, `stall/` ([index](witness/README.md)) |
| `targets/` | self-made targets: `greeting-agent` (phases 0–1, factorial kit), `pydantic-greeter` (phase 1′) |
| `vendor/` | pinned upstreams under test in phase 2: `eval-guide`, `skill-creator` |
| `runs/` | raw evidence, one directory per run set ([index and artifact policy](runs/README.md)) |
| `ledger/` | the fault ledger and its schema (below) |
| `docs/` | phase reports, notes and disclosures; method articles; upstream PR drafts; process records; skill-quake snapshots ([index](docs/README.md)) |
| `examples/` | templates and samples: `experiment-card.json` and its design variants, the `greeting-card` skill, prompts ([index](examples/README.md)) |
| `tests/` | `bash tests/run_tests.sh`: guard fixtures, collectors, cards, witnesses, the factorial dry-run, the ledger and this layout |

## Adding a phase

The layout phases 4–6 follow. `tests/test_layout.py` fails when an index, the
upstream list or a relative link falls behind:

1. Instrument in `witness/<name>/`, with a README, tests in `tests/`, and a row in
   `witness/README.md`.
2. Card in `cards/phase<N>-<slug>.json`, validated and committed before the first
   counted run; `skills/repo-quake/scripts/card_gate.py` refuses a matrix it does
   not cover.
3. Evidence root outside the repo; the audited public copy goes to
   `runs/phase<N>-<slug>-<date>/` with `card-frozen.json` byte-equal to the card,
   and gets a line in `runs/README.md`.
4. `docs/phase<N>-report.md` and `docs/phase<N>-disclosure.md`.
5. Ledger entries with `phase: phase<N>`; their upstream links also go in the
   list above.
6. One row in the experiment log above. Upstream first (the posting gate in
   `skills/repo-quake/references/reporting.md`), then push; tag the release when
   the phase ships.

## Fault ledger（缺陷台账）

`ledger/ledger.json` structures every target finding, instrument defect and
experiment-validity event narrated in `docs/` or carrying an upstream outcome
(the evidence guide's three ledgers) with per-cell x/N counts, evidence paths and
upstream links. Schema and conventions live in [`ledger/SCHEMA.md`](ledger/SCHEMA.md).
Attribution there is interpretation, not measurement.

```bash
python3 bin/ledger-check ledger/ledger.json
```

## License

Apache-2.0 (see LICENSE).
