"""Builds what a model sees for one spec: the evidence it asked for and a budgeted, redacted sample of files."""

from __future__ import annotations

import json
import re

from archaeology import util
from archaeology.config import DEPTH_LIMITS
from archaeology.evidence.index import Index
from archaeology.specs import Spec


def _trim_evidence(data, max_chars: int) -> str:
    text = json.dumps(data, ensure_ascii=False, separators=(",", ":"), default=str)
    return text if len(text) <= max_chars else text[:max_chars] + "…(truncated)"


def select_files(spec: Spec, idx: Index, evidence: dict, limit: int, only: set[str] | None = None) -> list[str]:
    """Ranks files for a spec: explicit globs, name keywords, hotspots and largest sources, in that order."""
    rules = spec.files or {}
    never = idx.cfg["privacy"]["never_send"]
    candidates = [f for f in idx.files if not util.matches(f.path, never) and util.is_text(idx.repo / f.path)]
    if only is not None:
        candidates = [f for f in candidates if f.path in only]
    chosen: list[str] = []

    def take(paths):
        for p in paths:
            if p not in chosen and len(chosen) < limit:
                chosen.append(p)

    globs = rules.get("globs", [])
    take(f.path for f in candidates if globs and util.matches(f.path, globs))
    words = [w.lower() for w in rules.get("keywords", [])]
    if words:
        take(f.path for f in sorted(candidates, key=lambda f: -f.code_lines)
             if any(w in f.path.lower() for w in words))
    content = rules.get("content")
    if content:
        rx = re.compile(content, re.I)
        take(f.path for f in candidates if f.language and rx.search(idx.text(f.path)[:20000]))
    allowed = {f.path for f in candidates}
    if rules.get("hotspots"):
        take(h["path"] for h in evidence.get("hotspots", []) if h["path"] in allowed)
    if rules.get("largest"):
        take(f.path for f in sorted((f for f in candidates if f.language), key=lambda f: -f.code_lines))
    return chosen


def build(spec: Spec, idx: Index, evidence: dict, cfg: dict, secret_values: set[str], only: set[str] | None = None) -> tuple[str, list[str]]:
    limits = DEPTH_LIMITS[cfg["depth"]]
    budget_tokens = cfg["ai"]["max_context_tokens"]
    parts = [f"# Spec: {spec.title} (v{spec.version})\n\n{spec.body}\n"]
    parts.append(f"\nReturn at most {limits['max_findings']} findings for this spec, the most important first.\n")
    parts.append("\n# Evidence from deterministic tools (JSON)\n")
    per_input = max(2000, int(budget_tokens * 4 * 0.35 / max(1, len(spec.inputs))))
    for key in spec.inputs:
        if key in evidence:
            parts.append(f"\n## {key}\n{_trim_evidence(evidence[key], per_input)}\n")
    files: list[str] = []
    if cfg["privacy"]["send_source"]:
        used = util.estimate_tokens("".join(parts))
        parts.append("\n# Source files (line-numbered, redacted). Cite files and lines exactly as shown.\n")
        for path in select_files(spec, idx, evidence, limits["files_per_spec"], only):
            text = util.redact(idx.text(path), cfg["privacy"]["redact"], secret_values)
            numbered = "\n".join(f"{n:>5}| {l}" for n, l in enumerate(text.splitlines(), 1))
            cost = util.estimate_tokens(numbered)
            if used + cost > budget_tokens:
                # Keep the start of the file rather than skipping it entirely, if there is room for a useful chunk.
                room = (budget_tokens - used) * 4
                if room < 2000:
                    break
                numbered = numbered[:room] + "\n…(file truncated to fit the budget)"
                cost = util.estimate_tokens(numbered)
            parts.append(f"\n## File: {path}\n```\n{numbered}\n```\n")
            files.append(path)
            used += cost
    else:
        parts.append("\n(Privacy setting send_source=false: no source code is included. Work from the evidence only and cite the files it names.)\n")
    return "".join(parts), files
