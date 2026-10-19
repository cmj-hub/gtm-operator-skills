# Changelog

## 0.7.0 — 2026-10-05

The scorer now checks evidence, not wording. A pass still means the record is complete and consistent, not that the page is indexed or cited; the README and skill say so.

- **Citation record is structured.** `citation_record` is an object: `brand`, `brand_domain`, and one entry per run in `observations[]` (`engine`, `method`, `query`, `observed_at`, `run`, `clean_session`, `brands_named`, `cited_urls`, `brand_status`, `evidence`). The scorer fails a query that is not the buyer question word for word or names the brand, fewer than three distinct runs per engine and method (one for `tool export`), a missing evidence file, an unclean session, a `brand_status` that contradicts the brands named or the URLs cited, and runs spread over more than a week. App and API runs are kept apart.
- **Indexability pass is structured.** `url`, `checked_at`, `status`, `redirects`, `robots` per crawler, `noindex`, `in_sitemap`, `raw_html_has_answer`. Status must be exactly 200 (a 204 used to pass); at most one redirect; Googlebot and Bingbot required; any search or AI-search crawler blocked fails; training crawlers may be blocked.
- **Brief is structured.** `page`, `summary`, `unique_claim`, `follow_up_questions`. A claim with no number, quoted name, or capitalized name fails.
- **Refusals read negation.** "No content calendar" and "one page, not a 40-article calendar" are no longer refused. Clauses are split so "llms.txt" stays one term.
- **Parallel experiments.** One file per buyer question: `gtm/findability.json`, then `gtm/findability/<slug>.json`. A different question no longer waits for another's kill date. Batches of ten or more posts are still refused.
- **New `review` mode** and optional `review` field. On the kill date: rerun every baseline engine and method, record `indexed`, `impressions`, `qualified_visits`, `conversions`, decide `expand`, `revise`, or `stop`. The scorer refuses a decision made on citations alone, and `stop` on a page that is not indexed or that earns visits or conversions. `Next:` follows the decision.
- A blank template counts as missing on every axis.
- Examples rewritten in the new shape; `examples/findability-reviewed.json` and sample evidence under `examples/evidence/` added.

### Breaking

- Free-text `citation_record`, `indexability_pass`, and `brief` now fail with "free text is not a record". Re-run those modes, or copy the shape from `examples/findability-good.json`.

## 0.6.0 — 2026-10-04

- One skill per pack: `geo` is the only skill. The five step skills are modes it reads on demand. Always-on cost drops from ~708 to ~181 tokens.
- `/geo:geo` takes a mode as its argument (`argument-hint` lists them). No argument runs `status`: what passes, what fails, the next step.
- The draft lives at `gtm/findability.json` (the suite's shared work folder), not `draft.json`.
- Scorer: every failing line reads `- field: what is wrong → what to change`; the last line names the next step (`Next: /landing-page:page` on a pass). `--json` adds `fix` per problem, `fix` on a refusal, and `next`. `--input` is a hidden alias for `--file`. `--help` shows an example.
- README "In 60 seconds" block. Trigger evals under `evals/` and a manual `evals.yml` workflow.
- `plugin.json` drops the `skills` key; default discovery finds `skills/geo/`.

### Moved

- `SKILL.md` → `skills/geo/SKILL.md`.
- `skills/<step>/SKILL.md` → `skills/geo/modes/<step>.md` for `channel-decision`, `buyer-question`, `citation-record`, `indexability`, `brief`.
- `/geo:brief` → `/geo:geo brief`; likewise `/geo:channel-decision`, `/geo:buyer-question`, `/geo:citation-record`, `/geo:indexability`.
- `draft.json` → `gtm/findability.json`.

## 0.5.1 — 2026-10-04

- `SECURITY.md`: what runs locally, which skills reach public pages and how, how to report a vulnerability.
- README privacy and security section.

## 0.5.0 — 2026-10-04

- `plugin.json` lists `"skills": ["./"]` so the root `geo` skill loads next to the five under `skills/`.
- Root skill routes to the step skills by command (`/geo:buyer-question` and the rest).
- Root and `buyer-question` read `psp.vocabulary` from `brand-config.json` when present; never invent it.
- "Works with the suite" section: step 9, hands off to landing-page.
- Root skill calls the scorer and examples through `${CLAUDE_SKILL_DIR}`.
- README adds the suite marketplace and `npx skills add` install lines.
- Manifest: author URL, keywords. Version synced in `marketplace.json`.

## 0.4.0 — 2026-10-04

- Scorer checks each axis instead of only checking that fields are filled: question shape, citation date and method, HTTP status / robots / sitemap / blocked pages, brief length, and a kill date 14 to 180 days after the citation record.
- Placeholders (`TBD`, `Unchecked`, `None observed`) fail.
- Refusals read the plan fields only, and catch any batch of ten or more posts or a content calendar, not only "40-article".
- `--json` output for agents.
- New skills: `channel-decision` and `brief` (with the kill-date loop).
- `buyer-question`, `citation-record`, and `indexability` now carry the protocol, not just a checklist: where real questions come from, a repeatable citation method, and an AI-crawler robots table with read-only checks.
- Skills call the scorer through `${CLAUDE_PLUGIN_ROOT}` so it runs from a plugin install.
- `.claude-plugin/marketplace.json` for `/plugin marketplace add cmj-hub/claude-geo`.
- New fixtures: `findability-template.json`, `findability-weak.json`. Tests cover every axis. CI runs them.

## 0.3.0

- Plugin manifest and icon.
