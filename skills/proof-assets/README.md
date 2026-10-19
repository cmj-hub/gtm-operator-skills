# Proof assets skill for Claude Code

A proof asset is a claim a buyer can check, from someone who agreed you could use it, dated. This pack collects your results, metrics, testimonials and logos, writes each one so a doubting buyer can check it, and refuses a claim without a source and a permission.

## In 60 seconds

```text
/plugin marketplace add cmj-hub/claude-proof-assets
/plugin install proof-assets@claude-proof-assets
/proof-assets:proof-assets kickoff
```

Or score the samples without an agent:

```bash
cd skills/proof-assets
python3 scripts/score_proof.py --file examples/proof-good.json --as-of 2026-10-17
# exit 0 → pass: 3 proof asset(s) a buyer can check

python3 scripts/score_proof.py --file examples/proof-vague.json --as-of 2026-10-17
# exit 1 → a1 claims a multiple with no two numbers behind it
```

```text
GOOD  2 days → 4 hours, time to first reply, first 60 days · CRM export · verbal, unnamed   →  exit 0
BAD   "Tripled pipeline for a leading SaaS brand" · no source · no permission                →  exit 1
BAD   Customer logo · verbal permission                                                       →  exit 1
```

## Install

```bash
npx skills add cmj-hub/claude-proof-assets --all -g --full-depth
```

One host:

```bash
npx skills add cmj-hub/claude-proof-assets --skill '*' -g --full-depth -y -a claude-code
```

Swap `claude-code` for `cursor`, `codex`, `grok`, `github-copilot`, `windsurf`, `cline`, or `opencode`.

## What you walk out with in 15 minutes

`gtm/proof.json`: every result, metric, testimonial and logo you have, each with its source, date and permission, scored. Plus a drafted email for the one customer whose quote or permission you still need.

## What's in the pack

| Path | What it is |
| --- | --- |
| `skills/proof-assets/SKILL.md` | The instrument: kickoff checklist, ask mode, rewrite mode, score. |
| `skills/proof-assets/references/proof-assets-context.md` | The context file: the four kinds, permission, freshness, better quotes, placement. |
| `skills/proof-assets/scripts/score_proof.py` | Deterministic scorer. Exit 0 / 1 / 2. |
| `skills/proof-assets/examples/` | Good, vague and unpermitted samples, and the worked example. Every client, person and figure in them is fictional. |
| `tests/` | `python3 -m unittest discover -s tests` |

## What this pack will not do

It will not invent a result or a quote. It will not upgrade a permission: if you do not know what the customer agreed to, it records `none` and refuses to use the asset. It will not send the ask email. It drafts it.

It does not write the page or the post. The landing-page and founder-brand packs do that, from what this pack scored.

## Why two numbers instead of "3x"?

A multiple asks the reader to trust your arithmetic. "From 2 days to 4 hours" lets them check it, and tells them where you started. A multiple with no numbers behind it is refused.

## How is this different from founder-brand?

This pack keeps the proof: what changed, for whom, how you know, and whether you may say so. The founder-brand pack (`claude-founder-brand`) writes a LinkedIn post from one receipt. Score the receipt here first.

## Works with the suite

Part of the [GTM skills for Claude Code](https://github.com/cmj-hub/gtm-operator-skills). Before this: the offer-stack pack, so each asset can name the pain it answers. After this: `/landing-page:page`, `/founder-brand:founder-brand`, `/cold-email:cold-email`.

## Free, no signup

**[Every JMC free tool](https://jaymountconsulting.com/prototypes)**: working GTM artifacts you can run in the browser. No account, no key.

## License

MIT. Built by [JMC Go-to-Market Systems](https://jaymountconsulting.com).
