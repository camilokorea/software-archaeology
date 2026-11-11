"""What git remembers: how much each file changes, who knows it, how old it is. Authors are pseudonymized by
default ("Dev 1"), because the report is about knowledge risk, not about people."""

from __future__ import annotations

import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


def _git(repo: Path, *args: str) -> str:
    out = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, timeout=300)
    return out.stdout if out.returncode == 0 else ""


def scan(repo: Path, files: set[str], pseudonymize: bool = True, max_commits: int = 20000) -> dict:
    if not (repo / ".git").exists() or not _git(repo, "rev-parse", "HEAD"):
        return {"available": False}
    log = _git(repo, "log", "--no-merges", f"-n{max_commits}", "--format=@@%H|%an|%ct", "--numstat")
    churn: Counter = Counter()
    authors_of: dict[str, Counter] = defaultdict(Counter)
    last_change: dict[str, int] = {}
    first_change: dict[str, int] = {}
    commits_by_year: Counter = Counter()
    authors_total: Counter = Counter()
    author, when = None, 0
    commits = 0
    for line in log.splitlines():
        if line.startswith("@@"):
            _, author, ts = line[2:].split("|", 2)
            when = int(ts)
            commits += 1
            commits_by_year[datetime.fromtimestamp(when, timezone.utc).year] += 1
            authors_total[author] += 1
            continue
        parts = line.split("\t")
        if len(parts) != 3 or author is None:
            continue
        path = parts[2]
        if "=>" in path:  # renames: keep the new name
            path = path.split("=>")[-1].strip("{} ").replace("{", "").replace("}", "")
        churn[path] += 1
        authors_of[path][author] += 1
        last_change[path] = max(last_change.get(path, 0), when)
        first_change[path] = min(first_change.get(path, when), when)

    alias = {a: (f"Dev {i}" if pseudonymize else a) for i, (a, _) in enumerate(authors_total.most_common(), 1)}
    in_scope = [p for p in churn if p in files]
    per_file = []
    for p in in_scope:
        owners = authors_of[p]
        top, top_n = owners.most_common(1)[0]
        per_file.append({
            "path": p, "commits": churn[p], "authors": len(owners), "top_author": alias[top],
            "top_author_share": round(top_n / sum(owners.values()), 2),
            "last_change": datetime.fromtimestamp(last_change[p], timezone.utc).date().isoformat(),
            "first_change": datetime.fromtimestamp(first_change[p], timezone.utc).date().isoformat(),
        })
    per_file.sort(key=lambda x: -x["commits"])
    # Knowledge concentration: files mostly written by one person, weighted by how often they change.
    concentrated = [f for f in per_file if f["top_author_share"] >= 0.8 and f["commits"] >= 3]
    owners_of_concentrated = Counter(f["top_author"] for f in concentrated)
    head = _git(repo, "rev-parse", "HEAD").strip()
    first = _git(repo, "log", "--reverse", "--format=%ct").strip().split("\n")[0]
    last = _git(repo, "log", "-n1", "--format=%ct").strip()
    shallow = _git(repo, "rev-parse", "--is-shallow-repository").strip() == "true"
    return {
        "available": True,
        "shallow": shallow,
        "head": head,
        "commits": commits,
        "contributors": len(authors_total),
        "first_commit": datetime.fromtimestamp(int(first), timezone.utc).date().isoformat() if first else None,
        "last_commit": datetime.fromtimestamp(int(last), timezone.utc).date().isoformat() if last else None,
        "commits_by_year": dict(sorted(commits_by_year.items())),
        "top_contributors": [{"author": alias[a], "commits": n} for a, n in authors_total.most_common(10)],
        "files": per_file[:400],
        "knowledge_concentration": {
            "files_owned_by_one_person": len(concentrated),
            "share_of_changed_files": round(len(concentrated) / max(1, len(per_file)), 2),
            "by_person": [{"author": a, "files": n} for a, n in owners_of_concentrated.most_common(5)],
            "examples": concentrated[:15],
        },
        "bus_factor": _bus_factor(authors_total),
    }


def _bus_factor(authors_total: Counter) -> int:
    """Smallest number of people who together made at least half of the commits."""
    total = sum(authors_total.values())
    acc, n = 0, 0
    for _, c in authors_total.most_common():
        acc += c
        n += 1
        if acc * 2 >= total:
            break
    return n


def changed_since(repo: Path, ref: str) -> set[str]:
    out = _git(repo, "diff", "--name-only", f"{ref}...HEAD")
    return {l.strip() for l in out.splitlines() if l.strip()}
