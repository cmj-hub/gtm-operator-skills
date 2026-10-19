# Contributing

Thanks for opening this repo. A few notes on how this project works
before you contribute.

## What kinds of contributions land

- **Bug reports**: open an issue with a reproducible case. The
  scorer is deterministic, so bugs there are usually one-line fixes.
- **Calibration improvements**: if you can show a case where the
  script scores wrong, that is gold.
- **Cross-runtime ports** (Cursor, Codex, Grok) via the skills CLI.
- **Docs** that keep the instrument public and complete.

## What doesn't land

- Softening the banned list (catch-all as valid, found as sendable).
- Adding LLM calls or paid verifier APIs inside the pack.
- Adding pip/npm dependencies to scripts. Scripts must work zero-dep.
- Gating the scorer or teaser-izing `SKILL.md`.

## Development setup

```bash
git clone https://github.com/cmj-hub/claude-found-vs-deliverable.git
cd claude-found-vs-deliverable
python3 skills/found-vs-deliverable/scripts/score.py --help
python3 -m unittest discover -s tests
```

## Pull-request checklist

- [ ] Skill directory matches `name:` in frontmatter
- [ ] If you touch the scorer, add a test and paste a smoke run in the PR
- [ ] CHANGELOG.md updated
- [ ] No new dependencies, paid APIs, or network calls
