"""Local sanity check for the generated skill-up eval YAML files."""
import glob
import os
import sys

root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "target")
root = os.path.normpath(root)

try:
    import yaml
except ImportError:
    print("PyYAML NOT AVAILABLE - cannot parse-check")
    sys.exit(0)

files = [os.path.join(root, "evals/eval.yaml")]
files += sorted(glob.glob(os.path.join(root, "evals/cases/*.yaml")))

eval_cfg = None
ok = True
for f in files:
    rel = os.path.relpath(f, root)
    try:
        with open(f, encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        print("OK   %s | keys: %s" % (rel, sorted(data.keys())))
        if rel == "evals/eval.yaml":
            eval_cfg = data
    except Exception as e:  # noqa: BLE001
        ok = False
        print("FAIL %s | %s" % (rel, e))

if eval_cfg:
    listed = set(eval_cfg.get("cases", {}).get("files", []))
    present = {
        os.path.relpath(f, root) for f in glob.glob(os.path.join(root, "evals/cases/*.yaml"))
    }
    missing = sorted(listed - present)
    unlisted = sorted(present - listed)
    print("\ncases.files entries: %d, case files on disk: %d" % (len(listed), len(present)))
    print("listed but missing:", missing)
    print("on disk but not listed:", unlisted)

    # Case id must equal the filename stem.
    for f in sorted(glob.glob(os.path.join(root, "evals/cases/*.yaml"))):
        with open(f, encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        stem = os.path.splitext(os.path.basename(f))[0]
        if data.get("id") != stem:
            ok = False
            print("ID MISMATCH: %s has id=%r" % (f, data.get("id")))

    # judge type must be one of the documented options.
    allowed = {"rule_based", "agent_judge", "script"}
    for f in sorted(glob.glob(os.path.join(root, "evals/cases/*.yaml"))):
        with open(f, encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        jtype = (data.get("judge") or {}).get("type")
        if jtype not in allowed:
            ok = False
            print("BAD JUDGE TYPE: %s -> %r" % (f, jtype))
        if jtype == "script":
            sp = (data.get("judge") or {}).get("script_path")
            target = os.path.join(root, sp or "")
            if not os.path.isfile(target):
                ok = False
                print("SCRIPT MISSING: %s -> %s" % (f, sp))
            else:
                print("script_path resolves: %s" % sp)

print("\nRESULT:", "ALL CHECKS PASSED" if ok else "PROBLEMS FOUND")
sys.exit(0 if ok else 1)
