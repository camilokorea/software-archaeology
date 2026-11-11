---
id: architecture
version: 1.0.0
title: Architecture, layers and coupling
order: 30
areas: [architecture]
inputs: [inventory, externals, database, api, hotspots]
files:
  keywords: [controller, service, repository, manager, helper, util, dao, facade, handler, startup, module, context]
  hotspots: true
  largest: true
---
## Purpose
Recover the real architecture from the code: the layers, the boundaries that exist and the ones that are broken,
and how the parts talk to each other and to outside systems.

## Look for
- The layering actually used (UI → logic → data) and places that skip it, e.g. SQL or data access inside UI code,
  business rules inside controllers or pages.
- "God" classes or modules that everything depends on.
- Static/global state and singletons used to share data across requests.
- Synchronous calls to external systems without timeouts or fallbacks; integration through shared databases or files.
- Natural seams where the system could be split (candidates for modernizing piece by piece).
- Patterns in use (MVC, repository, CQRS, event-driven) and whether they are applied consistently.

## Evidence rules
Each coupling claim cites both sides when possible (where the dependency is declared and where it is used).

## Business translation
Explain coupling as "changing X forces changes in Y", and seams as "parts that could be modernized one at a time".

## Out of scope
Database schema details (database spec) and endpoint lists (api spec).
