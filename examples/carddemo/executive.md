# carddemo: modernization brief

Prepared on 2026-11-10 from the code itself. Every statement links to the technical evidence behind it.

## Status: 🟠 Amber

**The system is maintainable today, with risks that will grow if nothing is done.**

- An important part of the system uses CICS, a technology that is hard to hire for and cannot be upgraded in place. [ARC-001](technical.md#arc-001)
- Nothing checks automatically that the system still works after a change. [TST-001](technical.md#tst-001)
- A small set of files absorbs most of the changes and most of the risk. [DEBT-001](technical.md#debt-001)
- Builds and releases depend on someone's machine and memory, which makes them slow and error-prone. [OPS-001](technical.md#ops-001)

**Recommendation.** Recommended path: refactor — Modernize gradually behind the same interfaces (strangler pattern), starting with the hotspots. The system is built on CICS, COBOL, JCL batch.

## What the system does

The entry points of this system do not name its business capabilities clearly enough to list them without guessing. Run the analysis with an AI provider (the capabilities spec reads the code) or list them with the people who use the system.

## Risks

Impact and probability from 1 (low) to 5 (high).

| Risk | Impact | Probability | Evidence |
|---|:---:|:---:|---|
| Nothing checks automatically that the system still works after a change. | 4 | 4 | [TST-001](technical.md#tst-001) |
| An important part of the system uses CICS, a technology that is hard to hire for and cannot be upgraded in place. | 4 | 3 | [ARC-001](technical.md#arc-001) |
| A small set of files absorbs most of the changes and most of the risk. | 3 | 3 | [DEBT-001](technical.md#debt-001) |
| Builds and releases depend on someone's machine and memory, which makes them slow and error-prone. | 3 | 3 | [OPS-001](technical.md#ops-001) |

| Impact ↓ / Probability → | 1 | 2 | 3 | 4 | 5 |
|---|:---:|:---:|:---:|:---:|:---:|
| **5** | 🟨 | 🟧 | 🟥 | 🟥 | 🟥 |
| **4** | 🟨 | 🟧 | 🟧 1 | 🟥 1 | 🟥 |
| **3** | 🟩 | 🟨 | 🟧 2 | 🟧 | 🟥 |
| **2** | 🟩 | 🟨 | 🟨 | 🟧 | 🟧 |
| **1** | 🟩 | 🟩 | 🟩 | 🟨 | 🟨 |

## Options

The seven standard modernization strategies, sized for this system. Weeks are ranges for the stated team, not commitments.

| Strategy | What it means | Cost | Risk | Weeks | |
|---|---|:---:|:---:|:---:|---|
| **retain** | Keep the system as it is and only fix what is urgent (secrets, known vulnerabilities). | S | high | 1–3 |  |
| **rehost** | Move the same application to new infrastructure (containers or cloud VMs) without changing its code. | S | medium | 3–8 |  |
| **replatform** | Upgrade runtimes and frameworks that are past end of life, keeping the architecture. | M | medium | 7–17 |  |
| **refactor** | Modernize gradually behind the same interfaces (strangler pattern), starting with the hotspots. | L | medium | 19–43 | ⭐ recommended |
| **rearchitect** | Rebuild on a new architecture, reusing the business rules found in this report. | XL | high | 48–105 |  |
| **replace** | Replace with a commercial or open-source product that covers the same capabilities. | L | high | 8–26 |  |
| **retire** | Switch the system off if its capabilities are no longer needed. | S | high | 1–4 |  |

**Assumptions behind the recommended option (refactor):**

- Team of 3 developers familiar with the stack
- Size: about 48 thousand lines of code
- Ranges are ±50% and come from size and findings, not from a detailed plan
- Tests are added before each part is moved

Based on: [ARC-001](technical.md#arc-001) [TST-001](technical.md#tst-001) [DEBT-001](technical.md#debt-001) [DEBT-002](technical.md#debt-002)

## Roadmap

### 0 · Make it safe (1–3 weeks)

Close the urgent risks without changing behavior.

- Exposed credentials rotated and removed
- Known vulnerable libraries upgraded
- Builds run in CI

*Addresses:* [OPS-001](technical.md#ops-001) [OPS-002](technical.md#ops-002) [OPS-003](technical.md#ops-003)

### 1 · Make it observable and testable (2–6 weeks)

Be able to change the system without fear.

- Characterization tests around the hotspots
- Logging and health metrics in production
- Business rules in the database cataloged

*Starts after:* 0 · Make it safe

*Addresses:* [TST-001](technical.md#tst-001) [DEBT-001](technical.md#debt-001) [DEBT-002](technical.md#debt-002)

### 2 · Refactor (19–43 weeks)

Modernize gradually behind the same interfaces (strangler pattern), starting with the hotspots.

- First module moved and in production
- Old and new run side by side with the same results
- Remaining modules scheduled

*Starts after:* 1 · Make it observable and testable

*Addresses:* [ARC-001](technical.md#arc-001) [TST-001](technical.md#tst-001) [DEBT-001](technical.md#debt-001) [DEBT-002](technical.md#debt-002)

### 3 · Spread the knowledge and retire the old (2–4 weeks)

Leave a system more than one person can maintain.

- Ownership of each module shared by at least two people
- Old components switched off

*Starts after:* 2 · Refactor

## How reliable is this?

- 7 findings: **7 verified by tools** (manifests, git, scanners) and **0 inferred by AI** and checked against the code they cite.
- 0 AI statements were rejected because the code did not back them.
- Analysis: deterministic tools only (no AI). Full method and costs: `run.json`.

## Questions

**Is the system at risk today?**

Not immediately, but the risks listed grow every month.

**Can we keep it as it is?**

Only for a short time: keeping it means accepting the risks above.

**How long would the recommended path take?**

About 19–43 weeks for a team of 3, plus the first two roadmap phases. These are ranges from the size of the code and the findings, not a commitment.

**What should we do first?**

Phase 0 of the roadmap: close exposed secrets and known vulnerabilities, and get builds running automatically.

**How sure are these findings?**

All 7 findings are verified by tools (manifests, git history, scanners). Each one links to its evidence.

## Glossary

| Term | Meaning |
|---|---|
| continuous integration | A service that builds and tests the system automatically on every change. |
| rehost / replatform / refactor | Move as is / upgrade the platform underneath / restructure the code gradually. |
| verified finding | A fact produced by a deterministic tool (a manifest, git, a scanner), not by an AI model. |
| inferred finding | A conclusion an AI model drew from the evidence; it was checked against the cited code, but should be confirmed. |

