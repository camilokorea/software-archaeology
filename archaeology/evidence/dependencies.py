"""Declared dependencies and runtimes, read from manifests, each with the file and line that declares it."""

from __future__ import annotations

import json
import re

from archaeology.evidence.index import Index


def _line(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _clean(version: str | None) -> str | None:
    if not version:
        return None
    v = version.strip().strip("\"'")
    v = re.sub(r"^[\^~>=<v ]+", "", v)
    m = re.match(r"\d+(\.\d+){0,3}", v)
    return m.group(0) if m else None


def scan(idx: Index) -> dict:
    deps: list[dict] = []
    runtimes: list[dict] = []

    def dep(eco, name, version, file, line, scope="runtime"):
        deps.append({"ecosystem": eco, "name": name, "version": _clean(version), "declared": version, "file": file, "line": line, "scope": scope})

    def runtime(product, version, file, line):
        if version:
            runtimes.append({"product": product, "version": version, "file": file, "line": line})

    for f in idx.by_name("package.json", "bower.json"):
        text = idx.text(f.path)
        try:
            data = json.loads(text)
        except ValueError:
            continue
        for section, scope in (("dependencies", "runtime"), ("devDependencies", "dev")):
            for name, version in (data.get(section) or {}).items():
                i = text.find(f'"{name}"')
                dep("npm", name, str(version), f.path, _line(text, max(i, 0)), scope)
        if node := (data.get("engines") or {}).get("node"):
            runtime("nodejs", _clean(str(node)), f.path, _line(text, text.find('"node"')))

    for f in idx.by_name("packages.config"):
        text = idx.text(f.path)
        for m in re.finditer(r'<package\s+id="([^"]+)"\s+version="([^"]+)"(?:[^>]*targetFramework="([^"]+)")?', text):
            dep("NuGet", m.group(1), m.group(2), f.path, _line(text, m.start()))

    for f in idx.by_suffix(".csproj", ".vbproj", ".fsproj"):
        text = idx.text(f.path)
        for m in re.finditer(r'<PackageReference\s+Include="([^"]+)"\s+Version="([^"]+)"', text):
            dep("NuGet", m.group(1), m.group(2), f.path, _line(text, m.start()))
        for m in re.finditer(r'<PackageReference\s+Include="([^"]+)"[^/]*?>\s*<Version>([^<]+)</Version>', text):
            dep("NuGet", m.group(1), m.group(2), f.path, _line(text, m.start()))
        if m := re.search(r"<TargetFrameworkVersion>v([\d.]+)</", text):
            runtime("dotnetfx", m.group(1), f.path, _line(text, m.start()))
        if m := re.search(r"<TargetFrameworks?>([^<]+)</", text):
            for tfm in m.group(1).split(";"):
                if mm := re.match(r"net(?:coreapp)?(\d+\.\d+)$", tfm.strip()):
                    runtime("dotnet", mm.group(1), f.path, _line(text, m.start()))
                elif mm := re.match(r"net(\d)(\d)(\d?)$", tfm.strip()):
                    runtime("dotnetfx", ".".join(x for x in mm.groups() if x), f.path, _line(text, m.start()))

    for f in idx.by_name("pom.xml"):
        text = idx.text(f.path)
        props = dict(re.findall(r"<([\w.\-]+)>([^<${}]+)</\1>", text))
        for m in re.finditer(r"<dependency>(.*?)</dependency>", text, re.S):
            block = m.group(1)
            g = re.search(r"<groupId>([^<]+)</groupId>", block)
            a = re.search(r"<artifactId>([^<]+)</artifactId>", block)
            v = re.search(r"<version>([^<]+)</version>", block)
            s = re.search(r"<scope>([^<]+)</scope>", block)
            if not (g and a):
                continue
            version = v.group(1) if v else None
            if version and version.startswith("${"):
                version = props.get(version[2:-1], version)
            dep("Maven", f"{g.group(1)}:{a.group(1)}", version, f.path, _line(text, m.start()), "test" if s and s.group(1) == "test" else "runtime")
        if m := re.search(r"<parent>.*?<artifactId>spring-boot-starter-parent</artifactId>\s*<version>([^<]+)</version>", text, re.S):
            dep("Maven", "org.springframework.boot:spring-boot", m.group(1), f.path, _line(text, m.start()))
        for key in ("java.version", "maven.compiler.source", "maven.compiler.release"):
            if key in props:
                runtime("java", _clean(props[key]), f.path, _line(text, text.find(f"<{key}>")))
                break

    for f in idx.by_name("build.gradle", "build.gradle.kts"):
        text = idx.text(f.path)
        for m in re.finditer(r"""(implementation|api|compile|testImplementation|runtimeOnly)\s*\(?\s*['"]([\w.\-]+):([\w.\-]+):([\w.\-]+)['"]""", text):
            dep("Maven", f"{m.group(2)}:{m.group(3)}", m.group(4), f.path, _line(text, m.start()), "test" if "test" in m.group(1).lower() else "runtime")

    for f in idx.by_name("requirements.txt"):
        text = idx.text(f.path)
        for m in re.finditer(r"^\s*([A-Za-z0-9_.\-]+)\s*(?:==|>=|~=)\s*([\w.]+)", text, re.M):
            dep("PyPI", m.group(1), m.group(2), f.path, _line(text, m.start()))

    for f in idx.by_name("composer.json"):
        text = idx.text(f.path)
        try:
            data = json.loads(text)
        except ValueError:
            continue
        for name, version in (data.get("require") or {}).items():
            if name == "php":
                runtime("php", _clean(version), f.path, _line(text, text.find('"php"')))
            elif "/" in name:
                dep("Packagist", name, version, f.path, _line(text, text.find(f'"{name}"')))

    for f in idx.by_name("go.mod"):
        text = idx.text(f.path)
        for m in re.finditer(r"^\s*([\w.\-/]+\.[\w.\-/]+)\s+v([\w.\-+]+)", text, re.M):
            dep("Go", m.group(1), m.group(2), f.path, _line(text, m.start()))
        if m := re.search(r"^go\s+([\d.]+)", text, re.M):
            runtime("go", m.group(1), f.path, _line(text, m.start()))

    for f in idx.by_name("gemfile.lock"):
        text = idx.text(f.path)
        for m in re.finditer(r"^    ([\w\-]+) \(([\d.]+)\)", text, re.M):
            dep("RubyGems", m.group(1), m.group(2), f.path, _line(text, m.start()))

    for f in idx.by_name(".nvmrc", ".node-version"):
        runtime("nodejs", _clean(idx.text(f.path)), f.path, 1)
    for f in idx.by_name(".python-version", "runtime.txt"):
        if v := _clean(idx.text(f.path).replace("python-", "")):
            runtime("python", v, f.path, 1)

    seen = set()
    unique = []
    for d in deps:
        key = (d["ecosystem"], d["name"].lower(), d["version"], d["file"])
        if key not in seen:
            seen.add(key)
            unique.append(d)
    return {"dependencies": unique, "runtimes": runtimes}
