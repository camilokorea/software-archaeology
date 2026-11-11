"""Phase 2: each spec reads its evidence and a sample of files and returns findings. Results are cached per spec
by the hash of everything that went into the prompt, so re-runs and resumed runs only pay for what changed."""

from __future__ import annotations

import json
from pathlib import Path

from archaeology import model, util
from archaeology.evidence.index import Index
from archaeology.llm import FatalProviderError, Provider, ProviderError, Usage
from archaeology.paths import PROMPTS
from archaeology.specs import Spec
from archaeology import context


def system_prompt() -> str:
    return (PROMPTS / "analyst-system.md").read_text(encoding="utf-8")


def plan(specs: list[Spec], idx: Index, evidence: dict, cfg: dict, secrets: set[str], only: set[str] | None) -> list[dict]:
    """The prompts that would be sent, with their size: used for the estimate, the dry run and the cache key."""
    sys_prompt = system_prompt()
    out = []
    for spec in specs:
        if spec.synthesis:
            continue
        for part, scope in partitions(idx, evidence, only):
            user, files = context.build(spec, idx, evidence, cfg, secrets, scope)
            if part:
                user = f"(This run covers the component `{part}` of a larger repository; cite only its files.)\n\n" + user
            key = util.sha(sys_prompt + user + json.dumps(model.schema("llm-findings")) + str(cfg["ai"]["model"]) + cfg["ai"]["provider"])
            out.append({"spec": spec, "part": part, "user": user, "files": files, "key": key,
                        "input_tokens": util.estimate_tokens(sys_prompt + user), "output_tokens": 3000})
    return out


def partitions(idx: Index, evidence: dict, only: set[str] | None, max_parts: int = 6) -> list[tuple[str | None, set[str] | None]]:
    """Small repositories are analyzed whole. Large ones and monorepos are analyzed per component (the biggest
    ones first), so each call sees a coherent part instead of a thin sample of everything."""
    inv = evidence.get("inventory", {})
    comps = [c for c in inv.get("components", []) if c["path"] != "." and c["kind"] != "tests"]
    if inv.get("size_class") in {"small", "medium"} or len(comps) < 2:
        return [(None, only)]
    sizes = {c["path"]: sum(f.code_lines for f in idx.files if f.path.startswith(c["path"] + "/")) for c in comps}
    parts = []
    for path in sorted(sizes, key=lambda p: -sizes[p])[:max_parts]:
        files = {f.path for f in idx.files if f.path.startswith(path + "/")}
        parts.append((path, files & only if only is not None else files))
    return parts


def estimate(plans: list[dict], prices: dict) -> dict:
    tin = sum(p["input_tokens"] for p in plans)
    tout = sum(p["output_tokens"] for p in plans) + 6000  # synthesis
    return {"calls": len(plans) + 1, "input_tokens": tin, "output_tokens": tout,
            "usd": round(tin / 1e6 * prices["input"] + tout / 1e6 * prices["output"], 3)}


def to_finding(raw: dict, spec: Spec) -> dict:
    area = raw["area"] if raw["area"] in model.AREA_PREFIX else spec.areas[0]
    return model.finding(
        spec=spec.id, area=area, title=raw["title"], severity=raw["severity"], kind="inferred",
        confidence=raw["confidence"], effort=raw["effort"],
        evidence=[model.ev(e["file"], max(0, int(e.get("line") or 0)), e.get("excerpt") or None, f"spec:{spec.id}") for e in raw["evidence"]],
        technical_impact=raw["technical_impact"], business_impact=raw["business_impact"],
        recommendation=raw["recommendation"], refs=raw.get("refs", []))


def run(plans: list[dict], provider: Provider, cache_dir: Path, budget_usd: float, prices: dict, log) -> tuple[list[dict], dict, Usage, list[str]]:
    findings: list[dict] = []
    not_found: dict[str, list[str]] = {}
    usage = Usage()
    warnings: list[str] = []
    schema = model.schema("llm-findings")
    sys_prompt = system_prompt()
    for p in plans:
        spec: Spec = p["spec"]
        label = spec.id + (f"@{p['part']}" if p.get("part") else "")
        cached = util.load_json(cache_dir / f"spec-{spec.id}-{p['key']}.json")
        if cached is None:
            projected = usage.cost(prices) + (p["input_tokens"] / 1e6 * prices["input"] + p["output_tokens"] / 1e6 * prices["output"])
            if projected > budget_usd:
                warnings.append(f"{label}: skipped, it would exceed the budget of ${budget_usd}")
                log(f"  · {label}: skipped (budget)")
                continue
            log(f"  · {label}: asking {provider.name}/{provider.model} ({p['input_tokens']:,} tokens, {len(p['files'])} files)")
            try:
                data, used = provider.complete(sys_prompt, p["user"], schema, spec.id)
            except FatalProviderError as e:
                warnings.append(str(e))
                log(f"  · {spec.id}: {e}. Stopping AI analysis; the reports keep the verified findings.")
                break
            except ProviderError as e:
                warnings.append(str(e))
                log(f"  · {spec.id}: failed ({e}); continuing with the other specs")
                continue
            usage.add(used)
            util.dump(cache_dir / f"spec-{spec.id}-{p['key']}.json", {"data": data, "usage": used.__dict__})
        else:
            data = cached["data"]
            log(f"  · {label}: reused from cache")
        problems = model.schema_errors("llm-findings", data)
        if problems:
            warnings.append(f"{spec.id}: answer did not match the schema: {problems[:3]}")
            continue
        findings += [to_finding(r, spec) for r in data["findings"]]
        if data.get("not_found"):
            not_found.setdefault(label, []).extend(data["not_found"])
    return findings, not_found, usage, warnings
