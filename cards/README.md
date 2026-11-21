# Experiment cards

One frozen card per counted matrix. A card is written, checked with
`skills/repo-quake/scripts/validate_card.py` and committed before the first
counted run. `skills/repo-quake/scripts/card_gate.py` then refuses any matrix
the card does not cover. After the runs, the public evidence copy carries the
same bytes as `card-frozen.json`.

| card | id | planned runs | evidence | report |
|---|---|---|---|---|
| [phase4-stream-retry.json](phase4-stream-retry.json) | `phase4-stream-retry-interactive-v1` | 36 | [runs/phase4-stream-retry-2026-11-15](../runs/phase4-stream-retry-2026-11-15/) | [phase 4](../docs/phase4-report.md) |
| [phase5-metacodes.json](phase5-metacodes.json) | `phase5-stream-retry-metacodes-v1` | 108 | [runs/phase5-metacodes-2026-11-16](../runs/phase5-metacodes-2026-11-16/) | [phase 5](../docs/phase5-report.md) |
| [phase5-appendix-f4f5.json](phase5-appendix-f4f5.json) | `phase5-appendix-f4f5-recheck-v1` | 60 | [runs/phase5-appendix-f4f5-2026-11-16](../runs/phase5-appendix-f4f5-2026-11-16/) | [phase 5](../docs/phase5-report.md) |
| [phase5-dsh.json](phase5-dsh.json) | `phase5-dsh-headless-recheck-v1` | 72 | [runs/phase5-dsh-2026-11-16](../runs/phase5-dsh-2026-11-16/) | [phase 5](../docs/phase5-report.md) |
| [phase6-metacodes-stall.json](phase6-metacodes-stall.json) | `phase6-stall-metacodes-v1` | 63 | [runs/phase6-metacodes-stall-2026-11-21](../runs/phase6-metacodes-stall-2026-11-21/) | [phase 6](../docs/phase6-report.md) |

Cards that are not in this directory:

- Templates for a new card are in `examples/`: `experiment-card.json`, plus the
  paired, memory, metamorphic and quality–cost variants.
- The factorial kit (prepared on 2026-10-30, never run) embeds its card in
  [witness/factorial/prereg/EXPERIMENT-CARD.md](../witness/factorial/prereg/EXPERIMENT-CARD.md).
- Phases 0–3 ran before cards existed.

Name a new phase's card `cards/phase<N>-<slug>.json`, using the same slug as its
run directory `runs/phase<N>-<slug>-<date>/`.

These cards lived at `examples/experiment-card-<name>.json` until 2026-11-21.
Manifests written before that date record the old path, at the commit they name.
