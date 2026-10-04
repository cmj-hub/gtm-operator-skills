---
name: setup
description: "Answer the shared GTM suite questions once: who you are and who you sell to. Writes the operator and icp fields of brand-config.json and the shared voice sections of SOUL.md, filling gaps only, so every pack in the suite skips those questions. Use when starting with the GTM operator suite, when a pack says to run /gtm:setup, or when brand-config.json has no operator or icp. Not for a pack's own questions (each pack's setup mode asks those)."
argument-hint: "[refresh]"
allowed-tools: Read Write Glob
license: MIT
models: ""
---

# Set up the suite once

Ten packs read one `brand-config.json` and one `SOUL.md` at the project root. This skill fills the part they all share. Each pack then asks only its own questions.

## Checklist

Copy this list and tick it in order.

- [ ] 1. Read `brand-config.json` and `SOUL.md` if they exist. List which shared fields are filled and which are empty.
- [ ] 2. Ask only for the empty fields, in one message (below). If `$ARGUMENTS` is `refresh`, show the current values and ask which to change.
- [ ] 3. Write the answers. Merge at the field level: keep every other key, never rewrite the file from scratch, and ask before changing a field that already has a value.
- [ ] 4. Create the `gtm/` folder at the project root if it is missing. Packs save their drafts there.
- [ ] 5. Show what changed, then run `/gtm:next`.

Go back to step 2 if an answer is a placeholder ("TBD", "everyone", "SMBs").

## The shared questions

```
1. Your name, title, and company?
2. A booking link, if you use one?
3. Who buys? One segment in plain words (e.g. "Series-B SaaS, 50-200 people, US").
4. Which roles feel the problem? (2-4 titles)
5. Who is out? (2-3 exclusions, e.g. "pre-revenue", "government")
6. Three phrases you use a lot, and three you never use.
7. One or two true stories you tell about a customer result.
```

## Where the answers go

| Answer | Field |
|---|---|
| 1-2 | `operator.name`, `operator.title`, `operator.company`, `operator.calendar_url` |
| 3 | `icp.segment` |
| 4 | `icp.role_targets` (list) |
| 5 | `icp.exclusion_criteria` (list) |
| 6 | SOUL.md `## Phrases I use a lot`, `## Phrases I refuse` |
| 7 | SOUL.md `## Stories I lean on` |

SOUL.md also gets `## Who I am` (one line from answer 1). Add a section only when it is missing; merge bullets into one that exists.

## Rules

- Fill gaps only. `operator` and `icp` are shared; no pack replaces a value another wrote.
- Never invent an answer. A skipped question stays empty and the pack that needs it will ask.
- Write nothing outside `brand-config.json`, `SOUL.md`, and the empty `gtm/` folder.
