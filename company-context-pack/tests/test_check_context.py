"""Tests for scripts/check_context.py. Stdlib only."""

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_context  # noqa: E402

FILES = ["company", "icp", "offer", "proof", "voice", "objections", "categories"]

GOOD = {
    "company": "# Company\nUpdated: 2026-03-02\n\nWe sell scheduling software to clinics.\n",
    "icp": "# ICP\nUpdated: 2026-03-02\n\n## Segments\n\n- Independent clinics with 5 to 20 staff.\n",
    "offer": "# Offer\nUpdated: 2026-03-02\n\n- Setup in a week.\n",
    "proof": (
        "# Proof\nUpdated: 2026-03-02\n\n## Results\n\n"
        "- Cut no-shows by 18 percent at one clinic. Source: case study, 2026-03-02.\n"
        "- Setup took five days on average. Source: unverified\n"
    ),
    "voice": (
        "# Voice\nUpdated: 2026-03-02\n\n## Sample lines\n\n"
        "- We fill the empty chair.\n- Booking should take ten seconds.\n- No call needed.\n"
    ),
    "objections": "# Objections\nUpdated: 2026-03-02\n\n- We already use a paper diary.\n",
    "categories": "# Categories\nUpdated: 2026-03-02\n\n- Paper diaries and spreadsheets.\n- Practice management suites.\n",
}


def index(names=FILES):
    lines = ["# Context", "", "Read these files first."]
    lines += [f"- [{n}.md]({n}.md)" for n in names]
    return "\n".join(lines) + "\n"


def make(tmp, overrides=None, drop=()):
    folder = Path(tmp) / "context"
    folder.mkdir()
    docs = dict(GOOD)
    docs.update(overrides or {})
    for name in FILES:
        if name not in drop:
            (folder / f"{name}.md").write_text(docs[name])
    (folder / "CONTEXT.md").write_text(index())
    return folder


class CheckFolderTest(unittest.TestCase):
    def check(self, **kwargs):
        with tempfile.TemporaryDirectory() as tmp:
            folder = make(tmp, **kwargs)
            return check_context.check_folder(folder)

    def test_good_folder_passes(self):
        result = self.check()
        self.assertEqual(result["refusals"], [])
        self.assertEqual(result["unverified"], 1)

    def test_missing_file_is_refused(self):
        result = self.check(drop=("icp",))
        self.assertTrue(any("icp.md is missing" in r for r in result["refusals"]))

    def test_result_without_source_is_refused(self):
        proof = GOOD["proof"] + "- Customers love it, revenue doubled.\n"
        result = self.check(overrides={"proof": proof})
        self.assertTrue(any("proof.md" in r and "Source" in r for r in result["refusals"]))

    def test_empty_source_is_refused(self):
        proof = GOOD["proof"] + "- Revenue doubled. Source:\n"
        result = self.check(overrides={"proof": proof})
        self.assertEqual(len(result["refusals"]), 1)

    def test_placeholder_source_is_refused(self):
        for value in ("n/a", "none", "TBD", "see above"):
            with self.subTest(value=value):
                proof = GOOD["proof"] + f"- Revenue doubled. Source: {value}\n"
                result = self.check(overrides={"proof": proof})
                self.assertTrue(any("has no Source" in r for r in result["refusals"]))

    def test_unverified_source_passes_and_counts(self):
        proof = GOOD["proof"] + "- Revenue doubled. Source: Unverified\n"
        result = self.check(overrides={"proof": proof})
        self.assertEqual(result["refusals"], [])
        self.assertEqual(result["unverified"], 2)

    def test_placeholder_text_is_refused(self):
        result = self.check(overrides={"offer": "# Offer\nUpdated: 2026-03-02\n\n- TODO price model\n"})
        self.assertTrue(any("offer.md" in r and "placeholder" in r for r in result["refusals"]))

    def test_index_must_list_every_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = make(tmp)
            (folder / "CONTEXT.md").write_text(index(FILES[:-1]))
            result = check_context.check_folder(folder)
        self.assertTrue(any("CONTEXT.md" in r and "categories.md" in r for r in result["refusals"]))

    def test_voice_needs_three_sample_lines(self):
        voice = "# Voice\nUpdated: 2026-03-02\n\n## Sample lines\n\n- One.\n- Two.\n"
        result = self.check(overrides={"voice": voice})
        self.assertTrue(any("voice.md" in r and "3" in r for r in result["refusals"]))

    def test_categories_refuses_a_link(self):
        cats = GOOD["categories"] + "- See https://example.com for more.\n"
        result = self.check(overrides={"categories": cats})
        self.assertTrue(any("categories.md" in r for r in result["refusals"]))

    def test_file_without_heading_is_refused(self):
        result = self.check(overrides={"company": "We sell scheduling software.\n"})
        self.assertTrue(any("company.md" in r and "heading" in r for r in result["refusals"]))

    def test_unknown_mid_line_is_counted(self):
        objections = GOOD["objections"] + "- Proof: Unknown: no customer has said this.\n"
        result = self.check(overrides={"objections": objections})
        self.assertEqual(result["unknown"], 1)

    def test_missing_updated_line_is_refused(self):
        result = self.check(overrides={"company": "# Company\n\nWe sell scheduling software.\n"})
        self.assertTrue(any("company.md" in r and "Updated" in r for r in result["refusals"]))

    def test_bad_updated_date_is_refused(self):
        result = self.check(overrides={"company": "# Company\nUpdated: last week\n\nWe sell it.\n"})
        self.assertTrue(any("company.md" in r and "Updated" in r for r in result["refusals"]))

    def test_em_dash_is_refused(self):
        result = self.check(overrides={"offer": GOOD["offer"] + "- Fast \u2014 and cheap.\n"})
        self.assertTrue(any("offer.md" in r and "em dash" in r for r in result["refusals"]))

    def test_unknown_lines_are_counted_not_refused(self):
        result = self.check(overrides={"icp": GOOD["icp"] + "- Unknown: buying triggers\n"})
        self.assertEqual(result["refusals"], [])
        self.assertEqual(result["unknown"], 1)


class ExampleTest(unittest.TestCase):
    def test_northwind_example_passes(self):
        result = check_context.check_folder(ROOT / "examples" / "northwind")
        self.assertEqual(result["refusals"], [])
        self.assertEqual(result["unverified"], 1)


class CliTest(unittest.TestCase):
    def run_cli(self, argv, stdin=""):
        out = io.StringIO()
        old = sys.stdin
        sys.stdin = io.StringIO(stdin)
        try:
            with contextlib.redirect_stdout(out):
                code = check_context.main(argv)
        finally:
            sys.stdin = old
        return code, out.getvalue()

    def test_pass_exit_zero_and_next_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = make(tmp)
            code, out = self.run_cli(["--dir", str(folder)])
        self.assertEqual(code, 0)
        self.assertTrue(out.strip().splitlines()[-1].startswith("Next:"))
        self.assertIn("1 unverified", out)

    def test_refusal_exit_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = make(tmp, drop=("icp",))
            code, out = self.run_cli(["--dir", str(folder)])
        self.assertEqual(code, 1)
        self.assertIn("Refusal:", out)
        self.assertIn("→", out)
        self.assertEqual(out.strip().splitlines()[-1], "Next: fix the lines above and run this again.")

    def test_missing_folder_exit_two(self):
        code, out = self.run_cli(["--dir", "/nonexistent/context"])
        self.assertEqual(code, 2)

    def test_json_is_one_object(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = make(tmp, drop=("icp",))
            code, out = self.run_cli(["--dir", str(folder), "--json"])
        data = json.loads(out)
        self.assertEqual(code, 1)
        self.assertFalse(data["passed"])
        self.assertIn("refusals", data)

    def test_stdin_checks_proof_text(self):
        code, out = self.run_cli(["--stdin"], stdin="# Proof\nUpdated: 2026-03-02\n\n- Revenue doubled.\n")
        self.assertEqual(code, 1)
        code, out = self.run_cli(["--stdin"], stdin=GOOD["proof"])
        self.assertEqual(code, 0)

    def test_file_checks_one_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = make(tmp, overrides={"proof": "# Proof\nUpdated: 2026-03-02\n\n- Revenue doubled.\n"})
            code, _ = self.run_cli(["--file", str(folder / "proof.md")])
            self.assertEqual(code, 1)
            code, _ = self.run_cli(["--file", str(folder / "company.md")])
            self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
