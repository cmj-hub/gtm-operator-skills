# Routine pre-flight checklist

Routine name:
Owner (claude.ai account):
Date checked:

Source: Claude Code docs, routines and scheduled tasks, read 2026-10-06. From jaymount.com/resources/routine-preflight-checklist

## Before you click Create

**Connectors**
- [ ] List what the routine must read and what it must change. Write it down.
- [ ] Remove every connector it does not need. A new routine includes all your connectors by default, and Anthropic's form says to remove any the routine doesn't need.
- [ ] Take the CRM connector off unless the routine truly has to write there. Let it draft the change from what it can read.
- [ ] For each connector you keep, assume every tool on it, writes included, can run without a prompt.

**Repositories and environment**
- [ ] Add only the repositories the routine works in. Claude pushes to `claude/`-prefixed branches unless the prompt says otherwise; use branch protection or rulesets to control the rest.
- [ ] Pick the network access level the job needs. The Default environment is Trusted: a default allowlist only.
- [ ] Keep secrets out of environment variables where you can. They are visible to anyone who uses the environment.

**The review step**
- [ ] End the routine where a person reads the result: a pull request, a message or a document with the proposed change.
- [ ] Name the person who applies the change. Two of Anthropic's own example routines, alert triage and docs drift, both finish in a pull request a person reviews.

**Ownership**
- [ ] Note whose claude.ai account owns the routine. Routines belong to one person's account and are not shared with teammates.
- [ ] On Team and Enterprise plans, decide on purpose whether routines stay on. An Owner can turn them off for every member.

## After the first runs

- [ ] Open each of the first runs and read the transcript. A green status only means the session started and exited without an infrastructure error. It does not mean the task in your prompt succeeded.
- [ ] Check in the tool itself that what the transcript says happened did happen.
- [ ] Look for any write you did not expect. If you find one, remove that connector before the next run.

## Choosing the right way to schedule

| | Cloud routine | Desktop task | `/loop` |
|---|---|---|---|
| Runs on | Anthropic's cloud | Your machine | Your machine |
| Asks permission | No, runs autonomously | Set per task | Inherits the session |
| Most often | Every hour | Every minute | Every minute |
| Needs an open session | No | No | Yes |

If the job has to ask before it writes, a routine is the wrong tool. Use a Desktop task with permissions set, or have the routine stop at a draft.

Routines are in research preview, so the form and the limits may change. Re-read the docs page before you rely on any line here.
