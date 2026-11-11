"""C4-style container diagram (Mermaid flowchart) drawn from the evidence: components, data stores, external
systems and messaging. Mermaid renders on GitHub, GitLab and in the HTML reports."""

from __future__ import annotations

import re


def _id(text: str) -> str:
    return re.sub(r"\W+", "_", text).strip("_")[:40] or "root"


def _label(text: str) -> str:
    return text.replace('"', "'")


def containers(evidence: dict) -> str:
    inv = evidence.get("inventory", {})
    db = evidence.get("database", {})
    ext = evidence.get("externals", {})
    lines = ["flowchart LR", '  users(["Users"])']
    comps = [c for c in inv.get("components", []) if c["kind"] != "tests"][:14]
    for c in comps:
        tech = ", ".join(c["languages"][:3]) or ", ".join(c["ecosystems"])
        lines.append(f'  {_id("c_" + c["path"])}["<b>{_label(c["path"])}</b><br/>{_label(c["kind"])}<br/><i>{_label(tech)}</i>"]')
    fronts = [c for c in comps if "frontend" in c["kind"] or "web application" in c["kind"]] or comps[:1]
    for c in fronts:
        lines.append(f"  users --> {_id('c_' + c['path'])}")
    for s in db.get("stores", [])[:5]:
        sid = _id("db_" + s["name"])
        lines.append(f'  {sid}[("{_label(s["name"])}")]')
        for c in comps:
            if c["kind"] not in {"frontend or Node.js application"}:
                lines.append(f"  {_id('c_' + c['path'])} --> {sid}")
                break
    for q in ext.get("messaging", [])[:4]:
        qid = _id("q_" + q["name"])
        lines.append(f'  {qid}[/"{_label(q["name"])}"/]')
        if comps:
            lines.append(f"  {_id('c_' + comps[0]['path'])} -.-> {qid}")
    for h in ext.get("hosts", [])[:6]:
        hid = _id("x_" + h["endpoint"])
        host = h["endpoint"].split("://", 1)[1]
        lines.append(f'  {hid}{{{{"{_label(host)}"}}}}')
        owner = next((c for c in sorted(comps, key=lambda c: -len(c["path"])) if c["path"] == "." or h["file"].startswith(c["path"] + "/")), None)
        if owner:
            lines.append(f"  {_id('c_' + owner['path'])} -.-> {hid}")
    return "\n".join(lines)
