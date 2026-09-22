#!/usr/bin/env python3
"""Read-only kilo workspace viewer. Python 3 stdlib only."""

from __future__ import annotations

import argparse
import html
import json
import os
import posixpath
import re
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(".").resolve()
STATIC = Path(__file__).resolve().parent / "static"


def safe_join(root: Path, rel: str) -> Path | None:
    rel = rel.replace("\\", "/").lstrip("/")
    if rel.startswith("..") or "/../" in f"/{rel}/":
        return None
    candidate = (root / rel).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return None
    return candidate


def list_tree(root: Path) -> list[dict]:
    projects_dir = root / "Projects"
    if not projects_dir.is_dir():
        return []
    out = []
    for proj in sorted(projects_dir.iterdir()):
        if not proj.is_dir() or proj.name.startswith("_"):
            continue
        homepage = proj / "project.md"
        if not homepage.is_file():
            continue
        lines = []
        for child in sorted(proj.iterdir()):
            if not child.is_dir():
                continue
            line_home = child / "line.md"
            if not line_home.is_file():
                line_home = child / "workstream.md"
            if not line_home.is_file():
                continue
            files = []
            for name in ("line.md", "workstream.md", "context.md", "spec.md", "ops.md", "tasks.md", "review.md"):
                p = child / name
                if p.is_file():
                    rel = p.relative_to(root).as_posix()
                    files.append({"name": name, "path": rel})
            lines.append(
                {
                    "id": child.name,
                    "path": child.relative_to(root).as_posix(),
                    "files": files,
                }
            )
        out.append(
            {
                "id": proj.name,
                "path": homepage.relative_to(root).as_posix(),
                "lines": lines,
            }
        )
    return out


def resolve_wiki(base_rel: str, target: str) -> str:
    target = target.strip().split("#", 1)[0]
    base_dir = posixpath.dirname(base_rel.replace("\\", "/"))
    joined = posixpath.normpath(posixpath.join(base_dir, target))
    if joined.startswith("../") or joined == "..":
        return ""
    candidates = [joined]
    if not joined.endswith(".md"):
        candidates = [
            joined + ".md",
            joined + "/line.md",
            joined + "/project.md",
            joined + "/workstream.md",
            joined + "/context.md",
        ]
    for rel in candidates:
        hit = safe_join(ROOT, rel)
        if hit is not None and hit.is_file():
            return rel
    return candidates[0]


def md_inline(text: str, base_rel: str = "") -> str:
    text = html.escape(text)

    def wiki(match: re.Match[str]) -> str:
        target, label = match.group(1), match.group(2)
        rel = resolve_wiki(base_rel, html.unescape(target))
        shown = html.escape(label or target.split("/")[-1])
        if not rel:
            return shown
        href = "/render?path=" + urllib.parse.quote(rel)
        return f'<a class="wiki" href="{href}">{shown}</a>'

    text = re.sub(r"\[\[([^\]|#]+)(?:\|([^\]]+))?\]\]", wiki, text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    return text


def strip_frontmatter(src: str) -> str:
    text = src.lstrip("\ufeff")
    if text.startswith("---"):
        rest = text[3:]
        end = rest.find("\n---")
        if end != -1:
            return rest[end + 4 :].lstrip("\n")
    return text


def md_to_html(src: str, base_rel: str = "") -> str:
    lines = strip_frontmatter(src).replace("\r\n", "\n").split("\n")
    out: list[str] = []
    i = 0
    in_code = False
    code_buf: list[str] = []
    in_ul = False
    in_table = False

    def close_lists():
        nonlocal in_ul, in_table
        if in_ul:
            out.append("</ul>")
            in_ul = False
        if in_table:
            out.append("</tbody></table>")
            in_table = False

    while i < len(lines):
        line = lines[i]
        if in_code:
            if line.startswith("```"):
                out.append("<pre><code>" + html.escape("\n".join(code_buf)) + "</code></pre>")
                code_buf = []
                in_code = False
            else:
                code_buf.append(line)
            i += 1
            continue
        if line.startswith("```"):
            close_lists()
            in_code = True
            code_buf = []
            i += 1
            continue
        if re.match(r"^\|.+\|$", line) and i + 1 < len(lines) and re.match(r"^\|[\s:|-]+\|$", lines[i + 1]):
            close_lists()
            headers = [c.strip() for c in line.strip("|").split("|")]
            i += 2
            out.append("<table><thead><tr>" + "".join(f"<th>{md_inline(h, base_rel)}</th>" for h in headers) + "</tr></thead><tbody>")
            in_table = True
            continue
        if in_table:
            if re.match(r"^\|.+\|$", line):
                cells = [c.strip() for c in line.strip("|").split("|")]
                out.append("<tr>" + "".join(f"<td>{md_inline(c, base_rel)}</td>" for c in cells) + "</tr>")
                i += 1
                continue
            close_lists()
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            close_lists()
            n = len(m.group(1))
            out.append(f"<h{n}>{md_inline(m.group(2), base_rel)}</h{n}>")
            i += 1
            continue
        if re.match(r"^[-*]\s+", line):
            if not in_ul:
                close_lists()
                out.append("<ul>")
                in_ul = True
            out.append("<li>" + md_inline(re.sub(r"^[-*]\s+", "", line), base_rel) + "</li>")
            i += 1
            continue
        if line.startswith(">"):
            close_lists()
            quote = [re.sub(r"^>\s?", "", line)]
            i += 1
            while i < len(lines) and lines[i].startswith(">"):
                quote.append(re.sub(r"^>\s?", "", lines[i]))
                i += 1
            out.append("<blockquote>" + md_to_html("\n".join(quote), base_rel) + "</blockquote>")
            continue
        if line.strip() == "":
            close_lists()
            i += 1
            continue
        close_lists()
        out.append("<p>" + md_inline(line, base_rel) + "</p>")
        i += 1
    if in_code:
        out.append("<pre><code>" + html.escape("\n".join(code_buf)) + "</code></pre>")
    close_lists()
    return "\n".join(out)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        path = posixpath.normpath(parsed.path)
        qs = urllib.parse.parse_qs(parsed.query)

        if path == "/":
            index = STATIC / "index.html"
            self._send(200, index.read_bytes(), "text/html; charset=utf-8")
            return
        if path.startswith("/static/"):
            rel = path[len("/static/") :]
            target = safe_join(STATIC, rel)
            if target is None or not target.is_file():
                self._send(404, b"not found", "text/plain")
                return
            ctype = "text/css" if target.suffix == ".css" else "application/javascript" if target.suffix == ".js" else "application/octet-stream"
            self._send(200, target.read_bytes(), ctype)
            return
        if path == "/api/tree":
            payload = json.dumps({"root": str(ROOT), "projects": list_tree(ROOT)}).encode()
            self._send(200, payload, "application/json; charset=utf-8")
            return
        if path in ("/api/html", "/render"):
            rel = (qs.get("path") or [""])[0]
            target = safe_join(ROOT, rel)
            if target is None or not target.is_file() or target.suffix != ".md":
                self._send(404, b"not found", "text/plain")
                return
            text = target.read_text(encoding="utf-8", errors="replace")
            converted = md_to_html(text, rel)
            if path == "/render":
                page = (
                    "<!DOCTYPE html><html><head><meta charset='utf-8'>"
                    "<link rel='stylesheet' href='/static/app.css'>"
                    "<script>document.addEventListener('click',function(e){"
                    "var a=e.target.closest('a');if(!a)return;"
                    "try{var u=new URL(a.href,location.origin);}catch(err){return;}"
                    "if(u.pathname==='/render'&&u.searchParams.get('path')){"
                    "e.preventDefault();"
                    "parent.postMessage({type:'kilo-open',path:u.searchParams.get('path')},'*');"
                    "}}});</script>"
                    "</head><body class='doc'>"
                    f"{converted}</body></html>"
                ).encode()
                self._send(200, page, "text/html; charset=utf-8")
                return
            body = json.dumps({"path": rel, "html": converted, "title": target.name}).encode()
            self._send(200, body, "application/json; charset=utf-8")
            return
        self._send(404, b"not found", "text/plain")


def main() -> None:
    global ROOT
    p = argparse.ArgumentParser(description="Read-only kilo workspace viewer")
    p.add_argument("--root", default=os.environ.get("KILO_WORKSPACE", ""), help="workspace root (contains Projects/)")
    p.add_argument("--port", type=int, default=8765)
    args = p.parse_args()
    if not args.root:
        sys.stderr.write("set --root or KILO_WORKSPACE\n")
        sys.exit(2)
    ROOT = Path(args.root).expanduser().resolve()
    if not ROOT.is_dir():
        sys.stderr.write(f"root not a directory: {ROOT}\n")
        sys.exit(2)
    httpd = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"kilo view  http://127.0.0.1:{args.port}  root={ROOT}", flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
