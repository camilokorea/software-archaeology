"""Phase 3: the business view. A deterministic synthesis always exists (rules written out below); when a model is
configured it may rewrite it, but every statement still has to cite validated findings or it is dropped."""

from __future__ import annotations

import json
import re
from collections import Counter

from archaeology import model, util, validate
from archaeology.llm import Provider, ProviderError, Usage
from archaeology.paths import PROMPTS

PROBABILITY = {"security": 4, "dependencies": 4, "testing": 4, "people": 3, "tech-debt": 3, "devops": 3, "database": 3,
               "architecture": 3, "risk": 3, "api": 3, "inventory": 2, "capabilities": 2}
IMPACT = {"critical": 5, "high": 4, "medium": 3, "low": 2, "info": 1}
TEAM = 3  # developers assumed by the estimates


def _first_sentence(text: str) -> str:
    m = re.match(r"(.+?[.!?])(\s|$)", text.strip())
    return (m.group(1) if m else text).strip()


def status(findings: list[dict]) -> str:
    sev = Counter(f["severity"] for f in findings)
    if sev["critical"] or sev["high"] >= 3:
        return "red"
    if sev["high"] or sev["medium"] >= 5:
        return "amber"
    return "green"


GENERIC = {"api", "v1", "v2", "v3", "actions", "action", "app", "index", "default", "src", "main", "webapp", "web-inf", "jsp",
           "pages", "views", "view", "includes", "include", "common", "shared", "static", "public", "new", "edit", "update",
           "delete", "remove", "add", "list", "show", "form", "home", "page", "get", "post", "put", "detail", "details",
           "create", "save", "search", "admin", "login", "logout", "error", "test", "resources", "content", "scripts", "root", "controller", "controllers", "handler", "service"}


def _name(text: str) -> str | None:
    words = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])", re.sub(r"(Controller|ActionBean|Action|Servlet|Resource|Page|Form|Service|Handler)$", "", text))
    words = [w for w in words if w.lower() not in GENERIC]
    return " ".join(w.capitalize() for w in words[:3]) or None


def capabilities(evidence: dict) -> list[dict]:
    """Business capabilities guessed from server entry points (heuristic, labeled so). Mainframe transactions and
    anything without a readable name are left for the AI analysis or a person, rather than guessed."""
    groups: dict[str, dict] = {}
    for e in evidence.get("api", []):
        if e["side"] != "server" or e["framework"] in {"CICS"}:
            continue
        candidates = []
        if e["path"] and not e["path"].startswith("/" + e["file"]):
            candidates = [seg for seg in re.split(r"[/.?&=]", e["path"]) if seg and not seg.startswith(("{", ":", "<", "("))]
        stem = re.sub(r"\.\w+$", "", e["file"].rsplit("/", 1)[-1])
        if re.match(r"(?i)(include|_|partial|layout|header|footer|top|bottom)", stem) or re.search(r"/(common|includes?|partials?|shared|layouts?)/", e["file"], re.I):
            continue  # page fragments are not capabilities
        name = next((n for n in (_name(c) for c in candidates) if n), None) or _name(stem)
        if not name or len(name) < 3:
            continue
        key = re.sub(r"(?<=[a-z])s$", "", name.lower())  # "Products" and "Product" are one capability
        g = groups.setdefault(key, {"name": name, "files": Counter(), "count": 0})
        g["files"][f"{e['file']}:{e['line']}" if e["line"] else e["file"]] += 1
        g["count"] += 1
    out = []
    for g in sorted(groups.values(), key=lambda g: -g["count"])[:12]:
        out.append({"name": g["name"], "description": f"{g['count']} entry point{'s' if g['count'] != 1 else ''}",
                    "evidence": [f for f, _ in g["files"].most_common(3)], "findings": []})
    return out


def _weeks(lo: float, hi: float) -> list[int]:
    return [max(1, round(lo)), max(1, round(hi))]


def options(findings: list[dict], evidence: dict) -> list[dict]:
    inv = evidence.get("inventory", {})
    kloc = max(1, inv.get("code_lines", 0) / 1000)
    by_tag = lambda tag: [f["id"] for f in findings if tag in f.get("tags", [])]  # noqa: E731
    eol, platform, dormant = by_tag("end-of-life"), by_tag("legacy-platform"), by_tag("dormant")
    debt = [f["id"] for f in findings if f["area"] in {"tech-debt", "testing", "database"}]
    serious = [f["id"] for f in findings if f["severity"] in {"critical", "high"}]
    base = [f"Team of {TEAM} developers familiar with the stack", f"Size: about {kloc:,.0f} thousand lines of code",
            "Ranges are ±50% and come from size and findings, not from a detailed plan"]
    opts = [
        {"strategy": "retain", "summary": "Keep the system as it is and only fix what is urgent (secrets, known vulnerabilities).",
         "cost": "S", "risk": "high" if serious else "low", "weeks": _weeks(1, 3), "assumptions": base[:1] + ["Risk keeps growing while the platform ages"],
         "findings": serious[:5]},
        {"strategy": "rehost", "summary": "Move the same application to new infrastructure (containers or cloud VMs) without changing its code.",
         "cost": "S" if kloc < 50 else "M", "risk": "medium", "weeks": _weeks(2 + kloc / 50, 6 + kloc / 25),
         "assumptions": base + ["Runtime can be containerized or installed on new servers"], "findings": by_tag("environment")},
        {"strategy": "replatform", "summary": "Upgrade runtimes and frameworks that are past end of life, keeping the architecture.",
         "cost": "M" if kloc < 100 else "L", "risk": "medium", "weeks": _weeks(kloc * 0.15 + len(eol) * 2, kloc * 0.35 + len(eol) * 4),
         "assumptions": base + ["Framework upgrades have a documented path"], "findings": eol},
        {"strategy": "refactor", "summary": "Modernize gradually behind the same interfaces (strangler pattern), starting with the hotspots.",
         "cost": "L", "risk": "medium", "weeks": _weeks(kloc * 0.4, kloc * 0.9), "assumptions": base + ["Tests are added before each part is moved"],
         "findings": (platform + debt)[:10]},
        {"strategy": "rearchitect", "summary": "Rebuild on a new architecture, reusing the business rules found in this report.",
         "cost": "XL", "risk": "high", "weeks": _weeks(kloc * 1.0, kloc * 2.2), "assumptions": base + ["Requirements are recovered from the code and validated with users"],
         "findings": (platform + serious)[:10]},
        {"strategy": "replace", "summary": "Replace with a commercial or open-source product that covers the same capabilities.",
         "cost": "L", "risk": "high", "weeks": _weeks(8, 26), "assumptions": ["A product exists for most capabilities", "Data migration and process changes are the bulk of the work"],
         "findings": []},
        {"strategy": "retire", "summary": "Switch the system off if its capabilities are no longer needed.",
         "cost": "S", "risk": "low" if dormant else "high", "weeks": _weeks(1, 4), "assumptions": ["The business confirms nobody depends on it"],
         "findings": dormant},
    ]
    # Keep the ranges consistent: a deeper change never costs less than a shallower one.
    floor = [0, 0]
    for o in opts[1:5]:
        o["weeks"] = [max(o["weeks"][0], floor[0]), max(o["weeks"][1], floor[1], o["weeks"][0] + 1)]
        floor = [o["weeks"][0] + (1 if o["strategy"] != "rehost" else 0), o["weeks"][1] + 1]
    if platform:
        pick = "refactor"
    elif eol:
        pick = "replatform"
    elif serious:
        pick = "refactor" if debt else "retain"
    else:
        pick = "retain"
    for o in opts:
        o["recommended"] = o["strategy"] == pick
    return opts


def roadmap(findings: list[dict], opts: list[dict]) -> list[dict]:
    pick = next(o for o in opts if o["recommended"])
    area = lambda *a: [f["id"] for f in findings if f["area"] in a]  # noqa: E731
    secure = [f["id"] for f in findings if f["area"] == "security" or "secret" in f.get("tags", [])]
    phases = [
        {"phase": "0 · Make it safe", "goal": "Close the urgent risks without changing behavior.", "weeks": [1, 3],
         "milestones": ["Exposed credentials rotated and removed", "Known vulnerable libraries upgraded", "Builds run in CI"],
         "depends_on": [], "findings": secure + area("devops")},
        {"phase": "1 · Make it observable and testable", "goal": "Be able to change the system without fear.", "weeks": [2, 6],
         "milestones": ["Characterization tests around the hotspots", "Logging and health metrics in production", "Business rules in the database cataloged"],
         "depends_on": ["0 · Make it safe"], "findings": area("testing", "tech-debt", "database")},
        {"phase": f"2 · {pick['strategy'].capitalize()}", "goal": pick["summary"], "weeks": pick["weeks"],
         "milestones": ["First module moved and in production", "Old and new run side by side with the same results", "Remaining modules scheduled"],
         "depends_on": ["1 · Make it observable and testable"], "findings": pick["findings"] + area("architecture", "dependencies")},
        {"phase": "3 · Spread the knowledge and retire the old", "goal": "Leave a system more than one person can maintain.", "weeks": [2, 4],
         "milestones": ["Ownership of each module shared by at least two people", "Old components switched off"],
         "depends_on": [f"2 · {pick['strategy'].capitalize()}"], "findings": area("people", "risk")},
    ]
    for p in phases:
        p["findings"] = list(dict.fromkeys(p["findings"]))[:12]
    return phases


GLOSSARY = {
    "end of life": "The date after which the maker of a technology stops publishing fixes, including security fixes.",
    "known vulnerability": "A security flaw that has been published (in OSV, CVE lists), with the affected versions.",
    "hotspot": "A file that is both complicated and changed often: where defects and delays concentrate.",
    "bus factor": "How many people would have to leave before the team could no longer maintain the system.",
    "technical debt": "Shortcuts in the code that make every future change slower or riskier until they are paid back.",
    "stored procedure": "A program stored and run inside the database; it often holds business rules.",
    "continuous integration": "A service that builds and tests the system automatically on every change.",
    "characterization test": "A test that records what the system does today, so a rewrite can prove it still does the same.",
    "strangler pattern": "Replacing a system piece by piece while the old and new versions run side by side.",
    "rehost / replatform / refactor": "Move as is / upgrade the platform underneath / restructure the code gradually.",
    "verified finding": "A fact produced by a deterministic tool (a manifest, git, a scanner), not by an AI model.",
    "inferred finding": "A conclusion an AI model drew from the evidence; it was checked against the cited code, but should be confirmed.",
}


def deterministic(findings: list[dict], evidence: dict) -> dict:
    st = status(findings)
    top = [f for f in findings if f["severity"] in {"critical", "high", "medium"}][:6]
    inv = evidence.get("inventory", {})
    opts = options(findings, evidence)
    pick = next(o for o in opts if o["recommended"])
    tooling = {"JUnit", "Bootstrap"}  # libraries, not platforms the system is "built on"
    fw = ", ".join([x["name"] for x in inv.get("frameworks", []) if x["name"] not in tooling][:5]) or "its current stack"
    headline = {
        "red": f"The system works, but it carries serious risks that should be handled before any new feature.",
        "amber": f"The system is maintainable today, with risks that will grow if nothing is done.",
        "green": f"No serious risks were found; the system can keep evolving as it is.",
    }[st]
    risks = [{"statement": _first_sentence(f["business_impact"]), "impact": IMPACT[f["severity"]],
              "probability": PROBABILITY.get(f["area"], 3) - (1 if f["confidence"] == "low" else 0), "findings": [f["id"]]}
             for f in findings if f["severity"] in {"critical", "high", "medium"}][:12]
    text = " ".join(f["title"].lower() for f in findings)
    glossary = [{"term": t, "definition": d} for t, d in GLOSSARY.items()
                if t.split(" /")[0].split()[0] in text or t in {"verified finding", "inferred finding", "rehost / replatform / refactor"}]
    verified = sum(1 for f in findings if f["kind"] == "verified")
    faq = [
        {"question": "Is the system at risk today?",
         "answer": {"red": "Yes. The first items in the risk list should be handled now.", "amber": "Not immediately, but the risks listed grow every month.",
                    "green": "No serious risk was found."}[st]},
        {"question": "Can we keep it as it is?",
         "answer": "Only for a short time: keeping it means accepting the risks above." if st != "green" else "Yes, with normal maintenance."},
        {"question": "How long would the recommended path take?",
         "answer": f"About {pick['weeks'][0]}–{pick['weeks'][1]} weeks for a team of {TEAM}, plus the first two roadmap phases. "
                   "These are ranges from the size of the code and the findings, not a commitment."},
        {"question": "What should we do first?", "answer": "Phase 0 of the roadmap: close exposed secrets and known vulnerabilities, and get builds running automatically."},
        {"question": "How sure are these findings?",
         "answer": (f"All {verified} findings are verified by tools (manifests, git history, scanners). " if verified == len(findings) else
                    f"{verified} of {len(findings)} findings are verified by tools; the other {len(findings) - verified} are AI inferences that were checked against the code they cite. ")
                   + "Each one links to its evidence."},
    ]
    return {
        "executive_summary": {
            "status": st, "headline": headline,
            "points": [{"text": _first_sentence(f["business_impact"]), "findings": [f["id"]]} for f in top],
            "recommendation": f"Recommended path: {pick['strategy']} — {pick['summary']} The system is built on {fw}.",
        },
        "capabilities": capabilities(evidence),
        "risks": risks,
        "options": opts,
        "roadmap": roadmap(findings, opts),
        "glossary": glossary,
        "faq": faq,
    }


def with_model(findings: list[dict], evidence: dict, draft: dict, provider: Provider, cache_dir, log) -> tuple[dict | None, Usage, list[str]]:
    compact = [{k: f[k] for k in ("id", "area", "title", "severity", "kind", "confidence", "business_impact", "technical_impact", "effort", "recommendation")}
               for f in findings]
    inv = evidence.get("inventory", {})
    user = (
        "# Validated findings\n" + json.dumps(compact, ensure_ascii=False) +
        "\n\n# Inventory summary\n" + json.dumps({k: inv.get(k) for k in ("code_lines", "size_class", "languages", "frameworks", "components")}, ensure_ascii=False, default=str)[:20000] +
        "\n\n# Capabilities seen in entry points (heuristic)\n" + json.dumps(draft["capabilities"], ensure_ascii=False) +
        "\n\n# Deterministic draft (improve it; keep its estimates unless the findings justify a change, and say why in assumptions)\n" +
        json.dumps(draft, ensure_ascii=False)
    )
    system = (PROMPTS / "synthesis-system.md").read_text(encoding="utf-8")
    key = util.sha(system + user + str(provider.model))
    cached = util.load_json(cache_dir / f"synthesis-{key}.json")
    if cached:
        log("  · synthesis: reused from cache")
        data, usage = cached["data"], Usage()
    else:
        log(f"  · synthesis: asking {provider.name}/{provider.model}")
        try:
            data, usage = provider.complete(system, user, model.schema("synthesis"), "synthesis")
        except ProviderError as e:
            return None, Usage(), [str(e)]
        util.dump(cache_dir / f"synthesis-{key}.json", {"data": data})
    data, problems = validate.synthesis(data, {f["id"] for f in findings})
    if model.schema_errors("synthesis", data):
        return None, usage, ["synthesis: the model's answer did not match the schema; using the deterministic synthesis"] + problems
    return data, usage, problems
