# Privacy and data handling

Software Archaeology is built to run on proprietary code.

| What | Where it goes |
|---|---|
| Your code | Read locally. Sent to a model **only** when an AI provider is configured and `privacy.send_source` is `true`, and only the files selected for each spec. |
| Secret values | Never written anywhere and never sent. Detected values are kept in memory to redact prompts and reports; reports show `[REDACTED-SECRET]`. |
| Emails, phone numbers, IP addresses | Redacted from prompts by default (`privacy.redact`). |
| Author names | Replaced by "Dev 1", "Dev 2"… (`privacy.pseudonymize_authors`). |
| Package names and versions | Sent to endoflife.date and osv.dev when `network.enabled` is true. No code. Set `--offline` to avoid it. |
| Files matching `privacy.never_send` | Never sent (`.env`, keys, certificates by default). |

Choosing a provider:

- `none`: nothing leaves the machine except the package lookups above.
- `ollama`: a local model; code stays on the machine (or your server).
- `anthropic`: code samples go to Anthropic's API under your account's terms.
- `claude-code` / other agents: the agent's own data policy applies.

`--dry-run` writes the exact prompts to the output folder so you can review what would be sent before sending it.
