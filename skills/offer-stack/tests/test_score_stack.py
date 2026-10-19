#!/usr/bin/env python3
"""score_stack.py passes a stack built on numbered pains and refuses the rest."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "offer-stack"
EXAMPLES = SKILL / "examples"
SCRIPT = SKILL / "scripts" / "score_stack.py"
GOOD = json.loads((EXAMPLES / "stack-good.json").read_text())


def run(args, stdin=None):
    return subprocess.run([sys.executable, str(SCRIPT), *args], input=stdin, capture_output=True, text=True)


def score(obj, *extra):
    return run(["--stdin", *extra], stdin=json.dumps(obj))


def copy():
    return json.loads(json.dumps(GOOD))


class Examples(unittest.TestCase):
    def test_good_passes_with_sum(self):
        out = run(["--file", str(EXAMPLES / "stack-good.json")])
        self.assertEqual(out.returncode, 0, out.stdout)
        self.assertIn("p1: 3 hours x 40 people x $55 x 52 weeks = $343,200 a year", out.stdout)
        self.assertIn("pain total: $490,080 a year", out.stdout)
        self.assertTrue(out.stdout.splitlines()[-1].startswith("Next: /pricing:pricing anchor"))

    def test_feature_list_refused(self):
        out = run(["--file", str(EXAMPLES / "stack-feature-list.json")])
        self.assertEqual(out.returncode, 1)
        self.assertIn("removes no pain", out.stdout)
        self.assertIn("satisfaction", out.stdout)
        self.assertTrue(out.stdout.rstrip().endswith("Next: fix the lines above and run this again."))

    def test_overpriced_refused(self):
        out = run(["--file", str(EXAMPLES / "stack-overpriced.json")])
        self.assertEqual(out.returncode, 1)
        self.assertIn("more than the pain", out.stdout)


class Rules(unittest.TestCase):
    def test_pain_without_source_refused(self):
        draft = copy()
        del draft["pains"][0]["source"]
        self.assertEqual(score(draft).returncode, 1)

    def test_all_assumptions_refused(self):
        draft = copy()
        for pain in draft["pains"]:
            pain["source"] = "assumption: guess"
        out = score(draft)
        self.assertEqual(out.returncode, 1)
        self.assertIn("every number is an assumption", out.stdout)

    def test_open_pain_refused(self):
        draft = copy()
        draft["components"] = draft["components"][:2]
        out = score(draft)
        self.assertEqual(out.returncode, 1)
        self.assertIn("pain p3 is left open", out.stdout)

    def test_unknown_pain_id_refused(self):
        draft = copy()
        draft["components"][0]["removes"] = ["p9"]
        self.assertEqual(score(draft).returncode, 1)

    def test_filler_refused(self):
        draft = copy()
        draft["components"][0]["name"] = "Best-in-class note sync"
        self.assertEqual(score(draft).returncode, 1)

    def test_no_risk_reversal_refused(self):
        draft = copy()
        draft["risk_reversal"] = ""
        self.assertEqual(score(draft).returncode, 1)

    def test_bad_period_refused(self):
        draft = copy()
        draft["pains"][0]["period"] = "fortnight"
        self.assertEqual(score(draft).returncode, 1)

    def test_price_optional(self):
        draft = copy()
        del draft["price"]
        self.assertEqual(score(draft).returncode, 0)

    def test_day_is_working_day(self):
        draft = copy()
        draft["pains"] = [dict(draft["pains"][0], count=1, people=1, cost_each=10, period="day")]
        draft["components"] = [{"name": "x", "removes": ["p1"]}]
        out = score(draft, "--json")
        self.assertEqual(json.loads(out.stdout)["pain_total_per_year"], 2600)

    def test_json_output(self):
        data = json.loads(score(GOOD, "--json").stdout)
        self.assertTrue(data["pass"])
        self.assertEqual(data["pain_total_per_year"], 490080)


class BadInput(unittest.TestCase):
    def test_not_json(self):
        self.assertEqual(run(["--stdin"], stdin="nope").returncode, 2)

    def test_no_pains(self):
        self.assertEqual(score(dict(GOOD, pains=[])).returncode, 2)

    def test_no_components(self):
        self.assertEqual(score(dict(GOOD, components=[])).returncode, 2)

    def test_missing_file(self):
        self.assertEqual(run(["--file", "nope.json"]).returncode, 2)

    def test_bool_is_not_a_number(self):
        draft = copy()
        draft["pains"][0]["count"] = True
        self.assertEqual(score(draft).returncode, 1)


if __name__ == "__main__":
    unittest.main()
