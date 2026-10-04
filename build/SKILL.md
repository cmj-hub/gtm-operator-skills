---
name: build-pack
description: Builds one GTM skill pack through a knowledge card, a design card, and a pack gate. Use when starting a pack, before the pack is written, or when a scorecard, license, secret, README, or install line is about to ship.
models: ""
---

# Build a skill pack

One pack finishes one job. The script is the gate. Cards are paths. They do not have to be committed.

Python 3.10 or newer, stdlib only. No install. Run the commands from this skill's base directory, or put that directory in front of `scripts/check_pack.py`. The `<dir>` and `<card>` paths point at the pack you are building.

```bash
python3 scripts/check_pack.py knowledge <card>
python3 scripts/check_pack.py design <card>
python3 scripts/check_pack.py pack <dir> --public
python3 scripts/check_pack.py pack <dir> --private
python3 scripts/check_pack.py all <dir> --public --knowledge <card> --design <card>
```

Success prints `knowledge ok`, `design ok`, or `pack ok`. A miss prints `Refusal:` and exits 1.

## Checklist

Copy this list and tick it in order.

- [ ] 1. Knowledge. Fill the card. Run the knowledge command. Read [knowledge.md](knowledge.md).
- [ ] 2. Design. Fill the card. Run the design command. Read [design.md](design.md).
- [ ] 3. Implementation. Write the pack. `name` is lowercase letters, numbers, and single hyphens, at most 64 characters, and never holds `claude` or `anthropic`. The description says what the pack does and when to use it, in under 1024 characters, with no angle-bracket tags. `models` stays empty until a named model has run it. For a Claude pack, probe a fast model, a mid model, and a large model: enough guidance, clear and efficient, and no extra explanation. A fast model that skips a step needs a clearer line or a script. A large model that does worse with the skill than without it needs fewer lines. If the only way to hold the line is all caps, make it a script. The body stays under 500 lines. Every SKILL.md loads: it lives in `skills/<name>/`, or plugin.json lists its folder under `skills`. An agent in `agents/` has frontmatter and takes `tools`, not `allowed-tools`. A frontmatter key holds a value or a list, never both. Call a bundled script by `${CLAUDE_PLUGIN_ROOT}` or `${CLAUDE_SKILL_DIR}`, never by a path that depends on the working directory. A reference over 100 lines has a Contents list inside the first 100 lines, and the bullets match the later headings. Link every reference from this file, one level deep. Run a script. Do not paste the script into the reply. A third-party import keeps its install line in the five lines above it.
- [ ] 4. Security. Write `SECURITY.md` at the pack root: what runs locally, what it reads and writes, the network it opens (or "None"), no telemetry, no credentials, and where to report. A public pack without it is refused. Run the pack command with `--public` or `--private`. Read [security.md](security.md).
- [ ] 5. UX. The README is the landing page. Read [ux.md](ux.md).
- [ ] 6. Scorecard. Run the scorer, fix, run the scorer, and check again until it passes. A miss the scorer does not know is a proposed rule. Leave it for a person to approve.
- [ ] 7. Release. Open a pull request from a worktree of origin/main. Leave it unmerged. Do not upload a zip by hand.

Go back to step 3 if step 4 or step 6 fails.
Go back to step 2 if step 5 fails.

Passing shapes: `examples/knowledge.json` and `examples/design.json`.
