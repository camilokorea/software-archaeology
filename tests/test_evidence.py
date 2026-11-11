from archaeology import rules
from archaeology.evidence import code, dependencies, history, inventory, secrets, surface
from archaeology.evidence.index import Index


def test_inventory_frameworks_and_components(legacy_repo, cfg):
    idx = Index.build(legacy_repo, cfg)
    inv = inventory.summarize(idx)
    names = {f["name"] for f in inv["frameworks"]}
    assert {"AngularJS 1.x", ".NET Framework", "jQuery"} <= names
    assert any(c["path"] == "LegacyShop.Web" for c in inv["components"])
    assert inv["code_lines"] > 40


def test_dependencies_and_runtimes(legacy_repo, cfg):
    deps = dependencies.scan(Index.build(legacy_repo, cfg))
    got = {(d["ecosystem"], d["name"], d["version"]) for d in deps["dependencies"]}
    assert ("NuGet", "Newtonsoft.Json", "9.0.1") in got
    assert ("npm", "angular", "1.5.8") in got
    assert {"product": "dotnetfx", "version": "4.5.2"}.items() <= deps["runtimes"][0].items()


def test_secrets_are_found_but_never_stored(legacy_repo, cfg):
    found, values = secrets.scan(Index.build(legacy_repo, cfg))
    hit = next(s for s in found if s["rule"] == "connection-string-password")
    assert hit["file"] == "LegacyShop.Web/web.config" and hit["line"] == 4
    assert "S3cr3tP4ss!" not in str(found)
    assert "S3cr3tP4ss!" in values


def test_history_is_pseudonymized_and_finds_hotspots(legacy_repo, cfg):
    idx = Index.build(legacy_repo, cfg)
    h = history.scan(legacy_repo, {f.path for f in idx.files})
    assert h["available"] and h["contributors"] == 2
    assert {c["author"] for c in h["top_contributors"]} == {"Dev 1", "Dev 2"}
    assert "Ana" not in str(h)
    hot = code.hotspots(code.complexity(idx), h)
    assert hot[0]["path"] == "LegacyShop.Web/Controllers/OrdersController.cs"


def test_surface(legacy_repo, cfg):
    idx = Index.build(legacy_repo, cfg)
    api = surface.endpoints(idx)
    assert any(a["path"] == "orders/checkout" and a["framework"] == "ASP.NET" for a in api)
    assert any(a["path"] == "/orders" and a["side"] == "client" for a in api)
    db = surface.database(idx)
    proc = next(o for o in db["objects"] if o["name"] == "dbo.ApproveOrder")
    assert proc["type"] == "PROCEDURE" and proc["logic_markers"] >= 5
    assert any(s["name"] == "SQL Server" for s in db["stores"])
    assert surface.tests(idx)["test_files"] == 0
    assert surface.devops(idx)["observability"] == ["log4net"]
    assert any("payments.example-bank.com" in h["endpoint"] for h in surface.externals(idx)["hosts"])


def test_rules_produce_verified_findings(legacy_repo, cfg):
    idx = Index.build(legacy_repo, cfg)
    h = history.scan(legacy_repo, {f.path for f in idx.files})
    cx = code.complexity(idx)
    found, _ = secrets.scan(idx)
    ev = {"inventory": inventory.summarize(idx), "history": h, "secrets": found, "complexity": cx,
          "hotspots": code.hotspots(cx, h), "tests": surface.tests(idx), "devops": surface.devops(idx),
          "database": surface.database(idx),
          "eol": [{"product": "angularjs", "name": "angular", "version": "1.5.8", "cycle": "1.5", "eol": "2021-12-31",
                   "is_eol": True, "newest_cycle": "1.8", "file": "LegacyShop.Web/Scripts/app/package.json", "line": 3,
                   "source": "https://endoflife.date/angularjs"}]}
    titles = [f["title"] for f in rules.run(ev)]
    assert any("past its end of life" in t for t in titles)
    assert any("connection string" in t.lower() for t in titles)
    assert "No automated tests were found" in titles
    assert any("database routines contain business logic" in t for t in titles)
    assert all(f["kind"] == "verified" for f in rules.run(ev))


def test_secret_rules_ignore_code_and_catch_config(tmp_path, cfg):
    (tmp_path / "src").mkdir()
    (tmp_path / "src/Login.java").write_text('final char[] password = System.getenv("MVNW_PASSWORD").toCharArray();\n')
    (tmp_path / "src/Sign.cbl").write_text("           IF SEC-USR-PWD = WS-USER-PWD\n")
    (tmp_path / "src/AccountMapper.xml").write_text("AND SIGNON.PASSWORD = #{password}\n")
    (tmp_path / "app.properties").write_text("spring.datasource.password=Hunter2Real!\nspring.datasource.url=jdbc:mysql://db/shop?user=a&password=Jdbc1234Pw\nother.password=${DB_PASSWORD}\n")
    (tmp_path / "Web.config").write_text('<add connectionString="Data Source=db;Initial Catalog=x;User Id=u;Password=Conn5tr1ng;" />\n')
    found, values = secrets.scan(Index.build(tmp_path, cfg))
    files = {(s["file"], s["line"]) for s in found}
    assert ("src/Login.java", 1) not in files and ("src/Sign.cbl", 1) not in files and ("src/AccountMapper.xml", 1) not in files
    assert {"Hunter2Real!", "Jdbc1234Pw", "Conn5tr1ng"} <= values
    assert not any("DB_PASSWORD" in v for v in values)


def test_validator_accepts_dot_folders(tmp_path):
    from archaeology import validate

    (tmp_path / ".github/workflows").mkdir(parents=True)
    (tmp_path / ".github/workflows/ci.yml").write_text("on: push\n")
    assert validate.check_evidence(tmp_path, {"file": ".github/workflows/ci.yml", "line": 1, "excerpt": "on: push"}, {}) is None
    assert validate.check_evidence(tmp_path, {"file": "./.github/workflows/ci.yml", "line": 0}, {}) is None
