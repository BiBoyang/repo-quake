# DISCLOSURE — e2e semantic cache and asynchronous commit audit (2026-10-25)

Measured nine full-runner cells against npm e2e 0.21.3 and @e2e-dev/web 0.15.3 using a deterministic executor and local Chrome.

**Estimate vs official.** Every result is a direct observation from our own local runs, one execution per cell. There are no organizer-measured numbers, model-derived estimates, or rates. Upstream main statements are source review only, not main-runtime measurements.

## 1. Access and contact

- Touched: local fixtures, copied cache entries, loopback HTTP, temporary Chrome profile, public npm package contents, and read-only public GitHub source/issue material during reporting review.
- Never touched: production applications, private/sealed data, real model providers, external telemetry, third-party writable state, upstream issues/PRs, or human subjects.
- Isolation: per-cell cache copies, fake HOME, headless temporary browser, no real model, and loopback-only app side effects. This was sufficient for the worst inducible behavior: duplicate writes only to the local event server.

## 2. Hash manifest

| artifact | sha256 / revision | note |
|---|---|---|
| target lockfile | 6e27c96b1463ea73e4f1cad902f88695c7e71d3af34064b5f61be42bc58960cf | e2e 0.21.3 and web 0.15.3 dependency pin |
| task contract | d5043eed003dea7b40e6b2d6c51614f21cddaea287a68eb776ef8721fa2a55f3 | frozen prompt, cells, expectations, invalid rules |
| fixture manifest | e0591499509b44e73813d04428b6358cc7ef502fa04b6b83f2a8feca7c0ff317 | hashes driver, grader, task, and fixture sources |
| C0 cache entry | 0778e1a1b9c3f0fe96efba46c9b56740f106df308634801b284febbf32fd92f0 | healthy seed for copied treatment caches |
| main source review | 69e123b17e04ed624df16d32f3b1ef95ce22c083 | main HEAD, read-only; not a main-runtime result |

## 3. Pre-registration and deviations

- Preregistration: `experiment-card.json` and `task-contract.txt`, validated before the nine executions.
- Deviations: `deviation-log.md`. Original U1 is invalid setup due to malformed EngineError construction; it was not replaced under this card.
- Corrected uncertain-commit work received a separate card at `../e2e-uncertain-verification-2026-10-25/`.

## 4. Integrity statements

1. No valid cell was selected, dropped, or relabeled after grading. Original U1 is visibly annotated `invalid setup`, not hidden or converted into a finding.
2. Environment/fixture failure count: one of nine, original U1. It remains in the execution denominator and outside valid product conclusions.
3. Contamination register: the healthy C0 seed remained on disk, but each treatment received only its configured copy. The deterministic executor could read browser state, params, and loopback witness only. Original U1 contamination is limited to that cell. N1 used a fresh healthy copy after the fault series.
4. Witness blind spots: one local async UI, one Chromium version, deterministic executor, no real provider/mobile/distributed store. The custom store proves one write seam, not every filesystem failure. Main was not rebuilt.

## 5. Posting gate

- [x] Upstream issue opened first: https://github.com/tester-army/e2e/issues/1371
- [x] Every reported number checked against primary artifacts
- [x] F1 conclusion independently re-verified by direct contract probe and standalone repro
- [x] Sample sizes and caveats stated
- [x] Contamination register reviewed; original U1 annotated
- [x] Repository evidence public on [codex/measurement-hardening](https://github.com/BiBoyang/repo-quake/tree/codex/measurement-hardening), after issue #1371 was created
