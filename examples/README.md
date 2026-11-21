# Examples

Templates to copy and samples to read. Nothing here was run as a counted matrix;
the cards that were are in [`cards/`](../cards/README.md). The skill-quake
bundle uses the same paths for `experiment-card.json`, `greeting-card/` and the
two prompts, so they keep these names.

| file | what it is |
|---|---|
| [experiment-card.json](experiment-card.json) | the card template to copy for a new matrix (`schema_version` 1.1); rules in `skills/repo-quake/references/experiment-card.md` |
| [experiment-card-paired.json](experiment-card-paired.json) | worked `design.kind=paired` card: two arms, AB/BA order ([playbook](../skills/repo-quake/references/paired-experiments.md)) |
| [experiment-card-memory.json](experiment-card-memory.json) | worked memory-evaluation card: write × retrieval × acceptance ([playbook](../skills/repo-quake/references/memory-eval.md)) |
| [experiment-card-metamorphic.json](experiment-card-metamorphic.json) | worked metamorphic card: relation-based oracle ([playbook](../skills/repo-quake/references/metamorphic.md)) |
| [experiment-card-quality-cost.json](experiment-card-quality-cost.json) | worked quality–cost card: per-success cost and Pareto choice ([playbook](../skills/repo-quake/references/quality-cost.md)) |
| [greeting-card/](greeting-card/SKILL.md) | the small sample skill that the skill-quake experiment wounded |
| [matrix-prompt.txt](matrix-prompt.txt), [replication-prompt.txt](replication-prompt.txt) | the skill-quake host prompts: matrix runs, and the replication runbook in `docs/skill-quake/REPLICATION.md` |

`tests/test_validate_card.py` validates every card here.
