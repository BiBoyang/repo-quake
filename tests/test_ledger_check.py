import contextlib
import copy
import importlib.machinery
import importlib.util
import io
import json
import re
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
SCHEMA = ROOT / "ledger/SCHEMA.md"


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
            "issue status from the pr table": (
                lambda d: d["entries"][0]["upstream"][0].update(status="merged"),
                "'merged' not in ['closed-fixed', 'closed-stale', 'none', 'open'] for kind 'issue'",
            ),
            "retired v1 issue status": (
                lambda d: d["entries"][0]["upstream"][0].update(status="closed-unmerged"),
                "for kind 'issue'",
            ),
            "pr status from the issue table": (
                lambda d: d["entries"][0]["upstream"][1].update(status="closed-fixed"),
                "'closed-fixed' not in ['closed-unmerged', 'merged', 'none', 'open'] for kind 'pr'",
            ),
            "status unknown to every table": (
                lambda d: d["entries"][0]["upstream"][0].update(kind="ticket", status="done"),
                "'done' not in",
            ),
            "wrong version": (lambda d: d.update(version=1), "'version' must be the integer 2"),
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

    def test_v11_enums_accept_every_documented_value(self):
        issue_statuses = {"open", "closed-fixed", "closed-stale", "none"}
        pr_statuses = {"open", "merged", "closed-unmerged", "none"}
        self.assertEqual(checker.UPSTREAM_STATUSES, {"issue": issue_statuses, "pr": pr_statuses})
        self.assertIn("on-path-no-gap", checker.PATH_RELATIONS)
        for relation in sorted(checker.PATH_RELATIONS):
            for issue_status, pr_status in zip(sorted(issue_statuses), sorted(pr_statuses)):
                with self.subTest(relation=relation, issue=issue_status, pr=pr_status):
                    doc = copy.deepcopy(self.doc)
                    first = doc["entries"][0]
                    first["fault"]["path_relation"] = relation
                    first["upstream"][0]["status"] = issue_status
                    first["upstream"][1]["status"] = pr_status
                    errors, _ = checker.validate(doc, ROOT)
                    self.assertEqual(errors, [])

    def test_v11_migrations_are_in_the_live_ledger(self):
        self.assertEqual(self.doc["version"], 2)
        entries = {e["id"]: e for e in self.doc["entries"]}
        upstream = {u["url"].rsplit("/", 1)[-1]: u for u in entries["RQ-F-001"]["upstream"]}
        self.assertEqual((upstream["1371"]["kind"], upstream["1371"]["status"]), ("issue", "closed-fixed"))
        self.assertEqual((upstream["1372"]["kind"], upstream["1372"]["status"]), ("pr", "merged"))
        self.assertEqual(entries["RQ-F-006"]["fault"]["path_relation"], "on-path-no-gap")

    def test_schema_doc_stays_in_sync_with_the_checker(self):
        text = SCHEMA.read_text(encoding="utf-8")
        self.assertIn(f'"version": {checker.SCHEMA_VERSION}', text)
        for value in sorted(checker.PATH_RELATIONS):
            self.assertIn(f"| `{value}` |", text)
        for kind, statuses in checker.UPSTREAM_STATUSES.items():
            self.assertIn(f"`kind: {kind}` 的 `status`", text)
            for status in sorted(statuses):
                self.assertIn(f"| `{status}` |", text)
        # Every complete entry example in SCHEMA.md must itself pass the checker.
        blocks = re.findall(r"```json\n(\{.*?\})\n```", text, re.S)
        examples = [json.loads(b) for b in blocks if '"id"' in b]
        self.assertGreaterEqual(len(examples), 2)
        doc = {"version": checker.SCHEMA_VERSION, "updated": "2026-10-30", "entries": examples}
        errors, _ = checker.validate(doc, ROOT)
        self.assertEqual(errors, [])

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
