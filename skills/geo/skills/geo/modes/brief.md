# Brief

Mode `brief`: one page brief an answer engine can quote, plus one kill date. Writes `brief` and `kill_date`.

One page. One brief. One kill date. The brief says what the page must say and in what order. It is not the page.

One brief per buyer question. A different buyer question is a separate experiment with its own file and brief; it does not wait for this one.

## Checklist

Copy this list and tick it in order.

- [ ] 1. Read the citation record. Note who was named and which pages were cited.
- [ ] 2. Write the first paragraph's job (below).
- [ ] 3. Name the one claim only this brand can say.
- [ ] 4. List the follow-up questions the page answers, as headings.
- [ ] 5. Set the kill date.
- [ ] 6. Write the `brief` object and `kill_date`. Run the scorer.

Review again until the scorer exits 0.

## What makes a page quotable

Answer engines lift passages, not pages. Every rule here makes one passage easy to lift.

- **The first paragraph answers the buyer question.** Directly, in 40 to 60 words, without needing the rest of the page. No preamble, no "in today's landscape".
- **One claim only this brand can say.** A number from your own data, a named method, a price, a dated result. Generic advice is already in the answer from someone else.
- **Specifics over adjectives.** Numbers, named tools, named roles, dates. "Cuts setup from 3 weeks to 4 days" gets quoted; "fast setup" does not.
- **Headings are follow-up questions.** Use the questions the engine suggests next and the ones the buyer asks after the first answer. Each section opens with its own direct answer.
- **A comparison table when buyers compare.** Rows are options, columns are what the buyer weighs. Tables are easy to lift.
- **Who says so.** A named author with a reason to know, and a visible updated date.
- **Structured data that matches the page.** `Article` or `WebPage` with `author` and `dateModified`; `Organization` with `sameAs` links on the site. Use `FAQPage` only for a real on-page Q&A. Markup that does not match visible text is ignored or penalised.

## The kill date

The kill date is when the citation record is run again with the same method.

- Set it 6 to 12 weeks after the page ships. Engines take weeks to recrawl and re-ground. The scorer accepts 14 to 180 days after the citation record.
- On the kill date, run `/geo:geo review`. It reruns the citation record with the same question, engines, and method, and adds indexation, impressions, qualified visits, and conversions.
- The decision is expand, revise, or stop, made on all of that evidence. A page that is not cited yet but is indexed and bringing qualified visits or conversions is revised, not stopped.
- Do not add more pages on the same question.

## Refuse

- A brief that covers more than one page. Split it into separate experiments, one brief each.
- A 40-article calendar, or any batch of ten or more posts. Each page needs its own buyer question and baseline.

## Output

The `brief` object and the `kill_date` field. Example:

```json
{
  "brief": {
    "page": "https://example.com/guides/which-buyer-question",
    "summary": "One page. First paragraph answers the buyer question in 40 to 60 words, then the claim, then one section per follow-up question.",
    "unique_claim": "Across 212 sales calls in 2026, the question asked right before pricing decided the deal 3 times in 4.",
    "follow_up_questions": ["Where do real buyer questions come from?", "How do I tell a question from a keyword?"]
  },
  "kill_date": "2026-12-15"
}
```

The scorer fails the brief when `page` is empty, `summary` is under 8 or over 150 words, `unique_claim` is missing or names nothing specific (no number, quoted name, or capitalized name), or a follow-up is not a question. The specificity check is a floor: it catches "fast, easy setup", not a claim a rival could also make. Check that yourself against the citation record.

## Score

Write the field into `gtm/findability.json` (create `gtm/` if missing; start from `${CLAUDE_PLUGIN_ROOT}/examples/findability-template.json`), then run:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/score.py --file gtm/findability.json
```

Exit 0 prints the six lines. Exit 1 prints `- field: what is wrong → what to change` per problem; fix that field first. Fields other skills own may read `missing` until those skills run.
