"""One walk over the repository, shared by every scanner."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path

from archaeology import util

LANGUAGES = {
    ".cs": "C#", ".vb": "VB.NET", ".fs": "F#", ".java": "Java", ".kt": "Kotlin", ".scala": "Scala", ".groovy": "Groovy",
    ".js": "JavaScript", ".jsx": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript", ".ts": "TypeScript",
    ".tsx": "TypeScript", ".py": "Python", ".rb": "Ruby", ".php": "PHP", ".go": "Go", ".rs": "Rust", ".c": "C",
    ".h": "C/C++ header", ".cpp": "C++", ".cc": "C++", ".hpp": "C++", ".swift": "Swift", ".m": "Objective-C",
    ".sql": "SQL", ".psql": "SQL", ".pls": "PL/SQL", ".pks": "PL/SQL", ".pkb": "PL/SQL", ".cbl": "COBOL", ".cob": "COBOL",
    ".cpy": "COBOL copybook", ".jcl": "JCL", ".bms": "BMS (CICS maps)", ".asm": "Assembler", ".pl": "Perl",
    ".sh": "Shell", ".bash": "Shell", ".ps1": "PowerShell", ".bat": "Batch", ".cmd": "Batch", ".html": "HTML",
    ".htm": "HTML", ".cshtml": "Razor", ".vbhtml": "Razor", ".aspx": "ASP.NET Web Forms", ".ascx": "ASP.NET Web Forms",
    ".master": "ASP.NET Web Forms", ".jsp": "JSP", ".jspx": "JSP", ".xhtml": "JSF", ".vue": "Vue", ".svelte": "Svelte",
    ".css": "CSS", ".scss": "SCSS", ".less": "LESS", ".cfm": "ColdFusion", ".cfc": "ColdFusion", ".asp": "Classic ASP",
    ".dart": "Dart", ".lua": "Lua", ".r": "R", ".ex": "Elixir", ".exs": "Elixir", ".clj": "Clojure", ".hs": "Haskell",
}
# Languages that count as program source (not markup, data or config) for complexity and coverage ratios.
SOURCE = {
    "C#", "VB.NET", "F#", "Java", "Kotlin", "Scala", "Groovy", "JavaScript", "TypeScript", "Python", "Ruby", "PHP", "Go",
    "Rust", "C", "C++", "Swift", "Objective-C", "PL/SQL", "COBOL", "Perl", "ColdFusion", "Classic ASP", "Dart", "Lua",
    "Elixir", "Clojure", "Haskell", "SQL", "Assembler",
}
COMMENT = {"C#": "//", "Java": "//", "JavaScript": "//", "TypeScript": "//", "Python": "#", "Ruby": "#", "PHP": "//",
           "Go": "//", "SQL": "--", "PL/SQL": "--", "Shell": "#", "Kotlin": "//", "Scala": "//", "C": "//", "C++": "//",
           "Rust": "//", "Swift": "//", "PowerShell": "#", "Perl": "#", "VB.NET": "'", "Groovy": "//"}


@dataclass
class FileInfo:
    path: str
    language: str | None
    bytes: int
    lines: int = 0
    code_lines: int = 0


@dataclass
class Index:
    repo: Path
    cfg: dict
    files: list[FileInfo] = field(default_factory=list)
    _cache: OrderedDict = field(default_factory=OrderedDict)

    @classmethod
    def build(cls, repo: Path, cfg: dict) -> "Index":
        idx = cls(repo=repo, cfg=cfg)
        for rel in util.walk(repo, cfg):
            full = repo / rel
            lang = LANGUAGES.get(full.suffix.lower())
            info = FileInfo(path=rel.as_posix(), language=lang, bytes=full.stat().st_size)
            if util.is_text(full):
                text = idx.text(info.path)
                lines = text.splitlines()
                info.lines = len(lines)
                marker = COMMENT.get(lang or "")
                info.code_lines = sum(1 for l in lines if l.strip() and not (marker and l.strip().startswith(marker)))
            idx.files.append(info)
        return idx

    def text(self, rel: str) -> str:
        if rel in self._cache:
            self._cache.move_to_end(rel)
            return self._cache[rel]
        content = util.read(self.repo, rel)
        self._cache[rel] = content
        if len(self._cache) > 400:
            self._cache.popitem(last=False)
        return content

    def by_name(self, *names: str) -> list[FileInfo]:
        lowered = {n.lower() for n in names}
        return [f for f in self.files if f.path.rsplit("/", 1)[-1].lower() in lowered]

    def by_suffix(self, *suffixes: str) -> list[FileInfo]:
        return [f for f in self.files if f.path.lower().endswith(tuple(s.lower() for s in suffixes))]

    def source(self) -> list[FileInfo]:
        return [f for f in self.files if f.language in SOURCE]

    def line_of(self, rel: str, offset: int) -> int:
        return self.text(rel).count("\n", 0, offset) + 1
