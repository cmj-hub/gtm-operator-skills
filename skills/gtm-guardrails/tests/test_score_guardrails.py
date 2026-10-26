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


def load_link_scan():
    import importlib.util
    spec = importlib.util.spec_from_file_location("skill_link_scan", SKILL / "scripts" / "skill_link_scan.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class LinkClassify(unittest.TestCase):
    """A link is labelled from its parsed host and path, never from a substring."""

    def setUp(self):
        self.classify = load_link_scan().classify
        self.own = "cmj-hub/claude-gtm-guardrails"

    def test_own_repo_needs_github_host_and_repo_path(self):
        self.assertEqual(self.classify("https://github.com/cmj-hub/claude-gtm-guardrails", self.own), ("own repo", "github.com"))
        self.assertEqual(self.classify("https://github.com/CMJ-Hub/claude-gtm-guardrails/blob/main/README.md", self.own)[0], "own repo")
        self.assertEqual(self.classify("https://raw.githubusercontent.com/cmj-hub/claude-gtm-guardrails/main/x", self.own)[0], "own repo")

    def test_own_repo_name_elsewhere_is_outside(self):
        for u in (
            "https://evil.example.net/?x=github.com/cmj-hub/claude-gtm-guardrails",
            "https://evil.net/cmj-hub/claude-gtm-guardrails",
            "https://github.com/cmj-hub/claude-gtm-guardrails-fork",
            "https://github.com.evil.net/cmj-hub/claude-gtm-guardrails",
        ):
            self.assertEqual(self.classify(u, self.own)[0], "outside link", u)

    def test_userinfo_cannot_fake_a_host(self):
        for u in (
            "https://example.com@evil.net/x",
            "https://localhost@evil.net/x",
            "https://github.com@evil.net/cmj-hub/claude-gtm-guardrails",
        ):
            kind, host = self.classify(u, self.own)
            self.assertEqual(kind, "outside link", u)
            self.assertEqual(host, "evil.net", u)

    def test_backslash_and_userinfo_are_outside(self):
        # Browsers read a backslash as "/" in http(s) URLs, so the real host is evil.net.
        for u in (
            "https://evil.net\\@github.com/cmj-hub/claude-gtm-guardrails",
            "https://evil.net\\@localhost/x",
            "https://evil.net\\@api.example.com/x",
            "https://user@github.com/cmj-hub/claude-gtm-guardrails",
            "https://user:pw@localhost/x",
        ):
            self.assertEqual(self.classify(u, self.own)[0], "outside link", u)

    def test_link_cut_short_before_userinfo_is_outside(self):
        links_in = load_link_scan().links_in
        for line in (
            "see https://localhost)@evil.net/x for setup",
            "see https://api.example.com]@evil.net/x",
            "see <https://localhost>@evil.net/x",
            "see https://github.com/cmj-hub/claude-gtm-guardrails\"@evil.net/",
        ):
            kinds = [kind for _, kind, _ in links_in(line, self.own)]
            self.assertEqual(kinds, ["outside link"], line)

    def test_dot_segments_cannot_leave_the_repo(self):
        for u in (
            "https://github.com/cmj-hub/claude-gtm-guardrails/../../evil/repo",
            "https://github.com/cmj-hub/claude-gtm-guardrails/%2e%2e/%2E%2E/evil/repo",
            "https://github.com/cmj-hub/./claude-gtm-guardrails/x",
        ):
            self.assertEqual(self.classify(u, self.own)[0], "outside link", u)

    def test_text_glued_after_a_cut_link_is_outside(self):
        links_in = load_link_scan().links_in
        for line in (
            "see https://github.com/cmj-hub/claude-gtm-guardrails)/../../evil/x",
            "see https://localhost)/../x",
            "see https://api.example.com]x.evil.net",
        ):
            self.assertEqual([k for _, k, _ in links_in(line, self.own)], ["outside link"], line)
        ok = links_in("(see [repo](https://github.com/cmj-hub/claude-gtm-guardrails)).", self.own)
        self.assertEqual([k for _, k, _ in ok], ["own repo"])

    def test_links_in_keeps_ordinary_markdown(self):
        links_in = load_link_scan().links_in
        got = links_in("[docs](https://code.claude.com/docs/x). Also http://localhost:3000/.", self.own)
        self.assertEqual([(u, k) for u, k, _ in got], [("https://code.claude.com/docs/x", "outside link"), ("http://localhost:3000/", "local")])

    def test_placeholder_and_local_use_the_parsed_host(self):
        self.assertEqual(self.classify("http://localhost:3000/x", "")[0], "local")
        self.assertEqual(self.classify("https://api.example.com/v1", "")[0], "placeholder")
        self.assertEqual(self.classify("https://notexample.com/x", "")[0], "outside link")


if __name__ == "__main__":
    unittest.main()
