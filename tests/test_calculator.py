import json
import unittest
from pathlib import Path

from vyaparvani.calculator import calculate


class GroundTruthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(__file__).parents[1] / "data" / "ground_truth.json"
        cls.cases = json.loads(path.read_text(encoding="utf-8"))

    def test_photo_cases_do_not_guess_units_or_missing_values(self):
        for case in self.cases:
            with self.subTest(case=case["id"]):
                result = calculate({
                    "product": case["product"],
                    "net_amount_paid": case["net_amount_paid"],
                    "paid_quantity": case["paid_quantity"],
                    "free_cartons": case["free_cartons"],
                    "quantity_unit": "unknown",
                })
                self.assertEqual(result["status"], case["expected_status"])
                self.assertEqual(result["landing_price_per_carton"], case["expected_landing_price_per_carton"])

    def test_clear_case_uses_gst_inclusive_amount_and_explicit_free_cartons(self):
        result = calculate({"product": "Demo jar", "net_amount_paid": "6600", "paid_quantity": "12",
                            "free_cartons": "0", "quantity_unit": "carton"})
        self.assertEqual(result["status"], "CLEAR")
        self.assertEqual(result["total_cartons"], "12")
        self.assertEqual(result["landing_price_per_carton"], "550.00")

    def test_free_cartons_are_added_only_when_explicit(self):
        result = calculate({"product": "Demo", "net_amount_paid": "6600", "paid_quantity": "12",
                            "free_cartons": "2", "quantity_unit": "carton"})
        self.assertEqual(result["total_cartons"], "14")
        self.assertEqual(result["landing_price_per_carton"], "471.43")


if __name__ == "__main__":
    unittest.main()
