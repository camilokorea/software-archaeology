# NodeGoat: modernization brief

Prepared on 2026-11-10 from the code itself. Every statement links to the technical evidence behind it.

## Status: 🔴 Red

**The system works, but it carries serious risks that should be handled before any new feature.**

- underscore 1.8.3, a library the system depends on, has publicly known security flaws. [SEC-001](technical.md#sec-001)
- Passwords or keys are written inside the code. [SEC-002](technical.md#sec-002)
- body-parser 1.15.1, a library the system depends on, has publicly known security flaws. [SEC-003](technical.md#sec-003)
- marked 0.3.5, a library the system depends on, has publicly known security flaws. [SEC-004](technical.md#sec-004)
- mongodb 2.1.18, a library the system depends on, has publicly known security flaws. [SEC-005](technical.md#sec-005)
- swig 1.4.2, a library the system depends on, has publicly known security flaws. [SEC-006](technical.md#sec-006)

**Recommendation.** Recommended path: refactor — Modernize gradually behind the same interfaces (strangler pattern), starting with the hotspots. The system is built on Express.

## What the system does

Capabilities found in the code. The names come from the code: confirm them with the people who use the system.

| Capability | Description | Where |
|---|---|---|
| Benefits | 4 entry points  | `app/routes/index.js:55`, `app/routes/index.js:56` |
| Signup | 2 entry points  | `app/routes/index.js:37`, `app/routes/index.js:38` |
| Profile | 2 entry points  | `app/routes/index.js:47`, `app/routes/index.js:48` |
| Contributions | 2 entry points  | `app/routes/index.js:51`, `app/routes/index.js:52` |
| Memos | 2 entry points  | `app/routes/index.js:66`, `app/routes/index.js:67` |
| Tutorial | 2 entry points  | `app/routes/tutorial.js:8`, `app/routes/tutorial.js:31` |
| Dashboard | 1 entry point  | `app/routes/index.js:44` |
| Allocations | 1 entry point  | `app/routes/index.js:63` |
| Learn | 1 entry point  | `app/routes/index.js:70` |
| Research | 1 entry point  | `app/routes/index.js:76` |

## Risks

Impact and probability from 1 (low) to 5 (high).

| Risk | Impact | Probability | Evidence |
|---|:---:|:---:|---|
| underscore 1.8.3, a library the system depends on, has publicly known security flaws. | 5 | 4 | [SEC-001](technical.md#sec-001) |
| Passwords or keys are written inside the code. | 4 | 4 | [SEC-002](technical.md#sec-002) |
| body-parser 1.15.1, a library the system depends on, has publicly known security flaws. | 4 | 4 | [SEC-003](technical.md#sec-003) |
| marked 0.3.5, a library the system depends on, has publicly known security flaws. | 4 | 4 | [SEC-004](technical.md#sec-004) |
| mongodb 2.1.18, a library the system depends on, has publicly known security flaws. | 4 | 4 | [SEC-005](technical.md#sec-005) |
| swig 1.4.2, a library the system depends on, has publicly known security flaws. | 4 | 4 | [SEC-006](technical.md#sec-006) |
| async 2.0.0, a tool used to build or test the system, has publicly known security flaws. | 3 | 4 | [SEC-007](technical.md#sec-007) |
| express 4.13.4, a library the system depends on, has publicly known security flaws. | 3 | 4 | [SEC-008](technical.md#sec-008) |
| grunt 1.0.3, a tool used to build or test the system, has publicly known security flaws. | 3 | 4 | [SEC-009](technical.md#sec-009) |
| A small set of files absorbs most of the changes and most of the risk. | 3 | 3 | [DEBT-001](technical.md#debt-001) |
| Nobody has changed this system in years. | 3 | 3 | [RSK-001](technical.md#rsk-001) |

| Impact ↓ / Probability → | 1 | 2 | 3 | 4 | 5 |
|---|:---:|:---:|:---:|:---:|:---:|
| **5** | 🟨 | 🟧 | 🟥 | 🟥 1 | 🟥 |
| **4** | 🟨 | 🟧 | 🟧 | 🟥 5 | 🟥 |
| **3** | 🟩 | 🟨 | 🟧 2 | 🟧 3 | 🟥 |
| **2** | 🟩 | 🟨 | 🟨 | 🟧 | 🟧 |
| **1** | 🟩 | 🟩 | 🟩 | 🟨 | 🟨 |

## Options

The seven standard modernization strategies, sized for this system. Weeks are ranges for the stated team, not commitments.

| Strategy | What it means | Cost | Risk | Weeks | |
|---|---|:---:|:---:|:---:|---|
| **retain** | Keep the system as it is and only fix what is urgent (secrets, known vulnerabilities). | S | high | 1–3 |  |
| **rehost** | Move the same application to new infrastructure (containers or cloud VMs) without changing its code. | S | medium | 2–6 |  |
| **replatform** | Upgrade runtimes and frameworks that are past end of life, keeping the architecture. | M | medium | 2–7 |  |
| **refactor** | Modernize gradually behind the same interfaces (strangler pattern), starting with the hotspots. | L | medium | 3–8 | ⭐ recommended |
| **rearchitect** | Rebuild on a new architecture, reusing the business rules found in this report. | XL | high | 5–11 |  |
| **replace** | Replace with a commercial or open-source product that covers the same capabilities. | L | high | 8–26 |  |
| **retire** | Switch the system off if its capabilities are no longer needed. | S | low | 1–4 |  |

**Assumptions behind the recommended option (refactor):**

- Team of 3 developers familiar with the stack
- Size: about 5 thousand lines of code
- Ranges are ±50% and come from size and findings, not from a detailed plan
- Tests are added before each part is moved

Based on: [DEBT-001](technical.md#debt-001)

## Roadmap

### 0 · Make it safe (1–3 weeks)

Close the urgent risks without changing behavior.

- Exposed credentials rotated and removed
- Known vulnerable libraries upgraded
- Builds run in CI

*Addresses:* [SEC-001](technical.md#sec-001) [SEC-002](technical.md#sec-002) [SEC-003](technical.md#sec-003) [SEC-004](technical.md#sec-004) [SEC-005](technical.md#sec-005) [SEC-006](technical.md#sec-006) [SEC-007](technical.md#sec-007) [SEC-008](technical.md#sec-008) [SEC-009](technical.md#sec-009) [OPS-001](technical.md#ops-001)

### 1 · Make it observable and testable (2–6 weeks)

Be able to change the system without fear.

- Characterization tests around the hotspots
- Logging and health metrics in production
- Business rules in the database cataloged

*Starts after:* 0 · Make it safe

*Addresses:* [DEBT-001](technical.md#debt-001)

### 2 · Refactor (3–8 weeks)

Modernize gradually behind the same interfaces (strangler pattern), starting with the hotspots.

- First module moved and in production
- Old and new run side by side with the same results
- Remaining modules scheduled

*Starts after:* 1 · Make it observable and testable

*Addresses:* [DEBT-001](technical.md#debt-001)

### 3 · Spread the knowledge and retire the old (2–4 weeks)

Leave a system more than one person can maintain.

- Ownership of each module shared by at least two people
- Old components switched off

*Starts after:* 2 · Refactor

*Addresses:* [RSK-001](technical.md#rsk-001)

## How reliable is this?

- 12 findings: **12 verified by tools** (manifests, git, scanners) and **0 inferred by AI** and checked against the code they cite.
- 0 AI statements were rejected because the code did not back them.
- Analysis: deterministic tools only (no AI). Full method and costs: `run.json`.

## Questions

**Is the system at risk today?**

Yes. The first items in the risk list should be handled now.

**Can we keep it as it is?**

Only for a short time: keeping it means accepting the risks above.

**How long would the recommended path take?**

About 3–8 weeks for a team of 3, plus the first two roadmap phases. These are ranges from the size of the code and the findings, not a commitment.

**What should we do first?**

Phase 0 of the roadmap: close exposed secrets and known vulnerabilities, and get builds running automatically.

**How sure are these findings?**

All 12 findings are verified by tools (manifests, git history, scanners). Each one links to its evidence.

## Glossary

| Term | Meaning |
|---|---|
| end of life | The date after which the maker of a technology stops publishing fixes, including security fixes. |
| known vulnerability | A security flaw that has been published (in OSV, CVE lists), with the affected versions. |
| rehost / replatform / refactor | Move as is / upgrade the platform underneath / restructure the code gradually. |
| verified finding | A fact produced by a deterministic tool (a manifest, git, a scanner), not by an AI model. |
| inferred finding | A conclusion an AI model drew from the evidence; it was checked against the cited code, but should be confirmed. |

