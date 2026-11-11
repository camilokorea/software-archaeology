# Finding format

Every phase produces and consumes the same structure ([schema](../schemas/finding.schema.json)). It is what links the
two reports.

```json
{
  "id": "SEC-003",
  "spec": "security",
  "area": "security",
  "title": "Password inside a connection string found in 1 file(s)",
  "severity": "high",
  "kind": "verified",
  "confidence": "high",
  "evidence": [{"file": "Web/web.config", "line": 4, "excerpt": "Password=[REDACTED-SECRET];", "source": "gitleaks"}],
  "technical_impact": "Credentials are committed to the source tree…",
  "business_impact": "Passwords are written inside the code…",
  "effort": "S",
  "recommendation": "Rotate these credentials now…",
  "tags": ["secret"],
  "refs": ["CWE-798", "OWASP A07:2021"]
}
```

| Field | Meaning |
|---|---|
| `id` | Area prefix and number, assigned after validation, ordered by priority. |
| `area` | inventory, dependencies, architecture, database, api, security, testing, tech-debt, devops, risk, capabilities, people. |
| `severity` | critical (breach, data loss or outage now) · high · medium · low · info. |
| `kind` | `verified` from deterministic tools, `inferred` from a model. |
| `confidence` | high, medium, low. |
| `evidence` | Files and lines, with a verbatim excerpt when the line matters. Checked by the validator. |
| `technical_impact` / `business_impact` | The same fact for the two audiences. |
| `effort` | S, M, L, XL for the recommendation. |

The business synthesis ([schema](../schemas/synthesis.schema.json)) cites findings by `id` in every summary point,
risk, option and roadmap phase.
