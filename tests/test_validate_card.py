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

    def test_new_design_examples_are_valid(self):
        for name in ("paired", "memory", "metamorphic", "quality-cost"):
            path = EXAMPLE.with_name(f"experiment-card-{name}.json")
            errors, planned = validator.validate(json.loads(path.read_text(encoding="utf-8")))
            self.assertEqual(errors, [], name)
            self.assertEqual(planned, 4, name)

    def test_paired_design_requires_balanced_order(self):
        card = json.loads(EXAMPLE.with_name("experiment-card-paired.json").read_text(encoding="utf-8"))
        card["design"]["paired"]["order_schedule"] = ["AB", "AB"]
        errors, _ = validator.validate(card)
        self.assertTrue(any("must balance AB and BA" in error for error in errors))

    def test_memory_design_requires_all_three_layers(self):
        card = json.loads(EXAMPLE.with_name("experiment-card-memory.json").read_text(encoding="utf-8"))
        del card["design"]["memory"]["layers"]["acceptance"]
        errors, _ = validator.validate(card)
        self.assertTrue(any("design.memory.layers.acceptance" in error for error in errors))

    def test_metamorphic_design_requires_relation_per_followup(self):
        card = json.loads(EXAMPLE.with_name("experiment-card-metamorphic.json").read_text(encoding="utf-8"))
        card["design"]["metamorphic"]["follow_ups"][0]["relation"] = ""
        errors, _ = validator.validate(card)
        self.assertTrue(any("follow_ups[0].relation" in error for error in errors))

    def test_cost_policy_rejects_negative_limit_and_missing_alignment(self):
        card = json.loads(EXAMPLE.with_name("experiment-card-quality-cost.json").read_text(encoding="utf-8"))
        card["cost_policy"]["max_per_run"] = -1
        card["cost_policy"]["billing_alignment"] = ""
        errors, _ = validator.validate(card)
        self.assertTrue(any("max_per_run" in error for error in errors))
        self.assertTrue(any("billing_alignment" in error for error in errors))

    def test_control_reference_must_have_matching_role(self):
        card = copy.deepcopy(self.card)
        card["controls"]["positive"] = "T1"
        errors, _ = validator.validate(card)
        self.assertTrue(any("not positive_control" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
