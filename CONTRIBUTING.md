# Contributing

Thanks for opening this repo. A few notes on how this project works
before you contribute.

## What this repo is

`gtm-operator-skills` is the **suite marketplace** for the JMC GTM skill
packs (ten MIT packs). Individual frameworks, scorers, examples, and
sub-skills live in the per-pack repos (`cmj-hub/claude-psp`,
`claude-evp`, `claude-cold-email`, and the rest). Changes to a pack's
scripts or skills belong in that pack's repo, not here.

## What kinds of contributions land

- **Bug reports** — open an issue with a reproducible case (broken
  install command, wrong marketplace plugin source, dead link, etc.).
- **Pack listing accuracy** — the README catalog and
  `.claude-plugin/marketplace.json` must match the real pack repos
  (name, description, install command). Corrections welcome.
- **Marketplace / install docs** — clearer install steps for the skills
  CLI or Claude Code marketplace commands, as long as they stay
  accurate.
- **Suite artwork** — regenerating `assets/header.png` /
  `assets/social-preview.png` / `assets/demo.gif` from `assets/spec.json`
  when the suite card copy changes.

## What doesn't land

- New paid-API or paid-service dependencies. Packs and this suite stay
  zero paid deps.
- Adding LLM calls "inside" the suite docs or marketplace metadata as
  if they were part of the instrument. Scorers live in the pack repos
  and stay deterministic Python.
- Shipping a new pack by PR here alone. A new pack needs its own repo
  first; then this suite can list it.
- Renaming JMC framework concepts that are course-anchored in the pack
  repos.

## Development setup

```bash
git clone https://github.com/cmj-hub/gtm-operator-skills.git
cd gtm-operator-skills
```

This repo has no `scripts/` scorers. To exercise a pack locally, clone
that pack (or use the install commands in the README).

Regenerate suite artwork:

```bash
node assets/card.mjs assets/spec.json assets/
# Demo GIF (needs playwright-core + ffmpeg + Chrome/Chromium):
#   cd assets && npm install playwright-core
#   CHROME_BIN=/usr/bin/google-chrome node demo.mjs spec.json demo.gif
```

## Pull-request checklist

- [ ] README pack table matches the live pack repos (links + blurbs)
- [ ] If you touch `.claude-plugin/marketplace.json`, plugin `name` /
      `source.repo` / `description` stay accurate
- [ ] Install commands in the README still work as written
- [ ] No new dependencies (pip packages, npm packages required at
      runtime, API keys, paid services)
- [ ] Soft CTAs only on the suite README (Growth Audit + Friday Signal).
      Do not add Pass CTAs

## Reporting issues against a pack scorer

Calibration bugs in `score_psp.py` / `score_evp.py` / `spam_word_lint.py`
/ etc. belong in the **pack** repo, not here. Paste the input, expected
score, actual score, and which axis looks wrong.

## License

By contributing, you agree your contributions ship under the MIT
license already on this repo.

## About

Built by [Jay Mount Consulting](https://jaymountconsulting.com).
Part of the JMC public-build spine — see [/build](https://jaymountconsulting.com/build).
