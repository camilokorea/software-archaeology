"""Builds the public examples, or checks that they still reproduce.

    python examples/build.py                 # clone the pinned commits, analyze, write examples/<name>/
    python examples/build.py --check         # re-run offline and compare with expected-offline.json (CI)
    python examples/build.py --only NodeGoat --workdir /tmp/repos

Published outputs are the reports and the structured findings. Paths of the machine that built them are removed.
The online lookups (end of life, known vulnerabilities) change over time, so the check compares the offline,
fully deterministic part of each run.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from archaeology import config, pipeline, util  # noqa: E402

PUBLISHED = ["executive.md", "executive.html", "technical.md", "technical.html", "backlog.csv", "architecture.mmd",
             "synthesis.json", "findings/findings.json", "findings/rejected.json", "findings/not-found.json", "run.json"]


def clone(repo: dict, workdir: Path) -> Path:
    target = workdir / repo["name"]
    if not (target / ".git").exists():
        subprocess.run(["git", "clone", "--quiet", repo["url"], str(target)], check=True)
    subprocess.run(["git", "-C", str(target), "fetch", "--quiet", "origin", repo["commit"]], check=False)
    subprocess.run(["git", "-C", str(target), "checkout", "--quiet", "--detach", repo["commit"]], check=True)
    return target


def analyze(repo: dict, path: Path, out: Path, offline: bool) -> dict:
    cfg = config.load(None, {"project": {"name": repo["name"]}, "network": {"enabled": not offline}})
    return pipeline.dig(path, cfg, out, log=lambda *_: None)


def fingerprint(findings: list[dict]) -> list[str]:
    """What must not change between runs: which verified facts were found, where."""
    return sorted(f"{f['area']} | {f['severity']} | {f['title']} | {', '.join(sorted({e['file'] for e in f['evidence']}))}" for f in findings)


def publish(repo: dict, out: Path, dest: Path, local_path: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    for rel in PUBLISHED:
        src = out / rel
        if src.exists():
            (dest / rel).parent.mkdir(parents=True, exist_ok=True)
            text = src.read_text(encoding="utf-8")
            # Remove the paths of the machine that built the example.
            text = text.replace(str(local_path), repo["url"]).replace(str(out), "archaeology-output/" + repo["name"])
            (dest / rel).write_text(text, encoding="utf-8")
    log = util.load_json(dest / "run.json")
    log["repo"] = {"url": repo["url"], "commit": repo["commit"]}
    log["config"].pop("output", None)
    util.dump(dest / "run.json", log)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--only")
    ap.add_argument("--workdir", type=Path)
    a = ap.parse_args()
    repos = [r for r in json.loads((HERE / "repos.json").read_text()) if not a.only or r["name"] == a.only]
    workdir = a.workdir or Path(tempfile.mkdtemp(prefix="archaeology-examples-"))
    workdir.mkdir(parents=True, exist_ok=True)
    failed = False
    for repo in repos:
        path = clone(repo, workdir)
        with tempfile.TemporaryDirectory() as tmp:
            offline = analyze(repo, path, Path(tmp) / "offline", offline=True)
            got = fingerprint(offline["findings"])
            expected_file = HERE / repo["name"] / "expected-offline.json"
            if a.check:
                expected = json.loads(expected_file.read_text())
                if got != expected:
                    failed = True
                    print(f"✗ {repo['name']}: verified findings changed")
                    for line in sorted(set(expected) - set(got)):
                        print(f"   - {line}")
                    for line in sorted(set(got) - set(expected)):
                        print(f"   + {line}")
                else:
                    print(f"✓ {repo['name']}: {len(got)} verified findings reproduce")
                continue
            online_out = Path(tmp) / "online"
            result = analyze(repo, path, online_out, offline=False)
            publish(repo, online_out, HERE / repo["name"], path)
            expected_file.write_text(json.dumps(got, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            print(f"• {repo['name']}: {len(result['findings'])} findings, status {result['synthesis']['executive_summary']['status']}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
