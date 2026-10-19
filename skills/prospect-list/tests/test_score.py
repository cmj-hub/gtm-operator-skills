#!/usr/bin/env python3
"""score.py prints a list score from a signal or refuses a title-only list."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "who-to-contact"
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
    "title": "Ops lead at Northwind",
    "signal": "Posted a role for an outbound lead this week.",
    "score": "call this week",
}


class ScoreList(unittest.TestCase):
    def test_good_draft_prints_score(self):
        result = run(["--file", str(EXAMPLES / "list-good.json")])
        self.assertEqual(result.returncode, 0)
        self.assertIn("a list score from a signal", result.stdout)
        self.assertIn("signal: Posted a role for an outbound lead this week.", result.stdout)
        self.assertNotIn("a title-only list", result.stdout)

    def test_hold_draft_prints_score(self):
        result = run(["--file", str(EXAMPLES / "list-hold.json")])
        self.assertEqual(result.returncode, 0)
        self.assertIn("score: hold", result.stdout)

    def test_title_only_exits_1(self):
        result = run(["--file", str(EXAMPLES / "list-title.json")])
        self.assertEqual(result.returncode, 1)
        self.assertIn("a title-only list", result.stdout)
        self.assertIn("- missing signal (a title with no signal is a directory, not a list) \u2192 write one thing", result.stdout)
        self.assertNotIn("a list score from a signal", result.stdout)

    def test_persona_label_is_refused(self):
        result = run(["--file", str(EXAMPLES / "list-persona.json")])
        self.assertEqual(result.returncode, 1)
        self.assertIn("persona label", result.stdout)

    def test_signal_repeating_title_is_refused(self):
        result = score({**GOOD, "signal": "Ops lead at Northwind."})
        self.assertEqual(result.returncode, 1)
        self.assertIn("repeats the title", result.stdout)

    def test_short_signal_is_refused(self):
        result = score({**GOOD, "signal": "hiring"})
        self.assertEqual(result.returncode, 1)
        self.assertIn("under 3 words", result.stdout)

    def test_score_must_be_a_slot(self):
        result = score({**GOOD, "score": "banana"})
        self.assertEqual(result.returncode, 1)
        self.assertIn("score is not a slot", result.stdout)

    def test_score_alias_folds_to_slot(self):
        result = score({**GOOD, "score": "  Call "})
        self.assertEqual(result.returncode, 0)
        self.assertIn("score: call this week", result.stdout)

    def test_missing_title_is_not_called_title_only(self):
        result = score({"signal": GOOD["signal"], "score": "hold"})
        self.assertEqual(result.returncode, 1)
        self.assertIn("not a list score", result.stdout)
        self.assertIn("- missing title \u2192 name the person", result.stdout)
        self.assertNotIn("a title-only list", result.stdout)

    def test_json_output(self):
        result = score(GOOD, "--json")
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["score"], "call this week")
        refused = json.loads(score({"title": "Ops lead"}, "--json").stdout)
        self.assertFalse(refused["ok"])
        self.assertEqual(refused["verdict"], "a title-only list")
        self.assertIsNone(refused["title"])

    def test_bad_json_hides_input(self):
        bad = run(["--stdin"], stdin='{"title": "' + CELL)
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
        fields = dict(line.split(": ", 1) for line in front.strip().splitlines())
        self.assertEqual(fields["name"], SKILL.name)
        self.assertTrue(fields["description"].strip('"'))

    def test_manifests_agree(self):
        plugin = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
        market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
        names = [p["name"] for p in market["plugins"]]
        self.assertIn(plugin["name"], names)

    def test_examples_are_valid_json(self):
        for path in EXAMPLES.glob("*.json"):
            with self.subTest(path=path.name):
                self.assertIsInstance(json.loads(path.read_text()), dict)


class CliConvention(unittest.TestCase):
    def test_refusal_lines_say_what_to_change(self):
        result = run(["--file", str(EXAMPLES / "list-title.json")])
        self.assertEqual(result.returncode, 1)
        lines = result.stdout.strip().splitlines()
        for line in lines[1:-1]:
            self.assertRegex(line, r"^- .+ \u2192 .+")
        self.assertEqual(lines[-1], "Next: fix the lines above and run this again.")

    def test_pass_names_next_step(self):
        result = run(["--file", str(EXAMPLES / "list-good.json")])
        self.assertEqual(result.stdout.strip().splitlines()[-1], "Next: /cold-email:cold-email")

    def test_json_fixes_parallel_to_reasons(self):
        payload = json.loads(run(["--file", str(EXAMPLES / "list-title.json"), "--json"]).stdout)
        self.assertEqual(len(payload["fixes"]), len(payload["reasons"]))
        self.assertIn("run this again", payload["next"])

    def test_help_and_input_alias(self):
        self.assertIn("examples/list-good.json", run(["--help"]).stdout)
        self.assertEqual(run(["--input", str(EXAMPLES / "list-good.json")]).returncode, 0)


if __name__ == "__main__":
    unittest.main()
