# Update mode

Refresh one file without redoing the interview. Run as `update <file>`, for example `update icp`. The file name is `company`, `icp`, `offer`, `proof`, `voice`, `objections`, or `categories`. Refuse any other name, and any name with a slash or "..".

## Checklist

Copy this list and tick it in order.

- [ ] 1. Read `context/<file>.md`. If it does not exist, say so and run the full interview instead.
- [ ] 2. Show the user its sections in a short list, with the `Updated:` date.
- [ ] 3. Ask one question: "What changed since <date>?" Take the answer as free text.
- [ ] 4. Ask follow-ups only for sections the answer touches, one at a time, using the matching questions in [interview.md](../interview.md). Leave every other section exactly as it is.
- [ ] 5. Show the user the old and new text of each section you will change. Write only after they agree.
- [ ] 6. Set `Updated:` to today's date in that file and in `context/CONTEXT.md`. Change nothing else in the index.
- [ ] 7. Run `python3 ${CLAUDE_SKILL_DIR}/scripts/check_context.py --dir context` and fix every refusal.

Go back to step 5 if step 7 refuses.

## Rules

- Touch one file. If the answer belongs in another file, say which and offer to run update on it.
- Keep results that still have a source. Do not remove a proof line unless the user says it is no longer true.
- Keep the proof rule: a new result needs `Source:` or `Source: unverified`.
- A file that did not change in a year is stale. Say so when you read it, and ask whether to refresh it.
