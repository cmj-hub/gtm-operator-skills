#!/usr/bin/env python3
"""score.py prints a domain route or refuses CRM write-back."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "inbound-from-domain"
EXAMPLES = SKILL / "examples"
CELL = "super-secret-cell"


def run(args, stdin=None):
    return subprocess.run(
        [sys.executable, str(SKILL / "scripts" / "score.py"), *args],
        input=stdin,
        capture_output=True,
        text=True,
    )


def score(obj, *extra):
    return run(["--stdin", *extra], stdin=json.dumps(obj))


GOOD = {
    "email": "alex@northwind.io",
    "domain": "northwind.io",
    "kind": "corporate",
    "company_guess": "Northwind",
    "evidence": [
        "Domain is not on the free-mail list",
        "Company-shaped second-level name",
    ],
    "route": "build-review",
    "crm_write": False,
}


class ScoreInbound(unittest.TestCase):
    def test_good_draft_prints_route(self):
        result = run(["--file", str(EXAMPLES / "inbound-good.json")])
        self.assertEqual(result.returncode, 0)
        self.assertIn("a build-review route from the domain", result.stdout)
        self.assertIn("domain: northwind.io", result.stdout)
        self.assertIn("crm_write: false", result.stdout)
        self.assertNotIn("a CRM write-back", result.stdout)

    def test_freemail_held(self):
        result = run(["--file", str(EXAMPLES / "inbound-freemail.json")])
        self.assertEqual(result.returncode, 0)
        self.assertIn("a personal route from the domain", result.stdout)

    def test_disposable_disqualify(self):
        result = run(["--file", str(EXAMPLES / "inbound-disposable.json")])
        self.assertEqual(result.returncode, 0)
        self.assertIn("a disqualify route from the domain", result.stdout)

    def test_crm_write_exits_1(self):
        result = run(["--file", str(EXAMPLES / "inbound-crm-write.json")])
        self.assertEqual(result.returncode, 1)
        self.assertIn("a CRM write-back", result.stdout)
        self.assertIn("CRM write-back is banned", result.stdout)
        self.assertIn("\u2192", result.stdout)

    def test_freemail_build_exits_1(self):
        result = run(["--file", str(EXAMPLES / "inbound-freemail-build.json")])
        self.assertEqual(result.returncode, 1)
        self.assertIn("a free-mail build route", result.stdout)
        self.assertIn("free-mail routed to build-review", result.stdout)

    def test_domain_mismatch(self):
        result = score({**GOOD, "domain": "other.io"})
        self.assertEqual(result.returncode, 1)
        self.assertIn("domain does not match the email", result.stdout)

    def test_missing_evidence(self):
        bad = {**GOOD}
        bad["evidence"] = []
        result = score(bad)
        self.assertEqual(result.returncode, 1)
        self.assertIn("evidence is empty", result.stdout)

    def test_corporate_without_company_guess(self):
        bad = {**GOOD}
        del bad["company_guess"]
        result = score(bad)
        self.assertEqual(result.returncode, 1)
        self.assertIn("company_guess", result.stdout)

    def test_route_alias_folds(self):
        result = score({**GOOD, "route": "Build"})
        self.assertEqual(result.returncode, 0)
        self.assertIn("route: build-review", result.stdout)

    def test_json_output(self):
        result = score(GOOD, "--json")
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["route"], "build-review")
        self.assertFalse(payload["crm_write"])
        refused = json.loads(score({**GOOD, "crm_write": True}, "--json").stdout)
        self.assertFalse(refused["ok"])
        self.assertEqual(refused["verdict"], "a CRM write-back")
        self.assertIsNone(refused["email"])

    def test_bad_json_hides_input(self):
        bad = run(["--stdin"], stdin='{"email": "' + CELL)
        self.assertEqual(bad.returncode, 2)
        self.assertNotIn(CELL, bad.stdout)
        self.assertNotIn(CELL, bad.stderr)

    def test_next_step_on_pass(self):
        result = run(["--file", str(EXAMPLES / "inbound-good.json")])
        self.assertEqual(result.returncode, 0)
        self.assertIn("Next: hand the route card to a human", result.stdout)


if __name__ == "__main__":
    unittest.main()
