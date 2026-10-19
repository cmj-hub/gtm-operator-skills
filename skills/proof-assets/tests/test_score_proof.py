#!/usr/bin/env python3
"""score_proof.py passes checkable, permitted, dated proof and refuses the rest."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "proof-assets"
EXAMPLES = SKILL / "examples"
SCRIPT = SKILL / "scripts" / "score_proof.py"
AS_OF = ["--as-of", "2026-10-17"]
GOOD = json.loads((EXAMPLES / "proof-good.json").read_text())


def run(args, stdin=None):
    return subprocess.run([sys.executable, str(SCRIPT), *args], input=stdin, capture_output=True, text=True)


def score(obj, *extra):
    return run(["--stdin", *AS_OF, *extra], stdin=json.dumps(obj))


def one(**changes):
    asset = dict(GOOD["assets"][0], **changes)
    return {"assets": [{k: v for k, v in asset.items() if v is not None}]}


class Examples(unittest.TestCase):
    def test_good_passes(self):
        out = run(["--file", str(EXAMPLES / "proof-good.json"), *AS_OF])
        self.assertEqual(out.returncode, 0, out.stdout)
        self.assertTrue(out.stdout.splitlines()[-1].startswith("Next: /landing-page:page"))

    def test_vague_refused(self):
        out = run(["--file", str(EXAMPLES / "proof-vague.json"), *AS_OF])
        self.assertEqual(out.returncode, 1)
        self.assertIn("multiple with no two numbers", out.stdout)
        self.assertIn("praise with nothing in it", out.stdout)
        self.assertTrue(out.stdout.rstrip().endswith("Next: fix the lines above and run this again."))

    def test_unpermitted_refused(self):
        out = run(["--file", str(EXAMPLES / "proof-unpermitted.json"), *AS_OF])
        self.assertEqual(out.returncode, 1)
        self.assertIn("verbal permission", out.stdout)
        self.assertIn("months old", out.stdout)


class Rules(unittest.TestCase):
    def test_result_needs_before_and_after(self):
        self.assertEqual(score(one(before=None)).returncode, 1)

    def test_result_needs_timeframe(self):
        self.assertEqual(score(one(timeframe=None)).returncode, 1)

    def test_needs_source(self):
        self.assertEqual(score(one(source="")).returncode, 1)

    def test_named_needs_written(self):
        out = score(one(named=True, permission="verbal"))
        self.assertEqual(out.returncode, 1)
        self.assertEqual(score(one(named=True, permission="public")).returncode, 0)

    def test_none_permission_refused_even_unnamed(self):
        self.assertEqual(score(one(permission="none")).returncode, 1)

    def test_future_date_refused(self):
        self.assertEqual(score(one(date="2027-01-01")).returncode, 1)

    def test_max_age_flag(self):
        self.assertEqual(score(one(date="2026-01-01")).returncode, 0)
        self.assertEqual(score(one(date="2026-01-01"), "--max-age-months", "6").returncode, 1)

    def test_multiple_with_numbers_passes(self):
        self.assertEqual(score(one(claim="Reply time 12x faster: 2 days to 4 hours.")).returncode, 0)

    def test_praise_with_number_passes(self):
        asset = dict(GOOD["assets"][1], claim="Amazing: we answer 100% of Friday requests the same day.")
        self.assertEqual(score({"assets": [asset]}).returncode, 0)

    def test_logo_needs_written(self):
        logo = {"id": "a1", "type": "logo", "claim": "Harbor", "permission": "written", "source": "email", "date": "2026-10-01"}
        self.assertEqual(score({"assets": [logo]}).returncode, 0)
        self.assertEqual(score({"assets": [dict(logo, permission="verbal")]}).returncode, 1)

    def test_unknown_type_refused(self):
        self.assertEqual(score(one(type="award")).returncode, 1)

    def test_json_output(self):
        data = json.loads(score(GOOD, "--json").stdout)
        self.assertTrue(data["pass"])
        self.assertEqual(data["assets"], 3)


class BadInput(unittest.TestCase):
    def test_not_json(self):
        self.assertEqual(run(["--stdin"], stdin="nope").returncode, 2)

    def test_empty_assets(self):
        self.assertEqual(score({"assets": []}).returncode, 2)

    def test_bad_as_of(self):
        self.assertEqual(run(["--file", str(EXAMPLES / "proof-good.json"), "--as-of", "today"]).returncode, 2)

    def test_missing_file(self):
        self.assertEqual(run(["--file", "nope.json"]).returncode, 2)


if __name__ == "__main__":
    unittest.main()
