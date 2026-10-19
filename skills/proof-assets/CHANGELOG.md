# Changelog

## 0.1.0 (2026-10-17)

- First public MIT release.
- Instrument: a proof asset is a claim a buyer can check, from someone who agreed you could use it, dated.
- Banned: no claim without a source and a permission.
- Scorer `skills/proof-assets/scripts/score_proof.py` (stdlib only): four kinds (result, metric, testimonial, logo); refuses a result with no before and after, a multiple with no numbers behind it, no metric or timeframe, no source, no date, future or stale dates (`--max-age-months`, default 24), names and logos without written or public permission, assets with no permission, and empty praise.
- `ask` mode drafts the email that asks a customer what changed, with the permission question in it. It never sends.
- Context file `references/proof-assets-context.md`: the four kinds, what makes proof checkable, permission, freshness, better quotes, matching proof to a pain, placement.
- Worked example: two vague homepage lines taken to three scored assets.
