"""archaeology: one command from a clone to two reports.

    archaeology dig ../legacy-app                 # evidence + verified findings + reports (no AI, no cost)
    archaeology dig ../legacy-app --provider anthropic
    archaeology estimate ../legacy-app --provider anthropic
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from archaeology import __version__, config, pipeline
from archaeology.specs import load_all


def _overrides(a: argparse.Namespace) -> dict:
    o: dict = {"ai": {}, "budget": {}, "network": {}, "output": {}}
    if getattr(a, "provider", None):
        o["ai"]["provider"] = a.provider
    if getattr(a, "model", None):
        o["ai"]["model"] = a.model
    if getattr(a, "effort", None):
        o["ai"]["effort"] = a.effort
    if getattr(a, "depth", None):
        o["depth"] = a.depth
    if getattr(a, "budget", None) is not None:
        o["budget"]["max_usd"] = a.budget
    if getattr(a, "offline", False):
        o["network"]["enabled"] = False
    if getattr(a, "specs", None):
        o["specs"] = [s.strip() for s in a.specs.split(",") if s.strip()]
    if getattr(a, "no_html", False):
        o["output"]["html"] = False
    return o


def _cfg(a: argparse.Namespace, repo: Path) -> dict:
    path = Path(a.config) if a.config else next((p for p in (repo / "archaeology.yaml", Path("archaeology.yaml")) if p.exists()), None)
    return config.load(path, _overrides(a))


def _common(p: argparse.ArgumentParser) -> None:
    p.add_argument("repo", type=Path, help="path to the codebase to analyze (read-only)")
    p.add_argument("--config", help="archaeology.yaml (default: ./archaeology.yaml if present)")
    p.add_argument("--out", type=Path, help="output folder (default: ./archaeology-output/<repo name>)")
    p.add_argument("--provider", choices=["none", "anthropic", "ollama", "claude-code"])
    p.add_argument("--model")
    p.add_argument("--effort", choices=["low", "medium", "high", "xhigh", "max"])
    p.add_argument("--depth", choices=["quick", "standard", "deep"])
    p.add_argument("--specs", help="comma-separated spec ids (default: all)")
    p.add_argument("--budget", type=float, help="maximum USD to spend on AI calls")
    p.add_argument("--offline", action="store_true", help="no network lookups (end of life, vulnerabilities)")
    p.add_argument("--no-html", action="store_true")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="archaeology", description="Evidence-first software archaeology for engineers and the business.")
    ap.add_argument("--version", action="version", version=f"software-archaeology {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("dig", help="run every phase and write both reports")
    _common(d)
    d.add_argument("--dry-run", action="store_true", help="write the prompts that would be sent, call no model")
    d.add_argument("--since", help="incremental: only analyze files changed since this git ref (reuses earlier results)")
    d.add_argument("--yes", action="store_true", help="run even if the estimate is over the budget (stops at the budget)")

    e = sub.add_parser("estimate", help="phases 0-1 and the cost estimate, without calling any model")
    _common(e)

    v = sub.add_parser("evidence", help="phases 0-1 and agent tasks, for Claude Code or other agents (see AGENTS.md)")
    _common(v)

    f = sub.add_parser("finish", help="validate agent findings and write the reports")
    f.add_argument("out", type=Path)

    r = sub.add_parser("report", help="re-render the reports from an existing output folder")
    r.add_argument("out", type=Path)

    i = sub.add_parser("init", help="write an archaeology.yaml with every option documented")
    i.add_argument("--force", action="store_true")

    sub.add_parser("specs", help="list the specs")

    a = ap.parse_args(argv)
    try:
        if a.cmd == "init":
            target = Path("archaeology.yaml")
            if target.exists() and not a.force:
                print("archaeology.yaml already exists (use --force to overwrite)")
                return 1
            target.write_text(config.example_yaml(), encoding="utf-8")
            print("Wrote archaeology.yaml")
            return 0
        if a.cmd == "specs":
            for s in load_all("all"):
                print(f"{s.id:<14} v{s.version:<6} {s.title}")
            return 0
        if a.cmd == "finish":
            pipeline.finish(a.out.resolve())
            return 0
        if a.cmd == "report":
            pipeline.rerender(a.out.resolve())
            return 0
        repo = a.repo.resolve()
        cfg = _cfg(a, repo)
        out = (a.out or (Path(cfg["output"]["dir"]) if cfg["output"]["dir"] else pipeline.default_out(repo))).resolve()
        if a.cmd == "estimate":
            pipeline.dig(repo, cfg | {"ai": cfg["ai"]}, out, dry_run=True)
            est = (out / "estimate.json").read_text()
            print(f"\nEstimate ({cfg['ai']['provider']}, prices in archaeology.yaml):\n{est}")
            return 0
        if a.cmd == "evidence":
            cfg["ai"]["provider"] = "claude-code"
            pipeline.dig(repo, cfg, out)
            return 0
        pipeline.dig(repo, cfg, out, dry_run=a.dry_run, since=a.since, assume_yes=a.yes)
        return 0
    except (pipeline.Abort, ValueError) as e:
        print(f"archaeology: {e}", file=sys.stderr)
        return 2
