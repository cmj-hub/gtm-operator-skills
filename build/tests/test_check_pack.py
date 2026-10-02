"""Gate tests. Stdlib only. Secret-shaped strings are built in memory."""

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_pack.py"

SKILL = """---
name: sample-pack
description: Use when the sample pack is under test.
models: ""
---

# Sample

One job.
"""

README = """# Sample job

One artifact. This pack does not invent a second job.

```bash
npx skills add example/sample --all -g --full-depth
```
"""

LICENSE = "MIT License\n\nCopyright (c) 2026 Jay Mount Consulting\n"


def load():
    spec = importlib.util.spec_from_file_location("check_pack", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def knowledge(**overrides):
    card = {
        "job": "Pain",
        "portal_course": "pain-signal-profiles",
        "portal_fact": "A persona describes who could buy. A profile describes who is in pain.",
        "tgd_url": "https://thegtmdirectory.com/category/prospecting-sales-intelligence",
        "outside_repo": "owner/name",
        "outside_artifact": "a scored persona file",
        "gtm_context": {"query": "pain profile"},
        "kept": True,
        "passage": "The operator keeps the sentence that names the pain.",
        "note": "",
    }
    card.update(overrides)
    return card


def design(**overrides):
    card = {
        "artifact": "one pain brief",
        "refusal": "a persona is not a pain brief",
        "group": "foundation",
        "topics": ["pain", "foundation", "agent-skills"],
        "freedom": [
            {"step": "score the brief", "level": "low", "script": "scripts/score.py"},
            {"step": "choose a phrase", "level": "high"},
        ],
    }
    card.update(overrides)
    return card


class CheckPackTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load()

    def run_main(self, argv):
        out = io.StringIO()
        err = io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = self.mod.main(argv)
        return code, out.getvalue(), err.getvalue()

    def write_card(self, directory, name, card):
        path = directory / name
        path.write_text(json.dumps(card))
        return path

    def make_pack(self, files):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        for name, content in files.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        return root

    def base_pack(self, **extra):
        files = {"SKILL.md": SKILL, "README.md": README, "LICENSE": LICENSE}
        files.update(extra)
        return self.make_pack(files)

    def test_knowledge_ok(self):
        root = self.make_pack({})
        card = self.write_card(root, "k.json", knowledge())
        code, out, _ = self.run_main(["knowledge", str(card)])
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), "knowledge ok")

    def test_knowledge_fact_bounds_and_lesson(self):
        root = self.make_pack({})
        short = self.write_card(root, "short.json", knowledge(portal_fact="too short"))
        code, out, _ = self.run_main(["knowledge", str(short)])
        self.assertEqual(code, 1)
        self.assertIn("Refusal: portal_fact is shorter than 20 characters", out)

        long = self.write_card(root, "long.json", knowledge(portal_fact="x" * 601))
        code, out, _ = self.run_main(["knowledge", str(long)])
        self.assertEqual(code, 1)
        self.assertIn("Refusal: portal_fact is longer than 600 characters", out)

        edge = self.write_card(root, "edge.json", knowledge(portal_fact="x" * 600))
        code, out, _ = self.run_main(["knowledge", str(edge)])
        self.assertEqual(code, 0, out)

        pasted = self.write_card(
            root,
            "pasted.json",
            knowledge(portal_fact="A real fact line.\n## Lesson\nmore"),
        )
        code, out, _ = self.run_main(["knowledge", str(pasted)])
        self.assertEqual(code, 1)
        self.assertIn("Refusal: portal_fact is a pasted lesson", out)

    def test_knowledge_sources_and_kept(self):
        root = self.make_pack({})
        bad_url = self.write_card(
            root, "url.json", knowledge(tgd_url="https://example.com/category/foo")
        )
        code, out, _ = self.run_main(["knowledge", str(bad_url)])
        self.assertIn("Refusal: tgd_url is not a directory category", out)
        self.assertEqual(code, 1)

        bad_repo = self.write_card(root, "repo.json", knowledge(outside_repo="just-owner"))
        code, out, _ = self.run_main(["knowledge", str(bad_repo)])
        self.assertIn("Refusal: outside_repo is not owner/name", out)

        empty_passage = self.write_card(root, "pass.json", knowledge(passage="  "))
        code, out, _ = self.run_main(["knowledge", str(empty_passage)])
        self.assertIn("Refusal: kept a passage and passage is empty", out)

        dropped = self.write_card(root, "drop.json", knowledge(kept=False, passage="", note=""))
        code, out, _ = self.run_main(["knowledge", str(dropped)])
        self.assertIn("Refusal: discarded the graph and note is empty", out)

        noted = self.write_card(
            root,
            "noted.json",
            knowledge(kept=False, passage="", note="The graph was empty."),
        )
        code, out, _ = self.run_main(["knowledge", str(noted)])
        self.assertEqual(code, 0, out)

    def test_design_ok_and_refusals(self):
        root = self.make_pack({})
        card = self.write_card(root, "d.json", design())
        code, out, _ = self.run_main(["design", str(card)])
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), "design ok")

        bad_group = self.write_card(root, "g.json", design(group="funnel"))
        code, out, _ = self.run_main(["design", str(bad_group)])
        self.assertIn("Refusal: group is not a catalog group", out)

        topics = self.write_card(root, "t.json", design(topics=["pain", "foundation"]))
        code, out, _ = self.run_main(["design", str(topics)])
        self.assertIn("Refusal: topics must be three, including agent-skills", out)

        missing_tag = self.write_card(
            root, "tag.json", design(topics=["pain", "foundation", "skills"])
        )
        code, out, _ = self.run_main(["design", str(missing_tag)])
        self.assertIn("Refusal: topics must be three, including agent-skills", out)

        low = self.write_card(
            root,
            "low.json",
            design(freedom=[{"step": "score", "level": "low"}]),
        )
        code, out, _ = self.run_main(["design", str(low)])
        self.assertIn("Refusal: a low-freedom step names no script", out)

        medium = self.write_card(
            root,
            "med.json",
            design(freedom=[{"step": "choose", "level": "medium"}]),
        )
        code, out, _ = self.run_main(["design", str(medium)])
        self.assertEqual(code, 0, out)

    def test_pack_public_ok(self):
        root = self.base_pack()
        code, out, _ = self.run_main(["pack", str(root), "--public"])
        self.assertEqual(code, 0, out)
        self.assertEqual(out.strip(), "pack ok")

    def test_pack_license_sides(self):
        op = "LicenseRef-JMC-Operator-Pass\n"
        grant = "Permission is hereby granted, free of charge, to any person\n"
        public_bad = self.base_pack(LICENSE="MIT\n" + op)
        code, out, _ = self.run_main(["pack", str(public_bad), "--public"])
        self.assertIn("Refusal: public LICENSE carries the Operator Pass license", out)
        self.assertEqual(code, 1)

        missing_mit = self.base_pack(LICENSE="See the suite license.\n")
        code, out, _ = self.run_main(["pack", str(missing_mit), "--public"])
        self.assertIn("Refusal: public LICENSE is missing MIT", out)

        private_ok = self.base_pack(LICENSE=op + "Use with an active pass.\n")
        code, out, _ = self.run_main(["pack", str(private_ok), "--private"])
        self.assertEqual(code, 0, out)

        private_grant = self.base_pack(LICENSE=op + grant)
        code, out, _ = self.run_main(["pack", str(private_grant), "--private"])
        self.assertIn("Refusal: private LICENSE carries the MIT grant", out)

        private_missing = self.base_pack()
        code, out, _ = self.run_main(["pack", str(private_missing), "--private"])
        self.assertIn("Refusal: private LICENSE is missing the Operator Pass license", out)

    def test_pack_secrets(self):
        cloud = "AK" + "IA" + ("A" * 16)
        vendor = "sk-" + "ant-" + ("a" * 8)
        pem = "-----BEG" + "IN RSA PRIVATE KEY-----\nline\n"
        assigned = "API_" + "KEY=" + ("s" * 12) + "\n"

        env_pack = self.base_pack()
        (env_pack / ".env").write_text("X=1\n")
        code, out, _ = self.run_main(["pack", str(env_pack), "--public"])
        self.assertIn("Refusal: .env file in the pack", out)
        self.assertNotIn("X=1", out)

        for label, text in (
            ("cloud.md", "# Notes\n" + cloud + "\n"),
            ("vendor.md", "# Notes\n" + vendor + "\n"),
            ("key.md", "# Notes\n" + pem),
            ("assigned.md", "# Notes\n" + assigned),
        ):
            pack = self.base_pack(**{label: text})
            code, out, _ = self.run_main(["pack", str(pack), "--public"])
            self.assertEqual(code, 1, label)
            self.assertIn(f"Refusal: key material in {label}", out)
            self.assertNotIn(cloud, out)
            self.assertNotIn(vendor, out)

    def test_skill_shape(self):
        missing_models = SKILL.replace('models: ""\n', "")
        pack = self.base_pack(**{"SKILL.md": missing_models})
        code, out, _ = self.run_main(["pack", str(pack), "--public"])
        self.assertIn("Refusal: SKILL.md is missing models", out)

        body = "\n".join(f"line {i}" for i in range(500))
        long_skill = (
            '---\nname: sample-pack\ndescription: Use when testing.\nmodels: ""\n---\n'
            + body
            + "\n"
        )
        pack = self.base_pack(**{"SKILL.md": long_skill})
        code, out, _ = self.run_main(["pack", str(pack), "--public"])
        self.assertIn("Refusal: SKILL.md body is 500 lines or more", out)

        short_body = "\n".join(f"line {i}" for i in range(20))
        short_skill = (
            '---\nname: sample-pack\ndescription: Use when testing.\nmodels: ""\n---\n'
            + short_body
            + "\n"
        )
        pack = self.base_pack(**{"SKILL.md": short_skill})
        code, out, _ = self.run_main(["pack", str(pack), "--public"])
        self.assertEqual(code, 0, out)

    def test_reference_contents_and_links(self):
        titles = ["Alpha", "Beta"]
        lines = ["# Ref", "", "## Contents", "", "- Alpha", "- Beta", ""]
        for title in titles:
            lines.extend([f"## {title}", "text", ""])
        while len(lines) <= 102:
            lines.append("pad")
        good = "\n".join(lines) + "\n"
        skill = SKILL.replace(
            "# Sample\n\nOne job.\n",
            "# Sample\n\nOne job.\n\nRead [ref](ref.md).\n",
        )
        pack = self.base_pack(**{"SKILL.md": skill, "ref.md": good})
        code, out, _ = self.run_main(["pack", str(pack), "--public"])
        self.assertEqual(code, 0, out)

        bad_lines = ["# Ref", "", "intro", ""]
        bad_lines.extend(["## Alpha", "text", ""])
        while len(bad_lines) <= 102:
            bad_lines.append("pad")
        pack = self.base_pack(**{"SKILL.md": skill, "ref.md": "\n".join(bad_lines) + "\n"})
        code, out, _ = self.run_main(["pack", str(pack), "--public"])
        self.assertIn("Refusal: ref.md is over 100 lines and has no Contents", out)

        partial = good.replace("- Beta\n", "")
        pack = self.base_pack(**{"SKILL.md": skill, "ref.md": partial})
        code, out, _ = self.run_main(["pack", str(pack), "--public"])
        self.assertIn("Refusal: ref.md Contents is missing heading Beta", out)

        nested_skill = SKILL.replace(
            "# Sample\n\nOne job.\n",
            "# Sample\n\nRead [knowledge](knowledge.md).\n",
        )
        pack = self.base_pack(
            **{
                "SKILL.md": nested_skill,
                "knowledge.md": "See [other](other.md).\n",
                "other.md": "# Other\n\nA note.\n",
            }
        )
        code, out, _ = self.run_main(["pack", str(pack), "--public"])
        self.assertIn("Refusal: knowledge.md links other.md and SKILL.md does not", out)

    def test_readme_landing(self):
        pack = self.base_pack(**{"README.md": "No heading yet.\n\nThis pack does not ship.\n\nnpx skills add example/sample\n"})
        code, out, _ = self.run_main(["pack", str(pack), "--public"])
        self.assertIn("Refusal: README is missing an H1", out)

        pack = self.base_pack(**{"README.md": "# Job\n\nAn artifact and a second sentence.\n\nnpx skills add example/sample\n"})
        code, out, _ = self.run_main(["pack", str(pack), "--public"])
        self.assertIn("Refusal: README is missing a refusal", out)

        pack = self.base_pack(**{"README.md": "# Job\n\nThis pack does not ship a second artifact.\n"})
        code, out, _ = self.run_main(["pack", str(pack), "--public"])
        self.assertIn("Refusal: README is missing npx skills add", out)

    def test_imports(self):
        clean = "import json\nimport argparse\n"
        pack = self.base_pack(**{"scripts/run.py": clean})
        code, out, _ = self.run_main(["pack", str(pack), "--public"])
        self.assertEqual(code, 0, out)

        local = "import helper\n"
        pack = self.base_pack(**{"scripts/run.py": local, "scripts/helper.py": "VALUE = 1\n"})
        code, out, _ = self.run_main(["pack", str(pack), "--public"])
        self.assertEqual(code, 0, out)

        third = "import requests\n"
        pack = self.base_pack(**{"scripts/run.py": third})
        code, out, _ = self.run_main(["pack", str(pack), "--public"])
        self.assertIn("Refusal: scripts/run.py imports requests with no install line", out)

        commented = "# pip install requests\nimport requests\n"
        pack = self.base_pack(**{"scripts/run.py": commented})
        code, out, _ = self.run_main(["pack", str(pack), "--public"])
        self.assertEqual(code, 0, out)

        far = "\n".join(["# note"] * 6 + ["import requests"]) + "\n"
        pack = self.base_pack(**{"scripts/run.py": far})
        code, out, _ = self.run_main(["pack", str(pack), "--public"])
        self.assertIn("Refusal: scripts/run.py imports requests with no install line", out)

    def test_all_and_usage(self):
        root = self.base_pack()
        k = self.write_card(root, "k.json", knowledge())
        d = self.write_card(root, "d.json", design())
        code, out, _ = self.run_main(
            ["all", str(root), "--public", "--knowledge", str(k), "--design", str(d)]
        )
        self.assertEqual(code, 0, out)
        self.assertIn("knowledge ok", out)
        self.assertIn("design ok", out)
        self.assertIn("pack ok", out)

        with self.assertRaises(SystemExit) as ctx:
            self.run_main(["pack", str(root)])
        self.assertEqual(ctx.exception.code, 2)

    def test_build_directory(self):
        code, out, _ = self.run_main(["pack", str(ROOT), "--public"])
        self.assertEqual(code, 0, out)
        code, out, _ = self.run_main(
            [
                "all",
                str(ROOT),
                "--public",
                "--knowledge",
                str(ROOT / "examples" / "knowledge.json"),
                "--design",
                str(ROOT / "examples" / "design.json"),
            ]
        )
        self.assertEqual(code, 0, out)

    def test_bad_json(self):
        root = self.make_pack({})
        path = root / "k.json"
        path.write_text("{")
        code, out, _ = self.run_main(["knowledge", str(path)])
        self.assertEqual(code, 1)
        self.assertIn("Refusal: card is not a JSON object", out)


if __name__ == "__main__":
    unittest.main()
