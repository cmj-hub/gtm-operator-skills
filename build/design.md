# Design

The card is a JSON object. `examples/design.json` is a shape the script accepts. Replace every value.

- `artifact` — the one thing a stranger holds.
- `refusal` — the wrong shape the pack refuses.
- `group` — one of foundation, offer, outbound, findability, pages, email, social, paid, measurement, motion.
- `topics` — exactly three strings, and one is `agent-skills`. The other two are the job tag and the group tag.
- `freedom` — a list of steps. `level` is `low`, `medium`, or `high`. A `low` step names the script that does it.

```bash
python3 scripts/check_pack.py design <card>
```

`design ok` means the shape passed. Topics stay on the card. This script does not call GitHub.
