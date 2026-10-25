# DISCLOSURE — cache write-throw settlement contract (2026-10-25)

Measured three direct settlement calls against npm e2e 0.21.3, with healthy and undefined-return controls before a thrown write.

**Estimate vs official.** All runtime outputs are direct local observations, one invocation per cell. Upstream main is a read-only source review at the recorded revision, not an executed or official measurement.

## 1. Access and contact

- Touched: in-memory stores and traces, pinned local package code, standalone repro, and read-only public GitHub source, documentation, templates, and issues.
- Never touched: production, private/sealed sets, real model/provider, third-party writable state, upstream issue/PR trackers in write mode, or human subjects.
- Isolation: each cell received a fresh in-memory context and store. The standalone repro used the same pinned package and no filesystem cache or network. No broader isolation was needed for these side-effect-free calls.

## 2. Hash manifest

| artifact | sha256 / revision | note |
|---|---|---|
| target lockfile | 6e27c96b1463ea73e4f1cad902f88695c7e71d3af34064b5f61be42bc58960cf | npm e2e 0.21.3 pin |
| task contract | 9c7e98137a18a8310ad567799f64efb26b6e83397179d93be0a0e04d5998dc90 | frozen three-cell expectations and controls |
| fixture manifest | 11c46c83830052a5a16b4897233a119d7c9ac23ab5e605f2cc3fd3c4b71975e6 | probe, package pin, and task hashes |
| standalone repro | 969f13c601e78366fdefd725c9f171393220aefcae9d891baa988e0f5b92ac58 | independently rerun for publication |
| upstream main source | 69e123b17e04ed624df16d32f3b1ef95ce22c083 | main HEAD; context.ts and docs/cache.mdx review |

## 3. Pre-registration and deviations

- Preregistration: `experiment-card.json` and `task-contract.txt`, validated before three invocations.
- C0 and C1 passed their frozen control expectations before T1 ran. There were no setup failures, retries, or preregistration deviations.
- The standalone repro was a publication re-verification, not a new measured cell and not a replacement for T1.

## 4. Integrity statements

1. No cell was selected, dropped, or relabeled after grading. T1 remains a failed preregistered expectation and is the finding.
2. Environment failures: zero of three. The deliberate T1 store throw is target behavior under test, not scaffolding failure.
3. Contamination register: fresh context/store per cell prevents shared staged state. Full-browser F1 is independent cross-evidence; original malformed U1 is unrelated and excluded.
4. Witness blind spots: direct internal-function probe plus one full-runner custom-store fixture, not every store implementation. Main source was inspected but not built. Upstream unit-test coverage is not claimed from failed downloads; a later successful read located the appropriate settlement suites for PR planning.

## 5. Posting gate

- [x] Upstream issue opened first: https://github.com/tester-army/e2e/issues/1371
- [x] Every number re-checked against primary outputs
- [x] Most striking conclusion re-verified by standalone `upstream-repro/repro.mjs`
- [x] One-per-cell sample and main-runtime caveat stated
- [x] Contamination register reviewed; no affected valid cell hidden
- [ ] Repository/artifacts public (issue body is self-contained; evidence push waits until after issue creation)
