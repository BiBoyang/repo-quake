# repo-quake

Fault-injection methodology and experiment workspace for one question: **pick an
open-source project, find where it silently breaks, and prove it with evidence an
upstream maintainer cannot dismiss.**

This repo is the umbrella. It absorbs and supersedes
[skill-quake](https://github.com/BiBoyang/skill-quake) (which remains available as
the file/skill-layer specialization, now vendored here under `skills/skill-quake/`).

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

## Experiment log (live runs)

| phase | target | headline | report |
|---|---|---|---|
| 1 | Vercel eve agent dir | blocking wounds 8/8, non-blocking 0/8; detection = f(read, report, path) | [docs/phase1-report.md](docs/phase1-report.md) |
| 1′ | pydantic-ai greeter | loud faults 8/8, stealth 0/16; byte-level payload proof | [docs/phase1p-report.md](docs/phase1p-report.md) |
| 2 | three examiner skills | 0/64 — redundancy, conditionality, and future-tense wounds don't block paths | [docs/phase2-report.md](docs/phase2-report.md) |

Upstream outcomes so far: alibaba/skill-up
[#253](https://github.com/alibaba/skill-up/issues/253)/[#257](https://github.com/alibaba/skill-up/pull/257),
[#263](https://github.com/alibaba/skill-up/issues/263)/[#265](https://github.com/alibaba/skill-up/pull/265),
[#280](https://github.com/alibaba/skill-up/issues/280)/[#281](https://github.com/alibaba/skill-up/pull/281);
MoonshotAI/kimi-code [#4012](https://github.com/MoonshotAI/kimi-code/issues/4012);
anthropics/skills [#1949](https://github.com/anthropics/skills/pull/1949);
microsoft/eval-guide [#16](https://github.com/microsoft/eval-guide/pull/16)
(drafts in `docs/pr-drafts/`).

## Layout

- `bin/skill-guard` — deterministic integrity gate for Agent Skills (stdlib-only
  Python, single file)
- `skills/repo-quake/` — the general methodology skill (this umbrella's core)
- `skills/skill-quake/` — file/skill-layer fault-injection specialization
- `witness/` — mechanical witnesses and matrix runners used in the phases
- `targets/` — self-made minimal targets (greeting-agent, pydantic-greeter)
- `vendor/` — pinned upstreams under test (eval-guide, skill-creator)
- `docs/` — phase reports, PR drafts; `docs/skill-quake/` — absorbed docs incl.
  `REPLICATION.md`
- `results/` — skill-quake era result summaries; `runs/` — raw per-run artifacts
  (gitignored except summaries)
- `tests/` — skill-guard fixture suite (`bash tests/run_tests.sh`)
- `examples/` — sample targets and prompts

## License

Apache-2.0 (see LICENSE).
