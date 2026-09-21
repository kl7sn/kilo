const treeEl = document.getElementById("tree");
const labelEl = document.getElementById("nav-label");
const docEl = document.getElementById("doc");
const crumbEl = document.getElementById("crumb");

let catalog = { root: "", projects: [] };
let loc = { level: "workspace", projectId: "", lineId: "", file: "" };

function projectById(id) {
  return catalog.projects.find((p) => p.id === id);
}

function lineById(proj, id) {
  return proj && proj.lines.find((l) => l.id === id);
}

function row(text, { active, muted, onClick } = {}) {
  const b = document.createElement("button");
  b.className = "row" + (active ? " active" : "") + (muted ? " muted-row" : "");
  b.textContent = text;
  if (onClick) b.onclick = onClick;
  return b;
}

function renderCrumb() {
  crumbEl.innerHTML = "";
  const add = (label, fn) => {
    if (crumbEl.childNodes.length) {
      const sep = document.createElement("span");
      sep.className = "sep";
      sep.textContent = "/";
      crumbEl.appendChild(sep);
    }
    const b = document.createElement("button");
    b.className = "crumb";
    b.textContent = label;
    b.onclick = fn;
    crumbEl.appendChild(b);
  };
  add("workspace", () => goWorkspace());
  if (loc.projectId) add(loc.projectId, () => goProject(loc.projectId));
  if (loc.lineId) add(loc.lineId, () => goLine(loc.projectId, loc.lineId));
  if (loc.file) {
    const sep = document.createElement("span");
    sep.className = "sep";
    sep.textContent = "/";
    crumbEl.appendChild(sep);
    const span = document.createElement("span");
    span.textContent = loc.file.split("/").pop();
    crumbEl.appendChild(span);
  }
}

function renderNav() {
  treeEl.innerHTML = "";
  if (loc.level === "workspace") {
    labelEl.textContent = "Workspace";
    if (!catalog.projects.length) {
      treeEl.textContent = "未找到 Projects/";
      return;
    }
    for (const proj of catalog.projects) {
      treeEl.appendChild(
        row(proj.id, {
          active: loc.projectId === proj.id && !loc.lineId,
          onClick: () => goProject(proj.id),
        })
      );
    }
    return;
  }
  if (loc.level === "project") {
    const proj = projectById(loc.projectId);
    labelEl.textContent = "Project";
    treeEl.appendChild(row("← workspace", { muted: true, onClick: () => goWorkspace() }));
    treeEl.appendChild(
      row("project.md", {
        active: loc.file === proj.path,
        onClick: () => openFile(proj.path),
      })
    );
    for (const line of proj.lines) {
      treeEl.appendChild(
        row(line.id, {
          active: loc.lineId === line.id,
          onClick: () => goLine(proj.id, line.id),
        })
      );
    }
    return;
  }
  const proj = projectById(loc.projectId);
  const line = lineById(proj, loc.lineId);
  labelEl.textContent = "Line";
  treeEl.appendChild(row("← " + proj.id, { muted: true, onClick: () => goProject(proj.id) }));
  for (const f of line.files) {
    treeEl.appendChild(
      row(f.name, {
        active: loc.file === f.path,
        onClick: () => openFile(f.path),
      })
    );
  }
}

function goWorkspace() {
  loc = { level: "workspace", projectId: "", lineId: "", file: "" };
  docEl.removeAttribute("src");
  renderNav();
  renderCrumb();
}

function goProject(id) {
  const proj = projectById(id);
  loc = { level: "project", projectId: id, lineId: "", file: proj.path };
  openFile(proj.path);
  renderNav();
  renderCrumb();
}

function goLine(projectId, lineId) {
  const proj = projectById(projectId);
  const line = lineById(proj, lineId);
  const first = line.files[0];
  loc = {
    level: "line",
    projectId,
    lineId,
    file: first ? first.path : "",
  };
  if (first) openFile(first.path);
  renderNav();
  renderCrumb();
}

function openFile(rel) {
  loc.file = rel;
  docEl.src = "/render?path=" + encodeURIComponent(rel);
  renderNav();
  renderCrumb();
}

async function loadTree() {
  const res = await fetch("/api/tree");
  catalog = await res.json();
  goWorkspace();
}

loadTree();
