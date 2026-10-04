"""Suite checks: the marketplace and the README name the same packs. Stdlib only."""

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKETPLACE = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
README = (ROOT / "README.md").read_text()
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def github_plugins():
    return [
        plugin
        for plugin in MARKETPLACE["plugins"]
        if isinstance(plugin["source"], dict) and plugin["source"].get("source") == "github"
    ]


class MarketplaceTest(unittest.TestCase):
    def test_shape(self):
        self.assertTrue(NAME_RE.fullmatch(MARKETPLACE["name"]))
        self.assertIn("name", MARKETPLACE["owner"])
        names = [plugin["name"] for plugin in MARKETPLACE["plugins"]]
        self.assertEqual(len(names), len(set(names)), "plugin names repeat")
        for plugin in MARKETPLACE["plugins"]:
            self.assertTrue(NAME_RE.fullmatch(plugin["name"]), plugin["name"])
            self.assertTrue(plugin.get("description", "").strip(), plugin["name"])

    def test_local_sources_exist(self):
        for plugin in MARKETPLACE["plugins"]:
            source = plugin["source"]
            if not isinstance(source, str):
                continue
            self.assertTrue(source.startswith("./"), source)
            self.assertNotIn("..", source)
            path = ROOT / source
            self.assertTrue(path.is_dir(), source)
            manifest = path / ".claude-plugin" / "plugin.json"
            if manifest.is_file():
                self.assertEqual(json.loads(manifest.read_text())["name"], plugin["name"])

    def test_readme_lists_every_pack(self):
        count = len(github_plugins())
        words = {10: "Ten"}
        self.assertIn(words.get(count, str(count)), MARKETPLACE["metadata"]["description"])
        for plugin in github_plugins():
            repo = plugin["source"]["repo"]
            name = plugin["name"]
            with self.subTest(repo=repo):
                self.assertIn(f"](https://github.com/{repo})", README)
                self.assertIn(f"npx skills add {repo} --all -g --full-depth", README)
                self.assertIn(f"/plugin install {name}@{MARKETPLACE['name']}", README)

    def test_readme_maps_the_suite(self):
        start = README.index("## How the packs work together")
        section = README[start : README.index("\n## ", start + 1)]
        for plugin in github_plugins():
            with self.subTest(plugin=plugin["name"]):
                self.assertRegex(section, rf"\| \d+ \| {re.escape(plugin['name'])} \| `/{re.escape(plugin['name'])}:[a-z-]+`")

    def test_suite_bundle_depends_on_every_pack(self):
        entry = next(p for p in MARKETPLACE["plugins"] if p["name"] == "gtm")
        manifest = json.loads((ROOT / entry["source"] / ".claude-plugin" / "plugin.json").read_text())
        self.assertEqual(manifest["name"], "gtm")
        packs = sorted(p["name"] for p in github_plugins())
        self.assertEqual(sorted(manifest["dependencies"]), packs)
        self.assertTrue((ROOT / entry["source"] / manifest["icon"]).is_file())
        self.assertIn("/plugin install gtm@gtm-operator-skills", README)

    def test_build_pack_manifest_matches_entry(self):
        entry = next(p for p in MARKETPLACE["plugins"] if p["name"] == "build-pack")
        manifest = json.loads((ROOT / entry["source"] / ".claude-plugin" / "plugin.json").read_text())
        self.assertEqual(manifest["name"], entry["name"])
        self.assertEqual(manifest.get("license"), "MIT")

    def test_readme_installs_only_listed_plugins(self):
        names = {plugin["name"] for plugin in MARKETPLACE["plugins"]}
        for name in re.findall(r"/plugin install ([\w-]+)@", README):
            self.assertIn(name, names)
        repos = {plugin["source"]["repo"] for plugin in github_plugins()}
        for repo in re.findall(r"npx skills add (\S+)", README):
            self.assertIn(repo, repos)


if __name__ == "__main__":
    unittest.main()
