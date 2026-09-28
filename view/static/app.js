const docEl = document.getElementById("doc");
const homeEl = document.getElementById("home");
const sessionsPage = document.getElementById("sessions-page");
const readerEl = document.getElementById("reader");
const heroEl = document.getElementById("home-hero");
const runningEl = document.getElementById("running");
const sessionsFilters = document.getElementById("sessions-filters");
const sessionsSub = document.getElementById("sessions-sub");

const gridEl = document.getElementById("card-grid");
const navHome = document.getElementById("nav-home");
const navCount = document.getElementById("nav-count");
const navSessions = document.getElementById("nav-sessions");
const navLive = document.getElementById("nav-live");
const navMemory = document.getElementById("nav-memory");
const navFacts = document.getElementById("nav-facts");
const navSkills = document.getElementById("nav-skills");
const navSkillsN = document.getElementById("nav-skills-n");
const memoryPage = document.getElementById("memory-page");
const memoryList = document.getElementById("memory-list");
const skillsPage = document.getElementById("skills-page");
const skillList = document.getElementById("skill-list");
const skillSearch = document.getElementById("skill-search");
const skillFilters = document.getElementById("skill-filters");
const skillsN = document.getElementById("skills-n");
const railEl = document.getElementById("rail");
const topHome = document.getElementById("top-home");
const lineSearch = document.getElementById("line-search");
const lineListEl = document.getElementById("line-list");
const detailTitle = document.getElementById("detail-title");
const detailProject = document.getElementById("detail-project");
const detailId = document.getElementById("detail-id");
const detailDesc = document.getElementById("detail-desc");
const detailStats = document.getElementById("detail-stats");
const detailTabs = document.getElementById("detail-tabs");
const sessionView = document.getElementById("session-view");

const FILE_TABS = [
  { name: "line.md", label: "Line", icon: "icLine" },
  { name: "workstream.md", label: "Line", icon: "icLine" },
  { name: "tasks.md", label: "Tasks", icon: "icTasks" },
  { name: "context.md", label: "Context", icon: "icContext" },
  { name: "spec.md", label: "Spec", icon: "icSpec" },
  { name: "review.md", label: "Review", icon: "icReview" },
  { name: "ops.md", label: "Ops", icon: "icOps" },
  { name: "project.md", label: "Project", icon: "icFolder" },
];

let catalog = { root: "", projects: [], facts: [] };
let loc = { projectId: "", lineId: "", file: "" };
let homeView = "projects";
let sessionFilter = "";

function projectById(id) {
  return catalog.projects.find((p) => p.id === id);
}

function projectAlias(p) {
  if (!p) return "";
  return p.alias || p.id;
}

function lineAlias(l) {
  if (!l) return "";
  if (l.alias) return l.alias;
  if (l.title && l.title !== l.id) return l.title;
  return l.id;
}

let skipCardClick = false;

function projectIds() {
  return catalog.projects.map((p) => p.id);
}

function pinnedIds() {
  return catalog.projects.filter((p) => p.pinned).map((p) => p.id);
}

function applyProjectLayout(ids, pinned) {
  const pinSet = new Set(pinned);
  const pinRank = new Map(pinned.map((id, i) => [id, i]));
  const rest = ids.filter((id) => !pinSet.has(id));
  const restRank = new Map(rest.map((id, i) => [id, i]));
  for (const p of catalog.projects) p.pinned = pinSet.has(p.id);
  catalog.projects.sort((a, b) => {
    if (a.pinned !== b.pinned) return a.pinned ? -1 : 1;
    if (a.pinned) return (pinRank.get(a.id) ?? 0) - (pinRank.get(b.id) ?? 0);
    return (restRank.get(a.id) ?? 9999) - (restRank.get(b.id) ?? 9999);
  });
  showHome();
  fetch("/api/project/order", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ids: [...pinned, ...rest], pinned }),
  }).catch(() => {});
}

function placeProject(fromId, toId) {
  if (!fromId || fromId === toId) return;
  const target = projectById(toId);
  if (!target) return;
  let pinned = pinnedIds().filter((id) => id !== fromId);
  let rest = catalog.projects.filter((p) => !p.pinned && p.id !== fromId).map((p) => p.id);
  if (target.pinned) {
    const i = Math.max(0, pinned.indexOf(toId));
    pinned.splice(i, 0, fromId);
  } else {
    const i = Math.max(0, rest.indexOf(toId));
    rest.splice(i, 0, fromId);
  }
  applyProjectLayout([...pinned, ...rest], pinned);
}

function moveProject(id, where) {
  const proj = projectById(id);
  if (!proj) return;
  const group = catalog.projects.filter((p) => !!p.pinned === !!proj.pinned).map((p) => p.id);
  const i = group.indexOf(id);
  if (i < 0) return;
  group.splice(i, 1);
  if (where === "start") group.unshift(id);
  else group.push(id);
  const pinned = proj.pinned ? group : pinnedIds();
  const rest = proj.pinned ? catalog.projects.filter((p) => !p.pinned).map((p) => p.id) : group;
  applyProjectLayout([...pinned, ...rest], pinned);
}

function togglePin(id) {
  const pinned = pinnedIds().filter((x) => x !== id);
  if (!projectById(id)?.pinned) pinned.unshift(id);
  applyProjectLayout(projectIds(), pinned);
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

function firstDoingLine(proj) {
  if (!proj) return null;
  const active = proj.lines.filter((l) => (l.status || "active") === "active");
  return active.find((l) => (l.task_status || {}).doing > 0) || active[0] || null;
}

function openProjectHome(id) {
  lineSearch.value = "";
  const proj = projectById(id);
  if (!proj) return;
  loc = { projectId: id, lineId: "", file: proj.path };
  openFile(proj.path);
}

function selectProject(id) {
  lineSearch.value = "";
  if (!id) {
    loc = { projectId: "", lineId: "", file: "" };
    docEl.removeAttribute("src");
    paint();
    return;
  }
  const proj = projectById(id);
  const line = firstDoingLine(proj);
  if (line) selectLine(id, line.id);
  else openProjectHome(id);
}

function preferredFile(files) {
  const order = ["line.md", "workstream.md", "tasks.md", "context.md", "spec.md"];
  for (const name of order) {
    const f = files.find((x) => x.name === name);
    if (f) return f.path;
  }
  return files[0] ? files[0].path : "";
}

function selectLine(projectId, lineId) {
  loc = { projectId, lineId, file: "__session__" };
  openSessions();
}

function openFile(rel) {
  loc.file = rel;
  stopSessionWatch();
  sessionView.hidden = true;
  docEl.hidden = false;
  if (rel && rel !== "__session__") {
    docEl.src = "/render?path=" + encodeURIComponent(rel);
  }
  paint();
}

function openSessions() {
  stopLiveWatch();
  loc.file = "__session__";
  docEl.hidden = true;
  sessionView.hidden = false;
  paint();
  loadSession();
  startSessionWatch();
}

let sessionPoll = 0;

function startSessionWatch() {
  stopSessionWatch();
  sessionPoll = setInterval(() => {
    if (document.hidden || loc.file !== "__session__") return;
    loadSession({ quiet: true });
  }, 12000);
}

function stopSessionWatch() {
  if (sessionPoll) clearInterval(sessionPoll);
  sessionPoll = 0;
}

function locateFromPath(rel) {
  const parts = rel.replace(/\\/g, "/").split("/").filter(Boolean);
  if (parts[0] === "Projects") parts.shift();
  if (!parts.length) {
    loc = { projectId: "", lineId: "", file: rel };
    return;
  }
  loc.projectId = parts[0];
  if (parts.length >= 3 || (parts.length === 2 && !parts[1].endsWith(".md"))) {
    loc.lineId = parts[1];
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

const icFolder =
  '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M3.5 7.25A1.75 1.75 0 0 1 5.25 5.5h4.1c.32 0 .63.13.85.35L12 7.5h6.75A1.75 1.75 0 0 1 20.5 9.25v8A1.75 1.75 0 0 1 18.75 19h-13.5A1.75 1.75 0 0 1 3.5 17.25V7.25z"/></svg>';
const icFile =
  '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M14 3H7.5A1.5 1.5 0 0 0 6 4.5v15A1.5 1.5 0 0 0 7.5 21h9A1.5 1.5 0 0 0 18 19.5V8.5L14 3z"/><path d="M14 3v5.5H18"/></svg>';
const icLink =
  '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.07 0l1.41-1.41a5 5 0 0 0-7.07-7.07L10 5.93"/><path d="M14 11a5 5 0 0 0-7.07 0L5.52 12.4a5 5 0 0 0 7.07 7.07L14 18.07"/></svg>';
const icMore =
  '<svg class="icon" viewBox="0 0 24 24" fill="currentColor"><circle cx="5" cy="12" r="1.6"/><circle cx="12" cy="12" r="1.6"/><circle cx="19" cy="12" r="1.6"/></svg>';
const icPin =
  '<svg class="space-pin-mark" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M16 9V4h1V2H7v2h1v5l-2 3v2h5.2v6h1.6v-6H18v-2l-2-3z"/></svg>';
const icList =
  '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M9 6h12M9 12h12M9 18h12"/><path d="M4.5 6h.01M4.5 12h.01M4.5 18h.01"/></svg>';
const icTasks =
  '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M9 6h12M9 12h12M9 18h12"/><path d="M3.2 6.2l1.3 1.3L7 4.8"/><path d="M3.2 12.2l1.3 1.3L7 10.8"/><rect x="3" y="16.2" width="3.2" height="3.2" rx="0.6"/></svg>';
const icContext =
  '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M5 7h10a3 3 0 0 1 3 3v7H8a3 3 0 0 1-3-3V7z"/><path d="M8 7V5.5A1.5 1.5 0 0 1 9.5 4H18"/><path d="M9 12h6M9 15h4"/></svg>';
const icSpec =
  '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3.5h6L18 7.5V19a1.5 1.5 0 0 1-1.5 1.5h-8A1.5 1.5 0 0 1 7 19V5A1.5 1.5 0 0 1 8.5 3.5H8z"/><path d="M14 3.5V8h4"/><path d="M9.5 12h5M9.5 15.5h3.5"/></svg>';
const icReview =
  '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><circle cx="10.5" cy="10.5" r="5.5"/><path d="M15 15.5L20 20.5"/><path d="M8.2 10.5l1.6 1.6 3-3.2"/></svg>';
const icOps =
  '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><rect x="3.5" y="5" width="17" height="14" rx="2"/><path d="M7 10l2.5 2L7 14M12 14h5"/></svg>';
const icSessions =
  '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M5 6.5h10A2.5 2.5 0 0 1 17.5 9v5A2.5 2.5 0 0 1 15 16.5H9l-4 3v-3H5A2.5 2.5 0 0 1 2.5 14V9A2.5 2.5 0 0 1 5 6.5z"/><path d="M17.2 8.5h1.3A2.5 2.5 0 0 1 21 11v4.5A2.5 2.5 0 0 1 18.5 18h-.5"/></svg>';
const icLine =
  '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><circle cx="6.5" cy="6.5" r="2.2"/><circle cx="17.5" cy="17.5" r="2.2"/><path d="M8 8.2v4.3A4 4 0 0 0 12 16.5h3"/></svg>';
const icPages =
  '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M7 7.5V5.5A1.5 1.5 0 0 1 8.5 4h6L18 7.5V17a1.5 1.5 0 0 1-1.5 1.5H8.5A1.5 1.5 0 0 1 7 17V7.5z"/><path d="M14 4v4h4"/><path d="M5.5 9v9A1.5 1.5 0 0 0 7 19.5h8"/></svg>';

function hello() {
  const h = new Date().getHours();
  let g = "你好";
  if (h < 5) g = "夜深了";
  else if (h < 12) g = "早上好";
  else if (h < 14) g = "中午好";
  else if (h < 18) g = "下午好";
  else g = "晚上好";
  const name = catalog.display_name || "";
  return name ? `${g}，${esc(name)}` : g;
}

function heatLevel(n, max) {
  if (!n) return 0;
  if (max <= 1) return 2;
  const t = n / max;
  if (t > 0.72) return 4;
  if (t > 0.45) return 3;
  if (t > 0.2) return 2;
  return 1;
}

function renderHeat() {
  const act = catalog.activity || {};
  const days = act.days || [];
  if (!days.length) return "";
  const max = days.reduce((m, d) => Math.max(m, d.n || 0), 0);
  const weeks = Math.ceil(days.length / 7);
  const monthAt = [];
  let lastM = "";
  let lastCol = -4;
  days.forEach((d, i) => {
    if (i % 7 !== 0) return;
    const dt = new Date(d.date + "T00:00:00");
    const m = `${dt.getMonth() + 1}月`;
    const col = i / 7;
    if (m !== lastM && col - lastCol >= 3) {
      monthAt.push({ col, label: m });
      lastCol = col;
      lastM = m;
    } else if (m !== lastM) {
      lastM = m;
    }
  });
  const months = monthAt
    .map((x) => `<span class="heat-month" style="grid-column:${x.col + 1}">${esc(x.label)}</span>`)
    .join("");
  const cells = days
    .map((d) => {
      const lv = heatLevel(d.n || 0, max);
      const title = `${d.date} · ${d.n || 0} 次更新`;
      return `<span class="heat-cell lv${lv}" title="${esc(title)}"></span>`;
    })
    .join("");
  const cols = `repeat(${weeks}, minmax(0, 1fr))`;
  const open = localStorage.getItem("kilo-heat-open") !== "0";
  return (
    `<div class="heat${open ? "" : " is-collapsed"}">` +
    `<button type="button" class="heat-toggle" aria-expanded="${open ? "true" : "false"}">` +
    `<span class="heat-title">活动</span>` +
    `<span class="heat-chev">›</span>` +
    `</button>` +
    `<div class="heat-plot">` +
    `<div class="heat-months" style="grid-template-columns:${cols}">${months}</div>` +
    `<div class="heat-dow"><span>Mon</span><span></span><span>Wed</span><span></span><span>Fri</span><span></span><span>Sun</span></div>` +
    `<div class="heat-grid" style="grid-template-columns:${cols}">${cells}</div>` +
    `</div></div>`
  );
}

function factCount() {
  return (catalog.facts || []).reduce((n, g) => n + (g.items || []).length, 0);
}

function setRailNav(which) {
  navHome.classList.toggle("active", which === "projects");
  navSessions.classList.toggle("active", which === "sessions");
  navMemory.classList.toggle("active", which === "memory");
  navSkills.classList.toggle("active", which === "skills");
  navCount.textContent = String(catalog.projects.length);
  navFacts.textContent = String(factCount());
}

function showHome() {
  closeFloatingMenus();
  homeView = "projects";
  loc = { projectId: "", lineId: "", file: "" };
  docEl.removeAttribute("src");
  homeEl.hidden = false;
  sessionsPage.hidden = true;
  memoryPage.hidden = true;
  skillsPage.hidden = true;
  readerEl.hidden = true;
  railEl.hidden = false;
  setRailNav("projects");
  const nProj = catalog.projects.length;
  const nLine = catalog.projects.reduce((n, p) => n + p.lines.length, 0);
  const nTask = catalog.projects.reduce((n, p) => n + (p.tasks || 0), 0);
  const nFile = catalog.projects.reduce((n, p) => {
    if (typeof p.files === "number") return n + p.files;
    return n + p.lines.reduce((m, l) => m + l.files.length, 0) + 1;
  }, 0);
  const nLineActive = catalog.projects.reduce(
    (n, p) => n + ((p.line_status && p.line_status.active) || 0),
    0
  );
  const nTaskDone = catalog.projects.reduce(
    (n, p) => n + ((p.task_status && p.task_status.done) || 0),
    0
  );
  const nTaskDoing = catalog.projects.reduce(
    (n, p) => n + ((p.task_status && p.task_status.doing) || 0),
    0
  );
  const stat = (icon, label, n, sub) =>
    `<div class="stat">${icon}<div class="stat-text"><div class="stat-label">${label}</div><div class="stat-n">${n}</div><div class="stat-sub">${
      sub || ""
    }</div></div></div>`;
  const taskSub = [
    nTaskDoing ? `${nTaskDoing} 进行中` : "",
    nTaskDone ? `${nTaskDone} 已完成` : "",
  ]
    .filter(Boolean)
    .join(" ");
  heroEl.innerHTML =
    `<div class="hero-copy"><h1>${hello()}</h1></div>` +
    renderSetup() +
    (catalog.projects.length ? renderHeat() : "");
  gridEl.innerHTML = "";
  bindSetup(heroEl);
  const heatToggle = heroEl.querySelector(".heat-toggle");
  if (heatToggle) {
    heatToggle.onclick = () => {
      const box = heatToggle.closest(".heat");
      const open = box.classList.toggle("is-collapsed");
      const shown = !open;
      heatToggle.setAttribute("aria-expanded", shown ? "true" : "false");
      localStorage.setItem("kilo-heat-open", shown ? "1" : "0");
    };
  }
  if (!catalog.projects.length && (catalog.orca || {}).ok) {
    const miss = document.createElement("div");
    miss.className = "home-empty";
    const root = catalog.root || "";
    miss.innerHTML =
      `<p>当前目录还没有 project。</p>` +
      `<p class="home-empty-path">${esc(root)}</p>` +
      `<p>用右上角「新建项目」，或选一个已有的 <code>Projects</code> 文件夹。</p>` +
      `<button type="button" class="new-line-btn" data-pick-ws="1">选择工作区</button>`;
    miss.querySelector("[data-pick-ws]").onclick = (ev) => {
      ev.stopPropagation();
      pickWorkspace();
    };
    gridEl.appendChild(miss);
  }
  for (const p of catalog.projects) {
    const card = document.createElement("article");
    card.className = "space-card" + (p.pinned ? " is-pinned" : "");
    card.dataset.project = p.id;
    card.innerHTML =
      `<div class="space-top">` +
      `<div class="space-title">${icFolder}<div class="space-copy"><div class="space-name">${projectAlias(p)}</div>${
        projectAlias(p) !== p.id ? `<div class="space-id">${p.id}</div>` : ""
      }</div></div>` +
      `<div class="space-more-wrap">` +
      (p.pinned ? `<span class="space-pin-wrap" title="已置顶">${icPin}</span>` : "") +
      `<button type="button" class="space-more" title="更多" aria-label="更多">${icMore}</button>` +
      `<div class="menu card-menu">` +
      `<button type="button" class="row" data-rename>重命名</button>` +
      `<button type="button" class="row" data-pin>${p.pinned ? "取消置顶" : "置顶"}</button>` +
      `<button type="button" class="row" data-move="start">移动到最前</button>` +
      `<button type="button" class="row" data-move="end">移动到最后</button>` +
      `<button type="button" class="row" data-delete>删除</button>` +
      `</div>` +
      `</div>` +
      `</div>` +
      `<div class="space-lines"></div>` +
      `<div class="space-foot"><button type="button" class="text-btn">打开工作区</button></div>`;
    paintCardLines(card, p);
    const open = () => selectProject(p.id);
    card.querySelector(".text-btn").onclick = (ev) => {
      ev.stopPropagation();
      open();
    };
    card.querySelector(".space-title").onclick = (ev) => {
      ev.stopPropagation();
      open();
    };
    const more = card.querySelector(".space-more");
    const cardMenu = card.querySelector(".card-menu");
    more.onclick = (ev) => {
      ev.stopPropagation();
      const openNow = !cardMenu.classList.contains("open");
      document.querySelectorAll(".card-menu.open").forEach((m) => m.classList.remove("open"));
      cardMenu.classList.toggle("open", openNow);
    };
    cardMenu.querySelector("[data-rename]").onclick = (ev) => {
      ev.stopPropagation();
      cardMenu.classList.remove("open");
      openAliasModal(p.id);
    };
    cardMenu.querySelector("[data-pin]").onclick = (ev) => {
      ev.stopPropagation();
      cardMenu.classList.remove("open");
      togglePin(p.id);
    };
    cardMenu.querySelector("[data-move='start']").onclick = (ev) => {
      ev.stopPropagation();
      cardMenu.classList.remove("open");
      moveProject(p.id, "start");
    };
    cardMenu.querySelector("[data-move='end']").onclick = (ev) => {
      ev.stopPropagation();
      cardMenu.classList.remove("open");
      moveProject(p.id, "end");
    };
    cardMenu.querySelector("[data-delete]").onclick = (ev) => {
      ev.stopPropagation();
      cardMenu.classList.remove("open");
      openDeleteModal(p.id);
    };
    card.draggable = true;
    card.ondragstart = (ev) => {
      if (ev.target.closest("button, .menu, a, input")) {
        ev.preventDefault();
        return;
      }
      skipCardClick = true;
      ev.dataTransfer.setData("text/plain", p.id);
      ev.dataTransfer.effectAllowed = "move";
      card.classList.add("dragging");
    };
    card.ondragend = () => {
      card.classList.remove("dragging");
      document.querySelectorAll(".space-card.drag-over").forEach((n) => n.classList.remove("drag-over"));
      setTimeout(() => {
        skipCardClick = false;
      }, 0);
    };
    card.ondragover = (ev) => {
      ev.preventDefault();
      ev.dataTransfer.dropEffect = "move";
      card.classList.add("drag-over");
    };
    card.ondragleave = () => card.classList.remove("drag-over");
    card.ondrop = (ev) => {
      ev.preventDefault();
      ev.stopPropagation();
      card.classList.remove("drag-over");
      const from = ev.dataTransfer.getData("text/plain");
      if (from) placeProject(from, p.id);
    };
    gridEl.appendChild(card);
  }
  document.querySelectorAll(".card-menu").forEach((m) => {
    m.onclick = (ev) => ev.stopPropagation();
  });
  startLiveWatch();
  if (runningCache) applyRunning(tagRunning(runningCache));
  loadRunning();
}

function showSessionsPage(projectId) {
  homeView = "sessions";
  sessionFilter = projectId || "";
  loc = { projectId: "", lineId: "", file: "" };
  docEl.removeAttribute("src");
  homeEl.hidden = true;
  sessionsPage.hidden = false;
  memoryPage.hidden = true;
  skillsPage.hidden = true;
  readerEl.hidden = true;
  railEl.hidden = false;
  setRailNav("sessions");
  startLiveWatch();
  if (runningCache) applyRunning(tagRunning(runningCache));
  loadRunning();
}

function samePath(a, b) {
  if (!a || !b) return false;
  const n = (p) => String(p).replace(/\/+$/, "").toLowerCase();
  return n(a) === n(b);
}

let sessionLinks = {};

function matchByLineId(lineId, gitRoot) {
  if (!lineId) return null;
  const hits = [];
  for (const p of catalog.projects) {
    for (const l of p.lines) {
      if (l.id === lineId) hits.push({ projectId: p.id, lineId: l.id, repos: l.repos || [] });
    }
  }
  if (!hits.length) return null;
  if (gitRoot) {
    const hit = hits.find((h) => h.repos.some((r) => samePath(r, gitRoot)));
    if (hit) return { projectId: hit.projectId, lineId: hit.lineId };
  }
  return { projectId: hits[0].projectId, lineId: hits[0].lineId };
}

function matchRunning(path, displayName, kilo) {
  for (const [k, v] of Object.entries(sessionLinks)) {
    if (v && v.project && v.line && samePath(k, path)) {
      return { projectId: v.project, lineId: v.line, manual: true };
    }
  }
  if (kilo && kilo.parent && kilo.line) {
    const proj = projectById(kilo.parent);
    if (proj && lineById(proj, kilo.line)) {
      return { projectId: kilo.parent, lineId: kilo.line };
    }
  }
  if (kilo && kilo.line && kilo.worktree_path && samePath(kilo.worktree_path, path)) {
    const viaState = matchByLineId(kilo.line, kilo.git_root);
    if (viaState) return viaState;
  }
  const segs = String(path || "")
    .replace(/\/+$/, "")
    .split("/");
  const last = segs[segs.length - 1] || "";
  for (const p of catalog.projects) {
    for (const l of p.lines) {
      if (samePath(l.worktree_path, path)) return { projectId: p.id, lineId: l.id };
      if (last && last === l.id) return { projectId: p.id, lineId: l.id };
      if (segs.includes(l.id)) return { projectId: p.id, lineId: l.id };
      if (displayName && (displayName === l.id || displayName === l.title || displayName === lineAlias(l))) {
        return { projectId: p.id, lineId: l.id };
      }
    }
  }
  return null;
}

function openLineSessions(projectId, lineId) {
  loc.projectId = projectId;
  loc.lineId = lineId;
  openSessions();
}

function fillLineSelect(sel, projectId, current) {
  sel.innerHTML = "";
  const proj = projectById(projectId);
  const lines = (proj ? proj.lines : []).filter(
    (l) => isLiveLine(l) || l.id === current
  );
  if (!lines.length) {
    sel.appendChild(new Option("没有未关闭的 line", ""));
    return;
  }
  for (const l of lines) {
    const label = lineAlias(l) === l.id ? l.id : `${lineAlias(l)}  (${l.id})`;
    sel.appendChild(new Option(label, l.id, false, l.id === current));
  }
}

function showLinkPick(row, path) {
  row.querySelector(".link-pick")?.remove();
  const box = document.createElement("div");
  box.className = "link-pick";
  const projSel = document.createElement("select");
  const lineSel = document.createElement("select");
  catalog.projects.forEach((p) =>
    projSel.appendChild(new Option(`${projectAlias(p)}  (${p.id})`, p.id))
  );
  fillLineSelect(lineSel, projSel.value);
  projSel.onchange = () => fillLineSelect(lineSel, projSel.value);
  const ok = document.createElement("button");
  ok.type = "button";
  ok.className = "running-jump";
  ok.textContent = "确定";
  ok.onclick = async (ev) => {
    ev.stopPropagation();
    if (!projSel.value || !lineSel.value) return;
    ok.disabled = true;
    try {
      const r = await fetch("/api/session/link", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          path,
          project: projSel.value,
          line: lineSel.value,
        }),
      }).then((x) => x.json());
      if (!r.ok) {
        ok.disabled = false;
        ok.textContent = r.error || "失败";
        return;
      }
      if (r.links) sessionLinks = r.links;
      box.remove();
      await loadRunning({ force: true });
    } catch (err) {
      ok.disabled = false;
      ok.textContent = "失败";
    }
  };
  const cancel = document.createElement("button");
  cancel.type = "button";
  cancel.className = "running-link";
  cancel.textContent = "取消";
  cancel.onclick = (ev) => {
    ev.stopPropagation();
    box.remove();
  };
  box.onclick = (ev) => ev.stopPropagation();
  box.append(projSel, lineSel, ok, cancel);
  row.appendChild(box);
}

async function jumpToOrca(path, btn) {
  if (!path) return;
  const el = btn || document.body;
  const canLabel = el.childElementCount === 0;
  const label = canLabel ? el.textContent : "";
  if (el.disabled !== undefined) el.disabled = true;
  if (canLabel) el.textContent = "打开中…";
  else el.classList.add("is-opening");
  try {
    const r = await fetch("/api/session/open", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path }),
    }).then((x) => x.json());
    if (el.disabled !== undefined) el.disabled = false;
    el.classList.remove("is-opening");
    if (canLabel) {
      el.textContent = r.ok
        ? r.action === "switch"
          ? "已打开"
          : "已新开"
        : r.error || "失败";
      setTimeout(() => {
        el.textContent = label;
      }, 1800);
    }
  } catch (err) {
    if (el.disabled !== undefined) el.disabled = false;
    el.classList.remove("is-opening");
    if (canLabel) el.textContent = "失败";
  }
}

let livePoll = 0;

function startLiveWatch() {
  stopLiveWatch();
  livePoll = setInterval(() => {
    if (document.hidden || railEl.hidden) return;
    if (runningEl.querySelector(".link-pick")) return;
    loadRunning();
  }, 12000);
}

function stopLiveWatch() {
  if (livePoll) clearInterval(livePoll);
  livePoll = 0;
}

function restoreRunningCache() {
  try {
    const data = JSON.parse(localStorage.getItem("kilo-running-cache") || "null");
    if (!data || !Array.isArray(data.sessions) || !data.sessions.length) return null;
    if (data.links && typeof data.links === "object") sessionLinks = data.links;
    return data.sessions;
  } catch (err) {
    return null;
  }
}

function persistRunningCache(tagged) {
  try {
    localStorage.setItem(
      "kilo-running-cache",
      JSON.stringify({ sessions: tagged, links: sessionLinks })
    );
  } catch (err) {
    /* quota */
  }
}

function tagRunning(sessions) {
  return (sessions || []).map((s) => ({
    ...s,
    hit: matchRunning(s.path, s.displayName, s.kilo) || s.hit || null,
  }));
}

let runningCache = restoreRunningCache();
let runningInflight = null;

async function loadRunning(opts) {
  if (!opts?.force && runningEl.querySelector(".link-pick")) return;
  if (runningInflight) return runningInflight;
  runningInflight = (async () => {
    try {
      const data = await fetch("/api/running").then((r) => r.json());
      const sessions = data && data.ok !== false ? data.sessions || [] : [];
      if (!data || data.ok === false || !sessions.length) {
        if (runningCache) applyRunning(tagRunning(runningCache));
        return;
      }
      sessionLinks = data.links || sessionLinks;
      runningCache = tagRunning(sessions);
      persistRunningCache(runningCache);
      applyRunning(runningCache);
    } catch (err) {
      if (runningCache) applyRunning(tagRunning(runningCache));
    } finally {
      runningInflight = null;
    }
  })();
  return runningInflight;
}

function applyRunning(tagged) {
  tagged = tagged || [];
  const workingN = tagged.filter((s) => s.kind === "working").length;
  navLive.textContent = String(workingN);
  document.querySelectorAll(".space-card[data-project]").forEach((card) => {
    const p = projectById(card.dataset.project);
    if (p) paintCardLines(card, p);
  });
  if (sessionsPage.hidden) return;
  if (runningEl.querySelector(".link-pick")) return;
  renderSessionFilters(tagged);
  const visible = sessionFilter
    ? tagged.filter((s) => s.hit && s.hit.projectId === sessionFilter)
    : tagged;
  if (!visible.length) {
    runningEl.innerHTML = sessionFilter
      ? "<p class='session-muted'>这个项目现在没有挂着的 Orca 会话。</p>"
      : "<p class='session-muted'>现在没有挂着的 Orca 会话。</p>";
    return;
  }
  runningEl.innerHTML = "";
  const buckets = new Map();
  for (const s of visible) {
    const pid = s.hit ? s.hit.projectId : "";
    if (!buckets.has(pid)) buckets.set(pid, []);
    buckets.get(pid).push(s);
  }
  const order = catalog.projects.map((p) => p.id).filter((id) => buckets.has(id));
  if (!sessionFilter && buckets.has("")) order.push("");
  for (const pid of order) {
    const items = buckets.get(pid) || [];
    items.sort((a, b) => {
      if (a.kind !== b.kind) return a.kind === "working" ? -1 : 1;
      return sessionLineName(a).localeCompare(sessionLineName(b), "zh");
    });
    const block = document.createElement("section");
    block.className = "session-block";
    const head = document.createElement("div");
    head.className = "session-block-head";
    head.innerHTML =
      `<h2>${esc(pid ? projectAlias(projectById(pid)) : "未关联")}</h2>` +
      `<span class="session-block-n">${items.length}</span>`;
    block.appendChild(head);
    for (const s of items) appendSessionRow(block, s);
    runningEl.appendChild(block);
  }
}

function sessionsForLine(projectId, lineId) {
  return (runningCache || []).filter(
    (s) => s.hit && s.hit.projectId === projectId && s.hit.lineId === lineId && s.path
  );
}

function sessionForLine(projectId, lineId) {
  const hits = sessionsForLine(projectId, lineId);
  return hits.find((s) => s.kind === "working") || hits[0] || null;
}

function paintCardLines(card, p) {
  const box = card.querySelector(".space-lines");
  if (!box) return;
  const active = (p.lines || []).filter((l) => (l.status || "active") === "active");
  if (!active.length) {
    box.innerHTML = "<p class='space-lines-empty'>没有未关闭 line</p>";
    return;
  }
  box.innerHTML = "";
  for (const l of active) {
    const hits = sessionsForLine(p.id, l.id);
    const s = hits.find((x) => x.kind === "working") || hits[0] || null;
    const a = s
      ? (s.agents || []).find((x) => x.state === "working") || (s.agents || [])[0] || {}
      : {};
    const bits = [];
    if (s) bits.push(sessionOrcaName(s));
    if (a.agentType) bits.push(a.agentType);
    if (s && s.kind === "working") bits.push("执行中");
    else if (hits.length > 1) bits.push(`+${hits.length - 1}`);
    const label = bits.join(" · ");
    const row = document.createElement("div");
    row.className = "space-line";
    row.innerHTML =
      `<span class="line-dot${s && s.kind === "working" ? " doing" : s ? " on" : ""}"></span>` +
      `<button type="button" class="space-line-name">${esc(lineAlias(l))}</button>` +
      (s && s.path
        ? `<button type="button" class="space-line-sess" title="${esc(label)}"><span>${esc(label)}</span></button>`
        : `<span class="space-line-sess is-empty">无会话</span>`);
    row.querySelector(".space-line-name").onclick = (ev) => {
      ev.stopPropagation();
      selectLine(p.id, l.id);
    };
    const sessBtn = row.querySelector("button.space-line-sess");
    if (sessBtn) {
      sessBtn.onclick = (ev) => {
        ev.stopPropagation();
        jumpToOrca(s.path, sessBtn);
      };
    }
    row.onclick = (ev) => ev.stopPropagation();
    box.appendChild(row);
  }
}

function sessionLineName(s) {
  if (!s.hit) return "";
  const line = lineById(projectById(s.hit.projectId), s.hit.lineId);
  return lineAlias(line) || s.hit.lineId || "";
}

function sessionOrcaName(s) {
  return s.displayName || shortPath(s.path) || "会话";
}

function appendSessionRow(parent, s) {
  const row = document.createElement("div");
  row.className = "running-row" + (s.hit ? "" : " is-unlinked");
  const lineName = sessionLineName(s);
  const sessName = sessionOrcaName(s);
  const a =
    (s.agents || []).find((x) => x.state === "working") ||
    (s.agents || [])[0] ||
    {};
  const prompt = shortPrompt(a.prompt) || a.toolName || "";
  row.innerHTML =
    `<span class="line-dot ${s.kind === "working" ? "doing" : "on"}"></span>` +
    `<button type="button" class="running-main">` +
    `<span class="running-name">${lineName ? esc(lineName) : ""}</span>` +
    `<span class="running-orca">${esc(sessName)}</span>` +
    `<span class="running-agent">${a.agentType ? esc(a.agentType) : ""}</span>` +
    `<span class="running-prompt">${prompt ? esc(prompt) : ""}</span>` +
    `</button>` +
    (!s.hit && s.path
      ? `<button type="button" class="running-link" title="关联到 line" aria-label="关联">${icLink}</button>`
      : "");
  const main = row.querySelector(".running-main");
  if (s.path) main.onclick = () => jumpToOrca(s.path, main);
  else main.disabled = true;
  const linkBtn = row.querySelector(".running-link");
  if (linkBtn) {
    linkBtn.onclick = (ev) => {
      ev.stopPropagation();
      showLinkPick(row, s.path);
    };
  }
  parent.appendChild(row);
}

function renderSessionFilters(tagged) {
  if (sessionFilter && !projectById(sessionFilter)) sessionFilter = "";
  const counts = new Map();
  for (const s of tagged) {
    if (!s.hit) continue;
    counts.set(s.hit.projectId, (counts.get(s.hit.projectId) || 0) + 1);
  }
  const ids = catalog.projects
    .map((p) => p.id)
    .filter((id) => counts.has(id) || id === sessionFilter);
  const proj = projectById(sessionFilter);
  sessionsSub.hidden = true;
  sessionsSub.textContent = "";
  sessionsFilters.innerHTML = "";
  if (!tagged.length && !sessionFilter) return;
  const addChip = (id, label, n) => {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "sessions-filter" + (sessionFilter === id ? " active" : "");
    b.innerHTML =
      `<span class="sessions-filter-label">${esc(label)}</span>` +
      (n != null ? `<span class="sessions-filter-n">${n}</span>` : "");
    b.onclick = () => {
      if (sessionFilter === id) return;
      sessionFilter = id;
      applyRunning(runningCache || []);
    };
    sessionsFilters.appendChild(b);
  };
  addChip("", "全部", tagged.length);
  for (const id of ids) {
    const p = projectById(id);
    addChip(id, projectAlias(p) || id, counts.get(id) || 0);
  }
}

function zhDate(s) {
  if (!s) return "";
  const m = /^(\d{4})-(\d{1,2})-(\d{1,2})/.exec(s);
  if (!m) return s;
  return `${m[1]}年${Number(m[2])}月${Number(m[3])}日`;
}

function tile(icon, label, value) {
  return `<div class="stat-tile"><div class="stat-ico">${icon}</div><div class="stat-text"><div class="stat-label">${label}</div><div class="stat-n">${value}</div></div></div>`;
}

let showClosedLines = localStorage.getItem("kilo-show-closed-lines") === "1";

function isLiveLine(l) {
  return (l.status || "active") === "active";
}

const lineBusyModal = document.getElementById("line-busy-modal");
const lineBusyHint = document.getElementById("line-busy-hint");
let lineBusy = { projectId: "", lineId: "" };

function openLineBusyModal(projectId, lineId, n) {
  lineBusy = { projectId, lineId };
  const line = lineById(projectById(projectId), lineId);
  const name = line ? lineAlias(line) : lineId;
  lineBusyHint.textContent = `「${name}」还有 ${n} 个 Orca 会话，请先处理完再关闭。`;
  lineBusyModal.hidden = false;
}

document.getElementById("line-busy-cancel").onclick = () => {
  lineBusyModal.hidden = true;
};
document.getElementById("line-busy-go").onclick = () => {
  lineBusyModal.hidden = true;
  if (lineBusy.projectId && lineBusy.lineId) selectLine(lineBusy.projectId, lineBusy.lineId);
};

async function requestCloseLine(projectId, lineId) {
  await loadRunning({ force: true });
  const n = sessionsForLine(projectId, lineId).length;
  if (n) {
    openLineBusyModal(projectId, lineId, n);
    return;
  }
  await setLineStatus(projectId, lineId, "completed");
}

async function setLineStatus(projectId, lineId, status) {
  try {
    const r = await fetch("/api/line/status", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ project: projectId, line: lineId, status }),
    }).then((x) => x.json());
    if (!r.ok) return;
    const line = lineById(projectById(projectId), lineId);
    if (line) line.status = r.status;
    const proj = projectById(projectId);
    if (proj) renderLineList(proj);
    loadTree();
  } catch (err) {
    /* keep list */
  }
}

function renderLineList(proj) {
  const q = (lineSearch.value || "").trim().toLowerCase();
  const matches = (l) =>
    !q ||
    l.id.toLowerCase().includes(q) ||
    lineAlias(l).toLowerCase().includes(q) ||
    (l.title || "").toLowerCase().includes(q);
  const liveLines = proj.lines.filter((l) => isLiveLine(l) && matches(l));
  const closedLines = proj.lines.filter((l) => !isLiveLine(l) && matches(l));
  lineListEl.innerHTML = "";

  const appendLine = (l) => {
    const live = isLiveLine(l);
    const ts = l.task_status || {};
    const total = l.tasks || 0;
    const done = ts.done || 0;
    const doing = ts.doing || 0;
    const blocked = ts.blocked || 0;
    const bits = [live ? "活跃" : "已完成"];
    if (total) bits.push(`${done}/${total} 任务`);
    if (doing) bits.push(`${doing} 进行中`);
    if (blocked) bits.push(`${blocked} 阻塞`);
    const row = document.createElement("div");
    row.className = "line-row";
    const b = document.createElement("button");
    b.type = "button";
    b.className =
      "rail-item" +
      (loc.lineId === l.id ? " active" : "") +
      (live ? "" : " is-closed");
    b.title = `${l.id} · ${bits.join(" ")}`;
    let meta = `<span class="line-dot${live ? " on" : ""}${blocked ? " blocked" : doing ? " doing" : ""}"></span>`;
    if (total) meta = `<span class="line-frac">${done}/${total}</span>` + meta;
    b.innerHTML = `${icFolder}<span>${esc(lineAlias(l))}</span><span class="line-meta">${meta}</span>`;
    b.onclick = () => selectLine(proj.id, l.id);
    const more = document.createElement("button");
    more.type = "button";
    more.className = "line-more";
    more.title = "状态";
    more.setAttribute("aria-label", "状态");
    more.innerHTML = icMore;
    const menu = document.createElement("div");
    menu.className = "menu line-menu";
    menu.innerHTML =
      `<button type="button" class="row" data-rename>重命名</button>` +
      (live
        ? `<button type="button" class="row" data-st="completed">关闭</button>`
        : `<button type="button" class="row" data-st="active">重新打开</button>`);
    more.onclick = (ev) => {
      ev.preventDefault();
      ev.stopPropagation();
      const openNow = !menu.classList.contains("open");
      document.querySelectorAll(".line-menu.open, .card-menu.open").forEach((m) => m.classList.remove("open"));
      if (!openNow) return;
      const r = more.getBoundingClientRect();
      menu.style.top = `${Math.round(r.bottom + 4)}px`;
      menu.style.right = `${Math.round(window.innerWidth - r.right)}px`;
      menu.style.left = "auto";
      menu.classList.add("open");
    };
    menu.onclick = (ev) => ev.stopPropagation();
    menu.querySelector("[data-rename]").onclick = (ev) => {
      ev.stopPropagation();
      menu.classList.remove("open");
      openLineAliasModal(proj.id, l.id);
    };
    menu.querySelector("[data-st]").onclick = (ev) => {
      ev.stopPropagation();
      menu.classList.remove("open");
      const st = menu.querySelector("[data-st]").dataset.st;
      if (st === "completed") requestCloseLine(proj.id, l.id);
      else setLineStatus(proj.id, l.id, st);
    };
    row.appendChild(b);
    row.appendChild(more);
    row.appendChild(menu);
    lineListEl.appendChild(row);
  };

  for (const l of liveLines) appendLine(l);
  if (!q) {
    const selectedClosed = closedLines.find((l) => l.id === loc.lineId);
    if (!showClosedLines && selectedClosed) appendLine(selectedClosed);
    if (closedLines.length) {
      const fold = document.createElement("button");
      fold.type = "button";
      fold.className = "line-closed-fold" + (showClosedLines ? " open" : "");
      fold.setAttribute("aria-expanded", showClosedLines ? "true" : "false");
      fold.title = showClosedLines ? "收起已关闭的 line" : "展开已关闭的 line";
      fold.innerHTML =
        `<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 6l6 6-6 6"/></svg>` +
        `<span>已关闭</span><span class="n">${closedLines.length}</span>`;
      fold.onclick = () => {
        showClosedLines = !showClosedLines;
        localStorage.setItem("kilo-show-closed-lines", showClosedLines ? "1" : "");
        renderLineList(proj);
      };
      lineListEl.appendChild(fold);
      if (showClosedLines) for (const l of closedLines) appendLine(l);
    }
  } else {
    for (const l of closedLines) appendLine(l);
  }
  if (!lineListEl.children.length) {
    const empty = document.createElement("p");
    empty.className = "session-muted";
    empty.textContent = q ? "没有匹配的 line。" : "没有进行中的 line。";
    lineListEl.appendChild(empty);
  }
}

function renderDetail() {
  const proj = projectById(loc.projectId);
  if (!proj) return;
  const line = lineById(proj, loc.lineId);
  renderLineList(proj);

  const title = line ? lineAlias(line) : projectAlias(proj);
  const desc = (line ? line.summary : proj.summary) || "暂无描述。";
  const updated = zhDate((line && line.updated) || proj.updated);
  detailTitle.textContent = title;
  detailTitle.contentEditable = "plaintext-only";
  detailTitle.classList.add("is-editable");
  detailTitle.title = "点击修改别名，回车保存";
  if (line) {
    detailProject.hidden = false;
    detailProject.textContent = projectAlias(proj);
    detailProject.title = "返回项目首页";
  } else {
    detailProject.hidden = true;
    detailProject.textContent = "";
  }
  if (line) {
    if (line.id !== title) {
      detailId.hidden = false;
      detailId.textContent = line.id;
    } else {
      detailId.hidden = true;
      detailId.textContent = "";
    }
  } else if (proj.id !== title) {
    detailId.hidden = false;
    detailId.textContent = proj.id;
  } else {
    detailId.hidden = true;
    detailId.textContent = "";
  }
  detailDesc.textContent = desc;

  if (line) {
    const ts = line.task_status || {};
    const live = (line.status || "active") === "active";
    detailStats.innerHTML =
      tile(icList, "任务", String(line.tasks || 0)) +
      tile(icPages, "已完成", String(ts.done || 0)) +
      tile(icFile, "待做", String((ts.todo || 0) + (ts.doing || 0))) +
      tile(icFile, "状态", live ? "活跃" : "已完成") +
      tile(icFolder, "位置", "本地") +
      tile(icPages, "更新", updated || "—");
  } else {
    const ls = proj.line_status || {};
    const live = (ls.active || 0) > 0;
    detailStats.innerHTML =
      tile(icFolder, "line", String(proj.lines.length)) +
      tile(icList, "任务", String(proj.tasks || 0)) +
      tile(icPages, "进行中", String(ls.active || 0)) +
      tile(icFile, "状态", live ? "活跃" : "已完成") +
      tile(icFolder, "位置", "本地") +
      tile(icPages, "更新", updated || "—");
  }

  const files = line
    ? line.files
    : [{ name: "project.md", path: proj.path }];
  const rank = (name) => {
    const i = FILE_TABS.findIndex((t) => t.name === name);
    return i === -1 ? 99 : i;
  };
  const ordered = [...files].sort((a, b) => rank(a.name) - rank(b.name));
  const icons = {
    icFolder,
    icFile,
    icList,
    icPages,
    icTasks,
    icContext,
    icSpec,
    icReview,
    icOps,
    icLine,
    icSessions,
  };
  detailTabs.innerHTML = "";
  for (const f of ordered) {
    const meta = FILE_TABS.find((t) => t.name === f.name);
    const tab = document.createElement("button");
    tab.type = "button";
    tab.className = "detail-tab" + (loc.file === f.path ? " active" : "");
    const icon = icons[meta && meta.icon] || icFile;
    const label = (meta && meta.label) || f.name.replace(/\.md$/, "");
    tab.innerHTML = icon + `<span>${label}</span>`;
    tab.onclick = () => openFile(f.path);
    detailTabs.appendChild(tab);
  }
  if (line) {
    const tab = document.createElement("button");
    tab.type = "button";
    tab.className = "detail-tab" + (loc.file === "__session__" ? " active" : "");
    tab.innerHTML = icSessions + "<span>Sessions</span>";
    tab.onclick = () => openSessions();
    detailTabs.appendChild(tab);
  }
}

function esc(s) {
  return String(s || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function shortPath(p) {
  const parts = String(p || "").replace(/\/+$/, "").split("/").filter(Boolean);
  if (parts.length <= 2) return p || "";
  return parts.slice(-2).join("/");
}

function shortPrompt(s) {
  let t = String(s || "").replace(/\s+/g, " ").trim();
  t = t.replace(/KILO_WORKSPACE=\S+\s*/g, "");
  t = t.replace(/Repo:\s*\S+\s*/gi, "");
  t = t.replace(/The user title is:\s*/i, "");
  t = t.replace(/Invent a short English[^.]*\.\s*/gi, "");
  t = t.replace(/Then run `\/kilo new[^`]*`[^.]*\.\s*/gi, "");
  t = t.replace(/Run `\/kilo new[^`]*`[^.]*\.\s*/gi, "");
  t = t.replace(/and set the line title[^.]*\.\s*/gi, "");
  t = t.replace(/The Orca worktree folder[^.]*\.\s*/gi, "");
  t = t.replace(/Create the line[^.]*\.\s*/gi, "");
  t = t.replace(/Do not auto-execute\.?/gi, "");
  t = t.replace(/Line title:\s*/i, "");
  t = t.replace(/\s+/g, " ").trim();
  if (t.length > 72) t = t.slice(0, 70) + "…";
  return t;
}

async function loadSession({ quiet } = {}) {
  if (!quiet) sessionView.innerHTML = "<p class='session-muted'>读取绑定和 worktree…</p>";
  try {
    const u =
      "/api/session?project=" +
      encodeURIComponent(loc.projectId) +
      "&line=" +
      encodeURIComponent(loc.lineId);
    const data = await fetch(u).then((r) => r.json());
    if (!data.ok) {
      sessionView.innerHTML = `<p class='session-muted'>${esc(data.error || "无法读取")}</p>`;
      return;
    }
    const choices = data.choices || [];
    const rows = choices
      .map((c, i) => {
        const kind = c.kind || "offline";
        const badge =
          kind === "working"
            ? "<span class='st st-doing'>working</span>"
            : kind === "idle"
              ? "<span class='st st-todo'>idle</span>"
              : "<span class='st st-todo'>offline</span>";
        const sid = c.session_id
          ? `<span class='mute'>${esc(String(c.session_id).slice(0, 8))}…</span>`
          : "<span class='mute'>无 session id</span>";
        const a = (c.agents || []).find((x) => x.state === "working") || (c.agents || [])[0] || {};
        const prompt = shortPrompt(a.prompt);
        const bits = [
          c.branch || "—",
          c.git ? "git " + c.git : "",
          a.agentType || "",
          prompt,
        ].filter(Boolean);
        return (
          `<div class='choice-row' data-open-i='${i}'>` +
          `<div class='choice-main'>` +
          `<div class='round-meta'>${badge}${
            c.primary ? "<span class='st st-done'>primary</span>" : ""
          }${sid}</div>` +
          `<div class='choice-path' title='${esc(c.path)}'>${esc(shortPath(c.path))}</div>` +
          `<div class='mute'>${esc(bits.join(" · "))}</div>` +
          `</div>` +
          `</div>`
        );
      })
      .join("");
    sessionView.innerHTML =
      `<div class='session-card'>` +
      (rows || "<p class='session-muted'>这条 line 还没有 worktree 或 Orca 会话。</p>") +
      `<div class='session-actions'>` +
      `<button type='button' class='cmd-btn' data-refresh='1'>刷新状态</button>` +
      `<div class='session-create'>` +
      `<div class='agent-picks' id='session-agent'>` +
      `<button type='button' class='agent-pick' data-agent='grok'>Grok</button>` +
      `<button type='button' class='agent-pick' data-agent='codex'>Codex</button>` +
      `<button type='button' class='agent-pick' data-agent='cursor' title='cursor-agent'>Cursor</button>` +
      `</div>` +
      `<button type='button' class='cmd-btn primary' data-create='1'>新建会话</button>` +
      `</div></div></div>`;
    sessionView.querySelectorAll("[data-open-i]").forEach((el) => {
      el.onclick = (ev) => {
        ev.stopPropagation();
        const c = choices[Number(el.getAttribute("data-open-i"))];
        if (c && c.path) jumpToOrca(c.path, el);
      };
    });
    bindAgentPicks(sessionView.querySelector("#session-agent"));
    const refreshBtn = sessionView.querySelector(".cmd-btn[data-refresh]");
    const createBtn = sessionView.querySelector(".cmd-btn[data-create]");
    if (createBtn) {
      createBtn.onclick = async () => {
        const label = createBtn.textContent;
        createBtn.disabled = true;
        createBtn.textContent = "正在创建…";
        try {
          const r = await fetch("/api/session/create", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              project: loc.projectId,
              line: loc.lineId,
              agent: preferredAgent(),
            }),
          }).then((x) => x.json());
          createBtn.disabled = false;
          createBtn.textContent = r.ok
            ? "已开 Orca 会话"
            : r.error || "失败";
          if (r.command && !r.ok) createBtn.title = r.command;
          setTimeout(() => {
            createBtn.textContent = label;
          }, 2200);
        } catch (err) {
          createBtn.disabled = false;
          createBtn.textContent = "失败";
        }
      };
    }
  } catch (err) {
    sessionView.innerHTML = "<p class='session-muted'>读取失败。</p>";
  }
}

function showMemoryPage() {
  homeView = "memory";
  loc = { projectId: "", lineId: "", file: "" };
  docEl.removeAttribute("src");
  homeEl.hidden = true;
  sessionsPage.hidden = true;
  memoryPage.hidden = false;
  skillsPage.hidden = true;
  readerEl.hidden = true;
  railEl.hidden = false;
  setRailNav("memory");
  stopLiveWatch();
  const groups = catalog.facts || [];
  if (!groups.length) {
    memoryList.innerHTML =
      "<p class='session-muted'>还没有记忆。在 <code>Projects/_facts.md</code> 里用列表项写一条。</p>";
    return;
  }
  const many = groups.length > 1;
  memoryList.innerHTML = groups
    .map((g) => {
      const sections = g.sections && g.sections.length
        ? g.sections
        : [{ title: "", items: g.items || [] }];
      const body = sections
        .map((sec) => {
          const rows = (sec.items || [])
            .map((t) => `<p class="memory-item">${fmtFact(t)}</p>`)
            .join("");
          const h = sec.title ? `<h3>${esc(sec.title)}</h3>` : "";
          return `<div class="memory-section">${h}${rows}</div>`;
        })
        .join("");
      const label = many ? `<h2>${esc(g.label)}</h2>` : "";
      return `<section class="memory-group">${label}<div class="memory-card">${body}</div></section>`;
    })
    .join("");
}

function fmtFact(t) {
  return esc(t).replace(/`([^`]+)`/g, "<code>$1</code>");
}

let skillCatalog = { n: 0, items: [], marks: [], counts: {} };
let skillFilter = "";
let skillOpen = "";
let skillDetail = {};

const SKILL_MARKS = [
  { id: "claude", label: "Claude" },
  { id: "cursor", label: "Cursor" },
  { id: "codex", label: "Codex" },
  { id: "grok", label: "Grok" },
  { id: "gemini", label: "Gemini" },
];

function skillMarks() {
  return skillCatalog.marks && skillCatalog.marks.length
    ? skillCatalog.marks
    : SKILL_MARKS;
}

function renderSkillFilters() {
  const marks = skillMarks();
  const counts = skillCatalog.counts || {};
  const chips = [
    { id: "", label: "全部", n: skillCatalog.n || 0 },
    ...marks.map((m) => ({ id: m.id, label: m.label, n: counts[m.id] || 0 })),
  ];
  skillFilters.innerHTML = chips
    .map((c) => {
      const on = skillFilter === c.id ? " active" : "";
      const n = c.n ? `<span class="sessions-filter-n">${c.n}</span>` : "";
      return (
        `<button type="button" class="sessions-filter${on}" data-src="${esc(c.id)}">` +
        `<span>${esc(c.label)}</span>${n}</button>`
      );
    })
    .join("");
  skillFilters.querySelectorAll("[data-src]").forEach((el) => {
    el.onclick = () => {
      const id = el.getAttribute("data-src") || "";
      if (skillFilter === id) return;
      skillFilter = id;
      renderSkillFilters();
      renderSkillList();
    };
  });
}

function renderSkillList() {
  const q = (skillSearch.value || "").trim().toLowerCase();
  const marks = skillMarks();
  const items = (skillCatalog.items || []).filter((s) => {
    if (skillFilter && !(s.sources || []).includes(skillFilter)) return false;
    if (!q) return true;
    const blob = `${s.name || ""} ${s.description || ""} ${(s.sources || []).join(" ")}`.toLowerCase();
    return blob.includes(q);
  });
  skillsN.textContent = items.length ? String(items.length) : "";
  if (!items.length) {
    skillList.innerHTML = q || skillFilter
      ? "<p class='session-muted'>没有匹配的 skill。</p>"
      : "<p class='session-muted'>本机还没有找到 SKILL.md。</p>";
    return;
  }
  skillList.innerHTML = items
    .map((s) => {
      const src = new Set(s.sources || []);
      const chips = marks
        .map((m) => {
          const on = src.has(m.id) ? " on" : "";
          return `<span class="skill-mark${on}">${esc(m.label)}</span>`;
        })
        .join("");
      const open = skillOpen === s.name;
      return (
        `<div class="skill-row${open ? " open" : ""}" data-skill="${esc(s.name)}" title="${esc(s.path || "")}">` +
        `<span class="skill-chev">›</span>` +
        `<div class="skill-name">${esc(s.name)}</div>` +
        `<div class="skill-marks">${chips}</div>` +
        (s.description ? `<p class="skill-desc">${esc(s.description)}</p>` : "") +
        (open ? `<div class="skill-detail" data-skill-detail="${esc(s.name)}"></div>` : "") +
        `</div>`
      );
    })
    .join("");
  skillList.querySelectorAll(".skill-row").forEach((row) => {
    row.onclick = (ev) => {
      if (ev.target.closest("button")) return;
      if (ev.target.closest(".skill-detail")) return;
      const name = row.getAttribute("data-skill") || "";
      skillOpen = skillOpen === name ? "" : name;
      renderSkillList();
      if (skillOpen) loadSkillDetail(skillOpen);
    };
  });
  if (skillOpen) fillSkillDetail(skillOpen);
}

function skillIsProtected(name, d) {
  if (d && d.protected) return true;
  const item = (skillCatalog.items || []).find((s) => s.name === name);
  if (item && item.protected) return true;
  return String(name || "").toLowerCase() === "kilo";
}

function skillDetailHtml(name, d) {
  if (!d) return "<p class='session-muted'>正在读取…</p>";
  if (!d.ok) return `<p class='session-muted'>${esc(d.error || "读取失败")}</p>`;
  const locked = skillIsProtected(name, d);
  const locs = (d.locations || [])
    .map((loc) => {
      const tag = loc.link ? "链接" : "";
      const del = locked
        ? ""
        : `<button type="button" class="skill-loc-del" data-del-src="${esc(loc.id)}">删除</button>`;
      return (
        `<div class="skill-loc">` +
        `<span class="skill-loc-src">${esc(loc.label || loc.id)}</span>` +
        `<span class="skill-loc-path" title="${esc(loc.path)}">${esc(loc.path)}${tag ? " · " + tag : ""}</span>` +
        del +
        `</div>`
      );
    })
    .join("");
  const files = (d.files || []).length
    ? `<p class="skill-files">${esc((d.files || []).join(" · "))}</p>`
    : "";
  const body = d.html
    ? `<div class="skill-md">${d.html}</div>`
    : "<p class='session-muted'>没有 SKILL.md。</p>";
  const note = locked
    ? `<p class="session-muted">kilo 不能从看板删除。</p>`
    : "";
  return `<div class="skill-locs">${locs}</div>${files}${body}${note}`;
}

function fillSkillDetail(name) {
  const pane = skillList.querySelector(`[data-skill-detail="${CSS.escape(name)}"]`);
  if (!pane) return;
  pane.innerHTML = skillDetailHtml(name, skillDetail[name]);
  pane.querySelectorAll("[data-del-src]").forEach((b) => {
    b.onclick = (ev) => {
      ev.stopPropagation();
      openSkillDelete(name, b.getAttribute("data-del-src") || "");
    };
  });
}

async function loadSkillDetail(name) {
  if (!skillDetail[name]) {
    fillSkillDetail(name);
    try {
      const r = await fetch("/api/skill?name=" + encodeURIComponent(name)).then((x) => x.json());
      skillDetail[name] = r;
    } catch (err) {
      skillDetail[name] = { ok: false, error: "读取失败" };
    }
  }
  fillSkillDetail(name);
}

async function loadSkills() {
  try {
    const r = await fetch("/api/skills").then((x) => x.json());
    if (r && r.ok !== false) skillCatalog = r;
  } catch (err) {
    skillCatalog = { n: 0, items: [], marks: [], counts: {} };
  }
  navSkillsN.textContent = String(skillCatalog.n || 0);
  if (homeView === "skills") {
    renderSkillFilters();
    renderSkillList();
    if (skillOpen) loadSkillDetail(skillOpen);
  }
}

function showSkillsPage() {
  homeView = "skills";
  loc = { projectId: "", lineId: "", file: "" };
  docEl.removeAttribute("src");
  homeEl.hidden = true;
  sessionsPage.hidden = true;
  memoryPage.hidden = true;
  skillsPage.hidden = false;
  readerEl.hidden = true;
  railEl.hidden = false;
  setRailNav("skills");
  stopLiveWatch();
  renderSkillFilters();
  renderSkillList();
  loadSkills();
}

function showReader() {
  stopLiveWatch();
  homeEl.hidden = true;
  sessionsPage.hidden = true;
  memoryPage.hidden = true;
  skillsPage.hidden = true;
  readerEl.hidden = false;
  railEl.hidden = true;
  navHome.classList.remove("active");
  navSessions.classList.remove("active");
  navMemory.classList.remove("active");
  navSkills.classList.remove("active");
  renderDetail();
}

function paint() {
  if (loc.projectId) showReader();
  else if (homeView === "sessions") showSessionsPage();
  else if (homeView === "memory") showMemoryPage();
  else if (homeView === "skills") showSkillsPage();
  else showHome();
}

async function loadTree() {
  const res = await fetch("/api/tree");
  catalog = await res.json();
  const foot = document.getElementById("rail-foot");
  if (foot) {
    const ver = catalog.version ? `v${catalog.version}` : "";
    foot.textContent = `Kilo${ver ? "  " + ver : ""}`;
  }
  paint();
  loadSkills();
}

async function pickWorkspace() {
  const path = await pickFolder();
  if (!path) return;
  const r = await fetch("/api/workspace", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ root: path }),
  }).then((x) => x.json());
  if (!r.ok) return;
  await loadTree();
}

async function initWorkspace() {
  const path = await pickFolder();
  if (!path) return;
  const r = await fetch("/api/workspace/init", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ root: path }),
  }).then((x) => x.json());
  if (!r.ok) {
    alert(r.error || "初始化失败");
    return;
  }
  await loadTree();
}

function renderSetup() {
  const orca = catalog.orca || {};
  const empty = !(catalog.projects || []).length;
  if (orca.ok && !empty) return "";
  const rows = [];
  if (!orca.ok) {
    rows.push(
      `<div class="setup-row">` +
        `<div class="setup-copy"><div class="setup-title">安装 Orca</div>` +
        `<p>会话和新建 line 需要本机的 Orca。装进「应用程序」后点重新检测。</p></div>` +
        `<div class="setup-actions">` +
        `<button type="button" class="new-line-btn" data-orca-install>下载 Orca</button>` +
        `<button type="button" class="cmd-btn" data-orca-retry>重新检测</button>` +
        `</div></div>`
    );
  }
  if (empty) {
    rows.push(
      `<div class="setup-row">` +
        `<div class="setup-copy"><div class="setup-title">初始化工作区</div>` +
        `<p>选一个空文件夹，Kilo 会建 <code>Projects/</code>。已有库就选现成的 Projects 文件夹。</p></div>` +
        `<div class="setup-actions">` +
        `<button type="button" class="new-line-btn" data-ws-init>初始化工作区</button>` +
        `<button type="button" class="cmd-btn" data-pick-ws>选择已有</button>` +
        `</div></div>`
    );
  }
  return `<div class="setup-card">${rows.join("")}</div>`;
}

function bindSetup(root) {
  if (!root) return;
  root.querySelector("[data-orca-install]")?.addEventListener("click", async (ev) => {
    ev.stopPropagation();
    await fetch("/api/setup/orca", { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" });
  });
  root.querySelector("[data-orca-retry]")?.addEventListener("click", (ev) => {
    ev.stopPropagation();
    loadTree();
  });
  root.querySelector("[data-ws-init]")?.addEventListener("click", (ev) => {
    ev.stopPropagation();
    initWorkspace();
  });
  root.querySelector("[data-pick-ws]")?.addEventListener("click", (ev) => {
    ev.stopPropagation();
    pickWorkspace();
  });
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
    if (loc.file && loc.file !== "__session__") {
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

const projectNewBtn = document.getElementById("project-new");
const projectNewModal = document.getElementById("project-new-modal");
const projectNewMsg = document.getElementById("project-new-msg");

async function pickFolder() {
  try {
    if (window.pywebview && window.pywebview.api && window.pywebview.api.pick_folder) {
      return (await window.pywebview.api.pick_folder()) || "";
    }
  } catch (err) {
    /* fall through */
  }
  try {
    const r = await fetch("/api/pick-folder", { method: "POST" }).then((x) => x.json());
    if (r && r.path) return r.path;
    if (r && r.error) throw new Error(r.error);
  } catch (err) {
    return "";
  }
  return "";
}

function folderBase(path) {
  return String(path || "").replace(/[/\\]+$/, "").split(/[/\\]/).pop() || "project";
}

projectNewBtn.onclick = async () => {
  const repo = await pickFolder();
  if (!repo) return;
  const title = folderBase(repo);
  projectNewModal.hidden = false;
  projectNewMsg.textContent = "正在创建…";
  try {
    const r = await fetch("/api/project/create", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, name: title, repo }),
    }).then((x) => x.json());
    if (!r.ok) {
      projectNewMsg.textContent = r.error || "失败";
      return;
    }
    projectNewModal.hidden = true;
    await loadTree();
    if (r.id) selectProject(r.id);
  } catch (err) {
    projectNewMsg.textContent = "请求失败";
  }
};
document.getElementById("project-new-cancel").onclick = () => {
  projectNewModal.hidden = true;
};

function preferredAgent() {
  let a = (localStorage.getItem("kilo-agent") || "grok").toLowerCase();
  if (a === "cursor-agent" || a === "cursoragent") a = "cursor";
  return ["grok", "codex", "cursor"].includes(a) ? a : "grok";
}

function bindAgentPicks(root) {
  if (!root) return;
  const cur = preferredAgent();
  root.querySelectorAll("[data-agent]").forEach((b) => {
    b.classList.toggle("active", b.getAttribute("data-agent") === cur);
    b.onclick = (ev) => {
      ev.preventDefault();
      const id = b.getAttribute("data-agent") || "grok";
      localStorage.setItem("kilo-agent", id);
      root.querySelectorAll("[data-agent]").forEach((x) => {
        x.classList.toggle("active", x === b);
      });
    };
  });
}

const lineNewBtn = document.getElementById("line-new");
const lineNewModal = document.getElementById("line-new-modal");
const lineNewForm = document.getElementById("line-new-form");
const lineNewMsg = document.getElementById("line-new-msg");

lineNewBtn.onclick = () => {
  if (!loc.projectId) return;
  lineNewMsg.textContent = "";
  bindAgentPicks(document.getElementById("line-new-agent"));
  lineNewModal.hidden = false;
  document.getElementById("line-new-title").focus();
};
document.getElementById("line-new-cancel").onclick = () => {
  lineNewModal.hidden = true;
};
lineNewForm.onsubmit = async (ev) => {
  ev.preventDefault();
  const name = document.getElementById("line-new-name").value.trim();
  const title = document.getElementById("line-new-title").value.trim();
  if (!loc.projectId || (!name && !title)) {
    lineNewMsg.textContent = "请填写标题";
    return;
  }
  lineNewMsg.textContent = "正在开 Orca 会话…";
  try {
    const res = await fetch("/api/line/new", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        project: loc.projectId,
        name,
        title,
        agent: preferredAgent(),
      }),
    });
    const text = await res.text();
    let r = {};
    try {
      r = JSON.parse(text);
    } catch (err) {
      lineNewMsg.textContent = res.ok ? "已创建，但返回不是 JSON" : `请求失败 (${res.status})`;
      return;
    }
    if (!r.ok) {
      lineNewMsg.textContent = r.error || "失败";
      return;
    }
    lineNewMsg.textContent = "已创建 Orca 会话，agent 会跑 /kilo new";
    setTimeout(() => {
      lineNewModal.hidden = true;
    }, 1200);
  } catch (err) {
    lineNewMsg.textContent = "请求失败";
  }
};

const aliasModal = document.getElementById("alias-modal");
const aliasForm = document.getElementById("alias-form");
const aliasInput = document.getElementById("alias-input");
const aliasMsg = document.getElementById("alias-msg");
let aliasProjectId = "";
let aliasLineId = "";

function openAliasModal(projectId) {
  const proj = projectById(projectId);
  if (!proj) return;
  aliasProjectId = projectId;
  aliasLineId = "";
  aliasInput.value = projectAlias(proj);
  aliasMsg.textContent = "";
  aliasModal.hidden = false;
  aliasInput.focus();
  aliasInput.select();
}

function openLineAliasModal(projectId, lineId) {
  const line = lineById(projectById(projectId), lineId);
  if (!line) return;
  aliasProjectId = projectId;
  aliasLineId = lineId;
  aliasInput.value = lineAlias(line);
  aliasMsg.textContent = "";
  aliasModal.hidden = false;
  aliasInput.focus();
  aliasInput.select();
}

async function postProjectAlias(projectId, next) {
  const proj = projectById(projectId);
  if (!proj) return { ok: false };
  next = (next || "").trim();
  if (!next || next === projectAlias(proj)) return { ok: true, skipped: true };
  return fetch("/api/project/alias", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ project: projectId, alias: next }),
  }).then((x) => x.json());
}

async function postLineAlias(projectId, lineId, next) {
  const line = lineById(projectById(projectId), lineId);
  if (!line) return { ok: false };
  next = (next || "").trim();
  if (!next || next === lineAlias(line)) return { ok: true, skipped: true };
  return fetch("/api/line/alias", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ project: projectId, line: lineId, alias: next }),
  }).then((x) => x.json());
}

async function saveProjectAlias() {
  if (!loc.projectId) return;
  const next = detailTitle.textContent.trim();
  const r = loc.lineId
    ? await postLineAlias(loc.projectId, loc.lineId, next)
    : await postProjectAlias(loc.projectId, next);
  if (r.ok && !r.skipped) await loadTree();
}

const deleteModal = document.getElementById("delete-modal");
const deleteForm = document.getElementById("delete-form");
const deleteInput = document.getElementById("delete-input");
const deleteHint = document.getElementById("delete-hint");
const deleteMsg = document.getElementById("delete-msg");
let deleteProjectId = "";

function openDeleteModal(projectId) {
  const proj = projectById(projectId);
  if (!proj) return;
  deleteProjectId = projectId;
  const name = projectAlias(proj);
  deleteHint.textContent =
    `会把 vault 里的 ${proj.id} 文档移到 Projects/_trash，不删 git 仓库。请输入「${name}」确认。`;
  deleteInput.value = "";
  deleteMsg.textContent = "";
  deleteModal.hidden = false;
  deleteInput.focus();
}

document.getElementById("delete-cancel").onclick = () => {
  deleteModal.hidden = true;
};
deleteForm.onsubmit = async (ev) => {
  ev.preventDefault();
  const proj = projectById(deleteProjectId);
  if (!proj) return;
  const expect = projectAlias(proj);
  if (deleteInput.value.trim() !== expect && deleteInput.value.trim() !== proj.id) {
    deleteMsg.textContent = "名称不匹配";
    return;
  }
  deleteMsg.textContent = "正在移动…";
  try {
    const r = await fetch("/api/project/delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ project: deleteProjectId }),
    }).then((x) => x.json());
    if (!r.ok) {
      deleteMsg.textContent = r.error || "失败";
      return;
    }
    deleteModal.hidden = true;
    if (loc.projectId === deleteProjectId) selectProject("");
    await loadTree();
  } catch (err) {
    deleteMsg.textContent = "请求失败";
  }
};

document.getElementById("alias-cancel").onclick = () => {
  aliasModal.hidden = true;
};
aliasForm.onsubmit = async (ev) => {
  ev.preventDefault();
  aliasMsg.textContent = "保存中…";
  try {
    const r = aliasLineId
      ? await postLineAlias(aliasProjectId, aliasLineId, aliasInput.value)
      : await postProjectAlias(aliasProjectId, aliasInput.value);
    if (!r.ok) {
      aliasMsg.textContent = r.error || "失败";
      return;
    }
    aliasModal.hidden = true;
    await loadTree();
  } catch (err) {
    aliasMsg.textContent = "请求失败";
  }
};
function closeFloatingMenus() {
  document.querySelectorAll(".card-menu.open, .line-menu.open, .meta-menu.open").forEach((m) => {
    m.classList.remove("open");
  });
}
document.addEventListener("click", () => closeFloatingMenus());

detailProject.onclick = () => {
  if (loc.projectId) openProjectHome(loc.projectId);
};
detailTitle.addEventListener("keydown", (ev) => {
  if (ev.key === "Enter") {
    ev.preventDefault();
    detailTitle.blur();
  }
  if (ev.key === "Escape") {
    ev.preventDefault();
    const proj = projectById(loc.projectId);
    detailTitle.textContent = projectAlias(proj);
    detailTitle.blur();
  }
});
detailTitle.addEventListener("blur", () => {
  if (!loc.lineId) saveProjectAlias();
});

navHome.onclick = () => {
  stopSessionWatch();
  homeView = "projects";
  selectProject("");
};
navSessions.onclick = () => {
  stopSessionWatch();
  showSessionsPage("");
};

navMemory.onclick = () => {
  stopSessionWatch();
  showMemoryPage();
};
navSkills.onclick = () => {
  stopSessionWatch();
  showSkillsPage();
};
skillSearch.oninput = () => renderSkillList();

const skillDelModal = document.getElementById("skill-del-modal");
const skillDelForm = document.getElementById("skill-del-form");
const skillDelInput = document.getElementById("skill-del-input");
const skillDelHint = document.getElementById("skill-del-hint");
const skillDelMsg = document.getElementById("skill-del-msg");
let skillDelName = "";
let skillDelSource = "";

function openSkillDelete(name, source) {
  if (skillIsProtected(name, skillDetail[name])) return;
  if (!source) return;
  const item = (skillCatalog.items || []).find((s) => s.name === name) || {};
  const d = skillDetail[name] || {};
  const locs = (d.locations || item.locations || []).filter((l) => l.id === source);
  skillDelName = name;
  skillDelSource = source;
  const where = (locs[0] && (locs[0].label || source)) || source;
  const paths = locs.map((l) => l.path).join("，") || "对应文件夹";
  skillDelHint.textContent =
    `只从 ${where} 删除「${name}」，不能恢复。路径：${paths}。请输入「${name}」确认。`;
  skillDelInput.value = "";
  skillDelMsg.textContent = "";
  skillDelModal.hidden = false;
  skillDelInput.focus();
}

document.getElementById("skill-del-cancel").onclick = () => {
  skillDelModal.hidden = true;
};
skillDelForm.onsubmit = async (ev) => {
  ev.preventDefault();
  if (skillDelInput.value.trim() !== skillDelName) {
    skillDelMsg.textContent = "名称不匹配";
    return;
  }
  if (!skillDelSource) {
    skillDelMsg.textContent = "必须指定来源";
    return;
  }
  skillDelMsg.textContent = "正在删除…";
  try {
    const r = await fetch("/api/skill/delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: skillDelName, source: skillDelSource }),
    }).then((x) => x.json());
    if (!r.ok) {
      skillDelMsg.textContent = r.error || "失败";
      return;
    }
    skillDelModal.hidden = true;
    delete skillDetail[skillDelName];
    await loadSkills();
  } catch (err) {
    skillDelMsg.textContent = "请求失败";
  }
};
topHome.onclick = () => {
  stopSessionWatch();
  homeView = "projects";
  selectProject("");
};
lineSearch.oninput = () => {
  const proj = projectById(loc.projectId);
  if (proj) renderLineList(proj);
};

loadTree();
setInterval(checkStamp, 1500);
setInterval(checkCode, 800);
