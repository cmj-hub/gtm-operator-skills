#!/usr/bin/env python3
"""check.py reads public HTML fixtures and prints three GTM gaps."""

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "gtm-leak-check"
EXAMPLES = SKILL / "examples"
SCRIPT = SKILL / "scripts" / "check.py"


def run(args, stdin=None):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        input=stdin,
        capture_output=True,
        text=True,
    )


class LeakCheck(unittest.TestCase):
    def test_thin_homepage_reports_site_gap(self):
        result = run(
            [
                "--html-file",
                str(EXAMPLES / "thin-home.html"),
                "--page-url",
                "https://thin.example/",
            ]
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Gap 1 of", result.stdout)
        self.assertNotIn("More public pages needed", result.stdout)
        self.assertIn("Source: https://thin.example/", result.stdout)
        self.assertRegex(result.stdout, r"title|thin|empty|next step", re.I)

    def test_noindex_and_blocked_crawlers_are_geo_gaps(self):
        result = run(
            [
                "--html-file",
                str(EXAMPLES / "noindex-home.html"),
                "--robots-file",
                str(EXAMPLES / "robots-block-ai.txt"),
                "--llms-status",
                "404",
                "--page-url",
                "https://hidden.example/",
            ]
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("noindex", result.stdout.lower())
        self.assertRegex(result.stdout.lower(), r"llms\.txt|gptbot|claudebot")

    def test_healthy_page_does_not_pad_or_call_gtm_a_leak(self):
        result = run(
            [
                "--html-file",
                str(EXAMPLES / "healthy-home.html"),
                "--robots-file",
                str(EXAMPLES / "robots-allow.txt"),
                "--llms-status",
                "200",
                "--page-url",
                "https://healthy.example/",
            ]
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("More public pages needed", result.stdout)
        self.assertNotIn("Public stack visible", result.stdout)
        self.assertNotIn("Gap 3 of 3", result.stdout)
        self.assertIn("Sources read:", result.stdout)
        self.assertIn("https://healthy.example/", result.stdout)
        self.assertRegex(result.stdout, r"Google Tag Manager")

    def test_json_mode_has_real_gaps_with_source_urls(self):
        result = run(
            [
                "--html-file",
                str(EXAMPLES / "thin-home.html"),
                "--page-url",
                "https://thin.example/",
                "--json",
            ]
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertGreaterEqual(len(payload["gaps"]), 1)
        self.assertLessEqual(len(payload["gaps"]), 3)
        names = [g["name"] for g in payload["gaps"]]
        self.assertNotIn("More public pages needed", names)
        self.assertNotIn("Public stack visible", names)
        for gap in payload["gaps"]:
            self.assertIn("name", gap)
            self.assertIn("source", gap)
            self.assertTrue(str(gap["source"]).startswith("http"))

    def test_missing_domain_exits_2(self):
        result = run([])
        self.assertEqual(result.returncode, 2)

    def test_stack_signatures_named_from_script_tags(self):
        result = run(
            [
                "--html-file",
                str(EXAMPLES / "healthy-home.html"),
                "--page-url",
                "https://healthy.example/",
                "--json",
            ]
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertIn("Google Tag Manager", payload["stack"])
        names = [g["name"] for g in payload["gaps"]]
        self.assertNotIn("Public stack visible", names)


    def test_thin_pricing_page_is_a_gap(self):
        result = run(
            [
                "--html-file",
                str(EXAMPLES / "healthy-home.html"),
                "--page-url",
                "https://healthy.example/",
                "--llms-status",
                "200",
                "--pricing-file",
                str(EXAMPLES / "pricing-thin.html"),
                "--pricing-url",
                "https://healthy.example/pricing",
                "--json",
            ]
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        names = [g["name"] for g in payload["gaps"]]
        self.assertIn("Thin or missing pricing", names)

    def test_careers_without_who_they_sell_to_is_a_gap(self):
        result = run(
            [
                "--html-file",
                str(EXAMPLES / "home-no-who.html"),
                "--page-url",
                "https://acme.example/",
                "--llms-status",
                "200",
                "--careers-file",
                str(EXAMPLES / "careers.html"),
                "--careers-url",
                "https://acme.example/careers",
                "--json",
            ]
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        names = [g["name"] for g in payload["gaps"]]
        self.assertIn("Homepage never names who they sell to", names)

    def test_homepage_that_names_the_buyer_skips_who_gap(self):
        result = run(
            [
                "--html-file",
                str(EXAMPLES / "healthy-home.html"),
                "--page-url",
                "https://healthy.example/",
                "--llms-status",
                "200",
                "--careers-file",
                str(EXAMPLES / "careers.html"),
                "--careers-url",
                "https://healthy.example/careers",
                "--json",
            ]
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        names = [g["name"] for g in payload["gaps"]]
        self.assertNotIn("Homepage never names who they sell to", names)


if __name__ == "__main__":
    unittest.main()

