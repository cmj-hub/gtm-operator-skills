# AGENTS.md

Instructions for any coding agent (Claude Code, Codex, Cursor, Grok, and the rest) working with this repo or the skills in it.

## What is here

Seventeen GTM skill packs under `skills/<pack>/`, each with one skill, a Python scorer, evals and a worked sample. Plus `suite/` (the `gtm` plugin: `/gtm:setup`, `/gtm:next`), `company-context-pack/`, `pick-gtm-tools/`, `skill-audit/` and `build-pack/`.

## Install

```bash
npx skills add cmj-hub/gtm-operator-skills --all -g --full-depth
```

Claude Code only:

```text
/plugin marketplace add cmj-hub/gtm-operator-skills
/plugin install gtm@gtm-operator-skills
```

## Rules for using a pack

1. Run the pack's scorer on every draft and show the user each flag. Exit 0 passes, 1 refuses, 2 is bad input. The last line of the output is `Next:`.
2. Drafts go in `gtm/` at the project root, one file per pack. Founder posts go in `drafts/`. Write nowhere else.
3. `brand-config.json` and `SOUL.md` are shared by every pack. Merge into them. Never overwrite a filled value without asking.
4. Never invent a signal, a result, a quote or a customer name. A claim needs a source and a date, or it stays out.
5. Nothing in a pack sends, posts or publishes. A human does that.
6. The scorers are standard-library Python. They need no key and make no network call.

## Rules for editing this repo

- A skill description is trigger phrases a user would type, then `For X, see Y.` boundaries. Keep each pack under 400 always-on tokens.
- Do not edit a pack's framework text without running its evals: `python3 -m unittest discover -s tests` inside the pack folder.
- Before a change to a manifest: `claude plugin validate --strict .` from the repo root.
- Scope `Write` and `Edit` in `allowed-tools` to the folder the skill writes, for example `Write(./gtm/**)`.

## Public sample and data policy (Jay, 2026-10-23)

Do not commit or distribute CSV files, proprietary datasets or bulk exports in any format. Never repackage withdrawn rows as JSON, images, Markdown or XLSX. A CSV for Jay requires his explicit approval after inspecting its exact contents. Preserve operator-provided private-input tooling. Tests must use native fictional dictionaries and mocked I/O without creating CSV files or serializing CSV samples.
