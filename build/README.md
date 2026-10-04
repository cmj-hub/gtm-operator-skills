# Build a skill pack

The gate for one pack: knowledge, design, implementation, security, UX, scorecard, release.

This directory does not ship as a customer pack. A customer pack's first screen carries its own `npx skills add owner/repo --all -g --full-depth` line.

Pack authors install it in Claude Code from the suite marketplace:

```text
/plugin marketplace add cmj-hub/gtm-operator-skills
/plugin install build-pack@gtm-operator-skills
```

Run it from this directory:

```bash
python3 scripts/check_pack.py pack . --public
python3 -m unittest discover -s tests
```

The checklist is [SKILL.md](SKILL.md).
