"""Where the framework's own files live (specs, schemas, prompts), installed or run from a clone."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPECS = ROOT / "specs"
SCHEMAS = ROOT / "schemas"
PROMPTS = ROOT / "prompts"
