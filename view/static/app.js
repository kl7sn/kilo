const docEl = document.getElementById("doc");
const crumbEl = document.getElementById("crumb");

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

function paint() {
  renderCrumb();
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

loadTree();
setInterval(checkStamp, 1500);
