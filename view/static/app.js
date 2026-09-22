const docEl = document.getElementById("doc");
const crumbEl = document.getElementById("crumb");
const homeEl = document.getElementById("home");
const readerEl = document.getElementById("reader");
const heroEl = document.getElementById("home-hero");
const gridEl = document.getElementById("card-grid");
const navHome = document.getElementById("nav-home");

let catalog = { root: "", projects: [] };
let loc = { projectId: "", lineId: "", file: "" };

function projectById(id) {
  return catalog.projects.find((p) => p.id === id);
}

function lineById(proj, id) {
  return proj && proj.lines.find((l) => l.id === id);
}

function row(text, { active, onClick } = {}) {
  const b = document.createElement("button");
  b.className = "row" + (active ? " active" : "");
  b.textContent = text;
  if (onClick) b.onclick = onClick;
  return b;
}

function crumbNode(label, items, onLabelClick) {
  const wrap = document.createElement("div");
  wrap.className = "crumb-item";
  const btn = document.createElement("button");
  btn.className = "crumb";
  btn.textContent = label;
  btn.onclick = onLabelClick;
  wrap.appendChild(btn);
  if (items && items.length) {
    const menu = document.createElement("div");
    menu.className = "menu";
    for (const it of items) menu.appendChild(it);
    wrap.appendChild(menu);
  }
  return wrap;
}

function sep() {
  const s = document.createElement("span");
  s.className = "sep";
  s.textContent = "/";
  return s;
}

function renderCrumb() {
  crumbEl.innerHTML = "";
  const proj = projectById(loc.projectId);
  const line = lineById(proj, loc.lineId);

  const projectItems = catalog.projects.map((p) =>
    row(p.id, { active: loc.projectId === p.id, onClick: () => selectProject(p.id) })
  );
  crumbEl.appendChild(
    crumbNode("workspace", projectItems, () => selectProject(""))
  );

  if (proj) {
    crumbEl.appendChild(sep());
    const lineItems = [
      row("project.md", {
        active: loc.file === proj.path && !loc.lineId,
        onClick: () => {
          loc.lineId = "";
          openFile(proj.path);
        },
      }),
      ...proj.lines.map((l) =>
        row(l.id, { active: loc.lineId === l.id, onClick: () => selectLine(proj.id, l.id) })
      ),
    ];
    crumbEl.appendChild(crumbNode(proj.id, lineItems, () => selectProject(proj.id)));
  }

  if (proj && line) {
    crumbEl.appendChild(sep());
    const fileItems = line.files.map((f) =>
      row(f.name, { active: loc.file === f.path, onClick: () => openFile(f.path) })
    );
    crumbEl.appendChild(crumbNode(line.id, fileItems, () => selectLine(proj.id, line.id)));
  }

  if (loc.file) {
    crumbEl.appendChild(sep());
    const name = loc.file.split("/").pop();
    const fileBtn = document.createElement("span");
    fileBtn.className = "muted";
    fileBtn.textContent = name;
    crumbEl.appendChild(fileBtn);
  }
}

function selectProject(id) {
  if (!id) {
    loc = { projectId: "", lineId: "", file: "" };
    docEl.removeAttribute("src");
    paint();
    return;
  }
  const proj = projectById(id);
  loc = { projectId: id, lineId: "", file: proj.path };
  openFile(proj.path);
}

function selectLine(projectId, lineId) {
  const proj = projectById(projectId);
  const line = lineById(proj, lineId);
  const first = line.files[0];
  loc = { projectId, lineId, file: first ? first.path : "" };
  if (first) openFile(first.path);
  else paint();
}

function openFile(rel) {
  loc.file = rel;
  docEl.src = "/render?path=" + encodeURIComponent(rel);
  paint();
}

function locateFromPath(rel) {
  const parts = rel.replace(/\\/g, "/").split("/").filter(Boolean);
  if (parts[0] !== "Projects" || parts.length < 2) {
    loc = { projectId: "", lineId: "", file: rel };
    return;
  }
  loc.projectId = parts[1];
  if (parts.length >= 4 || (parts.length === 3 && !parts[2].endsWith(".md"))) {
    loc.lineId = parts[2];
  } else {
    loc.lineId = "";
  }
  loc.file = rel;
}

window.addEventListener("message", (ev) => {
  const data = ev.data;
  if (!data || data.type !== "kilo-open" || !data.path) return;
  locateFromPath(data.path);
  if (docEl.src.indexOf("path=" + encodeURIComponent(data.path)) === -1) {
    openFile(data.path);
  } else {
    paint();
  }
});

docEl.addEventListener("load", () => {
  try {
    const u = new URL(docEl.contentWindow.location.href);
    if (u.pathname !== "/render") return;
    const p = u.searchParams.get("path");
    if (!p) return;
    locateFromPath(p);
    paint();
  } catch (err) {
    /* ignore cross-origin */
  }
});

function hello() {
  const h = new Date().getHours();
  if (h < 5) return "夜深了";
  if (h < 12) return "早上好";
  if (h < 18) return "下午好";
  return "晚上好";
}

function showHome() {
  loc = { projectId: "", lineId: "", file: "" };
  docEl.removeAttribute("src");
  homeEl.hidden = false;
  readerEl.hidden = true;
  navHome.classList.add("active");
  const nProj = catalog.projects.length;
  const nLine = catalog.projects.reduce((n, p) => n + p.lines.length, 0);
  heroEl.innerHTML =
    `<div class="hero-copy"><h1>${hello()}</h1><p>浏览 workspace 里的 project 和 line，只读。</p></div>` +
    `<div class="hero-stats">` +
    `<div class="stat"><svg viewBox="0 0 24 24" width="18" height="18"><path fill="currentColor" d="M10 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z"/></svg><div><div class="stat-l">项目</div><div class="stat-n">${nProj}</div></div></div>` +
    `<div class="stat"><svg viewBox="0 0 24 24" width="18" height="18"><path fill="currentColor" d="M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zm4 18H6V4h7v5h5v11z"/></svg><div><div class="stat-l">line</div><div class="stat-n">${nLine}</div></div></div>` +
    `</div>`;
  gridEl.innerHTML = "";
  for (const p of catalog.projects) {
    const card = document.createElement("article");
    card.className = "space-card";
    const n = p.lines.length;
    card.innerHTML =
      `<div class="space-top"><svg viewBox="0 0 24 24" width="18" height="18"><path fill="currentColor" d="M10 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z"/></svg><div class="space-name">${p.id}</div></div>` +
      `<p class="space-meta">${n} 条 line</p>` +
      `<div class="space-foot"><div class="pills"><span class="pill on">活跃</span><span class="pill">本地</span></div><button type="button" class="text-btn">打开</button></div>`;
    const open = () => selectProject(p.id);
    card.querySelector(".text-btn").onclick = (ev) => {
      ev.stopPropagation();
      open();
    };
    card.onclick = open;
    gridEl.appendChild(card);
  }
}

function showReader() {
  homeEl.hidden = true;
  readerEl.hidden = false;
  navHome.classList.remove("active");
  renderCrumb();
}

function paint() {
  if (!loc.projectId) showHome();
  else showReader();
}

async function loadTree() {
  const res = await fetch("/api/tree");
  catalog = await res.json();
  paint();
}

let stampKey = "";

async function checkStamp() {
  try {
    const s = await fetch("/api/stamp").then((r) => r.json());
    const key = s.n + ":" + s.t;
    if (!stampKey) {
      stampKey = key;
      return;
    }
    if (key === stampKey) return;
    stampKey = key;
    await loadTree();
    if (loc.file) {
      docEl.src = "/render?path=" + encodeURIComponent(loc.file) + "&t=" + s.t;
    }
  } catch (err) {
    /* server briefly down */
  }
}

let codeKey = "";

async function checkCode() {
  try {
    const s = await fetch("/api/code-stamp").then((r) => r.json());
    const key = s.ui + ":" + s.py;
    if (!codeKey) {
      codeKey = key;
      return;
    }
    if (key === codeKey) return;
    codeKey = key;
    location.reload();
  } catch (err) {
    /* restarting */
  }
}

navHome.onclick = () => selectProject("");

loadTree();
setInterval(checkStamp, 1500);
setInterval(checkCode, 800);
