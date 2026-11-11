---
id: inventory
version: 1.0.0
title: Inventory and system shape
order: 10
areas: [inventory, architecture]
inputs: [inventory, history]
files:
  keywords: [readme, startup, program, global.asax, web.config, app.config, main, index, application]
  globs: ["README*", "**/Program.cs", "**/Startup.cs", "**/Global.asax*", "**/web.config", "**/main.*", "**/app.js", "**/app.module.*"]
  largest: true
---
## Purpose
Establish what this system is, how big it is, how it starts, and how it is organized, so every other spec and both
audiences share the same picture.

## Look for
- Entry points: how the application starts (Program/Startup, Global.asax, main, index, app bootstrap), and how many
  separately deployable parts there are.
- Whether the folder structure matches the components the inventory found, or hides several applications in one.
- Generated, vendored or copied third-party code mixed with the team's own code.
- Dead weight: whole folders that look unused (no references, last changed long ago according to history).
- Configuration that differs per environment and how it is selected.

## Evidence rules
Cite the startup file and the configuration lines. For "unused" claims cite the history evidence (last change) and
say what reference you searched for.

## Business translation
Describe the system in one sentence a manager could repeat: what kind of application, roughly how big, how many
pieces have to be deployed.

## Out of scope
Line counts and language lists themselves (already in the evidence); security and dependencies (own specs).
