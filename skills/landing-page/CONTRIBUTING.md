# Contributing

Thanks for opening this repo. A few notes on how this project works
before you contribute.

## What kinds of contributions land

- **Bug reports** — open an issue with a reproducible case. The
  scorer in `scripts/` is deterministic, so bugs there are usually
  one-line fixes.
- **Scoring cases** — a draft the scorer passes that should fail, or
  fails that should pass. Add it as a test in `tests/test_score.py`.
- **Wording** in `skills/page/SKILL.md` that helps an agent write a tighter offer
  or action.

## What doesn't land

- A second offer, a second action, or a sitemap mode. The pack is one
  page, one offer, one action.
- Adding LLM calls inside the skill. The scorer is deterministic.
- Adding third-party packages to scripts. Scripts must work with the
  Python standard library only.
- Network calls or publishing. The pack scores a draft. You publish it.

## Development setup

```
git clone https://github.com/cmj-hub/claude-landing-page.git
cd claude-landing-page
python3 scripts/score.py --help
python3 -m unittest discover -s tests
```

## Pull-request checklist

- [ ] `python3 -m unittest discover -s tests` passes
- [ ] If you touch the scorer, add a test and paste the output for the
      three files in `examples/` in the PR
- [ ] If you change what the scorer checks, update the table in
      `skills/page/SKILL.md` and the list in `README.md`
- [ ] `CHANGELOG.md` updated and `version` bumped in
      `.claude-plugin/plugin.json`
- [ ] No new dependencies (pip packages or npm packages)

## Reporting a wrong score

If `scripts/score.py` scores a draft wrong:

1. Paste the draft JSON that produced the wrong result
2. State the result you expected and the result you got
3. Name the field: `url`, `offer`, or `action`

## License

By contributing, you agree your contributions ship under the MIT
license already on this repo.

## About

Built by [Jay Mount Consulting](https://jaymountconsulting.com).
Part of the JMC public-build spine — see [/build](https://jaymountconsulting.com/build).
