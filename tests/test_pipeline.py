import json

import pytest

from archaeology import config, model, pipeline, util, validate
from archaeology.llm import Provider, Usage


def test_validator_rejects_invented_citations(legacy_repo):
    good = model.finding(spec="security", area="security", title="SQL built from the request", severity="high",
                         evidence=[model.ev("LegacyShop.Web/Controllers/OrdersController.cs", 12, 'var sql = "SELECT * FROM Orders WHERE Id = " + id;')],
                         technical_impact="String concatenation of a route parameter into SQL.", business_impact="Someone could read other customers' orders.",
                         recommendation="Use a parameterized query.", kind="inferred")
    wrong_line = json.loads(json.dumps(good))
    wrong_line["evidence"][0]["excerpt"] = "DROP TABLE Customers"
    missing = json.loads(json.dumps(good))
    missing["evidence"][0]["file"] = "LegacyShop.Web/Controllers/PaymentsController.cs"
    too_far = json.loads(json.dumps(good))
    too_far["evidence"][0]["line"] = 999
    for f, n in ((good, 1), (wrong_line, 2), (missing, 3), (too_far, 4)):
        f["id"] = f"SEC-00{n}"
    valid, rejected = validate.findings(legacy_repo, [good, wrong_line, missing, too_far])
    assert [f["id"] for f in valid] == ["SEC-001"]
    reasons = " ".join(" ".join(r["reasons"]) for r in rejected)
    assert "not at that line" in reasons and "does not exist" in reasons and "only" in reasons


def test_synthesis_drops_unsupported_statements():
    data = {"executive_summary": {"status": "red", "headline": "h", "recommendation": "r",
                                  "points": [{"text": "supported", "findings": ["SEC-001"]}, {"text": "made up", "findings": ["SEC-999"]}]},
            "capabilities": [], "risks": [{"statement": "x", "impact": 3, "probability": 3, "findings": []}], "options": [],
            "roadmap": [], "glossary": [], "faq": []}
    out, dropped = validate.synthesis(data, {"SEC-001"})
    assert [p["text"] for p in out["executive_summary"]["points"]] == ["supported"]
    assert out["risks"] == [] and dropped


def test_dig_without_ai_writes_both_reports(legacy_repo, tmp_path):
    cfg = config.load(None, {"network": {"enabled": False}})
    out = tmp_path / "out"
    result = pipeline.dig(legacy_repo, cfg, out, log=lambda *_: None)
    for name in ("executive.md", "executive.html", "technical.md", "technical.html", "backlog.csv", "architecture.mmd", "run.json", "synthesis.json"):
        assert (out / name).exists(), name
    tech = (out / "technical.md").read_text()
    exe = (out / "executive.md").read_text()
    assert "S3cr3tP4ss!" not in tech + exe + (out / "backlog.csv").read_text() + json.dumps(util.load_json(out / "findings" / "findings.json"))
    assert "Ana" not in tech and "ana@example.com" not in tech
    assert "## Status: 🔴 Red" in exe and "(technical.md#" in exe
    ids = {f["id"] for f in result["findings"]}
    for p in result["synthesis"]["executive_summary"]["points"]:
        assert set(p["findings"]) <= ids
    assert sum(o["recommended"] for o in result["synthesis"]["options"]) == 1
    assert not model.schema_errors("synthesis", result["synthesis"])
    log = util.load_json(out / "run.json")
    assert log["prompts"]["security"]["version"] == "1.0.0" and log["usage"]["calls"] == 0


def test_refuses_to_write_inside_the_repo(legacy_repo):
    cfg = config.load(None, {"network": {"enabled": False}})
    with pytest.raises(pipeline.Abort):
        pipeline.dig(legacy_repo, cfg, legacy_repo / "out", log=lambda *_: None)


class FakeModel(Provider):
    """Answers like a model would: one finding with a real citation and one with an invented one."""

    def __init__(self):
        super().__init__(name="fake", model="fake-1")
        self.prompts = []

    def complete(self, system, user, schema, label):
        self.prompts.append(user)
        if label == "synthesis":
            raise __import__("archaeology.llm", fromlist=["ProviderError"]).ProviderError("no synthesis in the fake")
        if label != "security":
            return {"findings": [], "not_found": [f"{label}: nothing to add"]}, Usage(100, 10, 1)
        return {"findings": [
            {"area": "security", "title": "SQL query built from the route parameter", "severity": "high", "confidence": "high",
             "evidence": [{"file": "LegacyShop.Web/Controllers/OrdersController.cs", "line": 12, "excerpt": "var sql = \"SELECT * FROM Orders WHERE Id = \" + id;"}],
             "technical_impact": "SQL injection through the id route value.", "business_impact": "Anyone could read or change orders that are not theirs.",
             "effort": "S", "recommendation": "Use SqlParameter for id.", "refs": ["OWASP A03:2021", "CWE-89"]},
            {"area": "security", "title": "Admin panel without authentication", "severity": "critical", "confidence": "high",
             "evidence": [{"file": "LegacyShop.Web/Controllers/AdminController.cs", "line": 5, "excerpt": "public class AdminController"}],
             "technical_impact": "Invented.", "business_impact": "Invented for the test.", "effort": "S", "recommendation": "Invented, must be rejected.", "refs": []},
        ], "not_found": ["No password hashing code in the sample"]}, Usage(1000, 200, 1)


def test_ai_findings_are_validated_redacted_and_cached(legacy_repo, tmp_path, monkeypatch):
    fake = FakeModel()
    monkeypatch.setattr(pipeline, "make", lambda cfg: fake)
    cfg = config.load(None, {"network": {"enabled": False}, "ai": {"provider": "anthropic"}})
    out = tmp_path / "ai"
    result = pipeline.dig(legacy_repo, cfg, out, log=lambda *_: None)
    titles = [f["title"] for f in result["findings"]]
    assert "SQL query built from the route parameter" in titles
    assert "Admin panel without authentication" not in titles
    assert any("AdminController.cs" in json.dumps(r) for r in result["rejected"])
    assert all("S3cr3tP4ss!" not in p for p in fake.prompts), "secrets must be redacted before reaching the model"
    assert "[REDACTED-SECRET]" in "".join(fake.prompts)
    inferred = next(f for f in result["findings"] if f["kind"] == "inferred")
    assert inferred["spec"] == "security"
    calls = len(fake.prompts)
    pipeline.dig(legacy_repo, cfg, out, log=lambda *_: None)
    assert len(fake.prompts) == calls + 1, "only the synthesis is asked again; specs come from the cache"
    tech = (out / "technical.md").read_text()
    assert "🤖 inferred" in tech and "Checked and not found" in tech


def test_budget_stops_before_calling(legacy_repo, tmp_path, monkeypatch):
    fake = FakeModel()
    monkeypatch.setattr(pipeline, "make", lambda cfg: fake)
    cfg = config.load(None, {"network": {"enabled": False}, "ai": {"provider": "anthropic"}, "budget": {"max_usd": 0.0001}})
    with pytest.raises(pipeline.Abort):
        pipeline.dig(legacy_repo, cfg, tmp_path / "b", log=lambda *_: None)
    assert fake.prompts == []


def test_send_source_false_keeps_code_out(legacy_repo, tmp_path, monkeypatch):
    fake = FakeModel()
    monkeypatch.setattr(pipeline, "make", lambda cfg: fake)
    cfg = config.load(None, {"network": {"enabled": False}, "ai": {"provider": "anthropic"}, "privacy": {"send_source": False}})
    pipeline.dig(legacy_repo, cfg, tmp_path / "p", log=lambda *_: None)
    assert all("public ActionResult" not in p for p in fake.prompts)


def test_agent_handoff(legacy_repo, tmp_path):
    cfg = config.load(None, {"network": {"enabled": False}, "ai": {"provider": "claude-code"}})
    out = tmp_path / "agent"
    pipeline.dig(legacy_repo, cfg, out, log=lambda *_: None)
    assert (out / "agent-tasks" / "security.md").exists()
    (out / "findings" / "agent").mkdir(parents=True, exist_ok=True)
    util.dump(out / "findings" / "agent" / "security.json", {"findings": [{
        "area": "security", "title": "SQL query built from the route parameter", "severity": "high", "confidence": "high",
        "evidence": [{"file": "LegacyShop.Web/Controllers/OrdersController.cs", "line": 12, "excerpt": "var sql ="}],
        "technical_impact": "SQL injection.", "business_impact": "Orders of other customers could be read.", "effort": "S",
        "recommendation": "Parameterize the query.", "refs": []}], "not_found": []})
    result = pipeline.finish(out, log=lambda *_: None)
    assert any(f["kind"] == "inferred" for f in result["findings"])
    assert (out / "executive.html").exists()


def test_no_credit_stops_after_the_first_call(legacy_repo, tmp_path, monkeypatch):
    from archaeology.llm import FatalProviderError

    class Broke(FakeModel):
        def complete(self, system, user, schema, label):
            self.prompts.append(label)
            raise FatalProviderError("no credit")

    broke = Broke()
    monkeypatch.setattr(pipeline, "make", lambda cfg: broke)
    cfg = config.load(None, {"network": {"enabled": False}, "ai": {"provider": "anthropic"}})
    result = pipeline.dig(legacy_repo, cfg, tmp_path / "nc", log=lambda *_: None)
    assert broke.prompts[0] != "synthesis" and broke.prompts.count(broke.prompts[0]) == 1
    assert len([p for p in broke.prompts if p != "synthesis"]) == 1
    assert result["findings"] and all(f["kind"] == "verified" for f in result["findings"])
