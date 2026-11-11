"""The anti-hallucination gate. A finding survives only if it matches the schema and every citation points to a
real file, a line inside it, and (when an excerpt is given) text that is actually there."""

from __future__ import annotations

import re
from pathlib import Path

from archaeology import model, util

WS = re.compile(r"\s+")


def _norm(s: str) -> str:
    s = re.sub(r"\[REDACTED-[A-Z]+\]", "", s)
    return WS.sub(" ", s.replace('"', "'")).strip().lower()


def check_evidence(repo: Path, item: dict, line_cache: dict) -> str | None:
    rel = item["file"]
    if rel in {".", "./"}:
        rel = "."
    elif rel.startswith("./"):  # strip only a "./" prefix: ".github" and ".mvn" are real folder names
        rel = rel[2:]
    rel = rel.lstrip("/")
    target = (repo / rel).resolve()
    if not str(target).startswith(str(repo.resolve())):
        return f"{item['file']}: outside the repository"
    if not target.exists():
        return f"{item['file']}: file does not exist"
    line = item.get("line") or 0
    if target.is_dir():
        return None if line == 0 else f"{item['file']}: is a directory, a line was cited"
    if rel not in line_cache:
        line_cache[rel] = util.read(repo, rel).splitlines()
    lines = line_cache[rel]
    if line > len(lines):
        return f"{item['file']}:{line}: the file has only {len(lines)} lines"
    excerpt = item.get("excerpt")
    if excerpt and line > 0:
        want = _norm(excerpt)
        if want:
            end = item.get("end_line") or line
            window = _norm(" ".join(lines[max(0, line - 4): min(len(lines), end + 3)]))
            # Long excerpts may be paraphrased at the edges; require a solid shared core.
            core = want if len(want) <= 60 else want[: max(40, len(want) // 2)]
            if core not in window and _norm(util.redact(" ".join(lines[max(0, line - 4): end + 3]), ["secrets"])).find(core) < 0:
                return f"{item['file']}:{line}: the quoted text is not at that line"
    return None


def findings(repo: Path, items: list[dict]) -> tuple[list[dict], list[dict]]:
    valid, rejected = [], []
    cache: dict = {}
    for f in items:
        # Ids are assigned after validation; check the shape with a placeholder id.
        errors = model.schema_errors("finding", {**f, "id": f["id"] or "TMP-000"})
        if not errors:
            errors = [e for e in (check_evidence(repo, ev, cache) for ev in f["evidence"]) if e]
        if errors:
            rejected.append({"finding": f, "reasons": errors})
        else:
            valid.append(f)
    return valid, rejected


def synthesis(data: dict, ids: set[str]) -> tuple[dict, list[str]]:
    """Drops citations to findings that do not exist; statements left without support are removed."""
    problems = model.schema_errors("synthesis", data)
    if problems:
        return data, problems
    dropped: list[str] = []

    def clean(items: list[dict], what: str, require: bool = True) -> list[dict]:
        out = []
        for it in items:
            unknown = [i for i in it.get("findings", []) if i not in ids]
            if unknown:
                dropped.append(f"{what}: unknown findings {', '.join(unknown)}")
            it["findings"] = [i for i in it.get("findings", []) if i in ids]
            if require and not it["findings"]:
                dropped.append(f"{what}: «{(it.get('text') or it.get('statement') or it.get('name') or it.get('phase') or '')[:60]}» removed, no supporting finding")
                continue
            out.append(it)
        return out

    data["executive_summary"]["points"] = clean(data["executive_summary"]["points"], "summary")
    data["risks"] = clean(data["risks"], "risk")
    data["capabilities"] = clean(data["capabilities"], "capability", require=False)
    data["options"] = clean(data["options"], "option", require=False)
    data["roadmap"] = clean(data["roadmap"], "roadmap", require=False)
    return data, dropped
