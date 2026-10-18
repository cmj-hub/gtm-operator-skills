"""check_shortlist: the citation lint for a TGD shortlist. Stdlib only."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

PACK = Path(__file__).resolve().parents[1]
SCRIPT = PACK / "skills" / "pick-gtm-tools" / "scripts" / "check_shortlist.py"
EXAMPLES = PACK / "examples"

GOOD = """## Shortlist: cold email my agent can drive

1. **Instantly**: official MCP server, public API, works natively inside Clay (as of 2026-10-17). Source: The GTM Directory, https://thegtmdirectory.com/tools/instantly
2. **Smartlead**: official MCP server, public API, works natively inside Clay (as of 2026-10-17). Source: The GTM Directory, https://thegtmdirectory.com/tools/smartlead

Open on The GTM Directory: https://thegtmdirectory.com/best/cold-email
"""


def run(*args, stdin=None):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        input=stdin,
        capture_output=True,
        text=True,
    )


class ShortlistLintTest(unittest.TestCase):
    def test_good_shortlist_passes(self):
        result = run("--stdin", stdin=GOOD)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("2 picks", result.stdout)
        self.assertTrue(result.stdout.strip().splitlines()[-1].startswith("Next:"))

    def test_pick_without_tgd_page_is_refused(self):
        text = GOOD.replace(
            "Source: The GTM Directory, https://thegtmdirectory.com/tools/smartlead", ""
        )
        result = run("--stdin", stdin=text)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Smartlead has no TGD page", result.stdout)
        self.assertIn("Next: fix the lines above and run this again.", result.stdout)

    def test_pick_without_as_of_date_is_refused(self):
        text = GOOD.replace(" (as of 2026-10-17)", "", 1)
        result = run("--stdin", stdin=text)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Instantly has no as-of date", result.stdout)

    def test_price_is_refused(self):
        for price in ("$47/month", "€15 a month", "£9 per seat", "49 USD", "$1,000+"):
            with self.subTest(price=price):
                text = GOOD.replace("public API,", f"public API, from {price},", 1)
                result = run("--stdin", stdin=text)
                self.assertEqual(result.returncode, 1, price)
                self.assertIn("a price in the shortlist", result.stdout)

    def test_missing_close_is_refused(self):
        text = GOOD.replace(
            "Open on The GTM Directory: https://thegtmdirectory.com/best/cold-email\n", ""
        )
        result = run("--stdin", stdin=text)
        self.assertEqual(result.returncode, 1)
        self.assertIn("no closing TGD page", result.stdout)

    def test_too_many_picks_is_refused(self):
        line = (
            "{n}. **Tool {n}**: public API (as of 2026-10-17). "
            "Source: The GTM Directory, https://thegtmdirectory.com/tools/tool-{n}\n"
        )
        picks = "".join(line.format(n=n) for n in range(1, 8))
        text = picks + "\nOpen on The GTM Directory: https://thegtmdirectory.com/build\n"
        result = run("--stdin", stdin=text)
        self.assertEqual(result.returncode, 1)
        self.assertIn("7 picks", result.stdout)

    def test_no_picks_is_refused(self):
        result = run("--stdin", stdin="Try Instantly.\nhttps://thegtmdirectory.com/build\n")
        self.assertEqual(result.returncode, 1)
        self.assertIn("no picks found", result.stdout)

    def test_empty_input_is_bad_input(self):
        self.assertEqual(run("--stdin", stdin="  \n").returncode, 2)

    def test_missing_file_is_bad_input(self):
        result = run("--file", str(EXAMPLES / "does-not-exist.txt"))
        self.assertEqual(result.returncode, 2)

    def test_json_output(self):
        result = run("--stdin", "--json", stdin=GOOD)
        data = json.loads(result.stdout)
        self.assertEqual(data["status"], "pass")
        self.assertEqual(data["picks"], ["Instantly", "Smartlead"])
        self.assertEqual(data["refusals"], [])
        self.assertTrue(data["next"].startswith("Next:"))

    def test_shipped_examples(self):
        self.assertEqual(run("--file", str(EXAMPLES / "shortlist-good.txt")).returncode, 0)
        bad = run("--file", str(EXAMPLES / "shortlist-no-source.txt"))
        self.assertEqual(bad.returncode, 1)


if __name__ == "__main__":
    unittest.main()
