## What and why

- Preserve `not-written` when a confirmed staged recording's store write rejects instead of omitting `step.cache.write`.
- Keep settlement best-effort: a later healthy entry still settles, and `keep`, eviction, and unconfirmed outcomes are unchanged.
- Document that a rejected write is a `not-written` outcome.

## Issue

Fixes #1371

## Verified

Ran it locally: yes

- Added the regression test on `upstream/main` first: it failed with `expected undefined to be 'not-written'`; the other 26 tests in the file passed. With the fix, all 27 pass.
- Built-runner fixture with a rejected custom-store write: the test passed, the executor ran once with two taps and final count 2, `step.cache.write` was `not-written`, and the report passed report-1 schema validation.

| case | upstream/main | this branch |
| --- | --- | --- |
| healthy write | `saved` | `saved` |
| undefined write | `not-written` | `not-written` |
| thrown write | `undefined` | `not-written` |

- `pnpm bench:ab --base upstream/main --suite testbed --threshold 3 -- tests/forms.e2e.ts`: 20 pairs; behavior, step sequences, and counters matched on both builds. Timing was unresolved, so no performance claim.
- Node 22.22.3: `pnpm check` and the full `pnpm test` passed. Built-CLI testbed passed 79 tests with 1 skipped; web-benchmark passed all 91 tests.

## Checklist

- [x] Changeset added: `e2e` patch.
- [x] No breaking change, public API change, or wire-schema change.
- [x] `docs/cache.mdx` updated in the same PR.
- [x] Emitted `.d.ts`, `tests/types/sdk-types.ts`, report schema, and fixtures reviewed; unchanged because `not-written` already exists.
