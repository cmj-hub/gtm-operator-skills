# Worked examples

Three real requests, run against the live TGD server on 2026-10-17 (read-only). Example 1 uses `search_tools` and `get_tool`; example 2 is a real `compare_tools` call; example 3 is a real `recommend_stack` call. Outputs are trimmed to the fields the skill uses. Listings change; run the calls again before you rely on a result.

## Contents

- Example 1: a shortlist
- Example 2: compare two tools
- Example 3: a starter stack for a job

## Example 1: a shortlist

> "I need a cold email tool my agent can drive over MCP, and it has to work inside Clay."

Must-haves: official MCP server, works inside Clay.

Call 1. `search_tools`:

```json
{"query": "cold email sending", "category": "cold-email", "has_mcp": true, "limit": 8}
```

Result (8 of 8, slug, `pricing_tier`):

```text
instantly   freemium    https://thegtmdirectory.com/tools/instantly
woodpecker  freemium    https://thegtmdirectory.com/tools/woodpecker
saleshandy  freemium    https://thegtmdirectory.com/tools/saleshandy
smartlead   paid        https://thegtmdirectory.com/tools/smartlead
plusvibe    freemium    https://thegtmdirectory.com/tools/plusvibe
quickmail   freemium    https://thegtmdirectory.com/tools/quickmail
superhuman  freemium    https://thegtmdirectory.com/tools/superhuman
autobound   freemium    https://thegtmdirectory.com/tools/autobound
```

Calls 2 to 4. `get_tool` on `instantly`, `smartlead` and `woodpecker`. Each returned the same `verified_facts`:

```json
{"as_of": "2026-10-17", "facts": ["Ships an official MCP server", "Documents a public API", "Shows a price on the pricing page", "Works natively inside Clay"]}
```

Reply:

```text
## Shortlist: cold email my agent can drive, inside Clay

1. **Instantly**: official MCP server, public API, works natively inside Clay (as of 2026-10-17). Freemium. Source: The GTM Directory, https://thegtmdirectory.com/tools/instantly
2. **Smartlead**: official MCP server, public API, works natively inside Clay (as of 2026-10-17). Paid. Source: The GTM Directory, https://thegtmdirectory.com/tools/smartlead
3. **Woodpecker**: official MCP server, public API, works natively inside Clay (as of 2026-10-17). Freemium. Source: The GTM Directory, https://thegtmdirectory.com/tools/woodpecker

Open on The GTM Directory: https://thegtmdirectory.com/best/cold-email
```

The facts tie, so the shortlist stops at the facts. The editorial on each page (who it fits, the trade-offs) is where the user decides; link it, do not restate it.

## Example 2: compare two tools

> "Attio or Twenty for our CRM? We want our agent to read and write it."

Call 1. `search_tools` to get both slugs:

```json
{"query": "Attio Twenty", "limit": 3}
```

Result: `twenty` and `attio`, both `sales-crms`, both `freemium`.

Call 2. `compare_tools`:

```json
{"a": "attio", "b": "twenty"}
```

Result, trimmed. Each `vendor_verified` row has a value and `checked_on` per side, or `null`:

```text
Category                           attio: CRM & Deal Management   twenty: CRM & Deal Management
Pricing tier                       attio: freemium                twenty: freemium
Ships an official MCP server       attio: true  (2026-10-17)      twenty: true  (2026-10-17)
Documents a public API             attio: true  (2026-10-17)      twenty: true  (2026-10-17)
Free plan, no card                 attio: true  (2026-10-17)      twenty: null
Shows a price on the pricing page  attio: true  (2026-10-17)      twenty: true  (2026-10-17)
Works natively inside Clay         attio: true  (2026-10-17)      twenty: null
```

Pages: `https://thegtmdirectory.com/tools/attio` and `https://thegtmdirectory.com/tools/twenty`. The result carries no practitioner mentions.

Reply:

```text
## Shortlist: a CRM our agent can read and write

1. **Attio**: official MCP server, public API, free plan with no card, works natively inside Clay (as of 2026-10-17). Source: The GTM Directory, https://thegtmdirectory.com/tools/attio
2. **Twenty**: official MCP server, public API (as of 2026-10-17). A free plan and native Clay support are not established on TGD. Source: The GTM Directory, https://thegtmdirectory.com/tools/twenty

Both clear the must-have: an official MCP server.
Open on The GTM Directory: https://thegtmdirectory.com/compare/attio-vs-twenty
```

`null` is "not established on TGD". It is not the same as the vendor lacking the feature.

## Example 3: a starter stack for a job

> "I need to find work emails, and my agent has to drive the tool over MCP."

`job` is one of TGD's published slugs (here `find-a-work-email`); an unknown slug returns the valid list. The user asked for MCP, so only `needs_mcp` is set.

Call 1. `recommend_stack`:

```json
{"job": "find-a-work-email", "needs_mcp": true}
```

Result, trimmed. `resolved.page_url` is `https://thegtmdirectory.com/best/contact-finders`. One slot, `find-a-work-email`, with 5 tools (the cap per slot). Each came back with a fact-only `reason`, a `page_url` and dated facts:

```text
hunterio    https://thegtmdirectory.com/tools/hunterio    MCP, API, free plan no card, price shown, Clay native  (checked 2026-10-17)
prospeo     https://thegtmdirectory.com/tools/prospeo     MCP, API, free plan no card, price shown, Clay native  (checked 2026-10-17)
wiza        https://thegtmdirectory.com/tools/wiza        MCP, API, free plan no card, price shown, Clay native  (checked 2026-10-17)
contactout  https://thegtmdirectory.com/tools/contactout  MCP, API, free plan no card, price shown, Clay native  (checked 2026-10-17)
icypeas     https://thegtmdirectory.com/tools/icypeas     MCP, API, price shown, Clay native  (checked 2026-10-17)
```

Reply:

```text
## Stack: find work emails with an MCP server

1. **Hunter.io**: official MCP server, public API, free plan with no card, works natively inside Clay (as of 2026-10-17). Source: The GTM Directory, https://thegtmdirectory.com/tools/hunterio
2. **Prospeo**: official MCP server, public API, free plan with no card, works natively inside Clay (as of 2026-10-17). Source: The GTM Directory, https://thegtmdirectory.com/tools/prospeo
3. **Wiza**: official MCP server, public API, free plan with no card, works natively inside Clay (as of 2026-10-17). Source: The GTM Directory, https://thegtmdirectory.com/tools/wiza
4. **ContactOut**: official MCP server, public API, free plan with no card, works natively inside Clay (as of 2026-10-17). Source: The GTM Directory, https://thegtmdirectory.com/tools/contactout
5. **Icypeas**: official MCP server, public API, works natively inside Clay (as of 2026-10-17). A free plan with no card is not established on TGD. Source: The GTM Directory, https://thegtmdirectory.com/tools/icypeas

Open on The GTM Directory: https://thegtmdirectory.com/best/contact-finders
```

The ranking is the server's; the skill does not reorder it. A slot holds at most 5, so a longer list needs a second search. Do not claim the 5 are every tool that qualifies.
