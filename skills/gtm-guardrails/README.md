# GTM agent guardrails for Claude Code

Your agent can read the CRM all day. It cannot change a record until you have seen the change. It cannot delete one at all. This pack sets that up, scores it, and refuses a settings file that lets a CRM write run without a prompt.

## In 60 seconds

```text
/plugin marketplace add cmj-hub/claude-gtm-guardrails
/plugin install gtm-guardrails@claude-gtm-guardrails
/gtm-guardrails:gtm-guardrails setup
```

Or score the samples without an agent:

```bash
cd skills/gtm-guardrails
python3 scripts/score_guardrails.py --file examples/guardrails-good.json
# exit 0 → pass: crm reads run, writes ask first, deletes are denied

python3 scripts/score_guardrails.py --file examples/guardrails-open-crm.json
# exit 1 → allow rule mcp__crm__* lets every crm tool run, writes included
```

Score your own settings file:

```bash
python3 scripts/score_guardrails.py --settings ~/.claude/settings.json --crm <server name from /mcp>
```

```text
GOOD  allow get_* list_* search_* · ask *create* *update* … · deny *delete* *merge*  →  exit 0
BAD   allow mcp__crm__* · defaultMode bypassPermissions                             →  exit 1
BAD   allow mcp__crm__update_record · no ask rule                                   →  exit 1
```

## Install

```bash
npx skills add cmj-hub/claude-gtm-guardrails --all -g --full-depth
```

One host:

```bash
npx skills add cmj-hub/claude-gtm-guardrails --skill '*' -g --full-depth -y -a claude-code
```

Swap `claude-code` for `cursor`, `codex`, `grok`, `github-copilot`, `windsurf`, `cline`, or `opencode`. The scorer and the sheets work anywhere. The `permissions` rules are Claude Code's.

## What you walk out with in 15 minutes

`gtm/guardrails.json`: the `permissions` block for your CRM, scored, plus one approval card for the first change your agent wants to make. Then a five-minute undo drill with whoever uses the agent.

## What's in the pack

| Path | What it is |
| --- | --- |
| `skills/gtm-guardrails/SKILL.md` | The instrument: setup checklist, approval card, score. |
| `skills/gtm-guardrails/references/guardrails-context.md` | The context file. Ten rules, each with its public source. |
| `skills/gtm-guardrails/scripts/score_guardrails.py` | Deterministic scorer. Exit 0 / 1 / 2. |
| `skills/gtm-guardrails/templates/crm-read-only.settings.json` | Read allowed, writes asked, deletes denied. Rename `crm`. |
| `skills/gtm-guardrails/templates/approval-card.md` | The card an agent shows before a write, and its six rules. |
| `skills/gtm-guardrails/templates/managed-settings.json` | The team rollout file: providers, models, effort cap. |
| `skills/gtm-guardrails/references/undo-sheet.md` | What each undo reaches, and the one that reaches nothing. |
| `skills/gtm-guardrails/references/checker-ladder.md` | Claude Code's four built-in second opinions, and which job fits each. |
| `skills/gtm-guardrails/references/routine-preflight.md` | The checklist before a scheduled agent touches your CRM. |
| `skills/gtm-guardrails/scripts/skill_link_scan.py` | Lists every outside link and install command in a skill pack. |
| `skills/gtm-guardrails/examples/` | Good, write-allowed and open samples, and the worked example. |

The undo sheet, checker ladder, managed-settings template, routine pre-flight and link scan first shipped as separate sheets on [jaymount.com/resources](https://jaymount.com/resources). They are here in one install, so the agent can read them. The link scan carries one fix: its CSV cannot hold a spreadsheet formula.

## What this pack will not do

It will not connect to your CRM. It will not run a write tool to test a rule. It will not edit your settings file until you say yes, and then it merges, never overwrites.

It does not replace your CRM's own permissions. A Claude Code rule controls what Claude Code calls. Give the CRM connection a user whose CRM role fits the job, too.

## Why a write waits

Rewind takes back Claude's file edits. `git revert` takes back a commit. Nothing takes back a CRM update, a sent email or a merged record. So the agent reads freely, shows each write on a card, and waits.

## Why not trust the tool's read-only label?

The MCP spec calls `readOnlyHint` a hint. It is not a promise, and a client should not decide tool use from it for a server it does not trust. Read the tool list yourself with `/mcp`, then write the rules by name.

## Does this work for a claude.ai connector?

Yes. Connector tools show up in Claude Code as `mcp__claude_ai_<server>__<tool>`. Use that as the server name: `--crm claude_ai_<server>`.

## Free, no signup

**[Role Unbundler](https://jaymountconsulting.com/tools/role-unbundler)**: split a job into its weekly tasks and see which ones AI can do, which it can only draft for a person to approve, and which stay with the person. In your browser. No account, no key.

## License

MIT. Built by [JMC Go-to-Market Systems](https://jaymountconsulting.com).
