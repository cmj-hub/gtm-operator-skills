#!/usr/bin/env python3
"""score.py gates found vs deliverable; refuses catch-all marked valid."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "found-vs-deliverable"
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
    "stage": "verified",
    "bucket": "deliverable",
    "sendable": True,
}


class ScoreVerify(unittest.TestCase):
    def test_good_draft_prints_deliverable(self):
        result = run(["--file", str(EXAMPLES / "verify-good.json")])
        self.assertEqual(result.returncode, 0)
        self.assertIn("a deliverable verify", result.stdout)
        self.assertIn("bucket: deliverable", result.stdout)
        self.assertIn("sendable: true", result.stdout)

    def test_held_catchall_exits_0(self):
        result = run(["--file", str(EXAMPLES / "verify-held-catchall.json")])
        self.assertEqual(result.returncode, 0)
        self.assertIn("a held catch-all row", result.stdout)
        self.assertIn("sendable: false", result.stdout)

    def test_catchall_marked_sendable_exits_1(self):
        result = run(["--file", str(EXAMPLES / "verify-catchall.json")])
        self.assertEqual(result.returncode, 1)
        self.assertIn("a catch-all marked valid", result.stdout)
        self.assertIn("catch-all marked sendable", result.stdout)

    def test_found_marked_sendable_exits_1(self):
        result = run(["--file", str(EXAMPLES / "verify-found.json")])
        self.assertEqual(result.returncode, 1)
        self.assertIn("a found row marked sendable", result.stdout)

    def test_unknown_marked_sendable_exits_1(self):
        result = run(["--file", str(EXAMPLES / "verify-unknown.json")])
        self.assertEqual(result.returncode, 1)
        self.assertIn("unknown marked sendable", result.stdout)

    def test_invalid_marked_sendable_exits_1(self):
        result = run(["--file", str(EXAMPLES / "verify-invalid.json")])
        self.assertEqual(result.returncode, 1)
        self.assertIn("invalid marked sendable", result.stdout)

    def test_verify_alias_for_bucket(self):
        result = score(
            {
                "email": GOOD["email"],
                "stage": "verified",
                "verify": "deliverable",
                "sendable": True,
            }
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("bucket: deliverable", result.stdout)

    def test_bucket_alias_catchall(self):
        result = score(
            {
                "email": "ops@fabrikam.com",
                "stage": "verified",
                "bucket": "catchall",
                "sendable": False,
            }
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("bucket: catch-all", result.stdout)

    def test_missing_email_refused(self):
        result = score({"stage": "verified", "bucket": "deliverable", "sendable": True})
        self.assertEqual(result.returncode, 1)
        self.assertIn("missing email", result.stdout)

    def test_bad_email_shape_refused(self):
        result = score({**GOOD, "email": "not-an-email"})
        self.assertEqual(result.returncode, 1)
        self.assertIn("not shaped like an address", result.stdout)

    def test_json_output(self):
        result = score(GOOD, "--json")
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["bucket"], "deliverable")
        self.assertEqual(payload["next"], "/cold-email:cold-email")
        refused = json.loads(
            score(
                {
                    "email": "ops@fabrikam.com",
                    "stage": "verified",
                    "bucket": "catch-all",
                    "sendable": True,
                },
                "--json",
            ).stdout
        )
        self.assertFalse(refused["ok"])
        self.assertEqual(refused["verdict"], "a catch-all marked valid")
        self.assertIsNone(refused["email"])

    def test_held_next_step(self):
        result = run(["--file", str(EXAMPLES / "verify-held-catchall.json")])
        self.assertIn(
            "Next: keep the row in its bucket; do not send until verify = deliverable.",
            result.stdout,
        )

    def test_bad_json_hides_input(self):
        bad = run(["--stdin"], stdin='{"email": "' + CELL)
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
        fields = dict(line.split(": ", 1) for line in front.strip().splitlines())
        self.assertEqual(fields["name"], SKILL.name)
        self.assertTrue(fields["description"].strip('"'))

    def test_kickoff_exists(self):
        kick = ROOT / "skills" / "found-vs-deliverable-kickoff" / "SKILL.md"
        self.assertTrue(kick.is_file())
        text = kick.read_text(encoding="utf-8")
        self.assertIn("name: found-vs-deliverable-kickoff", text)

    def test_manifests_agree(self):
        plugin = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
        market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
        names = [p["name"] for p in market["plugins"]]
        self.assertIn(plugin["name"], names)

    def test_examples_are_valid_json(self):
        for path in EXAMPLES.glob("*.json"):
            with self.subTest(path=path.name):
                self.assertIsInstance(json.loads(path.read_text()), dict)

    def test_license_is_mit(self):
        text = (ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("MIT License"))


class CliConvention(unittest.TestCase):
    def test_refusal_lines_say_what_to_change(self):
        result = run(["--file", str(EXAMPLES / "verify-catchall.json")])
        self.assertEqual(result.returncode, 1)
        lines = result.stdout.strip().splitlines()
        for line in lines[1:-1]:
            self.assertRegex(line, r"^- .+ \u2192 .+")
        self.assertEqual(lines[-1], "Next: fix the lines above and run this again.")

    def test_pass_names_next_step(self):
        result = run(["--file", str(EXAMPLES / "verify-good.json")])
        self.assertEqual(
            result.stdout.strip().splitlines()[-1], "Next: /cold-email:cold-email"
        )

    def test_json_fixes_parallel_to_reasons(self):
        payload = json.loads(
            run(["--file", str(EXAMPLES / "verify-catchall.json"), "--json"]).stdout
        )
        self.assertEqual(len(payload["fixes"]), len(payload["reasons"]))
        self.assertFalse(payload["ok"])


if __name__ == "__main__":
    unittest.main()
