# Worked examples

Three real requests, run against the live TGD server on 2026-10-17 (read-only). The server listed `search_tools`, `get_tool` and `list_categories`, so the compare and stack examples use the fallback path. Outputs are trimmed to the fields the skill uses. Listings change; run the calls again before you rely on a result.

## Contents

- Example 1: a shortlist
- Example 2: compare two tools
- Example 3: a starter stack around Clay

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

Calls 2 and 3. `get_tool` on `attio` and `twenty`:

```json
{"slug": "attio", "verified_facts": {"as_of": "2026-10-17", "facts": ["Ships an official MCP server", "Documents a public API", "Free plan, no card", "Shows a price on the pricing page", "Works natively inside Clay"]}}
{"slug": "twenty", "verified_facts": {"as_of": "2026-10-17", "facts": ["Ships an official MCP server", "Documents a public API", "Shows a price on the pricing page"]}}
```

Reply:

```text
## Shortlist: a CRM our agent can read and write

1. **Attio**: official MCP server, public API, free plan with no card, works natively inside Clay (as of 2026-10-17). Source: The GTM Directory, https://thegtmdirectory.com/tools/attio
2. **Twenty**: official MCP server, public API (as of 2026-10-17). A free plan and native Clay support are not established on TGD. Source: The GTM Directory, https://thegtmdirectory.com/tools/twenty

Both clear the must-have: an official MCP server.
Open on The GTM Directory: https://thegtmdirectory.com/compare/attio-vs-twenty
```

"Not established" is the right words for Twenty's missing facts. TGD has not verified them, which is not the same as the vendor lacking them.

## Example 3: a starter stack around Clay

> "We run Clay. Give me a sending tool and a CRM that plug into it."

Slots: data hub (Clay, named by the user), send, record. Constraint: works natively inside Clay.

Call 1. `search_tools` to get the slug the user named:

```json
{"query": "Clay", "limit": 3}
```

Result: `clay` first, subcategory `data-enrichment`. Then `get_tool` on `clay`:

```json
{"as_of": "2026-10-17", "facts": ["Ships an official MCP server", "Documents a public API", "Free plan, no card", "Shows a price on the pricing page"]}
```

Send slot: Example 1's search and facts. Instantly is the top result with the Clay fact.

Record slot. `search_tools`:

```json
{"query": "CRM", "has_mcp": true, "limit": 5}
```

Result: `espocrm`, `monday-sales-crm`, `zoho-crm`, `attio`, `close`. `get_tool` on all five; only two carry "Works natively inside Clay":

```json
{"slug": "attio", "facts": ["Ships an official MCP server", "Documents a public API", "Free plan, no card", "Shows a price on the pricing page", "Works natively inside Clay"]}
{"slug": "close", "facts": ["Ships an official MCP server", "Documents a public API", "Shows a price on the pricing page", "Works natively inside Clay"]}
```

Reply:

```text
## Stack: Clay plus sending and a CRM

1. **Clay** (data hub): official MCP server, public API, free plan with no card (as of 2026-10-17). Source: The GTM Directory, https://thegtmdirectory.com/tools/clay
2. **Instantly** (send): official MCP server, public API, works natively inside Clay (as of 2026-10-17). Source: The GTM Directory, https://thegtmdirectory.com/tools/instantly
3. **Attio** (record): official MCP server, public API, free plan with no card, works natively inside Clay (as of 2026-10-17). Source: The GTM Directory, https://thegtmdirectory.com/tools/attio
4. **Close** (record, second choice): official MCP server, public API, works natively inside Clay (as of 2026-10-17). Source: The GTM Directory, https://thegtmdirectory.com/tools/close

Open on The GTM Directory: https://thegtmdirectory.com/build
```

When the server lists `recommend_stack`, one call replaces the per-slot searches, for example `{"job": "<slug from /jobs>", "needs_mcp": true, "clay_native": true}`. Each pick comes back with a reason built from cited facts and a page URL. Use the same format.
