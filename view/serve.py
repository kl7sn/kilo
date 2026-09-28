#!/usr/bin/env python3
"""Kilo Workspace board server. Python 3 stdlib only."""

from __future__ import annotations

import argparse
import html
import json
import os
import posixpath
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.parse
from datetime import date, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(".").resolve()


def config_dir() -> Path:
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Kilo Workspace"
    return Path.home() / ".kilo-workspace"


def saved_root() -> str:
    p = config_dir() / "workspace-root"
    try:
        return p.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def save_root(path: str) -> None:
    d = config_dir()
    d.mkdir(parents=True, exist_ok=True)
    (d / "workspace-root").write_text(path.strip() + "\n", encoding="utf-8")


def looks_like_projects_dir(p: Path) -> bool:
    if not p.is_dir():
        return False
    if p.name == "Projects":
        return True
    try:
        for child in p.iterdir():
            if (
                child.is_dir()
                and not child.name.startswith(("_", "."))
                and (child / "project.md").is_file()
            ):
                return True
    except OSError:
        return False
    return False


def normalize_workspace(path: str | Path) -> Path | None:
    p = Path(path).expanduser()
    try:
        p = p.resolve()
    except OSError:
        return None
    if not p.is_dir():
        return None
    if looks_like_projects_dir(p):
        return p
    nested = p / "Projects"
    if nested.is_dir():
        return nested
    return p


def set_workspace(path: str) -> dict:
    global ROOT
    n = normalize_workspace(path)
    if n is None:
        return {"ok": False, "error": "不是目录"}
    ROOT = n
    save_root(str(n))
    return {
        "ok": True,
        "root": str(n),
        "has_projects": looks_like_projects_dir(n),
    }


ORCA_INSTALL_URL = "https://www.onorca.dev/docs/install"
ORCA_DMG_URL = (
    "https://github.com/stablyai/orca/releases/latest/download/orca-macos-arm64.dmg"
)


def init_workspace(path: str) -> dict:
    p = Path(path).expanduser()
    try:
        p = p.resolve()
    except OSError:
        return {"ok": False, "error": "不是目录"}
    if not p.is_dir():
        return {"ok": False, "error": "不是目录"}
    if looks_like_projects_dir(p):
        return set_workspace(str(p))
    nested = p / "Projects"
    if nested.is_dir() and looks_like_projects_dir(nested):
        return set_workspace(str(nested))
    dest = p if p.name == "Projects" else nested
    dest.mkdir(parents=True, exist_ok=True)
    facts = dest / "_facts.md"
    if not facts.is_file():
        facts.write_text(
            "# 记忆\n\n工作区共用的稳定事实。\n\n## Stable Facts\n\n## Gotcha Index\n",
            encoding="utf-8",
        )
    return set_workspace(str(dest))


def orca_status() -> dict:
    global _ORCA_BIN
    _ORCA_BIN = ""
    path = ""
    for cand in (
        "/usr/local/bin/orca",
        "/Applications/Orca.app/Contents/Resources/bin/orca",
        "/opt/homebrew/bin/orca",
        shutil.which("orca") or "",
    ):
        if cand and Path(cand).exists():
            path = cand
            break
    if path:
        _ORCA_BIN = path
    app = Path("/Applications/Orca.app").is_dir()
    return {
        "ok": bool(path),
        "path": path,
        "app": app,
        "install_url": ORCA_INSTALL_URL,
        "dmg_url": ORCA_DMG_URL,
    }


def open_orca_install() -> dict:
    st = orca_status()
    if st.get("app"):
        try:
            subprocess.Popen(["open", "-a", "Orca"])
            return {"ok": True, "opened": "app"}
        except OSError:
            pass
    url = st.get("dmg_url") or ORCA_INSTALL_URL
    try:
        import webbrowser

        webbrowser.open(url)
    except Exception:
        if sys.platform == "darwin":
            subprocess.Popen(["open", url])
    return {"ok": True, "opened": "url", "url": url}


def bundle_dir() -> Path:
    meipass = getattr(sys, "_MEIPASS", None)
    if getattr(sys, "frozen", False) and meipass:
        return Path(meipass)
    return Path(__file__).resolve().parent


VIEW_DIR = bundle_dir()
STATIC = VIEW_DIR / "static"


def app_version() -> str:
    p = VIEW_DIR / "VERSION"
    try:
        return p.read_text(encoding="utf-8").strip() or "0.0.0"
    except OSError:
        return "0.0.0"


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


_TASK_ROW = re.compile(r"^\|\s*T\d+\s*\|")
_FM_STATUS = re.compile(r"(?m)^status:\s*[\"']?([A-Za-z0-9_-]+)")
_FM_FIELD = re.compile(r"(?m)^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$")


def read_frontmatter(path: Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    block = text[3:end] if end != -1 else ""
    out = {}
    repos: list[str] = []
    in_repos = False
    for line in block.splitlines():
        if re.match(r"^repos:\s*$", line):
            in_repos = True
            continue
        if in_repos:
            rm = re.match(r"^\s+-\s+(\S.*)$", line)
            if rm:
                repos.append(rm.group(1).strip().strip('"').strip("'"))
                continue
            in_repos = False
        m = _FM_FIELD.match(line)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip().strip('"').strip("'")
        if key in {
            "title",
            "summary",
            "status",
            "created",
            "updated",
            "worktree_root",
            "alias",
        }:
            out[key] = val
    if repos:
        out["repos"] = repos
    return out


_NUM_PREFIX = re.compile(r"^\d+(?:\.\d+)*-(.+)$")


def set_yaml_field(src: str, key: str, value: str) -> str:
    text = src.lstrip("\ufeff")
    q = value.replace("\\", "\\\\").replace('"', '\\"')
    line = f'{key}: "{q}"' if value else ""
    if not text.startswith("---"):
        return f"---\n{line}\n---\n\n{text}" if value else src
    end = text.find("\n---", 3)
    if end == -1:
        return src
    block = text[3:end]
    rest = text[end + 4 :]
    lines = block.splitlines()
    out: list[str] = []
    found = False
    for raw in lines:
        if re.match(rf"^{re.escape(key)}:\s*", raw):
            found = True
            if line:
                out.append(line)
            continue
        out.append(raw)
    if value and not found:
        inserted = False
        acc: list[str] = []
        for raw in out:
            acc.append(raw)
            if not inserted and raw.startswith("title:"):
                acc.append(line)
                inserted = True
        if not inserted:
            acc.insert(0 if acc[:1] == [""] else 0, line)
        out = acc
    return "---\n" + "\n".join(out) + "\n---" + rest


def set_project_alias(project_id: str, alias: str) -> dict:
    alias = alias.strip()
    homepage = ROOT / project_id / "project.md"
    if not homepage.is_file():
        return {"ok": False, "error": "project.md missing"}
    src = homepage.read_text(encoding="utf-8")
    derived = folder_alias(project_id, "")
    if alias == project_id or alias == derived:
        alias = ""
    homepage.write_text(set_yaml_field(src, "alias", alias), encoding="utf-8")
    return {"ok": True, "alias": alias or derived, "id": project_id}


def set_line_alias(project_id: str, line_id: str, alias: str) -> dict:
    alias = alias.strip()
    folder = ROOT / project_id / line_id
    path = folder / "line.md"
    if not path.is_file():
        path = folder / "workstream.md"
    if not path.is_file():
        return {"ok": False, "error": "line.md missing"}
    src = path.read_text(encoding="utf-8")
    derived = folder_alias(line_id, "")
    if alias == line_id or alias == derived:
        alias = ""
    path.write_text(set_yaml_field(src, "alias", alias), encoding="utf-8")
    return {"ok": True, "alias": alias or derived or line_id, "id": line_id}


def delete_project(project_id: str) -> dict:
    pid = Path(str(project_id or "")).name
    if not pid or pid != str(project_id) or pid.startswith(".") or pid.startswith("_"):
        return {"ok": False, "error": "invalid project"}
    root = ROOT.resolve()
    src = (root / pid).resolve()
    try:
        src.relative_to(root)
    except ValueError:
        return {"ok": False, "error": "invalid project"}
    if src.parent != root or not src.is_dir() or not (src / "project.md").is_file():
        return {"ok": False, "error": "project not found"}
    trash = root / "_trash"
    trash.mkdir(parents=True, exist_ok=True)
    dest = trash / f"{pid}-{time.strftime('%Y%m%d-%H%M%S')}"
    shutil.move(str(src), str(dest))
    ids, pinned = load_project_layout()
    save_project_order([i for i in ids if i != pid], [i for i in pinned if i != pid])
    return {"ok": True, "id": pid, "trash": dest.name}


def next_project_nn() -> int:
    n = 0
    for pid in known_project_ids():
        m = re.match(r"^(\d+)-", pid)
        if m:
            n = max(n, int(m.group(1)))
    return n + 1


def yaml_quote(s: str) -> str:
    return '"' + (s or "").replace("\\", "\\\\").replace('"', '\\"') + '"'


def repo_owner(path: str) -> str:
    want = expand_repo_path(path)
    if want is None:
        return ""
    key = str(want)
    for p in list_tree(ROOT):
        for r in p.get("repo_paths") or []:
            if _same_path(r, key):
                return str(p.get("alias") or p["id"])
    return ""


def create_project(title: str, name: str, summary: str, repo: str) -> dict:
    title = (title or "").strip()
    name = (name or "").strip()
    summary = (summary or "").strip()
    repo = (repo or "").strip()
    if not repo:
        return {"ok": False, "error": "需要仓库路径"}
    rp = expand_repo_path(repo)
    if rp is None:
        return {"ok": False, "error": "仓库路径不存在或不是目录"}
    if not title and name:
        title = name
    if not title:
        title = rp.name
    if not title:
        return {"ok": False, "error": "需要标题"}
    owner = repo_owner(str(rp))
    if owner:
        return {"ok": False, "error": f"该路径已被「{owner}」使用"}
    slug = ascii_slug(name) or ascii_slug(title) or "project"
    nn = next_project_nn()
    pid = f"{nn:02d}-{slug[:40]}"
    dest = ROOT / pid
    if dest.exists():
        pid = f"{nn:02d}-{slug[:28]}-{time.strftime('%H%M')}"
        dest = ROOT / pid
    dest.mkdir(parents=True, exist_ok=False)
    alias = title if title != pid and title != slug else ""
    repo_s = str(rp)
    repo_yaml = f"\n  - {yaml_quote(repo_s)}"
    repo_row = f"| repo | `{repo_s}` |\n"
    today = time.strftime("%Y-%m-%d")
    body = (
        "---\n"
        f"title: {yaml_quote(title)}\n"
        + (f"alias: {yaml_quote(alias)}\n" if alias else "")
        + "type: project\n"
        "parent: \"\"\n"
        f"project: {yaml_quote(pid)}\n"
        "status: active\n"
        "blocked: false\n"
        f"summary: {yaml_quote(summary)}\n"
        f"repos:{repo_yaml}\n"
        "lang: \"zh\"\n"
        f"updated: {yaml_quote(today)}\n"
        "tags:\n"
        "  - project\n"
        "---\n\n"
        f"# {title}\n\n"
        "`/kilo` 项目容器。具体落地走 `/kilo new`。\n\n"
        "## 下属任务包\n\n"
        "| 任务包 | 备注 | Worktree | Branch | State |\n"
        "| --- | --- | --- | --- | --- |\n\n"
        "## 仓库\n\n"
        "| ID | path |\n"
        "| --- | --- |\n"
        f"{repo_row}"
    )
    (dest / "project.md").write_text(body, encoding="utf-8")
    ids, pinned = load_project_layout()
    if pid not in ids:
        ids.append(pid)
    save_project_order(ids, pinned)
    return {"ok": True, "id": pid, "title": title}


def set_line_status(project_id: str, line_id: str, status: str) -> dict:
    want = "active" if norm_line_status(status) == "active" else "completed"
    folder = ROOT / project_id / line_id
    path = folder / "line.md"
    if not path.is_file():
        path = folder / "workstream.md"
    if not path.is_file():
        return {"ok": False, "error": "line.md missing"}
    src = path.read_text(encoding="utf-8")
    path.write_text(set_yaml_field(src, "status", want), encoding="utf-8")
    return {"ok": True, "status": norm_line_status(want), "id": line_id}


def folder_alias(folder: str, explicit: str = "") -> str:
    if explicit:
        return explicit
    m = _NUM_PREFIX.match(folder)
    return m.group(1) if m else folder


def _bump(d: dict, key: str, n: int = 1) -> None:
    d[key] = d.get(key, 0) + n


def norm_line_status(raw: str) -> str:
    s = raw.strip().strip("\"'").lower()
    if s in {"closed", "completed", "archived"}:
        return "closed"
    if s in {"active", "open"}:
        return "active"
    return s or "active"


def norm_task_status(raw: str) -> str:
    s = raw.strip().lower()
    if s.startswith("done"):
        return "done"
    if s in {"doing", "in_progress", "in-progress"}:
        return "doing"
    if s in {"blocked", "escalate"}:
        return "blocked"
    if s in {"cancelled", "canceled", "carried"}:
        return "cancelled"
    return "todo"


def read_line_status(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return "active"
    block = text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        block = text[3:end] if end != -1 else text[:400]
    m = _FM_STATUS.search(block)
    return norm_line_status(m.group(1) if m else "active")


def parse_task_statuses(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    out = []
    for line in text.splitlines():
        if not _TASK_ROW.match(line):
            continue
        cells = split_table_row(line)
        raw = cells[2] if len(cells) > 2 else ""
        out.append(norm_task_status(raw))
    return out


def count_task_rows(path: Path) -> int:
    return len(parse_task_statuses(path))


def list_tree(root: Path) -> list[dict]:
    projects_dir = root
    if not projects_dir.is_dir():
        return []
    out = []
    for proj in sorted(projects_dir.iterdir()):
        if not proj.is_dir() or proj.name.startswith("_"):
            continue
        homepage = proj / "project.md"
        if not homepage.is_file():
            continue
        proj_fm = read_frontmatter(homepage)
        lines = []
        n_files = 1
        n_tasks = 0
        line_status = {"active": 0, "closed": 0}
        task_status = {
            "done": 0,
            "doing": 0,
            "todo": 0,
            "blocked": 0,
            "cancelled": 0,
        }
        for child in sorted(proj.iterdir()):
            if not child.is_dir():
                continue
            line_home = child / "line.md"
            if not line_home.is_file():
                line_home = child / "workstream.md"
            if not line_home.is_file():
                continue
            fm = read_frontmatter(line_home)
            st = norm_line_status(fm.get("status") or read_line_status(line_home))
            _bump(line_status, st if st in line_status else "active")
            files = []
            line_n = 0
            line_ts = {
                "done": 0,
                "doing": 0,
                "todo": 0,
                "blocked": 0,
                "cancelled": 0,
            }
            for name in ("line.md", "workstream.md", "context.md", "spec.md", "ops.md", "tasks.md", "review.md"):
                p = child / name
                if p.is_file():
                    rel = p.relative_to(root).as_posix()
                    files.append({"name": name, "path": rel})
                    if name == "tasks.md":
                        for ts in parse_task_statuses(p):
                            line_n += 1
                            n_tasks += 1
                            _bump(line_ts, ts if ts in line_ts else "todo")
                            _bump(task_status, ts if ts in task_status else "todo")
            n_files += len(files)
            ho = handoff_worktree(child / "context.md")
            wt = (ho.get("worktree_path") or "").strip()
            if wt in {"-", "none"}:
                wt = ""
            for repo in fm.get("repos") or []:
                for ent in parse_kilo_state(Path(repo).expanduser() / ".kilo-state"):
                    if ent.get("project") == child.name:
                        alt = (ent.get("worktree_path") or "").strip()
                        if alt and alt not in {"-", "none"}:
                            wt = alt
            lines.append(
                {
                    "id": child.name,
                    "path": child.relative_to(root).as_posix(),
                    "status": st,
                    "alias": fm.get("alias") or "",
                    "title": fm.get("title") or child.name,
                    "summary": fm.get("summary") or "",
                    "updated": fm.get("updated") or fm.get("created") or "",
                    "tasks": line_n,
                    "task_status": line_ts,
                    "repos": fm.get("repos") or [],
                    "worktree_path": wt,
                    "files": files,
                }
            )
        repo_paths = []
        wr = expand_repo_path(str(proj_fm.get("worktree_root") or ""))
        if wr is not None and is_git_repo(str(wr)):
            repo_paths.append(str(wr))
        for r in proj_fm.get("repos") or []:
            rp = expand_repo_path(str(r))
            if rp is not None:
                repo_paths.append(str(rp))
        for ln in lines:
            for r in ln.get("repos") or []:
                rp = expand_repo_path(str(r))
                if rp is not None:
                    repo_paths.append(str(rp))
        try:
            src = homepage.read_text(encoding="utf-8")
        except OSError:
            src = ""
        in_repos = False
        for raw_line in src.splitlines():
            if raw_line.startswith("## ") and any(
                k in raw_line for k in ("仓库", "代码库", "Worktree", "Repos")
            ):
                in_repos = True
                continue
            if in_repos and raw_line.startswith("## "):
                break
            if in_repos and raw_line.startswith("|"):
                cells = split_table_row(raw_line)
                if len(cells) >= 2 and cells[0] not in {"ID", "---", "仓 ID"}:
                    for cell in cells[1:]:
                        rp = expand_repo_path(cell)
                        if rp is not None:
                            repo_paths.append(str(rp))
        seen = []
        for r in repo_paths:
            if r not in seen:
                seen.append(r)
        out.append(
            {
                "id": proj.name,
                "alias": folder_alias(proj.name, proj_fm.get("alias") or ""),
                "path": homepage.relative_to(root).as_posix(),
                "title": proj_fm.get("title") or proj.name,
                "summary": proj_fm.get("summary") or "",
                "updated": proj_fm.get("updated") or proj_fm.get("created") or "",
                "status": norm_line_status(proj_fm.get("status") or "active"),
                "repo_paths": seen,
                "lines": lines,
                "files": n_files,
                "tasks": n_tasks,
                "line_status": line_status,
                "task_status": task_status,
            }
        )
    return apply_project_order(out)


def parse_fact_sections(text: str) -> list[dict]:
    sections: list[dict] = []
    current = {"title": "", "items": []}
    for raw in text.splitlines():
        s = raw.strip()
        if s.startswith("## "):
            if current["items"]:
                sections.append(current)
            current = {"title": s[3:].strip(), "items": []}
            continue
        if len(s) < 2 or s[0] not in "-*•" or s[1] not in " \t":
            continue
        item = s[2:].strip()
        if item:
            current["items"].append(item)
    if current["items"]:
        sections.append(current)
    return sections


def list_facts(root: Path, projects: list[dict] | None = None) -> list[dict]:
    groups: list[dict] = []
    projects_dir = root
    if projects is None:
        projects = list_tree(root)

    def add_group(gid: str, label: str, path: Path) -> None:
        if not path.is_file():
            return
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            return
        sections = parse_fact_sections(text)
        if not sections:
            return
        rel = path.relative_to(root).as_posix()
        items = [it for sec in sections for it in sec["items"]]
        groups.append(
            {
                "id": gid,
                "label": label,
                "path": rel,
                "sections": sections,
                "items": items,
            }
        )

    add_group("", "所有项目", projects_dir / "_facts.md")
    for p in projects:
        add_group(p["id"], p.get("alias") or p["id"], projects_dir / p["id"] / "_facts.md")
    return groups


def _skip_skill_dir(name: str) -> bool:
    if not name or name.startswith(".") or name.startswith("_"):
        return True
    if name in {"node_modules", "__pycache__"}:
        return True
    if "backup" in name.lower():
        return True
    return False


def _parse_skill_fm(block: str) -> dict:
    out: dict[str, str] = {}
    lines = block.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if not m:
            i += 1
            continue
        key, val = m.group(1), m.group(2).rstrip()
        folded = val in {">", ">-", "|", "|-", ""} and key in {"description", "name"}
        if folded and (val in {">", ">-", "|", "|-"} or val == ""):
            chunks: list[str] = []
            i += 1
            while i < len(lines) and (
                not lines[i].strip()
                or lines[i].startswith(" ")
                or lines[i].startswith("\t")
            ):
                piece = lines[i].strip()
                if piece:
                    chunks.append(piece)
                i += 1
            if chunks:
                out[key] = " ".join(chunks)
            continue
        out[key] = val.strip().strip('"').strip("'")
        i += 1
    return out


def read_skill_meta(path: Path) -> dict:
    name = path.parent.name
    desc = ""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {"name": name, "description": "", "path": str(path.parent)}
    if text.startswith("---"):
        end = text.find("\n---", 3)
        block = text[3:end] if end != -1 else ""
        fm = _parse_skill_fm(block)
        if fm.get("name"):
            name = fm["name"].strip()
        desc = (fm.get("description") or "").strip()
    desc = re.sub(r"\s+", " ", desc)
    if len(desc) > 220:
        desc = desc[:217] + "…"
    return {"name": name, "description": desc, "path": str(path.parent.resolve())}


SKILL_SOURCES = [
    ("claude", "Claude"),
    ("cursor", "Cursor"),
    ("codex", "Codex"),
    ("grok", "Grok"),
    ("gemini", "Gemini"),
    ("agents", "Agents"),
    ("repo", "仓库"),
]
SKILL_SOURCE_IDS = [s[0] for s in SKILL_SOURCES]
SKILL_MARKS = ["claude", "cursor", "codex", "grok", "gemini"]
PROTECTED_SKILLS = {"kilo"}


def skill_is_protected(rec: dict) -> bool:
    if (rec.get("name") or "").strip().lower() in PROTECTED_SKILLS:
        return True
    for loc in rec.get("locations") or []:
        if Path(str(loc.get("path") or "")).name.lower() in PROTECTED_SKILLS:
            return True
    return False


def skill_roots() -> list[tuple[str, str, Path]]:
    home = Path.home()
    return [
        ("claude", "Claude", home / ".claude" / "skills"),
        ("cursor", "Cursor", home / ".cursor" / "skills"),
        ("codex", "Codex", home / ".codex" / "skills"),
        ("grok", "Grok", home / ".grok" / "skills"),
        ("gemini", "Gemini", home / ".gemini" / "skills"),
        ("agents", "Agents", home / ".agents" / "skills"),
        ("repo", "仓库", VIEW_DIR.parent / "skills"),
    ]


def list_skills() -> dict:
    by_name: dict[str, dict] = {}
    for gid, _label, root in skill_roots():
        if not root.is_dir():
            continue
        walked: set[tuple[int, int]] = set()
        seen_here: set[str] = set()
        for dirpath, dirnames, filenames in os.walk(root, followlinks=True):
            try:
                st = os.stat(dirpath)
                dkey = (st.st_dev, st.st_ino)
            except OSError:
                dirnames[:] = []
                continue
            if dkey in walked:
                dirnames[:] = []
                continue
            walked.add(dkey)
            dirnames[:] = [d for d in dirnames if not _skip_skill_dir(d)]
            if "SKILL.md" not in filenames:
                continue
            md = Path(dirpath) / "SKILL.md"
            try:
                real = str(md.resolve())
            except OSError:
                continue
            if real in seen_here:
                continue
            seen_here.add(real)
            meta = read_skill_meta(md)
            key = (meta["name"] or md.parent.name).strip().lower()
            if not key:
                continue
            rec = by_name.get(key)
            if rec is None:
                rec = {
                    "name": meta["name"],
                    "description": meta["description"],
                    "path": str(Path(dirpath)),
                    "sources": [],
                    "locations": [],
                }
                by_name[key] = rec
            if gid not in rec["sources"]:
                rec["sources"].append(gid)
            folder = Path(dirpath)
            loc = {
                "id": gid,
                "label": _label,
                "path": str(folder),
                "link": folder.is_symlink(),
            }
            if not any(
                x["id"] == loc["id"] and x["path"] == loc["path"] for x in rec["locations"]
            ):
                rec["locations"].append(loc)
            if len(meta["description"]) > len(rec["description"]):
                rec["description"] = meta["description"]
    rank = {sid: i for i, sid in enumerate(SKILL_SOURCE_IDS)}
    items = list(by_name.values())
    for rec in items:
        rec["sources"] = sorted(rec["sources"], key=lambda s: rank.get(s, 99))
        rec["protected"] = skill_is_protected(rec)
    items.sort(key=lambda s: s["name"].lower())
    counts = {sid: 0 for sid in SKILL_MARKS}
    for rec in items:
        for sid in rec["sources"]:
            if sid in counts:
                counts[sid] += 1
    return {
        "ok": True,
        "n": len(items),
        "items": items,
        "marks": [{"id": sid, "label": lab} for sid, lab in SKILL_SOURCES if sid in SKILL_MARKS],
        "counts": counts,
    }


def _skill_by_name(name: str) -> dict | None:
    key = (name or "").strip().lower()
    if not key or "/" in key or "\\" in key:
        return None
    for rec in list_skills().get("items") or []:
        if rec["name"].lower() == key:
            return rec
    return None


def skill_detail(name: str) -> dict:
    rec = _skill_by_name(name)
    if not rec:
        return {"ok": False, "error": "没有这个 skill"}
    html = ""
    files: list[str] = []
    for loc in rec.get("locations") or []:
        folder = Path(loc["path"])
        md = folder / "SKILL.md"
        if not html and md.is_file():
            try:
                src = md.read_text(encoding="utf-8", errors="replace")
            except OSError:
                src = ""
            if len(src) > 80_000:
                src = src[:80_000] + "\n\n…"
            html = md_to_html(src)
        if folder.is_dir() and not files:
            try:
                names = sorted(
                    p.name
                    for p in folder.iterdir()
                    if not p.name.startswith(".")
                )
            except OSError:
                names = []
            files = names[:40]
        if html and files:
            break
    return {
        "ok": True,
        "name": rec["name"],
        "description": rec["description"],
        "sources": rec["sources"],
        "locations": rec.get("locations") or [],
        "files": files,
        "html": html,
        "protected": skill_is_protected(rec),
    }


def _skill_folder_allowed(folder: Path) -> bool:
    folder = Path(folder).expanduser()
    if not folder.exists():
        return False
    abs_folder = Path(os.path.abspath(str(folder)))
    for _gid, _label, root in skill_roots():
        if not root.exists():
            continue
        abs_root = Path(os.path.abspath(str(root)))
        try:
            rel = abs_folder.relative_to(abs_root)
        except ValueError:
            continue
        if not rel.parts or rel.parts[0] in {"..", "."}:
            continue
        return True
    return False


def delete_skill(name: str, source: str = "") -> dict:
    rec = _skill_by_name(name)
    if not rec:
        return {"ok": False, "error": "没有这个 skill"}
    if skill_is_protected(rec):
        return {"ok": False, "error": "kilo 不允许删除"}
    source = (source or "").strip().lower()
    if not source:
        return {"ok": False, "error": "必须指定来源"}
    if source not in SKILL_SOURCE_IDS:
        return {"ok": False, "error": "未知来源"}
    targets = [t for t in rec.get("locations") or [] if t["id"] == source]
    if not targets:
        return {"ok": False, "error": "没有可删的路径"}
    removed: list[str] = []
    errors: list[str] = []
    for t in targets:
        folder = Path(t["path"]).expanduser()
        if not _skill_folder_allowed(folder):
            errors.append(f"路径不在 skill 目录内：{folder}")
            continue
        try:
            if folder.is_symlink() or folder.is_file():
                folder.unlink()
            elif folder.is_dir():
                shutil.rmtree(folder)
            else:
                errors.append(f"无法删除：{folder}")
                continue
            removed.append(str(folder))
        except OSError as exc:
            errors.append(str(exc))
    ok = bool(removed) and not errors
    out = {"ok": ok, "removed": removed, "name": rec["name"]}
    if errors:
        out["error"] = "；".join(errors)[:400]
    return out


def project_order_file() -> Path:
    return ROOT / "_kilo-project-order.json"


def known_project_ids() -> list[str]:
    projects_dir = ROOT
    if not projects_dir.is_dir():
        return []
    names = []
    for proj in sorted(projects_dir.iterdir()):
        if proj.is_dir() and not proj.name.startswith("_") and (proj / "project.md").is_file():
            names.append(proj.name)
    return names


def load_project_layout() -> tuple[list[str], list[str]]:
    p = project_order_file()
    if not p.is_file():
        return [], []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return [], []
    if isinstance(data, list):
        return [str(x) for x in data], []
    if not isinstance(data, dict):
        return [], []
    ids = [str(x) for x in data["ids"]] if isinstance(data.get("ids"), list) else []
    pinned = [str(x) for x in data["pinned"]] if isinstance(data.get("pinned"), list) else []
    return ids, pinned


def apply_project_order(projects: list[dict]) -> list[dict]:
    ids, pinned = load_project_layout()
    pin_rank = {pid: i for i, pid in enumerate(pinned)}
    rest_rank = {pid: i for i, pid in enumerate(ids)}
    for p in projects:
        p["pinned"] = p["id"] in pin_rank
    return sorted(
        projects,
        key=lambda p: (
            0 if p["pinned"] else 1,
            pin_rank.get(p["id"], 0) if p["pinned"] else rest_rank.get(p["id"], 10_000),
            p["id"],
        ),
    )


def save_project_order(ids: list[str], pinned: list[str] | None = None) -> dict:
    known = known_project_ids()
    known_set = set(known)
    cur_ids, cur_pinned = load_project_layout()
    if pinned is None:
        pinned = cur_pinned
    pinned_out = [i for i in pinned if i in known_set]
    ordered = [i for i in ids if i in known_set]
    for pid in known:
        if pid not in ordered:
            ordered.append(pid)
    path = project_order_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"ids": ordered, "pinned": pinned_out}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )
    return {"ok": True, "ids": ordered, "pinned": pinned_out}


def workspace_stamp(root: Path) -> dict:
    projects = root
    latest = 0
    n = 0
    if projects.is_dir():
        for p in projects.rglob("*.md"):
            try:
                n += 1
                latest = max(latest, p.stat().st_mtime_ns)
            except OSError:
                continue
    return {"n": n, "t": latest}


def display_name() -> str:
    try:
        r = subprocess.run(["id", "-F"], capture_output=True, text=True, timeout=2)
        if r.returncode == 0:
            return (r.stdout or "").strip()
    except Exception:
        pass
    return ""


def activity_grid(root: Path, weeks: int = 53) -> dict:
    today = date.today()
    start = today - timedelta(days=today.weekday()) - timedelta(weeks=weeks - 1)
    last = start + timedelta(weeks=weeks) - timedelta(days=1)
    counts: dict[str, int] = {}
    if root.is_dir():
        for p in root.rglob("*.md"):
            if any(part.startswith("_") for part in p.relative_to(root).parts):
                continue
            try:
                d = datetime.fromtimestamp(p.stat().st_mtime).date()
            except OSError:
                continue
            if d < start or d > last:
                continue
            key = d.isoformat()
            counts[key] = counts.get(key, 0) + 1
    days = []
    d = start
    while d <= last:
        days.append({"date": d.isoformat(), "n": counts.get(d.isoformat(), 0)})
        d += timedelta(days=1)
    return {
        "weeks": weeks,
        "start": start.isoformat(),
        "today": today.isoformat(),
        "days": days,
    }


def _ensure_gui_path() -> None:
    extras = [
        "/usr/local/bin",
        "/opt/homebrew/bin",
        "/opt/homebrew/sbin",
        "/Applications/Orca.app/Contents/Resources/bin",
        str(Path.home() / ".local" / "bin"),
    ]
    parts = [p for p in os.environ.get("PATH", "").split(":") if p]
    for extra in extras:
        if extra and extra not in parts and Path(extra).is_dir():
            parts.insert(0, extra)
    os.environ["PATH"] = ":".join(parts)


_ensure_gui_path()
_ORCA_BIN = ""


def orca_bin() -> str:
    global _ORCA_BIN
    if _ORCA_BIN:
        return _ORCA_BIN
    for cand in (
        "/usr/local/bin/orca",
        "/Applications/Orca.app/Contents/Resources/bin/orca",
        "/opt/homebrew/bin/orca",
        shutil.which("orca") or "",
    ):
        if cand and Path(cand).exists():
            _ORCA_BIN = cand
            return cand
    return ""


def _run_full(cmd: list[str], timeout: float = 4) -> tuple[int, str, str]:
    cmd = list(cmd)
    if cmd and cmd[0] == "orca":
        bin_path = orca_bin()
        if not bin_path:
            return 127, "", "orca not found"
        cmd[0] = bin_path
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"
    except OSError as e:
        return 127, "", str(e)
    return r.returncode, r.stdout or "", r.stderr or ""


def _run(cmd: list[str], timeout: float = 4) -> str:
    code, out, _err = _run_full(cmd, timeout=timeout)
    return out if code == 0 else ""


def _same_path(a: str, b: str) -> bool:
    if not a or not b or a in {"-", "none"}:
        return False
    try:
        return Path(a).expanduser().resolve() == Path(b).expanduser().resolve()
    except OSError:
        return os.path.normpath(a) == os.path.normpath(b)


def parse_kilo_state(path: Path) -> list[dict]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    entries: list[dict] = []
    cur: dict | None = None
    in_p = False
    for line in text.splitlines():
        if line.startswith("projects:"):
            in_p = True
            continue
        if not in_p:
            continue
        if re.match(r"^  - project:\s*", line):
            if cur:
                entries.append(cur)
            cur = {"project": line.split(":", 1)[1].strip()}
            continue
        if cur and re.match(r"^    [A-Za-z0-9_]+:", line):
            k, v = line.strip().split(":", 1)
            cur[k] = v.strip().strip('"')
            continue
        if cur and line and not line.startswith(" "):
            entries.append(cur)
            cur = None
            in_p = False
    if cur:
        entries.append(cur)
    return entries


def git_worktrees(repo: Path) -> list[dict]:
    out = _run(["git", "-C", str(repo), "worktree", "list", "--porcelain"])
    trees = []
    cur: dict = {}
    for line in out.splitlines():
        if line.startswith("worktree "):
            if cur:
                trees.append(cur)
            cur = {"path": line.split(" ", 1)[1]}
        elif line.startswith("branch ") and cur:
            br = line.split(" ", 1)[1]
            cur["branch"] = br.replace("refs/heads/", "")
        elif line == "":
            if cur:
                trees.append(cur)
                cur = {}
    if cur:
        trees.append(cur)
    return trees


def git_dirty(path: Path) -> str:
    if not path.is_dir():
        return "missing"
    out = _run(["git", "-C", str(path), "status", "--porcelain"])
    if out == "" and not (path / ".git").exists() and not (path / ".git").is_file():
        # still a worktree if git status works
        probe = _run(["git", "-C", str(path), "rev-parse", "--is-inside-work-tree"])
        if probe.strip() != "true":
            return "missing"
    return "dirty" if out.strip() else "clean"


_ORCA_MEMO: dict[tuple, tuple[float, object]] = {}


def orca_json(args: list[str], ttl: float = 8) -> dict | list | None:
    key = tuple(args)
    now = time.time()
    hit = _ORCA_MEMO.get(key)
    if hit and now - hit[0] < ttl and hit[1] is not None:
        return hit[1]  # type: ignore[return-value]
    raw = _run(["orca", *args, "--json"], timeout=5)
    if not raw.strip():
        return hit[1] if hit else None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return hit[1] if hit else None
    if isinstance(data, dict) and "result" in data:
        data = data["result"]
    _ORCA_MEMO[key] = (now, data)
    return data


def handoff_worktree(context_path: Path) -> dict:
    if not context_path.is_file():
        return {}
    try:
        text = context_path.read_text(encoding="utf-8")
    except OSError:
        return {}
    for title, body in split_h2(text):
        if title.lower() != "handoff":
            continue
        d = dict(parse_loose_kv(body))
        keys = (
            "worktree_path",
            "worktree_branch",
            "worktree_status",
            "worktree_git_status",
            "commit_status",
        )
        return {k: str(d.get(k) or "").strip() for k in keys}
    return {}


def orca_ps_rows() -> tuple[list[dict], bool]:
    ps = orca_json(["worktree", "ps", "--limit", "80"])
    if ps is None:
        return [], False
    if isinstance(ps, dict):
        rows = ps.get("worktrees") or []
    elif isinstance(ps, list):
        rows = ps
    else:
        rows = []
    return [t for t in rows if isinstance(t, dict)], True


def _agent_brief(a: dict) -> dict:
    prompt = str(a.get("prompt") or "").strip().replace("\n", " ")
    if len(prompt) > 160:
        prompt = prompt[:157] + "…"
    return {
        "state": a.get("state") or "",
        "agentType": a.get("agentType") or "",
        "prompt": prompt,
        "toolName": a.get("toolName") or "",
        "interrupted": bool(a.get("interrupted")),
    }


_KILO_LINE_RE = re.compile(r"line=([A-Za-z0-9._-]+)/([A-Za-z0-9._-]+)")


def kilo_hint_from_checkout(path: str) -> dict:
    if not path or not Path(path).is_dir():
        return {}
    root = _run(["git", "-C", path, "rev-parse", "--show-toplevel"], timeout=3).strip()
    common = _run(["git", "-C", path, "rev-parse", "--git-common-dir"], timeout=3).strip()
    hint = {}
    if root:
        hint["git_root"] = root
    candidates = []
    if root:
        candidates.append(Path(root) / ".kilo-state")
    if common:
        c = Path(common)
        candidates.append(c.parent / ".kilo-state")
    seen: set[str] = set()
    entries: list[dict] = []
    for p in candidates:
        key = str(p)
        if key in seen or not p.is_file():
            continue
        seen.add(key)
        entries.extend(parse_kilo_state(p))
    cur = None
    for e in entries:
        wp = (e.get("worktree_path") or "").strip()
        if wp and wp not in {"-", "none"} and _same_path(wp, path):
            cur = e
            break
    if cur:
        hint["line"] = cur.get("project") or ""
        hint["session_id"] = cur.get("session_id") or ""
        hint["worktree_path"] = cur.get("worktree_path") or ""
    return hint


def kilo_hint_from_terminal(path: str) -> dict:
    term = _pick_existing_terminal(_orca_terminals_for(path))
    handle = str((term or {}).get("handle") or "")
    if not handle:
        return {}
    data = orca_json(["terminal", "read", "--terminal", handle, "--screen", "--limit", "80"])
    blob = ""
    if isinstance(data, dict):
        inner = data.get("terminal") or data
        tail = inner.get("tail") if isinstance(inner, dict) else None
        if isinstance(tail, list):
            blob = "\n".join(str(x) for x in tail)
        elif isinstance(inner, dict):
            blob = str(inner.get("text") or inner.get("output") or "")
    m = _KILO_LINE_RE.search(blob)
    if not m:
        return {}
    return {"parent": m.group(1), "line": m.group(2)}


def running_sessions() -> dict:
    sessions = []
    rows, live = orca_ps_rows()
    for t in rows:
        if t.get("isArchived"):
            continue
        agents = [_agent_brief(a) for a in (t.get("agents") or []) if isinstance(a, dict)]
        working = t.get("status") == "working" or any(a.get("state") == "working" for a in agents)
        kept = int(t.get("liveTerminalCount") or 0) > 0 or bool(t.get("hasAttachedPty"))
        if working:
            kind = "working"
        elif kept and agents:
            kind = "idle"
        else:
            continue
        path = t.get("path") or ""
        hint = kilo_hint_from_checkout(path)
        if not hint.get("line") and kind == "working":
            hint.update({k: v for k, v in kilo_hint_from_terminal(path).items() if v})
        sessions.append(
            {
                "path": path,
                "displayName": t.get("displayName") or "",
                "status": t.get("status") or "",
                "kind": kind,
                "workspaceStatus": t.get("workspaceStatus") or "",
                "liveTerminalCount": int(t.get("liveTerminalCount") or 0),
                "agents": agents,
                "kilo": hint,
            }
        )
    sessions.sort(key=lambda s: (0 if s["kind"] == "working" else 1, str(s.get("displayName") or "")))
    return {"ok": live, "sessions": sessions, "links": load_session_links()}


def session_map_file() -> Path:
    return ROOT / "_kilo-session-map.json"


def _link_key(path: str) -> str:
    try:
        return str(Path(path).expanduser().resolve())
    except OSError:
        return os.path.normpath(path)


def load_session_links() -> dict:
    p = session_map_file()
    if not p.is_file():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def save_session_link(wt: str, project: str, line: str) -> dict:
    wt = wt.strip()
    if not wt:
        return {"ok": False, "error": "no path"}
    links = load_session_links()
    key = _link_key(wt)
    if not project or not line:
        links.pop(key, None)
        links.pop(wt, None)
    else:
        tree = {p["id"]: {l["id"] for l in p["lines"]} for p in list_tree(ROOT)}
        if project not in tree or line not in tree[project]:
            return {"ok": False, "error": "line not found"}
        links[key] = {"project": project, "line": line}
    session_map_file().parent.mkdir(parents=True, exist_ok=True)
    session_map_file().write_text(
        json.dumps(links, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return {"ok": True, "links": links}


def _looks_like_line(path: str, display: str, project_id: str, line_id: str) -> bool:
    path = (path or "").replace("\\", "/")
    display = display or ""
    if not line_id:
        return False
    last = path.rstrip("/").split("/")[-1] if path else ""
    if last == line_id or display == line_id or display.startswith(line_id + " "):
        return True
    if f"/{line_id}/" in path + "/" or path.endswith("/" + line_id):
        return True
    slug = folder_alias(line_id, "")
    if slug and slug != line_id:
        if last == slug or display == slug or path.endswith("/" + slug):
            return True
    return False


def session_snapshot(root: Path, project_id: str, line_id: str) -> dict:
    tree = list_tree(root)
    proj = next((p for p in tree if p["id"] == project_id), None)
    line = next((l for l in (proj["lines"] if proj else []) if l["id"] == line_id), None)
    if not proj or not line:
        return {"ok": False, "error": "line not found"}
    repo_s = _first_repo((line.get("repos") or []) + (proj.get("repo_paths") or []))
    repo = Path(repo_s) if repo_s else None
    ctx = root / project_id / line_id / "context.md"
    ho = handoff_worktree(ctx)
    bindings = []
    state_files = []
    if repo:
        state_files.append(repo / ".kilo-state")
        common = _run(["git", "-C", str(repo), "rev-parse", "--git-common-dir"], timeout=3).strip()
        if common:
            state_files.append(Path(common).parent / ".kilo-state")
    for sp in state_files:
        if not sp.is_file():
            continue
        for ent in parse_kilo_state(sp):
            if ent.get("project") == line_id:
                bindings.append(ent)
    links = load_session_links()
    choices: dict[str, dict] = {}

    def upsert(path: str, **fields: object) -> dict | None:
        path = str(path or "").strip()
        if not path or path in {"-", "none"}:
            return None
        key = _link_key(path)
        cur = choices.get(key)
        if not cur:
            cur = {
                "path": path,
                "branch": "",
                "session_id": "",
                "binding_status": "",
                "source": "",
                "git": "missing",
                "primary": False,
                "displayName": "",
                "exec_status": "",
                "agents": [],
                "terminals": [],
            }
            choices[key] = cur
        for k, v in fields.items():
            if k == "terminals" and isinstance(v, list):
                cur["terminals"] = (cur.get("terminals") or []) + v
                continue
            if k == "agents" and isinstance(v, list):
                cur["agents"] = (cur.get("agents") or []) + v
                continue
            if v in ("", None, False) and cur.get(k):
                continue
            if v:
                cur[k] = v
        return cur

    for b in bindings:
        upsert(
            b.get("worktree_path") or "",
            session_id=b.get("session_id") or "",
            binding_status=b.get("status") or "",
            branch=b.get("worktree_branch") or "",
            source="kilo-state",
            primary=b.get("status") == "current",
        )
    upsert(
        ho.get("worktree_path") or line.get("worktree_path") or "",
        branch=ho.get("worktree_branch") or "",
        source="handoff",
        primary=True,
    )
    for raw, meta in links.items():
        if isinstance(meta, dict) and meta.get("project") == project_id and meta.get("line") == line_id:
            upsert(raw, source="map")
    if repo and repo.is_dir():
        for t in git_worktrees(repo):
            p = t.get("path") or ""
            if _looks_like_line(p, "", project_id, line_id):
                upsert(p, branch=t.get("branch") or "", source="git", git=git_dirty(Path(p)))
    ow = orca_json(["worktree", "list"])
    trees = ow.get("worktrees") if isinstance(ow, dict) else ow if isinstance(ow, list) else []
    for t in trees or []:
        if not isinstance(t, dict):
            continue
        p = str(t.get("path") or "")
        name = str(t.get("displayName") or "")
        if _looks_like_line(p, name, project_id, line_id) or any(_same_path(p, c["path"]) for c in choices.values()):
            upsert(
                p,
                displayName=name,
                source="orca",
            )
    ot = orca_json(["terminal", "list"])
    terms = _orca_term_rows(ot)
    for t in terms:
        tp = str(t.get("worktreePath") or "")
        title = str(t.get("title") or "")
        if not tp:
            continue
        if _looks_like_line(tp, title, project_id, line_id) or any(
            _same_path(tp, c["path"]) for c in choices.values()
        ):
            upsert(
                tp,
                source="orca",
                terminals=[
                    {
                        "title": title,
                        "connected": bool(t.get("connected")),
                        "handle": t.get("handle") or "",
                    }
                ],
            )
    for t in orca_ps_rows()[0]:
        p = str(t.get("path") or "")
        name = str(t.get("displayName") or "")
        if not (
            _looks_like_line(p, name, project_id, line_id)
            or any(_same_path(p, c["path"]) for c in choices.values())
        ):
            continue
        agents = [_agent_brief(a) for a in (t.get("agents") or []) if isinstance(a, dict)]
        upsert(
            p,
            displayName=name,
            exec_status=str(t.get("status") or ""),
            agents=agents,
            source="orca",
        )
    for cur in choices.values():
        p = Path(cur["path"]).expanduser()
        if p.is_dir():
            cur["git"] = git_dirty(p)
            if not cur.get("branch"):
                br = _run(["git", "-C", str(p), "rev-parse", "--abbrev-ref", "HEAD"], timeout=3).strip()
                if br and br != "HEAD":
                    cur["branch"] = br
        working = cur.get("exec_status") == "working" or any(
            a.get("state") == "working" for a in (cur.get("agents") or [])
        )
        live = working or any(t.get("connected") for t in (cur.get("terminals") or []))
        cur["working"] = working
        cur["live"] = live
        cur["kind"] = "working" if working else "idle" if live else "offline"
    choice_list = sorted(
        choices.values(),
        key=lambda c: (0 if c.get("working") else 1 if c.get("live") else 2, str(c.get("path"))),
    )
    primary = next((c for c in choice_list if c.get("primary")), choice_list[0] if choice_list else None)
    wt = (primary or {}).get("path") or ""
    jump = next((c["path"] for c in choice_list if c.get("live") or c.get("working")), wt)
    return {
        "ok": True,
        "project": project_id,
        "line": line_id,
        "repo": str(repo) if repo else "",
        "choices": choice_list,
        "worktree_path": wt,
        "orca_path": jump,
        "worktree_status": ho.get("worktree_status") or "",
        "live": any(c.get("live") for c in choice_list),
        "working": any(c.get("working") for c in choice_list),
    }


def _orca_term_rows(ot) -> list[dict]:
    if isinstance(ot, dict):
        rows = ot.get("terminals") or ot.get("items") or []
    elif isinstance(ot, list):
        rows = ot
    else:
        rows = []
    return [t for t in rows if isinstance(t, dict)]


def _orca_terminals_for(path: str) -> list[dict]:
    scoped = _orca_term_rows(orca_json(["terminal", "list", "--worktree", f"path:{path}"]))
    rows = scoped or _orca_term_rows(orca_json(["terminal", "list"]))
    out = []
    for t in rows:
        if path and not _same_path(str(t.get("worktreePath") or ""), path):
            continue
        out.append(t)
    return out


def _pick_existing_terminal(terms: list[dict]) -> dict | None:
    if not terms:
        return None

    def score(t: dict) -> tuple:
        title = str(t.get("title") or "").lower()
        grok = "grok" in title
        connected = bool(t.get("connected"))
        return (grok, connected, str(t.get("lastOutputAt") or 0))

    return max(terms, key=score)


def _focus_orca_app() -> None:
    """Bring Orca to the front, including minimized windows."""
    if sys.platform == "darwin":
        script = (
            'tell application "Orca" to reopen\n'
            'tell application "Orca" to activate\n'
            'tell application "System Events"\n'
            '  if exists process "Orca" then\n'
            '    tell process "Orca"\n'
            '      set frontmost to true\n'
            '      try\n'
            '        repeat with w in windows\n'
            '          try\n'
            '            set value of attribute "AXMinimized" of w to false\n'
            '          end try\n'
            '        end repeat\n'
            '      end try\n'
            '    end tell\n'
            '  end if\n'
            'end tell\n'
        )
        _run(["osascript", "-e", script], timeout=5)
        _run(["open", "-a", "Orca"], timeout=5)
    _run(["orca", "open", "--json"], timeout=8)


def session_open(path: str) -> dict:
    path = path.strip()
    if not path or path in {"-", "none"} or not Path(path).is_dir():
        return {"ok": False, "error": "no worktree"}
    existing = _pick_existing_terminal(_orca_terminals_for(path))
    handle = str((existing or {}).get("handle") or "")
    if handle:
        raw = _run(
            ["orca", "terminal", "switch", "--terminal", handle, "--json"],
            timeout=8,
        )
        if not raw.strip():
            return {"ok": False, "error": "switch failed", "handle": handle, "action": "switch"}
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {"raw": raw[:500]}
        _focus_orca_app()
        return {
            "ok": True,
            "action": "switch",
            "handle": handle,
            "title": existing.get("title") or "",
            "result": data.get("result", data) if isinstance(data, dict) else data,
        }
    raw = _run(
        [
            "orca",
            "terminal",
            "create",
            "--worktree",
            f"path:{path}",
            "--command",
            "grok",
            "--focus",
            "--json",
        ],
        timeout=12,
    )
    if not raw.strip():
        return {"ok": False, "error": "orca failed", "command": f"cd {path} && grok", "action": "create"}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        _focus_orca_app()
        return {"ok": True, "action": "create", "raw": raw[:500]}
    _focus_orca_app()
    return {"ok": True, "action": "create", "result": data.get("result", data)}


def _git_has_commit(repo: str, ref: str) -> bool:
    if not ref:
        return False
    code, _, _ = _run_full(
        ["git", "-C", repo, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
        timeout=3,
    )
    return code == 0


def repo_base_branch(repo: str) -> str:
    head = _run(
        ["git", "-C", repo, "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"],
        timeout=4,
    ).strip()
    cands = []
    if head.startswith("origin/"):
        cands.append(head.split("/", 1)[1])
    elif head:
        cands.append(head)
    cands.extend(["main", "master"])
    br = _run(["git", "-C", repo, "rev-parse", "--abbrev-ref", "HEAD"], timeout=3).strip()
    if br and br not in cands and br != "HEAD":
        cands.append(br)
    seen = set()
    for cand in cands:
        if not cand or cand in seen:
            continue
        seen.add(cand)
        if _git_has_commit(repo, cand) or _git_has_commit(repo, f"origin/{cand}"):
            return cand
    if _git_has_commit(repo, "HEAD"):
        return "HEAD"
    return ""


def ensure_git_commit(repo: str) -> str:
    base = repo_base_branch(repo)
    if base:
        return base
    br = _run(["git", "-C", repo, "symbolic-ref", "--short", "HEAD"], timeout=3).strip()
    if not br:
        _run_full(["git", "-C", repo, "checkout", "-B", "main"], timeout=5)
        br = "main"
    _run_full(["git", "-C", repo, "add", "-A"], timeout=30)
    code, _, _ = _run_full(
        [
            "git",
            "-C",
            repo,
            "-c",
            "user.name=kilo",
            "-c",
            "user.email=kilo@local",
            "commit",
            "--allow-empty",
            "-m",
            "init",
        ],
        timeout=8,
    )
    if code != 0:
        return ""
    return repo_base_branch(repo) or br


def grok_terminal_on_path(path: str, prompt: str, title: str = "") -> dict:
    cmd = [
        "orca",
        "terminal",
        "create",
        "--worktree",
        f"path:{path}",
        "--command",
        "grok",
        "--focus",
        "--json",
    ]
    if title:
        cmd = [
            "orca",
            "terminal",
            "create",
            "--worktree",
            f"path:{path}",
            "--title",
            title,
            "--command",
            "grok",
            "--focus",
            "--json",
        ]
    code, raw, err = _run_full(cmd, timeout=20)
    if code != 0 or not raw.strip():
        return {"ok": False, "error": orca_err_message(err, raw)}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {}
    inner = data.get("result", data) if isinstance(data, dict) else {}
    handle = ""
    if isinstance(inner, dict):
        start = inner.get("startupTerminal") if isinstance(inner.get("startupTerminal"), dict) else {}
        handle = str(
            inner.get("handle")
            or inner.get("agentTerminalHandle")
            or start.get("handle")
            or inner.get("terminalHandle")
            or ""
        )
    if handle and prompt:
        _run_full(
            [
                "orca",
                "terminal",
                "send",
                "--terminal",
                handle,
                "--text",
                prompt,
                "--enter",
                "--json",
            ],
            timeout=12,
        )
    _focus_orca_app()
    return {"ok": True, "action": "terminal", "handle": handle, "result": inner}


def orca_err_message(*blobs: str) -> str:
    for blob in blobs:
        s = (blob or "").strip()
        if not s:
            continue
        try:
            data = json.loads(s)
        except json.JSONDecodeError:
            if s.startswith("{"):
                continue
            return s[:280]
        if not isinstance(data, dict):
            continue
        err = data.get("error")
        if isinstance(err, dict):
            return str(err.get("message") or err.get("code") or "orca error")
        if err:
            return str(err)
        if data.get("ok") is False:
            return str(data.get("message") or "orca error")
    joined = " ".join(blobs)
    if "repo_not_found" in joined:
        return "Orca 里还没有登记这个仓库，自动添加失败。请确认本地路径是 git 仓库后重试。"
    return "orca worktree create failed"


def ascii_slug(raw: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", (raw or "").strip()).strip("-").lower()


def ensure_orca_repo(repo: str, base: str = "") -> None:
    _run_full(["orca", "repo", "add", "--path", repo, "--json"], timeout=25)
    if base:
        _run_full(
            [
                "orca",
                "repo",
                "set-base-ref",
                "--repo",
                f"path:{repo}",
                "--ref",
                base,
                "--json",
            ],
            timeout=10,
        )


def norm_agent(raw: str) -> str:
    a = (raw or "grok").strip().lower()
    aliases = {
        "grok": "grok",
        "codex": "codex",
        "cursor": "cursor",
        "cursor-agent": "cursor",
        "cursoragent": "cursor",
    }
    return aliases.get(a, "grok")


def unique_wt_name(repo: str, stem: str) -> str:
    stem = (ascii_slug(stem) or "new-line")[:40]
    taken = set()
    raw = _run(["git", "-C", repo, "worktree", "list"], timeout=4)
    for line in raw.splitlines():
        parts = line.split()
        if parts:
            taken.add(Path(parts[0]).name.lower())
    name = stem
    n = 2
    while name.lower() in taken:
        name = f"{stem}-{n}"
        n += 1
    return name


def line_new(project_id: str, name: str, title: str, agent: str = "grok") -> dict:
    title = (title or "").strip()
    name = (name or "").strip()
    agent = norm_agent(agent)
    if not title and name:
        title = name
    given = ascii_slug(name)[:48]
    if not project_id:
        return {"ok": False, "error": "缺少项目"}
    if not title and not given:
        return {"ok": False, "error": "需要标题"}
    tree = list_tree(ROOT)
    proj = next((p for p in tree if p["id"] == project_id), None)
    if not proj:
        return {"ok": False, "error": "project not found"}
    repo = _first_git_repo(proj.get("repo_paths") or [])
    if not repo:
        return {"ok": False, "error": "没有可用的 git 仓库路径"}
    stem = given or ascii_slug(title) or time.strftime("new-%Y-%m-%d-%H-%M")
    wt_name = unique_wt_name(repo, stem)
    base = repo_base_branch(repo)
    if given:
        new_cmd = f"Run `/kilo new {given}` under project `{project_id}`."
        if title:
            new_cmd += f" Line title: {title}."
    else:
        new_cmd = (
            f"The user title is: {title}\n"
            "Invent a short English kebab-case slug from that title "
            "(ascii, hyphenated, no pinyin dump). "
            f"Then run `/kilo new <slug>` under project `{project_id}` "
            "and set the line title to the user's Chinese (or original) title. "
            f"The Orca worktree folder `{wt_name}` is only a temp name, not the line id."
        )
    prompt = (
        f"KILO_WORKSPACE={ROOT}\n"
        f"Repo: {repo}\n"
        f"{new_cmd} "
        "Create the line, bind this session, allocate the primary worktree. Do not auto-execute."
    )
    if not base:
        base = ensure_git_commit(repo)
    if not base:
        return {"ok": False, "error": "仓库还没有 commit，无法新建 worktree"}
    ensure_orca_repo(repo, base)
    code, raw, err = _run_full(
        [
            "orca",
            "worktree",
            "create",
            "--repo",
            f"path:{repo}",
            "--name",
            wt_name,
            "--no-parent",
            "--activate",
            "--base-branch",
            base,
            "--agent",
            agent,
            "--prompt",
            prompt,
            "--json",
        ],
        timeout=45,
    )
    if code != 0 or not raw.strip():
        return {"ok": False, "error": orca_err_message(err, raw)}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {"ok": True, "raw": raw[:800], "slug": given or wt_name}
    if isinstance(data, dict) and data.get("ok") is False:
        return {"ok": False, "error": orca_err_message(raw, err)}
    return {
        "ok": True,
        "slug": given or wt_name,
        "result": data.get("result", data) if isinstance(data, dict) else data,
    }


def is_git_repo(path: str) -> bool:
    if not path:
        return False
    code, out, _ = _run_full(
        ["git", "-C", path, "rev-parse", "--is-inside-work-tree"], timeout=3
    )
    return code == 0 and "true" in (out or "").lower()


def _first_git_repo(paths: list) -> str:
    for r in paths:
        p = expand_repo_path(str(r))
        if p is not None and is_git_repo(str(p)):
            return str(p)
    return ""


def expand_repo_path(raw: str) -> Path | None:
    raw = str(raw or "").strip().strip('"').strip("'")
    if not raw or raw in {"origin", "path", "worktree", "ID", "---"}:
        return None
    if raw.startswith("~"):
        raw = str(Path.home()) + raw[1:]
    p = Path(raw).expanduser()
    if p.is_dir():
        return p.resolve()
    if "/" in raw and not raw.startswith("/") and "://" not in raw:
        for base in (Path.home() / "cosmos/go/src", Path.home() / "go/src"):
            cand = (base / raw).expanduser()
            if cand.is_dir():
                return cand.resolve()
    return None


def _first_repo(paths: list) -> str:
    for r in paths:
        p = expand_repo_path(str(r))
        if p is not None:
            return str(p)
    return ""


def session_create(project_id: str, line_id: str, agent: str = "grok") -> dict:
    agent = norm_agent(agent)
    if not project_id or not line_id:
        return {"ok": False, "error": "need project and line"}
    tree = list_tree(ROOT)
    proj = next((p for p in tree if p["id"] == project_id), None)
    line = next((l for l in (proj["lines"] if proj else []) if l["id"] == line_id), None)
    if not proj or not line:
        return {"ok": False, "error": "line not found"}
    repo = _first_git_repo((line.get("repos") or []) + (proj.get("repo_paths") or []))
    if not repo:
        return {"ok": False, "error": "没有可用的 git 仓库路径"}
    prompt = (
        f"KILO_WORKSPACE={ROOT}\n"
        f"Repo: {repo}\n"
        f"Run `/kilo bind {project_id}/{line_id}`.\n"
        "If this line has no primary worktree, allocate one and write Handoff. "
        "Do not run `/kilo new`. Do not auto-execute."
    )
    base = repo_base_branch(repo) or ensure_git_commit(repo)
    if not base:
        return {"ok": False, "error": "仓库还没有 commit，无法新建 worktree"}
    ensure_orca_repo(repo, base)
    code, raw, err = _run_full(
        [
            "orca",
            "worktree",
            "create",
            "--repo",
            f"path:{repo}",
            "--name",
            line_id[:48],
            "--no-parent",
            "--activate",
            "--base-branch",
            repo_base_branch(repo),
            "--agent",
            agent,
            "--prompt",
            prompt,
            "--json",
        ],
        timeout=45,
    )
    if code != 0 or not raw.strip():
        msg = orca_err_message(err, raw)
        if len(msg) > 400:
            msg = msg[:400]
        return {
            "ok": False,
            "error": msg,
            "command": f"cd {repo} && {agent}  # then /kilo bind {project_id}/{line_id}",
        }
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {"ok": True, "raw": raw[:800]}
    if isinstance(data, dict) and data.get("ok") is False:
        return {"ok": False, "error": str(data.get("error") or data)[:400]}
    return {"ok": True, "result": data.get("result", data) if isinstance(data, dict) else data}


def _mtime(path: Path) -> int:
    try:
        return path.stat().st_mtime_ns
    except OSError:
        return 0


def code_stamp() -> dict:
    ui = 0
    py = 0
    if STATIC.is_dir():
        for p in STATIC.iterdir():
            if p.suffix in {".html", ".css", ".js"}:
                ui = max(ui, _mtime(p))
    for p in VIEW_DIR.glob("*.py"):
        py = max(py, _mtime(p))
    return {"ui": ui, "py": py}


def restart_process() -> None:
    sys.stderr.write("kilo view: code changed, restarting\n")
    sys.stderr.flush()
    os.execv(sys.executable, [sys.executable, *sys.argv])


def start_code_watch() -> None:
    if getattr(sys, "frozen", False):
        return

    def loop() -> None:
        last = code_stamp()
        while True:
            time.sleep(0.7)
            now = code_stamp()
            if now["py"] != last["py"]:
                restart_process()
            last = now

    threading.Thread(target=loop, daemon=True).start()


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


def split_table_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    cells: list[str] = []
    buf: list[str] = []
    i = 0
    wiki = 0
    code = False
    while i < len(line):
        if line[i] == "`":
            code = not code
            buf.append("`")
            i += 1
            continue
        if not code and line.startswith("[[", i):
            wiki += 1
            buf.append("[[")
            i += 2
            continue
        if not code and wiki and line.startswith("]]", i):
            wiki -= 1
            buf.append("]]")
            i += 2
            continue
        if line[i] == "\\" and i + 1 < len(line) and line[i + 1] == "|":
            buf.append("|")
            i += 2
            continue
        if line[i] == "|" and not code and wiki == 0:
            cells.append("".join(buf).strip())
            buf = []
            i += 1
            continue
        buf.append(line[i])
        i += 1
    cells.append("".join(buf).strip())
    return cells


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
            headers = split_table_row(line)
            i += 2
            out.append("<table><thead><tr>" + "".join(f"<th>{md_inline(h, base_rel)}</th>" for h in headers) + "</tr></thead><tbody>")
            in_table = True
            continue
        if in_table:
            if re.match(r"^\|.+\|$", line):
                cells = split_table_row(line)
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


def parse_fm_src(src: str) -> dict:
    text = src.lstrip("\ufeff")
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    out = {}
    for line in text[3:end].splitlines():
        m = _FM_FIELD.match(line)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip().strip('"').strip("'")
        if key in {"title", "summary", "status", "created", "updated", "parent", "phase"}:
            out[key] = val
    return out


def parse_task_table(src: str) -> list[dict]:
    rows = []
    for line in strip_frontmatter(src).splitlines():
        if not _TASK_ROW.match(line):
            continue
        cells = split_table_row(line)
        if len(cells) < 3:
            continue
        raw = cells[2]
        rows.append(
            {
                "id": cells[0].strip(),
                "title": cells[1],
                "status": norm_task_status(raw),
                "deps": cells[3] if len(cells) > 3 else "",
                "block": cells[4] if len(cells) > 4 else "",
                "accept": cells[5] if len(cells) > 5 else "",
            }
        )
    return rows


_TOP_KV = re.compile(r"^(?:- )?([A-Za-z0-9_]+):\s*(.*)$")


def parse_loose_kv(text: str) -> list[tuple[str, object]]:
    lines = text.replace("\r\n", "\n").split("\n")
    out: list[tuple[str, object]] = []
    i = 0
    n = len(lines)

    def strip_q(s: str) -> str:
        return s.strip().strip('"').strip("'")

    while i < n:
        line = lines[i]
        if not line.strip() or line.startswith(" ") or line.startswith("\t"):
            i += 1
            continue
        m = _TOP_KV.match(line)
        if not m:
            i += 1
            continue
        key, rest = m.group(1), m.group(2).strip()
        i += 1
        if rest == "|":
            buf: list[str] = []
            while i < n and (lines[i].startswith("  ") or lines[i] == ""):
                if lines[i].startswith("  "):
                    buf.append(lines[i][2:])
                elif buf:
                    buf.append("")
                i += 1
            out.append((key, "\n".join(buf).strip()))
            continue
        if rest == "":
            items: list = []
            while i < n and lines[i].startswith("  "):
                sub = lines[i]
                i += 1
                sm = re.match(r"^  - (?:([A-Za-z0-9_]+):\s*)?(.*)$", sub)
                if not sm:
                    items.append(sub.strip())
                    continue
                if sm.group(1):
                    obj = {sm.group(1): strip_q(sm.group(2))}
                    while i < n:
                        km = re.match(r"^    ([A-Za-z0-9_]+):\s*(.*)$", lines[i])
                        if not km:
                            break
                        subk, subrest = km.group(1), km.group(2).strip()
                        i += 1
                        if subrest == "|":
                            buf2: list[str] = []
                            while i < n and (lines[i].startswith("      ") or lines[i] == ""):
                                if lines[i].startswith("      "):
                                    buf2.append(lines[i][6:])
                                elif buf2:
                                    buf2.append("")
                                i += 1
                            obj[subk] = "\n".join(buf2).strip()
                        elif subrest == "":
                            nested: list[str] = []
                            while i < n and lines[i].startswith("      - "):
                                nested.append(strip_q(lines[i][8:]))
                                i += 1
                            obj[subk] = nested
                        else:
                            obj[subk] = strip_q(subrest)
                    if "path" in obj and "note" in obj:
                        items.append(f"{obj['path']} — {obj['note']}")
                    else:
                        items.append(obj)
                else:
                    items.append(strip_q(sm.group(2)))
            out.append((key, items))
            continue
        out.append((key, strip_q(rest)))
    return out


def parse_dash_kv(text: str) -> list[tuple[str, object]]:
    return parse_loose_kv(text)


def split_h2(src: str) -> list[tuple[str, str]]:
    body = strip_frontmatter(src)
    parts: list[tuple[str, str]] = []
    title = ""
    buf: list[str] = []
    for line in body.splitlines():
        m = re.match(r"^##\s+(.*)$", line)
        if m:
            if title or buf:
                parts.append((title, "\n".join(buf).strip()))
            title = m.group(1).strip()
            buf = []
            continue
        buf.append(line)
    if title or buf:
        parts.append((title, "\n".join(buf).strip()))
    return parts


def _esc(s: str) -> str:
    return html.escape(s)


def render_tasks_html(src: str, base_rel: str) -> str:
    rows = parse_task_table(src)
    if not rows:
        return "<div class='kilo-empty'>还没有任务。</div>"
    trs = []
    for r in rows:
        cls = {
            "done": "st-done",
            "doing": "st-doing",
            "todo": "st-todo",
            "blocked": "st-blocked",
            "cancelled": "st-cancel",
        }.get(r["status"], "st-todo")
        trs.append(
            "<tr>"
            f"<td class='tid'>{_esc(r['id'])}</td>"
            f"<td>{md_inline(r['title'], base_rel)}</td>"
            f"<td><span class='st {cls}'>{_esc(r['status'])}</span></td>"
            f"<td class='mute'>{md_inline(r['deps'], base_rel) if r['deps'] not in ('', '-') else '—'}</td>"
            f"<td class='mute'>{md_inline(r['block'], base_rel) if r['block'] not in ('', '-') else '—'}</td>"
            f"<td>{md_inline(r['accept'], base_rel)}</td>"
            "</tr>"
        )
    return (
        "<div class='kilo-tasks'><table><thead><tr>"
        "<th>ID</th><th>任务</th><th>状态</th><th>依赖</th><th>阻塞</th><th>验收</th>"
        "</tr></thead><tbody>"
        + "".join(trs)
        + "</tbody></table></div>"
    )


def _kv_cell(k: str, v: object, base_rel: str) -> tuple[str, bool]:
    empty = False
    if isinstance(v, list):
        if not v:
            shown = "<span class='mute'>—</span>"
            empty = True
        elif v and isinstance(v[0], dict):
            heads = []
            for d in v:
                for hk in d:
                    if hk not in heads:
                        heads.append(hk)
            th = "".join(f"<th>{_esc(h)}</th>" for h in heads)
            trs = []
            for d in v:
                tds = "".join(f"<td>{md_inline(str(d.get(h, '')), base_rel)}</td>" for h in heads)
                trs.append(f"<tr>{tds}</tr>")
            shown = f"<table class='mini'><thead><tr>{th}</tr></thead><tbody>{''.join(trs)}</tbody></table>"
        else:
            shown = "<ul class='kv-list'>" + "".join(f"<li>{md_inline(str(x), base_rel)}</li>" for x in v) + "</ul>"
    else:
        s = str(v).strip()
        empty = s in ("", "[]", "none", "false")
        shown = "<span class='mute'>—</span>" if empty else md_inline(s, base_rel)
    cell = f"<div class='kv'><div class='k'>{_esc(k)}</div><div class='v'>{shown}</div></div>"
    return cell, empty


def _kv_html(pairs: list[tuple[str, object]], base_rel: str, highlight: set[str]) -> str:
    hot, rest = [], []
    for k, v in pairs:
        cell, empty = _kv_cell(k, v, base_rel)
        if k in highlight:
            hot.append(cell)
        elif not empty:
            rest.append(cell)
    html_out = ""
    if hot:
        html_out += "<div class='kv-hot'>" + "".join(hot) + "</div>"
    if rest:
        html_out += (
            f"<details class='kv-more'><summary>更多 {len(rest)} 项</summary>"
            f"<div class='kv-rest'>{''.join(rest)}</div></details>"
        )
    return html_out


def render_context_html(src: str, base_rel: str) -> str:
    chunks = []
    for title, body in split_h2(src):
        if title.lower() == "handoff":
            pairs = parse_dash_kv(body)
            chunks.append(
                "<section class='kilo-sec'><h2>Handoff</h2>"
                + _kv_html(
                    pairs,
                    base_rel,
                    {
                        "status",
                        "phase",
                        "blocker",
                        "next_action",
                        "last_completed",
                        "smoke_status",
                        "impl_review_status",
                        "worktree_status",
                        "worktree_path",
                        "worktree_branch",
                        "worktree_git_status",
                        "commit_status",
                    },
                )
                + "</section>"
            )
        else:
            label = title or "Notes"
            chunks.append(f"<section class='kilo-sec'><h2>{_esc(label)}</h2>{md_to_html(body, base_rel)}</section>")
    return "<div class='kilo-context'>" + "".join(chunks) + "</div>"


def render_line_html(src: str, base_rel: str) -> str:
    fm = parse_fm_src(src)
    body = strip_frontmatter(src)
    body = re.sub(r"^#\s+.*\n+", "", body.lstrip(), count=1)
    chips = []
    if fm.get("status"):
        live = fm["status"] in {"active", "open"}
        chips.append(f"<span class='chip{' on' if live else ''}'>{_esc(fm['status'])}</span>")
    if fm.get("parent"):
        chips.append(f"<span class='chip'>{_esc(fm['parent'])}</span>")
    if fm.get("updated"):
        chips.append(f"<span class='chip'>{_esc(fm['updated'])}</span>")
    head = f"<div class='kilo-chips'>{''.join(chips)}</div>" if chips else ""
    return f"<div class='kilo-line'>{head}{md_to_html(body, base_rel)}</div>"


def render_sections_html(src: str, base_rel: str) -> str:
    chunks = []
    for title, body in split_h2(src):
        if not title:
            if body.strip():
                chunks.append(md_to_html(body, base_rel))
            continue
        chunks.append(f"<section class='kilo-sec'><h2>{md_inline(title, base_rel)}</h2>{md_to_html(body, base_rel)}</section>")
    return "<div class='kilo-secs'>" + "".join(chunks) + "</div>"


def split_h3(src: str) -> list[tuple[str, str]]:
    parts: list[tuple[str, str]] = []
    title = ""
    buf: list[str] = []
    for line in src.splitlines():
        m = re.match(r"^###\s+(.*)$", line)
        if m:
            if title or buf:
                parts.append((title, "\n".join(buf).strip()))
            title = m.group(1).strip()
            buf = []
            continue
        buf.append(line)
    if title or buf:
        parts.append((title, "\n".join(buf).strip()))
    return parts


def render_round_yaml(pairs: list[tuple[str, object]], base_rel: str) -> str:
    data = dict(pairs)
    verdict = str(data.get("verdict") or "").strip()
    result = str(data.get("acceptance_result") or "").strip()
    ver = str(data.get("acceptance_version") or "").strip()
    summary = str(data.get("summary") or "").strip()
    findings = data.get("findings") or []
    vcls = "st-done" if verdict == "approve" else "st-blocked" if verdict in {"reject", "block"} else "st-todo"
    bits = []
    if verdict:
        bits.append(f"<span class='st {vcls}'>{_esc(verdict)}</span>")
    if result:
        bits.append(f"<span class='round-result'>{_esc(result)}</span>")
    if ver:
        bits.append(f"<span class='mute'>v{_esc(ver)}</span>")
    html_out = ""
    if bits:
        html_out += "<div class='round-meta'>" + "".join(bits) + "</div>"
    if summary:
        html_out += f"<p class='round-summary'>{md_inline(summary, base_rel)}</p>"
    if isinstance(findings, list) and findings and isinstance(findings[0], dict):
        heads = []
        for d in findings:
            for hk in ("id", "severity", "status", "title"):
                if hk in d and hk not in heads:
                    heads.append(hk)
            for hk in d:
                if hk not in heads:
                    heads.append(hk)
        th = "".join(f"<th>{_esc(h)}</th>" for h in heads)
        trs = []
        for d in findings:
            tds = "".join(f"<td>{md_inline(str(d.get(h, '')), base_rel)}</td>" for h in heads)
            trs.append(f"<tr>{tds}</tr>")
        html_out += (
            "<div class='round-findings'><table class='mini'><thead><tr>"
            + th
            + "</tr></thead><tbody>"
            + "".join(trs)
            + "</tbody></table></div>"
        )
    skip = {"verdict", "acceptance_result", "acceptance_version", "summary", "findings"}
    rest_pairs = [(k, v) for k, v in pairs if k not in skip]
    if rest_pairs:
        html_out += _kv_html(rest_pairs, base_rel, set())
    return html_out


def parse_dash_maps(text: str) -> list[dict]:
    wrapped = "items:\n" + "\n".join(
        ("  " + line) if line.strip() else line for line in text.splitlines()
    )
    data = dict(parse_loose_kv(wrapped))
    items = data.get("items") or []
    return [x for x in items if isinstance(x, dict)]


def _verdict_cls(verdict: str) -> str:
    v = verdict.strip().lower()
    if v in {"approve", "approved", "pass", "supported"}:
        return "st-done"
    if v in {"reject", "block", "blocked", "fail"}:
        return "st-blocked"
    if v in {"comment", "revise", "request_changes"}:
        return "st-doing"
    return "st-todo"


def render_review_claims(body: str, base_rel: str) -> str:
    claims = parse_dash_maps(body)
    if not claims:
        return md_to_html(body, base_rel)
    cards = []
    for c in claims:
        cid = _esc(str(c.get("id") or ""))
        task = _esc(str(c.get("task") or ""))
        claim = md_inline(str(c.get("claim") or ""), base_rel)
        hint = str(c.get("disproof_hint") or "").strip()
        traces = c.get("must_trace") or []
        if isinstance(traces, str):
            traces = [traces] if traces else []
        files = "".join(f"<code>{_esc(str(t))}</code>" for t in traces)
        cards.append(
            "<article class='claim-card'>"
            f"<div class='claim-id'>{cid}"
            + (f"<span class='mute'> · {task}</span>" if task else "")
            + "</div>"
            f"<p class='claim-text'>{claim}</p>"
            + (f"<div class='claim-files'>{files}</div>" if files else "")
            + (f"<p class='claim-hint'>反证：{md_inline(hint, base_rel)}</p>" if hint else "")
            + "</article>"
        )
    return "<div class='claim-grid'>" + "".join(cards) + "</div>"


def render_review_process(pairs: list[tuple[str, object]], base_rel: str) -> str:
    data = dict(pairs)
    status = str(data.get("status") or "").strip()
    cycle = str(data.get("cycle") or "").strip()
    updated = str(data.get("updated") or "").strip()
    rounds = data.get("rounds") or []
    if not isinstance(rounds, list):
        rounds = []
    scls = _verdict_cls(status if status != "open" else "doing")
    if status in {"resolved", "closed", "done"}:
        scls = "st-done"
    elif status in {"open", "active", "in_review"}:
        scls = "st-doing"
    bits = []
    if status:
        bits.append(f"<span class='st {scls}'>{_esc(status)}</span>")
    if cycle:
        bits.append(f"<span class='mute'>{_esc(cycle)} 轮</span>")
    if updated:
        bits.append(f"<span class='mute'>{_esc(updated)}</span>")
    head = "<div class='review-hero'>" + "".join(bits) + "</div>" if bits else ""
    items = []
    for i, rnd in enumerate(rounds):
        if not isinstance(rnd, dict):
            continue
        rid = str(rnd.get("id") or f"R{i+1}")
        verdict = str(rnd.get("verdict") or "").strip()
        result = str(rnd.get("acceptance_result") or "").strip()
        ver = str(rnd.get("acceptance_version") or "").strip()
        summary = str(rnd.get("summary") or "").strip()
        role = str(rnd.get("role") or "").strip()
        at = str(rnd.get("at") or "").strip()
        commit = str(rnd.get("commit") or "").strip()
        findings = rnd.get("findings") or []
        vcls = _verdict_cls(verdict)
        meta = []
        meta.append(f"<span class='st {vcls}'>{_esc(verdict or 'pending')}</span>")
        if result:
            meta.append(f"<span class='round-result'>{_esc(result)}</span>")
        if ver:
            meta.append(f"<span class='mute'>验收 v{_esc(ver)}</span>")
        if role:
            meta.append(f"<span class='mute'>{_esc(role)}</span>")
        if at:
            meta.append(f"<span class='mute'>{_esc(at)}</span>")
        if commit and commit != "uncommitted":
            meta.append(f"<code>{_esc(commit[:8])}</code>")
        elif commit == "uncommitted":
            meta.append("<span class='mute'>未提交</span>")
        find_html = ""
        if isinstance(findings, list) and findings and isinstance(findings[0], dict):
            find_html = "<ul class='find-list'>" + "".join(
                f"<li><strong>{_esc(str(f.get('id') or ''))}</strong> "
                f"{md_inline(str(f.get('title') or f.get('summary') or ''), base_rel)}"
                f"<span class='st {_verdict_cls(str(f.get('status') or f.get('severity') or ''))}'>"
                f"{_esc(str(f.get('status') or f.get('severity') or ''))}</span></li>"
                for f in findings
            ) + "</ul>"
        items.append(
            "<article class='tl-item'>"
            f"<div class='tl-mark'></div>"
            f"<h3>{_esc(rid)}</h3>"
            f"<div class='round-meta'>{''.join(meta)}</div>"
            + (f"<p class='round-summary'>{md_inline(summary, base_rel)}</p>" if summary else "")
            + find_html
            + "</article>"
        )
    body = "<div class='timeline'>" + "".join(items) + "</div>" if items else "<p class='kilo-empty'>还没有审查回合。</p>"
    return "<section class='kilo-sec'><h2>审查过程</h2>" + head + body + "</section>"


def render_review_thread(body: str, base_rel: str) -> str:
    chunks = []
    for title, block in split_h3(body):
        if not title:
            if block.strip():
                chunks.append(md_to_html(block, base_rel))
            continue
        yaml_m = re.search(r"```ya?ml\n(.*?)```", block, re.S)
        inner = ""
        rest = block
        if yaml_m:
            pairs = parse_loose_kv(yaml_m.group(1))
            inner = render_round_yaml(pairs, base_rel)
            rest = (block[: yaml_m.start()] + block[yaml_m.end() :]).strip()
        if rest:
            inner += md_to_html(rest, base_rel)
        chunks.append(f"<section class='kilo-sec thread'><h3>{_esc(title)}</h3>{inner}</section>")
    return "<div class='kilo-thread'>" + "".join(chunks) + "</div>"


def render_review_html(src: str, base_rel: str) -> str:
    chunks = []
    for title, body in split_h2(src):
        low = title.lower()
        if low == "acceptance":
            pairs = parse_loose_kv(body)
            data = dict(pairs)
            prompt = str(data.get("user_prompt") or "").strip()
            pass_bar = str(data.get("pass_bar") or "").strip()
            status = str(data.get("status") or "").strip()
            ver = str(data.get("version") or "").strip()
            constraints = data.get("constraints") or []
            chips = []
            if status:
                chips.append(f"<span class='st {_verdict_cls(status)}'>{_esc(status)}</span>")
            if ver:
                chips.append(f"<span class='mute'>v{_esc(ver)}</span>")
            extra = [(k, v) for k, v in pairs if k not in {"user_prompt", "pass_bar", "status", "version", "constraints"}]
            cons = ""
            if isinstance(constraints, list) and constraints:
                cons = "<ul class='kv-list'>" + "".join(
                    f"<li>{md_inline(str(x), base_rel)}</li>" for x in constraints
                ) + "</ul>"
            inner = ""
            if chips:
                inner += "<div class='review-hero'>" + "".join(chips) + "</div>"
            if prompt:
                prose = "<br>".join(md_inline(ln, base_rel) if ln.strip() else "" for ln in prompt.splitlines())
                inner += f"<blockquote class='review-prompt'>{prose}</blockquote>"
            if pass_bar:
                inner += f"<div class='review-pass'><div class='k'>通过标准</div><div class='v'>{md_inline(pass_bar, base_rel)}</div></div>"
            if cons:
                inner += "<div class='review-cons'><div class='k'>约束</div>" + cons + "</div>"
            inner += _kv_html(extra, base_rel, {"spec_anchors", "supersedes", "updated"})
            chunks.append("<section class='kilo-sec'><h2>验收标准</h2>" + inner + "</section>")
        elif low == "claims":
            chunks.append("<section class='kilo-sec'><h2>主张</h2>" + render_review_claims(body, base_rel) + "</section>")
        elif low in {"reviewthread", "review thread"}:
            pairs = parse_loose_kv(body)
            if dict(pairs).get("rounds"):
                chunks.append(render_review_process(pairs, base_rel))
            else:
                chunks.append(
                    "<section class='kilo-sec'><h2>审查过程</h2>"
                    + render_review_thread(body, base_rel)
                    + "</section>"
                )
        elif low == "reviewindex":
            chunks.append(f"<section class='kilo-sec'><h2>发现索引</h2>{md_to_html(body, base_rel)}</section>")
        else:
            label = title or "Notes"
            chunks.append(f"<section class='kilo-sec'><h2>{_esc(label)}</h2>{md_to_html(body, base_rel)}</section>")
    return "<div class='kilo-review'>" + "".join(chunks) + "</div>"


def render_kilo_file(name: str, src: str, base_rel: str) -> tuple[str, str]:
    if name == "tasks.md":
        return "tasks", render_tasks_html(src, base_rel)
    if name == "context.md":
        return "context", render_context_html(src, base_rel)
    if name in {"line.md", "workstream.md"}:
        return "line", render_line_html(src, base_rel)
    if name == "review.md":
        return "review", render_review_html(src, base_rel)
    if name in {"spec.md", "ops.md"}:
        return name[:-3], render_sections_html(src, base_rel)
    return "md", md_to_html(src, base_rel)


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
            if target.suffix == ".css":
                ctype = "text/css"
            elif target.suffix == ".js":
                ctype = "application/javascript"
            elif target.suffix == ".woff2":
                ctype = "font/woff2"
            else:
                ctype = "application/octet-stream"
            self._send(200, target.read_bytes(), ctype)
            return
        if path == "/api/tree":
            projects = list_tree(ROOT)
            payload = json.dumps(
                {
                    "root": str(ROOT),
                    "name": "Kilo",
                    "version": app_version(),
                    "display_name": display_name(),
                    "activity": activity_grid(ROOT),
                    "orca": orca_status(),
                    "projects": projects,
                    "facts": list_facts(ROOT, projects),
                }
            ).encode()
            self._send(200, payload, "application/json; charset=utf-8")
            return
        if path == "/api/stamp":
            payload = json.dumps(workspace_stamp(ROOT)).encode()
            self._send(200, payload, "application/json; charset=utf-8")
            return
        if path == "/api/skills":
            payload = json.dumps(list_skills()).encode()
            self._send(200, payload, "application/json; charset=utf-8")
            return
        if path == "/api/skill":
            name = (qs.get("name") or [""])[0]
            payload = json.dumps(skill_detail(str(name))).encode()
            self._send(200, payload, "application/json; charset=utf-8")
            return
        if path == "/api/code-stamp":
            payload = json.dumps(code_stamp()).encode()
            self._send(200, payload, "application/json; charset=utf-8")
            return
        if path == "/api/session":
            project_id = (qs.get("project") or [""])[0]
            line_id = (qs.get("line") or [""])[0]
            payload = json.dumps(session_snapshot(ROOT, project_id, line_id)).encode()
            self._send(200, payload, "application/json; charset=utf-8")
            return
        if path == "/api/running":
            payload = json.dumps(running_sessions()).encode()
            self._send(200, payload, "application/json; charset=utf-8")
            return
        if path in ("/api/html", "/render"):
            rel = (qs.get("path") or [""])[0]
            target = safe_join(ROOT, rel)
            if target is None or not target.is_file() or target.suffix != ".md":
                self._send(404, b"not found", "text/plain")
                return
            text = target.read_text(encoding="utf-8", errors="replace")
            kind, converted = render_kilo_file(target.name, text, rel)
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
                    "</head>"
                    f"<body class='doc kilo-{html.escape(kind)}'>"
                    f"{converted}</body></html>"
                ).encode()
                self._send(200, page, "text/html; charset=utf-8")
                return
            body = json.dumps({"path": rel, "html": converted, "title": target.name}).encode()
            self._send(200, body, "application/json; charset=utf-8")
            return
        self._send(404, b"not found", "text/plain")

    def do_POST(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        path = posixpath.normpath(parsed.path)
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if n else b"{}"
        try:
            body = json.loads(raw.decode() or "{}")
        except json.JSONDecodeError:
            self._send(400, b'{"ok":false}', "application/json; charset=utf-8")
            return
        if path == "/api/session/open":
            payload = json.dumps(session_open(str(body.get("path") or ""))).encode()
            self._send(200, payload, "application/json; charset=utf-8")
            return
        if path == "/api/session/create":
            payload = json.dumps(
                session_create(
                    str(body.get("project") or ""),
                    str(body.get("line") or ""),
                    str(body.get("agent") or "grok"),
                )
            ).encode()
            self._send(200, payload, "application/json; charset=utf-8")
            return
        if path == "/api/project/order":
            raw_ids = body.get("ids") or []
            ids = [str(x) for x in raw_ids] if isinstance(raw_ids, list) else []
            raw_pin = body.get("pinned")
            pinned = [str(x) for x in raw_pin] if isinstance(raw_pin, list) else None
            payload = json.dumps(save_project_order(ids, pinned)).encode()
            self._send(200, payload, "application/json; charset=utf-8")
            return
        if path == "/api/line/status":
            payload = json.dumps(
                set_line_status(
                    str(body.get("project") or ""),
                    str(body.get("line") or ""),
                    str(body.get("status") or ""),
                )
            ).encode()
            self._send(200, payload, "application/json; charset=utf-8")
            return
        if path == "/api/pick-folder":
            picked = ""
            err = ""
            try:
                import tkinter as tk
                from tkinter import filedialog

                root = tk.Tk()
                root.withdraw()
                root.attributes("-topmost", True)
                picked = filedialog.askdirectory(title="选择仓库目录") or ""
                root.destroy()
            except Exception as exc:
                err = str(exc)
            payload = json.dumps(
                {"ok": bool(picked), "path": picked, "error": err}
            ).encode()
            self._send(200, payload, "application/json; charset=utf-8")
            return
        if path == "/api/workspace":
            payload = json.dumps(set_workspace(str(body.get("root") or ""))).encode()
            self._send(200, payload, "application/json; charset=utf-8")
            return
        if path == "/api/workspace/init":
            payload = json.dumps(init_workspace(str(body.get("root") or ""))).encode()
            self._send(200, payload, "application/json; charset=utf-8")
            return
        if path == "/api/setup/orca":
            payload = json.dumps(open_orca_install()).encode()
            self._send(200, payload, "application/json; charset=utf-8")
            return
        if path == "/api/project/create":
            payload = json.dumps(
                create_project(
                    str(body.get("title") or ""),
                    str(body.get("name") or ""),
                    str(body.get("summary") or ""),
                    str(body.get("repo") or ""),
                )
            ).encode()
            self._send(200, payload, "application/json; charset=utf-8")
            return
        if path == "/api/project/delete":
            payload = json.dumps(delete_project(str(body.get("project") or ""))).encode()
            self._send(200, payload, "application/json; charset=utf-8")
            return
        if path == "/api/skill/delete":
            payload = json.dumps(
                delete_skill(
                    str(body.get("name") or ""),
                    str(body.get("source") or ""),
                )
            ).encode()
            self._send(200, payload, "application/json; charset=utf-8")
            return
        if path == "/api/line/alias":
            payload = json.dumps(
                set_line_alias(
                    str(body.get("project") or ""),
                    str(body.get("line") or ""),
                    str(body.get("alias") or ""),
                )
            ).encode()
            self._send(200, payload, "application/json; charset=utf-8")
            return
        if path == "/api/project/alias":
            payload = json.dumps(
                set_project_alias(
                    str(body.get("project") or ""),
                    str(body.get("alias") or ""),
                )
            ).encode()
            self._send(200, payload, "application/json; charset=utf-8")
            return
        if path == "/api/line/new":
            payload = json.dumps(
                line_new(
                    str(body.get("project") or ""),
                    str(body.get("name") or ""),
                    str(body.get("title") or ""),
                    str(body.get("agent") or "grok"),
                )
            ).encode()
            self._send(200, payload, "application/json; charset=utf-8")
            return
        if path == "/api/session/link":
            payload = json.dumps(
                save_session_link(
                    str(body.get("path") or ""),
                    str(body.get("project") or ""),
                    str(body.get("line") or ""),
                )
            ).encode()
            self._send(200, payload, "application/json; charset=utf-8")
            return
        self._send(404, b"not found", "text/plain")


def main() -> None:
    global ROOT
    p = argparse.ArgumentParser(description="Kilo Workspace board server")
    p.add_argument("--root", default=os.environ.get("KILO_WORKSPACE", ""), help="Projects/ folder, or its parent")
    p.add_argument("--port", type=int, default=8765)
    args = p.parse_args()
    if not args.root:
        sys.stderr.write("set --root or KILO_WORKSPACE\n")
        sys.exit(2)
    got = set_workspace(args.root)
    if not got.get("ok"):
        sys.stderr.write(got.get("error") or "bad workspace\n")
        sys.exit(2)
    start_code_watch()
    httpd = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"kilo view  http://127.0.0.1:{args.port}  root={ROOT}", flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
