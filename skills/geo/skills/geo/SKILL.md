---
name: geo
description: "Score generative and answer engine findability for one buyer question: citation record, indexability, one page brief, one kill date. Use when the user says: \"do we show up in ChatGPT\", \"get quoted by Perplexity\", \"AI Overviews\", \"GEO\", \"AEO\". Refuses a content calendar. For drafting the page itself, see landing-page."
argument-hint: "[channel-decision | buyer-question | citation-record | indexability | brief | review | status]"
allowed-tools: Read Write(./gtm/**) Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/score.py:*)
models: ""
---

# Generative engine optimization

Generative engine optimization is how a page gets quoted by an answer engine.

Answer engine optimization is the same check.

This pack scores findability for one question. It refuses a 40-article calendar and a health-score dump. It does not start an llms.txt project.

The build guide teaches a human. This pack teaches an agent.

## Before any mode

1. If `brand-config.json` sits at the project root, read `psp.vocabulary` (below).
2. Read `gtm/findability.json` if it exists. That is the draft for the first experiment. If it does not exist, create `gtm/` if missing and copy `${CLAUDE_PLUGIN_ROOT}/examples/findability-template.json` to `gtm/findability.json`.

## One experiment per buyer question

An experiment is one buyer question, its citation record, one page, and one kill date. Keep each experiment focused: one question, one brief, one page.

Independent experiments can run side by side. The first lives in `gtm/findability.json`; each further question gets its own file, `gtm/findability/<slug>.json`, and its own run of the modes. Two files never share a buyer question. Do not wait for one experiment's kill date before starting a different question.

What stays refused is a batch: a content calendar, or ten or more posts planned at once. That is a list of pages with no question, no baseline, and no review.

## Modes

If `$ARGUMENTS` names a mode, go straight to it. If `$ARGUMENTS` is empty, run `status` and then the first mode whose field is still missing. Read the mode file with the Read tool and follow it.

| You say / argument | Mode file | Writes |
|---|---|---|
| `channel-decision`, "is search a channel for us" | [modes/channel-decision.md](modes/channel-decision.md) | `channel_decision` |
| `buyer-question`, "which question should the page answer" | [modes/buyer-question.md](modes/buyer-question.md) | `buyer_question` |
| `citation-record`, "do we show up in ChatGPT" | [modes/citation-record.md](modes/citation-record.md) | `citation_record` |
| `indexability`, "can crawlers fetch this URL" | [modes/indexability.md](modes/indexability.md) | `indexability_pass` |
| `brief`, "how should the page be written" | [modes/brief.md](modes/brief.md) | `brief`, `kill_date` |
| `review`, "it is the kill date", "keep or kill this page" | [modes/review.md](modes/review.md) | `review` |
| `status`, or no argument | this file, Status | nothing |

Run the modes in the table's order; `review` runs on the kill date, after the page ships. Each mode owns its checklist. This skill owns the draft and the score gate.

Moved in 0.6: the five step skills are modes now. `/geo:brief` is `/geo:geo brief`; the same holds for every former step command.

## Status

Run the scorer on `gtm/findability.json` and on each file in `gtm/findability/`. Per experiment, say which fields pass, which line fails, and the next step: the mode named in the first failing line, or the `Next:` line when it exits 0. If an experiment's kill date has passed and it has no `review`, say `/geo:geo review`.

## What a pass means

The scorer checks that the record is complete and consistent: three clean runs per engine with the exact question, saved evidence, a 200 with crawlers allowed, a brief with a specific claim. It does not check that the page is indexed, cited, or worth keeping. Say so when you report a pass. The review on the kill date measures that.

## From brand-config.json

If `brand-config.json` sits at the project root, read `psp.vocabulary`. Those are the buyer's own words; `buyer-question` phrases the question in them. Read only. This pack writes nothing to the file. If the block is missing, say that the psp pack makes it (`/plugin install psp@gtm-operator-skills`) and take the words from real sources. Do not invent them.

## Run

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/score.py --file gtm/findability.json
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/score.py --file gtm/findability.json --json
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/score.py --file ${CLAUDE_PLUGIN_ROOT}/examples/findability-good.json
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/score.py --file ${CLAUDE_PLUGIN_ROOT}/examples/findability-weak.json
```

Exit 0 prints the six lines (seven with a review) and the next step. Exit 1 prints one `- field: what is wrong → what to change` line per problem, or the refusal (calendar, health score, llms.txt), then `Next: fix the lines above and run this again.` Exit 2 means the file is unusable. `--json` prints one object with `pass`, `problems` (each with a `fix`), and `next`.

## The loop

On the kill date, run `/geo:geo review`. It reruns the citation record with the same question, engines, and method, and adds indexation, impressions, qualified visits, and conversions. The decision is expand, revise, or stop, with the evidence that drove it. Citation absence alone does not stop a page that is indexed and earning visits or conversions.

Python 3 standard library only. No network.

## Works with the suite

This is step 9 of the GTM operator suite (`/plugin marketplace add cmj-hub/gtm-operator-skills`).

- **Reads:** `psp.vocabulary` (the buyer's words) from `brand-config.json`, if present.
- **Writes:** `gtm/findability.json`, plus `gtm/findability/<slug>.json` per further experiment and saved answers under `gtm/evidence/`. It never touches another pack's keys.
- **Before this:** psp (`/psp:psp`), when there is no buyer vocabulary yet.
- **After this:** landing-page (`/landing-page:page`), to draft the page the brief describes.

When the scorer exits 0, end with its `Next:` line (`/landing-page:page` before a review). If a companion pack is not installed, name it and its install line (`/plugin install <name>@gtm-operator-skills`); do not do its job inline.
