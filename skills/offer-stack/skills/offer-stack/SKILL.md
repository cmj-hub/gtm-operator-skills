---
name: offer-stack
description: "Build and score an offer stack where every component removes a pain the buyer put a number on, with the yearly cost shown as a sum. Use when the user says: \"what is included in my offer\", \"package my offer\", \"cost of inaction\", \"is my guarantee any good\". For the price, see pricing. For the first email, see sales-offer. For proof, see proof-assets."
argument-hint: "[kickoff | score | pain | rewrite]"
allowed-tools: Read Write(./gtm/**) Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/score_stack.py:*)
license: MIT
models: ""
---

# Offer stack

Every line in the offer removes a pain the buyer has already put a number on. A line with no pain behind it is cut.

**Banned:** no component without a numbered pain.

The rules and the reasons are in [references/offer-stack-context.md](references/offer-stack-context.md). Read it before the first draft.

## Start here, every time

> **Scoring needs no setup.** If the user handed you a JSON draft or a path, run the scorer first and report every line. Offer kickoff afterwards.

1. `$ARGUMENTS` is `score`, or empty with `gtm/offer-stack.json` present: run the scorer and stop.
2. `kickoff`, or no draft: work the checklist below.
3. `pain`: ask the five questions from the context file and write only the `pains` list.
4. `rewrite`: the user pasted an existing offer or pricing page. Turn each line into a component, then ask which pain it removes. Lines with no answer go on a cut list you show them.

The draft lives at `gtm/offer-stack.json`. Create `gtm/` if it is missing. Read `brand-config.json` at the project root if it exists, for `icp` and the shared `psp` block. Never write to it.

## What you hold

```json
{
  "buyer": "Head of RevOps at a 40-rep B2B software company",
  "pains": [{"id": "p1", "pain": "Reps re-type call notes into the CRM",
             "count": 3, "unit": "hours", "people": 40, "cost_each": 55, "period": "week",
             "source": "discovery call, 2026-10-02"}],
  "components": [{"name": "Call notes in the CRM within ten minutes of each call", "removes": ["p1"]}],
  "risk_reversal": "If notes are not in the CRM within ten minutes for 90% of calls by day 30, month two is free.",
  "price": {"amount": 4000, "period": "month"}
}
```

`period` is `day`, `week`, `month`, `quarter` or `year`. `price` is optional. `source` is who said the number and when, or `assumption:` and why.

## Kickoff checklist

Copy this list and tick it in order.

- [ ] 1. Name one buyer: a role at a kind of company. One stack per buyer.
- [ ] 2. Get the pains. Ask the five questions in the context file, or read the user's call notes. Write each pain in the buyer's words, with a count, people, cost each, period and source.
- [ ] 3. Do not invent a number. If the user does not have one, write `assumption:` with the reasoning and mark it to confirm on the next call.
- [ ] 4. List the components. One job each, named as the outcome the buyer sees. Give each the pain ids it removes.
- [ ] 5. Write the risk reversal: an outcome you can check, a date, and what the buyer pays if it misses.
- [ ] 6. Save `gtm/offer-stack.json` and run `python3 ${CLAUDE_SKILL_DIR}/scripts/score_stack.py --file gtm/offer-stack.json`.
- [ ] 7. Go back to step 2 if step 6 exits 1. Fix each line and check again. When it exits 0, show the user the pain lines and the stack, and say the `Next:` line.

## Score

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/score_stack.py --file gtm/offer-stack.json
```

From a clone of the repo: `python3 skills/offer-stack/scripts/score_stack.py --file gtm/offer-stack.json`.

The scorer prints each pain's yearly cost as a sum the buyer can check, the total, and the price against it. Exit 0 passes and ends with the next step. Exit 1 lists each fix as `- what is wrong → what to change`, then `Next: fix the lines above and run this again.` Exit 2 is unreadable input. `--json` prints one object.

## Worked example

[examples/worked-example.md](examples/worked-example.md) takes a feature list to a scored stack, call note by call note.

| File | Exit | Why |
|---|---|---|
| `examples/stack-good.json` | 0 | Three pains with numbers and sources, three components, a checkable guarantee. |
| `examples/stack-feature-list.json` | 1 | A pain with no number, filler lines, a satisfaction guarantee. |
| `examples/stack-overpriced.json` | 1 | The price is more than the pain it removes. |

## Works with the suite

- **Writes:** `gtm/offer-stack.json` only.
- **Before this:** psp (`/psp:psp`), when there is no buying brief yet.
- **After this:** pricing (`/pricing:pricing anchor`), where the pain total becomes the status-quo anchor; sales-offer (`/sales-offer:cold-offer`), where the top pain opens a give-first first touch.

If a companion pack is not installed, name it and its install line (`/plugin install <name>@gtm-operator-skills`); do not do its job inline.

## Free hosted tool

Five numbers you already have, and the month the spend pays back: the [ROI Calculator](https://jaymountconsulting.com/tools/roi-calculator), in your browser. No account, no key.

Python 3 standard library only. No network.
