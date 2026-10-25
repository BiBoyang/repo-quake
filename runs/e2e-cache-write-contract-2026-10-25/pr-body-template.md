<!-- TEMPLATE ONLY. Replace every placeholder with final-diff facts and real output before use. -->

## What and why

- Preserve `not-written` when a confirmed recording's store write rejects.
- Keep cache persistence best-effort while making the existing report outcome visible.

## Issue

Fixes #<ISSUE_NUMBER>

## Verified

Ran it locally: <yes|no - reason; do not open a ready PR with unverified code>

- <Focused test run on main: failure evidence>
- <Same test on branch: passing evidence>
- <Built CLI/full-runner verification: one application commit and `write: not-written`>
- <Exact bench:ab command and result, or an explicit unverified reason>

| case | main | this branch |
| --- | --- | --- |
| thrown store write | `undefined` | <actual branch result> |

## Checklist

- [ ] Changeset added (`pnpm changeset`) for `e2e` patch.
- [ ] No breaking change; no new API or wire field.
- [ ] `docs/cache.mdx` updated in the same PR.
- [ ] Emitted `.d.ts` and report schema reviewed; unchanged because the field and enum already exist.
- [ ] Fresh-context review completed and all accepted critical/important findings resolved.
