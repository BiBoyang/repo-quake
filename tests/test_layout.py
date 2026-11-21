"""Layout guards: the indexes, the upstream list and the links keep up with the tree."""
import importlib.util
import json
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRE_LEDGER = {"https://github.com/MoonshotAI/kimi-code/issues/4012"}
LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)\)")
GITHUB_ITEM = re.compile(r"https://github\.com/[\w.-]+/[\w.-]+/(?:issues|pull|discussions)/\d+")
LINK_EXCLUDE = (
    "runs/", "vendor/", "targets/", "tests/fixtures/", "docs/skill-quake/", "docs/pr-drafts/",
    "docs/process/plans/", "docs/process/prompts/", "docs/process/reviews/",
)


def tracked(*patterns):
    out = subprocess.run(["git", "-C", str(ROOT), "ls-files", "--", *patterns],
                         capture_output=True, text=True, check=True)
    return out.stdout.split()


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def section(text, heading):
    match = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    return match.group(1) if match else ""


def subdirs(top):
    return sorted({rel.split("/")[1] for rel in tracked(top) if rel.count("/") >= 2})


def load_validator():
    spec = importlib.util.spec_from_file_location(
        "layout_validate_card", ROOT / "skills" / "repo-quake" / "scripts" / "validate_card.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class IndexTest(unittest.TestCase):
    def test_every_top_level_directory_is_in_the_layout_table(self):
        layout = section(read("README.md"), "Layout")
        tops = sorted({rel.split("/")[0] for rel in tracked() if "/" in rel})
        rows = set(re.findall(r"^\| `([\w.-]+)/", layout, re.M))
        self.assertEqual([d for d in tops if d not in rows], [])

    def test_every_run_directory_is_indexed(self):
        index = read("runs/README.md")
        self.assertEqual([d for d in subdirs("runs") if f"`{d}/`" not in index], [])

    def test_every_phase_document_is_linked(self):
        readme, docs_index = read("README.md"), read("docs/README.md")
        for rel in tracked("docs/phase*.md"):
            with self.subTest(rel=rel):
                self.assertIn(f"]({rel})", readme)
                self.assertIn(f"]({rel.split('/', 1)[1]})", docs_index)

    def test_every_witness_has_a_readme_and_an_index_row(self):
        index = read("witness/README.md")
        for name in subdirs("witness"):
            with self.subTest(witness=name):
                self.assertTrue((ROOT / "witness" / name / "README.md").is_file())
                self.assertIn(f"]({name}/README.md)", index)


class CardTest(unittest.TestCase):
    def test_cards_validate_are_indexed_and_match_their_frozen_copies(self):
        validator, index = load_validator(), read("cards/README.md")
        cards = {rel: (ROOT / rel).read_bytes() for rel in tracked("cards/*.json")}
        frozen = {rel: (ROOT / rel).read_bytes() for rel in tracked("runs/*/card-frozen.json")}
        self.assertTrue(cards)
        for rel, data in cards.items():
            with self.subTest(card=rel):
                self.assertIn(f"]({rel.split('/', 1)[1]})", index)
                problems, _ = validator.validate(json.loads(data))
                self.assertEqual(problems, [])
                self.assertIn(data, frozen.values(), "no byte-equal card-frozen.json under runs/")
        for rel, data in frozen.items():
            with self.subTest(frozen=rel):
                self.assertIn(data, cards.values(), "no card in cards/ with these bytes")


class UpstreamTest(unittest.TestCase):
    def test_upstream_list_and_ledger_agree(self):
        ledger_text, readme = read("ledger/ledger.json"), read("README.md")
        for entry in json.loads(ledger_text)["entries"]:
            for link in entry.get("upstream") or []:
                with self.subTest(entry=entry["id"], url=link["url"]):
                    self.assertIn(link["url"], readme)
        listed = set(GITHUB_ITEM.findall(section(readme, "Upstream outcomes")))
        self.assertTrue(listed)
        self.assertEqual(sorted(url for url in listed - PRE_LEDGER if url not in ledger_text), [])


class LinkTest(unittest.TestCase):
    def test_relative_links_resolve(self):
        broken = []
        for rel in tracked("*.md"):
            if rel.startswith(LINK_EXCLUDE):
                continue
            text = re.sub(r"```.*?```", "", read(rel), flags=re.S)
            for target in LINK.findall(text):
                if re.match(r"^[a-z][a-z0-9+.-]*:", target) or target.startswith("#"):
                    continue
                if not (ROOT / rel).parent.joinpath(target.split("#")[0]).exists():
                    broken.append(f"{rel}: {target}")
        self.assertEqual(broken, [])


if __name__ == "__main__":
    unittest.main()
