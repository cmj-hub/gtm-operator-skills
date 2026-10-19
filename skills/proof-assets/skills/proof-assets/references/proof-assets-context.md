# Proof assets: the context file

Load this when you collect, write, review or place proof: results, testimonials, metrics and logos. It holds the rules the scorer checks and the reasons behind them.

## Contents

- What a proof asset is
- The four kinds
- What makes it checkable
- Permission
- Freshness
- Getting a better quote
- Matching proof to a pain
- Where proof goes
- Banned lines

## What a proof asset is

A proof asset is a claim a buyer can check, from someone who agreed you could use it, dated.

Each one answers four questions. What changed? For whom? How do you know? May I say so? Miss one and it is a claim, not proof.

## The four kinds

| Kind | What it holds | Needs |
|---|---|---|
| `result` | A change: a metric, before, after, over a timeframe. | Both numbers, the unit, the timeframe. |
| `metric` | A count or level at a point in time. | The number, the metric, the timeframe. |
| `testimonial` | A sentence the buyer said or wrote, in their words. | Something specific in it: a number or a task. |
| `logo` | A company name or mark on your page. | Written or public permission. Always. |

Strongest first, for a buyer who doubts you: a result they could check in a public source, a named result, an unnamed result with numbers, a testimonial with a number in it, a logo. Praise with nothing in it does not make the list.

## What makes it checkable

- **Two numbers, not a multiple.** "From 2 days to 4 hours" lets the reader check the arithmetic. "6x faster" asks them to trust it.
- **A timeframe.** "In the first 60 days" tells the reader how long it took and whether it lasted.
- **A source you could show.** A CRM export, a dashboard screenshot, an email, a public page. You do not publish it. You could, if a buyer asked.
- **A who.** A role and a kind of company at least: "Head of Sales, 30-person logistics software company". "A leading brand" says nothing.

## Permission

Record what you have: `written`, `public` (the buyer published it themselves), `verbal`, or `none`.

- A name, a photo or a logo needs `written` or `public`. Verbal is not enough to put someone's name on your page.
- An unnamed result needs at least `verbal`. A buyer can recognise their own numbers.
- `none` is not usable anywhere. Ask first.
- Keep the permission with the asset: the email, the line in the contract, the date.

## Freshness

Every asset carries the ISO date it was measured or said. The scorer refuses anything older than 24 months by default (`--max-age-months` changes it). Old proof is not false, but the buyer is buying what you do now. Confirm it, re-date it, or retire it.

## Getting a better quote

Most testimonials are praise because the question was "Would you say a few words?" Ask about the work instead:

1. What were you doing before?
2. What changed, and when did you notice?
3. What number moved? (Even a rough one.)
4. What would you tell someone in your seat who is deciding now?

Quote the answer to 2 or 3, in their words. Send the quote back with the permission question in the same email.

## Matching proof to a pain

Proof works hardest next to the pain it answers. If the offer stack names a pain (`gtm/offer-stack.json`), put that pain's id on the asset as `pain`. A page section about slow replies gets the reply-time result, not the best result you have.

## Where proof goes

- **Landing page:** one result per section, beside the claim it backs. Not a wall of logos at the bottom.
- **Founder posts:** one asset as a story, from the receipt.
- **Cold email:** one line, one number, unnamed unless you have written permission.
- **Sales calls:** the source, ready to show if asked.

## Banned lines

The scorer refuses a testimonial that leans on these with no number in it: "game changer", "amazing", "incredible", "transformed", "transformative", "best decision", "highly recommend", "great to work with", "exceeded expectations", "world-class", "a pleasure", "can't recommend enough". It refuses a result that claims a multiple ("3x", "doubled", "tripled") without the two numbers behind it.
