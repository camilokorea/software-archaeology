---
description: Run a software archaeology of a repository and write the technical report and the business brief
argument-hint: <path-to-repository> [--depth quick|standard|deep] [--specs a,b]
allowed-tools: Bash, Read, Write, Glob, Grep, Task
---

Run a software archaeology of the repository at: $ARGUMENTS

Follow these steps exactly. Never modify files inside the analyzed repository.

1. **Evidence (deterministic, no AI).** Run:
   ```bash
   python3 -c "import yaml, jsonschema" 2>/dev/null || python3 -m pip install --user --quiet pyyaml jsonschema
   PYTHONPATH="${CLAUDE_PLUGIN_ROOT}" python3 -m archaeology evidence $ARGUMENTS
   ```
   Note the output folder it prints (by default `./archaeology-output/<repository name>`).

2. **Analysis (one subagent per task).** For every file in `<output>/agent-tasks/`, launch the
   `archaeology-analyst` subagent, at most four at a time, telling it the task file, the repository path and the
   output file `<output>/findings/agent/<spec id>.json` (the spec id is the task file name before any `@`). When a
   spec is split by component (`security@src_web.md`), the subagent appends its findings to the same output file.

3. **First pass of the reports.** Run:
   ```bash
   PYTHONPATH="${CLAUDE_PLUGIN_ROOT}" python3 -m archaeology finish <output>
   ```
   It validates every citation, rejects findings whose code does not match, assigns ids and writes the reports.

4. **Business synthesis.** Launch the `archaeology-synthesizer` subagent with the output folder. It writes
   `<output>/findings/agent/synthesis.json`. Then run step 3 again so the improved synthesis is validated and used.

5. **Tell the user** where `executive.html` (business) and `technical.html` (engineering) are, the status (red,
   amber, green), how many findings were verified, inferred and rejected, and the recommended option. Do not paste
   the reports.
