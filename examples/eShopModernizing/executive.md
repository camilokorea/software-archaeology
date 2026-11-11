# eShopModernizing: modernization brief

Prepared on 2026-11-10 from the code itself. Every statement links to the technical evidence behind it.

## Status: 🔴 Red

**The system works, but it carries serious risks that should be handled before any new feature.**

- Part of the system runs on .NET Framework 4.6.1, which its maker stopped fixing on 2022-04-26. [DEP-001](technical.md#dep-001)
- Passwords or keys are written inside the code. [SEC-001](technical.md#sec-001)
- An important part of the system uses ASP.NET Web Forms, a technology that is hard to hire for and cannot be upgraded in place. [ARC-001](technical.md#arc-001)
- An important part of the system uses WCF / ASMX web services, a technology that is hard to hire for and cannot be upgraded in place. [ARC-002](technical.md#arc-002)
- Part of the system runs on Bootstrap 4.3.1, which its maker stopped fixing on 2023-01-01. [DEP-002](technical.md#dep-002)
- Newtonsoft.Json 12.0.1, a library the system depends on, has publicly known security flaws. [SEC-002](technical.md#sec-002)

**Recommendation.** Recommended path: refactor — Modernize gradually behind the same interfaces (strangler pattern), starting with the hotspots. The system is built on .NET, .NET Framework, ASP.NET Core, ASP.NET MVC, ASP.NET Web Forms.

## What the system does

Capabilities found in the code. The names come from the code: confirm them with the people who use the system.

| Capability | Description | Where |
|---|---|---|
| Catalog | 10 entry points  | `eShopLegacyMVCSolution/eShopPorted/Controllers/CatalogController.cs:61`, `eShopLegacyMVCSolution/eShopPorted/Controllers/CatalogController.cs:99` |
| Pic | 3 entry points  | `eShopLegacyMVCSolution/eShopPorted/Controllers/PicController.cs:23`, `eShopLegacyMVCSolution/src/eShopLegacyMVC/Controllers/PicController.cs:23` |
| Brands | 3 entry points  | `eShopLegacyMVCSolution/eShopPorted/Controllers/Api/BrandsController.cs:24`, `eShopLegacyMVCSolution/eShopPorted/Controllers/Api/BrandsController.cs:8` |
| Files | 1 entry point  | `eShopLegacyMVCSolution/eShopPorted/Controllers/Api/FilesController.cs:10` |
| Uploadimage | 1 entry point  | `eShopModernizedMVCSolution/src/eShopModernizedMVC/Controllers/PicController.cs:26` |
| About | 1 entry point  | `eShopLegacyWebFormsSolution/src/eShopLegacyWebForms/About.aspx` |
| Contact | 1 entry point  | `eShopLegacyWebFormsSolution/src/eShopLegacyWebForms/Contact.aspx` |
| Pic Uploader | 1 entry point  | `eShopModernizedWebFormsSolution/src/eShopModernizedWebForms/Catalog/PicUploader.asmx` |

## Risks

Impact and probability from 1 (low) to 5 (high).

| Risk | Impact | Probability | Evidence |
|---|:---:|:---:|---|
| Part of the system runs on .NET Framework 4.6.1, which its maker stopped fixing on 2022-04-26. | 5 | 4 | [DEP-001](technical.md#dep-001) |
| Passwords or keys are written inside the code. | 5 | 4 | [SEC-001](technical.md#sec-001) |
| Part of the system runs on Bootstrap 4.3.1, which its maker stopped fixing on 2023-01-01. | 4 | 4 | [DEP-002](technical.md#dep-002) |
| Newtonsoft.Json 12.0.1, a library the system depends on, has publicly known security flaws. | 4 | 4 | [SEC-002](technical.md#sec-002) |
| Newtonsoft.Json 6.0.4, a library the system depends on, has publicly known security flaws. | 4 | 4 | [SEC-003](technical.md#sec-003) |
| Passwords or keys are written inside the code. | 4 | 4 | [SEC-004](technical.md#sec-004) |
| Nothing checks automatically that the system still works after a change. | 4 | 4 | [TST-001](technical.md#tst-001) |
| An important part of the system uses ASP.NET Web Forms, a technology that is hard to hire for and cannot be upgraded in place. | 4 | 3 | [ARC-001](technical.md#arc-001) |
| An important part of the system uses WCF / ASMX web services, a technology that is hard to hire for and cannot be upgraded in place. | 4 | 3 | [ARC-002](technical.md#arc-002) |
| A small set of files absorbs most of the changes and most of the risk. | 3 | 3 | [DEBT-001](technical.md#debt-001) |
| Builds and releases depend on someone's machine and memory, which makes them slow and error-prone. | 3 | 3 | [OPS-001](technical.md#ops-001) |
| Nobody has changed this system in years. | 3 | 3 | [RSK-001](technical.md#rsk-001) |

| Impact ↓ / Probability → | 1 | 2 | 3 | 4 | 5 |
|---|:---:|:---:|:---:|:---:|:---:|
| **5** | 🟨 | 🟧 | 🟥 | 🟥 2 | 🟥 |
| **4** | 🟨 | 🟧 | 🟧 2 | 🟥 5 | 🟥 |
| **3** | 🟩 | 🟨 | 🟧 3 | 🟧 | 🟥 |
| **2** | 🟩 | 🟨 | 🟨 | 🟧 | 🟧 |
| **1** | 🟩 | 🟩 | 🟩 | 🟨 | 🟨 |

## Options

The seven standard modernization strategies, sized for this system. Weeks are ranges for the stated team, not commitments.

| Strategy | What it means | Cost | Risk | Weeks | |
|---|---|:---:|:---:|:---:|---|
| **retain** | Keep the system as it is and only fix what is urgent (secrets, known vulnerabilities). | S | high | 1–3 |  |
| **rehost** | Move the same application to new infrastructure (containers or cloud VMs) without changing its code. | M | medium | 7–17 |  |
| **replatform** | Upgrade runtimes and frameworks that are past end of life, keeping the architecture. | L | medium | 43–100 |  |
| **refactor** | Modernize gradually behind the same interfaces (strangler pattern), starting with the hotspots. | L | medium | 105–237 | ⭐ recommended |
| **rearchitect** | Rebuild on a new architecture, reusing the business rules found in this report. | XL | high | 263–578 |  |
| **replace** | Replace with a commercial or open-source product that covers the same capabilities. | L | high | 8–26 |  |
| **retire** | Switch the system off if its capabilities are no longer needed. | S | low | 1–4 |  |

**Assumptions behind the recommended option (refactor):**

- Team of 3 developers familiar with the stack
- Size: about 263 thousand lines of code
- Ranges are ±50% and come from size and findings, not from a detailed plan
- Tests are added before each part is moved

Based on: [ARC-001](technical.md#arc-001) [ARC-002](technical.md#arc-002) [TST-001](technical.md#tst-001) [DEBT-001](technical.md#debt-001) [DEBT-002](technical.md#debt-002)

## Roadmap

### 0 · Make it safe (1–3 weeks)

Close the urgent risks without changing behavior.

- Exposed credentials rotated and removed
- Known vulnerable libraries upgraded
- Builds run in CI

*Addresses:* [SEC-001](technical.md#sec-001) [SEC-002](technical.md#sec-002) [SEC-003](technical.md#sec-003) [SEC-004](technical.md#sec-004) [SEC-005](technical.md#sec-005) [SEC-006](technical.md#sec-006) [SEC-007](technical.md#sec-007) [SEC-008](technical.md#sec-008) [OPS-001](technical.md#ops-001)

### 1 · Make it observable and testable (2–6 weeks)

Be able to change the system without fear.

- Characterization tests around the hotspots
- Logging and health metrics in production
- Business rules in the database cataloged

*Starts after:* 0 · Make it safe

*Addresses:* [TST-001](technical.md#tst-001) [DEBT-001](technical.md#debt-001) [DEBT-002](technical.md#debt-002)

### 2 · Refactor (105–237 weeks)

Modernize gradually behind the same interfaces (strangler pattern), starting with the hotspots.

- First module moved and in production
- Old and new run side by side with the same results
- Remaining modules scheduled

*Starts after:* 1 · Make it observable and testable

*Addresses:* [ARC-001](technical.md#arc-001) [ARC-002](technical.md#arc-002) [TST-001](technical.md#tst-001) [DEBT-001](technical.md#debt-001) [DEBT-002](technical.md#debt-002) [DEP-001](technical.md#dep-001) [DEP-002](technical.md#dep-002)

### 3 · Spread the knowledge and retire the old (2–4 weeks)

Leave a system more than one person can maintain.

- Ownership of each module shared by at least two people
- Old components switched off

*Starts after:* 2 · Refactor

*Addresses:* [RSK-001](technical.md#rsk-001)

## How reliable is this?

- 17 findings: **17 verified by tools** (manifests, git, scanners) and **0 inferred by AI** and checked against the code they cite.
- 0 AI statements were rejected because the code did not back them.
- Analysis: deterministic tools only (no AI). Full method and costs: `run.json`.

## Questions

**Is the system at risk today?**

Yes. The first items in the risk list should be handled now.

**Can we keep it as it is?**

Only for a short time: keeping it means accepting the risks above.

**How long would the recommended path take?**

About 105–237 weeks for a team of 3, plus the first two roadmap phases. These are ranges from the size of the code and the findings, not a commitment.

**What should we do first?**

Phase 0 of the roadmap: close exposed secrets and known vulnerabilities, and get builds running automatically.

**How sure are these findings?**

All 17 findings are verified by tools (manifests, git history, scanners). Each one links to its evidence.

## Glossary

| Term | Meaning |
|---|---|
| end of life | The date after which the maker of a technology stops publishing fixes, including security fixes. |
| known vulnerability | A security flaw that has been published (in OSV, CVE lists), with the affected versions. |
| continuous integration | A service that builds and tests the system automatically on every change. |
| rehost / replatform / refactor | Move as is / upgrade the platform underneath / restructure the code gradually. |
| verified finding | A fact produced by a deterministic tool (a manifest, git, a scanner), not by an AI model. |
| inferred finding | A conclusion an AI model drew from the evidence; it was checked against the cited code, but should be confirmed. |

