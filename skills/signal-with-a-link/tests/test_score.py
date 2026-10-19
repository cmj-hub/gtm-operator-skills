#!/usr/bin/env python3
"""score.py accepts a dated linkable signal or refuses undated / unlinkable claims."""

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "signal-with-a-link"
EXAMPLES = SKILL / "examples"
CELL = "super-secret-cell"
AS_OF = ["--as-of", "2026-10-08"]


def run(args, stdin=None):
    return subprocess.run(
        [sys.executable, str(SKILL / "scripts" / "score.py"), *args],
        input=stdin,
        capture_output=True,
        text=True,
    )


def score(obj, *extra):
    return run(["--stdin", *AS_OF, *extra], stdin=json.dumps(obj))


GOOD = {
    "company": "Northwind",
    "event": "Posted a Demand Gen Lead role on LinkedIn",
    "url": "https://www.linkedin.com/jobs/view/4019283741",
    "date": "2026-10-04",
}


class ScoreSignal(unittest.TestCase):
    def test_good_draft_prints_signal(self):
        result = run(["--file", str(EXAMPLES / "signal-good.json"), *AS_OF])
        self.assertEqual(result.returncode, 0)
        self.assertIn("a dated, linkable signal", result.stdout)
        self.assertIn("url: https://www.linkedin.com/jobs/view/4019283741", result.stdout)
        self.assertIn("date: 2026-10-04", result.stdout)
        self.assertIn("Next: /psp:psp", result.stdout)

    def test_intent_allowed_with_url_and_date(self):
        result = run(["--file", str(EXAMPLES / "signal-with-intent.json"), *AS_OF])
        self.assertEqual(result.returncode, 0)
        self.assertIn("a dated, linkable signal", result.stdout)

    def test_no_url_exits_1(self):
        result = run(["--file", str(EXAMPLES / "signal-no-url.json"), *AS_OF])
        self.assertEqual(result.returncode, 1)
        self.assertIn("missing url", result.stdout)
        self.assertIn("\u2192", result.stdout)

    def test_no_date_exits_1(self):
        result = run(["--file", str(EXAMPLES / "signal-no-date.json"), *AS_OF])
        self.assertEqual(result.returncode, 1)
        self.assertIn("missing date", result.stdout)

    def test_intent_only_is_banned(self):
        result = run(["--file", str(EXAMPLES / "signal-intent-only.json"), *AS_OF])
        self.assertEqual(result.returncode, 1)
        self.assertIn("intent score without a URL and a date", result.stdout)
        self.assertIn("intent without a link and a date", result.stdout)

    def test_firmographic_is_refused(self):
        result = run(["--file", str(EXAMPLES / "signal-firmographic.json"), *AS_OF])
        self.assertEqual(result.returncode, 1)
        self.assertIn("firmographic state", result.stdout)

    def test_stale_date_is_refused(self):
        result = score({**GOOD, "date": "2026-01-01"})
        self.assertEqual(result.returncode, 1)
        self.assertIn("older than 90 days", result.stdout)

    def test_future_date_is_refused(self):
        result = score({**GOOD, "date": "2026-12-01"})
        self.assertEqual(result.returncode, 1)
        self.assertIn("future", result.stdout)

    def test_bad_url_is_refused(self):
        result = score({**GOOD, "url": "linkedin.com/jobs/view/1"})
        self.assertEqual(result.returncode, 1)
        self.assertIn("not a public http", result.stdout)

    def test_short_event_is_refused(self):
        result = score({**GOOD, "event": "hiring"})
        self.assertEqual(result.returncode, 1)
        self.assertIn("under 3 words", result.stdout)

    def test_json_output(self):
        result = score(GOOD, "--json")
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["date"], "2026-10-04")
        self.assertEqual(payload["age_days"], 4)
        refused = json.loads(score({"event": GOOD["event"], "intent_score": 90}, "--json").stdout)
        self.assertFalse(refused["ok"])
        self.assertEqual(refused["verdict"], "intent without a link and a date")
        self.assertIsNone(refused["url"])

    def test_bad_json_hides_input(self):
        bad = run(["--stdin"], stdin='{"event": "' + CELL)
        self.assertEqual(bad.returncode, 2)
        self.assertNotIn(CELL, bad.stdout + bad.stderr)
        self.assertIn("invalid JSON", bad.stderr)
        array = run(["--stdin"], stdin='["' + CELL + '"]')
        self.assertEqual(array.returncode, 2)
        self.assertNotIn(CELL, array.stdout + array.stderr)
        self.assertIn("JSON must be an object", array.stderr)

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
        self.assertEqual(fields["name"].strip().strip('"'), "signal-with-a-link")
        self.assertEqual(SKILL.name, "signal-with-a-link")

    def test_banned_line_is_public(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("no intent score without a url and a date", text.lower())
        self.assertNotIn("treg", text.lower())

    def test_readme_never_names_treg(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8").lower()
        self.assertNotIn("treg", readme)

    def test_license_is_mit(self):
        text = (ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertIn("MIT License", text)


if __name__ == "__main__":
    unittest.main()
