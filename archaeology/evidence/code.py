"""Size and branching of each source file, and the hotspots: complex code that changes often."""

from __future__ import annotations

import re

from archaeology.evidence.index import Index

DECISIONS = re.compile(r"\b(if|elif|else if|for|foreach|while|case|catch|when|unless|except|EVALUATE|PERFORM)\b|&&|\|\||\?\s*[^:]+:", re.I)


def complexity(idx: Index) -> list[dict]:
    out = []
    for f in idx.source():
        text = idx.text(f.path)
        decisions = len(DECISIONS.findall(text))
        out.append({"path": f.path, "language": f.language, "code_lines": f.code_lines, "decisions": decisions,
                    "density": round(decisions / max(1, f.code_lines) * 100, 1)})
    out.sort(key=lambda x: -x["decisions"])
    return out


def hotspots(cx: list[dict], history: dict, top: int = 20) -> list[dict]:
    if not history.get("available"):
        return []
    churn = {f["path"]: f for f in history["files"]}
    max_c = max((c["decisions"] for c in cx), default=1) or 1
    max_h = max((f["commits"] for f in history["files"]), default=1) or 1
    rows = []
    for c in cx:
        h = churn.get(c["path"])
        if not h or c["decisions"] == 0:
            continue
        rows.append({**c, "commits": h["commits"], "authors": h["authors"], "last_change": h["last_change"],
                     "score": round((c["decisions"] / max_c) * (h["commits"] / max_h) * 100, 1)})
    rows.sort(key=lambda r: -r["score"])
    return rows[:top]
