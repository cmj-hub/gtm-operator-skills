#!/usr/bin/env python3
"""score.py gates ICP before any paid finder."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "qualify-before-enrich"
EXAMPLES = SKILL / "examples"
CELL = "super-secret-cell"

ICP = {
    "industries": ["3PL / freight", "warehousing"],
    "employee_min": 50,
    "employee_max": 500,
    "titles_include": ["VP Operations", "Director of Operations", "Head of Ops"],
    "titles_exclude": ["Intern", "SDR", "Recruiter", "Student"],
    "geos": ["US", "CA"],
}

GOOD_ROW = {
    "company": "Northwind Logistics",
    "title": "VP Operations",
    "industry": "3PL / freight",
    "employees": 180,
    "geo": "US",
    "verdict": "enrich",
}


def run(args, stdin=None):
    return subprocess.run(
        [sys.executable, str(SKILL / "scripts" / "score.py"), *args],
        input=stdin,
        capture_output=True,
        text=True,
    )


def score(obj, *extra):
    return run(["--stdin", *extra], stdin=json.dumps(obj))


class ScoreQualify(unittest.TestCase):
    def test_good_draft_prints_enrich(self):
        result = run(["--file", str(EXAMPLES / "rows-good.json")])
        self.assertEqual(result.returncode, 0)
        self.assertIn("qualify pass", result.stdout)
        self.assertIn("Northwind Logistics: enrich", result.stdout)
        self.assertIn("Next: /prospect-list:who-to-contact", result.stdout)

    def test_drop_draft_passes(self):
        result = run(["--file", str(EXAMPLES / "rows-drop.json")])
        self.assertEqual(result.returncode, 0)
        self.assertIn("Adventure Works: drop", result.stdout)

    def test_fail_icp_with_paid_lookup_exits_1(self):
        result = run(["--file", str(EXAMPLES / "rows-fail-icp.json")])
        self.assertEqual(result.returncode, 1)
        self.assertIn("paid lookup on a failing row", result.stdout)
        self.assertIn("fails ICP", result.stdout)

    def test_missing_fields_claimed_enrich_exits_1(self):
        result = run(["--file", str(EXAMPLES / "rows-missing-fields.json")])
        self.assertEqual(result.returncode, 1)
        self.assertIn("incomplete row", result.stdout)
        self.assertIn("missing industry", result.stdout)

    def test_honest_hold_passes(self):
        payload = {
            "icp": ICP,
            "rows": [
                {
                    "company": "Contoso Freight",
                    "title": "Director of Operations",
                    "industry": "",
                    "employees": 90,
                    "geo": "US",
                    "verdict": "hold",
                }
            ],
        }
        result = score(payload)
        self.assertEqual(result.returncode, 0)
        self.assertIn("Contoso Freight: hold", result.stdout)

    def test_excluded_title_cannot_enrich(self):
        payload = {
            "icp": ICP,
            "rows": [{**GOOD_ROW, "title": "SDR", "verdict": "enrich"}],
        }
        result = score(payload)
        self.assertEqual(result.returncode, 1)
        self.assertIn("titles_exclude", result.stdout)

    def test_employee_out_of_range(self):
        payload = {
            "icp": ICP,
            "rows": [{**GOOD_ROW, "employees": 12, "verdict": "enrich"}],
        }
        result = score(payload)
        self.assertEqual(result.returncode, 1)
        self.assertIn("outside 50-500", result.stdout)

    def test_geo_outside_icp(self):
        payload = {
            "icp": ICP,
            "rows": [{**GOOD_ROW, "geo": "DE", "verdict": "enrich"}],
        }
        result = score(payload)
        self.assertEqual(result.returncode, 1)
        self.assertIn("geo 'DE' is outside ICP", result.stdout)

    def test_paid_flag_on_drop_row_refused(self):
        payload = {
            "icp": ICP,
            "rows": [
                {
                    **GOOD_ROW,
                    "title": "SDR",
                    "verdict": "drop",
                    "finder_ran": True,
                }
            ],
        }
        result = score(payload)
        self.assertEqual(result.returncode, 1)
        self.assertIn("paid lookup on a failing row", result.stdout)

    def test_json_output(self):
        result = score({"icp": ICP, "rows": [GOOD_ROW]}, "--json")
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["enrich_count"], 1)
        self.assertEqual(payload["next"], "/prospect-list:who-to-contact")

    def test_missing_icp_exits_1(self):
        result = score({"rows": [GOOD_ROW]})
        self.assertEqual(result.returncode, 1)
        self.assertIn("missing icp", result.stdout)

    def test_bad_json_hides_input(self):
        bad = run(["--stdin"], stdin='{"icp": "' + CELL)
        self.assertEqual(bad.returncode, 2)
        self.assertNotIn(CELL, bad.stdout + bad.stderr)
        self.assertIn("invalid JSON", bad.stderr)

    def test_missing_file_exits_2(self):
        result = run(["--file", str(EXAMPLES / "nope.json")])
        self.assertEqual(result.returncode, 2)
        self.assertIn("file not found", result.stderr)


class PluginLayout(unittest.TestCase):
    def test_skill_name_matches_directory(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"))
        front = text.split("---\n")[1]
        fields = dict(line.split(": ", 1) for line in front.strip().splitlines() if ": " in line)
        self.assertEqual(fields["name"], "qualify-before-enrich")
        self.assertEqual(SKILL.name, "qualify-before-enrich")

    def test_banned_phrase_ships_in_skill(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8").lower()
        self.assertIn("no paid lookup on a failing row", text)

    def test_license_is_mit(self):
        license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertIn("MIT License", license_text)


if __name__ == "__main__":
    unittest.main()
