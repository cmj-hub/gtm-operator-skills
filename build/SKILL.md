---
name: build-pack
description: Use when starting a GTM skill pack, before the pack is written, or when a scorecard, license, secret, README, or install line is about to ship.
models: ""
---

# Build a skill pack

One pack finishes one job. The script is the gate. Cards are paths. They do not have to be committed.

Python 3 stdlib. No install.

```bash
python3 scripts/check_pack.py knowledge <card>
python3 scripts/check_pack.py design <card>
python3 scripts/check_pack.py pack <dir> --public
python3 scripts/check_pack.py pack <dir> --private
python3 scripts/check_pack.py all <dir> --public --knowledge <card> --design <card>
```

Success prints `knowledge ok`, `design ok`, or `pack ok`. A miss prints `Refusal:` and exits 1.

## Checklist

Copy this list and tick it in order.

- [ ] 1. Knowledge. Fill the card. Run the knowledge command. Read [knowledge.md](knowledge.md).
- [ ] 2. Design. Fill the card. Run the design command. Read [design.md](design.md).
- [ ] 3. Implementation. Write the pack. `models` stays empty until a named model has run it. The body stays under 500 lines. A reference over 100 lines starts with Contents. Link every reference from this file, one level deep. A low-freedom step is a script, and the script is executed.
- [ ] 4. Security. Run the pack command with `--public` or `--private`. Read [security.md](security.md).
- [ ] 5. UX. The README is the landing page. Read [ux.md](ux.md).
- [ ] 6. Scorecard. Run the pack's scorer on one bad fixture and one good fixture.
- [ ] 7. Release. Open a pull request from a worktree of origin/main. Leave it unmerged. Do not upload a zip by hand.

Go back to step 3 if step 4 or step 6 fails.
Go back to step 2 if step 5 fails.

One return. If the same step fails again, stop and fix the script or the card before another pass.

Passing shapes: `examples/knowledge.json` and `examples/design.json`.
