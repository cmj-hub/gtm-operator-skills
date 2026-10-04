---
name: next
description: "Name the next GTM pack to run from what is already in brand-config.json and the gtm/ folder: profile, value line, list, first touch, offer, price, page, sequence, findability, posts. Use when someone asks what to do next, where to start, or what the suite has done so far. Not for doing a pack's job; it names the command and stops."
argument-hint: "[status]"
allowed-tools: Read Glob
license: MIT
models: ""
---

# What to run next

Read the project's state and name one command. Do not do the pack's work here.

## Read

- `brand-config.json` at the project root (keys below).
- `gtm/` at the project root (file names below).
- `drafts/` for founder posts.

## Walk the suite in order

Stop at the first row whose "done when" is false and print its command.

| Step | Done when | Next command |
|---|---|---|
| 0 | `operator.name` and `icp.segment` are filled | `/gtm:setup` |
| 1 | `psp.primary_pain` and `psp.signal_anchors` are filled | `/psp:psp` |
| 2 | `evp.primary` is filled | `/evp:evp` |
| 3 | `gtm/list.json` exists | `/prospect-list:who-to-contact` |
| 4 | `gtm/letter.json` exists, or `tone` and `infrastructure` are filled | `/cold-email:cold-email` |
| 5 | `gtm/offer.json` exists | `/sales-offer:cold-offer` |
| 6 | `pricing.currentTiers` is filled or `gtm/price.json` exists | `/pricing:pricing` |
| 7 | `gtm/page.json` exists | `/landing-page:page` |
| 8 | `gtm/sequence.json` exists | `/email-sequence:lifecycle-email` |
| 9 | `gtm/findability.json` exists | `/geo:geo` |
| 10 | `drafts/` holds a post from the last 7 days | `/founder-brand:founder-brand` |

Steps 3-10 are not a strict chain. When the operator names a goal ("I need a page", "pricing first"), skip to that row and say which earlier rows it reads from.

## Output

```
Done: <steps whose files or fields exist, comma-separated>
Next: <command> — <one line on why, naming the missing field or file>
```

With `$ARGUMENTS` = `status`, also print one line per step: `✓` or `·`, the step name, and the field or file checked.

If a command's pack is not installed, give its install line: `/plugin install <name>@gtm-operator-skills`.
