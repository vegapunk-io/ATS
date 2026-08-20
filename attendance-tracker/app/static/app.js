/* Attendance Tracker — frontend app logic */
"use strict";

/* ---------- State ---------- */
const state = {
  me: null,            // current user
  people: [],          // admin: person list
  users: [],           // admin: user list
  groups: [],          // admin: distinct groups
  peopleById: {},      // id -> person
};

const STATUS_LABELS = { present: "Present", absent: "Absent", half_day: "Half day", holiday: "Holiday" };

/* ---------- Helpers ---------- */
function esc(s) {
  return String(s ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function fmtTime(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function fmtDate(iso) {
  if (!iso) return "—";
  const d = new Date(iso + (iso.length === 10 ? "T00:00:00" : ""));
  return d.toLocaleDateString([], { day: "2-digit", month: "short", year: "numeric" });
}

function fmtDur(min) {
  if (min == null) return "—";
  const h = Math.floor(min / 60);
  const m = min % 60;
  if (h === 0) return `${m}m`;
  if (m === 0) return `${h}h`;
  return `${h}h ${m}m`;
}

function emptyState(icon, msg, sub) {
  return `<div class="empty-state"><div class="ico">${icon}</div><div class="msg">${msg}</div>${sub ? `<div class="sub">${sub}</div>` : ""}</div>`;
}

function animateCount(el, target, duration) {
  duration = duration || 600;
  const start = parseInt(el.textContent) || 0;
  const diff = target - start;
  const startTime = performance.now();
  function step(now) {
    const elapsed = now - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const ease = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.round(start + diff * ease);
    if (progress < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

function todayISO() {
  const d = new Date();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${m}-${day}`;
}

function isoOffset(days) {
  const d = new Date();
  d.setDate(d.getDate() - days);
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${m}-${day}`;
}

function badge(status) {
  const label = STATUS_LABELS[status] || status;
  return `<span class="badge ${esc(status)}">${esc(label)}</span>`;
}

function debounce(fn, delay) {
  let timer;
  return function (...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}

function toast(msg, type = "") {
  const wrap = document.getElementById("toast-wrap");
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.textContent = msg;
  wrap.appendChild(el);
  setTimeout(() => el.remove(), 3500);
}

function confirm(title, message) {
  return new Promise((resolve) => {
    openModal(
      title,
      `<div class="del-confirm">
        <p>${message}</p>
        <div class="form-actions">
          <button class="btn secondary" id="confirm-cancel">Cancel</button>
          <button class="btn danger" id="confirm-ok">Confirm</button>
        </div>
      </div>`
    );
    document.getElementById("confirm-cancel").addEventListener("click", () => { closeModal(); resolve(false); });
    document.getElementById("confirm-ok").addEventListener("click", () => { closeModal(); resolve(true); });
  });
}

function openModal(title, bodyHtml) {
  document.getElementById("modal-title").textContent = title;
  document.getElementById("modal-body").innerHTML = bodyHtml;
  document.getElementById("modal-backdrop").classList.add("show");
}

function closeModal() {
  const modal = document.querySelector(".modal");
  const backdrop = document.getElementById("modal-backdrop");
  if (modal) {
    modal.style.animation = "modalOut 0.2s ease forwards";
    setTimeout(() => {
      backdrop.classList.remove("show");
      document.getElementById("modal-body").innerHTML = "";
      if (modal) modal.style.animation = "";
    }, 200);
  } else {
    backdrop.classList.remove("show");
    document.getElementById("modal-body").innerHTML = "";
  }
}

function showView(name) {
  document.querySelectorAll(".view").forEach((v) => v.classList.add("hidden"));
  document.getElementById(`view-${name}`).classList.remove("hidden");
  document.querySelectorAll(".nav-item").forEach((b) => b.classList.toggle("active", b.dataset.view === name));
  window.scrollTo({ top: 0 });
}

async function loadNavBadges() {
  try {
    // Pending leaves count
    const leaves = await api("/api/leaves?status=pending");
    const leavesBadge = document.getElementById("nav-badge-leaves");
    if (leavesBadge) {
      if (leaves.length > 0) {
        leavesBadge.textContent = leaves.length;
        leavesBadge.classList.add("show");
      } else {
        leavesBadge.classList.remove("show");
      }
    }

    // Announcements count (admin only)
    if (state.me && state.me.role === "admin") {
      const anns = await api("/api/announcements/all");
      const annBadge = document.getElementById("nav-badge-announcements");
      if (annBadge) {
        const active = anns.filter(a => a.is_active).length;
        if (active > 0) {
          annBadge.textContent = active;
          annBadge.classList.add("show");
        } else {
          annBadge.classList.remove("show");
        }
      }
    }
  } catch (_) {}
}

/* ---------- API helper ---------- */
function showProgress() {
  const bar = document.getElementById("progress-bar");
  if (bar) { bar.classList.add("active"); bar.classList.remove("complete"); }
}

function hideProgress() {
  const bar = document.getElementById("progress-bar");
  if (bar) { bar.classList.add("complete"); setTimeout(() => bar.classList.remove("active", "complete"), 400); }
}

async function api(path, opts = {}) {
  const headers = { ...(opts.headers || {}) };
  const token = localStorage.getItem("token");
  if (token) headers["Authorization"] = "Bearer " + token;
  if (opts.body && !(opts.body instanceof FormData) && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }
  
  // Show loading state on buttons if requested
  let btn = null;
  if (opts.loadingBtn) {
    btn = document.getElementById(opts.loadingBtn);
    if (btn) {
      btn._originalHtml = btn.innerHTML;
      btn.disabled = true;
      btn.innerHTML = '<span class="spinner"></span> Loading...';
    }
  }
  
  showProgress();
  try {
    const res = await fetch(path, { ...opts, headers });
    if (res.status === 401) {
      localStorage.removeItem("token");
      window.location.href = "/login";
      throw new Error("Session expired");
    }
    if (!res.ok) {
      let detail = `Request failed (${res.status})`;
      try {
        const data = await res.json();
        if (data.detail) detail = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
      } catch (_) {}
      throw new Error(detail);
    }
    if (res.status === 204) return null;
    return res.json();
  } finally {
    hideProgress();
    if (btn && btn._originalHtml) {
      btn.disabled = false;
      btn.innerHTML = btn._originalHtml;
    }
  }
}

const q = (id) => document.getElementById(id);

/* ---------- Navigation ---------- */
function bindNav() {
  document.querySelectorAll(".nav-item").forEach((btn) => {
    btn.addEventListener("click", () => {
      showView(btn.dataset.view);
      const loaders = {
        home: loadDashboard,
        calendar: loadCalendar,
        records: loadRecords,
        leaves: loadLeaves,
        breaks: loadBreaks,
        team: loadTeam,
        people: loadPeople,
        users: loadUsers,
        departments: loadDepartments,
        announcements: loadAnnouncements,
        salary: loadSalary,
        reports: loadReports,
        holidays: loadHolidays,
        shifts: loadShifts,
        notifications: loadNotifications,
        settings: loadSettings,
        profile: loadProfile,
        overtime: loadOvertime,
        "shift-swaps": loadShiftSwaps,
        tasks: loadTasks,
        chat: loadChat,
        meetings: loadMeetings,
        "activity-logs": loadActivityLogs,
      };
      (loaders[btn.dataset.view] || (() => {}))();
    });
  });
}

/* =========================================================
   DASHBOARD
========================================================= */
async function loadDashboard() {
  const [today, stats] = await Promise.all([
    api("/api/attendance/today"),
    api("/api/attendance/stats"),
  ]);
  renderHero(today);
  renderDashboardStats(stats);
  await loadWeekStrip();
  await loadMyRecent();
  await loadCharts();
  await loadAnnouncementBanner();
  renderQuickStats(stats);
}

function setText(id, val) {
  const el = q(id);
  if (el) el.textContent = val;
}

function renderHero(rec) {
  const now = new Date();
  setText("hero-date", now.toLocaleDateString([], { weekday: "long", year: "numeric", month: "long", day: "numeric" }));
  setText("hero-day", STATUS_LABELS[rec?.status] === undefined ? "No record yet" : STATUS_LABELS[rec.status]);

  setText("hero-in", fmtTime(rec?.check_in));
  setText("hero-out", fmtTime(rec?.check_out));
  setText("hero-dur", fmtDur(rec?.duration_minutes));
  setText("hero-status", rec ? STATUS_LABELS[rec.status] || rec.status : "Not checked in");

  const statusWrap = q("hero-status-wrap");
  if (statusWrap) {
    const pill = document.createElement("div");
    pill.className = "status-pill " + (rec && rec.check_in && !rec.check_out ? "on" : "off");
    pill.innerHTML = `<span class="dot"></span>${rec && rec.check_in && !rec.check_out ? "On clock" : "Off clock"}`;
    statusWrap.innerHTML = "";
    statusWrap.appendChild(pill);
  }

  const canCheck = state.me && state.me.person_id != null;
  const checkInBtn = q("btn-checkin");
  const checkOutBtn = q("btn-checkout");
  if (canCheck) {
    checkInBtn.disabled = !!(rec && rec.check_in);
    checkOutBtn.disabled = !(rec && rec.check_in && !rec.check_out);
  } else {
    checkInBtn.disabled = true;
    checkOutBtn.disabled = true;
  }
}

async function loadWeekStrip() {
  const from = isoOffset(6);
  const records = await api(`/api/attendance?date_from=${from}&date_to=${todayISO()}&limit=30`);
  const byDate = {};
  records.forEach((r) => (byDate[r.date] = r));
  const wrap = q("week-strip");
  const days = [];
  for (let i = 6; i >= 0; i--) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    const iso = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
    const rec = byDate[iso];
    let ico = "—";
    if (rec) {
      if (rec.status === "present") ico = rec.check_out ? "✅" : "🕐";
      else if (rec.status === "half_day") ico = "🌗";
      else if (rec.status === "absent") ico = "❌";
      else if (rec.status === "holiday") ico = "🎉";
    }
    days.push(`
      <div class="week-day ${iso === todayISO() ? "today" : ""}">
        <div class="wd">${d.toLocaleDateString([], { weekday: "short" })}</div>
        <div class="wn">${d.toLocaleDateString([], { day: "numeric" })}</div>
        <div class="week-ico">${ico}</div>
      </div>`);
  }
  wrap.innerHTML = days.join("");
}

async function loadMyRecent() {
  const records = await api(`/api/attendance?limit=10`);
  q("my-recent-table").innerHTML = renderRecordsTable(records, false);
}

function renderDashboardStats(stats) {
  setText("stat-streak", stats.streak);
  setText("stat-present", stats.total_present_month);
  setText("stat-absent", stats.total_absent_month);
  setText("stat-hours", stats.total_hours_month + "h");
  setText("stat-rate", Math.round(stats.attendance_rate_month * 100) + "%");
  setText("stat-late", stats.late_count);
  
  // Update streak badge in hero
  const streakCount = q("streak-count");
  if (streakCount) {
    streakCount.textContent = stats.streak;
  }
}

function renderQuickStats(stats) {
  // Quick stats are rendered below the hero, before charts
}

async function loadAnnouncementBanner() {
  try {
    const anns = await api("/api/announcements");
    if (anns.length > 0) {
      const latest = anns[0];
      const banner = document.getElementById("announcement-banner");
      const text = document.getElementById("announcement-banner-text");
      const closeBtn = document.getElementById("announcement-banner-close");
      
      if (banner && text) {
        text.textContent = latest.title;
        banner.className = "announcement-banner " + latest.priority;
        banner.style.display = "flex";
        
        closeBtn.addEventListener("click", () => {
          banner.style.display = "none";
        });
      }
    }
  } catch (_) {}
}

/* =========================================================
   CALENDAR VIEW
========================================================= */
let calYear, calMonth;

function initCalendar() {
  const now = new Date();
  calYear = now.getFullYear();
  calMonth = now.getMonth();
  loadCalendar();
}

async function loadCalendar() {
  const monthLabel = q("cal-month-label");
  if (monthLabel) {
    monthLabel.textContent = new Date(calYear, calMonth).toLocaleDateString([], { month: "long", year: "numeric" });
  }

  const from = `${calYear}-${String(calMonth + 1).padStart(2, "0")}-01`;
  const lastDay = new Date(calYear, calMonth + 1, 0).getDate();
  const to = `${calYear}-${String(calMonth + 1).padStart(2, "0")}-${String(lastDay).padStart(2, "0")}`;

  const records = await api(`/api/attendance?date_from=${from}&date_to=${to}&limit=500`);
  const byDate = {};
  records.forEach(r => byDate[r.date] = r);

  const grid = q("calendar-grid");
  if (!grid) return;

  const dayNames = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  let html = dayNames.map(d => `<div class="cal-header">${d}</div>`).join("");

  const firstDay = new Date(calYear, calMonth, 1).getDay();
  for (let i = 0; i < firstDay; i++) {
    html += `<div class="cal-day empty"></div>`;
  }

  const today = todayISO();
  for (let d = 1; d <= lastDay; d++) {
    const dateStr = `${calYear}-${String(calMonth + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
    const rec = byDate[dateStr];
    const isToday = dateStr === today;
    let statusClass = "";
    let statusText = "";

    if (rec) {
      statusClass = rec.status;
      if (rec.status === "present") statusText = rec.check_out ? "✓" : "🕐";
      else if (rec.status === "absent") statusText = "✗";
      else if (rec.status === "half_day") statusText = "½";
      else if (rec.status === "holiday") statusText = "🎉";
    }

    html += `<div class="cal-day ${statusClass} ${isToday ? "today" : ""}">
      <span class="day-num">${d}</span>
      <span class="day-status">${statusText}</span>
    </div>`;
  }

  grid.innerHTML = html;
}

/* =========================================================
   LEAVES
========================================================= */
async function loadLeaves() {
  await applyLeaveFilters();
}

async function applyLeaveFilters() {
  const status = q("leave-status-filter")?.value;
  const params = new URLSearchParams();
  if (status) params.set("status", status);

  const leaves = await api(`/api/leaves?${params}`);
  renderLeaves(leaves);
}

function renderLeaves(leaves) {
  if (!leaves.length) {
    q("leaves-table").innerHTML = emptyState("🏖️", "No leave requests", 'Click "Apply Leave" to create one.');
    return;
  }

  const isAdmin = state.me && state.me.role === "admin";
  const rows = leaves.map(l => {
    const statusBadge = `<span class="badge ${l.status === "approved" ? "active" : l.status === "rejected" ? "absent" : "half_day"}">${l.status}</span>`;
    const typeBadge = `<span class="break-type-badge ${l.leave_type}">${l.leave_type}</span>`;

    let actions = "";
    if (isAdmin && l.status === "pending") {
      actions = `<div class="action-cell">
        <button class="btn sm" onclick="approveLeave(${l.id})">Approve</button>
        <button class="btn sm danger" onclick="rejectLeave(${l.id})">Reject</button>
      </div>`;
    } else if (!isAdmin && l.status === "pending") {
      actions = `<button class="btn sm danger" onclick="deleteLeave(${l.id})">Cancel</button>`;
    }

    return `<tr>
      <td><b>${esc(l.person_name || "—")}</b></td>
      <td>${typeBadge}</td>
      <td class="mono">${fmtDate(l.start_date)}</td>
      <td class="mono">${fmtDate(l.end_date)}</td>
      <td class="muted">${esc(l.reason || "—")}</td>
      <td>${statusBadge}</td>
      <td>${actions}</td>
    </tr>`;
  }).join("");

  q("leaves-table").innerHTML = `<table>
    <thead><tr><th>Person</th><th>Type</th><th>From</th><th>To</th><th>Reason</th><th>Status</th><th></th></tr></thead>
    <tbody>${rows}</tbody></table>`;
}

function openApplyLeaveModal() {
  openModal(
    "Apply for Leave",
    `<form id="leave-form">
      <div class="form-row"><label>Leave Type</label>
        <select name="leave_type">
          <option value="sick">Sick Leave</option>
          <option value="casual">Casual Leave</option>
          <option value="annual">Annual Leave</option>
          <option value="unpaid">Unpaid Leave</option>
          <option value="other">Other</option>
        </select>
      </div>
      <div class="form-grid">
        <div class="form-row"><label>Start Date *</label><input type="date" name="start_date" required /></div>
        <div class="form-row"><label>End Date *</label><input type="date" name="end_date" required /></div>
      </div>
      <div class="form-row"><label>Reason</label><input name="reason" placeholder="Optional reason" /></div>
      <div class="form-actions">
        <button type="button" class="btn secondary" onclick="closeModal()">Cancel</button>
        <button type="submit" class="btn">Submit Request</button>
      </div>
    </form>`
  );
  q("leave-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const body = {
      leave_type: fd.get("leave_type"),
      start_date: fd.get("start_date"),
      end_date: fd.get("end_date"),
      reason: fd.get("reason") || null,
    };
    try {
      await api("/api/leaves", { method: "POST", body: JSON.stringify(body) });
      toast("Leave request submitted", "success");
      closeModal();
      await applyLeaveFilters();
    } catch (err) {
      toast(err.message, "error");
    }
  });
}

window.approveLeave = async (id) => {
  try {
    await api(`/api/leaves/${id}`, { method: "PATCH", body: JSON.stringify({ status: "approved" }) });
    toast("Leave approved", "success");
    await applyLeaveFilters();
  } catch (err) {
    toast(err.message, "error");
  }
};

window.rejectLeave = async (id) => {
  try {
    await api(`/api/leaves/${id}`, { method: "PATCH", body: JSON.stringify({ status: "rejected" }) });
    toast("Leave rejected", "success");
    await applyLeaveFilters();
  } catch (err) {
    toast(err.message, "error");
  }
};

window.deleteLeave = async (id) => {
  const ok = await confirm("Cancel Leave", "Cancel this leave request?");
  if (ok) {
    try {
      await api(`/api/leaves/${id}`, { method: "DELETE" });
      toast("Leave cancelled", "success");
      await applyLeaveFilters();
    } catch (err) {
      toast(err.message, "error");
    }
  }
};

/* =========================================================
   BREAKS
========================================================= */
async function loadBreaks() {
  const breaks = await api("/api/breaks/today");
  const status = await api("/api/breaks/status");

  // Update hero
  const statusEl = q("break-status");
  if (status.on_break) {
    statusEl.textContent = `On ${status.break_type} break`;
    q("btn-end-break").disabled = false;
    q("btn-start-break").disabled = true;
  } else {
    statusEl.textContent = "No break started";
    q("btn-end-break").disabled = true;
    q("btn-start-break").disabled = false;
  }

  setText("break-count", breaks.length);
  const totalMin = breaks.reduce((acc, b) => acc + (b.duration_minutes || 0), 0);
  setText("break-total", totalMin + "m");

  renderBreaks(breaks);
}

function renderBreaks(breaks) {
  if (!breaks.length) {
    q("breaks-table").innerHTML = `<div class="empty">No breaks today</div>`;
    return;
  }
  const rows = breaks.map(b => `<tr>
    <td class="mono">${fmtTime(b.break_start)}</td>
    <td class="mono">${b.break_end ? fmtTime(b.break_end) : "—"}</td>
    <td><span class="break-type-badge ${b.break_type}">${b.break_type}</span></td>
    <td class="mono">${b.duration_minutes != null ? b.duration_minutes + "m" : "—"}</td>
  </tr>`).join("");

  q("breaks-table").innerHTML = `<table>
    <thead><tr><th>Started</th><th>Ended</th><th>Type</th><th>Duration</th></tr></thead>
    <tbody>${rows}</tbody></table>`;
}

async function startBreak() {
  openModal(
    "Start Break",
    `<form id="break-form">
      <div class="form-row"><label>Break Type</label>
        <select name="break_type">
          <option value="lunch">Lunch</option>
          <option value="tea">Tea</option>
          <option value="coffee">Coffee</option>
          <option value="other">Other</option>
        </select>
      </div>
      <div class="form-actions">
        <button type="button" class="btn secondary" onclick="closeModal()">Cancel</button>
        <button type="submit" class="btn">Start Break</button>
      </div>
    </form>`
  );
  q("break-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    try {
      await api("/api/breaks/start", { method: "POST", body: JSON.stringify({ break_type: fd.get("break_type") }) });
      toast("Break started", "success");
      closeModal();
      await loadBreaks();
    } catch (err) {
      toast(err.message, "error");
    }
  });
}

async function endBreak() {
  try {
    await api("/api/breaks/end", { method: "POST" });
    toast("Break ended", "success");
    await loadBreaks();
  } catch (err) {
    toast(err.message, "error");
  }
}

/* =========================================================
   TEAM DASHBOARD
========================================================= */
async function loadTeam() {
  const team = await api("/api/attendance/team");

  const total = team.length;
  const inCount = team.filter(m => m.status === "present" || m.status === "half_day").length;
  const outCount = team.filter(m => m.status === "absent").length;
  const onClock = team.filter(m => m.is_on_clock).length;

  setText("team-total", total);
  setText("team-in", inCount);
  setText("team-out", outCount);
  setText("team-onclock", onClock);

  renderTeam(team);
}

function renderTeam(team) {
  if (!team.length) {
    q("team-table").innerHTML = `<div class="empty">No team members</div>`;
    return;
  }

  const rows = team.map(m => `<tr>
    <td><div style="display:flex;align-items:center;gap:10px;">
      <span class="team-status-dot ${m.is_on_clock ? "in" : "out"}"></span>
      <b>${esc(m.person_name)}</b>
    </div></td>
    <td class="muted">${esc(m.group_name || "—")}</td>
    <td>${badge(m.status)}</td>
    <td class="mono">${fmtTime(m.check_in)}</td>
    <td class="mono">${fmtTime(m.check_out)}</td>
    <td>${m.is_on_clock ? '<span class="badge active">On clock</span>' : '<span class="badge user">Off clock</span>'}</td>
  </tr>`).join("");

  q("team-table").innerHTML = `<table>
    <thead><tr><th>Person</th><th>Group</th><th>Status</th><th>Check-in</th><th>Check-out</th><th>Clock</th></tr></thead>
    <tbody>${rows}</tbody></table>`;
}

/* =========================================================
   DEPARTMENTS
========================================================= */
async function loadDepartments() {
  const depts = await api("/api/departments");
  renderDepartments(depts);
}

function renderDepartments(depts) {
  if (!depts.length) {
    q("departments-table").innerHTML = emptyState("🏢", "No departments", "Create your first department.");
    return;
  }
  const rows = depts.map(d => `<tr>
    <td><b>${esc(d.name)}</b></td>
    <td class="muted">${esc(d.description || "—")}</td>
    <td>${esc(d.head_name || "—")}</td>
    <td>${d.member_count}</td>
    <td>${d.is_active ? '<span class="badge active">Active</span>' : '<span class="badge inactive">Inactive</span>'}</td>
    <td><div class="action-cell">
      <button class="btn sm secondary" onclick="editDept(${d.id})">Edit</button>
      <button class="btn sm danger" onclick="deleteDept(${d.id})">Del</button>
    </div></td>
  </tr>`).join("");

  q("departments-table").innerHTML = `<table>
    <thead><tr><th>Name</th><th>Description</th><th>Head</th><th>Members</th><th>Status</th><th></th></tr></thead>
    <tbody>${rows}</tbody></table>`;
}

function deptForm(dept) {
  const peopleOpts = `<option value="">— none —</option>` + state.people
    .filter(p => p.is_active).map(p => `<option value="${p.id}" ${dept?.head_id === p.id ? "selected" : ""}>${esc(p.full_name)}</option>`).join("");
  return `<form id="dept-form">
    <div class="form-row"><label>Name *</label><input name="name" required value="${esc(dept?.name || "")}" /></div>
    <div class="form-row"><label>Description</label><input name="description" value="${esc(dept?.description || "")}" /></div>
    <div class="form-row"><label>Department Head</label><select name="head_id">${peopleOpts}</select></div>
    <div class="form-actions">
      <button type="button" class="btn secondary" onclick="closeModal()">Cancel</button>
      <button type="submit" class="btn">${dept ? "Save" : "Create"}</button>
    </div>
  </form>`;
}

function openDeptModal(dept) {
  openModal(dept ? "Edit Department" : "New Department", deptForm(dept));
  q("dept-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const body = { name: fd.get("name").trim(), description: fd.get("description").trim() || null, head_id: fd.get("head_id") ? Number(fd.get("head_id")) : null };
    try {
      if (dept) {
        await api(`/api/departments/${dept.id}`, { method: "PATCH", body: JSON.stringify(body) });
        toast("Department updated", "success");
      } else {
        await api("/api/departments", { method: "POST", body: JSON.stringify(body) });
        toast("Department created", "success");
      }
      closeModal(); await loadDepartments();
    } catch (err) { toast(err.message, "error"); }
  });
}

window.editDept = async (id) => {
  const depts = await api("/api/departments");
  const d = depts.find(x => x.id === id);
  if (d) openDeptModal(d);
};

window.deleteDept = async (id) => {
  const ok = await confirm("Delete Department", "Delete this department?");
  if (ok) {
    try { await api(`/api/departments/${id}`, { method: "DELETE" }); toast("Deleted", "success"); await loadDepartments(); }
    catch (err) { toast(err.message, "error"); }
  }
};

/* =========================================================
   ANNOUNCEMENTS
========================================================= */
async function loadAnnouncements() {
  const anns = await api("/api/announcements/all");
  renderAnnouncements(anns);
}

function renderAnnouncements(anns) {
  if (!anns.length) {
    q("announcements-list").innerHTML = emptyState("📢", "No announcements", "Create the first announcement.");
    return;
  }
  const isAdmin = state.me && state.me.role === "admin";
  q("announcements-list").innerHTML = anns.map(a => `
    <div class="announcement-card priority-${a.priority}">
      <div class="announcement-header">
        <div>
          <div class="announcement-title">${esc(a.title)}</div>
          <div class="announcement-meta">${fmtDate(a.created_at)} ${a.created_by_name ? "by " + esc(a.created_by_name) : ""}</div>
        </div>
        <div style="display:flex;align-items:center;gap:8px;">
          <span class="priority-badge ${a.priority}">${a.priority}</span>
          ${isAdmin ? `<button class="btn sm secondary" onclick="editAnnouncement(${a.id})">Edit</button>
          <button class="btn sm danger" onclick="deleteAnnouncement(${a.id})">Del</button>` : ""}
        </div>
      </div>
      <div class="announcement-content">${esc(a.content)}</div>
    </div>
  `).join("");
}

function openAnnouncementModal() {
  openModal("New Announcement", `<form id="ann-form">
    <div class="form-row"><label>Title *</label><input name="title" required /></div>
    <div class="form-row"><label>Content *</label><textarea name="content" rows="4" required></textarea></div>
    <div class="form-row"><label>Priority</label>
      <select name="priority"><option value="low">Low</option><option value="normal" selected>Normal</option><option value="high">High</option><option value="urgent">Urgent</option></select>
    </div>
    <div class="form-actions">
      <button type="button" class="btn secondary" onclick="closeModal()">Cancel</button>
      <button type="submit" class="btn">Publish</button>
    </div>
  </form>`);
  q("ann-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    try {
      await api("/api/announcements", { method: "POST", body: JSON.stringify({ title: fd.get("title"), content: fd.get("content"), priority: fd.get("priority") }) });
      toast("Announcement published", "success"); closeModal(); await loadAnnouncements();
    } catch (err) { toast(err.message, "error"); }
  });
}

window.editAnnouncement = async (id) => {
  try {
    const anns = await api("/api/announcements/all");
    const a = anns.find(x => x.id === id);
    if (!a) return;
    openModal("Edit Announcement", `<form id="ann-edit-form">
      <div class="form-row"><label>Title *</label><input name="title" value="${esc(a.title)}" required /></div>
      <div class="form-row"><label>Content *</label><textarea name="content" rows="4" required>${esc(a.content)}</textarea></div>
      <div class="form-row"><label>Priority</label>
        <select name="priority">
          <option value="low" ${a.priority==="low"?"selected":""}>Low</option>
          <option value="normal" ${a.priority==="normal"?"selected":""}>Normal</option>
          <option value="high" ${a.priority==="high"?"selected":""}>High</option>
          <option value="urgent" ${a.priority==="urgent"?"selected":""}>Urgent</option>
        </select>
      </div>
      <div class="form-actions">
        <button type="button" class="btn secondary" onclick="closeModal()">Cancel</button>
        <button type="submit" class="btn">Save</button>
      </div>
    </form>`);
    q("ann-edit-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const fd = new FormData(e.target);
      try {
        await api(`/api/announcements/${id}`, { method: "PATCH", body: JSON.stringify({ title: fd.get("title"), content: fd.get("content"), priority: fd.get("priority") }) });
        toast("Announcement updated", "success"); closeModal(); await loadAnnouncements();
      } catch (err) { toast(err.message, "error"); }
    });
  } catch (err) { toast(err.message, "error"); }
};

window.deleteAnnouncement = async (id) => {
  const ok = await confirm("Delete Announcement", "Delete this announcement?");
  if (ok) {
    try { await api(`/api/announcements/${id}`, { method: "DELETE" }); toast("Deleted", "success"); await loadAnnouncements(); }
    catch (err) { toast(err.message, "error"); }
  }
};

/* =========================================================
   SALARY
========================================================= */
async function loadSalary() {
  const monthSel = q("salary-month");
  const yearSel = q("salary-year");
  if (monthSel && !monthSel.options.length) {
    for (let m = 1; m <= 12; m++) monthSel.add(new Option(new Date(2024, m - 1).toLocaleString([], { month: "long" }), m));
    monthSel.value = new Date().getMonth() + 1;
  }
  if (yearSel && !yearSel.options.length) {
    for (let y = 2024; y <= 2030; y++) yearSel.add(new Option(y, y));
    yearSel.value = new Date().getFullYear();
  }
  await loadSalaryData();
}

async function loadSalaryData() {
  const month = q("salary-month").value;
  const year = q("salary-year").value;
  const records = await api(`/api/salary?month=${month}&year=${year}`);

  const totalNet = records.reduce((a, r) => a + r.net_salary, 0);
  const totalPresent = records.reduce((a, r) => a + r.present_days, 0);
  q("salary-stats").innerHTML = `
    <div class="stat-card"><div class="v">${records.length}</div><div class="k">👥 Employees</div></div>
    <div class="stat-card"><div class="v">₹${totalNet.toLocaleString()}</div><div class="k">💰 Total Payroll</div></div>
    <div class="stat-card"><div class="v">${totalPresent}</div><div class="k">✅ Total Present Days</div></div>`;

  if (!records.length) {
    q("salary-table").innerHTML = `<div class="empty">No salary records for this month. Click "Generate Salary" to create.</div>`;
    return;
  }
  const rows = records.map(s => `<tr>
    <td><b>${esc(s.person_name || "—")}</b></td>
    <td class="mono">₹${s.base_salary.toLocaleString()}</td>
    <td>${s.present_days}/${s.working_days}</td>
    <td>${s.absent_days}</td>
    <td class="mono">${s.overtime_hours}h</td>
    <td class="mono salary-negative">${s.deduction > 0 ? "-₹" + s.deduction.toLocaleString() : "—"}</td>
    <td class="mono salary-positive">₹${s.net_salary.toLocaleString()}</td>
    <td><span class="badge ${s.status === "paid" ? "active" : s.status === "processed" ? "half_day" : "user"}">${s.status}</span></td>
    <td><button class="btn sm secondary" onclick="editSalary(${s.id})">Edit</button></td>
  </tr>`).join("");

  q("salary-table").innerHTML = `<table>
    <thead><tr><th>Person</th><th>Base</th><th>Present</th><th>Absent</th><th>OT</th><th>Deduction</th><th>Net Salary</th><th>Status</th><th></th></tr></thead>
    <tbody>${rows}</tbody></table>`;
}

function openGenerateSalaryModal() {
  const month = new Date().getMonth() + 1;
  const year = new Date().getFullYear();
  openModal("Generate Salary", `<form id="gen-salary-form">
    <div class="form-grid">
      <div class="form-row"><label>Month *</label><select name="month" required>${[1,2,3,4,5,6,7,8,9,10,11,12].map(m => `<option value="${m}" ${m === month ? "selected" : ""}>${new Date(2024, m-1).toLocaleString([],{month:"long"})}</option>`).join("")}</select></div>
      <div class="form-row"><label>Year *</label><input type="number" name="year" value="${year}" min="2020" max="2030" required /></div>
    </div>
    <div class="form-row"><label>Base Salary (₹) *</label><input type="number" name="base_salary" value="50000" min="0" required /></div>
    <div class="form-actions">
      <button type="button" class="btn secondary" onclick="closeModal()">Cancel</button>
      <button type="submit" class="btn">Generate</button>
    </div>
  </form>`);
  q("gen-salary-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    try {
      const result = await api("/api/salary/generate", { method: "POST", body: JSON.stringify({ month: Number(fd.get("month")), year: Number(fd.get("year")), base_salary: Number(fd.get("base_salary")) }) });
      toast(`Generated ${result.length} salary records`, "success"); closeModal(); await loadSalaryData();
    } catch (err) { toast(err.message, "error"); }
  });
}

window.editSalary = async (id) => {
  const month = q("salary-month").value;
  const year = q("salary-year").value;
  const records = await api(`/api/salary?month=${month}&year=${year}`);
  const s = records.find(x => x.id === id);
  if (!s) return;
  openModal("Edit Salary — " + esc(s.person_name || ""), `<form id="sal-edit-form">
    <div class="form-grid">
      <div class="form-row"><label>Bonus (₹)</label><input type="number" name="bonus" value="${s.bonus}" min="0" step="0.01" /></div>
      <div class="form-row"><label>Deduction (₹)</label><input type="number" name="deduction" value="${s.deduction}" min="0" step="0.01" /></div>
    </div>
    <div class="form-row"><label>Status</label>
      <select name="status">
        <option value="pending" ${s.status==="pending"?"selected":""}>Pending</option>
        <option value="processed" ${s.status==="processed"?"selected":""}>Processed</option>
        <option value="paid" ${s.status==="paid"?"selected":""}>Paid</option>
      </select>
    </div>
    <div class="form-actions">
      <button type="button" class="btn secondary" onclick="closeModal()">Cancel</button>
      <button type="submit" class="btn">Save</button>
    </div>
  </form>`);
  q("sal-edit-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const bonus = fd.get("bonus") || 0;
    const deduction = fd.get("deduction") || 0;
    const statusVal = fd.get("status");
    try {
      await api(`/api/salary/${id}?bonus=${bonus}&deduction=${deduction}&status=${encodeURIComponent(statusVal)}`, { method: "PATCH" });
      toast("Salary updated", "success"); closeModal(); await loadSalaryData();
    } catch (err) { toast(err.message, "error"); }
  });
};

/* =========================================================
   SETTINGS
========================================================= */
async function loadSettings() {
  const settings = await api("/api/settings");
  renderSettings(settings);
}

function renderSettings(settings) {
  if (!settings.length) {
    q("settings-table").innerHTML = emptyState("⚙️", "No settings", "Add your first setting.");
    return;
  }
  const rows = settings.map(s => `<tr>
    <td><b>${esc(s.key)}</b></td>
    <td class="muted">${esc(s.description || "—")}</td>
    <td><input class="setting-input" data-key="${esc(s.key)}" value="${esc(s.value || "")}" style="width:200px;" /></td>
    <td><button class="btn sm" onclick="saveSetting('${esc(s.key)}')">Save</button></td>
  </tr>`).join("");

  q("settings-table").innerHTML = `<table>
    <thead><tr><th>Key</th><th>Description</th><th>Value</th><th></th></tr></thead>
    <tbody>${rows}</tbody></table>`;
}

/* =========================================================
   OVERTIME
========================================================= */
async function loadOvertime() {
  const records = await api("/api/overtime");
  renderOvertime(records);
}

function renderOvertime(records) {
  if (!records.length) {
    q("overtime-table").innerHTML = emptyState("⏰", "No overtime requests", "Request overtime hours.");
    return;
  }
  const isAdmin = state.me && state.me.role === "admin";
  const rows = records.map(o => `<tr>
    <td><b>${esc(o.person_name || "—")}</b></td>
    <td>${fmtDate(o.date)}</td>
    <td class="mono">${o.hours}h</td>
    <td class="muted">${esc(o.reason || "—")}</td>
    <td><span class="badge ${o.status}">${o.status}</span></td>
    ${isAdmin ? `<td><div class="action-cell">
      ${o.status === "pending" ? `<button class="btn sm" onclick="approveOvertime(${o.id})">Approve</button>
      <button class="btn sm danger" onclick="rejectOvertime(${o.id})">Reject</button>` : ""}
    </div></td>` : ""}
  </tr>`).join("");
  q("overtime-table").innerHTML = `<table>
    <thead><tr><th>Person</th><th>Date</th><th>Hours</th><th>Reason</th><th>Status</th>${isAdmin ? "<th></th>" : ""}</tr></thead>
    <tbody>${rows}</tbody></table>`;
}

function openOvertimeModal() {
  openModal("Request Overtime", `<form id="ot-form">
    <div class="form-grid">
      <div class="form-row"><label>Date *</label><input type="date" name="date" value="${todayISO()}" required /></div>
      <div class="form-row"><label>Hours *</label><input type="number" name="hours" min="0.5" max="24" step="0.5" value="1" required /></div>
    </div>
    <div class="form-row"><label>Reason</label><textarea name="reason" rows="3"></textarea></div>
    <div class="form-actions">
      <button type="button" class="btn secondary" onclick="closeModal()">Cancel</button>
      <button type="submit" class="btn">Submit</button>
    </div>
  </form>`);
  q("ot-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    try {
      await api("/api/overtime", { method: "POST", body: JSON.stringify({ date: fd.get("date"), hours: Number(fd.get("hours")), reason: fd.get("reason") || null }) });
      toast("Overtime requested", "success"); closeModal(); await loadOvertime();
    } catch (err) { toast(err.message, "error"); }
  });
}

window.approveOvertime = async (id) => {
  try { await api(`/api/overtime/${id}`, { method: "PATCH", body: JSON.stringify({ status: "approved" }) }); toast("Approved", "success"); await loadOvertime(); }
  catch (err) { toast(err.message, "error"); }
};

window.rejectOvertime = async (id) => {
  try { await api(`/api/overtime/${id}`, { method: "PATCH", body: JSON.stringify({ status: "rejected" }) }); toast("Rejected", "success"); await loadOvertime(); }
  catch (err) { toast(err.message, "error"); }
};

/* =========================================================
   SHIFT SWAPS
========================================================= */
async function loadShiftSwaps() {
  const swaps = await api("/api/shift-swaps");
  renderShiftSwaps(swaps);
}

function renderShiftSwaps(swaps) {
  if (!swaps.length) {
    q("swaps-table").innerHTML = emptyState("🔄", "No shift swap requests", "Request a shift swap.");
    return;
  }
  const isAdmin = state.me && state.me.role === "admin";
  const rows = swaps.map(s => `<tr>
    <td><b>${esc(s.requester_name || "—")}</b></td>
    <td>${fmtDate(s.requester_date)}</td>
    <td>${s.target_name ? esc(s.target_name) : "—"}</td>
    <td>${s.target_date ? fmtDate(s.target_date) : "—"}</td>
    <td class="muted">${esc(s.reason || "—")}</td>
    <td><span class="badge ${s.status}">${s.status}</span></td>
    ${isAdmin && s.status === "pending" ? `<td><div class="action-cell">
      <button class="btn sm" onclick="approveSwap(${s.id})">Approve</button>
      <button class="btn sm danger" onclick="rejectSwap(${s.id})">Reject</button>
    </div></td>` : !isAdmin && s.status === "pending" && s.requester_id === state.me?.person_id ? `<td><button class="btn sm danger" onclick="cancelSwap(${s.id})">Cancel</button></td>` : "<td></td>"}
  </tr>`).join("");
  q("swaps-table").innerHTML = `<table>
    <thead><tr><th>Requester</th><th>Their Date</th><th>Target</th><th>Target Date</th><th>Reason</th><th>Status</th><th></th></tr></thead>
    <tbody>${rows}</tbody></table>`;
}

function openSwapModal() {
  const peopleOpts = (state.people || []).map(p => `<option value="${p.id}">${esc(p.full_name)}</option>`).join("");
  openModal("Request Shift Swap", `<form id="swap-form">
    <div class="form-grid">
      <div class="form-row"><label>Your Date *</label><input type="date" name="requester_date" required /></div>
      <div class="form-row"><label>Swap With</label><select name="target_id"><option value="">— Select person —</option>${peopleOpts}</select></div>
    </div>
    <div class="form-row"><label>Their Date</label><input type="date" name="target_date" /></div>
    <div class="form-row"><label>Reason</label><textarea name="reason" rows="3"></textarea></div>
    <div class="form-actions">
      <button type="button" class="btn secondary" onclick="closeModal()">Cancel</button>
      <button type="submit" class="btn">Submit</button>
    </div>
  </form>`);
  q("swap-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    try {
      await api("/api/shift-swaps", { method: "POST", body: JSON.stringify({
        requester_date: fd.get("requester_date"),
        target_id: fd.get("target_id") ? Number(fd.get("target_id")) : null,
        target_date: fd.get("target_date") || null,
        reason: fd.get("reason") || null,
      }) });
      toast("Swap requested", "success"); closeModal(); await loadShiftSwaps();
    } catch (err) { toast(err.message, "error"); }
  });
}

window.approveSwap = async (id) => {
  try { await api(`/api/shift-swaps/${id}`, { method: "PATCH", body: JSON.stringify({ status: "accepted" }) }); toast("Approved", "success"); await loadShiftSwaps(); }
  catch (err) { toast(err.message, "error"); }
};

window.rejectSwap = async (id) => {
  try { await api(`/api/shift-swaps/${id}`, { method: "PATCH", body: JSON.stringify({ status: "rejected" }) }); toast("Rejected", "success"); await loadShiftSwaps(); }
  catch (err) { toast(err.message, "error"); }
};

window.cancelSwap = async (id) => {
  try { await api(`/api/shift-swaps/${id}`, { method: "PATCH", body: JSON.stringify({ status: "cancelled" }) }); toast("Cancelled", "success"); await loadShiftSwaps(); }
  catch (err) { toast(err.message, "error"); }
};

/* =========================================================
   TASKS
========================================================= */
async function loadTasks() {
  const status = q("task-status-filter")?.value || "";
  const params = status ? `?status_filter=${status}` : "";
  const tasks = await api(`/api/tasks${params}`);
  renderTasks(tasks);
}

function renderTasks(tasks) {
  if (!tasks.length) {
    q("tasks-table").innerHTML = emptyState("📋", "No tasks", "Create the first task.");
    return;
  }
  const isAdmin = state.me && state.me.role === "admin";
  const rows = tasks.map(t => {
    const prioColors = { low: "#94a3b8", normal: "#3b82f6", high: "#f59e0b", urgent: "#ef4444" };
    const statusIcons = { todo: "⬜", in_progress: "🔄", done: "✅" };
    return `<tr>
      <td>${statusIcons[t.status] || ""} <b>${esc(t.title)}</b></td>
      <td class="muted">${esc(t.assignee_name || "—")}</td>
      <td><span style="color:${prioColors[t.priority]};font-weight:600;">${t.priority}</span></td>
      <td>${t.due_date ? fmtDate(t.due_date) : "—"}</td>
      <td><span class="badge ${t.status === "done" ? "active" : t.status === "in_progress" ? "half_day" : "user"}">${t.status.replace("_", " ")}</span></td>
      <td><div class="action-cell">
        ${t.status !== "done" ? `<button class="btn sm" onclick="updateTaskStatus(${t.id}, '${t.status === "todo" ? "in_progress" : "done"}')">${t.status === "todo" ? "Start" : "Done"}</button>` : ""}
        ${isAdmin ? `<button class="btn sm danger" onclick="deleteTask(${t.id})">Del</button>` : ""}
      </div></td>
    </tr>`;
  }).join("");
  q("tasks-table").innerHTML = `<table>
    <thead><tr><th>Title</th><th>Assignee</th><th>Priority</th><th>Due</th><th>Status</th><th></th></tr></thead>
    <tbody>${rows}</tbody></table>`;
}

function openTaskModal() {
  const peopleOpts = (state.people || []).map(p => `<option value="${p.id}">${esc(p.full_name)}</option>`).join("");
  openModal("New Task", `<form id="task-form">
    <div class="form-row"><label>Title *</label><input name="title" required /></div>
    <div class="form-row"><label>Description</label><textarea name="description" rows="3"></textarea></div>
    <div class="form-grid">
      <div class="form-row"><label>Assign To</label><select name="assigned_to"><option value="">— Unassigned —</option>${peopleOpts}</select></div>
      <div class="form-row"><label>Priority</label><select name="priority"><option value="low">Low</option><option value="normal" selected>Normal</option><option value="high">High</option><option value="urgent">Urgent</option></select></div>
    </div>
    <div class="form-row"><label>Due Date</label><input type="date" name="due_date" /></div>
    <div class="form-actions">
      <button type="button" class="btn secondary" onclick="closeModal()">Cancel</button>
      <button type="submit" class="btn">Create</button>
    </div>
  </form>`);
  q("task-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    try {
      await api("/api/tasks", { method: "POST", body: JSON.stringify({
        title: fd.get("title"), description: fd.get("description") || null,
        assigned_to: fd.get("assigned_to") ? Number(fd.get("assigned_to")) : null,
        priority: fd.get("priority"), due_date: fd.get("due_date") || null,
      }) });
      toast("Task created", "success"); closeModal(); await loadTasks();
    } catch (err) { toast(err.message, "error"); }
  });
}

window.updateTaskStatus = async (id, newStatus) => {
  try { await api(`/api/tasks/${id}`, { method: "PATCH", body: JSON.stringify({ status: newStatus }) }); toast("Updated", "success"); await loadTasks(); }
  catch (err) { toast(err.message, "error"); }
};

window.deleteTask = async (id) => {
  const ok = await confirm("Delete Task", "Delete this task?");
  if (ok) {
    try { await api(`/api/tasks/${id}`, { method: "DELETE" }); toast("Deleted", "success"); await loadTasks(); }
    catch (err) { toast(err.message, "error"); }
  }
};

/* =========================================================
   CHAT
========================================================= */
let chatPollInterval = null;

async function loadChat() {
  const channel = q("chat-channel")?.value || "general";
  const messages = await api(`/api/chat?channel=${channel}&limit=100`);
  renderChat(messages);
  if (chatPollInterval) clearInterval(chatPollInterval);
  chatPollInterval = setInterval(async () => {
    if (document.getElementById("view-chat")?.classList.contains("hidden")) return;
    const msgs = await api(`/api/chat?channel=${q("chat-channel").value}&limit=100`);
    renderChat(msgs);
  }, 5000);
}

function renderChat(messages) {
  const container = q("chat-messages");
  if (!messages.length) {
    container.innerHTML = `<div class="empty" style="margin:auto;">No messages yet. Say hello!</div>`;
    return;
  }
  const myId = state.me?.person_id;
  container.innerHTML = messages.map(m => {
    const isMe = m.sender_id === myId;
    return `<div style="display:flex;gap:8px;${isMe ? "flex-direction:row-reverse;" : ""}">
      <div style="width:32px;height:32px;border-radius:50%;background:${isMe ? "var(--accent)" : "#6366f1"};color:#fff;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;flex-shrink:0;">${(m.sender_name || "?").charAt(0).toUpperCase()}</div>
      <div style="max-width:70%;${isMe ? "text-align:right;" : ""}">
        <div style="font-size:11px;color:var(--muted);margin-bottom:2px;">${esc(m.sender_name || "Unknown")} · ${new Date(m.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</div>
        <div style="padding:8px 12px;border-radius:12px;background:${isMe ? "var(--accent)" : "var(--card)"};color:${isMe ? "#fff" : "var(--text)"};border:1px solid var(--border);word-break:break-word;">${esc(m.content)}</div>
      </div>
    </div>`;
  }).join("");
  container.scrollTop = container.scrollHeight;
}

async function sendChatMessage() {
  const input = q("chat-input");
  const content = input?.value?.trim();
  if (!content) return;
  const channel = q("chat-channel")?.value || "general";
  try {
    await api("/api/chat", { method: "POST", body: JSON.stringify({ content, channel }) });
    input.value = "";
    const msgs = await api(`/api/chat?channel=${channel}&limit=100`);
    renderChat(msgs);
  } catch (err) { toast(err.message, "error"); }
}

/* =========================================================
   MEETINGS
========================================================= */
async function loadMeetings() {
  const meetings = await api("/api/meetings");
  renderMeetings(meetings);
}

function renderMeetings(meetings) {
  if (!meetings.length) {
    q("meetings-table").innerHTML = emptyState("📅", "No meetings", "Schedule the first meeting.");
    return;
  }
  const rows = meetings.map(m => {
    const attNames = (m.attendees || []).map(a => a.name).join(", ") || "—";
    const attStatus = (m.attendees || []).map(a => `<span class="badge ${a.status}" style="font-size:10px;">${(a.name || "?").split(" ")[0]}: ${a.status}</span>`).join(" ");
    const dt = new Date(m.scheduled_at);
    return `<tr>
      <td><b>${esc(m.title)}</b></td>
      <td>${dt.toLocaleDateString([], { month: "short", day: "numeric" })} ${dt.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</td>
      <td>${m.duration_minutes}m</td>
      <td class="muted">${esc(m.room || "—")}</td>
      <td>${attStatus}</td>
      <td><div class="action-cell">
        <button class="btn sm secondary" onclick="deleteMeeting(${m.id})">Del</button>
      </div></td>
    </tr>`;
  }).join("");
  q("meetings-table").innerHTML = `<table>
    <thead><tr><th>Title</th><th>Date & Time</th><th>Duration</th><th>Room</th><th>Attendees</th><th></th></tr></thead>
    <tbody>${rows}</tbody></table>`;
}

async function openMeetingModal() {
  await ensurePeople();
  const peopleOpts = (state.people || []).map(p => `<label style="display:flex;gap:6px;align-items:center;padding:4px 0;"><input type="checkbox" name="attendees" value="${p.id}" /> ${esc(p.full_name)}</label>`).join("");
  openModal("New Meeting", `<form id="meeting-form">
    <div class="form-row"><label>Title *</label><input name="title" required /></div>
    <div class="form-row"><label>Description</label><textarea name="description" rows="2"></textarea></div>
    <div class="form-grid">
      <div class="form-row"><label>Date & Time *</label><input type="datetime-local" name="scheduled_at" required /></div>
      <div class="form-row"><label>Duration (min)</label><input type="number" name="duration_minutes" value="30" min="5" max="480" /></div>
    </div>
    <div class="form-row"><label>Room</label><input name="room" /></div>
    <div class="form-row"><label>Attendees</label><div style="max-height:150px;overflow-y:auto;border:1px solid var(--border);border-radius:6px;padding:8px;">${peopleOpts || "<span class='muted'>No people</span>"}</div></div>
    <div class="form-actions">
      <button type="button" class="btn secondary" onclick="closeModal()">Cancel</button>
      <button type="submit" class="btn">Schedule</button>
    </div>
  </form>`);
  q("meeting-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const attendeeIds = Array.from(q("meeting-form").querySelectorAll('input[name="attendees"]:checked')).map(cb => Number(cb.value));
    try {
      await api("/api/meetings", { method: "POST", body: JSON.stringify({
        title: fd.get("title"), description: fd.get("description") || null,
        scheduled_at: new Date(fd.get("scheduled_at")).toISOString(),
        duration_minutes: Number(fd.get("duration_minutes")),
        room: fd.get("room") || null,
        attendee_ids: attendeeIds,
      }) });
      toast("Meeting scheduled", "success"); closeModal(); await loadMeetings();
    } catch (err) { toast(err.message, "error"); }
  });
}

window.deleteMeeting = async (id) => {
  const ok = await confirm("Delete Meeting", "Delete this meeting?");
  if (ok) {
    try { await api(`/api/meetings/${id}`, { method: "DELETE" }); toast("Deleted", "success"); await loadMeetings(); }
    catch (err) { toast(err.message, "error"); }
  }
};

/* =========================================================
   ACTIVITY LOGS
========================================================= */
async function loadActivityLogs() {
  const entity = q("log-entity-filter")?.value || "";
  const action = q("log-action-filter")?.value || "";
  const params = new URLSearchParams({ limit: "100" });
  if (entity) params.set("entity", entity);
  if (action) params.set("action", action);
  const logs = await api(`/api/activity-logs?${params}`);
  renderActivityLogs(logs);
}

function renderActivityLogs(logs) {
  if (!logs.length) {
    q("logs-table").innerHTML = emptyState("📋", "No activity logs", "No changes recorded yet.");
    return;
  }
  const actionColors = { create: "#22c55e", update: "#3b82f6", delete: "#ef4444" };
  const rows = logs.map(l => {
    let details = "—";
    if (l.details) {
      try {
        const obj = typeof l.details === "string" ? JSON.parse(l.details) : l.details;
        details = Object.entries(obj).map(([k, v]) => `<span class="mono">${esc(k)}</span>: ${esc(String(v).slice(0, 40))}`).join(", ");
      } catch { details = esc(String(l.details).slice(0, 60)); }
    }
    return `<tr>
      <td class="muted" style="white-space:nowrap;">${new Date(l.created_at).toLocaleString()}</td>
      <td><span class="badge" style="background:${actionColors[l.action] || "#666"};color:#fff;">${l.action}</span></td>
      <td><b>${esc(l.entity)}</b>${l.entity_id ? ` #${l.entity_id}` : ""}</td>
      <td class="muted">${esc(l.username || "system")}</td>
      <td style="max-width:300px;overflow:hidden;text-overflow:ellipsis;">${details}</td>
      <td class="muted">${esc(l.ip_address || "—")}</td>
    </tr>`;
  }).join("");
  q("logs-table").innerHTML = `<table>
    <thead><tr><th>Time</th><th>Action</th><th>Entity</th><th>User</th><th>Details</th><th>IP</th></tr></thead>
    <tbody>${rows}</tbody></table>`;
}

window.saveSetting = async (key) => {
  const input = document.querySelector(`.setting-input[data-key="${key}"]`);
  if (!input) return;
  try {
    await api(`/api/settings/${key}`, { method: "PATCH", body: JSON.stringify({ value: input.value }) });
    toast("Setting saved", "success");
  } catch (err) { toast(err.message, "error"); }
};

/* =========================================================
   PROFILE
========================================================= */
async function loadProfile() {
  const [profile, stats] = await Promise.all([
    api("/api/profile"),
    api("/api/profile/stats"),
  ]);

  const user = profile.user;
  const person = profile.person;

  setText("profile-name", user.full_name);
  setText("profile-role", user.role === "admin" ? "Administrator" : "User");
  setText("profile-username", user.role === "admin" ? "Admin" : user.username);
  setText("profile-email", user.email || "—");
  setText("profile-status", user.is_active ? "Active" : "Inactive");
  setText("profile-joined", fmtDate(user.created_at));

  const personFields = document.querySelectorAll(".profile-person-field");
  if (person) {
    setText("profile-department", person.group_name || "—");
    setText("profile-person-name", person.full_name);
    personFields.forEach((el) => (el.style.display = ""));
  } else {
    personFields.forEach((el) => (el.style.display = "none"));
  }

  const avatar = q("profile-avatar");
  if (avatar) avatar.textContent = user.full_name.charAt(0).toUpperCase();

  setText("profile-streak", stats.streak);
  setText("profile-present", stats.total_present);
  setText("profile-hours", stats.total_hours + "h");
  setText("profile-rate", Math.round(stats.attendance_rate * 100) + "%");
}

function openEditProfileModal() {
  const user = state.me;
  if (!user) return;
  openModal(
    "Edit Profile",
    `<form id="edit-profile-form">
      <div class="form-row">
        <label>Full Name</label>
        <input type="text" name="full_name" value="${esc(user.full_name || "")}" required />
      </div>
      <div class="form-row">
        <label>Email</label>
        <input type="email" name="email" value="${esc(user.email || "")}" />
      </div>
      <div class="form-actions">
        <button type="button" class="btn secondary" onclick="closeModal()">Cancel</button>
        <button type="submit" class="btn">Save Changes</button>
      </div>
    </form>`
  );
  q("edit-profile-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    try {
      const updated = await api("/api/profile", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          full_name: fd.get("full_name"),
          email: fd.get("email"),
        }),
      });
      state.me = updated;
      setText("me-name", updated.full_name);
      setText("me-role", updated.role === "admin" ? "Administrator" : "User");
      setText("profile-name", updated.full_name);
      setText("profile-email", updated.email || "—");
      const avatar = q("me-avatar");
      if (avatar) avatar.textContent = updated.full_name.charAt(0).toUpperCase();
      const pAvatar = q("profile-avatar");
      if (pAvatar) pAvatar.textContent = updated.full_name.charAt(0).toUpperCase();
      toast("Profile updated", "success");
      closeModal();
    } catch (err) {
      toast(err.message, "error");
    }
  });
}

function openChangePasswordModal() {
  openModal(
    "Change Password",
    `<form id="change-pw-form">
      <div class="form-row">
        <label>Current Password</label>
        <input type="password" name="current_password" required />
      </div>
      <div class="form-row">
        <label>New Password</label>
        <input type="password" name="new_password" required minlength="6" />
      </div>
      <div class="form-row">
        <label>Confirm New Password</label>
        <input type="password" name="confirm_password" required minlength="6" />
      </div>
      <div class="form-actions">
        <button type="button" class="btn secondary" onclick="closeModal()">Cancel</button>
        <button type="submit" class="btn">Update Password</button>
      </div>
    </form>`
  );
  q("change-pw-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const newPw = fd.get("new_password");
    const confirmPw = fd.get("confirm_password");
    if (newPw !== confirmPw) {
      toast("Passwords do not match", "error");
      return;
    }
    try {
      await api("/api/auth/change-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          current_password: fd.get("current_password"),
          new_password: newPw,
        }),
      });
      toast("Password updated", "success");
      closeModal();
    } catch (err) {
      toast(err.message, "error");
    }
  });
}

/* =========================================================
   CHARTS
========================================================= */
let chartTrend = null;
let chartStatus = null;
let chartWeekly = null;

function getChartColors() {
  const isDark = document.documentElement.getAttribute("data-theme") === "dark";
  return {
    text: isDark ? "#f1f5f9" : "#0f172a",
    grid: isDark ? "#334155" : "#e2e8f0",
    present: "#10b981",
    absent: "#ef4444",
    halfDay: "#f59e0b",
    holiday: "#6366f1",
  };
}

async function loadCharts() {
  const colors = getChartColors();
  
  // Fetch data for charts
  const from30 = isoOffset(29);
  const records = await api(`/api/attendance?date_from=${from30}&date_to=${todayISO()}&limit=500`);
  const stats = await api("/api/attendance/stats");
  
  renderTrendChart(records, colors);
  renderStatusChart(stats, colors);
  renderWeeklyChart(records, colors);
}

function renderTrendChart(records, colors) {
  const ctx = document.getElementById("chart-trend");
  if (!ctx) return;
  
  // Group by date
  const byDate = {};
  records.forEach(r => {
    if (!byDate[r.date]) byDate[r.date] = { present: 0, absent: 0, half: 0 };
    if (r.status === "present") byDate[r.date].present++;
    else if (r.status === "absent") byDate[r.date].absent++;
    else if (r.status === "half_day") byDate[r.date].half++;
  });
  
  const dates = Object.keys(byDate).sort();
  const labels = dates.map(d => {
    const dt = new Date(d + "T00:00:00");
    return dt.toLocaleDateString([], { month: "short", day: "numeric" });
  });
  
  if (chartTrend) chartTrend.destroy();
  chartTrend = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Present",
          data: dates.map(d => byDate[d].present),
          borderColor: colors.present,
          backgroundColor: colors.present + "20",
          fill: true,
          tension: 0.4,
          pointRadius: 3,
          pointHoverRadius: 6,
        },
        {
          label: "Absent",
          data: dates.map(d => byDate[d].absent),
          borderColor: colors.absent,
          backgroundColor: colors.absent + "20",
          fill: true,
          tension: 0.4,
          pointRadius: 3,
          pointHoverRadius: 6,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: "top", labels: { color: colors.text, usePointStyle: true, padding: 16 } },
      },
      scales: {
        x: { grid: { color: colors.grid }, ticks: { color: colors.text, maxTicksLimit: 10 } },
        y: { grid: { color: colors.grid }, ticks: { color: colors.text, stepSize: 1 }, beginAtZero: true },
      },
      interaction: { mode: "index", intersect: false },
    },
  });
}

function renderStatusChart(stats, colors) {
  const ctx = document.getElementById("chart-status");
  if (!ctx) return;
  
  if (chartStatus) chartStatus.destroy();
  chartStatus = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: ["Present", "Absent", "Late"],
      datasets: [{
        data: [stats.total_present_month, stats.total_absent_month, stats.late_count],
        backgroundColor: [colors.present, colors.absent, colors.halfDay],
        borderWidth: 0,
        hoverOffset: 8,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "65%",
      plugins: {
        legend: { position: "bottom", labels: { color: colors.text, usePointStyle: true, padding: 16 } },
      },
    },
  });
}

function renderWeeklyChart(records, colors) {
  const ctx = document.getElementById("chart-weekly");
  if (!ctx) return;
  
  // Group by week
  const weeks = {};
  records.forEach(r => {
    const d = new Date(r.date + "T00:00:00");
    const weekStart = new Date(d);
    weekStart.setDate(d.getDate() - d.getDay());
    const key = weekStart.toISOString().slice(0, 10);
    if (!weeks[key]) weeks[key] = { present: 0, absent: 0, half: 0 };
    if (r.status === "present") weeks[key].present++;
    else if (r.status === "absent") weeks[key].absent++;
    else if (r.status === "half_day") weeks[key].half++;
  });
  
  const weekKeys = Object.keys(weeks).sort().slice(-4);
  const labels = weekKeys.map(k => {
    const dt = new Date(k + "T00:00:00");
    return "Week of " + dt.toLocaleDateString([], { month: "short", day: "numeric" });
  });
  
  if (chartWeekly) chartWeekly.destroy();
  chartWeekly = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: "Present",
          data: weekKeys.map(k => weeks[k].present),
          backgroundColor: colors.present,
          borderRadius: 6,
        },
        {
          label: "Absent",
          data: weekKeys.map(k => weeks[k].absent),
          backgroundColor: colors.absent,
          borderRadius: 6,
        },
        {
          label: "Half Day",
          data: weekKeys.map(k => weeks[k].half),
          backgroundColor: colors.halfDay,
          borderRadius: 6,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: "top", labels: { color: colors.text, usePointStyle: true, padding: 16 } },
      },
      scales: {
        x: { grid: { display: false }, ticks: { color: colors.text } },
        y: { grid: { color: colors.grid }, ticks: { color: colors.text, stepSize: 1 }, beginAtZero: true },
      },
    },
  });
}

function renderRecordsTable(records, admin) {
  if (!records.length) return emptyState("📋", "No records found", "Try adjusting your filters or date range.");
  const rows = records
    .map((r) => {
      const personCell = admin
        ? `<td>${esc(r.person_name || "")}</td><td class="muted">${esc(r.group_name || "—")}</td>`
        : "";
      const actions = admin
        ? `<td><div class="action-cell">
             <button class="btn sm secondary" onclick="editRecord(${r.id})">Edit</button>
             <button class="btn sm danger" onclick="deleteRecord(${r.id})">Del</button>
           </div></td>`
        : "";
      return `<tr>
        <td class="mono">${fmtDate(r.date)}</td>
        ${personCell}
        <td class="mono">${fmtTime(r.check_in)}</td>
        <td class="mono">${fmtTime(r.check_out)}</td>
        <td class="mono">${fmtDur(r.duration_minutes)}</td>
        <td>${badge(r.status)}</td>
        ${actions}
      </tr>`;
    })
    .join("");
  const head = admin
    ? `<thead><tr><th>Date</th><th>Person</th><th>Group</th><th>In</th><th>Out</th><th>Duration</th><th>Status</th><th></th></tr></thead>`
    : `<thead><tr><th>Date</th><th>In</th><th>Out</th><th>Duration</th><th>Status</th></tr></thead>`;
  return `<table>${head}<tbody>${rows}</tbody></table>`;
}

/* ---------- Hero check-in / out ---------- */
async function checkIn() {
  try {
    const rec = await api("/api/attendance/check-in", { method: "POST", loadingBtn: "btn-checkin" });
    toast(`Checked in at ${fmtTime(rec.check_in)}`, "success");
    renderHero(rec);
    await loadWeekStrip();
    await loadMyRecent();
  } catch (e) {
    toast(e.message, "error");
  }
}

async function checkOut() {
  try {
    const rec = await api("/api/attendance/check-out", { method: "POST", loadingBtn: "btn-checkout" });
    toast(`Checked out at ${fmtTime(rec.check_out)}`, "success");
    renderHero(rec);
    await loadWeekStrip();
    await loadMyRecent();
  } catch (e) {
    toast(e.message, "error");
  }
}

/* =========================================================
   RECORDS (admin)
========================================================= */
async function loadRecords() {
  const isAdmin = state.me && state.me.role === "admin";
  if (isAdmin) await ensurePeople();
  const from = isoOffset(29);
  const to = todayISO();
  q("rec-from").value = from;
  q("rec-to").value = to;
  if (isAdmin) fillPersonSelect("rec-person");
  await applyRecordFilters();
}

function recordFiltersQuery() {
  const p = new URLSearchParams();
  const from = q("rec-from").value, to = q("rec-to").value;
  const person = q("rec-person")?.value;
  const status = q("rec-status").value;
  const search = q("rec-search")?.value?.trim();
  if (from) p.set("date_from", from);
  if (to) p.set("date_to", to);
  if (person) p.set("person_id", person);
  if (status) p.set("status", status);
  if (search) p.set("search", search);
  return p.toString();
}

async function applyRecordFilters() {
  const qs = recordFiltersQuery();
  const records = await api(`/api/attendance?${qs}&limit=500`);
  
  const search = q("rec-search")?.value?.trim().toLowerCase();
  let filtered = records;
  if (search) {
    filtered = records.filter(r => 
      (r.person_name || "").toLowerCase().includes(search) ||
      (r.group_name || "").toLowerCase().includes(search)
    );
  }
  
  const isAdmin = state.me && state.me.role === "admin";
  q("records-table").innerHTML = renderRecordsTable(filtered, isAdmin);
  if (isAdmin) ensureManualBtn();
}

function ensureManualBtn() {
  let btn = q("btn-manual-record");
  if (!btn) {
    const card = q("records-table").closest(".card");
    const hdr = document.createElement("div");
    hdr.style.cssText = "display:flex;justify-content:flex-end;margin-bottom:12px;";
    hdr.innerHTML = `<button class="btn sm" id="btn-manual-record">+ Add record</button>`;
    card.prepend(hdr);
    btn = q("btn-manual-record");
    btn.addEventListener("click", () => openManualRecordModal());
  }
}

function openManualRecordModal() {
  const personOpts = state.people.map((p) => `<option value="${p.id}">${esc(p.full_name)}</option>`).join("");
  openModal(
    "Add attendance record",
    `<form id="manual-form">
      <div class="form-row"><label>Person</label><select name="person_id" required>${personOpts}</select></div>
      <div class="form-row"><label>Date</label><input type="date" name="date" value="${todayISO()}" required /></div>
      <div class="form-grid">
        <div class="form-row"><label>Check-in (optional)</label><input type="datetime-local" name="check_in" /></div>
        <div class="form-row"><label>Check-out (optional)</label><input type="datetime-local" name="check_out" /></div>
      </div>
      <div class="form-row"><label>Status</label>
        <select name="status">
          <option value="present">Present</option>
          <option value="absent">Absent</option>
          <option value="half_day">Half day</option>
          <option value="holiday">Holiday</option>
        </select>
      </div>
      <div class="form-row"><label>Note</label><input type="text" name="note" placeholder="Optional" /></div>
      <div class="form-actions">
        <button type="button" class="btn secondary" onclick="closeModal()">Cancel</button>
        <button type="submit" class="btn">Save</button>
      </div>
    </form>`
  );
  q("manual-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const body = {
      person_id: Number(fd.get("person_id")),
      date: fd.get("date"),
      status: fd.get("status"),
      note: fd.get("note") || null,
    };
    if (fd.get("check_in")) body.check_in = new Date(fd.get("check_in")).toISOString();
    if (fd.get("check_out")) body.check_out = new Date(fd.get("check_out")).toISOString();
    try {
      await api("/api/attendance/manual", { method: "POST", body: JSON.stringify(body) });
      toast("Record created", "success");
      closeModal();
      await applyRecordFilters();
    } catch (err) {
      toast(err.message, "error");
    }
  });
}

async function editRecord(id) {
  // fetch single record via filters — simplest: fetch records and find
  const qs = recordFiltersQuery();
  const records = await api(`/api/attendance?${qs}&limit=1000`);
  const rec = records.find((r) => r.id === id);
  if (!rec) return;
  const toLocal = (iso) => (iso ? new Date(iso).toISOString().slice(0, 16) : "");
  openModal(
    "Edit record",
    `<form id="edit-form">
      <div class="form-row"><label>Date</label><input type="date" value="${rec.date}" disabled class="muted" /></div>
      <div class="form-grid">
        <div class="form-row"><label>Check-in</label><input type="datetime-local" name="check_in" value="${toLocal(rec.check_in)}" /></div>
        <div class="form-row"><label>Check-out</label><input type="datetime-local" name="check_out" value="${toLocal(rec.check_out)}" /></div>
      </div>
      <div class="form-row"><label>Status</label>
        <select name="status">
          ${["present", "absent", "half_day", "holiday"].map((s) => `<option value="${s}" ${s === rec.status ? "selected" : ""}>${STATUS_LABELS[s]}</option>`).join("")}
        </select>
      </div>
      <div class="form-row"><label>Note</label><input type="text" name="note" value="${esc(rec.note || "")}" /></div>
      <div class="form-actions">
        <button type="button" class="btn secondary" onclick="closeModal()">Cancel</button>
        <button type="submit" class="btn">Save changes</button>
      </div>
    </form>`
  );
  q("edit-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const body = { status: fd.get("status"), note: fd.get("note") || null };
    if (fd.get("check_in")) body.check_in = new Date(fd.get("check_in")).toISOString();
    else body.check_in = null;
    if (fd.get("check_out")) body.check_out = new Date(fd.get("check_out")).toISOString();
    else body.check_out = null;
    try {
      await api(`/api/attendance/${id}`, { method: "PATCH", body: JSON.stringify(body) });
      toast("Record updated", "success");
      closeModal();
      await applyRecordFilters();
    } catch (err) {
      toast(err.message, "error");
    }
  });
}

async function deleteRecord(id) {
  const ok = await confirm("Delete record", "Delete this attendance record? This cannot be undone.");
  if (ok) {
    try {
      await api(`/api/attendance/${id}`, { method: "DELETE" });
      toast("Record deleted", "success");
      await applyRecordFilters();
    } catch (err) {
      toast(err.message, "error");
    }
  }
}

/* =========================================================
   PEOPLE (admin)
========================================================= */
async function ensurePeople() {
  state.people = await api("/api/people?limit=500&include_inactive=true");
  state.peopleById = {};
  state.people.forEach((p) => (state.peopleById[p.id] = p));
}

async function loadPeople() {
  await ensurePeople();
  await loadGroups();
  renderPeople();
}

function openImportCsvModal() {
  openModal(
    "Import People from CSV",
    `<form id="import-form">
      <div class="form-row">
        <label>CSV File *</label>
        <input type="file" name="file" accept=".csv" required id="csv-file-input" />
        <div class="muted" style="margin-top:6px;font-size:12px;">Columns: full_name, email (optional), group_name (optional)</div>
      </div>
      <div id="csv-preview" style="display:none;">
        <div style="margin:12px 0 8px;font-weight:600;font-size:13px;">Preview (first 5 rows)</div>
        <div id="csv-preview-table" style="max-height:200px;overflow:auto;border:1px solid var(--border);border-radius:8px;"></div>
        <div id="csv-validation-msg" style="margin-top:8px;font-size:12px;"></div>
      </div>
      <div class="form-actions">
        <button type="button" class="btn secondary" onclick="closeModal()">Cancel</button>
        <button type="submit" class="btn" id="csv-import-btn">Import</button>
      </div>
    </form>`
  );

  // CSV preview on file select
  const fileInput = document.getElementById("csv-file-input");
  if (fileInput) {
    fileInput.addEventListener("change", () => {
      const file = fileInput.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = (e) => {
        const text = e.target.result;
        const lines = text.trim().split("\n");
        if (lines.length < 1) return;

        const headers = lines[0].split(",").map(h => h.trim().toLowerCase());
        const hasName = headers.includes("full_name") || headers.includes("name");
        const rows = lines.slice(1, 6).map(l => l.split(",").map(c => c.trim()));

        let html = '<table style="width:100%;border-collapse:collapse;font-size:12px;">';
        html += '<thead><tr>' + headers.map(h => `<th style="padding:6px 8px;text-align:left;border-bottom:1px solid var(--border);background:var(--bg);">${esc(h)}</th>`).join('') + '</tr></thead><tbody>';
        rows.forEach(r => {
          html += '<tr>' + r.map(c => `<td style="padding:6px 8px;border-bottom:1px solid var(--border);">${esc(c)}</td>`).join('') + '</tr>';
        });
        html += '</tbody></table>';
        if (lines.length > 6) html += `<div style="padding:6px 8px;font-size:11px;color:var(--muted);">... and ${lines.length - 6} more rows</div>`;

        document.getElementById("csv-preview-table").innerHTML = html;
        document.getElementById("csv-preview").style.display = "block";

        // Validation message
        const msgEl = document.getElementById("csv-validation-msg");
        const totalRows = lines.length - 1;
        if (!hasName) {
          msgEl.innerHTML = '<span style="color:var(--danger);">⚠ Missing "full_name" column — import may fail</span>';
        } else {
          msgEl.innerHTML = `<span style="color:var(--success);">✓ ${totalRows} rows ready to import</span>`;
        }
      };
      reader.readAsText(file);
    });
  }

  q("import-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const fileInput = e.target.querySelector('input[name="file"]');
    if (!fileInput.files.length) {
      toast("Select a CSV file", "error");
      return;
    }
    const fd = new FormData();
    fd.append("file", fileInput.files[0]);
    try {
      const token = localStorage.getItem("token");
      const res = await fetch("/api/people/import", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: fd,
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Import failed");
      }
      const result = await res.json();
      let msg = `Imported ${result.created} people`;
      if (result.skipped) msg += `, skipped ${result.skipped}`;
      if (result.errors.length) msg += `. Errors: ${result.errors.join("; ")}`;
      toast(msg, result.errors.length ? "error" : "success");
      closeModal();
      await loadPeople();
    } catch (err) {
      toast(err.message, "error");
    }
  });
}

function renderPeople() {
  if (!state.people.length) {
    q("people-table").innerHTML = `<div class="empty">No people yet — add the first one.</div>`;
    return;
  }
  const rows = state.people
    .map((p) => {
      const linked = (state.users.find((u) => u.person_id === p.id) || {}).username || "—";
      return `<tr>
        <td><b>${esc(p.full_name)}</b></td>
        <td>${esc(p.email || "—")}</td>
        <td class="muted">${esc(p.group_name || "—")}</td>
        <td>${p.is_active ? `<span class="badge active">Active</span>` : `<span class="badge inactive">Inactive</span>`}</td>
        <td class="muted">${esc(linked)}</td>
        <td><div class="action-cell">
          <button class="btn sm secondary" onclick="editPerson(${p.id})">Edit</button>
          <button class="btn sm danger" onclick="deletePerson(${p.id})">Del</button>
        </div></td>
      </tr>`;
    })
    .join("");
  q("people-table").innerHTML = `<table>
    <thead><tr><th>Name</th><th>Email</th><th>Group</th><th>Status</th><th>Linked user</th><th></th></tr></thead>
    <tbody>${rows}</tbody></table>`;
}

function personForm(person) {
  return `
    <form id="person-form">
      <div class="form-row"><label>Full name *</label><input name="full_name" required maxlength="255" value="${esc(person?.full_name || "")}" /></div>
      <div class="form-grid">
        <div class="form-row"><label>Email</label><input type="email" name="email" value="${esc(person?.email || "")}" /></div>
        <div class="form-row"><label>Group (dept/class)</label><input name="group_name" list="group-list" value="${esc(person?.group_name || "")}" />
          <datalist id="group-list">${state.groups.map((g) => `<option value="${esc(g)}">`).join("")}</datalist>
        </div>
      </div>
      <div class="form-row"><label>Status</label>
        <select name="is_active">
          <option value="true" ${person?.is_active === false ? "" : "selected"}>Active</option>
          <option value="false" ${person?.is_active === false ? "selected" : ""}>Inactive</option>
        </select>
      </div>
      <div class="form-actions">
        <button type="button" class="btn secondary" onclick="closeModal()">Cancel</button>
        <button type="submit" class="btn">${person ? "Save changes" : "Add person"}</button>
      </div>
    </form>`;
}

function openPersonModal(person) {
  openModal(person ? "Edit person" : "Add person", personForm(person));
  q("person-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const body = {
      full_name: fd.get("full_name").trim(),
      email: fd.get("email").trim() || null,
      group_name: fd.get("group_name").trim() || null,
      is_active: fd.get("is_active") === "true",
    };
    try {
      if (person) {
        await api(`/api/people/${person.id}`, { method: "PATCH", body: JSON.stringify(body) });
        toast("Person updated", "success");
      } else {
        await api("/api/people", { method: "POST", body: JSON.stringify(body) });
        toast("Person added", "success");
      }
      closeModal();
      await loadPeople();
    } catch (err) {
      toast(err.message, "error");
    }
  });
}

window.editPerson = (id) => openPersonModal(state.peopleById[id]);

window.deletePerson = async (id) => {
  const p = state.peopleById[id];
  const ok = await confirm("Delete person", `Delete <b>${esc(p.full_name)}</b> and all their attendance records?`);
  if (ok) {
    try {
      await api(`/api/people/${id}`, { method: "DELETE" });
      toast("Person deleted", "success");
      await loadPeople();
    } catch (err) {
      toast(err.message, "error");
    }
  }
};

async function loadGroups() {
  try {
    state.groups = await api("/api/people/groups");
  } catch (_) {
    state.groups = [];
  }
}

function fillPersonSelect(id) {
  const sel = q(id);
  if (!sel) return;
  sel.innerHTML = `<option value="">All people</option>` + state.people
    .filter((p) => p.is_active)
    .map((p) => `<option value="${p.id}">${esc(p.full_name)}</option>`)
    .join("");
}

/* =========================================================
   USERS (admin)
========================================================= */
async function loadUsers() {
  state.users = await api("/api/users");
  await ensurePeople();
  renderUsers();
}

function renderUsers() {
  if (!state.users.length) {
    q("users-table").innerHTML = `<div class="empty">No user accounts.</div>`;
    return;
  }
  const rows = state.users
    .map((u) => {
      const personName = u.person_id && state.peopleById[u.person_id] ? state.peopleById[u.person_id].full_name : "—";
      return `<tr>
        <td><b>${esc(u.username)}</b></td>
        <td>${esc(u.full_name)}</td>
        <td class="muted">${esc(u.email || "—")}</td>
        <td><span class="badge ${u.role}">${u.role}</span></td>
        <td>${u.is_active ? `<span class="badge active">Active</span>` : `<span class="badge inactive">Inactive</span>`}</td>
        <td class="muted">${esc(personName)}</td>
        <td class="muted">${fmtDate(u.created_at)}</td>
        <td><div class="action-cell">
          <button class="btn sm secondary" onclick="editUser(${u.id})">Edit</button>
          <button class="btn sm danger" onclick="deleteUser(${u.id})">Del</button>
        </div></td>
      </tr>`;
    })
    .join("");
  q("users-table").innerHTML = `<table>
    <thead><tr><th>Username</th><th>Full name</th><th>Email</th><th>Role</th><th>Status</th><th>Linked person</th><th>Joined</th><th></th></tr></thead>
    <tbody>${rows}</tbody></table>`;
}

function userForm(user) {
  const personOpts = `<option value="">— none —</option>` + state.people
    .filter((p) => p.is_active)
    .map((p) => `<option value="${p.id}" ${user?.person_id === p.id ? "selected" : ""}>${esc(p.full_name)}</option>`)
    .join("");
  return `
    <form id="user-form">
      <div class="form-grid">
        <div class="form-row"><label>Username *</label><input name="username" required minlength="3" value="${esc(user?.username || "")}" ${user ? "disabled" : ""} /></div>
        <div class="form-row"><label>Full name *</label><input name="full_name" required value="${esc(user?.full_name || "")}" /></div>
      </div>
      <div class="form-grid">
        <div class="form-row"><label>Email</label><input type="email" name="email" value="${esc(user?.email || "")}" /></div>
        <div class="form-row"><label>Password ${user ? "(blank = keep)" : "*"}</label><input type="password" name="password" ${user ? "" : "required minlength=6"} /></div>
      </div>
      <div class="form-grid">
        <div class="form-row"><label>Role</label>
          <select name="role">
            <option value="user" ${user?.role === "user" ? "selected" : ""}>User</option>
            <option value="admin" ${user?.role === "admin" ? "selected" : ""}>Admin</option>
          </select>
        </div>
        <div class="form-row"><label>Linked person</label><select name="person_id">${personOpts}</select></div>
      </div>
      <div class="form-row"><label>Status</label>
        <select name="is_active">
          <option value="true" ${user?.is_active === false ? "" : "selected"}>Active</option>
          <option value="false" ${user?.is_active === false ? "selected" : ""}>Inactive</option>
        </select>
      </div>
      <div class="form-actions">
        <button type="button" class="btn secondary" onclick="closeModal()">Cancel</button>
        <button type="submit" class="btn">${user ? "Save changes" : "Create user"}</button>
      </div>
    </form>`;
}

function openUserModal(user) {
  openModal(user ? "Edit user" : "Create user", userForm(user));
  q("user-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const body = {
      full_name: fd.get("full_name").trim(),
      email: fd.get("email").trim() || null,
      person_id: fd.get("person_id") ? Number(fd.get("person_id")) : null,
      role: fd.get("role"),
      is_active: fd.get("is_active") === "true",
    };
    const password = fd.get("password");
    if (password) body.password = password;
    if (!user) {
      body.username = fd.get("username").trim();
      body.password = password;
    }
    try {
      if (user) {
        await api(`/api/users/${user.id}`, { method: "PATCH", body: JSON.stringify(body) });
        toast("User updated", "success");
        // If admin edited their own account, refresh state.me and sidebar
        if (state.me && state.me.id === user.id) {
          state.me = await api("/api/auth/me");
          setText("me-name", state.me.full_name);
          setText("me-role", state.me.role === "admin" ? "Administrator" : "User");
          const avatar = q("me-avatar");
          if (avatar) avatar.textContent = state.me.full_name.charAt(0).toUpperCase();
        }
      } else {
        await api("/api/users", { method: "POST", body: JSON.stringify(body) });
        toast("User created", "success");
      }
      closeModal();
      await loadUsers();
    } catch (err) {
      toast(err.message, "error");
    }
  });
}

window.editUser = (id) => openUserModal(state.users.find((u) => u.id === id));

window.deleteUser = async (id) => {
  const u = state.users.find((x) => x.id === id);
  const ok = await confirm("Delete user", `Delete user account <b>${esc(u.username)}</b>?`);
  if (ok) {
    try {
      await api(`/api/users/${id}`, { method: "DELETE" });
      toast("User deleted", "success");
      await loadUsers();
    } catch (err) {
      toast(err.message, "error");
    }
  }
};

/* =========================================================
   REPORTS (admin)
========================================================= */
async function loadReports() {
  await loadGroups();
  const groupSel = q("rep-group");
  groupSel.innerHTML = `<option value="">All groups</option>` + state.groups.map((g) => `<option value="${esc(g)}">${esc(g)}</option>`).join("");
  const now = new Date();
  const firstOfMonth = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-01`;
  q("rep-from").value = firstOfMonth;
  q("rep-to").value = todayISO();
  await runReport();
}

async function runReport() {
  const from = q("rep-from").value;
  const to = q("rep-to").value;
  if (!from || !to) {
    toast("Choose a date range", "error");
    return;
  }
  const group = q("rep-group").value;
  const params = new URLSearchParams({ date_from: from, date_to: to });
  if (group) params.set("group", group);
  const data = await api(`/api/reports/summary?${params}`);
  renderReport(data);
}

function renderReport(data) {
  // summary stat cards
  const totals = data.people.reduce(
    (acc, p) => {
      acc.present += p.present_days;
      acc.absent += p.absent_days;
      acc.hours += p.total_work_minutes;
      return acc;
    },
    { present: 0, absent: 0, hours: 0 }
  );
  q("rep-stats").innerHTML = `
    <div class="stat-card"><div class="v">${data.total_people}</div><div class="k">People</div></div>
    <div class="stat-card"><div class="v">${data.total_days}</div><div class="k">Days in range</div></div>
    <div class="stat-card"><div class="v">${totals.present}</div><div class="k">Present day-marks</div></div>
    <div class="stat-card"><div class="v">${totals.absent}</div><div class="k">Absent day-marks</div></div>
    <div class="stat-card"><div class="v">${fmtDur(totals.hours)}</div><div class="k">Total work time</div></div>`;

  if (!data.people.length) {
    q("reports-table").innerHTML = `<div class="empty">No data for this range.</div>`;
    return;
  }
  const rows = data.people
    .map((p) => {
      const rate = Math.round(p.attendance_rate * 100);
      return `<tr>
        <td><b>${esc(p.person_name)}</b></td>
        <td class="muted">${esc(p.group_name || "—")}</td>
        <td>${p.present_days}</td>
        <td>${p.absent_days}</td>
        <td>${p.half_days}</td>
        <td>${p.holiday_days}</td>
        <td class="muted">${p.unrecorded_days}</td>
        <td class="mono">${fmtDur(p.total_work_minutes)}</td>
        <td class="mono">${esc(p.avg_check_in || "—")}</td>
        <td class="mono">${esc(p.avg_check_out || "—")}</td>
        <td><div class="rate-cell"><div class="rate-bar"><div class="rate-fill" style="width:${rate}%"></div></div><span class="mono">${rate}%</span></div></td>
      </tr>`;
    })
    .join("");
  q("reports-table").innerHTML = `<table>
    <thead><tr><th>Person</th><th>Group</th><th>Present</th><th>Absent</th><th>Half</th><th>Holiday</th><th>No data</th><th>Work time</th><th>Avg in</th><th>Avg out</th><th>Rate</th></tr></thead>
    <tbody>${rows}</tbody></table>`;
}

async function exportCsv() {
  const from = q("rep-from").value;
  const to = q("rep-to").value;
  const group = q("rep-group").value;
  const params = new URLSearchParams({ date_from: from || isoOffset(29), date_to: to || todayISO() });
  if (group) params.set("group", group);
  const token = localStorage.getItem("token");
  const res = await fetch(`/api/reports/export?${params}`, { headers: { Authorization: `Bearer ${token}` } });
  if (!res.ok) {
    toast("Export failed", "error");
    return;
  }
  const blob = await res.blob();
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `attendance_${params.get("date_from")}_${params.get("date_to")}.csv`;
  a.click();
  URL.revokeObjectURL(a.href);
  toast("CSV downloaded", "success");
}

async function exportXlsx() {
  const from = q("rep-from").value;
  const to = q("rep-to").value;
  const group = q("rep-group").value;
  const params = new URLSearchParams({ date_from: from || isoOffset(29), date_to: to || todayISO() });
  if (group) params.set("group", group);
  const token = localStorage.getItem("token");
  const res = await fetch(`/api/reports/export/xlsx?${params}`, { headers: { Authorization: `Bearer ${token}` } });
  if (!res.ok) { toast("Export failed", "error"); return; }
  const blob = await res.blob();
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `attendance_${params.get("date_from")}_${params.get("date_to")}.xlsx`;
  a.click();
  URL.revokeObjectURL(a.href);
  toast("Excel downloaded", "success");
}

async function exportPdf() {
  const from = q("rep-from").value || isoOffset(29);
  const to = q("rep-to").value || todayISO();
  const group = q("rep-group").value;
  const params = new URLSearchParams({ date_from: from, date_to: to });
  if (group) params.set("group", group);

  const data = await api(`/api/reports/summary?${params}`);

  // Build HTML for PDF
  let html = `
    <html><head><title>Attendance Report ${from} to ${to}</title>
    <style>
      body { font-family: Arial, sans-serif; padding: 20px; }
      h1 { font-size: 22px; margin-bottom: 4px; }
      .sub { color: #666; margin-bottom: 20px; }
      table { width: 100%; border-collapse: collapse; font-size: 12px; }
      th { background: #f5f5f5; padding: 8px; text-align: left; border-bottom: 2px solid #ddd; }
      td { padding: 8px; border-bottom: 1px solid #eee; }
      .summary { display: flex; gap: 20px; margin-bottom: 20px; }
      .stat { padding: 10px; background: #f9f9f9; border-radius: 6px; }
      .stat .val { font-size: 24px; font-weight: bold; }
      .stat .lbl { font-size: 11px; color: #666; }
    </style></head><body>
    <h1>Attendance Report</h1>
    <div class="sub">${fmtDate(from)} — ${fmtDate(to)} | ${data.total_people} people | ${data.total_days} days</div>
    <div class="summary">
      <div class="stat"><div class="val">${data.total_people}</div><div class="lbl">People</div></div>
      <div class="stat"><div class="val">${data.total_days}</div><div class="lbl">Days</div></div>`;

  const totals = data.people.reduce((a, p) => { a.present += p.present_days; a.absent += p.absent_days; a.hours += p.total_work_minutes; return a; }, { present: 0, absent: 0, hours: 0 });
  html += `<div class="stat"><div class="val">${totals.present}</div><div class="lbl">Present</div></div>
      <div class="stat"><div class="val">${totals.absent}</div><div class="lbl">Absent</div></div>
      <div class="stat"><div class="val">${fmtDur(totals.hours)}</div><div class="lbl">Work Time</div></div>
    </div><table><thead><tr><th>Person</th><th>Group</th><th>Present</th><th>Absent</th><th>Half</th><th>Holiday</th><th>Work Time</th><th>Rate</th></tr></thead><tbody>`;

  data.people.forEach(p => {
    html += `<tr><td>${esc(p.person_name)}</td><td>${esc(p.group_name || "—")}</td><td>${p.present_days}</td><td>${p.absent_days}</td><td>${p.half_days}</td><td>${p.holiday_days}</td><td>${fmtDur(p.total_work_minutes)}</td><td>${Math.round(p.attendance_rate * 100)}%</td></tr>`;
  });

  html += `</tbody></table></body></html>`;

  const printWindow = window.open("", "_blank");
  printWindow.document.write(html);
  printWindow.document.close();
  printWindow.print();
  toast("PDF export ready", "success");
}

/* =========================================================
   HOLIDAYS
========================================================= */
async function loadHolidays() {
  const holidays = await api("/api/holidays");
  renderHolidays(holidays);
}

function renderHolidays(holidays) {
  if (!holidays.length) {
    q("holidays-table").innerHTML = `<div class="empty">No holidays configured.</div>`;
    return;
  }
  const rows = holidays
    .map((h) => `<tr>
      <td><b>${esc(h.name)}</b></td>
      <td class="mono">${fmtDate(h.date)}</td>
      <td class="muted">${esc(h.description || "—")}</td>
      <td><div class="action-cell">
        <button class="btn sm secondary" onclick="editHoliday(${h.id})">Edit</button>
        <button class="btn sm danger" onclick="deleteHoliday(${h.id})">Del</button>
      </div></td>
    </tr>`)
    .join("");
  q("holidays-table").innerHTML = `<table>
    <thead><tr><th>Name</th><th>Date</th><th>Description</th><th></th></tr></thead>
    <tbody>${rows}</tbody></table>`;
}

function holidayForm(holiday) {
  return `
    <form id="holiday-form">
      <div class="form-row"><label>Name *</label><input name="name" required maxlength="255" value="${esc(holiday?.name || "")}" /></div>
      <div class="form-row"><label>Date *</label><input type="date" name="date" required value="${holiday?.date || ""}" /></div>
      <div class="form-row"><label>Description</label><input name="description" value="${esc(holiday?.description || "")}" /></div>
      <div class="form-actions">
        <button type="button" class="btn secondary" onclick="closeModal()">Cancel</button>
        <button type="submit" class="btn">${holiday ? "Save changes" : "Add holiday"}</button>
      </div>
    </form>`;
}

let _holidaysCache = [];
async function openHolidayModal(holiday) {
  if (!_holidaysCache.length) _holidaysCache = await api("/api/holidays");
  openModal(holiday ? "Edit holiday" : "Add holiday", holidayForm(holiday));
  q("holiday-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const body = { name: fd.get("name").trim(), date: fd.get("date"), description: fd.get("description").trim() || null };
    try {
      if (holiday) {
        await api(`/api/holidays/${holiday.id}`, { method: "PATCH", body: JSON.stringify(body) });
        toast("Holiday updated", "success");
      } else {
        await api("/api/holidays", { method: "POST", body: JSON.stringify(body) });
        toast("Holiday added", "success");
      }
      closeModal();
      await loadHolidays();
    } catch (err) {
      toast(err.message, "error");
    }
  });
}

window.editHoliday = async (id) => {
  const holidays = await api("/api/holidays");
  const h = holidays.find((x) => x.id === id);
  if (h) openHolidayModal(h);
};

window.deleteHoliday = async (id) => {
  const ok = await confirm("Delete holiday", "Delete this holiday?");
  if (ok) {
    try {
      await api(`/api/holidays/${id}`, { method: "DELETE" });
      toast("Holiday deleted", "success");
      await loadHolidays();
    } catch (err) {
      toast(err.message, "error");
    }
  }
};

/* =========================================================
   SHIFTS & ROSTER
========================================================= */
async function loadShifts() {
  const [shifts, assignments] = await Promise.all([
    api("/api/shifts"),
    api("/api/shifts/assignments"),
  ]);
  renderShifts(shifts);
  renderAssignments(assignments);
}

function renderShifts(shifts) {
  if (!shifts.length) {
    q("shifts-table").innerHTML = `<div class="empty">No shifts configured.</div>`;
    return;
  }
  const rows = shifts
    .map((s) => `<tr>
      <td><b>${esc(s.name)}</b></td>
      <td class="mono">${s.start_time}</td>
      <td class="mono">${s.end_time}</td>
      <td>${s.is_active ? `<span class="badge active">Active</span>` : `<span class="badge inactive">Inactive</span>`}</td>
      <td><div class="action-cell">
        <button class="btn sm secondary" onclick="editShift(${s.id})">Edit</button>
        <button class="btn sm danger" onclick="deleteShift(${s.id})">Del</button>
      </div></td>
    </tr>`)
    .join("");
  q("shifts-table").innerHTML = `<table>
    <thead><tr><th>Name</th><th>Start</th><th>End</th><th>Status</th><th></th></tr></thead>
    <tbody>${rows}</tbody></table>`;
}

function renderAssignments(assignments) {
  if (!assignments.length) {
    q("assignments-table").innerHTML = `<div class="empty">No shift assignments.</div>`;
    return;
  }
  const rows = assignments
    .map((a) => `<tr>
      <td><b>${esc(a.person_name || "—")}</b></td>
      <td>${esc(a.shift_name || "—")}</td>
      <td class="mono">${fmtDate(a.start_date)}</td>
      <td class="mono">${a.end_date ? fmtDate(a.end_date) : "—"}</td>
      <td>${a.is_active ? `<span class="badge active">Active</span>` : `<span class="badge inactive">Inactive</span>`}</td>
      <td><div class="action-cell">
        <button class="btn sm secondary" onclick="editAssignment(${a.id})">Edit</button>
        <button class="btn sm danger" onclick="deleteAssignment(${a.id})">Del</button>
      </div></td>
    </tr>`)
    .join("");
  q("assignments-table").innerHTML = `<table>
    <thead><tr><th>Person</th><th>Shift</th><th>From</th><th>To</th><th>Status</th><th></th></tr></thead>
    <tbody>${rows}</tbody></table>`;
}

function shiftForm(shift) {
  return `
    <form id="shift-form">
      <div class="form-row"><label>Name *</label><input name="name" required maxlength="128" value="${esc(shift?.name || "")}" /></div>
      <div class="form-grid">
        <div class="form-row"><label>Start time *</label><input type="time" name="start_time" required value="${shift?.start_time || ""}" /></div>
        <div class="form-row"><label>End time *</label><input type="time" name="end_time" required value="${shift?.end_time || ""}" /></div>
      </div>
      <div class="form-actions">
        <button type="button" class="btn secondary" onclick="closeModal()">Cancel</button>
        <button type="submit" class="btn">${shift ? "Save changes" : "Add shift"}</button>
      </div>
    </form>`;
}

async function openShiftModal(shift) {
  openModal(shift ? "Edit shift" : "Add shift", shiftForm(shift));
  q("shift-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const body = { name: fd.get("name").trim(), start_time: fd.get("start_time"), end_time: fd.get("end_time") };
    try {
      if (shift) {
        await api(`/api/shifts/${shift.id}`, { method: "PATCH", body: JSON.stringify(body) });
        toast("Shift updated", "success");
      } else {
        await api("/api/shifts", { method: "POST", body: JSON.stringify(body) });
        toast("Shift created", "success");
      }
      closeModal();
      await loadShifts();
    } catch (err) {
      toast(err.message, "error");
    }
  });
}

window.editShift = async (id) => {
  const shifts = await api("/api/shifts");
  const s = shifts.find((x) => x.id === id);
  if (s) openShiftModal(s);
};

window.deleteShift = async (id) => {
  const ok = await confirm("Delete shift", "Delete this shift? All assignments will also be removed.");
  if (ok) {
    try {
      await api(`/api/shifts/${id}`, { method: "DELETE" });
      toast("Shift deleted", "success");
      await loadShifts();
    } catch (err) {
      toast(err.message, "error");
    }
  }
};

function assignmentForm(assignment) {
  const personOpts = state.people.filter((p) => p.is_active).map((p) => `<option value="${p.id}" ${assignment?.person_id === p.id ? "selected" : ""}>${esc(p.full_name)}</option>`).join("");
  return `
    <form id="assignment-form">
      <div class="form-row"><label>Person *</label><select name="person_id" required>${personOpts}</select></div>
      <div class="form-row"><label>Shift *</label><select name="shift_id" required id="assign-shift-select"></select></div>
      <div class="form-grid">
        <div class="form-row"><label>Start date *</label><input type="date" name="start_date" required value="${assignment?.start_date || todayISO()}" /></div>
        <div class="form-row"><label>End date (optional)</label><input type="date" name="end_date" value="${assignment?.end_date || ""}" /></div>
      </div>
      <div class="form-actions">
        <button type="button" class="btn secondary" onclick="closeModal()">Cancel</button>
        <button type="submit" class="btn">${assignment ? "Save changes" : "Assign shift"}</button>
      </div>
    </form>`;
}

async function openAssignmentModal(assignment) {
  await ensurePeople();
  const shifts = await api("/api/shifts");
  openModal(assignment ? "Edit assignment" : "Assign shift", assignmentForm(assignment));
  const sel = q("assign-shift-select");
  sel.innerHTML = shifts.map((s) => `<option value="${s.id}" ${assignment?.shift_id === s.id ? "selected" : ""}>${esc(s.name)} (${s.start_time} - ${s.end_time})</option>`).join("");
  q("assignment-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const body = {
      person_id: Number(fd.get("person_id")),
      shift_id: Number(fd.get("shift_id")),
      start_date: fd.get("start_date"),
      end_date: fd.get("end_date") || null,
    };
    try {
      if (assignment) {
        await api(`/api/shifts/assignments/${assignment.id}`, { method: "PATCH", body: JSON.stringify(body) });
        toast("Assignment updated", "success");
      } else {
        await api("/api/shifts/assignments", { method: "POST", body: JSON.stringify(body) });
        toast("Shift assigned", "success");
      }
      closeModal();
      await loadShifts();
    } catch (err) {
      toast(err.message, "error");
    }
  });
}

window.editAssignment = async (id) => {
  const assignments = await api("/api/shifts/assignments");
  const a = assignments.find((x) => x.id === id);
  if (a) openAssignmentModal(a);
};

window.deleteAssignment = async (id) => {
  const ok = await confirm("Delete assignment", "Remove this shift assignment?");
  if (ok) {
    try {
      await api(`/api/shifts/assignments/${id}`, { method: "DELETE" });
      toast("Assignment deleted", "success");
      await loadShifts();
    } catch (err) {
      toast(err.message, "error");
    }
  }
};

/* =========================================================
   NOTIFICATIONS
========================================================= */
async function loadNotifications() {
  await ensurePeople();
  fillPersonSelect("notif-person");
  fillPersonSelect("notif-late-person");
  try {
    const settings = await api("/api/notifications/settings");
    q("notif-settings").innerHTML = `
      <table>
        <tr><td>Email enabled</td><td><b>${settings.email_enabled ? "Yes" : "No"}</b></td></tr>
        <tr><td>SMTP host</td><td class="mono">${esc(settings.smtp_host)}</td></tr>
        <tr><td>SMTP port</td><td class="mono">${settings.smtp_port}</td></tr>
        <tr><td>SMTP user</td><td class="mono">${esc(settings.smtp_user || "Not set")}</td></tr>
        <tr><td>From email</td><td class="mono">${esc(settings.smtp_from_email || "Not set")}</td></tr>
        <tr><td>Late threshold</td><td>${settings.late_check_in_minutes} minutes after shift start</td></tr>
        <tr><td>Daily reminders</td><td>${settings.send_daily_reminder ? "Enabled" : "Disabled"}</td></tr>
        <tr><td>Late alerts</td><td>${settings.send_late_alert ? "Enabled" : "Disabled"}</td></tr>
      </table>`;
  } catch (_) {
    q("notif-settings").innerHTML = `<div class="empty">Could not load settings.</div>`;
  }
}

q("btn-send-reminder")?.addEventListener("click", async () => {
  const personId = q("notif-person")?.value || null;
  try {
    const result = await api("/api/notifications/send-reminder", {
      method: "POST",
      body: JSON.stringify({ person_id: personId ? Number(personId) : null }),
    });
    toast(`Reminder sent to ${result.sent} of ${result.total} people`, "success");
  } catch (err) {
    toast(err.message, "error");
  }
});

q("btn-send-late-alert")?.addEventListener("click", async () => {
  const personId = q("notif-late-person")?.value;
  if (!personId) {
    toast("Select a person", "error");
    return;
  }
  try {
    await api("/api/notifications/send-alert", {
      method: "POST",
      body: JSON.stringify({ person_id: Number(personId), alert_type: "late" }),
    });
    toast("Alert sent", "success");
  } catch (err) {
    toast(err.message, "error");
  }
});

/* =========================================================
   PASSWORD CHANGE
========================================================= */
function openChangePasswordModal() {
  openModal(
    "Change Password",
    `<form id="pw-form">
      <div class="form-row"><label>Current password</label><input type="password" name="current_password" required /></div>
      <div class="form-row"><label>New password</label><input type="password" name="new_password" required minlength="6" /></div>
      <div class="form-row"><label>Confirm new password</label><input type="password" name="confirm_password" required minlength="6" /></div>
      <div class="form-actions">
        <button type="button" class="btn secondary" onclick="closeModal()">Cancel</button>
        <button type="submit" class="btn">Change password</button>
      </div>
    </form>`
  );
  q("pw-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const np = fd.get("new_password");
    const cp = fd.get("confirm_password");
    if (np !== cp) {
      toast("New passwords do not match", "error");
      return;
    }
    try {
      await api("/api/auth/change-password", {
        method: "POST",
        body: JSON.stringify({ current_password: fd.get("current_password"), new_password: np }),
      });
      toast("Password changed successfully", "success");
      closeModal();
    } catch (err) {
      toast(err.message, "error");
    }
  });
}

/* =========================================================
   DARK MODE
========================================================= */
function initDarkMode() {
  const saved = localStorage.getItem("theme");
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  if (saved === "dark" || (!saved && prefersDark)) {
    document.documentElement.setAttribute("data-theme", "dark");
    updateDarkModeUI(true);
  }
}

function toggleDarkMode() {
  const isDark = document.documentElement.getAttribute("data-theme") === "dark";
  if (isDark) {
    document.documentElement.removeAttribute("data-theme");
    localStorage.setItem("theme", "light");
    updateDarkModeUI(false);
  } else {
    document.documentElement.setAttribute("data-theme", "dark");
    localStorage.setItem("theme", "dark");
    updateDarkModeUI(true);
  }
  // Refresh charts with new colors
  if (document.getElementById("chart-trend")) {
    loadCharts();
  }
}

function updateDarkModeUI(isDark) {
  // Update sidebar theme button icon
  const sidebarThemeBtn = document.getElementById("sidebar-theme-btn");
  if (sidebarThemeBtn) {
    sidebarThemeBtn.innerHTML = isDark
      ? '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/></svg><span class="sidebar-action-label">Theme</span>'
      : '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg><span class="sidebar-action-label">Theme</span>';
  }
}

/* =========================================================
   MOBILE MENU
========================================================= */
function initMobileMenu() {
  const btn = document.getElementById("mobile-menu-btn");
  const sidebar = document.getElementById("sidebar");
  const overlay = document.getElementById("sidebar-overlay");
  const main = document.querySelector(".main");
  
  if (!btn || !sidebar) return;

  let touchStartX = 0;
  let touchCurrentX = 0;
  let isDragging = false;

  function openSidebar() {
    btn.classList.add("active");
    sidebar.classList.add("open");
    overlay.classList.add("show");
    document.body.style.overflow = "hidden";
    document.body.style.paddingRight = getScrollbarWidth() + "px";
  }

  function closeSidebar() {
    btn.classList.remove("active");
    sidebar.classList.remove("open");
    overlay.classList.remove("show");
    document.body.style.overflow = "";
    document.body.style.paddingRight = "";
  }

  function getScrollbarWidth() {
    return window.innerWidth - document.documentElement.clientWidth;
  }

  // Toggle button
  btn.addEventListener("click", () => {
    if (sidebar.classList.contains("open")) {
      closeSidebar();
    } else {
      openSidebar();
    }
  });

  // Overlay click
  overlay.addEventListener("click", closeSidebar);

  // Close on nav item click (mobile)
  sidebar.querySelectorAll(".nav-item").forEach(item => {
    item.addEventListener("click", () => {
      if (window.innerWidth <= 768) closeSidebar();
    });
  });

  // Swipe to close
  sidebar.addEventListener("touchstart", (e) => {
    if (window.innerWidth > 768) return;
    touchStartX = e.touches[0].clientX;
    isDragging = false;
  }, { passive: true });

  sidebar.addEventListener("touchmove", (e) => {
    if (window.innerWidth > 768) return;
    touchCurrentX = e.touches[0].clientX;
    const diff = touchStartX - touchCurrentX;
    
    if (diff > 10) {
      isDragging = true;
      const translateX = Math.max(-diff, -260);
      sidebar.style.transform = `translateX(${translateX}px)`;
      sidebar.style.transition = "none";
    }
  }, { passive: true });

  sidebar.addEventListener("touchend", () => {
    if (window.innerWidth > 768 || !isDragging) return;
    const diff = touchStartX - touchCurrentX;
    
    sidebar.style.transform = "";
    sidebar.style.transition = "";
    
    if (diff > 80) {
      closeSidebar();
    }
    isDragging = false;
  });

  // Swipe to open from edge
  document.addEventListener("touchstart", (e) => {
    if (window.innerWidth > 768 || sidebar.classList.contains("open")) return;
    if (e.touches[0].clientX > 30) return;
    touchStartX = e.touches[0].clientX;
  }, { passive: true });

  document.addEventListener("touchmove", (e) => {
    if (window.innerWidth > 768 || sidebar.classList.contains("open") || touchStartX === 0) return;
    touchCurrentX = e.touches[0].clientX;
    const diff = touchCurrentX - touchStartX;
    
    if (diff > 10) {
      isDragging = true;
      const translateX = Math.max(-260 + diff, 0);
      sidebar.style.transform = `translateX(${translateX}px)`;
      sidebar.style.transition = "none";
      overlay.style.transition = "none";
      overlay.classList.add("show");
      overlay.style.background = `rgba(0, 0, 0, ${Math.min(diff / 260, 0.55)})`;
      btn.classList.add("active");
      document.body.style.overflow = "hidden";
    }
  }, { passive: true });

  document.addEventListener("touchend", () => {
    if (window.innerWidth > 768 || !isDragging || sidebar.classList.contains("open")) return;
    const diff = touchCurrentX - touchStartX;
    
    sidebar.style.transform = "";
    sidebar.style.transition = "";
    overlay.style.transition = "";
    overlay.style.background = "";
    
    if (diff > 100) {
      sidebar.classList.add("open");
      btn.classList.add("active");
      overlay.classList.add("show");
      document.body.style.overflow = "hidden";
      document.body.style.paddingRight = getScrollbarWidth() + "px";
    } else {
      overlay.classList.remove("show");
      btn.classList.remove("active");
      document.body.style.overflow = "";
    }
    
    isDragging = false;
    touchStartX = 0;
  });

  // Keyboard: Escape to close
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && sidebar.classList.contains("open")) {
      closeSidebar();
    }
  });

  // Resize: close sidebar if window becomes desktop
  window.addEventListener("resize", () => {
    if (window.innerWidth > 768 && sidebar.classList.contains("open")) {
      closeSidebar();
    }
  });
}

/* =========================================================
   NAV RIPPLE EFFECT
========================================================= */
function initNavRipple() {
  document.querySelectorAll(".nav-item").forEach(item => {
    item.addEventListener("mousedown", (e) => {
      const rect = item.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width) * 100;
      const y = ((e.clientY - rect.top) / rect.height) * 100;
      item.style.setProperty("--ripple-x", x + "%");
      item.style.setProperty("--ripple-y", y + "%");
    });
  });
}

/* =========================================================
   SECTION COLLAPSE
========================================================= */
function initSectionCollapse() {
  document.querySelectorAll(".nav-group-label").forEach(label => {
    label.addEventListener("click", () => {
      const group = label.closest(".nav-group");
      if (group) group.classList.toggle("collapsed");
    });
  });
}

/* =========================================================
   KEYBOARD SHORTCUTS
========================================================= */
function initKeyboardShortcuts() {
  document.addEventListener("keydown", (e) => {
    // Ctrl+K or Cmd+K to focus search
    if ((e.ctrlKey || e.metaKey) && e.key === "k") {
      e.preventDefault();
      const searchInput = document.getElementById("rec-search");
      if (searchInput) {
        showView("records");
        loadRecords();
        setTimeout(() => searchInput.focus(), 100);
      }
    }
    // Escape to close modal
    if (e.key === "Escape") {
      closeModal();
    }
    // ? for keyboard shortcuts help
    if (e.key === "?" && !e.target.matches("input, textarea, select")) {
      e.preventDefault();
      showShortcutsHelp();
    }
  });
}

/* =========================================================
   SCROLL TO TOP
========================================================= */
function initScrollToTop() {
  const btn = document.getElementById("scroll-top-btn");
  if (!btn) return;

  window.addEventListener("scroll", () => {
    if (window.scrollY > 300) {
      btn.classList.add("visible");
    } else {
      btn.classList.remove("visible");
    }
  });

  btn.addEventListener("click", () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  });
}

/* =========================================================
   SIDEBAR COLLAPSE
========================================================= */
function initSidebarCollapse() {
  const collapseBtn = document.getElementById("sidebar-collapse-btn");
  const sidebar = document.getElementById("sidebar");
  if (!collapseBtn || !sidebar) return;

  // Check saved state
  if (localStorage.getItem("sidebar_collapsed") === "true") {
    sidebar.classList.add("collapsed");
  }

  collapseBtn.addEventListener("click", () => {
    sidebar.classList.toggle("collapsed");
    localStorage.setItem("sidebar_collapsed", sidebar.classList.contains("collapsed"));
  });

  // Tooltip for collapsed mode
  const tooltip = document.createElement("div");
  tooltip.className = "sidebar-tooltip";
  document.body.appendChild(tooltip);

  sidebar.querySelectorAll(".nav-item").forEach(item => {
    item.addEventListener("mouseenter", () => {
      if (!sidebar.classList.contains("collapsed")) return;
      const label = item.querySelector(".nav-label")?.textContent || item.textContent.trim();
      tooltip.textContent = label;
      const rect = item.getBoundingClientRect();
      tooltip.style.top = rect.top + rect.height / 2 - 16 + "px";
      tooltip.classList.add("show");
    });
    item.addEventListener("mouseleave", () => {
      tooltip.classList.remove("show");
    });
  });
}

/* =========================================================
   KEYBOARD SHORTCUTS HELP
========================================================= */
function showShortcutsHelp() {
  openModal(
    "Keyboard Shortcuts",
    `<div class="shortcuts-list">
      <div class="shortcut-row"><span class="kbd">Ctrl</span> + <span class="kbd">K</span><span>Focus search</span></div>
      <div class="shortcut-row"><span class="kbd">Esc</span><span>Close modal</span></div>
      <div class="shortcut-row"><span class="kbd">?</span><span>Show this help</span></div>
    </div>`
  );
}

/* =========================================================
   INIT
========================================================= */
async function init() {
  if (!localStorage.getItem("token")) {
    window.location.href = "/login";
    return;
  }
  
  // Initialize dark mode
  initDarkMode();
  initMobileMenu();
  initKeyboardShortcuts();
  initScrollToTop();
  initNavRipple();
  initSectionCollapse();
  initSidebarCollapse();
  
  try {
    state.me = await api("/api/auth/me");
  } catch (_) {
    return; // api() already redirected
  }

  q("me-name").textContent = state.me.full_name;
  q("me-role").textContent = state.me.role === "admin" ? "Administrator" : "User";
  
  // Set avatar initial
  const avatar = q("me-avatar");
  if (avatar && state.me.full_name) {
    avatar.textContent = state.me.full_name.charAt(0).toUpperCase();
  }
  
  // Set header date
  const headerDate = q("header-date");
  if (headerDate) {
    headerDate.textContent = new Date().toLocaleDateString([], { weekday: "long", year: "numeric", month: "long", day: "numeric" });
  }

  // Show/hide admin-only UI
  const isAdmin = state.me.role === "admin";
  document.querySelectorAll(".admin-only").forEach((el) => el.classList.toggle("hidden", !isAdmin));
  if (!isAdmin) {
    // hide admin-only nav sections entirely for regular users
    document.querySelectorAll(".nav-group.admin-only").forEach((el) => el.classList.add("hidden"));
  }

  // Load badge counts
  loadNavBadges();

  bindNav();

  // Hero buttons
  q("btn-checkin").addEventListener("click", checkIn);
  q("btn-checkout").addEventListener("click", checkOut);

  // Sidebar action buttons
  const sidebarThemeBtn = document.getElementById("sidebar-theme-btn");
  const sidebarLogoutBtn = document.getElementById("sidebar-logout-btn");
  if (sidebarThemeBtn) sidebarThemeBtn.addEventListener("click", toggleDarkMode);
  if (sidebarLogoutBtn) sidebarLogoutBtn.addEventListener("click", () => {
    localStorage.removeItem("token");
    window.location.href = "/login";
  });

  // Theme toggle button in header
  const themeToggleBtn = document.getElementById("theme-toggle-btn");
  if (themeToggleBtn) themeToggleBtn.addEventListener("click", toggleDarkMode);

  // Records filters
  q("rec-apply").addEventListener("click", applyRecordFilters);
  q("rec-status").addEventListener("change", applyRecordFilters);
  q("rec-search")?.addEventListener("input", debounce(applyRecordFilters, 300));

  // People / Users buttons
  q("btn-add-person").addEventListener("click", () => openPersonModal(null));
  q("btn-add-user").addEventListener("click", () => openUserModal(null));
  q("btn-import-csv").addEventListener("click", openImportCsvModal);

  // Reports
  q("rep-run").addEventListener("click", runReport);
  q("btn-export").addEventListener("click", exportCsv);
  q("btn-export-pdf").addEventListener("click", exportPdf);
  q("btn-export-xlsx")?.addEventListener("click", exportXlsx);

  // Holidays
  q("btn-add-holiday").addEventListener("click", () => openHolidayModal(null));

  // Overtime
  q("btn-add-overtime")?.addEventListener("click", openOvertimeModal);

  // Shift Swaps
  q("btn-add-swap")?.addEventListener("click", async () => { await ensurePeople(); openSwapModal(); });

  // Tasks
  q("btn-add-task")?.addEventListener("click", async () => { await ensurePeople(); openTaskModal(); });
  q("task-status-filter")?.addEventListener("change", loadTasks);

  // Chat
  q("btn-send-chat")?.addEventListener("click", sendChatMessage);
  q("chat-input")?.addEventListener("keydown", (e) => { if (e.key === "Enter") sendChatMessage(); });
  q("chat-channel")?.addEventListener("change", loadChat);

  // Meetings
  q("btn-add-meeting")?.addEventListener("click", openMeetingModal);

  // Activity Logs
  q("btn-load-logs")?.addEventListener("click", loadActivityLogs);

  // Leaves
  q("btn-apply-leave").addEventListener("click", openApplyLeaveModal);
  q("leave-status-filter").addEventListener("change", applyLeaveFilters);

  // Breaks
  q("btn-start-break").addEventListener("click", startBreak);
  q("btn-end-break").addEventListener("click", endBreak);

  // Team
  q("btn-refresh-team").addEventListener("click", loadTeam);

  // Profile
  q("btn-edit-profile").addEventListener("click", openEditProfileModal);
  q("btn-change-pw").addEventListener("click", openChangePasswordModal);

  // Calendar
  q("cal-prev").addEventListener("click", () => { calMonth--; if (calMonth < 0) { calMonth = 11; calYear--; } loadCalendar(); });
  q("cal-next").addEventListener("click", () => { calMonth++; if (calMonth > 11) { calMonth = 0; calYear++; } loadCalendar(); });
  initCalendar();

  // Shifts
  q("btn-add-shift").addEventListener("click", () => openShiftModal(null));
  q("btn-add-assignment").addEventListener("click", () => openAssignmentModal(null));

  // Notifications
  q("btn-send-reminder")?.addEventListener("click", () => {});
  q("btn-send-late-alert")?.addEventListener("click", () => {});

  // Departments
  q("btn-add-dept").addEventListener("click", () => openDeptModal(null));

  // Announcements
  q("btn-add-announcement").addEventListener("click", openAnnouncementModal);

  // Salary
  q("btn-generate-salary").addEventListener("click", openGenerateSalaryModal);
  q("btn-filter-salary").addEventListener("click", loadSalaryData);

  // Modal backdrop click closes it
  q("modal-backdrop").addEventListener("click", (e) => {
    if (e.target.id === "modal-backdrop") closeModal();
  });

  // Sidebar search click
  const sidebarSearch = document.getElementById("sidebar-search-trigger");
  if (sidebarSearch) {
    sidebarSearch.addEventListener("click", () => {
      showView("records");
      loadRecords();
      setTimeout(() => {
        const searchInput = document.getElementById("rec-search");
        if (searchInput) searchInput.focus();
      }, 100);
    });
  }

  // Table keyboard navigation
  document.addEventListener("keydown", (e) => {
    if (e.target.closest(".table-wrap")) {
      const rows = [...e.target.closest(".table-wrap").querySelectorAll("tbody tr")];
      const current = rows.indexOf(document.activeElement.closest("tr"));
      if (e.key === "ArrowDown" && current < rows.length - 1) {
        e.preventDefault();
        rows[current + 1].focus();
        rows[current + 1].classList.add("selected");
        rows[current]?.classList.remove("selected");
      } else if (e.key === "ArrowUp" && current > 0) {
        e.preventDefault();
        rows[current - 1].focus();
        rows[current - 1].classList.add("selected");
        rows[current]?.classList.remove("selected");
      }
    }
  });

  // Add focus tabindex to table rows
  document.addEventListener("click", (e) => {
    const row = e.target.closest("tbody tr");
    if (row) {
      row.setAttribute("tabindex", "0");
      row.focus();
      row.closest("table")?.querySelectorAll("tbody tr").forEach(r => r.classList.remove("selected"));
      row.classList.add("selected");
    }
  });

  await loadDashboard();
}

document.addEventListener("DOMContentLoaded", init);
