---
id: risk
version: 1.0.0
title: Modernization risks
order: 120
areas: [risk]
inputs: [inventory, eol, hotspots, tests, database, externals, history]
files:
  hotspots: true
  keywords: [config, startup, global, integration, client, gateway, adapter]
---
## Purpose
Name the risks that would make a modernization fail or cost more than planned, with what reduces each one.

## Look for
- Hidden integrations (shared databases, file drops, scheduled jobs, hard-coded hosts) that a rewrite could break.
- Behavior nobody could reproduce without the code (calculations, edge cases, date and currency handling).
- Platform lock-in (Windows-only APIs, vendor SDKs, mainframe services).
- Data migration risk (encodings, formats, volume, data quality checks in code).
- Operational dependencies (batch windows, manual steps).

## Evidence rules
Each risk cites what reveals it. Do not list generic project risks.

## Business translation
Write each risk as "if we change X without handling Y, then Z happens", with what reduces it.

## Out of scope
Budget and staffing risks not visible in the code.
