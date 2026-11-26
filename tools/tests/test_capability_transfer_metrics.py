"""Guard against misleading arithmetic and silent evidence promotion."""

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from capability_transfer_metrics import InvalidEvidence, summarize  # noqa: E402


class CapabilityTransferMetricsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((ROOT / "docs/capability-transfer/metrics-fixture.json").read_text(encoding="utf-8"))

    def data(self):
        return copy.deepcopy(self.fixture)

    def test_fictional_example_matches_documented_numbers(self):
        report = summarize(self.data())
        before, after = report["windows"]["baseline"], report["windows"]["followup"]
        self.assertEqual(report["comparison_status"], "DESCRIPTIVE_ONLY")
        self.assertEqual(before["avoidable_escalations"]["rate"], 0.4)
        self.assertEqual(after["avoidable_escalations"]["rate"], 0.1)
        self.assertEqual(before["acceptable_reviewed_outputs"]["rate"], 0.8)
        self.assertEqual(after["acceptable_reviewed_outputs"]["rate"], 0.9)
        self.assertEqual(before["independent_acceptable_outputs"]["rate"], None)
        self.assertEqual(after["independent_acceptable_outputs"]["rate"], 0.7)
        self.assertEqual(before["minutes"]["founder_minutes"]["per_opportunity"], 9)
        self.assertEqual(after["minutes"]["founder_minutes"]["per_opportunity"], 4.5)
        self.assertEqual(before["minutes"]["total_support_per_opportunity"], 10)
        self.assertEqual(after["minutes"]["total_support_per_opportunity"], 6.5)
        self.assertFalse(report["safety_hold_required"])
        self.assertEqual(report["competence_and_release_verdict"], "HUMAN_REVIEW_REQUIRED")

    def test_unknown_minutes_do_not_become_zero(self):
        data = self.data()
        data["windows"]["followup"]["opportunities"][0]["founder_minutes"] = None
        report = summarize(data)["windows"]["followup"]["minutes"]
        self.assertIsNone(report["founder_minutes"]["per_opportunity"])
        self.assertIsNone(report["total_support_per_opportunity"])
        self.assertEqual(report["founder_minutes"]["coverage"]["numerator"], 9)

    def test_unreviewed_is_not_a_pass_or_independence(self):
        data = self.data()
        row = data["windows"]["followup"]["opportunities"][0]
        row["quality"], row["independent"] = "unreviewed", None
        report = summarize(data)["windows"]["followup"]
        self.assertEqual(report["quality_review_coverage"]["numerator"], 9)
        self.assertEqual(report["acceptable_reviewed_outputs"]["denominator"], 9)

    def test_partial_independence_review_uses_unknown_rate(self):
        data = self.data()
        data["windows"]["followup"]["opportunities"][0]["independent"] = None
        metric = summarize(data)["windows"]["followup"]["independent_acceptable_outputs"]
        self.assertIsNone(metric["rate"])
        self.assertEqual(metric["numerator"], 7)

    def test_zero_denominator_is_unavailable_not_zero(self):
        data = self.data()
        data["windows"]["baseline"]["opportunities"] = []
        report = summarize(data)
        self.assertEqual(report["comparison_status"], "NOT_COMPARABLE")
        self.assertIsNone(report["windows"]["baseline"]["avoidable_escalations"]["rate"])

    def test_comparability_requires_explicit_human_confirmation(self):
        data = self.data()
        data["comparison_review"]["task_mix_reviewed"] = False
        self.assertEqual(summarize(data)["comparison_status"], "NOT_COMPARABLE")

    def test_critical_error_or_missed_required_triggers_hold(self):
        data = self.data()
        data["windows"]["followup"]["opportunities"][2]["critical_error"] = True
        self.assertTrue(summarize(data)["safety_hold_required"])
        data = self.data()
        data["windows"]["baseline"]["opportunities"][6]["escalation_class"] = "missed_required"
        self.assertTrue(summarize(data)["safety_hold_required"])

    def test_cli_check_exits_nonzero_on_safety_hold(self):
        data = self.data()
        data["windows"]["followup"]["opportunities"][0]["critical_error"] = True
        with tempfile.TemporaryDirectory() as temp:
            file = Path(temp) / "fictional.json"
            file.write_text(json.dumps(data), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(ROOT / "tools/capability_transfer_metrics.py"), "--input", str(file), "--check"],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("SAFETY_HOLD", result.stdout)

    def test_duplicate_ids_rejected(self):
        data = self.data()
        data["windows"]["baseline"]["opportunities"][0]["id"] = "b02"
        with self.assertRaises(InvalidEvidence):
            summarize(data)

    def test_inconsistent_escalation_rejected(self):
        data = self.data()
        data["windows"]["baseline"]["opportunities"][0]["escalated"] = False
        with self.assertRaises(InvalidEvidence):
            summarize(data)

    def test_unhashable_malformed_values_fail_cleanly(self):
        for field in ("quality", "escalation_class"):
            with self.subTest(field=field):
                data = self.data()
                data["windows"]["baseline"]["opportunities"][0][field] = ["bad"]
                with self.assertRaises(InvalidEvidence):
                    summarize(data)

    def test_independence_requires_reviewed_pass(self):
        data = self.data()
        data["windows"]["baseline"]["opportunities"][1]["independent"] = True
        with self.assertRaises(InvalidEvidence):
            summarize(data)

    def test_nonfinite_negative_and_boolean_minutes_rejected(self):
        for bad in (-1, float("nan"), float("inf"), True):
            with self.subTest(value=bad):
                data = self.data()
                data["windows"]["baseline"]["opportunities"][0]["founder_minutes"] = bad
                with self.assertRaises(InvalidEvidence):
                    summarize(data)

    def test_extra_fields_not_allowed_to_discourage_pii(self):
        data = self.data()
        data["windows"]["baseline"]["opportunities"][0]["customer_name"] = "DO NOT STORE"
        with self.assertRaises(InvalidEvidence):
            summarize(data)

    def test_scope_mismatch_rejected(self):
        data = self.data()
        data["windows"]["followup"]["scope_id"] = "different-work"
        with self.assertRaises(InvalidEvidence):
            summarize(data)

    def test_schema_mismatch_rejected(self):
        data = self.data()
        data["schema_version"] = 2
        with self.assertRaises(InvalidEvidence):
            summarize(data)


if __name__ == "__main__":
    unittest.main()
