"""The fixed sequence of phases, each with its own output, and the hand-off points for external agents."""

from __future__ import annotations

import json
import time
from datetime import date, datetime, timezone
from pathlib import Path

from archaeology import __version__, analyze, model, rules, synthesize, util, validate
from archaeology.evidence import code, dependencies, history, inventory, online, secrets, surface
from archaeology.evidence.index import Index
from archaeology.llm import Usage, make
from archaeology.report import backlog, diagrams, html, links, markdown
from archaeology.specs import load_all


class Abort(RuntimeError):
    pass


def default_out(repo: Path) -> Path:
    return Path.cwd() / "archaeology-output" / repo.resolve().name


def check_paths(repo: Path, out: Path) -> None:
    repo, out = repo.resolve(), out.resolve()
    if not repo.is_dir():
        raise Abort(f"{repo} is not a directory")
    if out == repo or str(out).startswith(str(repo) + "/"):
        raise Abort("The output folder must be outside the analyzed repository: the analysis never writes into it.")


class Run:
    def __init__(self, repo: Path, cfg: dict, out: Path, log=print):
        self.repo, self.cfg, self.out, self.log = repo.resolve(), cfg, out.resolve(), log
        self.cache = self.out / ".cache"
        self.started = datetime.now(timezone.utc)
        self.phases: list[dict] = []
        self.warnings: list[str] = []
        self.usage = Usage()
        self.secret_values: set[str] = set()

    def phase(self, name: str):
        run = self

        class _P:
            def __enter__(self):
                self.t = time.time()
                run.log(f"▸ {name}")

            def __exit__(self, *exc):
                run.phases.append({"phase": name, "seconds": round(time.time() - self.t, 1), "ok": exc[0] is None})

        return _P()

    # ------------------------------------------------ phases 0 and 1

    def evidence(self) -> tuple[Index, dict]:
        cfg = self.cfg
        with self.phase("0 · intake"):
            idx = Index.build(self.repo, cfg)
            inv = inventory.summarize(idx)
            self.log(f"  {inv['files']:,} files, {inv['code_lines']:,} lines of code ({inv['size_class']}); "
                     f"{', '.join(l['language'] for l in inv['languages'][:4] if l['language'] != 'Other')}")
        ev: dict = {"inventory": inv}
        with self.phase("1 · evidence"):
            files = {f.path for f in idx.files}
            ev["history"] = history.scan(self.repo, files, pseudonymize=cfg["privacy"].get("pseudonymize_authors", True))
            ev["dependencies"] = dependencies.scan(idx)
            net = online.Net(self.cache / "net", cfg["network"]["enabled"], cfg["network"]["timeout_s"])
            ev["eol"] = online.end_of_life(ev["dependencies"], net) if cfg["network"]["eol"] else []
            ev["vulnerabilities"] = online.vulnerabilities(ev["dependencies"], net) if cfg["network"]["osv"] else []
            self.warnings += [f"network: {e}" for e in net.errors[:5]]
            found, self.secret_values = secrets.scan(idx)
            ev["secrets"] = found
            ev["complexity"] = code.complexity(idx)[:300]
            ev["hotspots"] = code.hotspots(ev["complexity"], ev["history"])
            ev["api"] = surface.endpoints(idx)
            ev["database"] = surface.database(idx)
            ev["tests"] = surface.tests(idx)
            ev["devops"] = surface.devops(idx)
            ev["externals"] = surface.externals(idx)
            for k, v in ev.items():
                util.dump(self.out / "evidence" / f"{k}.json", v)
            self.log(f"  {len(ev['dependencies']['dependencies'])} dependencies, {sum(e['is_eol'] for e in ev['eol'])} past end of life, "
                     f"{len(ev['vulnerabilities'])} with known vulnerabilities, {len(ev['secrets'])} secrets, {len(ev['api'])} entry points")
        return idx, ev

    # ------------------------------------------------ phase 2

    def analysis(self, idx: Index, ev: dict, dry_run: bool, since: str | None, assume_yes: bool) -> tuple[list[dict], dict]:
        cfg = self.cfg
        provider_name = cfg["ai"]["provider"]
        specs = load_all(cfg["specs"])
        only = None
        if since:
            only = history.changed_since(self.repo, since)
            self.log(f"  incremental: {len(only)} files changed since {since}")
        plans = analyze.plan(specs, idx, ev, cfg, self.secret_values, only)
        prices = cfg["budget"]["price_per_mtok"]
        est = analyze.estimate(plans, prices)
        util.dump(self.out / "estimate.json", est)
        if provider_name == "claude-code" or dry_run:
            folder = self.out / ("agent-tasks" if provider_name == "claude-code" else "prompts")
            sys_prompt = analyze.system_prompt()
            for p in plans:
                (folder).mkdir(parents=True, exist_ok=True)
                (folder / f"{p['spec'].id}{'@' + p['part'].replace('/', '_') if p.get('part') else ''}.md").write_text(
                    f"<!-- system prompt -->\n{sys_prompt}\n\n<!-- task -->\n{p['user']}\n\n<!-- Write the answer as JSON matching "
                    f"schemas/llm-findings.schema.json to findings/agent/{p['spec'].id}.json "
                    f"(append to the same file when a spec is split by component) -->\n", encoding="utf-8")
            (self.out / "findings" / "agent").mkdir(parents=True, exist_ok=True)
            self.log(f"  {len(plans)} prompts written to {folder} (~{est['input_tokens']:,} input tokens; ≈ ${est['usd']} with {cfg['ai']['provider']} prices)")
            return [], {}
        provider = make(cfg)
        if provider is None:
            self.log("  no AI provider configured: the reports use verified findings only (set ai.provider to add AI analysis)")
            return [], {}
        with self.phase("2 · AI analysis"):
            self.log(f"  estimate: {est['calls']} calls, ~{est['input_tokens']:,} input tokens, ≈ ${est['usd']} (budget ${cfg['budget']['max_usd']})")
            if est["usd"] > cfg["budget"]["max_usd"] and not assume_yes:
                raise Abort(f"The estimate (${est['usd']}) is over the budget (${cfg['budget']['max_usd']}). Raise budget.max_usd, "
                            "use --depth quick, limit --specs, or pass --yes to run until the budget is spent.")
            found, not_found, usage, warns = analyze.run(plans, provider, self.cache / "llm", cfg["budget"]["max_usd"], prices, self.log)
            self.usage.add(usage)
            self.warnings += warns
            if since:
                previous = util.load_json(self.out / "findings" / "findings.json", []) or []
                kept = [f for f in previous if f["kind"] == "inferred" and not any(e["file"] in only for e in f["evidence"])]
                self.log(f"  incremental: kept {len(kept)} earlier AI findings about unchanged files")
                found += [{**f, "id": ""} for f in kept]
        return found, not_found

    # ------------------------------------------------ phases 3 and 4

    def finish(self, ev: dict, verified: list[dict], inferred: list[dict], not_found: dict, use_model: bool) -> dict:
        cfg = self.cfg
        with self.phase("3 · validation and synthesis"):
            valid, rejected = validate.findings(self.repo, verified + inferred)
            valid = model.assign_ids(valid)
            self.log(f"  {len(valid)} findings kept ({sum(f['kind'] == 'verified' for f in valid)} verified, "
                     f"{sum(f['kind'] == 'inferred' for f in valid)} inferred); {len(rejected)} rejected by the validator")
            util.dump(self.out / "findings" / "findings.json", valid)
            util.dump(self.out / "findings" / "rejected.json", rejected)
            util.dump(self.out / "findings" / "not-found.json", not_found)
            syn = synthesize.deterministic(valid, ev)
            provider = make(cfg) if use_model else None
            if provider:
                better, usage, problems = synthesize.with_model(valid, ev, syn, provider, self.cache / "llm", self.log)
                self.usage.add(usage)
                self.warnings += problems
                if better:
                    better["options"] = better["options"] or syn["options"]
                    syn = better
            agent = self.out / "findings" / "agent" / "synthesis.json"
            if cfg["ai"]["provider"] == "claude-code" and agent.exists():
                data, problems = validate.synthesis(util.load_json(agent, {}), {f["id"] for f in valid})
                if not model.schema_errors("synthesis", data):
                    syn = data
                self.warnings += problems
            util.dump(self.out / "synthesis.json", syn)
        with self.phase("4 · reports"):
            self.reports(ev, valid, rejected, not_found, syn)
        return {"findings": valid, "rejected": rejected, "synthesis": syn}

    def reports(self, ev: dict, findings: list[dict], rejected: list[dict], not_found: dict, syn: dict) -> None:
        cfg = self.cfg
        hist = ev.get("history", {})
        ai = cfg["ai"]
        provider_label = "deterministic tools only (no AI)" if ai["provider"] == "none" else \
            f"{ai['provider']} · {ai['model'] or 'default model'} · effort {ai['effort']}"
        ctx = {"name": cfg["project"]["name"] or self.repo.name, "version": __version__, "date": date.today().isoformat(),
               "evidence": ev, "findings": findings, "rejected": rejected, "not_found": not_found, "synthesis": syn,
               "link_base": links.remote_base(self.repo, hist.get("head")), "diagram": diagrams.containers(ev),
               "provider_label": provider_label}
        tech = markdown.technical(ctx)
        exe = markdown.executive(ctx)
        redact = lambda s: util.redact(s, ["secrets"], self.secret_values)  # noqa: E731 - last line of defense
        (self.out / "technical.md").write_text(redact(tech), encoding="utf-8")
        (self.out / "executive.md").write_text(redact(exe), encoding="utf-8")
        (self.out / "architecture.mmd").write_text(ctx["diagram"] + "\n", encoding="utf-8")
        (self.out / "backlog.csv").write_text(redact(backlog.render(findings)), encoding="utf-8")
        if cfg["output"]["html"]:
            (self.out / "technical.html").write_text(redact(html.convert(tech, f"Technical report: {ctx['name']}")), encoding="utf-8")
            (self.out / "executive.html").write_text(redact(html.convert(exe, f"{ctx['name']}: modernization brief")), encoding="utf-8")
        (self.out / "README.md").write_text(
            f"# Archaeology of {ctx['name']}\n\n"
            "| File | For | What |\n|---|---|---|\n"
            "| [executive.md](executive.md) / executive.html | product and project managers | status, capabilities, risks, options, roadmap |\n"
            "| [technical.md](technical.md) / technical.html | engineers | inventory, architecture, hotspots, every finding with evidence |\n"
            "| [backlog.csv](backlog.csv) | delivery | findings as tickets (Jira / GitHub import) |\n"
            "| [architecture.mmd](architecture.mmd) | everyone | container diagram (Mermaid) |\n"
            "| findings/ · synthesis.json · evidence/ | tools | structured data behind the reports |\n"
            "| [run.json](run.json) | auditors | model, prompt versions, tokens and cost of this run |\n", encoding="utf-8")

    def write_log(self, extra: dict | None = None) -> None:
        cfg = self.cfg
        specs = {s.id: {"version": s.version, "hash": s.hash} for s in load_all("all")}
        log = {
            "tool_version": __version__, "started_at": self.started.isoformat(), "finished_at": datetime.now(timezone.utc).isoformat(),
            "repo": {"path": str(self.repo), "head": util.load_json(self.out / "evidence" / "history.json", {}).get("head")},
            "config": {k: v for k, v in cfg.items() if k != "budget"} | {"budget": cfg["budget"]},
            "provider": {"name": cfg["ai"]["provider"], "model": cfg["ai"]["model"], "effort": cfg["ai"]["effort"]},
            "prompts": specs, "usage": {**self.usage.__dict__, "estimated_usd": self.usage.cost(cfg["budget"]["price_per_mtok"])},
            "phases": self.phases, "warnings": self.warnings, **(extra or {}),
        }
        util.dump(self.out / "run.json", log)


def dig(repo: Path, cfg: dict, out: Path, *, dry_run=False, since=None, assume_yes=False, log=print) -> dict:
    check_paths(repo, out)
    run = Run(repo, cfg, out, log)
    idx, ev = run.evidence()
    verified = rules.run(ev)
    inferred, not_found = run.analysis(idx, ev, dry_run, since, assume_yes)
    util.dump(run.out / "state.json", {"repo": str(run.repo), "config": cfg, "secrets_redaction": "in-memory only"})
    if cfg["ai"]["provider"] == "claude-code" and not dry_run:
        util.dump(run.out / "findings" / "verified.json", verified)
        run.write_log({"next": "agents fill findings/agent/*.json, then run: archaeology finish " + str(run.out)})
        log(f"\nEvidence ready. Agents: follow AGENTS.md, then run `archaeology finish {run.out}`.")
        return {"stage": "agent-tasks"}
    result = run.finish(ev, verified, inferred, not_found, use_model=cfg["ai"]["provider"] in {"anthropic", "ollama"} and not dry_run)
    run.write_log()
    log(f"\nDone. Open {run.out / 'executive.html'} (business) and {run.out / 'technical.html'} (engineering).")
    return result


def finish(out: Path, log=print) -> dict:
    """Ingests findings written by external agents (Claude Code, others) and produces the reports."""
    state = util.load_json(out / "state.json")
    if not state:
        raise Abort(f"{out} has no state.json: run `archaeology evidence` first")
    repo, cfg = Path(state["repo"]), state["config"]
    run = Run(repo, cfg, out, log)
    ev = {p.stem: util.load_json(p) for p in (out / "evidence").glob("*.json")}
    from archaeology.evidence.index import Index as _Index

    _, run.secret_values = secrets.scan(_Index.build(repo, cfg))
    verified = util.load_json(out / "findings" / "verified.json", None) or rules.run(ev)
    inferred, not_found = [], {}
    specs = {s.id: s for s in load_all("all")}
    for path in sorted((out / "findings" / "agent").glob("*.json")):
        if path.stem == "synthesis":
            continue
        data = util.load_json(path, {})
        problems = model.schema_errors("llm-findings", data)
        if problems or path.stem not in specs:
            run.warnings.append(f"{path.name}: ignored ({'; '.join(problems[:3]) or 'unknown spec'})")
            continue
        inferred += [analyze.to_finding(r, specs[path.stem]) for r in data["findings"]]
        if data.get("not_found"):
            not_found[path.stem] = data["not_found"]
    result = run.finish(ev, verified, inferred, not_found, use_model=False)
    run.write_log()
    log(f"\nDone. Open {out / 'executive.html'} (business) and {out / 'technical.html'} (engineering).")
    return result


def rerender(out: Path, log=print) -> None:
    state = util.load_json(out / "state.json")
    if not state:
        raise Abort(f"{out} has no state.json")
    run = Run(Path(state["repo"]), state["config"], out, log)
    ev = {p.stem: util.load_json(p) for p in (out / "evidence").glob("*.json")}
    run.reports(ev, util.load_json(out / "findings" / "findings.json", []), util.load_json(out / "findings" / "rejected.json", []),
                util.load_json(out / "findings" / "not-found.json", {}), util.load_json(out / "synthesis.json"))
    log(f"Reports re-rendered in {out}")
