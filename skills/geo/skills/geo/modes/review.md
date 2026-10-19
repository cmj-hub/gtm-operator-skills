# Review

Mode `review`: on the kill date, decide whether to expand, revise, or stop, from citations plus search and business evidence. Writes `review`.

A review is not a second citation record. Citations are one signal. A page can be uncited and still earn visits and conversions, or be cited and still not indexed for search. Decide on all of it.

## Checklist

Copy this list and tick it in order.

- [ ] 1. Read the experiment's `citation_record`. Note the question, engines, and methods.
- [ ] 2. Rerun every engine and method with the citation-record protocol: same question, word for word, three clean runs each. Save the answers under `gtm/evidence/`.
- [ ] 3. Collect the search and business evidence (below). Record null for anything not tracked.
- [ ] 4. Decide: expand, revise, or stop. Write the reason from the evidence.
- [ ] 5. Write `review`. Run the scorer.

Check again until the scorer exits 0.

## Evidence

| Metric | Where it comes from |
|---|---|
| `indexed` | Search Console URL inspection, or Bing Webmaster Tools. true, false, or null. |
| `impressions` | Search Console performance for the page, since it shipped. |
| `qualified_visits` | Analytics: visits from search or answer engines that reached a buyer step (pricing, demo, signup page). |
| `conversions` | Leads, demos, or signups attributed to the page. |

Ask the human for numbers you cannot reach. Do not estimate them. At least one must be recorded; citations alone are not enough to decide.

## Decide

- **Expand.** Named or cited more often than the baseline, or earning qualified visits or conversions. Keep the page and start the next buyer question as a new experiment file.
- **Revise.** Indexed but not yet cited, or cited but not converting. Rewrite the first paragraph and the claim, set a new kill date, and review again. Also revise when the page is not indexed: fix indexation first.
- **Stop.** Indexed, not cited, and no qualified visits or conversions after a fair window. Pick a different question. The scorer refuses `stop` for a page that is not indexed or that has qualified visits or conversions.

## Output

The `review` object. Example:

```json
{
  "date": "2026-09-14",
  "observations": [ "...same shape as citation_record.observations, three runs per engine and method..." ],
  "metrics": {"indexed": true, "impressions": 1840, "qualified_visits": 37, "conversions": 2},
  "decision": "expand",
  "reason": "Cited in 2 of 3 runs, indexed, and two demo requests came from the page; take the next buyer question."
}
```

See `${CLAUDE_PLUGIN_ROOT}/examples/findability-reviewed.json` for a full record.

## Score

Write the field into the experiment's file, then run:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/score.py --file gtm/findability.json
```

Exit 0 prints the record and the next step for the decision. Exit 1 prints `- review: what is wrong → what to change` per problem.
