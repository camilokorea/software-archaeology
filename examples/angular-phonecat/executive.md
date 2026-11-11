# angular-phonecat: modernization brief

Prepared on 2026-11-10 from the code itself. Every statement links to the technical evidence behind it.

## Status: 🔴 Red

**The system works, but it carries serious risks that should be handled before any new feature.**

- Part of the system runs on AngularJS 1.8, which its maker stopped fixing on 2021-12-31. [DEP-001](technical.md#dep-001)
- Part of the system runs on Bootstrap 3.3, which its maker stopped fixing on 2019-07-24. [DEP-002](technical.md#dep-002)
- angular 1.8, a library the system depends on, has publicly known security flaws. [SEC-001](technical.md#sec-001)
- A small set of files absorbs most of the changes and most of the risk. [DEBT-001](technical.md#debt-001)
- Nobody has changed this system in years. [RSK-001](technical.md#rsk-001)
- bootstrap 3.3, a library the system depends on, has publicly known security flaws. [SEC-002](technical.md#sec-002)

**Recommendation.** Recommended path: replatform — Upgrade runtimes and frameworks that are past end of life, keeping the architecture. The system is built on AngularJS 1.x, jQuery.

## What the system does

The entry points of this system do not name its business capabilities clearly enough to list them without guessing. Run the analysis with an AI provider (the capabilities spec reads the code) or list them with the people who use the system.

## Risks

Impact and probability from 1 (low) to 5 (high).

| Risk | Impact | Probability | Evidence |
|---|:---:|:---:|---|
| Part of the system runs on AngularJS 1.8, which its maker stopped fixing on 2021-12-31. | 5 | 4 | [DEP-001](technical.md#dep-001) |
| Part of the system runs on Bootstrap 3.3, which its maker stopped fixing on 2019-07-24. | 4 | 4 | [DEP-002](technical.md#dep-002) |
| angular 1.8, a library the system depends on, has publicly known security flaws. | 4 | 4 | [SEC-001](technical.md#sec-001) |
| bootstrap 3.3, a library the system depends on, has publicly known security flaws. | 3 | 4 | [SEC-002](technical.md#sec-002) |
| jquery 3.3, a library the system depends on, has publicly known security flaws. | 3 | 4 | [SEC-003](technical.md#sec-003) |
| A small set of files absorbs most of the changes and most of the risk. | 3 | 3 | [DEBT-001](technical.md#debt-001) |
| Nobody has changed this system in years. | 3 | 3 | [RSK-001](technical.md#rsk-001) |

| Impact ↓ / Probability → | 1 | 2 | 3 | 4 | 5 |
|---|:---:|:---:|:---:|:---:|:---:|
| **5** | 🟨 | 🟧 | 🟥 | 🟥 1 | 🟥 |
| **4** | 🟨 | 🟧 | 🟧 | 🟥 2 | 🟥 |
| **3** | 🟩 | 🟨 | 🟧 2 | 🟧 2 | 🟥 |
| **2** | 🟩 | 🟨 | 🟨 | 🟧 | 🟧 |
| **1** | 🟩 | 🟩 | 🟩 | 🟨 | 🟨 |

## Options

The seven standard modernization strategies, sized for this system. Weeks are ranges for the stated team, not commitments.

| Strategy | What it means | Cost | Risk | Weeks | |
|---|---|:---:|:---:|:---:|---|
| **retain** | Keep the system as it is and only fix what is urgent (secrets, known vulnerabilities). | S | high | 1–3 |  |
| **rehost** | Move the same application to new infrastructure (containers or cloud VMs) without changing its code. | S | medium | 2–6 |  |
| **replatform** | Upgrade runtimes and frameworks that are past end of life, keeping the architecture. | M | medium | 4–8 | ⭐ recommended |
| **refactor** | Modernize gradually behind the same interfaces (strangler pattern), starting with the hotspots. | L | medium | 5–9 |  |
| **rearchitect** | Rebuild on a new architecture, reusing the business rules found in this report. | XL | high | 6–10 |  |
| **replace** | Replace with a commercial or open-source product that covers the same capabilities. | L | high | 8–26 |  |
| **retire** | Switch the system off if its capabilities are no longer needed. | S | low | 1–4 |  |

**Assumptions behind the recommended option (replatform):**

- Team of 3 developers familiar with the stack
- Size: about 1 thousand lines of code
- Ranges are ±50% and come from size and findings, not from a detailed plan
- Framework upgrades have a documented path

Based on: [DEP-001](technical.md#dep-001) [DEP-002](technical.md#dep-002)

## Roadmap

### 0 · Make it safe (1–3 weeks)

Close the urgent risks without changing behavior.

- Exposed credentials rotated and removed
- Known vulnerable libraries upgraded
- Builds run in CI

*Addresses:* [SEC-001](technical.md#sec-001) [SEC-002](technical.md#sec-002) [SEC-003](technical.md#sec-003) [SEC-004](technical.md#sec-004) [OPS-001](technical.md#ops-001) [OPS-002](technical.md#ops-002)

### 1 · Make it observable and testable (2–6 weeks)

Be able to change the system without fear.

- Characterization tests around the hotspots
- Logging and health metrics in production
- Business rules in the database cataloged

*Starts after:* 0 · Make it safe

*Addresses:* [DEBT-001](technical.md#debt-001)

### 2 · Replatform (4–8 weeks)

Upgrade runtimes and frameworks that are past end of life, keeping the architecture.

- First module moved and in production
- Old and new run side by side with the same results
- Remaining modules scheduled

*Starts after:* 1 · Make it observable and testable

*Addresses:* [DEP-001](technical.md#dep-001) [DEP-002](technical.md#dep-002)

### 3 · Spread the knowledge and retire the old (2–4 weeks)

Leave a system more than one person can maintain.

- Ownership of each module shared by at least two people
- Old components switched off

*Starts after:* 2 · Replatform

*Addresses:* [RSK-001](technical.md#rsk-001)

## How reliable is this?

- 10 findings: **10 verified by tools** (manifests, git, scanners) and **0 inferred by AI** and checked against the code they cite.
- 0 AI statements were rejected because the code did not back them.
- Analysis: deterministic tools only (no AI). Full method and costs: `run.json`.

## Questions

**Is the system at risk today?**

Yes. The first items in the risk list should be handled now.

**Can we keep it as it is?**

Only for a short time: keeping it means accepting the risks above.

**How long would the recommended path take?**

About 4–8 weeks for a team of 3, plus the first two roadmap phases. These are ranges from the size of the code and the findings, not a commitment.

**What should we do first?**

Phase 0 of the roadmap: close exposed secrets and known vulnerabilities, and get builds running automatically.

**How sure are these findings?**

All 10 findings are verified by tools (manifests, git history, scanners). Each one links to its evidence.

## Glossary

| Term | Meaning |
|---|---|
| end of life | The date after which the maker of a technology stops publishing fixes, including security fixes. |
| known vulnerability | A security flaw that has been published (in OSV, CVE lists), with the affected versions. |
| rehost / replatform / refactor | Move as is / upgrade the platform underneath / restructure the code gradually. |
| verified finding | A fact produced by a deterministic tool (a manifest, git, a scanner), not by an AI model. |
| inferred finding | A conclusion an AI model drew from the evidence; it was checked against the cited code, but should be confirmed. |

