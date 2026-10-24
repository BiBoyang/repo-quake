## Summary

`skill-up validate` accepts `input.prompt` and `input.turns[].content` values that contain only whitespace. The same command rejects `input.prompt: ""`. This lets an empty task pass configuration validation.

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

Both cases should fail validation because they contain no meaningful task content, just as `input.prompt: ""` is rejected.

## Actual on ad5f533

Both produce:

```text
✓ eval.yaml is valid (loaded 1 case(s))
```

The control with `input.prompt: ""` correctly fails with:

```text
Error: validation failed: case empty: validation errors:
  - input.prompt or input.turns is required
```

An independent second agent reproduced the same behavior for spaces, tabs and newlines, while normal text was accepted.

## Code evidence

- `internal/config/validator.go:129-135` checks `cfg.Input.Prompt == ""` without `strings.TrimSpace`.
- `internal/config/validator.go:174-183` checks `turn.Content == ""` without `strings.TrimSpace`.
- `internal/evaluator/evaluator.go:332-347` uses the raw prompt/content to construct messages.
- Other validators in the same file already use `strings.TrimSpace`, including `user_simulator.scenario` and `expect` string checks.

This can allow an accidental empty evaluation to pass validation and reach the engine execution path. It does not by itself prove an overall PASS or a paid API call.

## Suggested direction

Use `strings.TrimSpace` for blank detection without rewriting stored prompt bytes. Preserve the existing mutual-exclusion semantics and add regression coverage for spaces, tabs, newlines, normal content, and whitespace-prompt plus valid turns.
