---
id: people
version: 1.0.0
title: People, knowledge and documentation
order: 110
areas: [people]
inputs: [history, hotspots]
files:
  globs: ["README*", "**/docs/**", "**/*.md", "CONTRIBUTING*", "CHANGELOG*"]
  hotspots: true
---
## Purpose
Assess how much of the system is understood by more than one person and how much is written down.

## Look for
- Whether the README explains how to build, run and deploy, and whether it matches the code.
- Architecture or decision documents, and whether they are current.
- Comments that explain *why* in the hotspots, or their absence.
- Knowledge concentration from the history evidence (authors are pseudonyms: never try to identify people).

## Evidence rules
Cite documentation lines or their absence in the hotspots. Use history only as provided.

## Business translation
Explain the risk of losing key people and what documentation would reduce it.

## Out of scope
Judging individual contributors.
