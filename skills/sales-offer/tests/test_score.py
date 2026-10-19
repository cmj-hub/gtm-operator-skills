#!/usr/bin/env python3
"""score.py prints a cold offer or names each rule email one breaks."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "cold-offer"
CELL = "super-secret-cell"
LEAK = "The homepage asks for a meeting before it shows any work."
PROTOTYPE = "A one-page sample that leads with one finding and the short trial."


def run(args, stdin=None):
    return subprocess.run(
        [sys.executable, str(SKILL / "scripts" / "score.py"), *args],
        input=stdin,
        capture_output=True,
        text=True,
    )


def score(email_one, leak=LEAK, prototype=PROTOTYPE):
    draft = {"leak": leak, "prototype": prototype, "email_one": email_one}
    result = run(["--stdin", "--json"], stdin=json.dumps(draft))
    report = json.loads(result.stdout)
    return result.returncode, [f["check"] for f in report["failures"]]


class ScoreColdOffer(unittest.TestCase):
    def test_good_draft_prints_three(self):
        result = run(["--file", str(SKILL / "examples" / "offer-good.json")])
        self.assertEqual(result.returncode, 0)
        self.assertIn("leak: The homepage asks for a meeting before it shows any work.", result.stdout)
        self.assertIn("prototype: A one-page sample that leads with one finding", result.stdout)
        self.assertIn("email one: Your homepage asks for a meeting before it shows any work.", result.stdout)
        self.assertNotIn("email one that sells the paid product", result.stdout)

    def test_sell_exits_1(self):
        result = run(["--file", str(SKILL / "examples" / "offer-sells.json")])
        self.assertEqual(result.returncode, 1)
        self.assertIn("email one that sells the paid product", result.stdout)
        self.assertIn("retainer", result.stdout)
        self.assertIn(" \u2192 ", result.stdout)
        self.assertEqual(result.stdout.strip().splitlines()[-1], "Next: fix the lines above and run this again.")
        self.assertNotIn("leak:", result.stdout)

    def test_meeting_ask_fails(self):
        code, checks = score(
            "Your homepage asks for a meeting before it shows any work. Can we hop on a quick call?"
        )
        self.assertEqual(code, 1)
        self.assertEqual(checks, ["meeting"])

    def test_mentioning_a_meeting_is_not_asking(self):
        code, checks = score("Your homepage asks for a meeting before it shows any work.")
        self.assertEqual((code, checks), (0, []))

    def test_email_must_deliver_the_finding(self):
        code, checks = score("I wrote a one-page sample for you. The full report is yours if you want it.")
        self.assertEqual(code, 1)
        self.assertEqual(checks, ["finding"])

    def test_long_email_fails(self):
        code, checks = score(LEAK + " More detail." * 70)
        self.assertEqual(code, 1)
        self.assertEqual(checks, ["length"])

    def test_incomplete_names_missing_fields(self):
        result = run(["--stdin"], stdin=json.dumps({"leak": LEAK, "prototype": 3}))
        self.assertEqual(result.returncode, 1)
        self.assertIn("draft is incomplete (missing prototype, email_one)", result.stdout)

    def test_bad_json_hides_input(self):
        bad = run(["--stdin"], stdin='{"email_one": "' + CELL)
        self.assertNotEqual(bad.returncode, 0)
        self.assertNotIn(CELL, bad.stdout + bad.stderr)
        self.assertIn("invalid JSON", bad.stderr)
        array = run(["--stdin"], stdin='["' + CELL + '"]')
        self.assertNotEqual(array.returncode, 0)
        self.assertNotIn(CELL, array.stdout + array.stderr)
        self.assertIn("JSON must be an object", array.stderr)


def checks_for(draft, *extra):
    result = run(["--stdin", "--json", *extra], stdin=json.dumps(draft))
    return result.returncode, [f["check"] for f in json.loads(result.stdout)["failures"]]


SCOPED = json.loads((SKILL / "examples" / "offer-scoped.json").read_text())


class ScoreOfferFields(unittest.TestCase):
    def test_scoped_example_passes(self):
        result = run(["--file", str(SKILL / "examples" / "offer-scoped.json"), "--today", "2026-10-04"])
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("scope: One page that rewrites the homepage hero", result.stdout)
        self.assertIn("deadline: 2026-12-15", result.stdout)

    def test_scoped_refused_example_names_each_check(self):
        result = run(["--file", str(SKILL / "examples" / "offer-scoped-refused.json"), "--json"])
        self.assertEqual(result.returncode, 1)
        checks = [f["check"] for f in json.loads(result.stdout)["failures"]]
        self.assertEqual(checks, ["offer_sells", "scope", "deadline"])

    def test_leak_or_prototype_that_sells_fails(self):
        for name, text in (
            ("leak", "The homepage hides our pricing below the fold."),
            ("prototype", "A trial of the retainer, one page long."),
        ):
            code, checks = checks_for(dict(SCOPED, **{name: text}))
            self.assertEqual(code, 1, name)
            self.assertIn("offer_sells", checks, name)

    def test_offer_sells_detail_names_field(self):
        result = run(["--stdin"], stdin=json.dumps(dict(SCOPED, scope="One page, then the retainer.")))
        self.assertEqual(result.returncode, 1)
        self.assertIn("the offer sells the paid product (scope: retainer)", result.stdout)

    def test_scope_names_one_deliverable(self):
        for scope, ok in (
            ("One page.", True),
            ("A single worked slice of the onboarding fix, delivered as a doc, and nothing more.", True),
            ("A rewritten homepage hero", True),
            ("Audit, rewrite, and ad plan", False),
            ("A rewritten homepage hero section with new copy for every block on the page", False),
        ):
            code, checks = checks_for(dict(SCOPED, scope=scope))
            self.assertEqual(code == 0, ok, scope)
            self.assertEqual("scope" in checks, not ok, scope)

    def test_deadline_must_be_iso_date(self):
        for deadline in ("2026-02-30", "Dec 15", "2026-12-15T09:00", "15/12/2026"):
            code, checks = checks_for(dict(SCOPED, deadline=deadline))
            self.assertEqual((code, checks), (1, ["deadline"]), deadline)

    def test_deadline_against_today(self):
        self.assertEqual(checks_for(SCOPED, "--today", "2026-12-15"), (0, []))
        self.assertEqual(checks_for(SCOPED, "--today", "2026-12-16"), (1, ["deadline"]))
        self.assertEqual(checks_for(SCOPED), (0, []))

    def test_bad_today_exits_2(self):
        result = run(["--stdin", "--today", "tomorrow"], stdin=json.dumps(SCOPED))
        self.assertEqual(result.returncode, 2)
        self.assertIn("--today must be a YYYY-MM-DD date", result.stderr)

    def test_present_but_empty_optional_is_incomplete(self):
        result = run(["--stdin"], stdin=json.dumps(dict(SCOPED, scope="  ")))
        self.assertEqual(result.returncode, 1)
        self.assertIn("draft is incomplete (missing scope)", result.stdout)

    def test_null_optional_fields_are_ignored(self):
        self.assertEqual(checks_for(dict(SCOPED, scope=None, deadline=None)), (0, []))


class CliConvention(unittest.TestCase):
    def test_every_failure_line_says_what_to_change(self):
        result = run(["--file", str(SKILL / "examples" / "offer-scoped-refused.json"), "--today", "2026-10-04"])
        self.assertEqual(result.returncode, 1)
        lines = result.stdout.strip().splitlines()
        for line in lines[:-1]:
            self.assertRegex(line, r"^- .+ \u2192 .+")
        self.assertEqual(lines[-1], "Next: fix the lines above and run this again.")

    def test_pass_names_next_step(self):
        result = run(["--file", str(SKILL / "examples" / "offer-good.json")])
        self.assertEqual(result.stdout.strip().splitlines()[-1], "Next: /landing-page:page")
        report = json.loads(run(["--file", str(SKILL / "examples" / "offer-good.json"), "--json"]).stdout)
        self.assertEqual(report["next"], "/landing-page:page")

    def test_help_and_input_alias(self):
        self.assertIn("examples/offer-good.json", run(["--help"]).stdout)
        self.assertEqual(run(["--input", str(SKILL / "examples" / "offer-good.json")]).returncode, 0)


if __name__ == "__main__":
    unittest.main()
