---
name: page
description: "Draft one landing page as one URL, one offer, one action, then score it. Use when the user says: \"write a landing page\", \"squeeze page\", \"sign-up page\", \"page with one CTA\", \"score my landing page\". Refuses a sitemap or a list of pages. For the value line, see evp. For price tiers, see pricing. For emails after opt-in, see email-sequence."
when_to_use: "Trigger on: landing page, one-page offer, squeeze page, sign-up page, page with one CTA, score my landing page draft. Do not use for a site map, site navigation, a multi-page site, or publishing."
argument-hint: "[what the page offers | score]"
license: MIT
allowed-tools: Read Write(./gtm/**) Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/score.py:*)
models: ""
---

# The page

A page is one address. It states one offer. It asks for one action. A sitemap is a list of addresses. This pack refuses that list.

The build guide teaches a human. This pack teaches an agent.

## Start

If `$ARGUMENTS` is `score`, run the scorer on `gtm/page.json` and report each line. Otherwise `$ARGUMENTS` is what the page offers, or empty; draft the page with the checklist below. The draft lives at `gtm/page.json`; create `gtm/` if missing.

## The three parts

1. URL. One https address for this page. Not a list of paths.
2. Offer. The thing the page puts in the reader's hands, in one sentence of 200 characters or less.
3. Action. The one thing the reader does on that page, in one sentence of 160 characters or less.

Two optional fields, scored only when present:

- `headline`. One sentence, no URL, and it shares a word with the offer, so the top of the page names what it gives.
- `proof`. One non-empty line that backs the offer. Use a real result; do not invent one.

## How to write each part

- URL. Use the address the user gives. If they give none, ask for it. Do not invent a domain. `https://example.com/<slug>` is a placeholder only, and say so.
- Offer. Name the outcome the reader gets, not the company. One noun the reader holds, one result it gives them.
- Action. Start with a verb the reader does: book, reply, start, download, read. One verb phrase. "Book a call or download the guide" is two actions. Pick one.

If the user brings two offers, ask which one this page carries. The other one gets its own page.

## From brand-config.json

If `brand-config.json` sits at the project root, read it before drafting. Read only. This pack writes nothing to it.

- `evp.primary` is the offer line. Use it, or cut it to one sentence. It is also the `headline` when the draft has one. `evp.outcome` backs it up on the page. `evp.proof`, when present, is the `proof` line; when it is absent, leave `proof` out.
- `pricing.currentTiers` names the tiers. The page sells one tier; ask which. The action matches it: start a trial, book a call, buy. `pricing.referenceAnchor.quantified` is the price frame, if the page shows a price.

If a block is missing, say which pack makes it and ask the user for the line. Do not invent an offer or a price. `evp` comes from `/plugin install evp@gtm-operator-skills`; `pricing` comes from `/plugin install pricing@gtm-operator-skills`.

## Checklist

Copy this list and tick it in order.

- [ ] 1. Name the one URL.
- [ ] 2. Write the draft to `gtm/page.json` (create `gtm/` if missing): `url`, `offer`, `action`, and `headline` / `proof` when you have them.
- [ ] 3. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/score.py --file gtm/page.json`.
- [ ] 4. Read each `- problem → fix` line. Make that change. Go back to step 3.

Stop when the script exits 0. Show the user the printed lines and the `Next:` line.

## What the scorer refuses

| Output line | What it means | Fix |
| --- | --- | --- |
| `a sitemap` | `kind` is sitemap, a `urls` or `pages` list, a list in `url`, or a URL whose path says sitemap or ends in `.xml` | Keep one address. Drop the list. |
| `url is missing` / `url is not https` / `url has no host` | The address is absent or not a full https URL | Write `https://host/path`. |
| `url holds more than one address` | Two URLs in one field | Keep one. |
| `more than one offer` / `more than one action` | A list, or an `offers`, `actions`, or `ctas` key | Pick one. Move the other to its own page. |
| `offer is more than one sentence` / `action is more than one sentence` | A second sentence usually smuggles in a second offer or action | Cut to one sentence. |
| `... is longer than N characters` | The line does not fit in a headline or a button | Cut it. |
| `headline is more than one sentence` / `headline holds a URL` | The headline carries a second idea or an address | One sentence. The URL lives in `url`. |
| `headline does not name the offer` | No word longer than three letters is shared with the offer | Name the offer's noun or result in the headline. |
| `proof is empty` / `proof is more than one line` | The proof is blank or spills over a line | One line, or drop the field. |

Exit 0 means the page passes; the last line is `Next: /email-sequence:lifecycle-email`. Exit 1 means it fails: each problem prints as `- problem → fix`, then `Next: fix the lines above and run this again.` Exit 2 means the input is unusable: no file, not UTF-8, broken JSON, or not an object. A broken JSON does not echo the raw input.

## Run

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/score.py --file ${CLAUDE_PLUGIN_ROOT}/examples/page-good.json
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/score.py --file ${CLAUDE_PLUGIN_ROOT}/examples/page-sitemap.json
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/score.py --file ${CLAUDE_PLUGIN_ROOT}/examples/page-two-offers.json
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/score.py --file ${CLAUDE_PLUGIN_ROOT}/examples/page-headline.json
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/score.py --file ${CLAUDE_PLUGIN_ROOT}/examples/page-headline-refused.json
```

Add `--json` to get one JSON object with `pass`, `sitemap`, `problems`, `fixes` (one per problem), `next`, and the fields that passed.

Python 3 standard library only. No network. No publish.

## Works with the suite

This is step 7 of the GTM operator suite (`/plugin marketplace add cmj-hub/gtm-operator-skills`).

- **Reads:** `evp` and `pricing` from `brand-config.json`, if present.
- **Writes:** `gtm/page.json` only. It never touches another pack's keys.
- **Before this:** evp (`/evp:evp`) when there is no offer line; pricing (`/pricing:pricing`) when the page sells a tier.
- **After this:** email-sequence (`/email-sequence:lifecycle-email`) once someone opts in; geo (`/geo:geo`) when the page must be quoted by an answer engine.

When the page passes, end with `Next: /email-sequence:lifecycle-email` (or `/geo:geo` when the page must be quoted by an answer engine). If a companion pack is not installed, name it and its install line (`/plugin install <name>@gtm-operator-skills`); do not do its job inline.

## Example draft

```json
{
  "url": "https://example.com/desk",
  "offer": "A one-page desk that names the week's leak.",
  "action": "Read the page and reply with the one number you want next."
}
```
