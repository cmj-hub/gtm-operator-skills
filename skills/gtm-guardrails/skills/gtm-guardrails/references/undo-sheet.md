# Claude Code undo sheet

Source: Claude Code docs (checkpointing, memory) and git docs, read 2026-10-06. From jaymount.com/resources/claude-code-undo-sheet

## What each undo reaches

| Undo | How | Takes back | Does not take back |
|---|---|---|---|
| Rewind | Press `Esc` twice with the prompt empty, or run `/rewind` | Claude's file edits in this session, back to any prompt you sent. You can restore code, conversation or both. | Files changed by Bash commands (`rm`, `mv`, `cp`). Edits by most subagents. Changes made outside Claude Code. |
| `git revert` | `git revert <commit>` | Anything committed to the repository. It adds a new commit that reverses the old one, so history stays intact. | Anything never committed. Anything outside the repository. |
| Nothing | | | A sent email. A CRM update. A post. A form submitted. Anything Claude did in a live tool. |

The live tools are where a mistake leaves the building. So the rule for a new user is simple: look before anything sends.

## Rewind, in a little more detail

- Every prompt you send that starts a turn creates a checkpoint. Claude Code keeps the 100 most recent in a session.
- The rewind menu offers: restore code and conversation, restore conversation only, restore code only, or summarize.
- Checkpoints survive `/resume`, but Claude Code deletes old snapshots in its clean-up sweep, by default about 30 days after the session last saved one.
- Anthropic's own line: checkpoints are for quick, session-level recovery. For real history, keep using git.

## The session hand-off prompt

Paste this at the end of every session:

```text
Before we stop, write a hand-off note:
- what we changed, file by file
- what we checked, and how
- what is still open or broken
- the first job for next time
Next session, read this note before anything else.
```

Save the note where the next session will find it, such as a `HANDOFF.md` in the project, and point to it from your `CLAUDE.md`. Claude reads `CLAUDE.md` at the start of every session.

## A first-day drill

1. Ask Claude to add one line to a text file. Press `Esc` twice and restore the code. Check the line is gone.
2. Ask Claude to add the line again, then commit it. Run `git revert HEAD`. Check the line is gone and the history shows both commits.
3. Ask Claude to draft an email but not send it. Read the draft. That pause is the only undo a live tool has.
