# Security

What this pack does on your machine:

- `skills/claim-check/scripts/claim_check.py` is standard-library Python. It reads only the files and folders you name on the command line (`.md`, `.mdx`, `.txt`; files over 2 MB are skipped), and it skips `.git`, `node_modules` and build folders.
- It prints file paths, line numbers, the matched figure and about 100 characters of the sentence around it. Everything it prints is cut to printable ASCII, so control and direction-changing characters in a draft never reach your terminal or your agent.
- The draft is data. Nothing in it is executed, fetched or followed, and the skill tells the agent to treat the quoted context as text, not instructions.
- It writes nothing, deletes nothing, and edits nothing. A test checks that a run leaves a throwaway tree byte-identical.
- Network: None. It never opens the links it finds.
- No telemetry, no credentials asked for or stored.

Report privately through GitHub's 'Report a vulnerability' button on this repo. Do not open a public issue.
