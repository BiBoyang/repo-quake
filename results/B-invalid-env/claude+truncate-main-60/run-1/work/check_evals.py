import json
import os

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "target", "evals")

with open(os.path.join(BASE, "evals.json")) as f:
    evals = json.load(f)

with open(os.path.join(BASE, "trigger_evals.json")) as f:
    triggers = json.load(f)

print("evals.json parses OK")
print("  skill_name   =", evals["skill_name"])
print("  n_evals      =", len(evals["evals"]))
print("  n_assertions =", sum(len(e["assertions"]) for e in evals["evals"]))
print("  ids          =", [e["id"] for e in evals["evals"]])
print("  keys used    =", sorted({k for e in evals["evals"] for k in e}))
print("trigger_evals.json parses OK")
print("  total =", len(triggers))
print("  should_trigger     =", sum(1 for q in triggers if q["should_trigger"]))
print("  should_not_trigger =", sum(1 for q in triggers if not q["should_trigger"]))

ids = [e["id"] for e in evals["evals"]]
assert ids == list(range(1, len(ids) + 1)), "ids must be 1..N with no gaps"
for e in evals["evals"]:
    for field in ("id", "prompt", "expected_output", "files", "assertions"):
        assert field in e, "eval %s missing %s" % (e["id"], field)
    assert e["assertions"], "eval %s has no assertions" % e["id"]
print("structural checks passed")
