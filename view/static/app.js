const treeEl = document.getElementById("tree");
const docEl = document.getElementById("doc");
const crumbEl = document.getElementById("crumb");

async function loadTree() {
  const res = await fetch("/api/tree");
  const data = await res.json();
  treeEl.innerHTML = "";
  if (!data.projects.length) {
    treeEl.textContent = "未找到 Projects/";
    return;
  }
  for (const proj of data.projects) {
    const wrap = document.createElement("div");
    wrap.className = "proj";
    const pb = document.createElement("button");
    pb.textContent = proj.id;
    pb.onclick = () => openFile(proj.path);
    wrap.appendChild(pb);
    for (const line of proj.lines) {
      const lw = document.createElement("div");
      lw.className = "line";
      const lb = document.createElement("button");
      lb.textContent = line.id;
      lb.onclick = () => {
        const first = line.files[0];
        if (first) openFile(first.path);
      };
      lw.appendChild(lb);
      for (const f of line.files) {
        const a = document.createElement("button");
        a.className = "file";
        a.dataset.path = f.path;
        a.textContent = f.name;
        a.onclick = () => openFile(f.path);
        lw.appendChild(a);
      }
      wrap.appendChild(lw);
    }
    treeEl.appendChild(wrap);
  }
}

async function openFile(rel) {
  const res = await fetch("/api/html?path=" + encodeURIComponent(rel));
  if (!res.ok) {
    docEl.textContent = "无法打开 " + rel;
    return;
  }
  const data = await res.json();
  crumbEl.textContent = data.path;
  docEl.innerHTML = data.html;
  document.querySelectorAll(".file").forEach((el) => {
    el.classList.toggle("active", el.dataset.path === rel);
  });
}

loadTree();
