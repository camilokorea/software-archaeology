---
id: dependencies
version: 1.0.0
title: Dependencies, runtimes and upgrade paths
order: 20
areas: [dependencies]
inputs: [dependencies, eol, vulnerabilities, inventory]
files:
  globs: ["**/package.json", "**/bower.json", "**/packages.config", "**/*.csproj", "**/pom.xml", "**/build.gradle", "**/requirements.txt", "**/composer.json", "**/web.config"]
---
## Purpose
Turn the dependency evidence into upgrade decisions. End-of-life and known vulnerabilities are already reported by
tools; add what tools cannot see.

## Look for
- Frameworks that block each other's upgrade (e.g. a library that only works on an old runtime).
- Abandoned or deprecated libraries (no successor, archived, replaced by the platform), visible from their names and
  versions.
- Copies of libraries checked into the source tree instead of declared in a manifest.
- Several versions of the same library in different components.
- Assembly binding redirects, version pins or comments explaining why a version is frozen.

## Evidence rules
Cite the manifest line that declares each dependency. Do not restate end-of-life or OSV results unless you add the
upgrade constraint or the blocking relationship.

## Business translation
Explain upgrades as "this part has to be replaced before that part can move", and the consequence of not doing it.

## Out of scope
Vulnerability details (security spec) and line-by-line code issues.
