# Channel decision

Mode `channel-decision`: whether answer-engine search is a channel for this offer, before any page is planned. Writes `channel_decision`.

A channel decision says whether answer-engine search is worth one page for this offer, and which question comes first. It is one or two sentences. It is not a strategy deck.

## Checklist

Copy this list and tick it in order.

- [ ] 1. Name the offer and the buyer in one line each.
- [ ] 2. Answer the three tests below. Write yes or no and one reason each.
- [ ] 3. Write the decision: "Search is a channel for this offer" or "Search is not a channel for this offer", then why, then what comes first.
- [ ] 4. If yes, hand off to `/geo:geo buyer-question`. If no, stop. Do not plan pages.

## The three tests

1. **Do buyers ask before they buy?** Look for real questions in sales calls, support tickets, community threads, or the "People also ask" box. No questions, no channel.
2. **Does an answer engine already answer it with names?** Paste one candidate question into one engine. If the answer names vendors, roundups, or tools, there is a slot to win. If it answers generically with no names, the slot is thin.
3. **Is there one claim only this brand can say?** Proprietary numbers, a named method, a price, a result with a date. Answer engines quote specifics. A brand with nothing specific to say will not be quoted.

Two or three yes means search is a channel. One or none means it is not, this quarter.

## Refuse

- A health-score dump, an llms.txt project, or a 40-article calendar. Name the refusal and return to step 1.
- "Rank for everything." Pick the first question.

## Output

The `channel_decision` field of the draft. Example:

> Search is a channel for this offer. Buyers ask which setup to pick before they book a call, and the pasted answer names two rivals. Own one orientation question before any new URL.

## Score

Write the field into `gtm/findability.json` (create `gtm/` if missing; start from `${CLAUDE_PLUGIN_ROOT}/examples/findability-template.json`), then run:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/score.py --file gtm/findability.json
```

Exit 0 prints the six lines. Exit 1 prints `- field: what is wrong → what to change` per problem; fix that field first. Fields other skills own may read `missing` until those skills run.
