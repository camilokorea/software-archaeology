---
id: devops
version: 1.0.0
title: Build, deployment and operations
order: 90
areas: [devops]
inputs: [devops, inventory]
files:
  globs: ["**/Dockerfile*", "**/*compose*.y*ml", "**/.github/workflows/*", "**/azure-pipelines*.yml", "**/Jenkinsfile", "**/.gitlab-ci.yml", "**/*.tf", "**/*.sh", "**/*.ps1", "**/*.bat", "**/web.config", "**/*.pubxml", "**/build.xml", "**/Makefile"]
---
## Purpose
Understand how the system is built, deployed and observed, and what makes releases slow or risky.

## Look for
- How a build is produced (scripts, IDE-only steps, manual instructions in READMEs).
- Deployment method (copy to server, web deploy, containers) and environment-specific steps.
- Configuration and secrets per environment, and how they reach the server.
- Logging, health checks, monitoring and error reporting in the code.
- Container images using old or unpinned base images.

## Evidence rules
Cite the script or configuration lines. When something is missing, cite where it would be expected (e.g. the README
build section) and put the absence in `not_found` if nothing points to it.

## Business translation
Describe how long and how risky a release is, and what would make it routine.

## Out of scope
Cloud provider selection.
