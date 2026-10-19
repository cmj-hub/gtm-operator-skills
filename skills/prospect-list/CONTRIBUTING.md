# Contributing

Thanks for opening this repo. A few notes on how this project works
before you contribute.

## What kinds of contributions land

- **Bug reports** — open an issue with a reproducible case. The
  scripts in `scripts/` are deterministic, so bugs there are usually
  one-line fixes.
- **New steps** that extend the existing framework, inside the one
  skill at `skills/who-to-contact/SKILL.md` (the suite ships one skill
  per pack). Discuss in an issue first if it's a substantial addition.
- **Calibration improvements** to the scoring scripts — if you can
  show a case where the script scores wrong, that's gold.
- **Cross-runtime ports** (Cursor, Gemini CLI, Codex) — see the
  companion packs listed in the README.
- **Translation** of the framework reference docs.

## What doesn't land

- Renaming the JMC framework concepts (Signal → Pain → EVP → Ask, the
  5 Schwartz tiers, the 4 content pillars) — these are course-anchored.
- Adding LLM calls inside the skills. The whole point is that the
  skills are deterministic.
- Adding paid-API dependencies to scripts. Scripts must work zero-dep.
- Renaming `claude-*` → `<other-runtime>-*`. We ship per-runtime ports
  as separate plugins instead.

## Development setup

```bash
git clone https://github.com/cmj-hub/claude-prospect-list.git
cd claude-prospect-list
# Test the install locally
npx skills add cmj-hub/claude-prospect-list --all -g --full-depth
```

For Python scripts:

```bash
# All scripts are zero-dep Python 3.8+ — just run them
python3 skills/who-to-contact/scripts/score.py --help
python3 -m unittest discover -s tests
claude plugin validate --strict .   # if you have Claude Code
```

## Pull-request checklist

- [ ] Skill names follow the spec (lowercase, hyphens, ≤64 chars,
      directory matches `name:` in frontmatter)
- [ ] Sub-skill descriptions include trigger phrases inline
- [ ] If you touch a script, add a test in `tests/` and paste a smoke-test
      run in the PR
- [ ] No new skills: new steps go in `skills/who-to-contact/SKILL.md`
      (or a mode file it links) and in the README "What's in the pack" table
- [ ] CHANGELOG.md updated
- [ ] No new dependencies (any of: pip packages, npm packages, API
      keys, paid services)

## Reporting calibration issues with scoring scripts

If `skills/who-to-contact/scripts/score.py` scores something obviously wrong:

1. Paste the input that produced the wrong score
2. State your expected score + actual score
3. Note which field is mis-calibrated (`title` / `signal` / `score`)

The scorer refuses a title-only list. New calibration cases should keep
the deterministic path stable — no LLM calls, no network, no paid APIs.

## License

By contributing, you agree your contributions ship under the MIT
license already on this repo.

## About

Built by [Jay Mount Consulting](https://jaymountconsulting.com).
Part of the JMC public-build spine — see [/build](https://jaymountconsulting.com/build).
