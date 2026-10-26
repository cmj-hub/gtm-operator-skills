# Approval card

One proposed change per card. The agent fills it, shows it, and waits. Nothing runs until the person answers.

```text
Proposed change. Nothing has run yet.

Record:  {record name and type}
Field:   {field}
Now:     {value read from the record just now}
After:   {new value}
Why:     {one line, in plain words}
Source:  {URL, call note, or file and row the new value came from}
Undo:    {the one step that puts it back, or "nothing takes this back"}

Reply yes to apply, no to drop it, or edit any line.
```

## Rules for the agent

1. Read the record before you write the card. `Now` is what the record says at this moment, not what you remember.
2. One record, one field, one card. Ten changes are ten cards, shown together if the person wants a batch.
3. `Source` is something the person can open. If you cannot point to one, the change is a guess. Say so on the card.
4. `Undo` is honest. A field edit can be set back. A sent email, a deleted record or a merged pair cannot. Write "nothing takes this back" when that is true.
5. A yes covers this card only. It is not permission for the next one.
6. After a yes, read the record again and say what it now holds.

## Filled in

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

The same card, as JSON, is the `approval_cards` entry in `examples/guardrails-good.json`. The scorer refuses a card with no `before`, no `source` or no `undo`.
