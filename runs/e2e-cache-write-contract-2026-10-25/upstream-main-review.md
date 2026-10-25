# Upstream main review (read-only)

Reviewed on 2026-10-25 using the GitHub API. No upstream state was changed.

- File: `packages/e2e/src/cache/context.ts` on `tester-army/e2e` main.
- Main HEAD when retrieved: `69e123b17e04ed624df16d32f3b1ef95ce22c083`, dated 2026-10-23T19:31:37Z.
- Latest commit returned for `context.ts`: `689620d728d04202757ffd11ed001b512b68044a`, dated 2026-10-22T15:57:15Z.
- Main-HEAD permalink: https://github.com/tester-army/e2e/blob/69e123b17e04ed624df16d32f3b1ef95ce22c083/packages/e2e/src/cache/context.ts#L188-L223
- Documentation permalink: https://github.com/tester-army/e2e/blob/69e123b17e04ed624df16d32f3b1ef95ce22c083/docs/cache.mdx#L48-L57

The retrieved main source still has the same structure as the pinned npm runtime:

```ts
const written = await context.store.write(entry.keyHash, entry.trace);
outcomes.set(entry.stepIndex, written === undefined ? 'not-written' : 'saved');
// ...
} catch {
  // The cache is disposable; a failed flush is a slower next run only.
}
```

Thus a rejected write can still leave no outcome by inspection on main. The direct runtime probe itself used npm `e2e@0.21.3`; main was source-inspected, not rebuilt or executed.

Related issue review:

- https://github.com/tester-army/e2e/issues/939 introduced the cache-outcome report so automation could tell what settlement did; a missing outcome removes that signal.
- https://github.com/tester-army/e2e/issues/1363 asks the console Cache summary to count explicit `unconfirmed`, `no-change`, and `not-written` outcomes.
- The present case is different: a thrown write has **no outcome at all**, so a tally of existing outcomes cannot expose it.
- Searches for `cache write throw` and `"store.write"` returned no matching issue on 2026-10-25. The `not-written` search found #939, #1363, and unrelated documentation history; none duplicates the rejected-write case.

Two attempts to download the large upstream unit-test file failed with TLS handshake timeouts. No claim is made about the presence or absence of an upstream regression test; the successfully retrieved main implementation is sufficient for the source-level scope above.
