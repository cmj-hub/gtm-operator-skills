# Claude Code checker ladder

Four built-in second opinions, lightest at the bottom. Source: Anthropic's Claude Code docs and changelog, read 2026-10-06. From jaymount.com/resources/claude-code-checker-ladder

## The ladder

| Rung | Check | What it does to a mistake | Turn it on | Example GTM job |
|---|---|---|---|---|
| 4 | `/goal` | Decides done. After each turn a fresh model checks whether your end state holds, and Claude keeps working until it does. | `/goal <end state>` | Enrich a list until no row is missing an email, or stop after 20 turns. |
| 3 | `/code-review` | Reports findings on a diff or a file path, in a background agent with its own context window. | `/code-review --max-findings all` | The SQL behind a Snowflake report, before anyone reads the numbers. |
| 2 | Advisor | Advises. Claude consults a second, usually stronger model at key moments. | `/advisor opus` | An ICP scoring rubric built over many steps, where the plan is the hard part. |
| 1 | You should know | Flags. A side agent watches the session and flags things you or Claude might miss. | `/plugin enable cc-plugin-you-should-know@builtin` | A long list build you won't watch line by line. |

The GTM jobs are my examples of where each documented behaviour fits. The behaviours are from Anthropic's docs and changelog.

## The limits, from the docs

**/goal (added in 2.1.139)**
- The judge doesn't run commands or read files. It reads what Claude shows. So make Claude print the count.
- Write one measurable end state: a test result, an exit code, a file count, an empty queue.
- Bound it with a turn or time clause, such as `or stop after 20 turns`.

**/code-review**
- It reviews your branch's commits ahead of upstream plus uncommitted changes. To review something else, pass a target: a file path, a PR number or a branch name.
- At `low` and `medium` effort it reports only the findings it is most confident in.
- `--max-findings <n>|all` needs Claude Code 2.1.288 or later. The choice is reused until you pass `--max-findings default`.

**Advisor**
- You choose the advisor model. Claude decides when to call it.
- It is experimental and needs the Anthropic API.
- If a variable that turns flag fetching off is set, such as `DISABLE_TELEMETRY`, the advisor stays off.

**You should know (added in 2.1.287)**
- First-party sessions with telemetry on only.

## Example end states for /goal

Write them so Claude's own output can prove them:

```text
/goal every row in leads.csv has a non-empty email column; print the count of empty emails, which must be 0; or stop after 20 turns
/goal the weekly pipeline query runs without error and prints the row count for each stage; or stop after 10 turns
/goal all 200 accounts in accounts.csv have a segment value from the allowed list; print the counts per segment; or stop after 15 turns
```

## Why bother

Anthropic's best-practices page names the cost of skipping this. Without a check Claude can run, you become the verification loop: every mistake waits for you to notice it.
