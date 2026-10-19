# Offer stack skill for Claude Code

An offer stack is what the buyer gets, line by line, where every line removes a pain the buyer has already put a number on. This pack builds the stack, prints what each pain costs a year as a sum the buyer can check, and refuses a line with no pain behind it.

## In 60 seconds

```text
/plugin marketplace add cmj-hub/claude-offer-stack
/plugin install offer-stack@claude-offer-stack
/offer-stack:offer-stack kickoff
```

Or score the samples without an agent:

```bash
cd skills/offer-stack
python3 scripts/score_stack.py --file examples/stack-good.json
# exit 0 → pain total: $490,080 a year · every component removes a numbered pain

python3 scripts/score_stack.py --file examples/stack-feature-list.json
# exit 1 → component 'Premium support' removes no pain → tie it to a pain id, or cut it
```

```text
GOOD  "Call notes in the CRM within ten minutes"  removes p1 (3 h x 40 reps x $55 x 52)   →  exit 0
BAD   "Unlimited dashboards and much more"         removes nothing                          →  exit 1
BAD   $10,800 a year against $8,320 of pain                                                  →  exit 1
```

## Install

```bash
npx skills add cmj-hub/claude-offer-stack --all -g --full-depth
```

One host:

```bash
npx skills add cmj-hub/claude-offer-stack --skill '*' -g --full-depth -y -a claude-code
```

Swap `claude-code` for `cursor`, `codex`, `grok`, `github-copilot`, `windsurf`, `cline`, or `opencode`.

## What you walk out with in 15 minutes

`gtm/offer-stack.json`: one buyer, their pains with numbers and sources, the components that remove them, a guarantee they can check, and the pain total the pricing page anchors on.

## What's in the pack

| Path | What it is |
| --- | --- |
| `skills/offer-stack/SKILL.md` | The instrument: kickoff checklist, rewrite mode, score. |
| `skills/offer-stack/references/offer-stack-context.md` | The context file: pain quantification, the five questions, banned lines, honest limits. |
| `skills/offer-stack/scripts/score_stack.py` | Deterministic scorer. Exit 0 / 1 / 2. |
| `skills/offer-stack/examples/` | Good, feature-list and overpriced samples, and the worked example. |
| `tests/` | `python3 -m unittest discover -s tests` |

## What this pack will not do

It will not invent a number. A pain the buyer has not sized is written `assumption:` and confirmed on the next call, and a stack built only on assumptions is refused.

It does not set the price. That is the pricing pack. It only refuses a price larger than the pain it removes.

It will not call time saved "money saved". Forty reps who get three hours back are not paid less.

## How is this different from a sales offer?

The offer stack is the package: everything the buyer gets, and the pain each part removes. A sales offer (the `claude-sales-offer` pack) is the first email: one give-first finding, no pitch. The stack's top pain is often where that email starts.

## Where does pain quantification come from?

From the buyer. Five questions on a call: what they do today instead, how often, how many people, what one of those costs, and what happens if it is still like this next quarter. The first four multiply. The fifth is the line you quote back.

## Works with the suite

Part of the [GTM skills for Claude Code](https://github.com/cmj-hub/gtm-operator-skills). Before this: `/psp:psp` for the buying brief. After this: `/pricing:pricing anchor`, where the pain total is the status-quo anchor, and `/sales-offer:cold-offer` for the first touch.

## Free, no signup

**[ROI Calculator](https://jaymountconsulting.com/tools/roi-calculator)**: five numbers you already have, and the month the spend pays back. In your browser. No account, no key.

## License

MIT. Built by [JMC Go-to-Market Systems](https://jaymountconsulting.com).
