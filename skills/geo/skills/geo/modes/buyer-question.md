# Buyer question

Mode `buyer-question`: one buyer question, in the buyer's own words, for the next page to answer. Writes `buyer_question`.

One question. One brief. One kill date. A calendar of topics is a different job.

A buyer question is the sentence a buyer types into an answer engine right before they decide. It is in their words, not ours.

## Checklist

Copy this list and tick it in order.

- [ ] 1. Collect five to ten candidate questions from real sources (below). Quote them; do not paraphrase.
- [ ] 2. Cut any candidate that fails a filter (below).
- [ ] 3. Pick one. Prefer the one closest to a buying decision.
- [ ] 4. Write it into `buyer_question`, ending in `?`.
- [ ] 5. Hand off to `/geo:geo citation-record` with that exact wording.
- [ ] 6. Run the scorer. Review again until it exits 0.

Go back to step 1 if the question is a keyword list.

## Where real questions come from

- Sales call notes and transcripts: what did the buyer ask before pricing?
- Support tickets and onboarding emails.
- Community threads where buyers ask peers (Reddit, Slack groups, forums).
- The "People also ask" box and the follow-up questions an answer engine suggests.
- The buyer's own phrasing in a lost-deal note.

If `brand-config.json` sits at the project root and has `psp.vocabulary`, those are the buyer's words from the Pain Signal Profile. Phrase the question in them. Read only; do not write to the file. If the block is missing, say so (`/plugin install psp@gtm-operator-skills` makes it) and use the sources above. Do not invent vocabulary.

Keyword tools give volume, not wording. Use them to break ties, not to write the question.

## Filters

Cut the candidate if any of these is true:

- It is a keyword list or a fragment ("geo agency pricing").
- It is two questions joined together.
- It is our question ("What should we publish?").
- It names our brand. Buyers who know our name do not need the page to be found.
- An answer engine answers it in one line with no names. There is no slot to win.
- Only a different offer could honestly answer it.

## Shapes that tend to get quoted

- "How do I choose between X and Y for Z?"
- "What does X cost for a team of N?"
- "Is X worth it if I already have Y?"
- "What is the fastest way to do X without Y?"

## Output

The `buyer_question` field. Example:

> How do I know which buyer question is worth one page?

## Score

Write the field into `gtm/findability.json` (create `gtm/` if missing; start from `${CLAUDE_PLUGIN_ROOT}/examples/findability-template.json`), then run:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/score.py --file gtm/findability.json
```

Exit 0 prints the six lines. Exit 1 prints `- field: what is wrong → what to change` per problem; fix that field first. Fields other skills own may read `missing` until those skills run.
