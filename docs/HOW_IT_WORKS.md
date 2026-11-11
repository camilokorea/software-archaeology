# How it works

## Phases

| Phase | What happens | Uses AI | Output |
|---|---|---|---|
| 0 · Intake | One walk over the repository: languages, size, frameworks, components (one per build manifest). | No | `evidence/inventory.json` |
| 1 · Evidence | Dependencies and runtimes from manifests; end of life from endoflife.date; known vulnerabilities from osv.dev; secrets (gitleaks or built-in rules); git history (churn, authors, knowledge concentration, bus factor); complexity and hotspots; entry points; database objects and stores; tests; CI, containers, IaC, observability; external hosts and messaging. | No | `evidence/*.json` |
| Rules | The evidence becomes **verified** findings: end of life, vulnerabilities, secrets, hotspots, large files, knowledge concentration, dormant code, missing tests, missing CI, logic in stored procedures, legacy platforms. | No | in `findings/findings.json` |
| 2 · Analysis | Each spec gets its evidence and a ranked, budgeted, redacted sample of files, and returns **inferred** findings and a `not_found` list. Large repositories and monorepos are analyzed per component. Results are cached by the hash of everything in the prompt. | Optional | cache, then findings |
| 3 · Validation | Every finding is checked against its schema and every citation against the code: the file exists, the line exists, the quoted text is there. Failures go to `findings/rejected.json`. | No | `findings/` |
| 3 · Synthesis | The business view: status, capabilities, risks, seven options, roadmap, FAQ, glossary. Built by explicit rules, then optionally rewritten by a model; statements that cite unknown findings are removed. | Optional | `synthesis.json` |
| 4 · Reports | Both reports, HTML twins, backlog CSV, diagram, run log. | No | output folder |

## Guarantees

- **Read-only.** The analyzed repository is never written. The output folder must be outside it, and Docker mounts it
  read-only. Git is only read (`log`, `rev-parse`, `diff`, `remote get-url`).
- **Evidence first.** A finding without a valid citation does not reach a report.
- **Verified vs inferred.** Reports mark which findings come from tools and which from a model.
- **Secrets never leave.** Secret values are kept in memory only, redacted from prompts and from every report.
- **Repeatable.** `run.json` records the tool version, each spec's version and hash, the model and the cost.
- **Failure-tolerant.** A failed spec is skipped and logged; a missing key or credit stops AI calls and the reports
  still come out with the verified findings. Network lookups fail soft and are cached.

## Agents

`archaeology evidence` stops after phase 1 and writes one task per spec in `agent-tasks/`. Any agent can analyze
them and write JSON to `findings/agent/`; `archaeology finish` validates and reports. See [AGENTS.md](../AGENTS.md).
