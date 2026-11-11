# Changelog

## 2.0.0

A rewrite: the repository is now a tool you run, not a set of documents to read.

- Added the `archaeology` CLI and `dig.sh`: intake, evidence, rules, AI analysis, validation, synthesis and reports.
- Added twelve executable specs with front matter, JSON schemas for findings and synthesis, and the analyst and
  synthesis prompts.
- Added the business brief and the technical report (Markdown and HTML), backlog CSV, container diagram, run log.
- Added Anthropic and Ollama providers, the Claude Code plugin (`/software-archaeology:dig`) and AGENTS.md.
- Added privacy controls, budget and cost estimate, dry run, cache and incremental runs.
- Added a Dockerfile with tokei and gitleaks, CI, and tests against a synthetic legacy application.
- Added five public examples in `examples/` (eShopModernizing, CardDemo, JPetStore, angular-phonecat, NodeGoat) and
  a CI job that checks their verified findings still reproduce.
- Removed the 63 placeholder documents of 1.0; their topics are listed in ROADMAP.md as planned specs.
- Renamed the project files to "archaeology" consistently and replaced the banner.

## 1.0.0

- Initial repository: placeholder specification documents, prompts and templates.
