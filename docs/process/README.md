# Process records

How some of the work here was planned, handed out and accepted. These are
records, kept as they were written. Paths inside them are the paths of the day:
until 2026-11-21 these three directories sat at the top of the repo as
`plans/`, `prompts/` and `reviews/`.

## The 2026-10-30 three-role tasks

A Planner wrote a contract (`plans/`) and a dispatch prompt (`prompts/*.prompt.md`).
An Executor ran it and appended to a status log (`prompts/*.status.md`). The
Owner reviewed the result (`reviews/`). All three tasks were approved on
2026-10-30, and their work is on master as 281c587 (ledger), 9a9bd80
(factorial materials) and 00bc8d7 (article). The "待 Owner 确认" status line
in each contract is the status at dispatch; the final status is the prompt
header `status: done`.

| task | contract | prompt | status log | review | what it produced |
|---|---|---|---|---|---|
| fault ledger | [plan](plans/TASK-flaw-ledger-schema.md) | [prompt](prompts/TASK-flaw-ledger-schema.prompt.md) | [log](prompts/TASK-flaw-ledger-schema.status.md) | [Approved](reviews/REVIEW-flaw-ledger-schema-2026-10-30.md) | `ledger/`, `bin/ledger-check` |
| factorial probes | [plan](plans/TASK-factorial-probes.md) | [prompt](prompts/TASK-factorial-probes.prompt.md) | [log](prompts/TASK-factorial-probes.status.md) | [Approved](reviews/REVIEW-factorial-probes-2026-10-30.md) | `witness/factorial/` (prepared, never run; labeled phase3 then, `factorial` since card v3) |
| detection-model article | [plan](plans/TASK-detection-model-article.md) | [prompt](prompts/TASK-detection-model-article.prompt.md) | [log](prompts/TASK-detection-model-article.status.md) | [Approved](reviews/REVIEW-detection-model-article-2026-10-30.md) | [`docs/detection-model.md`](../detection-model.md) |

## Execution prompt templates

- [plans/TASK-stream-retry-display.md](plans/TASK-stream-retry-display.md): the
  phase-4 executor prompt, with a review checklist (2026-11-15). Its card path
  is now `cards/phase4-stream-retry.json`, and its gate is
  `skills/repo-quake/scripts/card_gate.py`.
