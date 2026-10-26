# Worked example: one settings file, open to guarded

A sample, not a client. Northwind Analytics is made up. Their AE connected the CRM to Claude Code on Monday and clicked "don't ask again" on everything by Wednesday. This is the file they had, and the file they ended with.

## The file they had

`examples/guardrails-open-crm.json` holds it:

```json
{"permissions": {"defaultMode": "bypassPermissions", "allow": ["mcp__crm__*"]}}
```

The scorer refuses it with seven fixes:

```bash
python3 scripts/score_guardrails.py --file examples/guardrails-open-crm.json
```

```text
refused: 7 fix(es) for crm
- defaultMode is bypassPermissions, so CRM writes skip every prompt → use default, or acceptEdits for file edits only
- allow rule mcp__crm__* lets every crm tool run, writes included → allow only read tools, e.g. mcp__crm__get_*, mcp__crm__list_*, mcp__crm__search_*
- crm writes with no ask rule: create, update, upsert, archive, write, send, patch, import → add mcp__crm__*create*, mcp__crm__*update*, ... to ask, so every write shows you the change first
- crm delete, remove, merge not denied → add mcp__crm__*delete*, mcp__crm__*remove*, mcp__crm__*merge* to deny; nothing takes these back, so do them by hand in the CRM
- card 1 has no before value → ...
- card 1 has no source → ...
- card 1 has no undo line → ...
Next: fix the lines above and run this again.
```

Read the second line twice. `mcp__crm__*` reads like "the CRM tools". It means every CRM tool, the update and the delete included.

## Step 1: sort the tools

`/mcp` listed nine tools on the server. Sorted:

| Read | Write | Cannot be taken back |
|---|---|---|
| `get_record`, `list_records`, `search_records`, `list_notes` | `create_record`, `update_record`, `create_note` | `delete_record`, `merge_records` |

## Step 2: the rules

Reads go in allow, by prefix. Writes go in ask, one rule per write verb, so a tool named `send_email` or `import_contacts` cannot slip past. The last column goes in deny.

```json
{"permissions": {
  "allow": ["mcp__crm__get_*", "mcp__crm__list_*", "mcp__crm__search_*"],
  "ask":   ["mcp__crm__*create*", "mcp__crm__*update*", "mcp__crm__*upsert*", "mcp__crm__*archive*",
             "mcp__crm__*write*", "mcp__crm__*send*", "mcp__crm__*patch*", "mcp__crm__*import*"],
  "deny":  ["mcp__crm__*delete*", "mcp__crm__*remove*", "mcp__crm__*merge*"]}}
```

`defaultMode` comes out. The default prompts on first use, and the ask rules prompt every time after that.

## Step 3: the card

The old card said "update Northwind to Closed won" and nothing else. Nobody could tell what it was before, where "Closed won" came from, or how to put it back. The new one:

```text
Proposed change. Nothing has run yet.

Record:  Northwind Analytics (company)
Field:   stage
Now:     Evaluation
After:   Proposal sent
Why:     The call notes say the proposal went out on Tuesday.
Source:  notes/2026-10-14-northwind-call.md, line 12
Undo:    Set stage back to Evaluation

Reply yes to apply, no to drop it, or edit any line.
```

Notice the value changed too. The notes said the proposal went out. They did not say the deal closed. The card made the agent show its source, and the source did not support "Closed won".

## Step 4: score again

```bash
python3 scripts/score_guardrails.py --file examples/guardrails-good.json
```

```text
pass: crm reads run, writes ask first, deletes are denied
approval cards: 1 ready to show
Next: run the undo drill in references/undo-sheet.md with the new user, then the routine pre-flight if this agent runs on a schedule.
```

Then the drill: one rewind, one `git revert`, and one email drafted and not sent. That last pause is the only undo a live tool has.
