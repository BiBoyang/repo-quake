# Draft issue: whitespace-only prompt and turn content pass validation

**Repository:** alibaba/skill-up
**Tested commit:** `ad5f533b79b98b7281370fd2938c7d7e811e8c0a`
**Status:** draft only; not submitted

## Summary

`skill-up validate` accepts cases whose `input.prompt` or `input.turns[].content` contains only whitespace. The same command rejects `input.prompt: ""`. This makes “a task exists” depend on raw string length rather than whether the task contains any non-whitespace content.

## Minimal reproduction

Single-turn case:

```yaml
id: whitespace-prompt
title: whitespace-only prompt
input:
  prompt: "   "
judge:
  type: rule_based
  success:
    - exit_code: 0
```

Multi-turn case:

```yaml
id: whitespace-turn
title: whitespace-only turn
input:
  turns:
    - role: user
      content: "   "
judge:
  type: rule_based
  success:
    - exit_code: 0
```

For each case, use an `eval.yaml` whose `cases.files` contains the case and run `skill-up validate <path>`.

## Expected

Both cases should fail validation because there is no meaningful prompt/task content, just as `input.prompt: ""` is rejected.

## Actual on commit ad5f533

```text
✓ eval.yaml is valid (loaded 1 case(s))
```

The same result occurs for `prompt: "   "` and `turns[].content: "   "`. The control case with `input.prompt: ""` correctly fails with:

```text
Error: validation failed: case empty: validation errors:
  - input.prompt or input.turns is required
```

## Why this matters

The evaluator later constructs transcript messages from the raw strings, so a whitespace-only task can be accepted and delivered to an engine. This permits meaningless or accidental empty evaluations to pass configuration validation and can waste engine invocations or create misleading “loaded N case(s)” evidence.

## Relevant code

- `internal/config/validator.go:129-135` checks `cfg.Input.Prompt == ""` without `strings.TrimSpace`.
- `internal/config/validator.go:174-183` checks `turn.Content == ""` without `strings.TrimSpace`.
- `internal/evaluator/evaluator.go:332-347` uses the raw prompt/content to construct messages.

Other validators in the same file already use `strings.TrimSpace`, including `user_simulator.scenario` and `expect` string checks, so the input validation is inconsistent with those fields.

## Suggested fix

Use `strings.TrimSpace` in the presence checks, while preserving the original prompt bytes for runtime:

- Treat `strings.TrimSpace(cfg.Input.Prompt) == ""` as no prompt.
- Treat `strings.TrimSpace(turn.Content) == ""` as no content.
- Keep the mutual-exclusion behavior for `input.prompt` and `input.turns` unchanged.

Add table-driven tests for spaces, tabs and newlines in both single-turn `input.prompt` and multi-turn `input.turns[].content`, plus non-whitespace controls proving that valid content and its original bytes are preserved.

## Evidence artifacts

Local reproduction logs and fixtures are preserved under `runs/skill-up-main-2026-10-24/deterministic-config-matrix/` in repo-quake. A limited GitHub issue search did not show an obvious existing duplicate; that search is not exhaustive.

## Independent verification (subagent, 2026-10-24)

A separate agent independently reproduced the behavior without modifying the upstream checkout or calling a model/API. It confirmed `vcs.modified=false` on the tested binary and checked normal text, empty strings, spaces, tabs and newlines:

| input | normal text | empty string | spaces | tab | newline |
|---|---:|---:|---:|---:|---:|
| `input.prompt` | accepted | rejected | accepted | accepted | accepted |
| `input.turns[].content` | accepted | rejected | accepted | accepted | accepted |

The subagent found no documented intent to support vacuous tasks. Its conclusion was **confirmed / suitable for an issue**, while noting that this does not exclude a different maintainer intent and does not prove an overall PASS or paid API usage.

### Additional PR caution

Do not simply rewrite all presence/mutual-exclusion logic with `hasPrompt = strings.TrimSpace(prompt) != ""`. If whitespace-only prompt is present alongside valid turns, the existing implementation rejects the combination because raw prompt is non-empty. Replacing that logic naively could silently turn it into a turns-only case while the runtime still follows the raw non-empty single-prompt path.

The safe minimal direction is:

- use `TrimSpace` only for detecting blank input, not for rewriting stored content;
- preserve the existing mutual-exclusion semantics and add a specific whitespace-prompt + valid-turns regression test;
- keep the PR limited to validator changes and table-driven tests, without broadening to `respond` or evaluator rewrites.
