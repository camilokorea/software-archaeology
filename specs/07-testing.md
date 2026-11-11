---
id: testing
version: 1.0.0
title: Tests and safety net
order: 70
areas: [testing]
inputs: [tests, hotspots]
files:
  keywords: [test, spec]
  hotspots: true
---
## Purpose
Judge whether the existing tests would catch a regression during modernization, and where tests are needed first.

## Look for
- What the tests actually check: real behavior, or only that code runs (tests without assertions, mocked-out logic).
- Whether the hotspots are covered by any test.
- Tests that depend on a live database, network or the current date, and would be flaky.
- Disabled or skipped tests and why.
- Code that is hard to test (static dependencies, `new` inside logic, no seams) and the smallest change that makes it testable.

## Evidence rules
Cite test files and the production code they exercise (or fail to).

## Business translation
Explain how safely the system can be changed today and what has to happen before a migration.

## Out of scope
Writing the tests.
