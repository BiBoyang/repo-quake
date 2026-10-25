# PR implementation and publication plan (not started)

## Required sequence

This repository requires an existing issue on a community `fix` PR. Do not open a PR without an issue number.

1. Publish `issue-body.md` and record its number.
2. Branch from current `upstream/main`, using `codex/fix-cache-write-outcome`.
3. Prove the new regression test fails on main before applying the fix.
4. Apply the small fix, run focused and full verification, then open the PR with `Fixes #<number>`.
5. Follow the upstream `ship-pr` process through fresh-context review, green checks, handled bot threads, and `Ready for Human Review`. Never merge or approve our own PR.

## Intended small change

- `packages/e2e/src/cache/context.ts`
  - In the existing settlement catch, preserve `not-written` for a confirmed `kind=write` entry when the read/write path throws before an outcome is recorded.
  - Do not change `keep`, eviction, unconfirmed, or interrupted-attempt behavior.
- `packages/e2e/tests/unit/trace-cache-config.test.ts`
  - Add a custom-store rejection test beside the other `settleStagedTraces` cases.
  - Assert the rejected confirmed write reports `not-written` and a later healthy entry still settles, proving containment as well as reporting.
  - Run the test on main first and retain its failure as the before evidence.
- `docs/cache.mdx`
  - Extend the existing `not-written` row to include a store rejection, without changing the public contract.
- `.changeset/<generated-name>.md`
  - Add a `patch` changeset for `e2e` through `pnpm changeset`.

No new API or wire field is needed: `step.cache.write` and the `not-written` enum already exist. The emitted `.d.ts`, JSON Schema, and schema fixtures should therefore remain unchanged. Verify that assumption in the final diff.

## Verification before PR

Run from the monorepo root after `pnpm install`:

```sh
pnpm --filter e2e run build
pnpm --filter e2e exec vitest run tests/unit/trace-cache-config.test.ts
pnpm --filter e2e run test:unit
pnpm check
pnpm test
pnpm --filter @e2e-dev/testbed test
pnpm test:web-benchmark
```

The repository also asks for a main-vs-candidate `pnpm bench:ab` run when the runner changes. Select the deterministic suite that covers the touched runner/cache path and record the exact command actually used; do not claim it if skipped.

Behavior verification must compare the same standalone repro on main and the branch:

| case | main | branch |
| --- | --- | --- |
| healthy write | `saved` | `saved` |
| undefined write | `not-written` | `not-written` |
| thrown write | `undefined` | `not-written` |

Also verify the built CLI/full-runner fixture: one application commit, passing test, and `step.cache.write: not-written`. Unit tests alone are not the intended user-facing verification.

## PR requirements checked from upstream

- Conventional title: `fix(cache): report rejected recording writes`.
- `## Issue` contains `Fixes #<number>`; the community bot requires it for `fix`.
- `## Verified` contains real local evidence and a main-vs-branch table, not a lint/test laundry list.
- Add the patch changeset for the published package.
- Update docs in the same PR.
- Keep the description short and written from the final diff.
- Complete fresh-context review and upstream `ship-pr`/`babysit`; a later push requires re-earning the review label.

## Fork command sketch (only after authorization)

```sh
gh repo fork tester-army/e2e --clone=true
# Inside the fork checkout:
git remote add upstream https://github.com/tester-army/e2e.git
git fetch upstream
git switch -c codex/fix-cache-write-outcome upstream/main
```

Do not fork, branch, edit, push, or open the PR until the issue is filed and implementation is explicitly authorized.
