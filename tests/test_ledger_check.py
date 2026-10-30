import contextlib
import copy
import importlib.machinery
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
MODULE_PATH = ROOT / "bin/ledger-check"
LOADER = importlib.machinery.SourceFileLoader("quake_ledger_check", str(MODULE_PATH))
SPEC = importlib.util.spec_from_loader("quake_ledger_check", LOADER)
checker = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(checker)
LEDGER = ROOT / "ledger/ledger.json"


def run_main(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        rc = checker.main(argv)
    return rc, out.getvalue()


def write_copy(tmp, doc, name="ledger.json"):
    path = Path(tmp) / name
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    return path


class LedgerCheckTests(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads(LEDGER.read_text(encoding="utf-8"))

    def test_live_ledger_is_valid(self):
        errors, summary = checker.validate(self.doc, ROOT)
        self.assertEqual(errors, [])
        self.assertEqual(summary["entries"], len(self.doc["entries"]))
        self.assertGreaterEqual(summary["entries"], 1)
        rc, out = run_main([str(LEDGER)])
        self.assertEqual(rc, 0, out)
        self.assertIn("OK", out)

    def test_minimal_entries_only_need_the_narrow_required_fields(self):
        doc = copy.deepcopy(self.doc)
        doc["entries"].append({
            "id": "RQ-X-999", "created": "2026-10-30", "phase": "phase1",
            "class": "experiment-invalid", "title": "最小效度条目", "status": "n-a",
            "evidence": ["docs/phase1-report.md"], "lesson": "可选字段缺省也应通过",
        })
        doc["entries"].append({
            "id": "RQ-I-999", "created": "2026-10-30", "phase": "phase2",
            "class": "instrument-defect", "title": "最小仪器条目", "status": "open",
            "target": {"repo": "BiBoyang/repo-quake", "artifact": "bin/skill-guard"},
            "evidence": ["bin/skill-guard"], "lesson": "I 类只多一个 target",
        })
        errors, summary = checker.validate(doc, ROOT)
        self.assertEqual(errors, [])
        self.assertEqual(summary["by_class"]["X"], sum(1 for e in doc["entries"] if e["class"] == "experiment-invalid"))

    def test_broken_copies_fail_with_readable_errors(self):
        first = self.doc["entries"][0]

        def cell(**overrides):
            base = {"host": "kimi", "runs": 8, "detected": 0}
            base.update(overrides)
            return [base]

        cases = {
            "duplicate id": (lambda d: d["entries"].append(copy.deepcopy(first)), "duplicate id"),
            "bad id format": (lambda d: d["entries"][0].update(id="RQ-F-1"), "does not match ^RQ-"),
            "id letter vs class": (lambda d: d["entries"][0].update(id="RQ-X-001"), "does not match class"),
            "unknown status": (lambda d: d["entries"][0].update(status="closed"), "'closed' not in"),
            "experiment-invalid needs n-a": (
                lambda d: d["entries"][0].update(id="RQ-X-001", **{"class": "experiment-invalid"}),
                "must use 'n-a'",
            ),
            "n-a reserved": (lambda d: d["entries"][0].update(status="n-a"), "reserved for experiment-invalid"),
            "missing lesson": (lambda d: d["entries"][0].pop("lesson"), "missing required field 'lesson'"),
            "unknown field": (lambda d: d["entries"][0].update(evidense=["x"]), "unknown field 'evidense'"),
            "missing evidence path": (lambda d: d["entries"][0].update(evidence=["docs/does-not-exist.md"]), "does not exist"),
            "absolute evidence path": (lambda d: d["entries"][0].update(evidence=["/etc/hosts"]), "repo-root-relative"),
            "empty evidence": (lambda d: d["entries"][0].update(evidence=[]), "non-empty array"),
            "detected > runs": (lambda d: d["entries"][0].update(cells=cell(detected=9)), "detected 9 > runs 8"),
            "levels count": (lambda d: d["entries"][0].update(cells=cell(levels="L0,L0")), "2 segment(s) but runs = 8"),
            "levels vs detected": (
                lambda d: d["entries"][0].update(cells=cell(runs=2, levels="L2,L0")),
                "1 L2/L3 segment(s) but detected = 0",
            ),
            "bad level token": (lambda d: d["entries"][0].update(cells=cell(runs=2, levels="L0,L9")), "must be L0..L3"),
            "runs zero": (lambda d: d["entries"][0].update(cells=cell(runs=0)), "runs: must be an integer > 0"),
            "bad date": (lambda d: d["entries"][0].update(created="2026-13-01"), "not a real calendar date"),
            "date format": (lambda d: d["entries"][0].update(created="2026/10/30"), "is not YYYY-MM-DD"),
            "bad phase": (lambda d: d["entries"][0].update(phase="Phase 1"), "lowercase letters"),
            "missing target on F": (lambda d: d["entries"][0].pop("target"), "require 'target'"),
            "missing fault on F": (lambda d: d["entries"][0].pop("fault"), "require 'fault'"),
            "missing attribution on F": (lambda d: d["entries"][0].pop("attribution"), "require 'attribution'"),
            "bad confidence": (lambda d: d["entries"][0]["attribution"].update(confidence="sure"), "'sure' not in"),
            "bad primary factor": (lambda d: d["entries"][0]["attribution"].update(primary_factor="luck"), "'luck' not in"),
            "bad path relation": (lambda d: d["entries"][0]["fault"].update(path_relation="sideways"), "'sideways' not in"),
            "observation not bool": (lambda d: d["entries"][0].update(observation={"detected": "yes"}), "must be true or false"),
            "observation needs detected": (lambda d: d["entries"][0].update(observation={"reported": True}), "missing required field 'detected'"),
            "bad upstream kind": (lambda d: d["entries"][0]["upstream"][0].update(kind="ticket"), "'ticket' not in"),
            "bad upstream url": (lambda d: d["entries"][0]["upstream"][0].update(url="github.com/x"), "not an http(s) URL"),
            "bad upstream status": (lambda d: d["entries"][0]["upstream"][0].update(status="done"), "'done' not in"),
            "wrong version": (lambda d: d.update(version=2), "'version' must be the integer 1"),
            "entries not a list": (lambda d: d.update(entries={}), "'entries' must be an array"),
        }
        with tempfile.TemporaryDirectory() as tmp:
            for name, (mutate, expected) in cases.items():
                with self.subTest(case=name):
                    doc = copy.deepcopy(self.doc)
                    mutate(doc)
                    path = write_copy(tmp, doc, f"{name.replace(' ', '-')}.json")
                    rc, out = run_main([str(path), "--root", str(ROOT)])
                    self.assertEqual(rc, 1, out)
                    self.assertIn(expected, out)
                    self.assertIn("FAIL", out)

    def test_root_override_controls_evidence_lookup(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_copy(tmp, self.doc)
            rc, out = run_main([str(path), "--root", tmp])
            self.assertEqual(rc, 1, out)
            self.assertIn("does not exist", out)
            rc, out = run_main([str(path), "--root", str(ROOT)])
            self.assertEqual(rc, 0, out)

    def test_invalid_json_and_missing_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            broken = Path(tmp) / "broken.json"
            broken.write_text('{"version": 1, "entries": [', encoding="utf-8")
            rc, out = run_main([str(broken), "--root", str(ROOT)])
            self.assertEqual(rc, 1, out)
            self.assertIn("invalid JSON", out)
            rc, out = run_main([str(Path(tmp) / "missing.json"), "--root", str(ROOT)])
            self.assertEqual(rc, 2, out)
            rc, out = run_main([str(LEDGER), "--root", str(Path(tmp) / "no-such-root")])
            self.assertEqual(rc, 2, out)


if __name__ == "__main__":
    unittest.main()
