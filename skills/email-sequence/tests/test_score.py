#!/usr/bin/env python3
"""score.py prints a lifecycle sequence or refuses a generic drip and a cold email."""

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CELL = "incomplete-json-probe"


GOOD = json.loads((ROOT / "examples" / "lifecycle-good.json").read_text())


def run(args, stdin=None):
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "score.py"), *args],
        input=stdin,
        capture_output=True,
        text=True,
    )


class ScoreLifecycle(unittest.TestCase):
    def test_good_draft_prints_three(self):
        result = run(["--file", str(ROOT / "examples" / "lifecycle-good.json")])
        self.assertEqual(result.returncode, 0)
        self.assertIn("welcome: You asked for the trial checklist.", result.stdout)
        self.assertIn("bargain: The checklist is the bargain.", result.stdout)
        self.assertIn("nurture: The next note stays on the pain you showed: the trial dies after the first login.", result.stdout)

    def test_refused_exits_1(self):
        result = run(["--file", str(ROOT / "examples" / "lifecycle-refused.json")])
        self.assertEqual(result.returncode, 1)
        self.assertIn("a generic drip and a cold email", result.stdout)
        self.assertNotIn("welcome:", result.stdout)

    def test_bad_json_hides_input(self):
        bad = run(["--stdin"], stdin='{"welcome": "' + CELL)
        self.assertNotEqual(bad.returncode, 0)
        self.assertNotIn(CELL, bad.stdout + bad.stderr)
        self.assertIn("invalid JSON", bad.stderr)
        array = run(["--stdin"], stdin='["' + CELL + '"]')
        self.assertNotEqual(array.returncode, 0)
        self.assertNotIn(CELL, array.stdout + array.stderr)
        self.assertIn("JSON must be an object", array.stderr)

    def test_refused_names_each_gate(self):
        result = run(["--file", str(ROOT / "examples" / "lifecycle-refused.json")])
        self.assertIn('- cold email: welcome says "introduce our"', result.stdout)
        self.assertIn('- generic drip: bargain says "Day 1"', result.stdout)
        self.assertIn("- pain mismatch:", result.stdout)

    def test_missing_part_is_incomplete(self):
        draft = dict(GOOD, bargain="  ")
        result = run(["--stdin"], stdin=json.dumps(draft))
        self.assertEqual(result.returncode, 1)
        self.assertIn("draft is incomplete", result.stdout)
        self.assertIn("- missing: bargain", result.stdout)

    def test_pain_mismatch_refused(self):
        draft = dict(GOOD, nurture="Here is a tip about onboarding.")
        result = run(["--stdin"], stdin=json.dumps(draft))
        self.assertEqual(result.returncode, 1)
        self.assertIn("a generic drip and a cold email", result.stdout)
        self.assertIn("- pain mismatch:", result.stdout)

    def test_pain_match_ignores_case_spacing_and_end_punctuation(self):
        draft = dict(GOOD, pain="The Trial dies after the first login.",
                     nurture="Still on it: the trial  dies after\nthe first login, again.")
        result = run(["--stdin"], stdin=json.dumps(draft))
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_json_output(self):
        good = run(["--file", str(ROOT / "examples" / "lifecycle-good.json"), "--json"])
        self.assertEqual(good.returncode, 0)
        body = json.loads(good.stdout)
        self.assertTrue(body["pass"])
        self.assertEqual(body["reasons"], [])
        self.assertEqual(body["nurture"], GOOD["nurture"])
        bad = run(["--file", str(ROOT / "examples" / "lifecycle-refused.json"), "--json"])
        self.assertEqual(bad.returncode, 1)
        body = json.loads(bad.stdout)
        self.assertFalse(body["pass"])
        self.assertNotIn("welcome", body)
        self.assertTrue(body["reasons"])

    def test_input_errors_exit_2(self):
        self.assertEqual(run([]).returncode, 2)
        self.assertEqual(run(["--file", str(ROOT / "nope.json")]).returncode, 2)
        both = run(["--file", str(ROOT / "examples" / "lifecycle-good.json"), "--stdin"], stdin="{}")
        self.assertEqual(both.returncode, 2)


SUBJECTS = json.loads((ROOT / "examples" / "lifecycle-subjects.json").read_text())


class ScoreSubjectsAndNotes(unittest.TestCase):
    def test_subjects_example_passes_and_prints_subjects(self):
        result = run(["--file", str(ROOT / "examples" / "lifecycle-subjects.json")])
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("welcome subject: You asked for the trial checklist", result.stdout)
        self.assertIn("nurture subject: When the trial dies after the first login", result.stdout)
        body = json.loads(run(["--file", str(ROOT / "examples" / "lifecycle-subjects.json"), "--json"]).stdout)
        self.assertEqual(body["nurture_subject"], SUBJECTS["nurture_subject"])

    def test_subjects_refused_example_names_each_gate(self):
        result = run(["--file", str(ROOT / "examples" / "lifecycle-subjects-refused.json")])
        self.assertEqual(result.returncode, 1)
        self.assertIn("- not three notes:", result.stdout)
        self.assertIn("- subjects repeat:", result.stdout)
        self.assertIn("- no opt-in:", result.stdout)
        self.assertIn("- pain mismatch: nurture_subject", result.stdout)

    def test_bodies_must_differ(self):
        draft = dict(GOOD, bargain=GOOD["welcome"].upper())
        result = run(["--stdin"], stdin=json.dumps(draft))
        self.assertEqual(result.returncode, 1)
        self.assertIn("- not three notes:", result.stdout)

    def test_welcome_must_reference_opt_in(self):
        draft = dict(GOOD, welcome="Here is the trial checklist. This note starts there.")
        result = run(["--stdin"], stdin=json.dumps(draft))
        self.assertEqual(result.returncode, 1)
        self.assertIn("- no opt-in:", result.stdout)
        for phrase in ("You signed up for", "You requested", "You downloaded", "Thanks for your opt-in to"):
            draft = dict(GOOD, welcome=phrase + " the trial checklist.")
            result = run(["--stdin"], stdin=json.dumps(draft))
            self.assertEqual(result.returncode, 0, phrase + ": " + result.stdout)

    def test_one_subject_requires_all_three(self):
        draft = dict(GOOD, welcome_subject="You asked for the trial checklist")
        result = run(["--stdin"], stdin=json.dumps(draft))
        self.assertEqual(result.returncode, 1)
        self.assertIn("draft is incomplete", result.stdout)
        self.assertIn("- missing: bargain_subject, nurture_subject", result.stdout)

    def test_subjects_must_differ(self):
        draft = dict(SUBJECTS, bargain_subject=" you asked for the TRIAL checklist ")
        result = run(["--stdin"], stdin=json.dumps(draft))
        self.assertEqual(result.returncode, 1)
        self.assertIn("- subjects repeat:", result.stdout)

    def test_nurture_subject_names_pain(self):
        draft = dict(SUBJECTS, nurture_subject="Checking in")
        result = run(["--stdin"], stdin=json.dumps(draft))
        self.assertEqual(result.returncode, 1)
        self.assertIn("- pain mismatch: nurture_subject", result.stdout)
        draft = dict(SUBJECTS, nurture_subject="The Trial  dies after the first login?")
        self.assertEqual(run(["--stdin"], stdin=json.dumps(draft)).returncode, 0)

    def test_subjects_are_scanned_for_drip_and_cold(self):
        draft = dict(SUBJECTS, bargain_subject="Day 3 tip")
        result = run(["--stdin"], stdin=json.dumps(draft))
        self.assertEqual(result.returncode, 1)
        self.assertIn('- generic drip: bargain_subject says "Day 3"', result.stdout)


class PackLayout(unittest.TestCase):
    def frontmatter(self):
        text = (ROOT / "skills" / "lifecycle-email" / "SKILL.md").read_text()
        match = re.match(r"---\n(.*?)\n---\n", text, re.DOTALL)
        self.assertIsNotNone(match, "SKILL.md needs YAML frontmatter")
        fields = {}
        for line in match.group(1).splitlines():
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip().strip('"')
        return fields

    def test_skill_frontmatter(self):
        fields = self.frontmatter()
        self.assertRegex(fields["name"], r"^[a-z0-9-]{1,64}$")
        self.assertTrue(0 < len(fields["description"]) <= 1024)
        self.assertLessEqual(set(fields), {"name", "description", "license", "allowed-tools", "argument-hint", "metadata", "models"})

    def test_plugin_manifest(self):
        manifest = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
        self.assertRegex(manifest["name"], r"^[a-z0-9-]+$")
        self.assertRegex(manifest["version"], r"^\d+\.\d+\.\d+$")
        self.assertTrue((ROOT / manifest["icon"]).is_file())
        self.assertNotIn("skills", manifest)


class CliConvention(unittest.TestCase):
    def test_refusal_lines_say_what_to_change(self):
        result = run(["--file", str(ROOT / "examples" / "lifecycle-refused.json")])
        self.assertEqual(result.returncode, 1)
        lines = result.stdout.strip().splitlines()
        self.assertEqual(lines[-1], "Next: fix the lines above and run this again.")
        for line in lines[1:-1]:
            self.assertRegex(line, r"^- .+ \u2192 .+")

    def test_pass_names_next_step(self):
        result = run(["--file", str(ROOT / "examples" / "lifecycle-good.json")])
        self.assertEqual(result.stdout.strip().splitlines()[-1], "Next: /gtm:next")

    def test_json_fixes_parallel_to_reasons(self):
        body = json.loads(run(["--file", str(ROOT / "examples" / "lifecycle-refused.json"), "--json"]).stdout)
        self.assertEqual(len(body["fixes"]), len(body["reasons"]))
        self.assertIn("run this again", body["next"])

    def test_help_and_input_alias(self):
        self.assertIn("examples/lifecycle-good.json", run(["--help"]).stdout)
        self.assertEqual(run(["--input", str(ROOT / "examples" / "lifecycle-good.json")]).returncode, 0)


if __name__ == "__main__":
    unittest.main()
