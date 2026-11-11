"""archaeology.yaml: what to analyze, how deep, for whom, with which model and within which budget."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml

DEFAULTS: dict[str, Any] = {
    "project": {"name": None, "description": None},
    "scope": {
        "include": ["**/*"],
        "exclude": [
            "**/.git/**", "**/node_modules/**", "**/bower_components/**", "**/vendor/**", "**/packages/**",
            "**/bin/**", "**/obj/**", "**/dist/**", "**/build/**", "**/target/**", "**/.venv/**", "**/venv/**",
            "**/__pycache__/**", "**/*.min.js", "**/*.min.css", "**/*.map", "**/.archaeology/**",
        ],
        "max_file_kb": 512,
    },
    "depth": "standard",  # quick | standard | deep
    "audiences": ["technical", "business"],
    "specs": "all",  # or a list of spec ids
    "ai": {
        "provider": "none",  # none | anthropic | ollama | claude-code
        "model": None,  # provider default when null
        "effort": "medium",
        "ollama_url": "http://localhost:11434",
        "max_context_tokens": 60000,
        "temperature": None,
    },
    "budget": {"max_usd": 5.0, "price_per_mtok": {"input": 4.0, "output": 20.0}},
    "privacy": {
        "send_source": True,  # false: only evidence summaries reach the model, never code
        "redact": ["secrets", "emails", "phones", "ips"],
        "pseudonymize_authors": True,
        "never_send": ["**/.env*", "**/*.pem", "**/*.key", "**/*.pfx", "**/*.p12", "**/id_rsa*", "**/secrets.*"],
    },
    "network": {"enabled": True, "eol": True, "osv": True, "timeout_s": 10},
    "output": {"dir": None, "html": True, "language": "en"},
}

DEPTH_LIMITS = {
    "quick": {"files_per_spec": 8, "max_findings": 6},
    "standard": {"files_per_spec": 20, "max_findings": 12},
    "deep": {"files_per_spec": 45, "max_findings": 25},
}


def _merge(base: dict, extra: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in (extra or {}).items():
        out[k] = _merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def load(path: Path | None, overrides: dict | None = None) -> dict:
    data: dict = {}
    if path and path.exists():
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    cfg = _merge(DEFAULTS, data)
    cfg = _merge(cfg, overrides or {})
    if cfg["depth"] not in DEPTH_LIMITS:
        raise ValueError(f"depth must be one of {', '.join(DEPTH_LIMITS)}")
    if cfg["ai"]["provider"] not in {"none", "anthropic", "ollama", "claude-code"}:
        raise ValueError("ai.provider must be none, anthropic, ollama or claude-code")
    return cfg


def example_yaml() -> str:
    return (Path(__file__).resolve().parent.parent / "archaeology.example.yaml").read_text(encoding="utf-8")
