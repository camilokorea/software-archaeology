# AI Modernization Specs

## Project Vision
AI Modernization Specs is an open-source, AI-native specification framework for enterprise legacy application modernization. This repository defines structured Markdown artifacts for reverse engineering, architecture discovery, modernization assessment, and AI-driven transformation workflows.

## Problem Statement
Legacy applications are difficult to understand, assess, and modernize at enterprise scale. Existing documentation is fragmented, technology-specific, and not optimized for large language models or autonomous analysis agents.

## Why AI-Native Specifications Matter
This repository treats Markdown specifications as first-class artifacts for AI systems. It provides deterministic, agent-friendly guidance for discovery, analysis, and modernization, reducing hallucination risk and increasing repeatability.

## How to Use the Specs
1. Review the inventory and architecture artifacts to build a detailed application profile.
2. Use prompts in `prompts/` to orchestrate LLM or agent workflows.
3. Apply templates in `templates/` when creating new assessments.
4. Reference `docs/` for governance, terminology, and agentic engineering guidance.

## Supported Technologies
- Enterprise Java, .NET, Node.js, Python
- Cloud platforms: AWS, Azure, GCP
- Containers and orchestration: Docker, Kubernetes
- Data platforms: SQL, NoSQL, ORM systems
- AI systems: RAG, semantic indexing, code graphs, prompt engineering

## Example Workflows
- Inventory a codebase using `inventory/SOURCE_CODE_INVENTORY.md`
- Discover architecture with `architecture/ARCHITECTURE_DISCOVERY.md`
- Assess modernization readiness using `modernization/LEGACY_MODERNIZATION_ASSESSMENT.md`
- Generate secure migration plans with `security/SECURITY_ANALYSIS.md`

## Example AI Usage
- Use `prompts/legacy-modernization-prompt.md` to seed a modernization planning agent.
- Use `prompts/ai-code-analysis-prompt.md` to drive a reverse-engineering pipeline.
- Use `templates/architecture-template.md` to create consistent architectural assessments.

## Contribution Instructions
See `CONTRIBUTING.md` for contribution workflow, issue templates, and review expectations.

## Roadmap
See `ROADMAP.md` for planned releases and future expansion.

## Future Vision
This repository will evolve into an enterprise-grade standard for AI-assisted software archaeology and modernization. It is designed to scale across cross-functional teams, automated agents, and governance practices.
