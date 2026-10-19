---
name: proof-assets
description: "Collect, write and score proof a buyer can check: results with before and after, testimonials and logos, each with a source, a date and recorded permission. Use when the user says: \"write a case study\", \"ask a customer for a quote\", \"can I use this logo\", \"check my claims before they go live\". For the LinkedIn post, see founder-brand. For the page, see landing-page."
argument-hint: "[kickoff | score | ask | rewrite]"
allowed-tools: Read Write(./gtm/**) Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/score_proof.py:*)
license: MIT
models: ""
---

# Proof assets

A proof asset is a claim a buyer can check, from someone who agreed you could use it, dated.

**Banned:** no claim without a source and a permission.

The rules and the reasons are in [references/proof-assets-context.md](references/proof-assets-context.md). Read it before the first draft.

## Start here, every time

> **Scoring needs no setup.** If the user handed you a JSON draft or a path, run the scorer first and report every line. Offer kickoff afterwards.

1. `$ARGUMENTS` is `score`, or empty with `gtm/proof.json` present: run the scorer and stop.
2. `kickoff`, or no draft: work the checklist below.
3. `ask`: draft the email that asks one customer the four questions in the context file, with the permission question in it. Do not send it.
4. `rewrite`: the user pasted proof from a page or deck. Turn each line into an asset, score it, and show what each one is missing.

The draft lives at `gtm/proof.json`. Create `gtm/` if it is missing. If `gtm/offer-stack.json` exists, read its pain ids so each asset can name the pain it answers.

## What you hold

```json
{"assets": [{
  "id": "a1", "type": "result",
  "claim": "Time to first reply on inbound demo requests went from 2 days to 4 hours.",
  "metric": "time to first reply", "before": "2 days", "after": "4 hours",
  "timeframe": "first 60 days",
  "who": "Head of Sales, 30-person logistics software company (fictional sample)",
  "named": false, "permission": "verbal",
  "source": "CRM export of demo requests, Jul-Sep 2026",
  "date": "2026-09-30", "pain": "p1"}]}
```

`type` is `result`, `metric`, `testimonial` or `logo`. `permission` is `written`, `public`, `verbal` or `none`. `pain` is optional.

## Kickoff checklist

Copy this list and tick it in order.

- [ ] 1. Gather what the user already has: case notes, emails from customers, dashboards, reviews, logos on the site. Do not invent a result or a quote.
- [ ] 2. Write each one as an asset. A result gets its metric, before, after and timeframe. A testimonial is the customer's own words, quoted, not tidied.
- [ ] 3. Record the source and the permission for each, as the user states them. If the user does not know, write `none`.
- [ ] 4. Save `gtm/proof.json` and run `python3 ${CLAUDE_SKILL_DIR}/scripts/score_proof.py --file gtm/proof.json`.
- [ ] 5. Go back to step 2 if step 4 exits 1. Fix what the user can fix now and check again. For a missing permission or a missing number, use `ask` mode to draft the email that gets it.
- [ ] 6. When it exits 0, show the user the assets and say the `Next:` line.

Never upgrade a permission yourself. Never round a number in the buyer's favour.

## Score

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/score_proof.py --file gtm/proof.json
```

From a clone of the repo: `python3 skills/proof-assets/scripts/score_proof.py --file gtm/proof.json`.

Exit 0 passes and ends with the next step. Exit 1 lists each fix as `- what is wrong → what to change`, then `Next: fix the lines above and run this again.` Exit 2 is unreadable input. `--json` prints one object. `--as-of YYYY-MM-DD` freezes the date for tests and demos. `--max-age-months` sets how old proof may be (default 24).

## Worked example

[examples/worked-example.md](examples/worked-example.md) takes two vague lines from a homepage to proof a buyer can check.

| File | Exit (as of 2026-10-17) | Why |
|---|---|---|
| `examples/proof-good.json` | 0 | A result with both numbers, a specific testimonial, a dated metric. |
| `examples/proof-vague.json` | 1 | "Tripled pipeline" with no numbers or source; empty praise. |
| `examples/proof-unpermitted.json` | 1 | A logo and a named result on verbal permission; a result 34 months old. |

## Works with the suite

- **Writes:** `gtm/proof.json` only.
- **Before this:** offer-stack (`/offer-stack:offer-stack`), so each asset can name the pain it answers.
- **After this:** landing-page (`/landing-page:page`) for the proof block; founder-brand (`/founder-brand:founder-brand`) for a proof post from the receipt; cold-email (`/cold-email:cold-email`) for one line of it.

If a companion pack is not installed, name it and its install line; do not do its job inline.

## Free hosted tools

Every JMC free tool runs in your browser, no account and no key: [jaymountconsulting.com/prototypes](https://jaymountconsulting.com/prototypes).

Python 3 standard library only. No network.
