# DISCLOSURE — focused real-browser uncertain-commit verification (2026-10-25)

Measured two cells against npm e2e 0.21.3 and @e2e-dev/web 0.15.3 using the archived healthy C0 seed and a corrected EngineError fixture.

**Estimate vs official.** All results are direct local observations, one execution per cell. No rates, model estimates, or official/upstream runtime numbers are claimed.

## 1. Access and contact

- Touched: archived seed copy, local fixture copies, loopback app/event server, temporary Chrome, and the real pinned web engine.
- Never touched: production, private data, real model/provider, external telemetry, third-party writes, or human subjects.
- Isolation: per-cell seed copies, fake HOME, loopback-only side effects, and one deterministic post-tap fault. The worst behavior was a duplicate write to the local witness, which the valid U1 did not produce.

## 2. Hash manifest

| artifact | sha256 / revision | note |
|---|---|---|
| target lockfile | 6e27c96b1463ea73e4f1cad902f88695c7e71d3af34064b5f61be42bc58960cf | same target pin as original C0 |
| archived seed entry | 0778e1a1b9c3f0fe96efba46c9b56740f106df308634801b284febbf32fd92f0 | copied from healthy C0 evidence |
| task contract | 1c237cba629e5ec1c103e19be7def29a13423d60f26eab38fa9d322cb0a3b7ed | two-cell corrected verification contract |
| fixture manifest | b637182735338a9c4cac4af0685a18ad83e456e93841358259bc0e99855df6d7 | includes corrected engine, driver, grader, and seed |
| checker output | results/matrix.json + results/adjudication.json | initial output retained; correction separate |

## 3. Pre-registration and deviations

- Preregistration: `experiment-card.json` and `task-contract.txt`, validated before two executions.
- Deviation/adjudication: `deviation-log.md`. The initial grader wrongly required `mode=missed`; primary artifacts support `agent-concluded/action-uncertain`.
- No preregistration, raw result, budget, or initial matrix was edited after execution.

## 4. Integrity statements

1. No cell was dropped or relabeled to manufacture a pass. The grader implementation error is public in the run's own deviation log and adjudication.
2. Environment/fixture failures: none in this focused card. The earlier malformed U1 remains in the original run, not rewritten as a success here.
3. Contamination register: both cells used separate copies of the same archived healthy seed. N1 establishes healthy replay after U1. No executor access to pristine fixture sources was needed.
4. Witness blind spots: one async commit window, deterministic verification policy, one browser, no model/provider/mobile/distributed backend, and no independent re-recording in this focused card.

## 5. Posting gate

- [x] No upstream defect finding from U1/N1; no new issue required for these valid outcomes
- [x] Counts checked against primary artifacts
- [x] Most important conclusion re-read from report, fault log, executor prefix, DOM, and server ledger
- [x] Sample sizes and caveats stated
- [x] Grader contamination/correction disclosed
- [ ] Repository evidence made public (will accompany the related evidence push)
