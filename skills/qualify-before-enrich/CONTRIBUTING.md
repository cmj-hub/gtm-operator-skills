# Contributing

Thanks for opening this repo. A few notes on how this project works
before you contribute.

## What kinds of contributions land

- **Bug reports** — open an issue with a reproducible case. The
  scripts in `scripts/` are deterministic, so bugs there are usually
  one-line fixes.
- **New steps** that extend the existing framework, inside the one
  skill at `skills/qualify-before-enrich/SKILL.md` (the suite ships one
  skill per pack). Discuss in an issue first if it's a substantial
  addition.
- **Calibration improvements** to the scoring scripts — if you can
  show a case where the script scores wrong, that's gold.
- **Cross-runtime ports** (Cursor, Gemini CLI, Codex) — see the
  companion packs listed in the README.
- **Translation** of the framework reference docs.

## What doesn't land

- Softening the ban **no paid lookup on a failing row**.
- Adding LLM calls inside the skills. The whole point is that the
  skills are deterministic.
- Adding paid-API dependencies to scripts. Scripts must work zero-dep.
- Renaming `claude-*` → `<other-runtime>-*`. We ship per-runtime ports
  as separate plugins instead.
- Private writing skills or gated scorers. This pack is a public MIT magnet.

## Development setup

```bash
git clone https://github.com/cmj-hub/claude-qualify-before-enrich.git
cd claude-qualify-before-enrich
npx skills add cmj-hub/claude-qualify-before-enrich --all -g --full-depth
```

For Python scripts:

```bash
python3 skills/qualify-before-enrich/scripts/score.py --help
python3 -m unittest discover -s tests
```

## Pull-request checklist

- [ ] Skill names follow the spec (lowercase, hyphens, ≤64 chars,
      directory matches `name:` in frontmatter)
- [ ] Sub-skill descriptions include trigger phrases inline
- [ ] If you touch a script, add a test in `tests/` and paste a smoke-test
      run in the PR
- [ ] No new skills: new steps go in `skills/qualify-before-enrich/SKILL.md`
      and in the README "What's in the pack" table
- [ ] CHANGELOG.md updated
- [ ] No new dependencies (any of: pip packages, npm packages, API
      keys, paid services)

## Reporting calibration issues with scoring scripts

If `skills/qualify-before-enrich/scripts/score.py` scores something obviously wrong:

1. Paste the input that produced the wrong score
2. State your expected verdict + actual verdict
3. Note which field is mis-calibrated (`industry` / `employees` / `title` / `geo` / paid flags)

The scorer refuses paid lookup on a failing row. New calibration cases should keep
the deterministic path stable — no LLM calls, no network, no paid APIs.

## License

By contributing, you agree your contributions ship under the MIT
license already on this repo.

## About

Built by [Jay Mount Consulting](https://jaymountconsulting.com).
Part of the JMC public-build spine — see [/build](https://jaymountconsulting.com/build).
