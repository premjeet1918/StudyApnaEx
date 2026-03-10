import os
import sys
import time
import subprocess
from flask import Flask, jsonify, render_template_string
from bot_status import get_tasks, get_bot_info, mark_bot_stopped

app = Flask(__name__)
PORT = int(os.environ.get("PORT", 3000))
START_TIME = time.time()
bot_process = None


# ────────────────────────────────────────────────────────────
# Dashboard HTML — single-file template for easy deployment
# ────────────────────────────────────────────────────────────

DASHBOARD_HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>StudyApna Bot — Dashboard</title>
  <meta name="description" content="Real-time dashboard for StudyApna Bot extraction server showing live course extraction progress and server status." />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet" />
  <style>
    /* ── Reset & Base ─────────────────────────────── */
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --bg-main: #0a0e17;
      --bg-card: #111827;
      --bg-card-alt: #1a2234;
      --bg-table-header: #1f2b3d;
      --bg-table-row-hover: rgba(99,102,241,.08);
      --border: #1e293b;
      --border-glow: rgba(99,102,241,.25);
      --text-primary: #f1f5f9;
      --text-secondary: #94a3b8;
      --text-muted: #64748b;
      --accent: #6366f1;
      --accent-light: #818cf8;
      --green: #22c55e;
      --green-dim: rgba(34,197,94,.15);
      --amber: #f59e0b;
      --amber-dim: rgba(245,158,11,.15);
      --red: #ef4444;
      --red-dim: rgba(239,68,68,.15);
      --cyan: #06b6d4;
      --cyan-dim: rgba(6,182,212,.12);
      --gradient-brand: linear-gradient(135deg, #6366f1, #06b6d4);
      --shadow-card: 0 4px 24px rgba(0,0,0,.35);
      --shadow-glow: 0 0 40px rgba(99,102,241,.12);
      --radius: 16px;
      --radius-sm: 10px;
    }
    html { scroll-behavior: smooth; }
    body {
      font-family: 'Inter', system-ui, -apple-system, sans-serif;
      background: var(--bg-main);
      color: var(--text-primary);
      min-height: 100vh;
      overflow-x: hidden;
    }

    /* ── Animated Background ─────────────────────── */
    body::before {
      content: '';
      position: fixed; inset: 0;
      background:
        radial-gradient(ellipse 80% 50% at 50% -20%, rgba(99,102,241,.15), transparent),
        radial-gradient(ellipse 60% 40% at 80% 100%, rgba(6,182,212,.1), transparent);
      pointer-events: none;
      z-index: 0;
    }

    /* ── Container ───────────────────────────────── */
    .wrapper {
      position: relative; z-index: 1;
      max-width: 1040px;
      margin: 0 auto;
      padding: 40px 20px 60px;
    }

    /* ── Header ──────────────────────────────────── */
    .header {
      text-align: center;
      margin-bottom: 36px;
    }
    .header-title {
      font-size: 2.2rem;
      font-weight: 800;
      letter-spacing: -0.5px;
      display: inline-flex; align-items: center; gap: 12px;
    }
    .header-title .rocket {
      font-size: 2rem;
      animation: rocketFloat 2.5s ease-in-out infinite;
    }
    @keyframes rocketFloat {
      0%, 100% { transform: translateY(0) rotate(-8deg); }
      50%      { transform: translateY(-8px) rotate(0deg); }
    }
    .header-title .brand {
      background: var(--gradient-brand);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    .header-subtitle {
      margin-top: 4px;
      font-size: .95rem;
      color: var(--text-secondary);
      font-weight: 500;
    }

    /* ── Status Row ───────────────────────────────── */
    .status-row {
      display: flex;
      justify-content: center;
      gap: 10px;
      margin-top: 14px;
      flex-wrap: wrap;
    }
    .badge {
      display: inline-flex; align-items: center; gap: 6px;
      padding: 6px 16px;
      border-radius: 999px;
      font-size: .82rem;
      font-weight: 600;
      letter-spacing: .3px;
    }
    .badge-active {
      background: var(--green-dim);
      color: var(--green);
      border: 1px solid rgba(34,197,94,.3);
    }
    .badge-inactive {
      background: var(--red-dim);
      color: var(--red);
      border: 1px solid rgba(239,68,68,.3);
    }
    .badge .dot {
      width: 8px; height: 8px;
      border-radius: 50%;
      display: inline-block;
    }
    .badge-active .dot { background: var(--green); box-shadow: 0 0 6px var(--green); animation: pulse 1.8s infinite; }
    .badge-inactive .dot { background: var(--red); }
    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50%      { opacity: .4; }
    }

    /* ── Stat Cards ───────────────────────────────── */
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
      margin-bottom: 32px;
      margin-top: 28px;
    }
    .stat-card {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 22px 20px;
      box-shadow: var(--shadow-card);
      transition: transform .25s, border-color .25s, box-shadow .25s;
      position: relative;
      overflow: hidden;
    }
    .stat-card:hover {
      transform: translateY(-3px);
      border-color: var(--border-glow);
      box-shadow: var(--shadow-glow);
    }
    .stat-card::before {
      content: '';
      position: absolute;
      top: 0; left: 0; right: 0;
      height: 3px;
      border-radius: var(--radius) var(--radius) 0 0;
    }
    .stat-card:nth-child(1)::before { background: var(--accent); }
    .stat-card:nth-child(2)::before { background: var(--green); }
    .stat-card:nth-child(3)::before { background: var(--cyan); }
    .stat-card:nth-child(4)::before { background: var(--amber); }
    .stat-icon { font-size: 1.5rem; margin-bottom: 8px; }
    .stat-label { font-size: .78rem; text-transform: uppercase; letter-spacing: 1px; color: var(--text-muted); font-weight: 600; }
    .stat-value { font-size: 1.8rem; font-weight: 800; margin-top: 4px; font-family: 'JetBrains Mono', monospace; }

    /* ── Activity Table Card ─────────────────────── */
    .card {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      box-shadow: var(--shadow-card);
      overflow: hidden;
    }
    .card-header {
      display: flex; align-items: center; justify-content: space-between;
      padding: 18px 24px;
      border-bottom: 1px solid var(--border);
    }
    .card-header h2 {
      font-size: 1.05rem;
      font-weight: 700;
      display: flex; align-items: center; gap: 8px;
    }
    .refresh-btn {
      background: rgba(99,102,241,.12);
      border: 1px solid rgba(99,102,241,.25);
      color: var(--accent-light);
      padding: 7px 16px;
      border-radius: 8px;
      font-size: .8rem;
      font-weight: 600;
      cursor: pointer;
      transition: all .2s;
      font-family: inherit;
    }
    .refresh-btn:hover {
      background: rgba(99,102,241,.2);
      border-color: var(--accent);
      transform: scale(1.03);
    }
    .power-btn {
      background: var(--bg-card);
      border: 1px solid var(--border);
      color: var(--text-primary);
      padding: 8px 20px;
      border-radius: 999px;
      font-size: .85rem;
      font-weight: 600;
      cursor: pointer;
      transition: all .2s;
      font-family: inherit;
      display: inline-flex;
      align-items: center;
      gap: 8px;
    }
    .power-btn:hover { background: var(--bg-card-alt); }
    .power-btn.on { color: var(--red); border-color: rgba(239,68,68,.3); background: rgba(239,68,68,.1); }
    .power-btn.off { color: var(--green); border-color: rgba(34,197,94,.3); background: rgba(34,197,94,.1); }
    .power-btn.loading { opacity: 0.7; pointer-events: none; }

    /* ── Table ────────────────────────────────── */
    .table-wrap { overflow-x: auto; }
    table { width: 100%; border-collapse: collapse; }
    thead th {
      background: var(--bg-table-header);
      padding: 13px 18px;
      text-align: left;
      font-size: .76rem;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: var(--text-muted);
      font-weight: 700;
      border-bottom: 1px solid var(--border);
      position: sticky; top: 0; z-index: 2;
    }
    tbody td {
      padding: 14px 18px;
      font-size: .88rem;
      color: var(--text-secondary);
      border-bottom: 1px solid rgba(30,41,59,.4);
      vertical-align: middle;
    }
    tbody tr { transition: background .18s; }
    tbody tr:hover { background: var(--bg-table-row-hover); }
    tbody tr:last-child td { border-bottom: none; }
    .batch-id {
      font-family: 'JetBrains Mono', monospace;
      font-size: .82rem;
      font-weight: 600;
      color: var(--accent-light);
      background: rgba(99,102,241,.1);
      padding: 3px 9px;
      border-radius: 6px;
    }
    .course-name {
      font-weight: 600;
      color: var(--text-primary);
      max-width: 320px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .progress-cell {
      display: flex; align-items: center; gap: 10px;
    }
    .progress-bar-bg {
      flex: 1;
      height: 6px;
      background: rgba(255,255,255,.06);
      border-radius: 999px;
      overflow: hidden;
      min-width: 60px;
    }
    .progress-bar-fill {
      height: 100%;
      border-radius: 999px;
      transition: width .6s ease;
    }
    .progress-text {
      font-family: 'JetBrains Mono', monospace;
      font-size: .8rem;
      font-weight: 600;
      white-space: nowrap;
    }
    .status-tag {
      display: inline-flex; align-items: center; gap: 5px;
      padding: 4px 12px;
      border-radius: 999px;
      font-size: .78rem;
      font-weight: 700;
      letter-spacing: .3px;
    }
    .status-running  { background: var(--green-dim); color: var(--green); border: 1px solid rgba(34,197,94,.25); }
    .status-completed { background: var(--cyan-dim); color: var(--cyan); border: 1px solid rgba(6,182,212,.25); }
    .status-failed   { background: var(--red-dim); color: var(--red); border: 1px solid rgba(239,68,68,.25); }
    .status-pending  { background: var(--amber-dim); color: var(--amber); border: 1px solid rgba(245,158,11,.25); }
    .date-cell {
      font-family: 'JetBrains Mono', monospace;
      font-size: .8rem;
      color: var(--text-muted);
    }

    /* empty state */
    .empty-state {
      text-align: center;
      padding: 56px 20px;
      color: var(--text-muted);
    }
    .empty-state .icon { font-size: 2.8rem; margin-bottom: 12px; opacity: .6; }
    .empty-state p { font-size: .92rem; }
    .empty-state .hint { font-size: .8rem; margin-top: 6px; color: var(--text-muted); }

    /* ── Footer ──────────────────────────────── */
    .footer {
      text-align: center;
      margin-top: 40px;
      font-size: .78rem;
      color: var(--text-muted);
    }
    .footer a { color: var(--accent-light); text-decoration: none; }
    .footer a:hover { text-decoration: underline; }

    /* ── Responsive ──────────────────────────── */
    @media (max-width: 640px) {
      .header-title { font-size: 1.5rem; }
      .stat-value { font-size: 1.4rem; }
      .stats-grid { grid-template-columns: repeat(2, 1fr); gap: 10px; }
      thead th, tbody td { padding: 10px 12px; }
    }

    /* ── Auto-refresh spinner ────────────────── */
    .spin { animation: spin .8s linear infinite; display: inline-block; }
    @keyframes spin { to { transform: rotate(360deg); } }
  </style>
</head>
<body>
  <div class="wrapper">

    <!-- ─ Header ──────────────────────────────────── -->
    <header class="header">
      <h1 class="header-title">
        <span class="rocket">🚀</span>
        <span class="brand">StudyApna Bot Server is RUNNING</span>
      </h1>
      <p class="header-subtitle" id="uptime-text">Uptime: calculating…</p>
      <div class="status-row">
        <span class="badge" id="server-badge">
          <span class="dot"></span>
          <span id="server-status-text">Checking…</span>
        </span>
        <button id="power-btn" class="power-btn" onclick="toggleBot()">
          <span id="power-icon">⏳</span> <span id="power-text">Loading...</span>
        </button>
      </div>
    </header>

    <!-- ─ Stat Cards ──────────────────────────────── -->
    <section class="stats-grid" id="stats-grid">
      <div class="stat-card">
        <div class="stat-icon">📦</div>
        <div class="stat-label">Total Extractions</div>
        <div class="stat-value" id="stat-total">—</div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">✅</div>
        <div class="stat-label">Completed</div>
        <div class="stat-value" id="stat-completed">—</div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">⚡</div>
        <div class="stat-label">Running Now</div>
        <div class="stat-value" id="stat-running">—</div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">❌</div>
        <div class="stat-label">Failed</div>
        <div class="stat-value" id="stat-failed">—</div>
      </div>
    </section>

    <!-- ─ Activity Table ──────────────────────────── -->
    <div class="card">
      <div class="card-header">
        <h2>📋 Recent Bot Activity</h2>
        <button class="refresh-btn" id="refresh-btn" onclick="fetchData()">
          ↻ Refresh
        </button>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Batch ID</th>
              <th>Name</th>
              <th>Progress</th>
              <th>Status</th>
              <th>Date Added</th>
            </tr>
          </thead>
          <tbody id="task-tbody">
            <tr>
              <td colspan="5">
                <div class="empty-state">
                  <div class="icon">📡</div>
                  <p>Loading activity data…</p>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <footer class="footer">
      Made with ❤️ by <a href="https://t.me/StudyApna" target="_blank">StudyApna</a> &bull; Auto-refreshes every 5 s
    </footer>
  </div>

  <script>
    const API = "/api/status";

    async function toggleBot() {
      const btn = document.getElementById("power-btn");
      const isUp = btn.classList.contains("on");
      const action = isUp ? "stop" : "start";
      const endpoint = "/api/" + action;

      btn.classList.add("loading");
      document.getElementById("power-text").textContent = "Please wait...";

      try {
        await fetch(endpoint, { method: "POST" });
        setTimeout(fetchData, 1000); // Wait 1s and refresh
      } catch (e) {
        console.error("Failed to toggle bot:", e);
      } finally {
        setTimeout(() => btn.classList.remove("loading"), 1500);
      }
    }

    function statusClass(s) {
      const l = s.toLowerCase();
      if (l === "running")   return "status-running";
      if (l === "completed") return "status-completed";
      if (l === "failed")    return "status-failed";
      return "status-pending";
    }

    function barColor(pct) {
      if (pct >= 100) return "var(--cyan)";
      if (pct >= 50)  return "var(--green)";
      if (pct >= 20)  return "var(--amber)";
      return "var(--accent)";
    }

    function uptimeStr(sec) {
      const d = Math.floor(sec / 86400);
      const h = Math.floor((sec % 86400) / 3600);
      const m = Math.floor((sec % 3600) / 60);
      const s = Math.floor(sec % 60);
      let parts = [];
      if (d) parts.push(d + "d");
      if (h) parts.push(h + "h");
      if (m) parts.push(m + "m");
      parts.push(s + "s");
      return parts.join(" ");
    }

    async function fetchData() {
      const btn = document.getElementById("refresh-btn");
      btn.innerHTML = '<span class="spin">↻</span> Refreshing';
      try {
        const r = await fetch(API);
        const d = await r.json();

        // Server badge
        const badge = document.getElementById("server-badge");
        const isUp = d.bot_info.running;
        badge.className = "badge " + (isUp ? "badge-active" : "badge-inactive");
        document.getElementById("server-status-text").textContent = isUp ? "Active" : "Offline";

        // Uptime
        document.getElementById("uptime-text").textContent = "Uptime: " + uptimeStr(d.uptime);

        // Power Button
        const pBtn = document.getElementById("power-btn");
        const pIcon = document.getElementById("power-icon");
        const pText = document.getElementById("power-text");
        if (isUp) {
          pBtn.className = "power-btn on";
          pIcon.textContent = "⏹";
          pText.textContent = "Stop Bot";
        } else {
          pBtn.className = "power-btn off";
          pIcon.textContent = "▶";
          pText.textContent = "Start Bot";
        }

        // Stats
        const tasks = d.tasks || [];
        const total = tasks.length;
        const completed = tasks.filter(t => t.status === "Completed").length;
        const running = tasks.filter(t => t.status === "Running").length;
        const failed = tasks.filter(t => t.status === "Failed").length;
        animateValue("stat-total", total);
        animateValue("stat-completed", completed);
        animateValue("stat-running", running);
        animateValue("stat-failed", failed);

        // Table
        const tbody = document.getElementById("task-tbody");
        if (!tasks.length) {
          tbody.innerHTML = `<tr><td colspan="5">
            <div class="empty-state">
              <div class="icon">🔎</div>
              <p>No extractions yet</p>
              <p class="hint">Send a command to your bot to start extracting courses</p>
            </div>
          </td></tr>`;
        } else {
          tbody.innerHTML = tasks.map(t => {
            const pct = t.total > 0 ? Math.round((t.done / t.total) * 100) : 0;
            return `<tr>
              <td><span class="batch-id">${t.batch_id}</span></td>
              <td><span class="course-name" title="${t.name}">${t.name}</span></td>
              <td>
                <div class="progress-cell">
                  <div class="progress-bar-bg">
                    <div class="progress-bar-fill" style="width:${pct}%;background:${barColor(pct)}"></div>
                  </div>
                  <span class="progress-text">${t.done} / ${t.total}</span>
                </div>
              </td>
              <td><span class="status-tag ${statusClass(t.status)}">${t.status === "Running" ? '<span class="dot" style="width:6px;height:6px;border-radius:50%;background:var(--green);animation:pulse 1.5s infinite"></span>' : ''}${t.status}</span></td>
              <td><span class="date-cell">${t.date_added}</span></td>
            </tr>`;
          }).join("");
        }
      } catch (e) {
        console.error("Fetch error:", e);
      } finally {
        btn.innerHTML = "↻ Refresh";
      }
    }

    // number counter animation
    function animateValue(id, end) {
      const el = document.getElementById(id);
      const cur = parseInt(el.textContent) || 0;
      if (cur === end) { el.textContent = end; return; }
      const step = Math.sign(end - cur);
      let v = cur;
      const iv = setInterval(() => {
        v += step;
        el.textContent = v;
        if (v === end) clearInterval(iv);
      }, 40);
    }

    // initial & auto-refresh
    fetchData();
    setInterval(fetchData, 5000);
  </script>
</body>
</html>
"""


# ────────────────────────────────────────────────────────────
# Routes
# ────────────────────────────────────────────────────────────

@app.route("/")
def dashboard():
    return render_template_string(DASHBOARD_HTML)

@app.route("/api/start", methods=["POST"])
def start_bot():
    global bot_process
    if bot_process is None or bot_process.poll() is not None:
        try:
            bot_process = subprocess.Popen([sys.executable, "-m", "Extractor"])
        except Exception as e:
            return jsonify({"success": False, "message": str(e)})
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "Already running"})

@app.route("/api/stop", methods=["POST"])
def stop_bot():
    global bot_process
    if bot_process is not None and bot_process.poll() is None:
        try:
            bot_process.terminate()
            bot_process.wait(timeout=5)
        except Exception:
            try: bot_process.kill()
            except: pass
    bot_process = None
    mark_bot_stopped()
    return jsonify({"success": True})


@app.route("/api/status")
def api_status():
    uptime = time.time() - START_TIME
    return jsonify({
        "bot_info": get_bot_info(),
        "tasks": get_tasks(),
        "uptime": round(uptime),
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
