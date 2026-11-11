# Contributing

Thanks for helping. The most valuable contributions are new executable specs, better evidence scanners for more
stacks, and reports that read well for non-engineers.

## Set up

```bash
python3 -m venv .venv && .venv/bin/pip install -e ".[dev,anthropic]"
.venv/bin/pytest
```

## Adding a spec

Follow [docs/WRITING_SPECS.md](docs/WRITING_SPECS.md). A spec is ready when:

- it asks for things that can be seen in code, with concrete patterns;
- it says how to translate findings for the business and what is out of scope;
- it runs end to end on the test fixture (`archaeology dig <fixture> --dry-run` shows a sensible prompt).

## Adding evidence for a stack

Scanners live in `archaeology/evidence/`. Add the manifest, framework or endpoint pattern, extend the synthetic
application in `tests/conftest.py` with a minimal example, and assert the result in `tests/test_evidence.py`.

## Rules for every change

- The analyzed repository is never written.
- Nothing reaches a report without evidence the validator can check.
- Secret values never reach a model, a log or a report.
- Business text is plain language; technical text is precise.

## Pull requests

One topic per pull request, with tests, and a CHANGELOG entry under the next version.
