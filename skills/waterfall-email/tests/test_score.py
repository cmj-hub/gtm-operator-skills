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
