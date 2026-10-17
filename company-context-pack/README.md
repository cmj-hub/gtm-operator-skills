# Company context pack

A short interview that writes down what your agents need to know about your company, once, as plain files any skill or agent can read first.

It writes a `context/` folder in your project:

```text
context/
  CONTEXT.md      index: read these first
  company.md      what you sell, to whom, the price model in words
  icp.md          segments, firmographics, buying triggers, disqualifiers
  offer.md        offers and outcomes
  proof.md        results you can cite, each with its source
  voice.md        tone, words you use and avoid, three sample lines
  objections.md   what buyers say before they say yes
  categories.md   the alternatives buyers weigh, as categories
```

The pack does not invent proof. A result with no source is marked `unverified`, and the checker refuses a result line that has neither. It does not name competitors: `categories.md` holds kinds of alternatives, not companies.

The model is the same one everyone else has. What makes its output yours is what you feed it. This pack is the feeding part. Background: [the Context System](https://jaymountconsulting.com/frameworks/context-system).

## In 60 seconds

```text
/plugin marketplace add cmj-hub/gtm-operator-skills
/plugin install company-context-pack@gtm-operator-skills
/company-context-pack:company-context-pack https://your-site.com
```

The skills CLI line (`npx skills add owner/repo --all -g --full-depth`) works once this pack has its own repo. Until then, use the marketplace.

You answer one question at a time. Anything your site or docs already say is skipped. To refresh one file later:

```text
/company-context-pack:company-context-pack update icp
```

Check the folder yourself:

```bash
python3 scripts/check_context.py --dir context
```

It prints `context ok: 1 unverified, 0 unknown` on a pass, or `Refusal:` with one `what is wrong → what to change` line each, and ends with a `Next:` line. Exit 0 pass, 1 refused, 2 bad input.

## See a finished one

[`examples/northwind/`](examples/northwind/CONTEXT.md) is a complete pack for Northwind Analytics, a fictional company. [The transcript](examples/northwind/transcript.md) shows the interview that produced it, including the questions it skipped.

## How the PSP and EVP packs read it

The [psp](https://github.com/cmj-hub/claude-psp) and [evp](https://github.com/cmj-hub/claude-evp) packs read `brand-config.json` and `SOUL.md`. They do not read `context/` on their own, and nothing here converts one to the other. Do this once, by hand or by asking your agent:

| This pack writes | The other packs read | What to carry over |
|---|---|---|
| `icp.md` Segments, Firmographics | `brand-config.json` `icp.segment`, `icp.size_range`, `icp.geos` | One line per field |
| `icp.md` Roles, Disqualifiers | `icp.role_targets`, `icp.exclusion_criteria` | The lists |
| `icp.md` Buying triggers | psp: the signals to hunt | Each trigger is a candidate signal. A psp signal also needs a link and a date. |
| `voice.md` Words we use, avoid | `SOUL.md` `## Phrases I use a lot`, `## Phrases I refuse` | The bullets |
| `proof.md` Results | evp `proof`, founder-brand receipts | Only lines with a real source. Skip `unverified` ones. |
| `objections.md` | psp `vocabulary` | The buyer's own words |

Going the other way is simple. Tell any pack's agent, "Read context/CONTEXT.md first." Every file is plain markdown.

## Limits

- It writes down what you tell it and what your pages say. It does not research your market.
- It does not verify a result. It only refuses to present one without a source.
- It does not refresh itself. Run `update <file>` when something changes.

## Free, no signup

[All the free tools](https://jaymountconsulting.com/prototypes), the same jobs these packs do, in a browser.

## License

MIT. Built by [Jay Mount Consulting](https://jaymountconsulting.com).
