"""What the repository is made of: languages, size, frameworks, components."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from collections import Counter, defaultdict

from archaeology.evidence.index import Index

MANIFESTS = {
    "package.json": "npm", "bower.json": "bower", "packages.config": "NuGet", "pom.xml": "Maven", "build.gradle": "Gradle",
    "build.gradle.kts": "Gradle", "requirements.txt": "PyPI", "pyproject.toml": "PyPI", "setup.py": "PyPI",
    "composer.json": "Packagist", "gemfile": "RubyGems", "go.mod": "Go", "cargo.toml": "Cargo",
}


def frameworks(idx: Index) -> list[dict]:
    """Frameworks recognized from manifests and tell-tale files, each with the file that proves it."""
    found: dict[str, dict] = {}

    def add(name: str, file: str, line: int = 0, detail: str | None = None):
        found.setdefault(name, {"name": name, "file": file, "line": line, "detail": detail})

    for f in idx.by_name("package.json", "bower.json"):
        try:
            data = json.loads(idx.text(f.path))
        except ValueError:
            continue
        deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
        for dep, label in [("angular", "AngularJS 1.x"), ("@angular/core", "Angular"), ("react", "React"), ("vue", "Vue"),
                           ("jquery", "jQuery"), ("express", "Express"), ("backbone", "Backbone"), ("ember-source", "Ember"),
                           ("knockout", "Knockout"), ("next", "Next.js"), ("@nestjs/core", "NestJS"), ("bootstrap", "Bootstrap")]:
            if dep in deps:
                add(label, f.path, _line(idx.text(f.path), f'"{dep}"'), str(deps[dep]))
    for f in idx.by_suffix(".csproj", ".vbproj"):
        text = idx.text(f.path)
        if m := re.search(r"<TargetFrameworkVersion>v([\d.]+)<", text):
            add(".NET Framework", f.path, _line(text, m.group(0)), m.group(1))
        if m := re.search(r"<TargetFrameworks?>([^<]+)<", text):
            add(".NET", f.path, _line(text, m.group(0)), m.group(1))
        if "Microsoft.NET.Sdk.Web" in text or "System.Web.Mvc" in text:
            add("ASP.NET" + (" Core" if "Sdk.Web" in text else " MVC"), f.path, _line(text, "Sdk.Web" if "Sdk.Web" in text else "System.Web.Mvc"))
        if "EntityFramework" in text:
            add("Entity Framework", f.path, _line(text, "EntityFramework"))
    if any(f.path.lower().endswith((".aspx", ".ascx")) for f in idx.files):
        add("ASP.NET Web Forms", next(f.path for f in idx.files if f.path.lower().endswith((".aspx", ".ascx"))))
    if any(f.path.lower().endswith((".svc", ".asmx")) for f in idx.files):
        add("WCF / ASMX web services", next(f.path for f in idx.files if f.path.lower().endswith((".svc", ".asmx"))))
    for f in idx.by_name("pom.xml", "build.gradle", "build.gradle.kts"):
        text = idx.text(f.path)
        for marker, label in [("spring-boot", "Spring Boot"), ("springframework", "Spring"), ("struts", "Struts"),
                              ("stripes", "Stripes"), ("hibernate", "Hibernate"), ("mybatis", "MyBatis"), ("javax.ejb", "Java EE / EJB"),
                              ("jakarta", "Jakarta EE"), ("junit", "JUnit")]:
            if marker in text:
                add(label, f.path, _line(text, marker))
    for f in idx.by_name("requirements.txt", "pyproject.toml"):
        text = idx.text(f.path).lower()
        for marker, label in [("django", "Django"), ("flask", "Flask"), ("fastapi", "FastAPI")]:
            if marker in text:
                add(label, f.path, _line(text, marker))
    cobol = [f for f in idx.files if f.language == "COBOL"]
    if cobol:
        add("COBOL", cobol[0].path)
        cics = next((f for f in cobol if "EXEC CICS" in idx.text(f.path)), None)
        if cics:
            add("CICS", cics.path, _line(idx.text(cics.path), "EXEC CICS"))
    if idx.by_suffix(".jcl"):
        add("JCL batch", idx.by_suffix(".jcl")[0].path)
    if idx.by_suffix(".cfm", ".cfc"):
        add("ColdFusion", idx.by_suffix(".cfm", ".cfc")[0].path)
    if idx.by_suffix(".asp"):
        add("Classic ASP", idx.by_suffix(".asp")[0].path)
    return sorted(found.values(), key=lambda x: x["name"])


def _line(text: str, needle: str) -> int:
    i = text.find(needle)
    return text.count("\n", 0, i) + 1 if i >= 0 else 0


def components(idx: Index) -> list[dict]:
    """A component per directory that holds a build manifest: the containers of the C4 diagram."""
    comps: dict[str, dict] = {}
    for f in idx.files:
        name = f.path.rsplit("/", 1)[-1].lower()
        kind = MANIFESTS.get(name) or ("NuGet" if name.endswith((".csproj", ".vbproj", ".fsproj")) else None)
        if not kind:
            continue
        folder = f.path.rsplit("/", 1)[0] if "/" in f.path else "."
        comp = comps.setdefault(folder, {"path": folder, "manifests": [], "ecosystems": set(), "languages": Counter()})
        comp["manifests"].append(f.path)
        comp["ecosystems"].add(kind)
    if not comps:
        comps["."] = {"path": ".", "manifests": [], "ecosystems": set(), "languages": Counter()}
    folders = sorted(comps, key=len, reverse=True)
    for f in idx.files:
        if not f.language:
            continue
        owner = next((c for c in folders if c == "." or f.path.startswith(c + "/")), None)
        if owner:
            comps[owner]["languages"][f.language] += f.code_lines
    out = []
    for c in comps.values():
        langs = [l for l, _ in c["languages"].most_common(4)]
        out.append({"path": c["path"], "manifests": c["manifests"], "ecosystems": sorted(c["ecosystems"]),
                    "languages": langs, "kind": _kind(c, idx)})
    return sorted(out, key=lambda c: c["path"])


def _kind(comp: dict, idx: Index) -> str:
    path = comp["path"].lower()
    langs = set(comp["languages"])
    if "test" in path:
        return "tests"
    if langs & {"ASP.NET Web Forms", "Razor", "JSP", "JSF", "ColdFusion", "Classic ASP"}:
        return "web application (server-rendered)"
    if "npm" in comp["ecosystems"] or "bower" in comp["ecosystems"]:
        return "frontend or Node.js application"
    if langs & {"COBOL", "JCL"}:
        return "mainframe programs"
    if langs == {"SQL"} or "sql" in path or "database" in path:
        return "database scripts"
    return "application or library"


def summarize(idx: Index) -> dict:
    by_lang: dict[str, dict] = defaultdict(lambda: {"files": 0, "code_lines": 0})
    for f in idx.files:
        key = f.language or "Other"
        by_lang[key]["files"] += 1
        by_lang[key]["code_lines"] += f.code_lines
    tokei = _tokei(idx)
    total_code = sum(v["code_lines"] for k, v in by_lang.items() if k != "Other")
    top_dirs = Counter(f.path.split("/")[0] if "/" in f.path else "." for f in idx.files)
    return {
        "files": len(idx.files),
        "code_lines": total_code,
        "size_class": "small" if total_code < 20_000 else "medium" if total_code < 150_000 else "large" if total_code < 1_000_000 else "very large",
        "languages": sorted(({"language": k, **v} for k, v in by_lang.items()), key=lambda x: -x["code_lines"]),
        "top_directories": [{"path": p, "files": n} for p, n in top_dirs.most_common(15)],
        "frameworks": frameworks(idx),
        "components": components(idx),
        "largest_files": [{"path": f.path, "code_lines": f.code_lines, "language": f.language}
                          for f in sorted(idx.source(), key=lambda f: -f.code_lines)[:15]],
        "tokei": tokei,
    }


def _tokei(idx: Index) -> dict | None:
    """Cross-check with tokei when it is installed (the Docker image has it)."""
    if not shutil.which("tokei"):
        return None
    try:
        out = subprocess.run(["tokei", "--output", "json", str(idx.repo)], capture_output=True, text=True, timeout=120)
        data = json.loads(out.stdout)
        return {k: {"code": v.get("code"), "files": len(v.get("reports", []))} for k, v in data.items() if k != "Total"}
    except Exception:  # noqa: BLE001 - optional cross-check only
        return None
