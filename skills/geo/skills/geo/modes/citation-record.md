# Citation record

Mode `citation-record`: who an answer engine named for one question, on one date, by one method. Writes `citation_record`.

A citation record names who was attached to one answer, on one date, by one method. A guessed list is not a record.

It is the baseline. On the kill date, `/geo:geo review` runs the same question, engines, and method again and compares the two.

## Checklist

Copy this list and tick it in order.

- [ ] 1. Lock the buyer question. Use the exact wording from the `buyer-question` mode.
- [ ] 2. Name the brand you are looking for, and its domain.
- [ ] 3. Pick the engines. At least one the buyer actually uses. Write them down.
- [ ] 4. Run the question with the protocol below. Save each answer.
- [ ] 5. Write one observation per run into `citation_record.observations`.
- [ ] 6. Run the scorer.

Check again until the scorer exits 0.

Return to step 4 if step 6 fails.

## Protocol

- Paste the question verbatim. Do not add the brand name, a location, or "best".
- Use a fresh session. Logged out or a clean profile where the engine allows it. Personal memory and history change the answer.
- Run it three times per engine. Answers vary between runs.
- Record, for each run: the brands named in the answer text, the pages linked or cited as sources, and whether this brand was named, cited, both, or neither.
- Save the raw answer text or a screenshot. Put it under `gtm/evidence/` and name it by date and engine (`gtm/evidence/2026-10-01-chatgpt-runs.txt`). One file may hold all three runs.
- Run the whole set within one week. It is one baseline.

If the agent cannot reach an engine, it asks the human to paste each run's answer. A pasted answer is a valid method. A remembered answer is not.

## Methods

Each observation's `method` is one of:

- `pasted answer`: a human ran the question and pasted the text.
- `manual run`: the agent or a human ran it in a clean session in the consumer app.
- `api run`: the question was sent through an API. API answers can differ from the consumer app; keep app and API runs apart, as the scorer does.
- `tool export`: a tracking tool's export for this exact question and date. One row is enough.

`pasted answer` and `manual run` need `clean_session: true`.

## Output

The `citation_record` object. One entry per run:

```json
{
  "brand": "Example Co",
  "brand_domain": "example.com",
  "observations": [
    {
      "engine": "ChatGPT",
      "method": "pasted answer",
      "query": "How do I know which buyer question is worth one page?",
      "observed_at": "2026-10-01",
      "run": 1,
      "clean_session": true,
      "brands_named": ["Rival Co"],
      "cited_urls": ["https://rival.example/guide"],
      "brand_status": "neither",
      "evidence": "evidence/2026-10-01-chatgpt-runs.txt"
    }
  ]
}
```

`evidence` is a URL, or a path relative to the draft file: `evidence/...` from `gtm/findability.json`, `../evidence/...` from `gtm/findability/<slug>.json`. The scorer checks the file exists; it does not read it.

The scorer fails the record when: a run's query is not the buyer question word for word, or names the brand; an engine and method has fewer than three distinct runs (one for `tool export`); a run has no saved evidence; `brand_status` disagrees with `brands_named` or with a cited URL on `brand_domain`; a date is missing, in the future, or the runs span more than a week.

## Do not

- Do not infer citations from rankings. A blue-link position is not a citation.
- Do not average across many questions into one visibility score. That is a health-score dump.
- Do not record a date you did not run it.

## Score

Write the field into `gtm/findability.json` (create `gtm/` if missing; start from `${CLAUDE_PLUGIN_ROOT}/examples/findability-template.json`), then run:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/score.py --file gtm/findability.json
```

Exit 0 prints the six lines. Exit 1 prints `- field: what is wrong → what to change` per problem; fix that field first. Fields other skills own may read `missing` until those skills run.
