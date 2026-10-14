import glob
import os
import sys

try:
    import yaml
except ImportError:
    print("PyYAML not available")
    sys.exit(2)

root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "target")
ok = True
for path in sorted(glob.glob(os.path.join(root, "evals", "**", "*.yaml"), recursive=True)):
    try:
        with open(path, encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except Exception as exc:  # noqa: BLE001
        ok = False
        print("PARSE FAIL %s: %s" % (path, exc))
        continue
    rel = os.path.relpath(path, root)
    if rel.startswith("evals/cases/"):
        cid = data.get("id")
        expected = os.path.basename(path)[:-5]
        judge_type = (data.get("judge") or {}).get("type")
        print("%s id=%s (filename match=%s) judge=%s" % (rel, cid, cid == expected, judge_type))
    else:
        print("%s keys=%s" % (rel, sorted(data.keys())))
        for case_file in data["cases"]["files"]:
            full = os.path.join(root, case_file)
            exists = os.path.isfile(full)
            if not exists:
                ok = False
            print("   case file %s exists=%s" % (case_file, exists))
        for case_file in data["cases"]["files"]:
            with open(os.path.join(root, case_file), encoding="utf-8") as fh:
                yaml.safe_load(fh)
        for case_file in data["cases"]["files"]:
            with open(os.path.join(root, case_file), encoding="utf-8") as fh:
                case = yaml.safe_load(fh)
            sp = ((case.get("judge") or {}).get("script_path"))
            if sp:
                print("   script_path %s exists=%s" % (sp, os.path.isfile(os.path.join(root, sp))))

print("ALL OK" if ok else "PROBLEMS FOUND")
