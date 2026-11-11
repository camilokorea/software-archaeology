"""Deterministic findings: facts proven by the evidence of phase 1, before any model is involved.
They are marked kind="verified" in both reports."""

from __future__ import annotations

from datetime import date

from archaeology.model import ev, finding

CRITICAL_SECRETS = {"private-key", "aws-access-key", "github-token", "stripe-key", "slack-token", "google-api-key"}
OSV_SEVERITY = {"CRITICAL": "critical", "HIGH": "high", "MODERATE": "medium", "MEDIUM": "medium", "LOW": "low"}


def _years_ago(iso: str) -> float:
    try:
        return (date.today() - date.fromisoformat(iso[:10])).days / 365.25
    except ValueError:
        return 0


def run(evidence: dict) -> list[dict]:
    out: list[dict] = []
    out += _end_of_life(evidence.get("eol", []))
    out += _vulnerabilities(evidence.get("vulnerabilities", []))
    out += _secrets(evidence.get("secrets", []))
    out += _code(evidence.get("hotspots", []), evidence.get("complexity", []))
    out += _people(evidence.get("history", {}))
    out += _testing(evidence.get("tests", {}), evidence.get("inventory", {}))
    out += _devops(evidence.get("devops", {}), evidence.get("inventory", {}))
    out += _database(evidence.get("database", {}))
    out += _legacy_platforms(evidence.get("inventory", {}))
    return out


def _end_of_life(items: list[dict]) -> list[dict]:
    out = []
    for e in items:
        eol = e["eol"]
        name = e.get("label") or e["name"]
        when = "an unpublished date" if eol is True else eol
        stopped = f"which its maker no longer supports" if eol is True else f"which its maker stopped fixing on {eol}"
        if e["is_eol"]:
            old = isinstance(eol, str) and _years_ago(eol) > 2
            out.append(finding(
                spec="dependencies", area="dependencies",
                title=f"{name} {e['version']} is past its end of life" + ("" if eol is True else f" ({eol})"),
                severity="critical" if old and e["product"] in {"dotnetfx", "angularjs", "nodejs", "python", "php", "eclipse-temurin"} else "high",
                evidence=[ev(e["file"], e["line"], None, "endoflife.date")],
                technical_impact=f"Release cycle {e['cycle']} of {e['product']} gets no security or bug fixes since {when}. "
                                 f"The newest cycle is {e['newest_cycle']}.",
                business_impact=f"Part of the system runs on {name} {e['version']}, {stopped}. "
                                "New security holes will stay open, and auditors and insurers usually flag this.",
                recommendation=f"Plan an upgrade of {name} to a supported release ({e['newest_cycle']} or another supported cycle).",
                effort="L", refs=[e["source"]], tags=["end-of-life"]))
        elif isinstance(eol, str) and 0 > _years_ago(eol) > -1:
            out.append(finding(
                spec="dependencies", area="dependencies", title=f"{name} {e['version']} reaches end of life on {eol}",
                severity="medium", evidence=[ev(e["file"], e["line"], None, "endoflife.date")],
                technical_impact=f"Release cycle {e['cycle']} of {e['product']} stops receiving fixes within a year.",
                business_impact=f"Within a year, {name} will stop getting security fixes. Upgrading now is cheaper than in a hurry later.",
                recommendation=f"Schedule the upgrade of {name} before {eol}.", effort="M", refs=[e["source"]], tags=["end-of-life"]))
    return out


def _short(name: str) -> str:
    """Maven coordinates read better as the artifact name: org.springframework:spring-web → spring-web."""
    return name.split(":")[-1]


def _vulnerabilities(items: list[dict]) -> list[dict]:
    out = []
    for v in items:
        sevs = [OSV_SEVERITY.get(str(d.get("severity") or "").upper()) for d in v.get("details", [])]
        order = ["critical", "high", "medium", "low"]
        sev = next((s for s in order if s in sevs), "medium")
        dev = v.get("scope") == "dev"
        if dev:  # build and test tools do not run in production: one level lower
            sev = order[min(order.index(sev) + 1, len(order) - 1)]
        places = v.get("declared_in") or [{"file": v["file"], "line": v["line"]}]
        summary = "; ".join(d["summary"] for d in v.get("details", [])[:2] if d.get("summary"))
        out.append(finding(
            spec="security", area="security",
            title=f"{_short(v['name'])} {v['version']} has {len(v['ids'])} known vulnerabilit{'y' if len(v['ids']) == 1 else 'ies'}"
                  + (" (development dependency)" if dev else "") + (f", declared in {len(places)} places" if len(places) > 1 else ""),
            severity=sev, evidence=[ev(p["file"], p["line"], None, "osv.dev") for p in places[:10]],
            technical_impact=f"OSV lists {', '.join(v['ids'][:6])}{'…' if len(v['ids']) > 6 else ''} for this exact version. {summary}".strip(),
            business_impact=(f"{_short(v['name'])} {v['version']}, a tool used to build or test the system, has publicly known security flaws. "
                             "It does not run in production, but it can affect developers' machines and the build."
                             if dev else f"{_short(v['name'])} {v['version']}, a library the system depends on, has publicly known security flaws. "
                             "Attackers read these lists too."),
            recommendation=f"Upgrade {v['name']} to a version without these advisories and re-test the features that use it.",
            effort="S" if len(v["ids"]) < 3 else "M", refs=[f"https://osv.dev/vulnerability/{i}" for i in v["ids"][:5]], tags=["vulnerability"]))
    return out


def _secrets(items: list[dict]) -> list[dict]:
    by_rule: dict[str, list[dict]] = {}
    for s in items:
        by_rule.setdefault(s["rule"], []).append(s)
    out = []
    for rule, hits in by_rule.items():
        out.append(finding(
            spec="security", area="security",
            title=f"{hits[0]['description']} found in {len({h['file'] for h in hits})} file(s)",
            severity="critical" if rule in CRITICAL_SECRETS else "high",
            evidence=[ev(h["file"], h["line"], h["excerpt"], h["tool"]) for h in hits[:10]],
            technical_impact="Credentials are committed to the source tree. Anyone with read access to the repository, its "
                             "history or a backup can use them.",
            business_impact="Passwords or keys are written inside the code. Whoever gets a copy of the code gets access to the "
                            "systems those keys open.",
            recommendation="Rotate these credentials now, move them to a secrets store (environment, vault), and purge them "
                           "from the git history.",
            effort="S", refs=["CWE-798", "OWASP A07:2021"], tags=["secret"]))
    return out


def _code(hot: list[dict], cx: list[dict]) -> list[dict]:
    out = []
    if hot:
        top = hot[:8]
        out.append(finding(
            spec="tech-debt", area="tech-debt", title=f"{len(top)} complex files change far more often than the rest",
            severity="medium",
            evidence=[ev(h["path"], 0, None, f"hotspot: {h['decisions']} branches, {h['commits']} commits") for h in top],
            technical_impact="These files combine high branching with frequent edits: the places where defects and merge "
                             "conflicts concentrate.",
            business_impact="A small set of files absorbs most of the changes and most of the risk. Every new feature that "
                            "touches them costs more and breaks more often.",
            recommendation="Cover these files with tests first, then split them along their responsibilities before any "
                           "larger migration.",
            effort="L", tags=["hotspot"]))
    big = [c for c in cx if c["code_lines"] >= 1500][:10]
    if big:
        out.append(finding(
            spec="tech-debt", area="tech-debt", title=f"{len(big)} source files exceed 1,500 lines of code",
            severity="low", evidence=[ev(c["path"], 0, None, f"{c['code_lines']} lines") for c in big],
            technical_impact="Very large files usually hold several responsibilities, are hard to test and to review.",
            business_impact="Some parts of the code are too big for one person to understand quickly, which slows every change.",
            recommendation="Break these files apart when they are next changed, guided by tests.", effort="M", tags=["size"]))
    return out


def _people(h: dict) -> list[dict]:
    if not h.get("available"):
        return []
    out = []
    kc = h["knowledge_concentration"]
    if h["contributors"] >= 2 and h["bus_factor"] == 1:
        lead = h["top_contributors"][0]
        out.append(finding(
            spec="people", area="people", title=f"One person made half or more of all commits ({lead['author']})",
            severity="high", evidence=[ev(e["path"], 0, None, f"{e['top_author']} wrote {int(e['top_author_share'] * 100)}%") for e in kc["examples"][:6]] or [ev(".", 0, None, "git history")],
            technical_impact=f"Bus factor 1 out of {h['contributors']} contributors over {h['commits']} commits.",
            business_impact="Most of the system's knowledge sits with one person. If that person leaves or is unavailable, "
                            "changes slow down sharply.",
            recommendation="Pair others on the hotspots, write down the key decisions, and spread code reviews.", effort="M",
            tags=["knowledge"]))
    if kc["files_owned_by_one_person"] >= 5 and kc["share_of_changed_files"] >= 0.4:
        out.append(finding(
            spec="people", area="people",
            title=f"{int(kc['share_of_changed_files'] * 100)}% of the actively changed files are known by a single person",
            severity="medium", evidence=[ev(e["path"], 0, None, f"{e['top_author']} wrote {int(e['top_author_share'] * 100)}%") for e in kc["examples"][:8]],
            technical_impact="Files where one author made at least 80% of at least three commits.",
            business_impact="Large parts of the code have only one person who really knows them.",
            recommendation="Rotate ownership of these areas and document them as part of the modernization.", effort="M",
            tags=["knowledge"]))
    if h.get("last_commit") and _years_ago(h["last_commit"]) > 2:
        out.append(finding(
            spec="risk", area="risk", title=f"No changes since {h['last_commit']}",
            severity="medium", evidence=[ev(".", 0, None, "git history")],
            technical_impact="The last commit is more than two years old; the build tools and dependencies have likely drifted.",
            business_impact="Nobody has changed this system in years. Even small fixes will first need someone to make it "
                            "build and run again.",
            recommendation="Before planning changes, prove the system still builds and runs in a clean environment.",
            effort="M", tags=["dormant"]))
    return out


def _anchor(inv: dict) -> list[dict]:
    comps = inv.get("components") or []
    manifests = [m for c in comps for m in c.get("manifests", [])][:3]
    return [ev(m, 0, None, "inventory") for m in manifests] or [ev(".", 0, None, "inventory")]


def _testing(t: dict, inv: dict) -> list[dict]:
    if not t:
        return []
    if t["test_files"] == 0:
        return [finding(
            spec="testing", area="testing", title="No automated tests were found", severity="high",
            evidence=_anchor(inv),
            technical_impact=f"0 test files for {t['source_code_lines']:,} lines of source code. Regressions can only be caught by hand.",
            business_impact="Nothing checks automatically that the system still works after a change. Every change, and "
                            "especially a migration, needs slow manual testing and still risks breaking things.",
            recommendation="Before modernizing, add characterization tests around the most used features and the hotspots.",
            effort="L", tags=["no-tests"])]
    if t["ratio"] < 0.1:
        return [finding(
            spec="testing", area="testing", title=f"Test code is only {t['ratio'] * 100:.0f}% of the source code", severity="medium",
            evidence=[ev(p, 0, None, "tests scanner") for p in t["examples"][:5]],
            technical_impact=f"{t['test_files']} test files, {t['test_code_lines']:,} test lines against {t['source_code_lines']:,} source lines.",
            business_impact="Only a small part of the system is checked automatically, so changes carry a high chance of "
                            "breaking something that nobody notices until users do.",
            recommendation="Grow tests where the code changes most (see the hotspots) before moving it.", effort="L",
            tags=["low-coverage"])]
    return []


def _devops(d: dict, inv: dict) -> list[dict]:
    if not d:
        return []
    out = []
    if not d["ci"]:
        out.append(finding(
            spec="devops", area="devops", title="No continuous integration pipeline found", severity="medium",
            evidence=_anchor(inv),
            technical_impact="No CI definition (GitHub Actions, Azure Pipelines, Jenkins, GitLab…) builds or tests the code on each change.",
            business_impact="Builds and releases depend on someone's machine and memory, which makes them slow and error-prone.",
            recommendation="Add a pipeline that builds and runs the tests on every change.", effort="S", tags=["ci"]))
    if not d["dockerfiles"] and not d["iac"]:
        out.append(finding(
            spec="devops", area="devops", title="No container or infrastructure-as-code definitions", severity="low",
            evidence=_anchor(inv),
            technical_impact="The runtime environment is not described in code, so it cannot be recreated automatically.",
            business_impact="Setting up a new server or a test environment is manual work that only a few people know how to do.",
            recommendation="Describe the runtime in a Dockerfile or IaC as a first, low-risk modernization step.",
            effort="M", tags=["environment"]))
    if not d["observability"]:
        out.append(finding(
            spec="devops", area="devops", title="No logging or monitoring library detected", severity="low",
            evidence=_anchor(inv),
            technical_impact="No known logging, tracing or metrics library is declared in the manifests or configuration.",
            business_impact="When something fails in production it is hard to know what happened or how often.",
            recommendation="Add structured logging and basic health metrics before any migration, to compare before and after.",
            effort="S", tags=["observability"]))
    return out


def _database(db: dict) -> list[dict]:
    procs = [o for o in db.get("objects", []) if o["type"] in {"PROCEDURE", "FUNCTION", "TRIGGER", "PACKAGE", "PACKAGE BODY"}]
    heavy = sorted([p for p in procs if p["logic_markers"] >= 5], key=lambda p: -p["logic_markers"])
    if not heavy:
        return []
    return [finding(
        spec="database", area="database",
        title=f"{len(heavy)} database routines contain business logic", severity="medium" if len(heavy) < 20 else "high",
        evidence=[ev(p["file"], p["line"], None, f"{p['type'].lower()} {p['name']}: {p['logic_markers']} logic statements") for p in heavy[:10]],
        technical_impact="Stored procedures, functions or triggers with branching and data changes: rules that live in the "
                         "database instead of the application, tied to one database engine.",
        business_impact="Part of how the business works is written inside the database. Changing database or rewriting the "
                        "application means finding and moving those rules without losing any.",
        recommendation="Catalog what each routine decides, cover it with tests, and decide per routine whether it stays or moves.",
        effort="L" if len(heavy) > 10 else "M", tags=["stored-procedures"])]


def _legacy_platforms(inv: dict) -> list[dict]:
    names = {f["name"]: f for f in inv.get("frameworks", [])}
    out = []
    platform = {
        "ASP.NET Web Forms": ("Web Forms has no successor in modern .NET; pages must be rebuilt (Razor, Blazor or a SPA).", "XL"),
        "WCF / ASMX web services": ("WCF server and ASMX are not available in modern .NET; services must be ported (CoreWCF, REST, gRPC).", "L"),
        "Classic ASP": ("Classic ASP (VBScript) has been unsupported for years and runs only on Windows IIS.", "XL"),
        "ColdFusion": ("ColdFusion needs a commercial runtime and a shrinking pool of developers.", "L"),
        "Struts": ("Struts 1 is end of life and Struts 2 has a long security record.", "L"),
        "CICS": ("CICS online programs depend on the mainframe transaction monitor.", "XL"),
    }
    for name, (text, effort) in platform.items():
        if name in names:
            f = names[name]
            out.append(finding(
                spec="architecture", area="architecture", title=f"Built on {name}", severity="high",
                evidence=[ev(f["file"], f["line"], None, "inventory")], technical_impact=text,
                business_impact=f"An important part of the system uses {name}, a technology that is hard to hire for and cannot "
                                "be upgraded in place. Moving off it is a project, not an update.",
                recommendation=f"Treat leaving {name} as its own track in the roadmap, screen by screen or service by service.",
                effort=effort, tags=["legacy-platform"]))
    return out
