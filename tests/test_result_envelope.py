"""Offline outcome checks for independently installed scorer envelopes."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "scripts/shared/scorer_envelope.py"


def adapter():
    spec = importlib.util.spec_from_file_location("envelope_test", ADAPTER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.envelope


class EnvelopeContract(unittest.TestCase):
    def test_refusal_has_recovery_and_single_action(self):
        env = adapter()({"ok": False, "reasons": ["missing source"],
                         "fixes": ["collect a dated URL"], "next": "Next: retry"},
                        tool="test", inputs={}, passed=False)
        self.assertEqual(next(iter(env)), "summary")
        self.assertEqual(env["status"], "abstain")
        self.assertEqual(env["abstain"]["to_collect"], ["collect a dated URL"])
        self.assertEqual(env["next_action"], "retry")
        self.assertLessEqual(len(env["summary"]), 150)  # conservative character cap

    def test_unknowns_are_not_zero_false_or_cold(self):
        build = adapter()
        for value in [0, False, "cold", "", [], {}]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                build({"rows": [{"score": value}]}, tool="test", inputs={}, passed=True,
                      unknowns=[{"field": "result.rows.0.score", "why": "not measured"}])
        env = build({"score": None}, tool="test", inputs={}, passed=True,
                    unknowns=[{"field": "result.score", "why": "not measured"}])
        self.assertEqual(env["status"], "partial")
        self.assertIsNone(env["result"]["score"])
        self.assertEqual(env["confidence"], {"value": None, "basis": "unmeasured"})

    def test_inputs_cannot_choose_status_or_verify_evidence(self):
        env = adapter()({"status": "ok", "confidence": 1, "evidence": ["a claim"]},
                        tool="test", inputs={"status": "ok"}, passed=False)
        self.assertEqual(env["status"], "abstain")
        self.assertEqual(env["evidence"], [])
        self.assertEqual(env["result"]["confidence"], 1)
        self.assertTrue(env["limits"])

    def test_receipt_hashes_inputs_not_outputs(self):
        build = adapter()
        one = build({}, tool="test", inputs={"a": 1, "b": 2}, passed=True)
        two = build({"score": 7}, tool="test", inputs={"b": 2, "a": 1}, passed=True)
        three = build({}, tool="test", inputs={"a": 2}, passed=True)
        self.assertEqual(one["receipt"]["inputs_hash"], two["receipt"]["inputs_hash"])
        self.assertNotEqual(one["receipt"]["inputs_hash"], three["receipt"]["inputs_hash"])
        self.assertIsNone(one["receipt"]["model"])
        self.assertEqual(one["receipt"]["cost"], 0)


    def test_receipt_hash_includes_scoring_date_and_assumptions(self):
        build = adapter()
        one = build({}, tool="test", inputs={}, passed=True, as_of="2026-11-20")
        two = build({}, tool="test", inputs={}, passed=True, as_of="2026-11-21")
        three = build({}, tool="test", inputs={}, passed=True, as_of="2026-11-20",
                      assumptions=[{"name": "window", "value": 90, "source": "default"}])
        self.assertNotEqual(one["receipt"]["inputs_hash"], two["receipt"]["inputs_hash"])
        self.assertNotEqual(one["receipt"]["inputs_hash"], three["receipt"]["inputs_hash"])


class ScorerCoverage(unittest.TestCase):
    def test_primary_scorers_emit_envelope(self):
        cases = []
        for pack in sorted((ROOT / "skills").iterdir()):
            if not pack.is_dir():
                continue
            scripts = sorted(p for p in pack.rglob("scripts/score*.py")
                             if p.name != "scorer_envelope.py")
            # Ancillary cold-email subject/reply/list graders are a later slice.
            script = next((p for p in scripts if p.name == "score_letter.py"), None)
            if script is None:
                script = next((p for p in scripts if p.name != "score_anchor.py"), None)
            if script is None:
                script = next(pack.rglob("scripts/check.py"))
            base = script.parent.parent
            example = next((p for p in sorted(base.glob("examples/*good*")) if p.is_file()), None)
            if pack.name == "pricing":
                example = base / "examples/price-good.json"
            if script.name == "check.py":
                args = ["--html-file", str(base / "examples/thin-home.html"),
                        "--page-url", "https://example.org/"]
            else:
                args = ["--file", str(example)]
            if pack.name == "signal-with-a-link":
                args += ["--as-of", "2026-10-08"]
            if pack.name == "proof-assets":
                args += ["--as-of", "2026-10-17"]
            if pack.name == "psp":
                args += ["--today", "2026-10-07"]
            cases.append((script, args))
        self.assertEqual(len(cases), 19)
        for script, args in cases:
            with self.subTest(script=script):
                proc = subprocess.run([sys.executable, str(script), *args, "--json"],
                                      capture_output=True, text=True)
                self.assertIn(proc.returncode, (0, 1), proc.stderr)
                env = json.loads(proc.stdout)
                self.assertEqual(next(iter(env)), "summary")
                self.assertEqual(env["status"], "abstain" if proc.returncode == 1 else
                                 "partial" if env["unknowns"] else "ok")
                self.assertIsInstance(env["next_action"], str)
                self.assertTrue(env["next_action"])
                self.assertIsInstance(env["result"], dict)
                self.assertTrue(env["limits"])
                self.assertLessEqual(len(env["summary"]), 150)
                validated = subprocess.run(
                    ["node", "--input-type=module", "-e",
                     "import {validateEnvelope} from './scripts/shared/result-envelope/index.mjs';"
                     "let s='';for await(const c of process.stdin)s+=c;"
                     "const r=validateEnvelope(JSON.parse(s));"
                     "if(!r.ok){console.error(JSON.stringify(r));process.exit(1)}"],
                    input=proc.stdout, capture_output=True, text=True, cwd=ROOT)
                self.assertEqual(validated.returncode, 0, validated.stderr)

    def test_missing_inputs_abstain_for_priority_packs(self):
        scripts = ["psp/scripts/score_psp.py", "pricing/scripts/score_price.py",
                   "prospect-list/skills/who-to-contact/scripts/score.py",
                   "signal-with-a-link/skills/signal-with-a-link/scripts/score.py"]
        for script in scripts:
            with self.subTest(script=script):
                proc = subprocess.run([sys.executable, str(ROOT / "skills" / script),
                                       "--stdin", "--json"], input=json.dumps({}),
                                      capture_output=True, text=True)
                self.assertEqual(proc.returncode, 1, proc.stderr)
                env = json.loads(proc.stdout)
                self.assertEqual(env["status"], "abstain")
                self.assertTrue(env["abstain"]["reason"])
                self.assertTrue(env["abstain"]["to_collect"])
                self.assertIsInstance(env["next_action"], str)


class InstalledSignal(unittest.TestCase):
    def run_signal(self, draft):
        source = ROOT / "skills/signal-with-a-link/skills/signal-with-a-link"
        with tempfile.TemporaryDirectory() as directory:
            installed = Path(directory) / "signal"
            shutil.copytree(source, installed)
            process = subprocess.run([sys.executable, str(installed / "scripts/score.py"),
                                      "--stdin", "--json", "--as-of", "2026-11-22"],
                                     input=json.dumps(draft), text=True, capture_output=True,
                                     cwd=directory)
        self.assertIn(process.returncode, (0, 1), process.stderr)
        return json.loads(process.stdout)

    def test_syntax_pass_does_not_claim_verified_source(self):
        env = self.run_signal({"event": "Announced a new sales office", "url": "https://example.org/news",
                               "date": "2026-11-20", "verified": True,
                               "retrieved_at": "2026-11-22T00:00:00Z"})
        self.assertEqual(env["status"], "partial")
        self.assertFalse(env["evidence"][0]["verified"])
        self.assertNotIn("retrieved_at", env["evidence"][0])
        self.assertIsNone(env["result"]["source_verified"])
        self.assertEqual(env["receipt"]["as_of"], "2026-11-22")

    def test_no_source_abstains(self):
        env = self.run_signal({"event": "Announced a new sales office", "intent_score": 90})
        self.assertEqual(env["status"], "abstain")
        self.assertTrue(env["abstain"]["to_collect"])
        self.assertEqual(env["evidence"], [])


if __name__ == "__main__":
    unittest.main()
