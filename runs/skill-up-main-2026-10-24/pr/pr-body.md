## Summary

Reject whitespace-only `input.prompt` and `input.turns[].content` during validation, while preserving the original prompt bytes and the existing prompt/turns mutual-exclusion behavior.

## Related issues

Closes #337

## Changes

- Use `strings.TrimSpace` for blank detection in prompt and turn-content validation.
- Keep presence checks used for mutual exclusion byte-based, so a whitespace-only prompt alongside turns cannot silently become a turns-only case.
- Add table-driven tests for spaces, tabs, newlines, valid surrounding whitespace, and prompt/content plus respond mutual exclusion.
- Document the validation change in `CHANGELOG.md`.

## Test plan

- [x] `make test` passes, including the race detector and plugin suites
- [x] `make verify` passes (`go vet`, `revive`, `golangci-lint`)
- [x] Manual validation of healthy, empty-string, whitespace-prompt and whitespace-turn fixtures
- [x] Independent second-agent reproduction with spaces, tabs and newlines

## Notes for reviewers

This PR deliberately does not change evaluator code or rewrite stored prompt content. `TrimSpace` is used only to decide whether input is blank. The mutual-exclusion path still treats the original non-empty field as present, so `prompt: " "` plus valid turns remains invalid rather than becoming turns-only. No real model or paid API calls were used in verification.
