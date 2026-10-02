# Design

The card is a JSON object. `examples/design.json` is a shape the script accepts. Replace every value.

- `artifact` — the one thing a stranger holds.
- `refusal` — the wrong shape the pack refuses.
- `group` — one of foundation, offer, outbound, findability, pages, email, social, paid, measurement, motion.
- `topics` — exactly three strings, and one is `agent-skills`. The other two are the job tag and the group tag.
- `freedom` — a list of steps. Each step has `level` and `if_different`.
  - `level` is `low`, `medium`, or `high`. `low` names the script and the script is executed. `medium` names a `template` (parameters or pseudocode). `high` is guidance.
  - `if_different` is `nothing-much` or `consequential`. Consequential means money, a delete, a send, or anything irreversible, and that step is `low` with a script. `nothing-much` may stay `high`, and it may still be `low` when a script already does it.
- `ordered` — true when sequence matters. `all` then requires each SKILL.md to have a checklist (`- [ ]` or "Copy this") and a go-back line (`go back to step` or `return to step`). False when order does not matter, and a checklist is not required.
- `quality` — true when the draft is checked against something concrete. `all` then requires "check again" or "review again" in a SKILL.md, or a script whose name starts with `score` or contains `validat` or `lint`. False when a second pass would not change the artifact.

```bash
python3 scripts/check_pack.py design <card>
```

`design ok` means the shape passed. `all` applies `ordered` and `quality` to the pack. Topics stay on the card. This script does not call GitHub.
