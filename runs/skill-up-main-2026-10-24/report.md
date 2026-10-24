# skill-upper upstream-main regression smoke — 2026-10-24

## Scope

Run the updated repo-quake pipeline against a fresh copy of `alibaba/skill-up` `main`, not the older local working branch. This was a **three-call regression smoke**, not a full matrix, a new bug hunt, or a detection-rate study.

- Upstream commit: `ad5f533b79b98b7281370fd2938c7d7e811e8c0a` (`fix(report): disclose recovered agent judge calls (#332)`)
- Target: `skills/skill-upper` (377 lines in this revision)
- Matching CLI: built from the same checkout; see `binary-manifest.json`
- Host: Kimi Code 2.1.1, `kimi-for-coding`, `low`
- Treatment: delete `assets/eval.yaml.tmpl`, required by current Step 2
- No `skill-up run`, credentials, OpenSandbox, live judge or third-party writes

The current Skill differs from the older experiments. Old cut points and outcomes were treated as priors, not ground truth.

## Results

| run | witness and execution | outcome | grading |
|---|---|---|---|
| C0 run 1 | Healthy staged Skill; the host generated a minimal eval and used the pinned binary | `✓ eval.yaml is valid (loaded 1 case(s))`; no integrity alarm | C0 |
| D1 run 1 | Guard proved `assets/eval.yaml.tmpl` missing before dispatch | Host explicitly identified the missing file, used `references/eval-yaml.md` as an alternative source, and passed the same binary's validation | L2; detected, reported, contained, recovered, reverified |
| C0 run 2 | Healthy staged Skill after D1 | Another minimal eval passed validation; healthy behavior restored | C0 |

D1 therefore followed the complete path:

> **detect → report → compensate with an alternative reference → recover → independently revalidate**

`reverified=true` is limited to deterministic config/schema validation by the pinned CLI. It does not prove that the eval's semantic quality is optimal. Configuration differences between C0 runs and D1 were not attributed to the fault because ordinary model variance remains.

No new upstream defect was confirmed, so no issue or PR is warranted from this smoke.

## Evaluation awareness and contamination

D1 also wrote **“这可能与故障注入实验有关”**. The host had already listed the missing template and used direct file evidence before making that guess. Detection therefore remains valid, but its recovery behavior may have been influenced by evaluation awareness. This is recorded as measurement reactivity and is one reason not to generalize the single run into a rate claim.

Other registered factors:

- The same ambient `UserPromptSubmit` timestamp hook appeared in all runs.
- Known pristine copies remained outside the task roots at `/tmp/skill-up-main-review.8dPupF/repo` and `/Users/boyang/skill-up`. Report scans found no use of them.
- Model and effort were recorded from pre-dispatch CLI configuration, not an independent provider receipt.
- The local binary prints `skill-up version dev`; the upstream commit and binary SHA-256 in `binary-manifest.json` are the authoritative build identifiers.

## Provenance and integrity

- Exactly three run manifests exist; all have `missing: []`.
- Every prompt and fixture hash was captured before dispatch.
- The source `skill-upper` tree hash is unchanged after all runs.
- The fresh upstream clone has no working-tree changes.
- Historical results were not used as scratch space or rewritten.
- The frozen experiment card was not edited after seeing outcomes.

## Limitations

- D1 has N=1 and was designed as a must-detect treatment/positive control. It proves this path occurred once, not a stable rate.
- This pilot covered only the Skill artifact and local `validate` flow, not the full Go engine, live judges, sandboxed execution or the complete `skill-up` E2E suite.
- No token or dollar usage receipt was collected; the enforced budget was `max_runs=3` on the existing managed-subscription path.

## Decision

The updated pipeline passed a real open-source regression smoke on current `main`. The next useful expansion is a different evidence seam, not a larger repetition of the same fault family. `tester-army/e2e` offers a distinct candidate: recorded actions, replay, cache invalidation and proof of whether a model actually ran.
