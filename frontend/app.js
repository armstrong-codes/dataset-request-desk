const API = "http://localhost:8000";
const app = document.getElementById("app");
let currentUser = null;
let requests = [];
let episodes = [];
let users = [];
let adminStats = null;
let analytics = null;
let errorMessage = "";

async function api(path, options = {}) {
  const token = localStorage.getItem("token");
  const headers = { ...(options.headers || {}) };
  if (token) headers.Authorization = `Bearer ${token}`;
  if (options.body && !(options.body instanceof FormData))
    headers["Content-Type"] = "application/json";
  const response = await fetch(API + path, { ...options, headers });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || "Request failed");
  return data;
}

function escapeHtml(value) {
  return String(value ?? "").replace(
    /[&<>'"]/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" })[
        c
      ],
  );
}

function renderLogin() {
  app.innerHTML = `<div class="center"><form id="loginForm" class="card login"><h1>Dataset Request Desk</h1><p>Sign in to continue.</p><input id="email" type="email" value="client-a@example.com" placeholder="Email" required><input id="password" type="password" value="client123" placeholder="Password" required><button type="submit">Login</button>${errorMessage ? `<div class="error">${escapeHtml(errorMessage)}</div>` : ""}<p class="muted">Demo: admin@example.com / admin123 · ops1@example.com / ops123 · client-a@example.com / client123</p></form></div>`;
  document.getElementById("loginForm").addEventListener("submit", login);
}

async function login(event) {
  event.preventDefault();
  errorMessage = "";
  try {
    const data = await api("/auth/login", {
      method: "POST",
      body: JSON.stringify({
        email: document.getElementById("email").value,
        password: document.getElementById("password").value,
      }),
    });
    localStorage.setItem("token", data.access_token);
    await load();
  } catch (e) {
    errorMessage = e.message;
    renderLogin();
  }
}

async function load() {
  try {
    currentUser = await api("/auth/me");
    requests = await api("/requests");
    episodes = ["operator", "admin"].includes(currentUser.role)
      ? await api("/episodes")
      : [];
    if (currentUser.role === "admin") {
      users = await api("/users");
      adminStats = await api("/users/stats");
      const end = new Date();
      const start = new Date(end.getTime() - 30 * 24 * 60 * 60 * 1000);
      analytics = await api(
        `/analytics?start=${encodeURIComponent(start.toISOString())}&end=${encodeURIComponent(end.toISOString())}`,
      );
    }
    errorMessage = "";
    renderApp();
  } catch (e) {
    if (
      String(e.message).toLowerCase().includes("token") ||
      e.message.includes("inactive") ||
      e.message.includes("401")
    )
      localStorage.removeItem("token");
    errorMessage = e.message;
    if (!localStorage.getItem("token")) {
      currentUser = null;
      renderLogin();
    } else renderApp();
  }
}

function logout() {
  localStorage.removeItem("token");
  currentUser = null;
  errorMessage = "";
  renderLogin();
}

function requestCard(r) {
  const staff = ["operator", "admin"].includes(currentUser.role);
  let actions = "";
  if (currentUser.role === "client" && r.status === "delivered")
    actions = `<button data-status="accepted" data-id="${r.id}">Accept</button><button class="danger" data-status="rejected" data-id="${r.id}">Reject</button>`;
  if (staff && r.status === "submitted")
    actions = `<button data-status="in_progress" data-id="${r.id}">Start</button>`;
  if (staff && r.status === "in_progress")
    actions = `<button data-status="delivered" data-id="${r.id}">Deliver</button>`;
  if (staff && r.status === "rejected")
    actions = `<button data-status="in_progress" data-id="${r.id}">Rework</button>`;
  let assign = "";
  if (staff && !["delivered", "accepted"].includes(r.status)) {
    const opts = episodes
      .filter((e) => ["good", "usable"].includes(e.quality))
      .map(
        (e) =>
          `<option value="${escapeHtml(e.episode_id)}">${escapeHtml(e.episode_id)} · ${escapeHtml(e.task_name)} · ${escapeHtml(e.quality)}</option>`,
      )
      .join("");
    assign = `<div class="assign"><select data-assign="${r.id}"><option value="">Assign an episode…</option>${opts}</select></div>`;
  }
  return `<div class="card request"><div><b>#${r.id} · ${escapeHtml(r.task_name)}</b><span class="status">${escapeHtml(r.status)}</span><p>${r.episodes_requested} episodes · deadline ${new Date(r.deadline).toLocaleString()}</p></div><div class="actions">${actions}</div>${assign}</div>`;
}

function statCard(label, value) {
  return `<div class="stat"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`;
}

function renderAdminDashboard() {
  const u = adminStats?.users || {};
  const statusRows = analytics?.requests_by_status || [];
  const topTasks = analytics?.top_good_tasks || [];
  return `<section class="admin-panel">
    <div class="panel-heading"><div><h2>Admin Dashboard</h2><p class="muted">Monitor users, requests, inventory and system performance.</p></div><button id="refreshAdmin">Refresh</button></div>
    <div class="stats-grid">${statCard("Total users", u.total || 0)}${statCard("Active users", u.active || 0)}${statCard("Clients", u.clients || 0)}${statCard("Operators", u.operators || 0)}${statCard("Admins", u.admins || 0)}${statCard("Requests", adminStats?.requests || 0)}${statCard("Episodes", adminStats?.episodes || 0)}${statCard("Assignments", adminStats?.assignments || 0)}</div>
    <div class="admin-grid">
      <div class="card"><h3>User management</h3><div class="table user-table"><div class="row user-head"><b>Name</b><b>Email</b><b>Role</b><b>Status</b><b>Action</b></div>${users.map((u) => `<div class="row user-row"><span>${escapeHtml(u.name)}</span><span>${escapeHtml(u.email)}</span><span><select data-role="${u.id}">${["client", "operator", "admin"].map((r) => `<option value="${r}" ${u.role === r ? "selected" : ""}>${r}</option>`).join("")}</select></span><span><span class="status ${u.is_active ? "active" : "inactive"}">${u.is_active ? "Active" : "Inactive"}</span></span><span>${u.id === currentUser.id ? "Current user" : u.is_active ? `<button class="small danger" data-deactivate="${u.id}">Deactivate</button>` : `<button class="small" data-activate="${u.id}">Activate</button>`}</span></div>`).join("")}</div></div>
      <div class="card"><h3>Request status</h3>${statusRows.length ? statusRows.map((x) => `<div class="metric-row"><span>${escapeHtml(x.status)}</span><b>${x.count}</b></div>`).join("") : `<p class="muted">No request data in the last 30 days.</p>`}<hr><h3>Performance</h3><p>Median submitted → delivered: <b>${analytics?.median_submitted_to_delivered_seconds == null ? "—" : Math.round(analytics.median_submitted_to_delivered_seconds / 60) + " min"}</b></p><h3>Top good-quality tasks</h3>${topTasks.length ? topTasks.map((x) => `<div class="metric-row"><span>${escapeHtml(x.task_name)}</span><b>${x.count}</b></div>`).join("") : `<p class="muted">No episode data in the last 30 days.</p>`}</div>
    </div>
  </section>`;
}

function renderApp() {
  const staff = ["operator", "admin"].includes(currentUser.role);
  const createForm =
    currentUser.role === "client"
      ? `<form id="createForm" class="card"><h2>New dataset request</h2><div class="grid"><input id="task" value="pick cup" placeholder="Task name" required><input id="count" type="number" value="5" min="1" required><input id="deadline" type="datetime-local" value="2026-10-10T17:00" required><input id="notes" placeholder="Notes"></div><button>Create request</button></form>`
      : "";
  const inventory = staff
    ? `<section><div class="panel-heading"><h2>Episode inventory</h2><span class="muted">${episodes.length} loaded</span></div><div class="table"><div class="row episode-head"><b>Episode</b><b>Robot</b><b>Task</b><b>Quality</b><b>Duration</b></div>${episodes.map((e) => `<div class="row"><span>${escapeHtml(e.episode_id)}</span><span>${escapeHtml(e.robot_id)}</span><span>${escapeHtml(e.task_name)}</span><span>${escapeHtml(e.quality)}</span><span>${e.duration_seconds}s</span></div>`).join("")}</div></section>`
    : "";
  const admin = currentUser.role === "admin" ? renderAdminDashboard() : "";
  app.innerHTML = `<div class="page"><header><div><h1>Dataset Request Desk</h1><span>${escapeHtml(currentUser.name)} · ${escapeHtml(currentUser.role)}</span></div><button id="logout">Logout</button></header>${errorMessage ? `<div class="error">${escapeHtml(errorMessage)}</div>` : ""}${admin}${createForm}<section><div class="panel-heading"><h2>Requests</h2><span class="muted">${requests.length} request(s)</span></div>${requests.length ? requests.map(requestCard).join("") : `<div class="card muted">No requests yet.</div>`}</section>${inventory}</div>`;
  document.getElementById("logout").onclick = logout;
  const create = document.getElementById("createForm");
  if (create) create.addEventListener("submit", createRequest);
  document
    .querySelectorAll("[data-status]")
    .forEach(
      (b) => (b.onclick = () => changeStatus(b.dataset.id, b.dataset.status)),
    );
  document.querySelectorAll("[data-assign]").forEach(
    (s) =>
      (s.onchange = () => {
        if (s.value) assignEpisode(s.dataset.assign, s.value);
      }),
  );
  document
    .querySelectorAll("[data-role]")
    .forEach((s) => (s.onchange = () => changeRole(s.dataset.role, s.value)));
  document
    .querySelectorAll("[data-deactivate]")
    .forEach(
      (b) => (b.onclick = () => setUserActive(b.dataset.deactivate, false)),
    );
  document
    .querySelectorAll("[data-activate]")
    .forEach(
      (b) => (b.onclick = () => setUserActive(b.dataset.activate, true)),
    );
  const refresh = document.getElementById("refreshAdmin");
  if (refresh) refresh.onclick = load;
}

async function createRequest(event) {
  event.preventDefault();
  try {
    await api("/requests", {
      method: "POST",
      body: JSON.stringify({
        task_name: document.getElementById("task").value,
        episodes_requested: Number(document.getElementById("count").value),
        deadline: new Date(
          document.getElementById("deadline").value,
        ).toISOString(),
        notes: document.getElementById("notes").value,
      }),
    });
    await load();
  } catch (e) {
    errorMessage = e.message;
    renderApp();
  }
}
async function changeStatus(id, status) {
  try {
    await api(`/requests/${id}/status`, {
      method: "POST",
      body: JSON.stringify({ status }),
    });
    await load();
  } catch (e) {
    errorMessage = e.message;
    renderApp();
  }
}
async function assignEpisode(id, episodeId) {
  try {
    await api(`/requests/${id}/assign`, {
      method: "POST",
      body: JSON.stringify({ episode_id: episodeId }),
    });
    await load();
  } catch (e) {
    errorMessage = e.message;
    renderApp();
  }
}
async function changeRole(id, role) {
  try {
    await api(`/users/${id}/role`, {
      method: "PATCH",
      body: JSON.stringify({ role }),
    });
    await load();
  } catch (e) {
    errorMessage = e.message;
    renderApp();
  }
}
async function setUserActive(id, active) {
  try {
    await api(`/users/${id}/${active ? "activate" : "deactivate"}`, {
      method: "PATCH",
    });
    await load();
  } catch (e) {
    errorMessage = e.message;
    renderApp();
  }
}

if (localStorage.getItem("token")) load();
else renderLogin();
