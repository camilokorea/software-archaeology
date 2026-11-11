"""The outside of the system: HTTP endpoints, client routes, database objects, tests, build and deploy files,
and external systems referenced in configuration."""

from __future__ import annotations

import re
from collections import Counter

from archaeology.evidence.index import Index

ENDPOINT_PATTERNS = [
    ("ASP.NET", "server", re.compile(r"\[(Http(?:Get|Post|Put|Delete|Patch))(?:\(\s*\"([^\"]*)\"\s*\))?\]")),
    ("ASP.NET", "server", re.compile(r"\[Route\(\s*\"([^\"]+)\"\s*\)\]")),
    ("Express", "server", re.compile(r"\b(?:app|router|server)\.(get|post|put|delete|patch|all)\(\s*['\"`]([^'\"`]+)")),
    ("Spring", "server", re.compile(r"@(Get|Post|Put|Delete|Patch|Request)Mapping\(\s*(?:value\s*=\s*|path\s*=\s*)?\{?\s*\"([^\"]*)\"")),
    ("JAX-RS", "server", re.compile(r"@Path\(\s*\"([^\"]+)\"")),
    ("Stripes", "server", re.compile(r"@UrlBinding\(\s*\"([^\"]+)\"")),
    ("Flask/FastAPI", "server", re.compile(r"@(?:app|router|bp|blueprint)\.(route|get|post|put|delete|patch)\(\s*['\"]([^'\"]+)")),
    ("Django", "server", re.compile(r"\b(?:path|re_path|url)\(\s*r?['\"]([^'\"]*)['\"]")),
    ("Laravel", "server", re.compile(r"Route::(get|post|put|delete|patch|any)\(\s*['\"]([^'\"]+)")),
    ("AngularJS", "client", re.compile(r"\.when\(\s*['\"](/[^'\"]*)['\"]")),
    ("AngularJS ui-router", "client", re.compile(r"\.state\(\s*['\"]([\w.]+)['\"]")),
    ("Angular", "client", re.compile(r"\bpath:\s*['\"]([^'\"]*)['\"]")),
    ("CICS", "server", re.compile(r"EXEC\s+CICS\s+(SEND\s+MAP|RECEIVE\s+MAP|LINK|XCTL)\b[^.]*?(?:PROGRAM|MAP)\s*\(\s*'?([\w-]+)", re.S)),
]


def endpoints(idx: Index) -> list[dict]:
    out = []
    for f in idx.files:
        if not f.language or f.language in {"CSS", "SCSS", "LESS", "HTML"}:
            continue
        text = idx.text(f.path)
        for framework, side, pattern in ENDPOINT_PATTERNS:
            if framework == "Angular" and f.language != "TypeScript":
                continue
            if framework == "Django" and f.language != "Python":
                continue
            for m in pattern.finditer(text):
                groups = [g for g in m.groups() if g is not None]
                verb_only = framework == "ASP.NET" and len(groups) == 1 and groups[0].lower().startswith("http")
                method = groups[0].upper().replace("HTTP", "") if len(groups) > 1 or verb_only else None
                path = None if verb_only else groups[-1]
                out.append({"framework": framework, "side": side, "method": method, "path": path, "file": f.path,
                            "line": idx.line_of(f.path, m.start())})
    for f in idx.by_suffix(".aspx", ".asmx", ".svc", ".jsp", ".cfm", ".asp", ".php"):
        out.append({"framework": f.language or "page", "side": "server", "method": None, "path": "/" + f.path, "file": f.path, "line": 0})
    return out[:2000]


SQL_OBJECT = re.compile(r"\bCREATE\s+(?:OR\s+(?:REPLACE|ALTER)\s+)?(TABLE|VIEW|PROCEDURE|PROC|FUNCTION|TRIGGER|PACKAGE(?:\s+BODY)?)\s+([\[\]\w.\"`]+)", re.I)
LOGIC = re.compile(r"\b(IF|ELSE|WHILE|CURSOR|CASE|UPDATE|INSERT|DELETE|MERGE|LOOP|RAISERROR|THROW|EXCEPTION)\b", re.I)


def database(idx: Index) -> dict:
    objects, entities, stores = [], [], Counter()
    for f in idx.files:
        if f.language not in {"SQL", "PL/SQL"}:
            continue
        text = idx.text(f.path)
        matches = list(SQL_OBJECT.finditer(text))
        for i, m in enumerate(matches):
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            body = text[m.start():end]
            kind = m.group(1).upper().replace("PROC", "PROCEDURE").replace("PROCEDUREEDURE", "PROCEDURE")
            objects.append({"type": kind, "name": m.group(2).strip('[]"`'), "file": f.path, "line": idx.line_of(f.path, m.start()),
                            "lines": body.count("\n") + 1, "logic_markers": len(LOGIC.findall(body)) if kind != "TABLE" else 0})
    entity_patterns = [re.compile(r"DbSet<(\w+)>"), re.compile(r"@Entity\b[\s\S]{0,200}?class\s+(\w+)"),
                       re.compile(r"\[Table\(\s*\"(\w+)\""), re.compile(r"<mapper\s+namespace=\"([\w.]+)\""),
                       re.compile(r"class\s+(\w+)\(models\.Model\)")]
    for f in idx.files:
        if f.language not in {"C#", "Java", "Python", "Kotlin"} and not f.path.endswith(".xml"):
            continue
        text = idx.text(f.path)
        for p in entity_patterns:
            for m in p.finditer(text):
                entities.append({"name": m.group(1), "file": f.path, "line": idx.line_of(f.path, m.start())})
    markers = {"SQL Server": r"SqlConnection|System\.Data\.SqlClient|Microsoft\.Data\.SqlClient|sqlserver|mssql",
               "Oracle": r"Oracle\.|oracle\.jdbc|OracleConnection", "MySQL": r"mysql", "PostgreSQL": r"Npgsql|postgres",
               "MongoDB": r"MongoClient|mongodb://", "DB2": r"\bDB2\b|com\.ibm\.db2", "SQLite": r"sqlite",
               "VSAM": r"\bVSAM\b|ORGANIZATION\s+IS\s+INDEXED", "HSQLDB": r"hsqldb", "Redis": r"redis"}
    for f in idx.files:
        if not f.language and not f.path.lower().endswith((".config", ".xml", ".json", ".properties", ".yml", ".yaml")):
            continue
        text = idx.text(f.path)
        for name, pattern in markers.items():
            if re.search(pattern, text, re.I):
                stores[name] += 1
    return {"objects": objects[:2000], "entities": entities[:1000],
            "stores": [{"name": n, "files": c} for n, c in stores.most_common()],
            "migrations": sorted({f.path.rsplit("/", 1)[0] for f in idx.files if re.search(r"(^|/)(migrations?|db/migrate|flyway|liquibase)(/|$)", f.path, re.I)})[:50]}


TEST_PATH = re.compile(r"(^|/)(tests?|__tests__|spec|specs|src/test)(/|$)|(Tests?|Spec)\.(cs|java|kt|ts|js|py|rb|php)$|\.(spec|test)\.(ts|js|tsx|jsx)$|(^|/)test_\w+\.py$|_test\.(go|py|rb)$", re.I)
TEST_FRAMEWORKS = {"xUnit": r"\bxunit\b", "NUnit": r"\bnunit\b", "MSTest": r"MSTest|Microsoft\.VisualStudio\.TestTools",
                   "JUnit": r"junit", "TestNG": r"testng", "Jest": r"\bjest\b", "Jasmine": r"jasmine", "Karma": r"karma",
                   "Mocha": r"\bmocha\b", "pytest": r"pytest", "unittest": r"import unittest", "PHPUnit": r"phpunit",
                   "RSpec": r"rspec", "Cypress": r"cypress", "Selenium": r"selenium", "Protractor": r"protractor"}


def tests(idx: Index) -> dict:
    test_files = [f for f in idx.source() if TEST_PATH.search(f.path)]
    test_lines = sum(f.code_lines for f in test_files)
    src_lines = sum(f.code_lines for f in idx.source() if f not in test_files)
    manifests = " ".join(idx.text(f.path) for f in idx.files if f.path.rsplit("/", 1)[-1].lower() in
                         {"package.json", "pom.xml", "packages.config", "build.gradle", "requirements.txt", "composer.json"}
                         or f.path.endswith(".csproj"))[:2_000_000]
    sample = " ".join(idx.text(f.path)[:3000] for f in test_files[:50])
    frameworks = [n for n, p in TEST_FRAMEWORKS.items() if re.search(p, manifests + sample, re.I)]
    return {"test_files": len(test_files), "test_code_lines": test_lines, "source_code_lines": src_lines,
            "ratio": round(test_lines / max(1, src_lines), 3), "frameworks": frameworks,
            "examples": [f.path for f in test_files[:15]]}


def devops(idx: Index) -> dict:
    ci_patterns = {"GitHub Actions": r"^\.github/workflows/.+\.ya?ml$", "Azure Pipelines": r"(^|/)azure-pipelines[^/]*\.ya?ml$",
                   "Jenkins": r"(^|/)Jenkinsfile$", "GitLab CI": r"(^|/)\.gitlab-ci\.yml$", "Travis CI": r"(^|/)\.travis\.yml$",
                   "Bitbucket Pipelines": r"(^|/)bitbucket-pipelines\.yml$", "CircleCI": r"^\.circleci/"}
    ci = [{"system": n, "file": f.path} for f in idx.files for n, p in ci_patterns.items() if re.search(p, f.path, re.I)]
    dockerfiles = []
    for f in idx.files:
        if re.search(r"(^|/)Dockerfile[^/]*$", f.path, re.I) or f.path.lower().endswith(".dockerfile"):
            text = idx.text(f.path)
            bases = [(m.group(1), idx.line_of(f.path, m.start())) for m in re.finditer(r"^\s*FROM\s+(\S+)", text, re.M | re.I)]
            dockerfiles.append({"file": f.path, "base_images": [{"image": b, "line": l} for b, l in bases]})
    compose = [f.path for f in idx.files if re.search(r"(^|/)(docker-)?compose[^/]*\.ya?ml$", f.path, re.I)]
    k8s = [f.path for f in idx.files if f.path.endswith((".yaml", ".yml")) and re.search(r"^\s*kind:\s*(Deployment|Service|StatefulSet|Ingress|CronJob)\b", idx.text(f.path), re.M)]
    iac = {"Terraform": [f.path for f in idx.by_suffix(".tf")][:20], "Bicep": [f.path for f in idx.by_suffix(".bicep")][:20],
           "CloudFormation": [f.path for f in idx.files if f.path.endswith((".yaml", ".yml", ".json")) and "AWSTemplateFormatVersion" in idx.text(f.path)][:20],
           "Helm": sorted({f.path.rsplit("/", 1)[0] for f in idx.by_name("Chart.yaml")})[:20]}
    obs_markers = {"log4net": r"log4net", "Serilog": r"serilog", "NLog": r"\bnlog\b", "log4j": r"log4j", "Logback": r"logback",
                   "SLF4J": r"slf4j", "winston": r"winston", "Application Insights": r"applicationinsights", "OpenTelemetry": r"opentelemetry",
                   "Prometheus": r"prometheus", "Sentry": r"sentry", "New Relic": r"newrelic", "Datadog": r"datadog"}
    blob = " ".join(idx.text(f.path) for f in idx.files if f.path.rsplit("/", 1)[-1].lower() in
                    {"package.json", "pom.xml", "packages.config", "build.gradle", "requirements.txt", "web.config", "app.config"}
                    or f.path.endswith(".csproj"))
    observability = [n for n, p in obs_markers.items() if re.search(p, blob, re.I)]
    return {"ci": ci, "dockerfiles": dockerfiles, "compose": compose, "kubernetes": k8s[:50],
            "iac": {k: v for k, v in iac.items() if v}, "observability": observability}


URL = re.compile(r"""(?i)\b(https?|amqp|amqps|jdbc:[a-z]+|mongodb|redis|ftp|sftp|ldap|smtp)://([A-Za-z0-9.\-_]+)""")
QUEUES = {"RabbitMQ": r"rabbitmq|amqp://", "Kafka": r"kafka", "MSMQ": r"msmq|System\.Messaging", "Azure Service Bus": r"servicebus",
          "AWS SQS": r"\bsqs\b", "IBM MQ": r"\bIBM ?MQ\b|com\.ibm\.mq|MQSeries", "ActiveMQ": r"activemq"}


def externals(idx: Index) -> dict:
    hosts: Counter = Counter()
    where: dict[str, dict] = {}
    for f in idx.files:
        if not f.path.lower().endswith((".config", ".json", ".xml", ".properties", ".yml", ".yaml", ".ini", ".env", ".toml")) and f.language not in {"C#", "Java", "JavaScript", "TypeScript", "Python", "PHP"}:
            continue
        text = idx.text(f.path)
        for m in URL.finditer(text):
            host = m.group(2).lower()
            if host in {"localhost", "127.0.0.1", "0.0.0.0", "www.w3.org", "schemas.microsoft.com", "schemas.xmlsoap.org",
                        "xmlns.jcp.org", "java.sun.com", "maven.apache.org", "www.springframework.org", "json-schema.org",
                        "github.com", "www.apache.org", "example.com", "tempuri.org", "schemas.android.com"} or host.endswith(".w3.org"):
                continue
            hosts[f"{m.group(1).lower()}://{host}"] += 1
            where.setdefault(f"{m.group(1).lower()}://{host}", {"file": f.path, "line": idx.line_of(f.path, m.start())})
    blob_files = [f for f in idx.files if f.language in {"C#", "Java", "JavaScript", "TypeScript", "Python", "COBOL"} or f.path.lower().endswith((".config", ".xml", ".json", ".properties", ".yml", ".yaml"))]
    queues = []
    for name, pattern in QUEUES.items():
        for f in blob_files:
            m = re.search(pattern, idx.text(f.path), re.I)
            if m:
                queues.append({"name": name, "file": f.path, "line": idx.line_of(f.path, m.start())})
                break
    return {"hosts": [{"endpoint": h, "references": n, **where[h]} for h, n in hosts.most_common(40)], "messaging": queues}
