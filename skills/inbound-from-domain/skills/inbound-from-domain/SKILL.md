---
name: inbound-from-domain
description: "Route an inbound lead from its email domain in seconds: corporate, free-mail, disposable, or personal-looking, then a route card. Use when the user says: \"who just filled in this form\", \"route this inbound\", \"is this a real company\", \"triage this lead\". Never writes the CRM. For finding more contacts, see waterfall-email."
argument-hint: "[email or draft | score]"
allowed-tools: Read Write(./gtm/**) Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/score.py:*)
license: MIT
models: ""
---

# Inbound from domain

Enrich inbound from the email domain. Route in seconds. The free pack stops at the route card — it does not write the CRM.

The build guide teaches a human. This pack teaches an agent.

## Start

If `$ARGUMENTS` is `score`, run the scorer on `gtm/inbound.json` and report each line. Otherwise `$ARGUMENTS` names an inbound email or is empty; work through the checklist below. The draft lives at `gtm/inbound.json`; create `gtm/` if missing. On bare invocation with no draft, load `inbound-from-domain-kickoff` first.

## What you hold

Write one JSON route card:

```json
{
  "email": "alex@northwind.io",
  "domain": "northwind.io",
  "kind": "corporate",
  "company_guess": "Northwind",
  "evidence": [
    "Domain is not on the free-mail list",
    "Company-shaped second-level name"
  ],
  "route": "build-review",
  "crm_write": false
}
```

1. `email`. The inbound address.
2. `domain`. The part after `@`, lowercased.
3. `kind`. One of: `corporate`, `free-mail`, `disposable`, `personal-looking`.
4. `company_guess`. Short name from the domain when `kind` is `corporate`.
5. `evidence`. One or more checkable facts that drove the kind (free-mail list hit, disposable list hit, company-shaped domain).
6. `route`. One of: `build-review`, `operator-pass`, `need-more`, `personal`, `disqualify`.
7. `crm_write`. Always `false` in this pack.

## Kinds

| Kind | Meaning | Typical route |
| --- | --- | --- |
| `corporate` | Company domain, not free-mail | `build-review` or `operator-pass` |
| `free-mail` | gmail, outlook, icloud, and peers | `personal` or `need-more` |
| `disposable` | Temp / throwaway inbox | `disqualify` |
| `personal-looking` | Ambiguous non-free domain | `need-more` |

## Routes

| Route | When |
| --- | --- |
| `build-review` | Corporate domain that looks like a company worth a human Build look |
| `operator-pass` | DIY / seat-shaped inbound on a real domain |
| `need-more` | Ambiguous; ask one clarifying question before routing |
| `personal` | Free-mail; treat as a person, not a logo |
| `disqualify` | Disposable, clear out, or seller-risk you already know |

## Banned patterns

Copy these. Do not soften them.

- **No CRM write-back in the free pack.** `crm_write` stays `false`. The route card is the artifact. A human (or Operator Pass tooling) owns the CRM upsert.
- **Free-mail is not Build.** Do not route `gmail.com` (and peers) to `build-review`.
- **Disposable is disqualify.** Do not keep a temp inbox alive as `need-more`.
- **Evidence is required.** A kind with no checkable fact is a guess, not enrichment.

| Passes | Refused |
| --- | --- |
| corporate + build-review + crm_write false | crm_write true |
| free-mail + personal + crm_write false | free-mail + build-review |
| disposable + disqualify + crm_write false | disposable + need-more |

## Checklist

Copy this list and tick it in order.

- [ ] 1. Take the inbound `email` and extract `domain`.
- [ ] 2. Classify `kind` from the domain (free-mail list, disposable list, or company-shaped).
- [ ] 3. Write `evidence` — one fact you could show a teammate.
- [ ] 4. Set `company_guess` when `kind` is `corporate`.
- [ ] 5. Pick `route`. Set `crm_write: false`.
- [ ] 6. Write the object to `gtm/inbound.json` (create `gtm/` if missing).
- [ ] 7. Run `python3 ${CLAUDE_SKILL_DIR}/scripts/score.py --file gtm/inbound.json`.

Go back to step 2 if step 7 exits 1. Stop when it exits 0. The last line hands the route card to a human — this pack does not write the CRM.

The scorer runs from this skill's directory (`${CLAUDE_SKILL_DIR}`). Use `--stdin` to pipe the object, and `--json` for one result object (`ok`, `verdict`, `reasons`, `fixes` parallel to `reasons`, `next`).

## Run

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/score.py --file ${CLAUDE_SKILL_DIR}/examples/inbound-good.json
python3 ${CLAUDE_SKILL_DIR}/scripts/score.py --file ${CLAUDE_SKILL_DIR}/examples/inbound-crm-write.json
```

| File | Exit | Why |
| --- | --- | --- |
| `examples/inbound-good.json` | 0 | Corporate domain → build-review, no CRM write. |
| `examples/inbound-freemail.json` | 0 | Free-mail → personal, held. |
| `examples/inbound-disposable.json` | 0 | Disposable → disqualify. |
| `examples/inbound-crm-write.json` | 1 | CRM write-back banned. |
| `examples/inbound-freemail-build.json` | 1 | Free-mail routed to Build. |

Exit 2 means the input could not be read: missing file, not UTF-8, broken JSON, or not an object. A broken JSON does not echo the raw input.

## Works with the suite

Part of the GTM operator suite (`/plugin marketplace add cmj-hub/gtm-operator-skills`).

- **Writes:** `gtm/inbound.json` only. Never touches `brand-config.json`. Never writes a CRM.
- **Before this:** a form, reply, or lead with an email. qualify-before-enrich when list ICP fields fail before any paid lookup.
- **After this:** a human reviews the route card. Operator Pass / Build Partnership owns CRM upsert and Slack HITL.
- **Not this pack:** live Firecrawl / firmographic APIs, existing-customer CRM lookup, or auto-reply send. Those are compounding layers.

If a companion pack is not installed, name it and its install line (`/plugin install <name>@gtm-operator-skills`); do not do its job inline.

Python 3 standard library only. No network. No paid API. No CRM write-back.
