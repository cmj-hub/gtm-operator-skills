# claim-check

A statistic with no source cannot be checked. This skill reads a draft, finds every statistic written as a number, and flags the ones with no source URL or no date next to them. Then it helps you fix each flag: add the source and the date you read it, rewrite the claim without the number, or drop it.

It is read-only. It never edits your draft unless you agree to a fix, and it opens no network connection.

## Install

```text
/plugin marketplace add cmj-hub/gtm-operator-skills
/plugin install claim-check@gtm-operator-skills
```

Other agents:

```bash
npx skills add cmj-hub/gtm-operator-skills --skill claim-check -g
```

Then ask: `check this draft for unsourced stats` or run `/claim-check:claim-check path/to/draft.md`.

## What it checks

- Percentages (`47%`, `12 percent`), multipliers (`3x`, `2.5 times`), ratios (`1 in 3`), money with a magnitude (`$4M`) and large counts (`27,000 companies`).
- A statistic is sourced when its sentence, or the next sentence when that one has no figure of its own, has a URL and a date. Footnotes and reference links are followed.
- Statuses: `no-source`, `no-date`, `ok`. The script exits 1 when anything is flagged, so it also works in CI.

It does not open the link or judge whether the page says the number. A source and a date make a claim checkable, not true.

## Run it without Claude

```bash
python3 skills/claim-check/scripts/claim_check.py path/to/draft.md
python3 skills/claim-check/scripts/claim_check.py content/ --json
```

Python 3.8 or newer, standard library only. See [SECURITY.md](SECURITY.md) for exactly what it reads.

## Test it

```bash
python3 -m unittest discover -s tests
```

Built by JMC Go-to-Market Systems.

Free build guides and Skills: https://jaymountconsulting.com/resources
