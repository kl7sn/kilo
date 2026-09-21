const wsEl = document.getElementById("col-workspace");
const projEl = document.getElementById("col-project");
const lineEl = document.getElementById("col-line");
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

function empty(text) {
  const d = document.createElement("div");
  d.className = "col-empty";
  d.textContent = text;
  return d;
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
  add("workspace", () => selectProject(""));
  if (loc.projectId) add(loc.projectId, () => selectProject(loc.projectId));
  if (loc.lineId) add(loc.lineId, () => selectLine(loc.projectId, loc.lineId));
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

function fillWorkspace() {
  wsEl.innerHTML = "";
  if (!catalog.projects.length) {
    wsEl.appendChild(empty("未找到 Projects/"));
    return;
  }
  for (const proj of catalog.projects) {
    wsEl.appendChild(
      row(proj.id, {
        active: loc.projectId === proj.id,
        onClick: () => selectProject(proj.id),
      })
    );
  }
}

function fillProject() {
  projEl.innerHTML = "";
  const proj = projectById(loc.projectId);
  if (!proj) {
    projEl.appendChild(empty("选择 project"));
    return;
  }
  projEl.appendChild(
    row("project.md", {
      active: loc.file === proj.path && !loc.lineId,
      onClick: () => {
        loc.lineId = "";
        openFile(proj.path);
      },
    })
  );
  for (const line of proj.lines) {
    projEl.appendChild(
      row(line.id, {
        active: loc.lineId === line.id,
        onClick: () => selectLine(proj.id, line.id),
      })
    );
  }
}

function fillLine() {
  lineEl.innerHTML = "";
  const proj = projectById(loc.projectId);
  const line = lineById(proj, loc.lineId);
  if (!line) {
    lineEl.appendChild(empty("选择 line"));
    return;
  }
  for (const f of line.files) {
    lineEl.appendChild(
      row(f.name, {
        active: loc.file === f.path,
        onClick: () => openFile(f.path),
      })
    );
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

function paint() {
  fillWorkspace();
  fillProject();
  fillLine();
  renderCrumb();
}

async function loadTree() {
  const res = await fetch("/api/tree");
  catalog = await res.json();
  paint();
}

loadTree();
