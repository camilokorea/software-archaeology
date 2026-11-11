"""Self-contained HTML versions of the reports, for people who will not open a Markdown file. It converts only the
Markdown this tool writes (headings, lists, tables, code, links, emphasis) and needs no dependency."""

from __future__ import annotations

import html
import re

CSS = """
:root{--bg:#fbfaf7;--card:#fff;--ink:#1f2430;--muted:#5b6170;--line:#e4e1d8;--accent:#2f6fde}
@media (prefers-color-scheme:dark){:root{--bg:#14171f;--card:#1c2029;--ink:#eceae4;--muted:#a3a9b6;--line:#2d3240;--accent:#7aa7ff}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:980px;margin:0 auto;padding:32px 20px 64px}h1{font-size:2rem;line-height:1.2}h2{margin-top:2.2em;border-bottom:1px solid var(--line);padding-bottom:.3em}
h4{margin-bottom:.4em}a{color:var(--accent)}code{font:.88em ui-monospace,Consolas,monospace;background:color-mix(in srgb,var(--line) 50%,transparent);padding:.1em .3em;border-radius:4px}
pre{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px;overflow:auto}
table{border-collapse:collapse;width:100%;margin:12px 0;font-size:.94rem;display:block;overflow-x:auto}th,td{border:1px solid var(--line);padding:6px 9px;text-align:left;vertical-align:top}
th{background:var(--card)}
.b{display:inline-block;width:.85em;height:.85em;border-radius:50%;vertical-align:-.05em;margin-right:.25em}.sq{border-radius:2px;width:1.1em;height:1.1em}
.red{background:#d73a49}.orange{background:#f08c2e}.yellow{background:#f2c94c}.blue{background:#3d7be0}.white{background:#c9ccd3}.green{background:#2ea44f}.mermaid{background:#fff;border-radius:8px;padding:12px;border:1px solid var(--line)}
@media print{a{color:inherit}main{max-width:none}}
"""

INLINE = [
    (re.compile(r"`([^`]+)`"), lambda m: f"<code>{m.group(1)}</code>"),
    (re.compile(r"\*\*(.+?)\*\*"), lambda m: f"<strong>{m.group(1)}</strong>"),
    (re.compile(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)"), lambda m: f"<em>{m.group(1)}</em>"),
    (re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)"), lambda m: f'<a href="{_href(m.group(2))}">{m.group(1)}</a>'),
    (re.compile(r"&lt;(https?://[^&\s]+)&gt;"), lambda m: f'<a href="{m.group(1)}">{m.group(1)}</a>'),
]


def _href(url: str) -> str:
    # Links between the two Markdown reports point to their HTML twins.
    return re.sub(r"^(technical|executive)\.md", r"\1.html", url)


# Emoji depend on the reader's fonts (corporate desktops and headless browsers often lack them): draw them in CSS.
GLYPHS = {"🔴": '<span class="b red"></span>', "🟠": '<span class="b orange"></span>', "🟡": '<span class="b yellow"></span>',
          "🔵": '<span class="b blue"></span>', "⚪": '<span class="b white"></span>', "🟢": '<span class="b green"></span>',
          "🟥": '<span class="b sq red"></span>', "🟧": '<span class="b sq orange"></span>', "🟨": '<span class="b sq yellow"></span>',
          "🟩": '<span class="b sq green"></span>', "✅": "✔", "🤖": "AI:", "⭐": "★", "⚠️": "⚠", "⛔": "⊘"}


def inline(text: str) -> str:
    anchors = re.findall(r'<a id="[\w-]+"></a>', text)
    text = html.escape(text, quote=False)
    for a in anchors:
        text = text.replace(html.escape(a, quote=False), a)
    for rx, fn in INLINE:
        text = rx.sub(fn, text)
    for glyph, span in GLYPHS.items():
        text = text.replace(glyph, span)
    return text


def convert(md: str, title: str) -> str:
    out: list[str] = []
    lines = md.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            lang = line[3:].strip()
            body = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                body.append(lines[i])
                i += 1
            code = "\n".join(body)
            out.append(f'<pre class="mermaid">{html.escape(code)}</pre>' if lang == "mermaid" else f"<pre><code>{html.escape(code)}</code></pre>")
        elif m := re.match(r"^(#{1,4})\s+(.*)$", line):
            n = len(m.group(1))
            out.append(f"<h{n}>{inline(m.group(2))}</h{n}>")
        elif line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append(lines[i])
                i += 1
            i -= 1
            cells = lambda r: [c.strip() for c in r.strip().strip("|").split("|")]  # noqa: E731
            head, body = cells(rows[0]), [cells(r) for r in rows[2:]]
            out.append("<table><thead><tr>" + "".join(f"<th>{inline(c)}</th>" for c in head) + "</tr></thead><tbody>" +
                       "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in body) + "</tbody></table>")
        elif line.startswith("- "):
            items = []
            while i < len(lines) and lines[i].startswith("- "):
                items.append(lines[i][2:])
                i += 1
            i -= 1
            out.append("<ul>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ul>")
        elif line.startswith('<a id="'):
            out.append(line)
        elif line.strip():
            para = [line]
            while i + 1 < len(lines) and lines[i + 1].strip() and not re.match(r"^(#|\||- |```|<a id)", lines[i + 1]):
                i += 1
                para.append(lines[i])
            out.append(f"<p>{inline(' '.join(para))}</p>")
        i += 1
    mermaid = ('<script type="module">import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.esm.min.mjs";'
               "mermaid.initialize({startOnLoad:true,securityLevel:'strict'});</script>") if "mermaid" in md else ""
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f"<title>{html.escape(title)}</title><style>{CSS}</style></head><body><main>{''.join(out)}</main>{mermaid}</body></html>\n")
