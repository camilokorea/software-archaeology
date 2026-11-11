"""Optional lookups that need the network: end of life (endoflife.date) and known vulnerabilities (osv.dev).
Results are cached on disk, so repeated runs and offline runs work. Only package names and versions leave the
machine, never code."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

USER_AGENT = "software-archaeology/2.0 (+https://github.com/camilokorea/software-archaeology)"

# Package name (lowercase) → endoflife.date product. Runtimes use their own product names directly.
EOL_PACKAGES = {
    ("npm", "angular"): "angularjs", ("npm", "@angular/core"): "angular", ("npm", "react"): "react", ("npm", "vue"): "vue",
    ("npm", "jquery"): "jquery", ("npm", "bootstrap"): "bootstrap", ("npm", "electron"): "electron",
    ("bower", "angular"): "angularjs", ("bower", "jquery"): "jquery", ("bower", "bootstrap"): "bootstrap",
    ("nuget", "bootstrap"): "bootstrap", ("nuget", "jquery"): "jquery",
    ("maven", "org.springframework.boot:spring-boot"): "spring-boot",
    ("maven", "org.springframework:spring-core"): "spring-framework", ("maven", "org.springframework:spring-webmvc"): "spring-framework",
    ("maven", "org.springframework:spring-context"): "spring-framework", ("pypi", "django"): "django",
    ("packagist", "laravel/framework"): "laravel", ("rubygems", "rails"): "rails",
}
LABELS = {"dotnetfx": ".NET Framework", "dotnet": ".NET", "angularjs": "AngularJS", "angular": "Angular", "nodejs": "Node.js",
          "eclipse-temurin": "Java", "python": "Python", "php": "PHP", "go": "Go", "ruby": "Ruby", "react": "React", "vue": "Vue",
          "jquery": "jQuery", "bootstrap": "Bootstrap", "django": "Django", "spring-boot": "Spring Boot",
          "spring-framework": "Spring Framework", "laravel": "Laravel", "rails": "Ruby on Rails", "electron": "Electron"}
RUNTIME_PRODUCTS = {"dotnet": "dotnet", "dotnetfx": "dotnetfx", "nodejs": "nodejs", "python": "python", "php": "php",
                    "java": "eclipse-temurin", "go": "go", "ruby": "ruby"}
OSV_ECOSYSTEM = {"npm": "npm", "NuGet": "NuGet", "Maven": "Maven", "PyPI": "PyPI", "Packagist": "Packagist",
                 "RubyGems": "RubyGems", "Go": "Go"}


class Net:
    def __init__(self, cache_dir: Path, enabled: bool, timeout: int):
        self.cache = cache_dir
        self.enabled = enabled
        self.timeout = timeout
        self.errors: list[str] = []

    def get_json(self, url: str, body: dict | None = None):
        key = re.sub(r"[^A-Za-z0-9]+", "_", url)[-120:] + (f"_{abs(hash(json.dumps(body, sort_keys=True)))}" if body else "")
        path = self.cache / f"{key}.json"
        if path.exists():
            return json.loads(path.read_text())
        if not self.enabled:
            return None
        req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None,
                                     headers={"User-Agent": USER_AGENT, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                data = json.loads(r.read())
        except (urllib.error.URLError, TimeoutError, ValueError) as e:
            self.errors.append(f"{url}: {e}")
            return None
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data))
        return data


def _cycle_for(version: str, cycles: list[dict]) -> dict | None:
    parts = version.split(".")
    for n in (2, 1, 3):
        candidate = ".".join(parts[:n])
        for c in cycles:
            if str(c.get("cycle")) == candidate:
                return c
    return None


def end_of_life(deps: dict, net: Net) -> list[dict]:
    targets = []
    for r in deps["runtimes"]:
        if product := RUNTIME_PRODUCTS.get(r["product"]):
            targets.append({"product": product, "name": r["product"], "version": r["version"], "file": r["file"], "line": r["line"]})
    for d in deps["dependencies"]:
        product = EOL_PACKAGES.get((d["ecosystem"].lower(), d["name"].lower()))
        if product and d["version"]:
            targets.append({"product": product, "name": d["name"], "version": d["version"], "file": d["file"], "line": d["line"]})
    # One entry per technology and version: Spring's several artifacts are one Spring Framework.
    unique: dict[tuple, dict] = {}
    for t in targets:
        unique.setdefault((t["product"], t["version"]), t)
    out = []
    for t in unique.values():
        cycles = net.get_json(f"https://endoflife.date/api/{t['product']}.json")
        if not isinstance(cycles, list):
            continue
        cycle = _cycle_for(t["version"], cycles)
        if not cycle:
            continue
        eol = cycle.get("eol")
        is_eol = eol is True or (isinstance(eol, str) and eol <= date.today().isoformat())
        out.append({**t, "label": LABELS.get(t["product"], t["name"]), "cycle": str(cycle.get("cycle")), "eol": eol, "is_eol": bool(is_eol),
                    "latest_in_cycle": cycle.get("latest"), "newest_cycle": str(cycles[0].get("cycle")) if cycles else None,
                    "source": f"https://endoflife.date/{t['product']}"})
    return out


def vulnerabilities(deps: dict, net: Net, limit: int = 60) -> list[dict]:
    queries, owners = [], []
    for d in deps["dependencies"]:
        eco = OSV_ECOSYSTEM.get(d["ecosystem"])
        if eco and d["version"]:
            queries.append({"package": {"name": d["name"], "ecosystem": eco}, "version": d["version"]})
            owners.append(d)
    out = []
    for start in range(0, len(queries), 500):
        batch = net.get_json("https://api.osv.dev/v1/querybatch", {"queries": queries[start:start + 500]})
        if not batch:
            continue
        for d, res in zip(owners[start:start + 500], batch.get("results", [])):
            ids = [v["id"] for v in res.get("vulns", [])]
            if ids:
                out.append({**{k: d[k] for k in ("ecosystem", "name", "version", "file", "line")}, "ids": ids})
    # Details (summary, severity) for the most affected packages only, to keep the run fast.
    for item in sorted(out, key=lambda x: -len(x["ids"]))[:limit]:
        details = []
        for vid in item["ids"][:5]:
            v = net.get_json(f"https://api.osv.dev/v1/vulns/{vid}")
            if v:
                sev = (v.get("database_specific") or {}).get("severity")
                details.append({"id": vid, "summary": (v.get("summary") or "")[:200], "severity": sev,
                                "aliases": v.get("aliases", [])[:3]})
        item["details"] = details
    return out
