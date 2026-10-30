"""phase3 factorial materials (witness/factorial/): dry-run coverage, zero host calls.

The dry-run is the pre-fire gate: it must be green on the live repo, refuse to
fire, never write under targets/, and turn red on a drifted card, an edited
prereg file, a host invocation in either script, or an enabled host entry.
"""
import importlib.machinery
import importlib.util
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).parents[1]
FACTORIAL = REPO / "witness/factorial"
DRIVER = FACTORIAL / "run_factorial.sh"
GENERATOR = FACTORIAL / "gen_materials.sh"
SALT = "0123456789abcdef0123456789abcdef"
WOUNDS = ("W1", "W2", "W3", "W4", "W5")
HOST_CELLS = ("kimi-kfc", "kimi-k3", "codex-kfc", "codex-k3")
WORKSPACE = (
    "targets/greeting-agent", "witness/eve_guard.py", "witness/run_matrix.sh", "witness/factorial",
    "bin/skill-guard", "bin/ledger-check", "ledger/ledger.json",
    "skills/skill-quake/scripts/write_meta.py", "skills/repo-quake/scripts/validate_card.py",
)
# Written independently of the driver's own audit patterns.
HOST_INVOCATION = (
    re.compile(r"(?<![\w./-])(?:kimi|codex)\s+(?:-{1,2}\w|exec\b|e\b|run\b|chat\b)"),
    re.compile(r"\b(?:command\s+-v|which|exec)\s+(?:kimi|codex)\b"),
    re.compile(r"(?<![\w-])(?:curl|wget)\s+\S"),
)


def load(name, path):
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    module = importlib.util.module_from_spec(importlib.util.spec_from_loader(name, loader))
    loader.exec_module(module)
    return module


ledger_check = load("factorial_ledger_check", REPO / "bin/ledger-check")
write_meta = load("factorial_write_meta", REPO / "skills/skill-quake/scripts/write_meta.py")
card_validator = load("factorial_validate_card", REPO / "skills/repo-quake/scripts/validate_card.py")


def run_driver(driver, roots, *args, extra_env=None):
    env = dict(os.environ, RQ_FACTORIAL_SALT=SALT, RQ_FACTORIAL_META=str(roots / "meta"),
               RQ_FACTORIAL_STAGE=str(roots / "stage"))
    env.update(extra_env or {})
    return subprocess.run(["bash", str(driver), *args], capture_output=True, text=True, env=env, timeout=600)


def make_workspace(root):
    for rel in WORKSPACE:
        src, dst = REPO / rel, root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__"))
        else:
            shutil.copy2(src, dst)
    return root / "witness/factorial/run_factorial.sh"


def front_matter(path):
    head = path.read_text(encoding="utf-8").split("---\n")[1]
    return dict(re.findall(r"^([a-z_]+): (.+)$", head, re.M))


def phase1_prompt():
    text = (REPO / "witness/run_matrix.sh").read_text(encoding="utf-8")
    body = re.search(r'cat > "\$3" <<EOF\n(.*?)\nEOF\n', text, re.S).group(1)
    return body + "\n"


class FactorialMaterialsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.roots = cls.tmp / "full"
        cls.source_before = write_meta.tree_hash(str(REPO / "targets/greeting-agent"))
        cls.full = run_driver(DRIVER, cls.roots, "--dry-run")
        cls.meta = Path(os.path.realpath(cls.roots / "meta"))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    # --- material sections: independent of the prereg files -----------------

    def test_material_sections_are_green(self):
        for section in ("materials", "registry", "cards", "witness", "prompt", "plan", "runs", "audit"):
            with self.subTest(section=section):
                self.assertIn(f"ok   [{section}]", self.full.stdout, self.full.stdout + self.full.stderr)

    def test_material_tree_is_complete_and_recomputable(self):
        registry = json.loads((self.meta / "registry.json").read_text(encoding="utf-8"))
        self.assertEqual(set(registry["variants"]), {"C0", *WOUNDS})
        self.assertEqual(registry["variants"]["C0"]["tree_sha256"], registry["source"]["tree_sha256"])
        for variant, item in registry["variants"].items():
            with self.subTest(variant=variant):
                self.assertEqual(write_meta.tree_hash(str(self.meta / item["dir"])), item["tree_sha256"])
        plan = json.loads((self.meta / "runs/plan.json").read_text(encoding="utf-8"))
        self.assertEqual(len(plan["rows"]), 168)
        self.assertEqual(len((self.meta / "runs/plan.tsv").read_text(encoding="utf-8").splitlines()), 169)
        for row in plan["rows"]:
            run_dir = self.meta / "runs" / row["run_id"]
            meta = json.loads((run_dir / "meta.json").read_text(encoding="utf-8"))
            self.assertTrue((run_dir / "prompt.txt").is_file() and (run_dir / "guard.json").is_file())
            self.assertEqual(meta["fixture_sha256"], registry["variants"][row["wound"]]["tree_sha256"])
            self.assertEqual(meta["dispatch"]["status"], "not-dispatched")
            self.assertTrue(all(not Path(p).is_absolute() for p in meta["artifacts"].values()))
        self.assertFalse((self.roots / "stage").exists(), "staging must be removed after the rehearsal")

    def test_targets_stay_untouched(self):
        self.assertEqual(write_meta.tree_hash(str(REPO / "targets/greeting-agent")), self.source_before)
        status = subprocess.run(["git", "status", "--porcelain", "--", "targets"], cwd=REPO,
                                capture_output=True, text=True)
        if status.returncode == 0:
            self.assertEqual(status.stdout, "")

    def test_prompts_are_phase1_verbatim_and_opaque(self):
        expected = phase1_prompt()
        plan = json.loads((self.meta / "runs/plan.json").read_text(encoding="utf-8"))
        stage_root = plan["stage_root"]
        for row in plan["rows"]:
            meta = json.loads((self.meta / "runs" / row["run_id"] / "meta.json").read_text(encoding="utf-8"))
            prompt = (self.meta / "runs" / row["run_id"] / "prompt.txt").read_text(encoding="utf-8")
            self.assertEqual(prompt.replace(meta["stage"]["target"], "$1").replace(meta["stage"]["workdir"], "$2"),
                             expected)
            visible = meta["stage"]["dir"][len(stage_root):]
            self.assertRegex(visible, r"^/[0-9a-f]{12}$")

    def test_fire_is_refused_without_side_effects(self):
        roots = self.tmp / "fire"
        proc = run_driver(DRIVER, roots, "--fire", "--tier", "full", "--cell", "kimi-kfc", "--block", "gate")
        self.assertEqual(proc.returncode, 3, proc.stderr)
        self.assertIn("EXPERIMENT-CARD.md", proc.stderr)
        self.assertFalse((roots / "meta").exists() or (roots / "stage").exists())

    def test_tiers_plan_the_preregistered_counts(self):
        for tier, count, wounds in (("minimal", 72, {"C0", "W2", "W4"}), ("standard", 136, {"C0", "W1", "W2", "W3", "W4"})):
            with self.subTest(tier=tier):
                roots = self.tmp / tier
                proc = run_driver(DRIVER, roots, "--dry-run", "--tier", tier)
                self.assertIn("ok   [runs]", proc.stdout, proc.stdout)
                plan = json.loads((Path(os.path.realpath(roots / "meta")) / "runs/plan.json").read_text(encoding="utf-8"))
                self.assertEqual(len(plan["rows"]), count)
                self.assertEqual({row["wound"] for row in plan["rows"]}, wounds)
                gate = {row["wound"] for row in plan["rows"] if row["block"] == "gate"}
                self.assertEqual(gate, {"C0"} if tier == "minimal" else {"C0", "W1"})
                self.assertEqual("WARN [tier]" in proc.stdout, tier == "minimal")

    def test_scripts_make_no_host_calls(self):
        for script in (DRIVER, GENERATOR):
            for number, line in enumerate(script.read_text(encoding="utf-8").splitlines(), 1):
                for pattern in HOST_INVOCATION:
                    self.assertIsNone(pattern.search(line), f"{script.name}:{number}: {line}")
        driver = DRIVER.read_text(encoding="utf-8")
        self.assertRegex(driver, r"(?m)^HOST_ENTRY=disabled$")
        self.assertIn("RESERVED HOST ENTRY", driver)
        stub = re.search(r"(?ms)^dispatch_host\(\) \{[^\n]*\n(.*?)^\}", driver).group(1)
        self.assertEqual([line.strip().split()[0] for line in stub.strip().splitlines()], ["echo", "return"])

    def test_cards_cover_every_path_relation_once(self):
        cards = {w: front_matter(FACTORIAL / "cards" / f"{w}.md") for w in WOUNDS}
        relations = [card["path_relation"] for card in cards.values()]
        self.assertEqual(sorted(relations), sorted(ledger_check.PATH_RELATIONS - {"unknown"}))
        self.assertEqual([w for w, c in cards.items() if c["role"] == "positive-control"], ["W1"])
        self.assertEqual(cards["W1"]["path_relation"], "blocks-path")
        self.assertIn("阳性对照", (FACTORIAL / "cards/W1.md").read_text(encoding="utf-8"))
        for wound in WOUNDS:
            text = (FACTORIAL / "cards" / f"{wound}.md").read_text(encoding="utf-8")
            reach = text.split("## 路径触达性前置检查", 1)[1].split("\n## ", 1)[0]
            verdict = "结论：非必经" if cards[wound]["reach_required"] == "no" else "结论：必经"
            self.assertIn(verdict, reach, wound)

    # --- prereg-dependent: green only once prereg/ is frozen (S4) ------------

    def test_full_dry_run_is_green(self):
        self.assertEqual(self.full.returncode, 0, self.full.stdout + self.full.stderr)
        self.assertIn("DRY-RUN GREEN", self.full.stdout)

    def test_prereg_is_frozen_and_valid(self):
        texts = {name: (FACTORIAL / "prereg" / name).read_text(encoding="utf-8")
                 for name in ("RUBRIC.md", "INVALID-RULES.md", "EXPERIMENT-CARD.md")}
        for name, text in texts.items():
            self.assertIsNone(re.search(r"TODO|TBD|FIXME|待定|待补|占位", text), name)
        self.assertIn("ledger/SCHEMA.md", texts["RUBRIC.md"])
        self.assertRegex(texts["INVALID-RULES.md"], r"W1[^\n]*0/N")
        card = json.loads(re.search(r"```json\n(\{.*?\})\n```", texts["EXPERIMENT-CARD.md"], re.S).group(1))
        errors, planned = card_validator.validate(card)
        self.assertEqual(errors, [])
        self.assertEqual(planned, 168)
        self.assertEqual({t: v["max_runs"] for t, v in card["tiers"].items()},
                         {"minimal": 72, "standard": 136, "full": 168})
        self.assertEqual([h["id"] for h in card["hosts"]], list(HOST_CELLS))
        self.assertEqual(card["phase"], "phase3")

    def test_broken_inputs_turn_the_dry_run_red(self):
        def drift_card(ws):
            path = ws / "witness/factorial/cards/W3.md"
            path.write_text(path.read_text(encoding="utf-8").replace("keep_lines: 12", "keep_lines: 11"), encoding="utf-8")

        def host_call(ws):
            with (ws / "witness/factorial/gen_materials.sh").open("a", encoding="utf-8") as handle:
                handle.write("# smoke test: codex exec --version\n")

        def enable_entry(ws):  # a global search-and-replace must not be able to silence the audit
            path = ws / "witness/factorial/run_factorial.sh"
            path.write_text(path.read_text(encoding="utf-8").replace("HOST_ENTRY=disabled", "HOST_ENTRY=enabled"),
                            encoding="utf-8")

        def edit_prereg(ws):
            with (ws / "witness/factorial/prereg/RUBRIC.md").open("a", encoding="utf-8") as handle:
                handle.write("\n补充一条事后规则。\n")

        cases = {
            "card drifts from the generator": (drift_card, "keep_lines 11"),
            "host invocation in the generator": (host_call, "host binary invoked"),
            "host entry enabled": (enable_entry, "HOST_ENTRY must be 'disabled'"),
            "prereg edited after freezing": (edit_prereg, "frozen hash mismatch for witness/factorial/prereg/RUBRIC.md"),
        }
        for name, (mutate, expected) in cases.items():
            with self.subTest(case=name):
                base = self.tmp / ("red-" + re.sub(r"\W+", "-", name))
                driver = make_workspace(base / "ws")
                mutate(base / "ws")
                proc = run_driver(driver, base, "--dry-run", "--tier", "minimal")
                self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                self.assertIn("DRY-RUN RED", proc.stdout)
                self.assertIn(expected, proc.stdout)

    def test_materials_never_land_inside_the_repo(self):
        base = self.tmp / "inside"
        driver = make_workspace(base / "ws")
        proc = run_driver(driver, base, "--dry-run", extra_env={"RQ_FACTORIAL_META": str(base / "ws/targets/m")})
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertFalse((base / "ws/targets/m").exists())

    def test_reserved_fire_loop_keeps_artifacts_out_of_the_host_tree(self):
        base = self.tmp / "fake-fire"
        driver = make_workspace(base / "ws")
        dry = run_driver(driver, base, "--dry-run", "--tier", "standard")
        self.assertEqual(dry.returncode, 0, dry.stdout + dry.stderr)
        fake = (
            "dispatch_host() { # test double: transcript into the meta tree, card into the workdir\n"
            '  printf \'%s\\n\' "$1" >> "$FAKE_HOST_LOG"\n'
            '  printf \'fake transcript\\n\' > "$4"\n'
            '  printf \'小明，生日快乐！🎂\\n\' > "$3/card.txt"\n'
            '  printf \'host edit\\n\' >> "$3/../greeting-agent/agent/agent.ts"\n'
            "  return 0\n"
            "}"
        )
        text = driver.read_text(encoding="utf-8").replace("HOST_ENTRY=disabled", "HOST_ENTRY=enabled")
        enabled = driver.with_name("run_factorial_fire.sh")
        enabled.write_text(re.sub(r"(?ms)^dispatch_host\(\) \{.*?^\}", lambda _: fake, text, count=1), encoding="utf-8")
        log = base / "host.log"
        env = {"FAKE_HOST_LOG": str(log)}
        refused = run_driver(enabled, base, "--fire", "--tier", "standard", "--cell", "kimi-kfc", "--block", "rest",
                             extra_env=env)
        self.assertEqual(refused.returncode, 2, refused.stderr)
        self.assertIn("W1 gate", refused.stderr)
        fired = run_driver(enabled, base, "--fire", "--tier", "standard", "--cell", "kimi-kfc", "--block", "gate",
                           extra_env=env)
        self.assertEqual(fired.returncode, 0, fired.stdout + fired.stderr)
        meta_root = Path(os.path.realpath(base / "meta"))
        plan = json.loads((meta_root / "runs/plan.json").read_text(encoding="utf-8"))
        gate = [r for r in plan["rows"] if r["cell"] == "kimi-kfc" and r["block"] == "gate"]
        self.assertEqual(len(gate), 10)
        self.assertEqual(log.read_text(encoding="utf-8").splitlines(), ["kimi-kfc"] * 10)
        for row in gate:
            run_dir = meta_root / "runs" / row["run_id"]
            meta = json.loads((run_dir / "meta.json").read_text(encoding="utf-8"))
            self.assertEqual(meta["dispatch"]["status"], "dispatched")
            self.assertEqual((run_dir / "report.txt").read_text(encoding="utf-8"), "fake transcript\n")
            self.assertEqual((run_dir / "exitcode").read_text(encoding="utf-8"), "0\n")
            self.assertTrue((run_dir / "card.txt").is_file())
            self.assertTrue(meta["dispatch"]["target_modified"])
            self.assertFalse(Path(meta["stage"]["dir"]).exists())
        again = run_driver(enabled, base, "--fire", "--tier", "standard", "--cell", "kimi-kfc", "--block", "gate",
                           extra_env=env)
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertEqual(len(log.read_text(encoding="utf-8").splitlines()), 10, "no run may be dispatched twice")
        (meta_root / "runs/gate-kimi-kfc.json").write_text(json.dumps({"wound": "W1", "valid": 8, "detected": 0}))
        blocked = run_driver(enabled, base, "--fire", "--tier", "standard", "--cell", "kimi-kfc", "--block", "rest",
                             extra_env=env)
        self.assertEqual(blocked.returncode, 2, blocked.stderr)


if __name__ == "__main__":
    unittest.main()
