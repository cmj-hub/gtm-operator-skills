#!/usr/bin/env python3
"""score.py --mode full scores a full sales offer: what they get, price, why now, one first step."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "cold-offer"
FACTS = ("Ledgerline: AP automation. Pricing: $1,900/month flat plus $0.40 per invoice over 1,000. "
         "Tidewater Mechanical closed month-end 6 days faster. Loses deals to Procore's AP module.")
GOOD = {
    "what_they_get": "Ledgerline reads each subcontractor invoice, matches it to the PO and lien waiver, and codes it to job-cost lines in Sage 300.",
    "proof": "Tidewater Mechanical closed month-end 6 days faster.",
    "price": "$1,900/month flat plus $0.40 per invoice over 1,000.",
    "why_now": "Your 2026-10-02 job post says the team keys roughly 400 invoices a week by hand.",
    "first_step": "Reply yes and I'll set up a 30-minute walkthrough on a sample of your invoices.",
    "facts": FACTS,
}


def run(args, stdin=None):
    return subprocess.run(
        [sys.executable, str(SKILL / "scripts" / "score.py"), *args],
        input=stdin, capture_output=True, text=True,
    )


def checks(draft):
    result = run(["--stdin", "--json", "--mode", "full"], stdin=json.dumps(draft))
    report = json.loads(result.stdout)
    return result.returncode, [f["check"] for f in report["failures"]]


class ScoreFullOffer(unittest.TestCase):
    def test_example_passes_and_prints_parts(self):
        result = run(["--mode", "full", "--file", str(SKILL / "examples" / "offer-full.json")])
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("price: ", result.stdout)
        self.assertIn("first step: ", result.stdout)

    def test_good_passes(self):
        self.assertEqual(checks(GOOD), (0, []))

    def test_price_is_required_in_full_mode(self):
        code, found = checks(dict(GOOD, price=""))
        self.assertEqual(code, 1)
        self.assertIn("complete", found)

    def test_price_needs_a_number(self):
        self.assertIn("price", checks(dict(GOOD, price="Ask us for pricing."))[1])

    def test_why_now_needs_a_dated_or_specific_signal(self):
        self.assertIn("why_now", checks(dict(GOOD, why_now="Now is the perfect time to automate."))[1])

    def test_one_first_step(self):
        step = "Reply yes for a walkthrough? Or send a batch? Or book a call?"
        self.assertIn("first_step", checks(dict(GOOD, first_step=step))[1])

    def test_invented_terms_refused_unless_in_facts(self):
        code, found = checks(dict(GOOD, price="$1,900/month with a 30-day money-back guarantee."))
        self.assertIn("invented_terms", found)
        allowed = dict(GOOD, price="$1,900/month with a money-back guarantee.", facts=FACTS + " Money-back guarantee.")
        self.assertNotIn("invented_terms", checks(allowed)[1])

    def test_invented_numbers_refused(self):
        found = checks(dict(GOOD, proof="Customers save $80,000 a year and close 40% faster."))[1]
        self.assertIn("numbers", found)

    def test_estimate_math_allowed_in_price(self):
        price = "$1,900/month flat plus $0.40 per invoice over 1,000. At about 1,730 invoices a month, roughly $2,192/month (estimate)."
        self.assertEqual(checks(dict(GOOD, price=price)), (0, []))

    def test_hype_refused(self):
        self.assertIn("hype", checks(dict(GOOD, why_now="Act now: 2026-10-02 pricing ends soon, limited spots."))[1])

    def test_too_long(self):
        self.assertIn("length", checks(dict(GOOD, what_they_get="word " * 400))[1])

    def test_give_first_mode_unchanged_by_default(self):
        result = run(["--file", str(SKILL / "examples" / "offer-good.json")])
        self.assertEqual(result.returncode, 0)


class GiveFirstAttachment(unittest.TestCase):
    def test_attached_prototype_needs_to_exist(self):
        draft = {"leak": "Close takes 12 business days.", "prototype": "One worked invoice.",
                 "email_one": "Your close takes 12 business days. I've attached one worked invoice. The full report is yours if you want it."}
        result = run(["--stdin", "--json"], stdin=json.dumps(draft))
        found = [f["check"] for f in json.loads(result.stdout)["failures"]]
        self.assertIn("attached", found)
        draft["prototype_ready"] = True
        result = run(["--stdin", "--json"], stdin=json.dumps(draft))
        self.assertNotIn("attached", [f["check"] for f in json.loads(result.stdout)["failures"]])


if __name__ == "__main__":
    unittest.main()
