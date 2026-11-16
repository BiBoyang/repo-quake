# repo-quake

Fault-injection methodology and experiment workspace for one question: **pick an
open-source project, find where it silently breaks, and prove it with evidence an
upstream maintainer cannot dismiss.**

This repo is the umbrella and the source of truth. It absorbs and supersedes
[skill-quake](https://github.com/BiBoyang/skill-quake), which stays online as the
small self-contained bundle for the file/skill-layer experiment (same guard, same
skill, same tests — ~316 KB clone vs ~23 MB here). Method and code changes land in
this repo first; the bundle is refreshed from here when it needs to be.

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

## Evidence guide and archive audit

For a Chinese, example-driven guide to failure attribution, independent
outcomes and publication read-back, read
[`docs/eval-evidence-guide.md`](docs/eval-evidence-guide.md).

Before archiving an experiment directory, run:

```bash
python3 skills/repo-quake/scripts/audit_artifacts.py <experiment-directory>
```

It reports symlinks, runtime-only trees and high-confidence credential shapes
without deleting or rewriting evidence.

## Experiment log (live runs)

| phase | target | headline | report |
|---|---|---|---|
| 1 | Vercel eve agent dir | blocking wounds 8/8, non-blocking 0/8; detection = f(read, report, path) | [docs/phase1-report.md](docs/phase1-report.md) |
| 1′ | pydantic-ai greeter | loud faults 8/8, stealth 0/16; byte-level payload proof | [docs/phase1p-report.md](docs/phase1p-report.md) |
| 2 | three examiner skills | 0/64 — redundancy, conditionality, and future-tense wounds don't block paths | [docs/phase2-report.md](docs/phase2-report.md) |
| 4 | Claude Code / codex / Kimi Code: display after a mid-stream retry | Kimi Code takes a terminator-less stream as a finished turn (TUI 3/3, `-p` 3/3; [#4964](https://github.com/MoonshotAI/kimi-code/issues/4964)); its retry sends the partial back without `partial` 12/12 (consequence unverified, not reported); Claude Code and codex end with one answer 18/18 (codex shows both copies while retrying, and keeps all six attempts on screen when the retries run out, 6/6 exploratory; [#47538](https://github.com/openai/codex/issues/47538)) | [docs/phase4-report.md](docs/phase4-report.md) |
| 5 | re-tests with the phase-4 witness: metacodes (main, TUI and headless), Claude Code / codex on length stops, deepseek-harness 0.2.2-rc.3, skill-up fixes | metacodes' TUI re-issues a dropped stream but keeps the dropped text or thinking on screen above the retried answer, with no notice (15/15; headless never prints it 30/30, `--stream-json` retracts it 15/15); Claude Code still gives no signal on a length stop (12/12, raw bytes included), codex 0.169.0 now reports `max_output_tokens` instead of retrying (12/12); deepseek-harness still ends a length stop with a bare exit 1 (18/18); skill-up #253 and #263 confirmed fixed, #280 still reproduces | [docs/phase5-report.md](docs/phase5-report.md) |

Upstream outcomes so far: alibaba/skill-up
[#253](https://github.com/alibaba/skill-up/issues/253)/[#257](https://github.com/alibaba/skill-up/pull/257),
[#263](https://github.com/alibaba/skill-up/issues/263)/[#265](https://github.com/alibaba/skill-up/pull/265),
[#280](https://github.com/alibaba/skill-up/issues/280)/[#281](https://github.com/alibaba/skill-up/pull/281);
MoonshotAI/kimi-code [#4012](https://github.com/MoonshotAI/kimi-code/issues/4012),
[#4964](https://github.com/MoonshotAI/kimi-code/issues/4964);
openai/codex [#47538](https://github.com/openai/codex/issues/47538#issuecomment-6905066983) (comment with a repro);
anthropics/skills [#1949](https://github.com/anthropics/skills/pull/1949);
microsoft/eval-guide [#16](https://github.com/microsoft/eval-guide/pull/16)
(drafts in `docs/pr-drafts/`).

## Layout

- `bin/skill-guard` — deterministic integrity gate for Agent Skills (stdlib-only
  Python, single file)
- `skills/repo-quake/` — the general methodology skill (this umbrella's core),
  including fault injection plus paired, memory, metamorphic and quality–cost
  experiment contracts
- `skills/skill-quake/` — file/skill-layer fault-injection specialization
- `witness/` — mechanical witnesses and matrix runners used in the phases
- `targets/` — self-made minimal targets (greeting-agent, pydantic-greeter)
- `vendor/` — pinned upstreams under test (eval-guide, skill-creator)
- `docs/` — phase reports, PR drafts; `docs/skill-quake/` — labeled snapshots of
  the bundle's docs (`REPLICATION.md`, article, upstream issue drafts); the living
  copies stay in the skill-quake repo
- `results/` — skill-quake era result summaries; `runs/` — raw per-run artifacts
  (gitignored except summaries)
- `tests/` — guard fixtures plus collector, metadata, card and fake-host matrix tests (`bash tests/run_tests.sh`)
- `examples/` — sample targets, prompts and `experiment-card.json`
- `skills/repo-quake/scripts/validate_card.py` — stdlib experiment-card validator
- `skills/repo-quake/scripts/audit_artifacts.py` — stdlib pre-archive symlink,
  runtime-tree and credential-shape audit
- `skills/skill-quake/scripts/write_meta.py` — per-run provenance and content-hash writer

## License

Apache-2.0 (see LICENSE).

## Fault ledger（缺陷台账）

`ledger/ledger.json` structures every target finding, instrument defect and
experiment-validity event narrated in `docs/` (the evidence guide's three ledgers)
with per-cell x/N counts, evidence paths and upstream links; schema and conventions
live in [`ledger/SCHEMA.md`](ledger/SCHEMA.md). Attribution there is interpretation, not measurement.

```bash
python3 bin/ledger-check ledger/ledger.json
```
