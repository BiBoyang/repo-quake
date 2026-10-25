# Issue and evidence publication checklist

## Ready now

- [x] Three direct contract calls and the full-browser F1 witness agree.
- [x] Standalone minimal repro rerun; output is stored in `upstream-repro/actual-output.txt`.
- [x] Expected behavior is tied to the existing `CacheWrite` contract and `docs/cache.mdx`, not personal preference.
- [x] Main source inspected at main HEAD `69e123b17e04ed624df16d32f3b1ef95ce22c083`; `context.ts` last-path commit `689620d728d04202757ffd11ed001b512b68044a` is recorded separately, and main runtime is explicitly not claimed.
- [x] Related #939 and #1363 reviewed and distinguished; `store.write` and throw searches found no duplicate.
- [x] Sample sizes and deterministic-executor limitations stated.
- [x] Original malformed U1 and grader-error cells excluded from the finding.
- [x] Issue body is self-contained and does not cite private/unpublished evidence.
- [x] PR requirements checked against CONTRIBUTING, PR template, AGENTS, writing-pr, and ship-pr on 2026-10-25.

## Ordered publication gate

- [x] Human reviewed the title and draft on 2026-10-25; final edit was tone-only, with the reproduction and technical claims unchanged.
- [x] Upstream issue published and content verified: https://github.com/tester-army/e2e/issues/1371. The `bug` label could not be added because the upstream denied `AddLabelsToLabelable`; title/body are correct and the label is left for a maintainer.
- [x] Recorded https://github.com/tester-army/e2e/issues/1371 in all three disclosure files and this checklist.
- [x] Committed disclosure URL updates and pushed the [repo-quake evidence branch](https://github.com/BiBoyang/repo-quake/tree/codex/measurement-hardening) through `85babcf`, after issue #1371 was created.
- [x] PR implemented and opened as https://github.com/tester-army/e2e/pull/1372 with `Fixes #1371`; checks and Cubic passed. Ready label and Mintlify approval require upstream write access; no merge or self-approval.
- [x] PR body populated with final-diff facts and actual verification; no placeholders remain in the public body.

## Manual issue command (do not run during preparation)

From `/Users/boyang/repo-quake`:

```sh
gh issue create \
  --repo tester-army/e2e \
  --label bug \
  --title "$(cat runs/e2e-cache-write-contract-2026-10-25/issue-title.txt)" \
  --body-file runs/e2e-cache-write-contract-2026-10-25/issue-body.md
```

The command is intentionally not executed by the preparation flow.
