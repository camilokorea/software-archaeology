"""The finding format shared by every phase and both reports."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from jsonschema import Draft202012Validator

from archaeology.paths import SCHEMAS

AREA_PREFIX = {
    "inventory": "INV", "dependencies": "DEP", "architecture": "ARC", "database": "DB", "api": "API",
    "security": "SEC", "testing": "TST", "tech-debt": "DEBT", "devops": "OPS", "risk": "RSK",
    "capabilities": "CAP", "people": "PPL",
}
SEVERITY_RANK = {"critical": 5, "high": 4, "medium": 3, "low": 2, "info": 1}
CONFIDENCE_RANK = {"high": 3, "medium": 2, "low": 1}
EFFORT_WEEKS = {"S": (0.5, 1), "M": (1, 3), "L": (3, 8), "XL": (8, 20)}


@lru_cache
def schema(name: str) -> dict:
    return json.loads((SCHEMAS / f"{name}.schema.json").read_text(encoding="utf-8"))


@lru_cache
def validator(name: str) -> Draft202012Validator:
    return Draft202012Validator(schema(name))


def schema_errors(name: str, data: Any) -> list[str]:
    return [f"{'/'.join(map(str, e.path)) or '(root)'}: {e.message}" for e in validator(name).iter_errors(data)]


def finding(
    *, spec: str, area: str, title: str, severity: str, evidence: list[dict], technical_impact: str,
    business_impact: str, recommendation: str, effort: str = "M", confidence: str = "high", kind: str = "verified",
    tags: list[str] | None = None, refs: list[str] | None = None,
) -> dict:
    return {
        "id": "", "spec": spec, "area": area, "title": title[:160], "severity": severity, "kind": kind,
        "confidence": confidence, "evidence": evidence, "technical_impact": technical_impact,
        "business_impact": business_impact, "effort": effort, "recommendation": recommendation,
        "tags": tags or [], "refs": refs or [],
    }


def ev(file: str, line: int = 0, excerpt: str | None = None, source: str | None = None, end_line: int | None = None) -> dict:
    return {"file": file, "line": line, "end_line": end_line, "excerpt": excerpt, "source": source}


def score(f: dict) -> int:
    """Priority: severity first, then confidence; verified facts outrank inferences of equal weight."""
    return SEVERITY_RANK[f["severity"]] * 10 + CONFIDENCE_RANK[f["confidence"]] * 2 + (1 if f["kind"] == "verified" else 0)


def assign_ids(findings: list[dict]) -> list[dict]:
    counters: dict[str, int] = {}
    for f in sorted(findings, key=lambda x: (-score(x), x["area"], x["title"])):
        prefix = AREA_PREFIX[f["area"]]
        counters[prefix] = counters.get(prefix, 0) + 1
        f["id"] = f"{prefix}-{counters[prefix]:03d}"
    return sorted(findings, key=lambda x: (-score(x), x["id"]))
