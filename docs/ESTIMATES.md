# Where the estimates come from

Estimates in the business brief are deliberately simple, written out, and shown as ranges. They are a starting
point for planning, not a commitment. Change the assumptions and the numbers change; that is the point of writing
them down.

## Inputs

- **Size:** thousands of lines of code (KLOC), from phase 0.
- **Findings:** how many runtimes and frameworks are past end of life, whether a legacy platform (Web Forms, WCF,
  Classic ASP, ColdFusion, Struts, CICS) is present, and how many technical-debt, testing and database findings exist.
- **Team:** three developers who know the stack.

## Week ranges per strategy

| Strategy | Low | High |
|---|---|---|
| retain | 1 | 3 |
| rehost | 2 + KLOC/50 | 6 + KLOC/25 |
| replatform | KLOC × 0.15 + 2 per end-of-life item | KLOC × 0.35 + 4 per end-of-life item |
| refactor | KLOC × 0.4 | KLOC × 0.9 |
| rearchitect | KLOC × 1.0 | KLOC × 2.2 |
| replace | 8 | 26 |
| retire | 1 | 4 |

A deeper strategy never shows fewer weeks than a shallower one (rehost ≤ replatform ≤ refactor ≤ rearchitect).

## Recommended strategy

1. A legacy platform is present → **refactor** (strangler: replace it piece by piece).
2. Otherwise, something is past end of life → **replatform**.
3. Otherwise, serious findings with technical debt → **refactor**; serious findings without debt → **retain** and fix.
4. Otherwise → **retain**.

With a model configured, the synthesis may adjust a range; it must say why in that option's assumptions.

## Effort per finding

S under a week · M one to three weeks · L one to two months · XL more. In `backlog.csv` they become 2, 5, 13 and 21
story points.
