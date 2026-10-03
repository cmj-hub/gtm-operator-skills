# Build a skill pack

The gate for one pack: knowledge, design, implementation, security, UX, scorecard, release.

This directory does not install as a customer pack. A customer pack's first screen carries its own `npx skills add owner/repo --all -g --full-depth` line.

Run it from this directory:

```bash
python3 scripts/check_pack.py pack . --public
```

The checklist is [SKILL.md](SKILL.md).
