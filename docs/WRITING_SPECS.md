# Writing a spec

A spec is a Markdown file in `specs/` with YAML front matter. The front matter tells the pipeline what to send; the
body is what the analyst follows.

```markdown
---
id: background-jobs            # unique, kebab-case; also the name of the agent task and output file
version: 1.0.0                 # bump when the text changes: it is recorded in run.json and busts the cache
title: Background jobs and schedules
order: 95                      # position in the run and in the reports
areas: [architecture, risk]    # the first one is the default area of its findings
inputs: [inventory, devops]    # evidence files to include (names in evidence/)
files:                         # how to choose source files, in priority order
  globs: ["**/*Job*.cs", "**/crontab", "**/*.jcl"]
  keywords: [job, scheduler, worker, batch]
  content: "Quartz|Hangfire|@Scheduled|cron"
  hotspots: true               # then the hotspots
  largest: true                # then the largest files
---
## Purpose
## Look for
## Evidence rules
## Business translation
## Out of scope
```

Guidelines:

- Ask for things that can be seen in code. Put judgment calls in "Business translation", not in "Look for".
- Prefer checklists of concrete patterns over abstract goals.
- Say what is out of scope, so findings do not overlap with other specs.
- Add a test fixture or extend `tests/conftest.py` when the spec depends on a new kind of evidence.
