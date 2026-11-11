---
id: tech-debt
version: 1.0.0
title: Technical debt and refactoring opportunities
order: 80
areas: [tech-debt]
inputs: [hotspots, complexity]
files:
  hotspots: true
  largest: true
---
## Purpose
Find the debt that most raises the cost of change, starting from the hotspots, and propose specific refactorings.

## Look for
- Duplicated logic (the same rule implemented in several places, possibly differently).
- Very long methods, deep nesting, flags that switch behavior, magic numbers that encode business rules.
- Error handling that swallows exceptions or hides failures.
- Commented-out code, TODO/FIXME/HACK markers that describe known problems.
- Dead code and unused parameters.

## Evidence rules
Cite the exact lines. For duplication cite at least two places.

## Business translation
Explain debt as extra time and risk on future work, with the area of the product it affects.

## Out of scope
Style preferences that do not affect cost of change.
