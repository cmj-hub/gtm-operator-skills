# Security

What runs on your machine:

- One script, `scripts/check_context.py`. Python 3.10 or newer, standard library only. It reads the files in your `context/` folder and prints a result. It writes nothing.
- The skill itself asks you questions and writes seven markdown files and an index into `context/` at your project root. It writes nowhere else.
- If you point it at a website, the skill fetches those pages through your agent's own fetch tool. The pack opens no connection of its own.

Network: none from the pack's script. Telemetry: none. Credentials: none read, none needed.

Your answers stay in your `context/` folder. Check the files before you commit them: they hold what you tell the agent about your company and customers, and a result you cite may name a customer.

Report a vulnerability by email to jay@jaymountconsulting.com with "security" and "company-context-pack" in the subject, or open a private advisory under this repo's Security tab. Do not open a public issue for it.
