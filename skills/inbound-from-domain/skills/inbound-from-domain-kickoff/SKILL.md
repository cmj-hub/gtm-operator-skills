---
name: inbound-from-domain-kickoff
description: "Router for the inbound-from-domain pack. Use when the user says: \"where do I start\", \"route this inbound email\", bare /inbound-from-domain. Names the next step: score the sample, draft a route card, or hand off to a human. For the route card itself, see inbound-from-domain."
argument-hint: "[status | sample]"
allowed-tools: Read Bash(python3 */skills/inbound-from-domain/scripts/score.py:*)
license: MIT
models: ""
---

# Inbound from domain — kickoff

Fifteen minutes. One inbound email. Enrich the domain. Route. Do not write the CRM.

## Start

1. If `$ARGUMENTS` is `sample`, run the good and CRM-write examples and show both exits.
2. If `$ARGUMENTS` is `status`, report whether `gtm/inbound.json` exists and what the scorer says.
3. Otherwise detect state and route.

## State

| State | Next |
| --- | --- |
| No `gtm/inbound.json` | Score the samples first (below), then draft one route card with `crm_write: false`. |
| Draft exists, never scored | Run `inbound-from-domain` with `score`. |
| Score exits 1 | Fix the `- … → …` lines; re-score. |
| Score exits 0 | Hand the route card to a human. Do not write the CRM from this pack. |

## Sample loop (the worked example)

```bash
python3 skills/inbound-from-domain/scripts/score.py --file skills/inbound-from-domain/examples/inbound-good.json
python3 skills/inbound-from-domain/scripts/score.py --file skills/inbound-from-domain/examples/inbound-crm-write.json
```

Good exits 0: `alex@northwind.io` → corporate → `high-touch`, `crm_write: false`. CRM-write exits 1: write-back is banned. Then write yours to `gtm/inbound.json`.

## Welcome

```
Enrich inbound from the email domain. Route in seconds.

Kinds: corporate | free-mail | disposable | personal-looking
Routes: high-touch | self-serve | need-more | personal | disqualify
Banned: no CRM write-back in the free pack.

1. Score the sample (good vs CRM-write)     ← start here
2. Draft one route card (crm_write false)
3. Score gtm/inbound.json
4. Hand the card to a human

Ready to score the sample?
```

## Rules to repeat

- `crm_write` stays `false`. The route card is the artifact.
- Free-mail never routes to `high-touch`.
- Disposable always routes to `disqualify`.
- This pack does not call a paid enrichment API. You classify from the domain; the scorer gates the card.
