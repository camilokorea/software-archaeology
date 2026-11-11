"""File walking with include/exclude globs, safe reading, redaction and hashing."""

from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Iterable, Iterator

TEXT_EXT = {
    ".cs", ".vb", ".fs", ".java", ".kt", ".scala", ".groovy", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".py",
    ".rb", ".php", ".go", ".rs", ".c", ".h", ".cpp", ".hpp", ".cc", ".m", ".swift", ".sql", ".psql", ".pls", ".pks",
    ".pkb", ".cbl", ".cob", ".cpy", ".jcl", ".bms", ".asm", ".pl", ".pm", ".sh", ".bash", ".ps1", ".bat", ".cmd",
    ".html", ".htm", ".cshtml", ".vbhtml", ".aspx", ".ascx", ".asax", ".master", ".jsp", ".jspx", ".xhtml", ".vue",
    ".svelte", ".css", ".scss", ".less", ".xml", ".config", ".json", ".yaml", ".yml", ".toml", ".ini", ".properties",
    ".gradle", ".csproj", ".vbproj", ".sln", ".tf", ".hcl", ".md", ".txt", ".cfm", ".cfc", ".asp", ".dockerfile",
    ".env", ".erb", ".twig", ".tpl", ".lua", ".r", ".dart", ".ex", ".exs", ".clj", ".hs", ".ml",
}
TEXT_NAMES = {"dockerfile", "makefile", "jenkinsfile", "procfile", "gemfile", "rakefile", "vagrantfile", ".gitlab-ci.yml"}


def matches(rel: str, patterns: Iterable[str]) -> bool:
    rel = rel.replace(os.sep, "/")
    for p in patterns:
        if fnmatch.fnmatch(rel, p) or fnmatch.fnmatch("/" + rel, p) or (p.startswith("**/") and fnmatch.fnmatch(rel, p[3:])):
            return True
    return False


def is_text(path: Path) -> bool:
    return path.suffix.lower() in TEXT_EXT or path.name.lower() in TEXT_NAMES


def walk(repo: Path, cfg: dict) -> Iterator[Path]:
    """Every in-scope file, as a path relative to the repo. Never follows symlinks out of the repo."""
    include = cfg["scope"]["include"]
    exclude = cfg["scope"]["exclude"]
    max_bytes = cfg["scope"]["max_file_kb"] * 1024
    for dirpath, dirnames, filenames in os.walk(repo, followlinks=False):
        rel_dir = os.path.relpath(dirpath, repo)
        rel_dir = "" if rel_dir == "." else rel_dir.replace(os.sep, "/")
        dirnames[:] = sorted(d for d in dirnames if not matches(f"{rel_dir}/{d}/x".lstrip("/"), exclude))
        for name in sorted(filenames):
            rel = f"{rel_dir}/{name}".lstrip("/")
            full = Path(dirpath) / name
            if full.is_symlink() or not matches(rel, include) or matches(rel, exclude):
                continue
            try:
                if full.stat().st_size > max_bytes:
                    continue
            except OSError:
                continue
            yield Path(rel)


def read(repo: Path, rel: Path | str) -> str:
    try:
        return (repo / rel).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def sha(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()[:16]


def dump(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")


def load_json(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


# ---------------------------------------------------------------- redaction

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE = re.compile(r"(?<!\w)(?:\+?\d{1,3}[ .-]?)?(?:\(?\d{3}\)?[ .-]?)\d{3}[ .-]?\d{4}(?!\w)")
IPV4 = re.compile(r"(?<![\d.])(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)(?![\d.])")


def redact(text: str, kinds: Iterable[str], secrets: Iterable[str] = ()) -> str:
    """Removes what must never reach a model or a report: known secret values first, then patterns."""
    for value in sorted({s for s in secrets if s and len(s) >= 6}, key=len, reverse=True):
        text = text.replace(value, "[REDACTED-SECRET]")
    kinds = set(kinds)
    if "secrets" in kinds:
        from archaeology.evidence.secrets import redact_inline

        text = redact_inline(text)
    if "emails" in kinds:
        text = EMAIL.sub("[REDACTED-EMAIL]", text)
    if "phones" in kinds:
        text = PHONE.sub("[REDACTED-PHONE]", text)
    if "ips" in kinds:
        text = IPV4.sub(lambda m: m.group(0) if m.group(0).startswith(("127.", "0.")) else "[REDACTED-IP]", text)
    return text


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)
