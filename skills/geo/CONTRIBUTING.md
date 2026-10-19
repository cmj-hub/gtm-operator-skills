# Contributing

Thanks for opening this repo. A few notes on how this project works
before you contribute.

## What kinds of contributions land

- **Bug reports** — open an issue with a reproducible case. The
  scripts in `scripts/` are deterministic, so bugs there are usually
  one-line fixes.
- **New modes** that extend the existing framework (a file under
  `skills/geo/modes/`, routed from `skills/geo/SKILL.md`). Discuss in
  an issue first if it's a substantial addition.
- **Calibration improvements** to the scoring scripts — if you can
  show a case where the script scores wrong, that's gold.
- **Cross-runtime ports** (Cursor, Gemini CLI, Codex) — ship as
  separate plugins; clone this repo to work on the files locally.
- **Translation** of the framework reference docs.

## What doesn't land

- Renaming the findability artifacts (channel decision, buyer question,
  citation record, indexability pass, brief, kill date) — these are
  course-anchored.
- Turning the pack into a health-score dump, an llms.txt project, or a
  40-article calendar.
- Adding LLM calls inside the skills. The whole point is that the
  skills are deterministic.
- Adding paid-API dependencies to scripts. Scripts must work zero-dep.
- Renaming `claude-*` → `<other-runtime>-*`. We ship per-runtime ports
  as separate plugins instead.

## Development setup

```bash
git clone https://github.com/cmj-hub/claude-geo.git
cd claude-geo
```

For Python scripts:

```bash
# All scripts are zero-dep Python 3.8+ — just run them
python3 scripts/score.py --help
python3 scripts/score.py --file examples/findability-good.json
python3 -m unittest discover -s tests
```

To try the plugin locally in Claude Code:

```bash
claude plugin validate .
claude --plugin-dir .
```

## Pull-request checklist

- [ ] Skill names follow the spec (lowercase, hyphens, ≤64 chars,
      directory matches `name:` in frontmatter)
- [ ] The pack ships one skill (`skills/geo/SKILL.md`); new steps are
      modes, not new skills
- [ ] If you touch a script, smoke-test it and paste output in the PR
- [ ] If you add a new mode, list it in the README modes table, the routing table and `argument-hint` in `skills/geo/SKILL.md`
- [ ] CHANGELOG.md updated
- [ ] `python3 -m unittest discover -s tests` passes
- [ ] No new dependencies (any of: pip packages, npm packages, API
      keys, paid services)

## Reporting calibration issues with scoring scripts

If `score.py` scores something obviously wrong:

1. Paste the input that produced the wrong score
2. State your expected exit code + printed lines vs actual
3. Note which axis is mis-calibrated (channel decision, buyer
   question, citation record, indexability, brief, or kill date)

The scorer is stdlib-only and deterministic. New calibration cases add
to fixtures under `examples/` and `tests/`, not to script side paths
that call a network — keep the deterministic path stable.

## License

By contributing, you agree your contributions ship under the MIT
license already on this repo.

## About

Built by [Jay Mount Consulting](https://jaymountconsulting.com).
Part of the JMC public-build spine — see [/build](https://jaymountconsulting.com/build).
