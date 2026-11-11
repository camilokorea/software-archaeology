---
id: capabilities
version: 1.0.0
title: Business capabilities and rules
order: 100
areas: [capabilities]
inputs: [api, database, inventory]
files:
  keywords: [order, invoice, bill, payment, customer, account, product, catalog, cart, report, user, admin, inventory, ship, price, tax, loan, policy, claim, card, transaction]
  content: "class\\s+\\w*(Service|Manager|Controller|ActionBean)|PROCEDURE|PROGRAM-ID"
---
## Purpose
Recover what the system does for the business — its capabilities and the rules inside them — in words a product
manager recognizes. This is the bridge between the two reports.

## Look for
- Capabilities: the main things users can do (e.g. "place an order", "approve a credit") and where each lives.
- Business rules encoded in the code: thresholds, statuses, calculations, approvals. Quote the condition.
- Rules implemented in more than one place, or inconsistently.
- Capabilities that look half-built, disabled or unreachable.

## Evidence rules
Each capability cites at least one entry point or class; each rule cites the line with the condition.

## Business translation
This spec is mostly business translation: name capabilities and rules as a user or manager would.

## Out of scope
Judging whether the rules are correct for the business; only report what the code does.
