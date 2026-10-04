# UX

The README is the landing page. The first screen has four parts:

1. An H1 that names the job.
2. The artifact the stranger holds.
3. A refusal in the first 100 lines. The script looks for a refusal, "will not", or "does not".
4. The install line `npx skills add owner/repo --all -g --full-depth`.

Right under the H1 and the one-line job, an "In 60 seconds" block: the marketplace add, the install, the one command, then the scorer on the good example and the bad example with the line each prints. A stranger tries the pack before reading further.

A refusal says what is wrong and what to change: `- <what is wrong> → <what to change>`. The last line names the next step: `Next: fix the lines above and run this again.` on a miss, the next command on a pass.

GitHub topics are the three strings on the design card. One of them is `agent-skills`. This script does not call GitHub.

This build directory is the gate. It is not a row on the suite page. Pack authors install it from the marketplace as `build-pack`.
