"""The findings as a backlog CSV that Jira and GitHub Issues can import."""

from __future__ import annotations

import csv
import io

PRIORITY = {"critical": "Highest", "high": "High", "medium": "Medium", "low": "Low", "info": "Lowest"}
POINTS = {"S": 2, "M": 5, "L": 13, "XL": 21}


def render(findings: list[dict]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Summary", "Description", "Issue Type", "Priority", "Labels", "Component", "Story Points", "Finding ID"])
    for f in findings:
        if f["severity"] == "info":
            continue
        evidence = "\n".join(f"- {e['file']}{':' + str(e['line']) if e.get('line') else ''}" for e in f["evidence"][:10])
        desc = (f"{f['recommendation']}\n\nWhy: {f['technical_impact']}\n\nBusiness impact: {f['business_impact']}\n\n"
                f"Evidence:\n{evidence}\n\n({f['kind']}, confidence {f['confidence']})")
        w.writerow([f"[{f['id']}] {f['title']}", desc, "Task", PRIORITY[f["severity"]],
                    " ".join(["archaeology", f["area"], *f.get("tags", [])]), f["area"], POINTS[f["effort"]], f["id"]])
    return buf.getvalue()
