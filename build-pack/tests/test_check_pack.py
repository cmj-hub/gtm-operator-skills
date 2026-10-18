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

AGENT = """---
name: reviewer
description: Use when a draft needs a second read.
tools:
  - Read
---
"""

LICENSE = "MIT License\n\nCopyright (c) 2026 Jay Mount Consulting\n"

SECURITY = "# Security\n\nNo script opens a network connection.\n"


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
        "ordered": False,
        "quality": False,
        "freedom": [
            {
                "step": "score the brief",
                "level": "low",
                "script": "scripts/score.py",
                "if_different": "nothing-much",
            },
            {"step": "choose a phrase", "level": "high", "if_different": "nothing-much"},
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
        files = {"SKILL.md": SKILL, "README.md": README, "LICENSE": LICENSE, "SECURITY.md": SECURITY}
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
            design(freedom=[{"step": "choose", "level": "medium", "if_different": "nothing-much"}]),
        )
        code, out, _ = self.run_main(["design", str(medium)])
        self.assertIn("Refusal: a medium-freedom step names no template", out)
        self.assertEqual(code, 1)

        shaped = self.write_card(
            root,
            "shaped.json",
            design(
                freedom=[
                    {
                        "step": "shape the report",
                        "level": "medium",
                        "template": "format and include_charts",
                        "if_different": "nothing-much",
                    }
                ]
            ),
        )
        code, out, _ = self.run_main(["design", str(shaped)])
        self.assertEqual(code, 0, out)

        loose = self.write_card(
            root,
            "loose.json",
            design(
                freedom=[
                    {
                        "step": "score",
                        "level": "low",
                        "script": "scripts/score.py",
                        "if_different": "nothing-much",
                    }
                ]
            ),
        )
        code, out, _ = self.run_main(["design", str(loose)])
        self.assertEqual(code, 0, out)

        send = self.write_card(
            root,
            "send.json",
            design(freedom=[{"step": "send", "level": "high", "if_different": "consequential"}]),
        )
        code, out, _ = self.run_main(["design", str(send)])
        self.assertIn("Refusal: a consequential step is not low freedom", out)

        missing_flag = self.write_card(root, "flag.json", design())
        payload = json.loads(missing_flag.read_text())
        del payload["ordered"]
        missing_flag.write_text(json.dumps(payload))
        code, out, _ = self.run_main(["design", str(missing_flag)])
        self.assertIn("Refusal: card is missing ordered", out)

    def test_pack_public_ok(self):
        root = self.base_pack()
        code, out, _ = self.run_main(["pack", str(root), "--public"])
        self.assertEqual(code, 0, out)
        self.assertEqual(out.strip(), "pack ok")

    def test_public_pack_needs_security_md(self):
        root = self.base_pack()
        (root / "SECURITY.md").unlink()
        code, out, _ = self.run_main(["pack", str(root), "--public"])
        self.assertEqual(code, 1)
        self.assertIn("Refusal: public pack is missing SECURITY.md", out)
        (root / "SECURITY.md").write_text("  \n")
        code, out, _ = self.run_main(["pack", str(root), "--public"])
        self.assertIn("Refusal: SECURITY.md is empty", out)

    def test_private_pack_may_skip_security_md(self):
        op = "LicenseRef-JMC-Operator-Pass\nUse with an active pass.\n"
        root = self.base_pack(LICENSE=op)
        (root / "SECURITY.md").unlink()
        code, out, _ = self.run_main(["pack", str(root), "--private"])
        self.assertEqual(code, 0, out)

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

        bad_name = SKILL.replace("name: sample-pack", "name: Sample_Pack")
        pack = self.base_pack(**{"SKILL.md": bad_name})
        code, out, _ = self.run_main(["pack", str(pack), "--public"])
        self.assertIn("Refusal: SKILL.md name is not a lowercase hyphen name", out)

        long_name = SKILL.replace("name: sample-pack", "name: " + ("a" * 65))
        pack = self.base_pack(**{"SKILL.md": long_name})
        code, out, _ = self.run_main(["pack", str(pack), "--public"])
        self.assertIn("Refusal: SKILL.md name is not a lowercase hyphen name", out)

        name_64 = SKILL.replace("name: sample-pack", "name: " + ("a" * 64))
        pack = self.base_pack(**{"SKILL.md": name_64})
        code, out, _ = self.run_main(["pack", str(pack), "--public"])
        self.assertEqual(code, 0, out)

        no_when = SKILL.replace(
            "description: Use when the sample pack is under test.",
            "description: Scores one brief.",
        )
        pack = self.base_pack(**{"SKILL.md": no_when})
        code, out, _ = self.run_main(["pack", str(pack), "--public"])
        self.assertIn("Refusal: SKILL.md description does not say when", out)

        empty_desc = SKILL.replace(
            "description: Use when the sample pack is under test.",
            'description: ""',
        )
        pack = self.base_pack(**{"SKILL.md": empty_desc})
        code, out, _ = self.run_main(["pack", str(pack), "--public"])
        self.assertIn("Refusal: SKILL.md description is empty", out)

        prefix = "Use when "
        over = SKILL.replace(
            "description: Use when the sample pack is under test.",
            "description: " + prefix + ("y" * (1025 - len(prefix))),
        )
        pack = self.base_pack(**{"SKILL.md": over})
        code, out, _ = self.run_main(["pack", str(pack), "--public"])
        self.assertIn("Refusal: SKILL.md description is over 1024 characters", out)

        at_cap = SKILL.replace(
            "description: Use when the sample pack is under test.",
            "description: " + prefix + ("y" * (1024 - len(prefix))),
        )
        pack = self.base_pack(**{"SKILL.md": at_cap})
        code, out, _ = self.run_main(["pack", str(pack), "--public"])
        self.assertEqual(code, 0, out)

        folded = """---
name: sample-pack
description: >
  Write one brief and refuse a persona.
  Use when the operator has a profile.
models: ""
---

# Sample

One job.
"""
        pack = self.base_pack(**{"SKILL.md": folded})
        code, out, _ = self.run_main(["pack", str(pack), "--public"])
        self.assertEqual(code, 0, out)

        folded_bare = folded.replace(
            "  Write one brief and refuse a persona.\n  Use when the operator has a profile.\n",
            "  Write one brief and refuse a persona.\n",
        )
        pack = self.base_pack(**{"SKILL.md": folded_bare})
        code, out, _ = self.run_main(["pack", str(pack), "--public"])
        self.assertIn("Refusal: SKILL.md description does not say when", out)

        folded_empty = folded.replace(
            "description: >\n  Write one brief and refuse a persona.\n  Use when the operator has a profile.\n",
            "description: >\n",
        )
        pack = self.base_pack(**{"SKILL.md": folded_empty})
        code, out, _ = self.run_main(["pack", str(pack), "--public"])
        self.assertIn("Refusal: SKILL.md description is empty", out)

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

        on_time = ["# Ref"]
        while len(on_time) < 99:
            on_time.append("pad")
        on_time.extend(["## Contents", "", "- Alpha", "", "## Alpha", "text"])
        pack = self.base_pack(**{"SKILL.md": skill, "ref.md": "\n".join(on_time) + "\n"})
        code, out, _ = self.run_main(["pack", str(pack), "--public"])
        self.assertEqual(code, 0, out)

        late = ["# Ref"]
        while len(late) < 100:
            late.append("pad")
        late.extend(["## Contents", "", "- Alpha", "", "## Alpha", "text"])
        pack = self.base_pack(**{"SKILL.md": skill, "ref.md": "\n".join(late) + "\n"})
        code, out, _ = self.run_main(["pack", str(pack), "--public"])
        self.assertIn("Refusal: ref.md Contents starts after line 100", out)

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

        prose = SKILL + "\nimport requests\n"
        pack = self.base_pack(**{"SKILL.md": prose})
        code, out, _ = self.run_main(["pack", str(pack), "--public"])
        self.assertEqual(code, 0, out)

        fenced = SKILL + "\n```python\nimport requests\n```\n"
        pack = self.base_pack(**{"SKILL.md": fenced})
        code, out, _ = self.run_main(["pack", str(pack), "--public"])
        self.assertIn("Refusal: SKILL.md imports requests with no install line", out)

        installed = SKILL + "\n```python\npip install requests\nimport requests\n```\n"
        pack = self.base_pack(**{"SKILL.md": installed})
        code, out, _ = self.run_main(["pack", str(pack), "--public"])
        self.assertEqual(code, 0, out)

        stdlib_fence = SKILL + "\n```python\nimport json\n```\n"
        pack = self.base_pack(**{"SKILL.md": stdlib_fence})
        code, out, _ = self.run_main(["pack", str(pack), "--public"])
        self.assertEqual(code, 0, out)

    def test_all_and_usage(self):
        root = self.base_pack(
            **{
                "SKILL.md": SKILL + "\n```bash\npython3 scripts/score.py\n```\n",
                "scripts/score.py": "print(1)\n",
            }
        )
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

    def test_ordered_and_quality(self):
        root = self.base_pack()
        k = self.write_card(root, "k.json", knowledge())
        ordered = self.write_card(root, "ordered.json", design(ordered=True))
        code, out, _ = self.run_main(
            ["all", str(root), "--public", "--knowledge", str(k), "--design", str(ordered)]
        )
        self.assertEqual(code, 1)
        self.assertIn("Refusal: SKILL.md is an ordered job with no checklist", out)
        self.assertNotIn("pack ok", out)

        listed = (
            SKILL
            + "\n```bash\npython3 scripts/score.py\n```\n\n## Checklist\n\nCopy this list.\n\n- [ ] 1. Do the job.\n\nGo back to step 1 if it fails.\n"
        )
        listed_root = self.base_pack(
            **{"SKILL.md": listed, "scripts/score.py": "print(1)\n"}
        )
        k = self.write_card(listed_root, "k.json", knowledge())
        ordered = self.write_card(listed_root, "ordered.json", design(ordered=True))
        code, out, _ = self.run_main(
            ["all", str(listed_root), "--public", "--knowledge", str(k), "--design", str(ordered)]
        )
        self.assertEqual(code, 0, out)

        bare = self.base_pack()
        k = self.write_card(bare, "k.json", knowledge())
        quality = self.write_card(bare, "quality.json", design(quality=True))
        code, out, _ = self.run_main(
            ["all", str(bare), "--public", "--knowledge", str(k), "--design", str(quality)]
        )
        self.assertIn("Refusal: quality job has no check-again loop", out)
        self.assertEqual(code, 1)

        checked = (
            SKILL
            + "\n```bash\npython3 scripts/score.py\n```\nRun the scorer, fix, and check again until it passes.\n"
        )
        checked_root = self.base_pack(
            **{"SKILL.md": checked, "scripts/score.py": "print(1)\n"}
        )
        k = self.write_card(checked_root, "k.json", knowledge())
        quality = self.write_card(checked_root, "quality.json", design(quality=True))
        code, out, _ = self.run_main(
            ["all", str(checked_root), "--public", "--knowledge", str(k), "--design", str(quality)]
        )
        self.assertEqual(code, 0, out)

        scored = self.base_pack(
            **{
                "SKILL.md": SKILL + "\n```bash\npython3 scripts/score.py\n```\n",
                "scripts/score.py": "print(1)\n",
                "scripts/score_job.py": "print(1)\n",
            }
        )
        k = self.write_card(scored, "k.json", knowledge())
        quality = self.write_card(scored, "quality.json", design(quality=True))
        code, out, _ = self.run_main(
            ["all", str(scored), "--public", "--knowledge", str(k), "--design", str(quality)]
        )
        self.assertEqual(code, 0, out)

    def test_install_doc_is_not_a_skill_reference(self):
        pack = self.base_pack(**{"INSTALL.md": "Unzip, then run install.sh.\n"})
        code, out, _ = self.run_main(["pack", str(pack), "--public"])
        self.assertEqual(code, 0, out)
        self.assertNotIn("INSTALL.md", out)

        orphan = self.base_pack(**{"notes.md": "# Notes\n\nA reference.\n"})
        code, out, _ = self.run_main(["pack", str(orphan), "--public"])
        self.assertIn("Refusal: notes.md is not linked from SKILL.md", out)
        self.assertEqual(code, 1)

    def test_low_script_is_the_command(self):
        root = self.base_pack()
        k = self.write_card(root, "k.json", knowledge())
        card = self.write_card(root, "d.json", design())
        code, out, _ = self.run_main(
            ["all", str(root), "--public", "--knowledge", str(k), "--design", str(card)]
        )
        self.assertIn("Refusal: scripts/score.py is not a command in a SKILL.md", out)
        self.assertEqual(code, 1)

        named = SKILL + "\n```bash\npython3 scripts/score.py --file draft.json\n```\n"
        missing = self.base_pack(**{"SKILL.md": named})
        k = self.write_card(missing, "k.json", knowledge())
        card = self.write_card(missing, "d.json", design())
        code, out, _ = self.run_main(
            ["all", str(missing), "--public", "--knowledge", str(k), "--design", str(card)]
        )
        self.assertIn("Refusal: scripts/score.py is missing", out)
        self.assertEqual(code, 1)

        bound = self.base_pack(**{"SKILL.md": named, "scripts/score.py": "print(1)\n"})
        k = self.write_card(bound, "k.json", knowledge())
        card = self.write_card(bound, "d.json", design())
        code, out, _ = self.run_main(
            ["all", str(bound), "--public", "--knowledge", str(k), "--design", str(card)]
        )
        self.assertEqual(code, 0, out)

    def test_build_directory(self):
        code, out, _ = self.run_main(["pack", str(ROOT), "--public"])
        self.assertEqual(code, 0, out)
        sample = json.loads((ROOT / "examples" / "design.json").read_text())
        sample["freedom"][0]["script"] = "scripts/check_pack.py"
        card_root = self.make_pack({})
        card = self.write_card(card_root, "design.json", sample)
        code, out, _ = self.run_main(
            [
                "all",
                str(ROOT),
                "--public",
                "--knowledge",
                str(ROOT / "examples" / "knowledge.json"),
                "--design",
                str(card),
            ]
        )
        self.assertEqual(code, 0, out)

    def test_assigned_secret_needs_a_literal(self):
        name = "API" + "_KEY"
        for body in (
            f"{name} = os.environ['X']\n",
            f"{name} = os.getenv('X')\n",
            f"{name}_RE = re.compile(r'x')\n",
            f'{name} = ""\n',
            f"{name}=<your key>\n",
            f"if {name} == other:\n    pass\n",
        ):
            root = self.base_pack(**{"scripts/run.py": body})
            code, out, _ = self.run_main(["pack", str(root), "--public"])
            self.assertEqual(code, 0, body + out)
        root = self.base_pack(**{"scripts/run.py": f'    {name} = "abc123"\n'})
        code, out, _ = self.run_main(["pack", str(root), "--public"])
        self.assertIn("Refusal: key material in scripts/run.py", out)

    def test_env_example_is_allowed_and_scanned(self):
        root = self.base_pack(**{".env.example": "X=\n"})
        code, out, _ = self.run_main(["pack", str(root), "--public"])
        self.assertEqual(code, 0, out)
        root = self.base_pack(**{".env.example": "SECRET=abc123\n"})
        code, out, _ = self.run_main(["pack", str(root), "--public"])
        self.assertIn("Refusal: key material in .env.example", out)
        self.assertNotIn(".env file in the pack", out)

    def test_tests_import_pack_scripts(self):
        root = self.base_pack(
            **{
                "scripts/score_brief.py": "print(1)\n",
                "tests/test_score.py": "import score_brief\n",
            }
        )
        code, out, _ = self.run_main(["pack", str(root), "--public"])
        self.assertEqual(code, 0, out)

    def test_repo_docs_and_plugin_parts(self):
        long = "# Doc\n\n" + "line\n" * 120
        root = self.base_pack(
            **{
                "CHANGELOG.md": long,
                "CONTRIBUTING.md": "# Contributing\n",
                "agents/reviewer.md": AGENT + long,
                ".github/PULL_REQUEST_TEMPLATE.md": "# PR\n",
                "evals/fires/prompt.md": "---\nmax_turns: 6\n---\n\nWrite one.\n",
                "evals/fires/graders/fired.md": "---\ntype: tool_used\ntool: Skill\n---\n",
            }
        )
        code, out, _ = self.run_main(["pack", str(root), "--public"])
        self.assertEqual(code, 0, out)
        root = self.base_pack(**{"docs/CHANGELOG.md": "# Log\n"})
        code, out, _ = self.run_main(["pack", str(root), "--public"])
        self.assertIn("Refusal: docs/CHANGELOG.md is not linked from SKILL.md", out)

    def test_skill_links_another_skill(self):
        skill = SKILL.replace("One job.", "Next: [other](skills/other/SKILL.md).")
        other = SKILL.replace("sample-pack", "other").replace(
            "One job.", "See [ref](ref.md)."
        )
        root = self.base_pack(
            **{
                "SKILL.md": skill,
                "skills/other/SKILL.md": other,
                "skills/other/ref.md": "# Ref\n",
            }
        )
        code, out, _ = self.run_main(["pack", str(root), "--public"])
        self.assertEqual(code, 0, out)

    def test_name_and_description_rules(self):
        for name in ("claude-helper", "my-anthropic-pack", "-lead", "a--b", "x" * 65):
            root = self.base_pack(**{"SKILL.md": SKILL.replace("sample-pack", name)})
            code, out, _ = self.run_main(["pack", str(root), "--public"])
            self.assertEqual(code, 1, name)
        root = self.base_pack(
            **{"SKILL.md": SKILL.replace("Use when", "Use when the <ICP> asks;")}
        )
        code, out, _ = self.run_main(["pack", str(root), "--public"])
        self.assertIn("Refusal: SKILL.md description carries an XML tag", out)
        self.assertEqual(out.count("Refusal:"), 1)

    def test_plugin_manifest(self):
        manifest = {"name": "sample", "version": "0.1.0"}
        root = self.base_pack(**{".claude-plugin/plugin.json": json.dumps(manifest)})
        code, out, _ = self.run_main(["pack", str(root), "--public"])
        self.assertIn(
            "Refusal: plugin.json installs no skills; list the SKILL.md folder in skills",
            out,
        )
        manifest["skills"] = ["./"]
        root = self.base_pack(**{".claude-plugin/plugin.json": json.dumps(manifest)})
        code, out, _ = self.run_main(["pack", str(root), "--public"])
        self.assertEqual(code, 0, out)
        root = self.make_pack(
            {
                "skills/sample-pack/SKILL.md": SKILL,
                "README.md": README,
                "LICENSE": LICENSE,
                "SECURITY.md": SECURITY,
                ".claude-plugin/plugin.json": json.dumps({"name": "sample"}),
            }
        )
        code, out, _ = self.run_main(["pack", str(root), "--public"])
        self.assertEqual(code, 0, out)
        bad = {"name": "Sample", "version": "1", "skills": ["../x"]}
        root = self.base_pack(**{".claude-plugin/plugin.json": json.dumps(bad)})
        code, out, _ = self.run_main(["pack", str(root), "--public"])
        self.assertIn("Refusal: plugin.json name is not a lowercase hyphen name", out)
        self.assertIn("Refusal: plugin.json version is not semver", out)
        self.assertIn("Refusal: plugin.json skills path ../x leaves the pack", out)
        root = self.base_pack(**{".claude-plugin/plugin.json": "["})
        code, out, _ = self.run_main(["pack", str(root), "--public"])
        self.assertIn("Refusal: plugin.json is not a JSON object", out)

    def test_every_skill_loads(self):
        manifest = json.dumps({"name": "sample"})
        root = self.make_pack(
            {
                "skills/sample-pack/SKILL.md": SKILL,
                "main/SKILL.md": SKILL.replace("sample-pack", "main"),
                "README.md": README,
                "LICENSE": LICENSE,
                "SECURITY.md": SECURITY,
                ".claude-plugin/plugin.json": manifest,
            }
        )
        code, out, _ = self.run_main(["pack", str(root), "--public"])
        self.assertIn(
            "Refusal: main/SKILL.md does not load; move it to skills/<name>/ "
            "or list its folder in plugin.json skills",
            out,
        )
        (root / ".claude-plugin" / "plugin.json").write_text(
            json.dumps({"name": "sample", "skills": ["./main/"]})
        )
        code, out, _ = self.run_main(["pack", str(root), "--public"])
        self.assertEqual(code, 0, out)

    def test_agent_frontmatter(self):
        root = self.base_pack(**{"agents/reviewer.md": AGENT})
        code, out, _ = self.run_main(["pack", str(root), "--public"])
        self.assertEqual(code, 0, out)
        bad = AGENT.replace("tools:", "permissionMode: auto\nallowed-tools:")
        root = self.base_pack(**{"agents/reviewer.md": bad})
        code, out, _ = self.run_main(["pack", str(root), "--public"])
        self.assertIn("Refusal: agents/reviewer.md uses allowed-tools; an agent takes tools", out)
        self.assertIn(
            "Refusal: agents/reviewer.md sets permissionMode, which a plugin agent ignores", out
        )
        root = self.base_pack(**{"agents/reviewer.md": "# Reviewer\n"})
        code, out, _ = self.run_main(["pack", str(root), "--public"])
        self.assertIn("Refusal: agents/reviewer.md has no frontmatter", out)

    def test_frontmatter_value_folds_a_list(self):
        skill = SKILL.replace('models: ""', 'models: ""\nallowed-tools: Read\n  - Grep')
        root = self.base_pack(**{"SKILL.md": skill})
        code, out, _ = self.run_main(["pack", str(root), "--public"])
        self.assertIn("Refusal: SKILL.md frontmatter allowed-tools mixes a value and a list", out)
        skill = SKILL.replace('models: ""', 'models: ""\nallowed-tools:\n  - Read\n  - Grep')
        root = self.base_pack(**{"SKILL.md": skill})
        code, out, _ = self.run_main(["pack", str(root), "--public"])
        self.assertEqual(code, 0, out)

    def test_never_fire_grader_needs_min(self):
        grader = "---\ntype: tool_used\ntool: Skill\nmax: 0\n---\n"
        root = self.base_pack(**{"evals/miss/graders/not-fired.md": grader})
        code, out, _ = self.run_main(["pack", str(root), "--public"])
        self.assertIn(
            "Refusal: evals/miss/graders/not-fired.md sets max: 0 without min: 0, so it never passes",
            out,
        )
        fixed = grader.replace("max: 0", "min: 0\nmax: 0")
        root = self.base_pack(**{"evals/miss/graders/not-fired.md": fixed})
        code, out, _ = self.run_main(["pack", str(root), "--public"])
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
