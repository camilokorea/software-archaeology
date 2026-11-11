"""A small synthetic legacy application, built fresh for each test session (it is invented, not a real project)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

FILES = {
    "README.md": "# Legacy Shop\n\nOpen LegacyShop.sln in Visual Studio 2015 and press F5.\n",
    "LegacyShop.Web/LegacyShop.Web.csproj": """<Project ToolsVersion="14.0">
  <PropertyGroup>
    <TargetFrameworkVersion>v4.5.2</TargetFrameworkVersion>
  </PropertyGroup>
  <ItemGroup>
    <Reference Include="System.Web.Mvc" />
  </ItemGroup>
</Project>
""",
    "LegacyShop.Web/packages.config": """<?xml version="1.0" encoding="utf-8"?>
<packages>
  <package id="Newtonsoft.Json" version="9.0.1" targetFramework="net452" />
  <package id="EntityFramework" version="6.1.3" targetFramework="net452" />
  <package id="log4net" version="2.0.8" targetFramework="net452" />
</packages>
""",
    "LegacyShop.Web/web.config": """<?xml version="1.0"?>
<configuration>
  <connectionStrings>
    <add name="Shop" connectionString="Server=db01;Database=Shop;User Id=shop;Password=S3cr3tP4ss!;" providerName="System.Data.SqlClient" />
  </connectionStrings>
  <appSettings>
    <add key="PaymentGateway" value="https://payments.example-bank.com/api" />
  </appSettings>
</configuration>
""",
    "LegacyShop.Web/Controllers/OrdersController.cs": """using System.Web.Mvc;
using System.Data.SqlClient;

namespace LegacyShop.Web.Controllers
{
    public class OrdersController : Controller
    {
        [HttpGet]
        [Route("orders/{id}")]
        public ActionResult Details(string id)
        {
            var sql = "SELECT * FROM Orders WHERE Id = " + id;
            using (var cn = new SqlConnection("Server=db01"))
            {
                if (id == null) { return HttpNotFound(); }
                return View();
            }
        }

        [HttpPost]
        [Route("orders/checkout")]
        public ActionResult Checkout(decimal total)
        {
            if (total > 1000 && total < 5000) { total = total * 0.95m; }
            else if (total >= 5000) { total = total * 0.9m; }
            return Json(total);
        }
    }
}
""",
    "LegacyShop.Web/Controllers/CustomersController.cs": """using System.Web.Mvc;

namespace LegacyShop.Web.Controllers
{
    public class CustomersController : Controller
    {
        [HttpGet]
        [Route("customers/{id}")]
        public ActionResult Profile(int id) { return View(); }
    }
}
""",
    "LegacyShop.Web/Scripts/app/package.json": """{
  "name": "legacy-shop-ui",
  "dependencies": { "angular": "1.5.8", "jquery": "1.12.4" }
}
""",
    "LegacyShop.Web/Scripts/app/app.js": """angular.module('shop', ['ngRoute']).config(function ($routeProvider) {
  $routeProvider.when('/orders', { templateUrl: 'orders.html' }).when('/cart', { templateUrl: 'cart.html' });
});
""",
    "Database/procedures.sql": """CREATE TABLE Orders (Id INT, Total DECIMAL(10,2), Status VARCHAR(20));
GO
CREATE PROCEDURE dbo.ApproveOrder @OrderId INT
AS
BEGIN
  IF (SELECT Total FROM Orders WHERE Id = @OrderId) > 10000
  BEGIN
    UPDATE Orders SET Status = 'REVIEW' WHERE Id = @OrderId;
  END
  ELSE
  BEGIN
    UPDATE Orders SET Status = 'APPROVED' WHERE Id = @OrderId;
    INSERT INTO AuditLog (OrderId, Action) VALUES (@OrderId, 'AUTO');
  END
  IF @@ERROR <> 0 RAISERROR('fail', 16, 1);
END
""",
}


def _git(repo: Path, *args: str, author: str = "Ana") -> None:
    env = {"GIT_AUTHOR_NAME": author, "GIT_AUTHOR_EMAIL": f"{author.lower()}@example.com", "GIT_COMMITTER_NAME": author,
           "GIT_COMMITTER_EMAIL": f"{author.lower()}@example.com", "PATH": "/usr/bin:/bin", "HOME": str(repo)}
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, env=env)


@pytest.fixture(scope="session")
def legacy_repo(tmp_path_factory) -> Path:
    repo = tmp_path_factory.mktemp("legacy-shop")
    _git(repo, "init", "-q", "-b", "main")
    for i, (path, content) in enumerate(FILES.items()):
        target = repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        _git(repo, "add", path)
        _git(repo, "commit", "-q", "-m", f"add {path}", author="Ana" if i % 4 else "Beto")
    # The checkout controller keeps changing: it becomes a hotspot.
    ctl = repo / "LegacyShop.Web/Controllers/OrdersController.cs"
    for n in range(4):
        ctl.write_text(ctl.read_text() + f"\n// tweak {n}\n")
        _git(repo, "commit", "-qam", f"tweak checkout {n}")
    return repo


@pytest.fixture
def cfg():
    from archaeology import config

    return config.load(None, {"network": {"enabled": False}})
