#!/usr/bin/env python3
"""score.py prints a waterfall route or refuses banned cascades."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCORE = ROOT / "skills" / "waterfall-email" / "scripts" / "score.py"
EXAMPLES = ROOT / "skills" / "waterfall-email" / "examples"
CELL = "super-secret-cell"


def run(args, stdin=None):
    return subprocess.run(
        [sys.executable, str(SCORE), *args],
        input=stdin,
        capture_output=True,
        text=True,
    )


class ScoreWaterfallEmail(unittest.TestCase):
    def test_fixed_pack_version_is_updateable(self):
        manifest = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
        marketplace = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
        entry = next(p for p in marketplace["plugins"] if p["name"] == manifest["name"])
        self.assertEqual(manifest["version"], "0.1.1")
        self.assertNotIn("version", entry)  # plugin.json owns the installed cache version.

    def test_good_draft_prints_route(self):
        result = run(["--file", str(EXAMPLES / "waterfall-good.json")])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("person: Ops lead at Northwind", result.stdout)
        self.assertIn("on_4xx: fix_input", result.stdout)
        self.assertIn("cascade order:", result.stdout)
        self.assertIn("crm email", result.stdout)
        self.assertIn("Next: /cold-email:cold-email on sendable rows only", result.stdout)

    def test_4xx_retry_exits_1(self):
        result = run(["--file", str(EXAMPLES / "waterfall-4xx-retry.json")])
        self.assertEqual(result.returncode, 1)
        self.assertIn("4xx retry", result.stdout)
        self.assertIn("fix_input or stop", result.stdout)
        self.assertNotIn("person: Ops lead", result.stdout)

    def test_found_unverified_exits_1(self):
        result = run(["--file", str(EXAMPLES / "waterfall-found-unverified.json")])
        self.assertEqual(result.returncode, 1)
        self.assertIn("deliverable", result.stdout)
        self.assertIn("sendable", result.stdout)

    def test_paid_first_exits_1(self):
        result = run(["--file", str(EXAMPLES / "waterfall-paid-first.json")])
        self.assertEqual(result.returncode, 1)
        self.assertIn("paid-first", result.stdout)

    def test_json_mode(self):
        result = run(["--file", str(EXAMPLES / "waterfall-good.json"), "--json"])
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["person"], "Ops lead at Northwind")

    def score_order(self, order):
        # Fictional native input, with existing row and 4xx contracts satisfied.
        draft = {
            "person": "Fictional operations lead", "field": "work_email",
            "inputs_held": ["company domain"], "cascade_order": order,
            "on_4xx": "stop", "rows": [{"id": "fictional-1",
                "email": "lead@fictional.example", "verify": "deliverable",
                "sendable": True}],
        }
        result = run(["--stdin", "--json"], stdin=json.dumps(draft))
        return result, json.loads(result.stdout)

    def test_verify_before_finder_is_refused(self):
        result, payload = self.score_order(["company domain", "verify", "paid finder"])
        self.assertEqual(result.returncode, 1)
        self.assertFalse(payload["ok"])
        self.assertTrue(any("does not end with verify" in r for r in payload["reasons"]))

    def test_non_finder_after_verify_is_also_refused(self):
        result, payload = self.score_order(["company domain", "paid finder", "verify", "archive"])
        self.assertEqual(result.returncode, 1)
        self.assertFalse(payload["ok"])

    def test_valid_order_and_existing_verify_names_are_preserved(self):
        for verify in ["verify", "verify email", "  VERIFY email.  "]:
            with self.subTest(verify=verify):
                order = ["company domain", "paid finder", verify]
                result, payload = self.score_order(order)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertTrue(payload["ok"])
                self.assertEqual(payload["cascade_order"], [v.strip() for v in order])

    def test_repeated_verify_still_requires_a_final_verify(self):
        # Earlier verification is not a substitute for verifying the later result.
        for final, expected in [("paid finder", 1), ("verify email", 0)]:
            with self.subTest(final=final):
                result, payload = self.score_order(["company domain", "verify", "paid finder", "verify", final])
                self.assertEqual(result.returncode, expected, result.stdout)
                self.assertEqual(payload["ok"], expected == 0)

    def test_missing_verify_keeps_existing_refusal(self):
        result, payload = self.score_order(["company domain", "paid finder"])
        self.assertEqual(result.returncode, 1)
        self.assertIn("cascade_order has no verify step; add verify at the end", payload["reasons"])

    def test_held_inputs_can_end_in_verify_without_paid_finder(self):
        result, payload = self.score_order(["company domain", "verify"])
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertTrue(payload["ok"])

    def test_bad_json_hides_input(self):
        bad = run(["--stdin"], stdin='{"person": "' + CELL)
        self.assertEqual(bad.returncode, 2)
        self.assertNotIn(CELL, bad.stdout + bad.stderr)
        self.assertIn("invalid JSON", bad.stderr)
        array = run(["--stdin"], stdin='["' + CELL + '"]')
        self.assertEqual(array.returncode, 2)
        self.assertNotIn(CELL, array.stdout + array.stderr)
        self.assertIn("JSON must be an object", array.stderr)


if __name__ == "__main__":
    unittest.main()
