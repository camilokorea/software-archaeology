"""Links from a citation to the code: to the hosting service when the repo has a known remote, else a path."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


def remote_base(repo: Path, head: str | None) -> str | None:
    out = subprocess.run(["git", "-C", str(repo), "remote", "get-url", "origin"], capture_output=True, text=True)
    url = out.stdout.strip()
    if not url or not head:
        return None
    url = re.sub(r"^git@([^:]+):", r"https://\1/", url)
    url = re.sub(r"//[^/@]+@", "//", url)  # never keep credentials embedded in a remote URL
    url = re.sub(r"\.git$", "", url)
    if "github.com" in url or "gitlab" in url:
        return f"{url}/blob/{head}/"
    return None


def cite(item: dict, base: str | None) -> str:
    file, line = item["file"], item.get("line") or 0
    label = f"{file}:{line}" if line else file
    if base and file not in {".", "./"}:
        return f"[`{label}`]({base}{file}{f'#L{line}' if line else ''})"
    return f"`{label}`"
