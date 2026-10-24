import copy
import importlib.util
import json
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "skills/repo-quake/scripts/validate_card.py"
SPEC = importlib.util.spec_from_file_location("quake_validate_card", MODULE_PATH)
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)
EXAMPLE = Path(__file__).parents[1] / "examples/experiment-card.json"


class ValidateCardTests(unittest.TestCase):
    def setUp(self):
        self.card = json.loads(EXAMPLE.read_text(encoding="utf-8"))

    def test_example_is_valid_and_budgeted(self):
        errors, planned = validator.validate(self.card)
        self.assertEqual(errors, [])
        self.assertEqual(planned, 6)

    def test_controls_budget_isolation_and_ethics_are_checked(self):
        card = copy.deepcopy(self.card)
        card["arms"] = [arm for arm in card["arms"] if arm["role"] != "negative_control"]
        card["budget"]["max_runs"] = 1
        card["isolation"]["pristine_original_unreachable"] = False
        card["ethics"]["human_subjects"] = True
        errors, _ = validator.validate(card)
        joined = "\n".join(errors)
        self.assertIn("negative-control arm", joined)
        self.assertIn("cannot fund planned_runs", joined)
        self.assertIn("isolation.contamination", joined)
        self.assertIn("ethics.consent", joined)

    def test_run_overrides_and_declared_pristine_exposure_are_supported(self):
        card = copy.deepcopy(self.card)
        card["sampling"]["runs_overrides"] = {"C0": 3, "T1": 1, "R3": 1}
        card["isolation"]["pristine_original_unreachable"] = False
        card["isolation"]["contamination"] = "Original is outside the task root; any access invalidates the run."
        errors, planned = validator.validate(card)
        self.assertEqual(errors, [])
        self.assertEqual(planned, 5)

    def test_malformed_ids_and_non_finite_budget_do_not_crash(self):
        card = copy.deepcopy(self.card)
        card["hosts"][0]["id"] = ["not", "text"]
        card["arms"][0]["id"] = {"bad": "id"}
        card["budget"]["max_usd"] = float("nan")
        errors, _ = validator.validate(card)
        self.assertTrue(any("hosts[0].id" in error for error in errors))
        self.assertTrue(any("arms[0].id and fault" in error for error in errors))
        self.assertTrue(any("max_usd" in error for error in errors))

    def test_control_reference_must_have_matching_role(self):
        card = copy.deepcopy(self.card)
        card["controls"]["positive"] = "T1"
        errors, _ = validator.validate(card)
        self.assertTrue(any("not positive_control" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
