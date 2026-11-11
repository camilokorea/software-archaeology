"""Executable specs: Markdown with YAML front matter. The front matter tells the pipeline what evidence and which
files the spec needs; the body is the analyst's instructions."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from archaeology import util
from archaeology.paths import SPECS


@dataclass
class Spec:
    id: str
    version: str
    title: str
    areas: list[str]
    inputs: list[str]
    files: dict
    body: str
    path: Path
    order: int = 50
    synthesis: bool = False
    hash: str = field(default="")


def load_all(selected: list[str] | str = "all") -> list[Spec]:
    specs = []
    for path in sorted(SPECS.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---"):
            continue
        _, front, body = text.split("---", 2)
        meta = yaml.safe_load(front)
        spec = Spec(id=meta["id"], version=str(meta["version"]), title=meta["title"], areas=meta["areas"],
                    inputs=meta.get("inputs", []), files=meta.get("files", {}), body=body.strip(), path=path,
                    order=meta.get("order", 50), synthesis=meta.get("synthesis", False), hash=util.sha(text))
        specs.append(spec)
    if selected != "all":
        wanted = set(selected)
        specs = [s for s in specs if s.id in wanted]
    return sorted(specs, key=lambda s: s.order)
