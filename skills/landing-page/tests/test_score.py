#!/usr/bin/env python3
"""score.py prints one URL, one offer, and one action, or refuses a sitemap."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CELL = "incomplete-json-probe"
GOOD = {
    "url": "https://example.com/desk",
    "offer": "A one-page desk that names the week's leak.",
    "action": "Read the page and reply with the one number you want next.",
}


def run(args, stdin=None):
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "score.py"), *args],
        input=stdin,
        capture_output=True,
        text=True,
    )


def score(draft):
    result = run(["--stdin", "--json"], stdin=json.dumps(draft))
    return result.returncode, json.loads(result.stdout)


class ScorePage(unittest.TestCase):
    def test_good_draft_prints_three(self):
        result = run(["--file", str(ROOT / "examples" / "page-good.json")])
        self.assertEqual(result.returncode, 0)
        self.assertIn("url: https://example.com/desk", result.stdout)
        self.assertIn("offer: A one-page desk that names the week's leak.", result.stdout)
        self.assertIn("action: Read the page and reply with the one number you want next.", result.stdout)
        self.assertNotIn("a sitemap", result.stdout)

    def test_sitemap_exits_1(self):
        result = run(["--file", str(ROOT / "examples" / "page-sitemap.json")])
        self.assertEqual(result.returncode, 1)
        self.assertIn("a sitemap", result.stdout)
        self.assertNotIn("url:", result.stdout)

    def test_two_offers_example_fails(self):
        result = run(["--file", str(ROOT / "examples" / "page-two-offers.json")])
        self.assertEqual(result.returncode, 1)
        self.assertIn("- offer is more than one sentence", result.stdout)

    def test_sitemap_shapes(self):
        for draft in (
            {**GOOD, "kind": "Sitemap"},
            {**GOOD, "pages": ["https://example.com/a"]},
            {**GOOD, "url": ["https://example.com/a", "https://example.com/b"]},
            {**GOOD, "url": "https://example.com/sitemap"},
            {**GOOD, "url": "https://example.com/pages.xml"},
        ):
            code, out = score(draft)
            self.assertEqual(code, 1, draft)
            self.assertTrue(out["sitemap"], draft)

    def test_url_problems(self):
        cases = {
            "http://example.com/desk": "url is not https",
            "example.com/desk": "url is not https",
            "https://example.com/a https://example.com/b": "url holds more than one address",
            "https:///desk": "url has no host",
            "": "url is missing",
        }
        for url, problem in cases.items():
            code, out = score({**GOOD, "url": url})
            self.assertEqual(code, 1, url)
            self.assertEqual(out["problems"], [problem], url)

    def test_second_offer_or_action_fails(self):
        for draft, problem in (
            ({**GOOD, "offer": ["one", "two"]}, "more than one offer"),
            ({**GOOD, "offers": ["two"]}, "more than one offer"),
            ({**GOOD, "action": ["Book", "Read"]}, "more than one action"),
            ({**GOOD, "ctas": ["Book a call"]}, "more than one action"),
            ({**GOOD, "action": "Book a call. Or download the guide."}, "action is more than one sentence"),
        ):
            code, out = score(draft)
            self.assertEqual(code, 1, draft)
            self.assertIn(problem, out["problems"], draft)

    def test_reports_every_problem(self):
        code, out = score({"url": "http://example.com"})
        self.assertEqual(code, 1)
        self.assertEqual(
            out["problems"], ["url is not https", "offer is missing", "action is missing"]
        )

    def test_long_offer_fails(self):
        code, out = score({**GOOD, "offer": "A desk " + "x" * 300})
        self.assertEqual(code, 1)
        self.assertIn("offer is longer than 200 characters", out["problems"])

    def test_abbreviation_is_one_sentence(self):
        code, out = score({**GOOD, "offer": "A desk for B2B teams, e.g. ops leads, at $4.50 a week."})
        self.assertEqual(code, 0, out)

    def test_json_output_on_pass(self):
        code, out = score(GOOD)
        self.assertEqual(code, 0)
        self.assertEqual(out, {"pass": True, "sitemap": False, "problems": [], **GOOD,
                               "fixes": [], "next": "/email-sequence:lifecycle-email"})

    def test_bad_json_hides_input(self):
        bad = run(["--stdin"], stdin='{"url": "' + CELL)
        self.assertEqual(bad.returncode, 2)
        self.assertNotIn(CELL, bad.stdout + bad.stderr)
        self.assertIn("invalid JSON", bad.stderr)
        array = run(["--stdin"], stdin='["' + CELL + '"]')
        self.assertEqual(array.returncode, 2)
        self.assertNotIn(CELL, array.stdout + array.stderr)
        self.assertIn("JSON must be an object", array.stderr)

    def test_headline_example_passes(self):
        result = run(["--file", str(ROOT / "examples" / "page-headline.json")])
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("headline: Find the week's leak before Monday's pipeline review.", result.stdout)
        self.assertIn("proof: Built from the leaks", result.stdout)
        draft = json.loads((ROOT / "examples" / "page-headline.json").read_text())
        code, out = score(draft)
        self.assertEqual(code, 0)
        self.assertEqual(out, {"pass": True, "sitemap": False, "problems": [], **draft,
                               "fixes": [], "next": "/email-sequence:lifecycle-email"})

    def test_headline_refused_example_lists_each_problem(self):
        result = run(["--file", str(ROOT / "examples" / "page-headline-refused.json")])
        self.assertEqual(result.returncode, 1)
        for line in (
            "- headline is more than one sentence",
            "- headline holds a URL",
            "- headline does not name the offer",
            "- proof is empty",
        ):
            self.assertIn(line, result.stdout)

    def test_headline_is_one_sentence(self):
        code, out = score({**GOOD, "headline": "The week's leak. Named."})
        self.assertEqual(code, 1)
        self.assertEqual(out["problems"], ["headline is more than one sentence"])

    def test_headline_has_no_url(self):
        for headline in ("The week's leak at https://example.com/desk", "The week's leak at WWW.example.com"):
            code, out = score({**GOOD, "headline": headline})
            self.assertEqual(code, 1, headline)
            self.assertEqual(out["problems"], ["headline holds a URL"], headline)

    def test_headline_names_the_offer(self):
        code, out = score({**GOOD, "headline": "Grow faster this quarter."})
        self.assertEqual(code, 1)
        self.assertEqual(out["problems"], ["headline does not name the offer"])
        code, out = score({**GOOD, "headline": "Your DESK for Monday."})
        self.assertEqual(code, 0, out)

    def test_headline_list_or_blank_fails(self):
        self.assertIn("more than one headline", score({**GOOD, "headline": ["a", "b"]})[1]["problems"])
        self.assertIn("headline is missing", score({**GOOD, "headline": "  "})[1]["problems"])

    def test_proof_is_one_nonempty_line(self):
        for proof, problem in (
            ("", "proof is empty"),
            (["one", "two"], "proof is more than one line"),
            ("Used by 40 teams.\nCut churn by 12%.", "proof is more than one line"),
            ("x" * 201, "proof is longer than 200 characters"),
        ):
            code, out = score({**GOOD, "proof": proof})
            self.assertEqual(code, 1, proof)
            self.assertEqual(out["problems"], [problem], proof)
        code, out = score({**GOOD, "proof": "Used by 40 teams. Cut churn by 12%."})
        self.assertEqual(code, 0, out)

    def test_null_optional_fields_are_ignored(self):
        code, out = score({**GOOD, "headline": None, "proof": None})
        self.assertEqual(code, 0, out)
        self.assertNotIn("headline", out)

    def test_offers_list_refused(self):
        code, out = score({**GOOD, "offers": [GOOD["offer"]]})
        self.assertEqual(code, 1)
        self.assertEqual(out["problems"], ["more than one offer"])

    def test_missing_file_exits_2(self):
        result = run(["--file", str(ROOT / "examples" / "nope.json")])
        self.assertEqual(result.returncode, 2)
        self.assertIn("file not found", result.stderr)


class CliConvention(unittest.TestCase):
    def test_refusal_lines_say_what_to_change(self):
        result = run(["--file", str(ROOT / "examples" / "page-headline-refused.json")])
        lines = result.stdout.strip().splitlines()
        self.assertEqual(lines[-1], "Next: fix the lines above and run this again.")
        for line in lines[1:-1]:
            self.assertRegex(line, r"^- .+ \u2192 .+")

    def test_pass_names_next_step(self):
        result = run(["--file", str(ROOT / "examples" / "page-good.json")])
        self.assertEqual(result.stdout.strip().splitlines()[-1], "Next: /email-sequence:lifecycle-email")

    def test_json_fixes_parallel_to_problems(self):
        code, out = score({**GOOD, "url": "http://example.com/desk", "offer": "One. Two."})
        self.assertEqual(code, 1)
        self.assertEqual(len(out["fixes"]), len(out["problems"]))
        self.assertIn("run this again", out["next"])

    def test_help_and_input_alias(self):
        self.assertIn("examples/page-good.json", run(["--help"]).stdout)
        self.assertEqual(run(["--input", str(ROOT / "examples" / "page-good.json")]).returncode, 0)


if __name__ == "__main__":
    unittest.main()
