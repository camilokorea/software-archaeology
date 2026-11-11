"""Secrets in the working tree. Values are never written anywhere: findings carry a masked excerpt and a hash.
Uses gitleaks when installed; otherwise a built-in rule set."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from archaeology.evidence.index import Index

# (rule id, description, pattern with the secret in group "v")
RULES: list[tuple[str, str, re.Pattern]] = [
    ("aws-access-key", "AWS access key id", re.compile(r"(?P<v>(?:AKIA|ASIA)[0-9A-Z]{16})")),
    ("private-key", "Private key", re.compile(r"(?P<v>-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY-----)")),
    ("github-token", "GitHub token", re.compile(r"(?P<v>gh[pousr]_[A-Za-z0-9]{36,})")),
    ("slack-token", "Slack token", re.compile(r"(?P<v>xox[baprs]-[A-Za-z0-9-]{10,})")),
    ("google-api-key", "Google API key", re.compile(r"(?P<v>AIza[0-9A-Za-z\-_]{35})")),
    ("stripe-key", "Stripe live key", re.compile(r"(?P<v>(?:sk|rk)_live_[0-9A-Za-z]{16,})")),
    # A password inside a real connection string or JDBC URL, not any "password = something" in code.
    ("connection-string-password", "Password inside a connection string",
     re.compile(r"(?i)(?:(?:server|data source|host|database|initial catalog|user id|uid)\s*=[^;\n]*;[^\n]*?|jdbc:[^\s\"']*?[?&;])(?:password|pwd)\s*=\s*(?P<v>[^;&\"'<>\s]{4,})")),
    ("assigned-secret", "Hard-coded password, secret or API key",
     re.compile(r"""(?i)\b(?:password|passwd|secret|api[_-]?key|apikey|client[_-]?secret|auth[_-]?token|access[_-]?token)\b["']?\s*[:=]\s*["'](?P<v>[^"'\s]{6,})["']""")),
]
# key=value / key: value lines in configuration files (properties, env, ini, YAML).
CONFIG_SECRET = ("config-secret", "Password, secret or API key in a configuration file",
                 re.compile(r"""(?i)^\s*[\w.\-]*(?:password|passwd|pwd|secret|api[_.\-]?key|access[_.\-]?key|token)\s*[=:]\s*["']?(?P<v>[^\s"'#]{6,})["']?\s*$"""))
CONFIG_SUFFIXES = (".properties", ".env", ".ini", ".cfg", ".conf", ".yml", ".yaml", ".toml")
VARIABLE = re.compile(r"^(\$\{.*\}|\$\w+|%\w+%|\{\{.*\}\}|#\{.*\}|<%.*%>|\w+\(.*|[A-Z0-9_]+-[A-Z0-9_-]+|[A-Z_][A-Z0-9_]*)$")
PLACEHOLDERS = re.compile(r"(?i)^(\*+|x+|\$\{.*\}|\{\{.*\}\}|%.*%|<.*>|changeme|change_me|password|secret|your[_-]?.*|example.*|dummy|test|null|none|todo)$")


def _mask(line: str, value: str) -> str:
    # Same marker as redact_inline, so the validator can match the excerpt against the (redacted) line.
    return line.replace(value, "[REDACTED-SECRET]").strip()[:200]


def redact_inline(text: str) -> str:
    """Masks every rule match in a text; used before anything is sent to a model or written to a report."""
    for _, _, pattern in RULES:
        text = pattern.sub(lambda m: m.group(0).replace(m.group("v"), "[REDACTED-SECRET]"), text)
    return text


def scan(idx: Index) -> tuple[list[dict], set[str]]:
    """Returns (findings without values, the raw values for in-memory redaction only)."""
    if shutil.which("gitleaks"):
        found = _gitleaks(idx)
        if found is not None:
            return found
    results, values = [], set()
    for f in idx.files:
        if f.language in {None} and not f.path.lower().endswith((".config", ".json", ".yml", ".yaml", ".xml", ".properties",
                                                                   ".ini", ".env", ".toml", ".txt", ".sh", ".ps1")):
            continue
        text = idx.text(f.path)
        low = f.path.lower()
        ci_file = low.startswith((".github/", ".gitlab-ci", ".circleci/")) or "azure-pipelines" in low or low.endswith("jenkinsfile")
        # CI files use "token:" for matrix values and reference real secrets as variables; known token formats
        # (ghp_, AKIA…) are still caught by the specific rules.
        config_file = (low.endswith(CONFIG_SUFFIXES) or "/.env" in "/" + low) and not ci_file
        rules = RULES + ([CONFIG_SECRET] if config_file else [])
        for n, line in enumerate(text.splitlines(), 1):
            for rule, desc, pattern in rules:
                for m in pattern.finditer(line):
                    v = m.group("v")
                    # Variables, references and expressions are not secrets: only literal values are.
                    if PLACEHOLDERS.match(v) or VARIABLE.match(v) or len(set(v)) < 3:
                        continue
                    values.add(v)
                    results.append({"rule": rule, "description": desc, "file": f.path, "line": n,
                                    "excerpt": _mask(line, v), "fingerprint": hashlib.sha256(v.encode()).hexdigest()[:12],
                                    "tool": "built-in rules"})
    return results, values


def _relative(file: str, repo: Path) -> str:
    """gitleaks reports paths as given on the command line: absolute, or relative to where it ran."""
    p = Path(file)
    root = repo.resolve()
    for candidate in (p, Path.cwd() / p, root / p):
        try:
            return candidate.resolve().relative_to(root).as_posix()
        except ValueError:
            continue
    return file


def _gitleaks(idx: Index):
    with tempfile.TemporaryDirectory() as tmp:
        report = Path(tmp) / "report.json"
        try:
            subprocess.run(["gitleaks", "detect", "--no-git", "--source", str(idx.repo), "--report-format", "json",
                            "--report-path", str(report), "--exit-code", "0", "--no-banner"],
                           capture_output=True, timeout=300, check=False)
            data = json.loads(report.read_text() or "[]")
        except Exception:  # noqa: BLE001 - fall back to built-in rules
            return None
    results, values = [], set()
    for item in data:
        secret = item.get("Secret") or ""
        values.add(secret)
        rel = _relative(item.get("File") or "", idx.repo)
        results.append({"rule": item.get("RuleID"), "description": item.get("Description"), "file": rel,
                        "line": item.get("StartLine", 0), "excerpt": _mask(item.get("Match", ""), secret) if secret else "",
                        "fingerprint": hashlib.sha256(secret.encode()).hexdigest()[:12], "tool": "gitleaks"})
    return results, values
