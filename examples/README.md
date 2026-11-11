# Examples

Five public, open-source legacy applications analyzed with Software Archaeology, at pinned commits. Open the
business brief or the technical report of each; every finding links to the exact line on GitHub.

| Repository | Stack | Status | Findings | Recommended | Reports |
|---|---|---|---|---|---|
| [eShopModernizing](https://github.com/dotnet-architecture/eShopModernizing) | .NET Framework, ASP.NET MVC and Web Forms, WCF | 🔴 Red | 17 (9 critical or high) | refactor | [business](eShopModernizing/executive.md) · [technical](eShopModernizing/technical.md) |
| [carddemo](https://github.com/aws-samples/aws-mainframe-modernization-carddemo) | COBOL, CICS, JCL, VSAM | 🟠 Amber | 7 (2 critical or high) | refactor | [business](carddemo/executive.md) · [technical](carddemo/technical.md) |
| [jpetstore-6](https://github.com/mybatis/jpetstore-6) | Java, Spring, MyBatis, JSP | 🔴 Red | 6 (3 critical or high) | replatform | [business](jpetstore-6/executive.md) · [technical](jpetstore-6/technical.md) |
| [angular-phonecat](https://github.com/angular/angular-phonecat) | AngularJS 1.x | 🔴 Red | 10 (3 critical or high) | replatform | [business](angular-phonecat/executive.md) · [technical](angular-phonecat/technical.md) |
| [NodeGoat](https://github.com/OWASP/NodeGoat) | Node.js, Express, MongoDB | 🔴 Red | 12 (6 critical or high) | refactor | [business](NodeGoat/executive.md) · [technical](NodeGoat/technical.md) |

## How they were made

- Analysis with deterministic tools only (no AI): every finding here is **verified** by manifests, git history,
  scanners, [endoflife.date](https://endoflife.date) and [osv.dev](https://osv.dev). With an AI provider the specs
  add inferred findings and better capability names.
- End-of-life dates and known vulnerabilities are as of the date in each report; they change as new advisories are
  published.
- Secrets found in these repositories are shown redacted. Authors appear as "Dev 1", "Dev 2"…
- Some of these applications are deliberately insecure (NodeGoat) or archived samples; the findings describe the code,
  not the quality of the projects, which were built to teach or to demonstrate.

## Reproduce or refresh

```bash
python examples/build.py                 # clone the pinned commits (repos.json), analyze, rewrite examples/<name>/
python examples/build.py --only NodeGoat
python examples/build.py --check         # what CI runs: the verified findings must reproduce (offline)
```

## Credits and licenses

The analyzed projects belong to their authors and keep their licenses: eShopModernizing (MIT, .NET Foundation and
Microsoft), CardDemo (Apache-2.0, Amazon Web Services), JPetStore 6 (Apache-2.0, the MyBatis team), angular-phonecat
(MIT, Google and the AngularJS team), NodeGoat (Apache-2.0, OWASP). The reports quote short excerpts of their code as
evidence and link to the originals.
