"""Suite checker hygiene rules, on throwaway packs. Stdlib and local git only."""

import importlib.util
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("check_suite", ROOT / "scripts" / "check_suite.py")
check_suite = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(check_suite)

MANIFEST = {
    "name": "sample",
    "repository": "https://github.com/example/sample",
    "license": "MIT",
    "documentationUrl": "https://github.com/example/sample#readme",
    "supportUrl": "https://github.com/example/sample/issues",
}


class HygieneTest(unittest.TestCase):
    def pack(self, security=True, icon=True):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / ".claude-plugin").mkdir()
        if security:
            (root / "SECURITY.md").write_text("# Security\n")
        if icon:
            (root / ".claude-plugin" / "icon.png").write_bytes(b"\x89PNG\r\n\x1a\n")
        return root

    def test_complete_pack_passes(self):
        self.assertEqual(check_suite.hygiene(self.pack(), dict(MANIFEST)), [])

    def test_missing_security_md(self):
        self.assertIn("missing SECURITY.md", check_suite.hygiene(self.pack(security=False), dict(MANIFEST)))

    def test_missing_default_icon(self):
        problems = check_suite.hygiene(self.pack(icon=False), dict(MANIFEST))
        self.assertIn("missing icon .claude-plugin/icon.png", problems)

    def test_manifest_icon_must_exist(self):
        manifest = dict(MANIFEST, icon="assets/icon.png")
        self.assertIn("missing icon assets/icon.png", check_suite.hygiene(self.pack(), manifest))
        manifest = dict(MANIFEST, icon="../outside.png")
        self.assertIn("missing icon ../outside.png", check_suite.hygiene(self.pack(), manifest))

    def test_manifest_links(self):
        manifest = {"name": "sample", "license": "MIT"}
        problems = check_suite.hygiene(self.pack(), manifest)
        self.assertIn("plugin.json lacks repository, documentationUrl, supportUrl", problems)

    @unittest.skipUnless(shutil.which("git"), "git not installed")
    def test_tracked_bytecode(self):
        root = self.pack()
        cache = root / "scripts" / "__pycache__"
        cache.mkdir(parents=True)
        (cache / "x.cpython-311.pyc").write_bytes(b"\0")
        (root / "stray.pyc").write_bytes(b"\0")
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        self.assertEqual(check_suite.tracked_bytecode(root), [], "untracked bytecode is ignored")
        subprocess.run(["git", "-C", str(root), "add", "-f", "."], check=True)
        tracked = check_suite.tracked_bytecode(root)
        self.assertEqual(sorted(tracked), ["scripts/__pycache__/x.cpython-311.pyc", "stray.pyc"])
        self.assertTrue(any(p.startswith("tracked bytecode") for p in check_suite.hygiene(root, dict(MANIFEST))))


if __name__ == "__main__":
    unittest.main()
