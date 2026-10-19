# Contributing

Thanks for opening this repo. A few notes on how this project works
before you contribute.

## What kinds of contributions land

- **Bug reports** — open an issue with a reproducible case. The
  scorer in `skills/cold-offer/scripts/` is deterministic, so bugs
  there are usually one-line fixes.
- **Calibration cases** — a draft the scorer passes that sells or asks
  for a meeting, or a clean draft it fails. Paste the draft and the
  output. That's gold.
- **Cross-runtime ports** (Cursor, Gemini CLI, Codex) — discuss in an
  issue first.

## What doesn't land

- Renaming the three parts (leak, prototype, email one) or letting
  email one sell the paid product.
- Adding LLM calls to the scorer. The whole point is that it is
  deterministic.
- Adding dependencies or paid APIs. The scorer is Python 3 standard
  library only.
- Code that sends email or books meetings.

## Layout

```
.claude-plugin/plugin.json           plugin manifest
skills/cold-offer/SKILL.md           the skill
skills/cold-offer/scripts/score.py   the scorer
skills/cold-offer/examples/          good and sell drafts
tests/test_score.py                  unit tests
```

## Development

```bash
git clone https://github.com/cmj-hub/claude-sales-offer.git
cd claude-sales-offer
python3 -m unittest discover -s tests -v
python3 skills/cold-offer/scripts/score.py --file skills/cold-offer/examples/offer-good.json
```

## Pull-request checklist

- [ ] `python3 -m unittest discover -s tests` passes
- [ ] A scorer change comes with a test for the case it fixes
- [ ] If you change a check, update the table in `skills/cold-offer/SKILL.md`
- [ ] Skill name stays lowercase with hyphens and matches its directory
- [ ] Bump `version` in `.claude-plugin/plugin.json`
- [ ] No new dependencies (pip packages, npm packages, API keys, paid
      services)

## Reporting calibration issues

If `score.py` scores something obviously wrong:

1. Paste the draft JSON that produced the wrong result
2. Paste the output of `score.py --json`
3. Name the check you think is wrong (`sells`, `meeting`, `complete`,
   `finding`, `length`)

## License

By contributing, you agree your contributions ship under the MIT
license already on this repo.

## About

Built by [Jay Mount Consulting](https://jaymountconsulting.com).
Part of the JMC public-build spine — see [/build](https://jaymountconsulting.com/build).
