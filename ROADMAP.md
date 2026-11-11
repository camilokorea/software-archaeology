# Roadmap

## 2.0 (this release)

- One command from a clone to two reports (`./dig.sh`, `archaeology dig`), Docker image, local fallback.
- Deterministic evidence: inventory, dependencies, end of life, known vulnerabilities, secrets, git history,
  hotspots, entry points, database, tests, DevOps, external systems.
- Twelve executable specs, structured findings, citation validator, verified vs inferred.
- Business brief (status, capabilities, risks, 7R options, roadmap, FAQ, glossary) and technical report, with HTML
  twins, backlog CSV and a container diagram.
- Providers: none, Anthropic, Ollama; Claude Code plugin and AGENTS.md for any agent.
- Budget, cost estimate, dry run, cache, incremental runs, per-component analysis of large repositories.

## Next

- **Public worked examples** in `examples/`, analyzing open-source legacy applications, with their published
  reports, and CI that re-runs them on every change. Candidates under review.
- Reports in Spanish and Portuguese (`output.language`).
- More providers through an OpenAI-compatible endpoint (Azure OpenAI, vLLM, LM Studio).
- Optional coverage import (Cobertura, LCOV, JaCoCo) to replace the test/source ratio.

## Planned specs

These areas were sketched in version 1 as placeholders and will be written as executable specs, one by one:

- **Architecture:** clean architecture conformance, CQRS, domain-driven design discovery.
- **Backend:** background jobs, error handling, message queues, service layer.
- **Frontend:** component inventory, routing, state management, UI technical debt.
- **Data:** ORM mapping, query performance.
- **Security:** authentication and authorization in depth.
- **DevOps:** Kubernetes and container hardening.
- **Diagrams:** class diagrams, sequence diagrams, PlantUML export.
- **Governance:** coding standards, engineering maturity, architecture governance.
- **AI:** semantic code graph, knowledge graph and RAG index export.
- **Modernization:** cloud migration readiness, monolith decomposition, framework-specific upgrade guides
  (AngularJS → Angular, .NET Framework → .NET, Java EE → Spring Boot).
