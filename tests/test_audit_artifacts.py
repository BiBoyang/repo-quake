import contextlib
import importlib.util
import io
import json
import os
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "skills/repo-quake/scripts/audit_artifacts.py"
SPEC = importlib.util.spec_from_file_location("quake_audit_artifacts", MODULE_PATH)
auditor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(auditor)


class AuditArtifactsTests(unittest.TestCase):
    def test_healthy_evidence_and_redaction_placeholders_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "results").mkdir()
            (root / "README.md").write_text("password is a field name; modelTokens: 0\n", encoding="utf-8")
            (root / "results/report.json").write_text('{"observed":"<secret:token>"}\n', encoding="utf-8")
            (root / "results/.gitattributes").write_text("*.log whitespace=-blank-at-eof\n", encoding="utf-8")
            report = auditor.audit(root)
            self.assertTrue(report["ok"])
            self.assertEqual(report["files"], 3)
            self.assertEqual(report["issues"], [])
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = auditor.main(["--json", str(root)])
            self.assertEqual(rc, 0)
            self.assertTrue(json.loads(output.getvalue())["ok"])

    def test_symlink_is_rejected_by_type_without_following_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "run"
            outside = Path(tmp) / "outside"
            root.mkdir()
            outside.mkdir()
            (outside / "package.json").write_text("{}\n", encoding="utf-8")
            os.symlink(outside, root / "node_modules")
            report = auditor.audit(root)
            self.assertFalse(report["ok"])
            self.assertEqual([issue["code"] for issue in report["issues"]], ["SYMLINK"])
            self.assertEqual(report["issues"][0]["path"], "node_modules")

    def test_runtime_directories_are_rejected_without_descending(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ["node_modules", "chrome-profile", "runtime", "home", "bin", "__pycache__", ".stage", ".e2e", "cache-A"]:
                (root / name).mkdir()
                (root / name / "artifact").write_text("runtime\n", encoding="utf-8")
            report = auditor.audit(root)
            self.assertFalse(report["ok"])
            self.assertEqual(len(report["issues"]), 9)
            self.assertTrue(all(issue["code"] == "FORBIDDEN_DIR" for issue in report["issues"]))
            self.assertEqual(report["files"], 0)

    def test_forbidden_filenames_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            names = [".env", ".env.local", "id_rsa", "cert.pem", "key.key", "run.pid", "chrome.log", "chrome-error.log", ".salt", "cert.p12"]
            for name in names:
                (root / name).write_text("not scanned\n", encoding="utf-8")
            report = auditor.audit(root)
            self.assertEqual(len(report["issues"]), len(names))
            self.assertTrue(all(issue["code"] == "FORBIDDEN_FILE" for issue in report["issues"]))

    def test_high_confidence_secret_shapes_are_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "github.txt").write_text("ghp_" + "a" * 20 + "\n", encoding="utf-8")
            (root / "api.txt").write_text("sk-" + "b" * 20 + "\n", encoding="utf-8")
            (root / "auth.txt").write_text("Authorization: Bearer " + "c" * 24 + "\n", encoding="utf-8")
            (root / "private.txt").write_text("-----BEGIN " + "OPENSSH PRIVATE KEY-----\n", encoding="utf-8")
            (root / "safe.md").write_text("<secret:token> and modelTokens: 0\n", encoding="utf-8")
            report = auditor.audit(root)
            self.assertEqual(len(report["issues"]), 4)
            self.assertTrue(all(issue["code"] == "SECRET" for issue in report["issues"]))
            self.assertNotIn("safe.md", [issue["path"] for issue in report["issues"]])

    def test_audit_root_symlink_is_a_usage_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            actual = Path(tmp) / "actual"
            link = Path(tmp) / "link"
            actual.mkdir()
            os.symlink(actual, link)
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(auditor.main([str(link)]), 2)

    def test_missing_root_is_a_usage_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing"
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(auditor.main([str(missing)]), 2)


if __name__ == "__main__":
    unittest.main()
