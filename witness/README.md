# Witnesses

The instruments the phases used: mechanical checkers, mocks, fakes and drivers.
Each family has its own directory and README (in Chinese).

| directory | phases | what it observes | entry point | tests |
|---|---|---|---|---|
| [integrity/](integrity/README.md) | 0, 1, 1′, 2 | file and skill integrity faults on an agent directory, a Python project and examiner skills; guards check each staged copy before a host sees it | `run_matrix.sh`, `run_matrix_py.sh`, `run_phase2.sh` (as run then) | through the factorial dry-run |
| [factorial/](factorial/README.md) | prepared, not run | wound path_relation × shell × model on `targets/greeting-agent` | `run_factorial.sh --dry-run` | `tests/test_factorial_materials.py`, `[factorial-dry-run]` |
| [stream-retry/](stream-retry/README.md) | 4, 5 | what the screen and the saved conversation hold after a stream drops and the client retries; a loopback mock for three wire protocols, raw terminal bytes, version witnesses | `runner.py` | `tests/test_stream_retry.py` |
| [stall/](stall/README.md) | 6 | whether an interactive client bounds and names a wait on a dependency that answers late or never; loopback fakes and a timestamped pty | `stall.py` | `tests/test_stall.py` |

Shared tooling lives with the method skill, not in a witness:

- `skills/repo-quake/scripts/validate_card.py` checks an experiment card.
- `skills/repo-quake/scripts/card_gate.py` refuses a counted matrix that the card
  does not cover (used by `stream-retry` and `stall`).
- `skills/repo-quake/scripts/audit_artifacts.py` audits a public evidence copy
  before it is committed.
- `skills/skill-quake/scripts/write_meta.py` writes per-run provenance and
  content hashes (used by `factorial`).

Until 2026-11-21 the `integrity/` files sat at the top of `witness/`, and
`card_gate.py` sat in `stream-retry/`. Records written before then use those
paths.
