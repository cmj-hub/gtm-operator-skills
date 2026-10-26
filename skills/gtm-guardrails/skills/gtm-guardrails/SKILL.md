---
name: gtm-guardrails
description: "Set up and score the guardrails on a GTM agent that can reach a CRM: reads allowed, writes asked first, deletes denied, every write shown on an approval card. Use when the user says: \"connect Claude to my CRM\", \"roll Claude Code out to my sales team\", \"schedule an agent safely\", \"are my permissions safe\", \"vet this skill\". For writing outreach, see cold-email. For scoring leads, see prospect-list."
argument-hint: "[setup | score | card | undo | checks | team | routine | vet]"
allowed-tools: Read Write Glob Grep Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/score_guardrails.py:*) Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/skill_link_scan.py:*)
license: MIT
models: ""
---

# GTM agent guardrails

The agent reads freely. Every write waits for a person. Nothing that cannot be taken back runs at all.

**Banned:** no CRM write without a prompt. An allow rule on a whole CRM server, or on a write tool, is refused.

The rules, each with its public source, are in [references/guardrails-context.md](references/guardrails-context.md). Read it before you change a settings file.

## Start here, every time

> **Scoring needs no setup.** If the user handed you a settings file or a `gtm/guardrails.json`, run the scorer first and report every line. Offer setup afterwards.

1. `$ARGUMENTS` is `score`, or empty with `gtm/guardrails.json` present: run the scorer and stop.
2. `setup`, or no draft yet: work the checklist below.
3. `card`: write an approval card from [templates/approval-card.md](templates/approval-card.md) for the change the user named.
4. `undo`: walk the first-day drill in [references/undo-sheet.md](references/undo-sheet.md).
5. `checks`: pick a rung from [references/checker-ladder.md](references/checker-ladder.md) for the job named.
6. `team`: build the managed-settings file (step 7 below).
7. `routine`: copy [references/routine-preflight.md](references/routine-preflight.md) next to the routine's prompt and tick it with the user.
8. `vet`: run the link scan (step 9 below) on the pack the user names.

The draft lives at `gtm/guardrails.json`. Create `gtm/` if it is missing.

## What you hold

```json
{
  "crm_servers": ["crm"],
  "settings": {"permissions": {
    "allow": ["mcp__crm__get_*", "mcp__crm__list_*", "mcp__crm__search_*"],
    "ask":   ["mcp__crm__*create*", "mcp__crm__*update*", "mcp__crm__*upsert*", "mcp__crm__*archive*",
             "mcp__crm__*write*", "mcp__crm__*send*", "mcp__crm__*patch*", "mcp__crm__*import*"],
    "deny":  ["mcp__crm__*delete*", "mcp__crm__*remove*", "mcp__crm__*merge*"]}},
  "approval_cards": []
}
```

`crm_servers` is the server name as `/mcp` shows it. The `permissions` block is what goes into `.claude/settings.json`, or into managed settings for a team.

## Setup checklist

Copy this list and tick it in order.

- [ ] 1. Ask the user which CRM, inbox and other live tools the agent connects to. Run `/mcp` or read `.mcp.json` and list each server's tools.
- [ ] 2. Sort every tool into read, write, or delete. Read the tool's own description; do not trust a `readOnlyHint` alone.
- [ ] 3. Copy [templates/crm-read-only.settings.json](templates/crm-read-only.settings.json). Rename `crm` to the real server name. Add any read tool whose name does not start with get, list or search by its exact name.
- [ ] 4. Save the draft as `gtm/guardrails.json` with `crm_servers` and that `settings` block.
- [ ] 5. Run `python3 ${CLAUDE_SKILL_DIR}/scripts/score_guardrails.py --file gtm/guardrails.json`.
- [ ] 6. Go back to step 3 if step 5 exits 1. Fix each line, then check again. When it exits 0, show the user the block and merge it into `.claude/settings.json` only after they say yes. Merge, never overwrite: keep every rule already there.
- [ ] 7. Team rollout only: start from [templates/managed-settings.json](templates/managed-settings.json), add the `permissions` block, and say where the file goes on each OS (the context file, Rule 7).
- [ ] 8. Scheduled agent only: tick [references/routine-preflight.md](references/routine-preflight.md) before the routine is created.
- [ ] 9. Before the team installs any other skill pack, run `python3 ${CLAUDE_SKILL_DIR}/scripts/skill_link_scan.py <pack-folder>` and read every outside link it lists with the user.

Do not edit a settings file the user has not approved. Do not run a write tool to test a rule.

## Before any write: the card

When the agent is about to change a record, it writes a card from [templates/approval-card.md](templates/approval-card.md) and waits. Read the record first, so `Now` is the value it holds at this moment. One change per card. A yes covers that card only. After the write, read the record again and report what it holds.

To score cards, add them to `approval_cards` in `gtm/guardrails.json` and run the scorer. A card with no `before`, no `source` or no `undo` is refused.

## Score

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/score_guardrails.py --file gtm/guardrails.json
python3 ${CLAUDE_SKILL_DIR}/scripts/score_guardrails.py --settings .claude/settings.json --crm crm
```

Exit 0 passes and ends with the next step. Exit 1 lists each fix as `- what is wrong → what to change`, then `Next: fix the lines above and run this again.` Exit 2 is unreadable input. `--json` prints one object. `${CLAUDE_SKILL_DIR}` is this skill's folder. From a clone of the repo, run `python3 skills/gtm-guardrails/scripts/score_guardrails.py --file gtm/guardrails.json` instead.

## Worked example

[examples/worked-example.md](examples/worked-example.md) takes one sales team's open settings file to a passing one, line by line.

| File | Exit | Why |
|---|---|---|
| `examples/guardrails-good.json` | 0 | Reads allowed, writes asked, deletes denied, one full card. |
| `examples/guardrails-write-allowed.json` | 1 | An update tool sits in allow, and nothing asks first. |
| `examples/guardrails-open-crm.json` | 1 | Whole server allowed, bypass mode on, card with no before value. |

## Free hosted tool

Which of a role's weekly tasks should an agent do alone, and which should it only draft for a person to approve? The [Role Unbundler](https://jaymountconsulting.com/tools/role-unbundler) sorts them in your browser. No account, no key.

Python 3 standard library only. No network. Nothing in this pack writes to a CRM.
