#!/usr/bin/env python3
"""score_guardrails.py passes guarded settings and refuses CRM writes with no prompt."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "gtm-guardrails"
EXAMPLES = SKILL / "examples"
SCRIPT = SKILL / "scripts" / "score_guardrails.py"

GOOD = json.loads((EXAMPLES / "guardrails-good.json").read_text())


def run(args, stdin=None):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], input=stdin, capture_output=True, text=True
    )


def score(obj, *extra):
    return run(["--stdin", *extra], stdin=json.dumps(obj))


def with_perms(**perms):
    draft = json.loads(json.dumps(GOOD))
    draft["settings"]["permissions"].update(perms)
    return draft


class Examples(unittest.TestCase):
    def test_good_passes(self):
        out = run(["--file", str(EXAMPLES / "guardrails-good.json")])
        self.assertEqual(out.returncode, 0, out.stdout)
        self.assertIn("Next:", out.stdout.splitlines()[-1])

    def test_open_crm_refused(self):
        out = run(["--file", str(EXAMPLES / "guardrails-open-crm.json")])
        self.assertEqual(out.returncode, 1)
        self.assertIn("bypassPermissions", out.stdout)
        self.assertIn("lets every crm tool run", out.stdout)
        self.assertIn("no before value", out.stdout)
        self.assertTrue(out.stdout.rstrip().endswith("Next: fix the lines above and run this again."))

    def test_write_allowed_refused(self):
        out = run(["--file", str(EXAMPLES / "guardrails-write-allowed.json")])
        self.assertEqual(out.returncode, 1)
        self.assertIn("mcp__crm__update_record runs a CRM write", out.stdout)

    def test_template_passes_as_settings(self):
        out = run(["--settings", str(SKILL / "templates" / "crm-read-only.settings.json"), "--crm", "crm"])
        self.assertEqual(out.returncode, 0, out.stdout)


class Rules(unittest.TestCase):
    def test_bare_server_allow_refused(self):
        out = score(with_perms(allow=["mcp__crm"]))
        self.assertEqual(out.returncode, 1)

    def test_leading_wildcard_allow_refused(self):
        out = score(with_perms(allow=["mcp__crm__*_record"]))
        self.assertEqual(out.returncode, 1)
        self.assertIn("starts with a wildcard", out.stdout)

    def test_no_ask_refused(self):
        out = score(with_perms(ask=[]))
        self.assertEqual(out.returncode, 1)
        self.assertIn("no ask rule", out.stdout)

    def test_whole_server_ask_counts(self):
        out = score(with_perms(ask=["mcp__crm__*"]))
        self.assertEqual(out.returncode, 0, out.stdout)

    def test_delete_not_denied_refused(self):
        out = score(with_perms(deny=[]))
        self.assertEqual(out.returncode, 1)
        self.assertIn("not denied", out.stdout)

    def test_other_server_rules_ignored(self):
        out = score(with_perms(allow=GOOD["settings"]["permissions"]["allow"] + ["mcp__docs__*"]))
        self.assertEqual(out.returncode, 0, out.stdout)

    def test_dotted_server_name(self):
        draft = json.loads(json.dumps(GOOD).replace("mcp__crm__", "mcp__my_crm__"))
        draft["crm_servers"] = ["my.crm"]
        self.assertEqual(score(draft).returncode, 0)

    def test_card_without_undo_refused(self):
        draft = json.loads(json.dumps(GOOD))
        del draft["approval_cards"][0]["undo"]
        out = score(draft)
        self.assertEqual(out.returncode, 1)
        self.assertIn("no undo line", out.stdout)

    def test_noop_card_refused(self):
        draft = json.loads(json.dumps(GOOD))
        draft["approval_cards"][0]["after"] = draft["approval_cards"][0]["before"]
        self.assertEqual(score(draft).returncode, 1)

    def test_json_output(self):
        out = score(GOOD, "--json")
        data = json.loads(out.stdout)
        self.assertTrue(data["pass"])
        self.assertEqual(data["fixes"], [])


class SecurityReview(unittest.TestCase):
    """Findings from the 2026-10-17 security review, pinned."""

    def test_unanchored_allow_globs_refused(self):
        for rule in ("mcp__*", "*", "mcp__crm*"):
            out = score(with_perms(allow=GOOD["settings"]["permissions"]["allow"] + [rule]))
            self.assertEqual(out.returncode, 1, rule)

    def test_read_prefix_glob_that_matches_writes_refused(self):
        # get* (no underscore) also matches a hypothetical getandupdate tool;
        # a glob is refused when it matches any write-shaped tool name.
        for rule in ("mcp__crm__*e*", "mcp__crm__?pdate_*", "mcp__crm__[cu]*"):
            out = score(with_perms(allow=GOOD["settings"]["permissions"]["allow"] + [rule]))
            self.assertEqual(out.returncode, 1, rule)

    def test_each_write_verb_needs_ask(self):
        # Only *create* in ask: update and upsert would run on first-use prompts only.
        out = score(with_perms(ask=["mcp__crm__*create*"]))
        self.assertEqual(out.returncode, 1)
        self.assertIn("update", out.stdout)

    def test_each_delete_verb_needs_deny(self):
        out = score(with_perms(deny=["mcp__crm__*delete*"]))
        self.assertEqual(out.returncode, 1)
        self.assertIn("merge", out.stdout)

    def test_server_wide_deny_covers_deletes(self):
        perms = GOOD["settings"]["permissions"]
        out = score(with_perms(deny=["mcp__crm__*"], ask=perms["ask"]))
        self.assertEqual(out.returncode, 0, out.stdout)

    def test_exact_name_read_tool_allowed(self):
        # SKILL.md step 3: add a read tool that does not start with get/list/search by exact name.
        out = score(with_perms(allow=GOOD["settings"]["permissions"]["allow"] + ["mcp__crm__whoami"]))
        self.assertEqual(out.returncode, 0, out.stdout)

    def test_non_read_glob_still_refused(self):
        out = score(with_perms(allow=GOOD["settings"]["permissions"]["allow"] + ["mcp__crm__who*"]))
        self.assertEqual(out.returncode, 1)

    def test_csv_cells_cannot_start_a_formula(self):
        # In-process on strings: no CSV file is created (hub data policy).
        import importlib.util

        spec = importlib.util.spec_from_file_location("skill_link_scan", SKILL / "scripts" / "skill_link_scan.py")
        scan = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(scan)
        for cell in ('=HYPERLINK("https://evil.example.org")', "@cmd npm install x", "-pip install y", "+1", "\tx", "\rx"):
            self.assertEqual(scan.safe_cell(cell), "'" + cell)
        self.assertEqual(scan.safe_cell("plain"), "plain")


class BadInput(unittest.TestCase):
    def test_no_servers(self):
        draft = dict(GOOD, crm_servers=[])
        self.assertEqual(score(draft).returncode, 2)

    def test_not_json(self):
        self.assertEqual(run(["--stdin"], stdin="nope").returncode, 2)

    def test_settings_needs_crm(self):
        out = run(["--settings", str(SKILL / "templates" / "crm-read-only.settings.json")])
        self.assertEqual(out.returncode, 2)

    def test_missing_file(self):
        self.assertEqual(run(["--file", "does-not-exist.json"]).returncode, 2)


class LinkScan(unittest.TestCase):
    def test_scans_this_pack(self):
        out = subprocess.run(
            [sys.executable, str(SKILL / "scripts" / "skill_link_scan.py"), str(SKILL)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("code.claude.com", out.stdout)


if __name__ == "__main__":
    unittest.main()
