from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
import json

router = APIRouter(tags=["dashboard"])

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>HashA2A — Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.5.1"></script>
<style>
:root {
  --bg-primary: #0b1120;
  --bg-card: #131b2e;
  --bg-header: #0d1526;
  --border: #1e2a45;
  --text-primary: #e8edf5;
  --text-secondary: #7b8cae;
  --text-muted: #4a5a7a;
  --accent-1: #3b82f6;
  --accent-2: #8b5cf6;
  --accent-3: #06b6d4;
  --green: #22c55e;
  --yellow: #eab308;
  --red: #ef4444;
  --radius: 12px;
  --gap: 16px;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: var(--bg-primary);
  color: var(--text-primary);
  min-height: 100vh;
}
.dashboard { max-width: 1440px; margin: 0 auto; padding: var(--gap); }

/* Header */
.header {
  background: linear-gradient(135deg, #0f1d3a, #1a0e3a);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px 24px;
  margin-bottom: var(--gap);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  animation: headerGlow 3s ease-in-out infinite alternate;
}
@keyframes headerGlow {
  0% { box-shadow: 0 0 8px rgba(59,130,246,0.1); }
  100% { box-shadow: 0 0 20px rgba(139,92,246,0.3); }
}
.header h1 { font-size: 22px; font-weight: 700; }
.header h1 span { background: linear-gradient(135deg, var(--accent-1), var(--accent-2)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.header-right { display: flex; align-items: center; gap: 16px; }
.badge {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 4px 12px; border-radius: 9999px; font-size: 12px; font-weight: 600;
}
.badge-live { background: rgba(34,197,94,0.12); color: var(--green); border: 1px solid rgba(34,197,94,0.25); }
.badge-live::before { content: ''; width: 8px; height: 8px; border-radius: 50%; background: var(--green); animation: pulse 2s infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
.badge-version { background: rgba(59,130,246,0.1); color: var(--accent-1); border: 1px solid rgba(59,130,246,0.2); }

/* 3-Column Layout */
.layout {
  display: grid;
  grid-template-columns: 280px 1fr 300px;
  gap: var(--gap);
}
@media (max-width: 1200px) { .layout { grid-template-columns: 1fr; } }

/* Sidebar Left */
.sidebar-left {
  display: flex;
  flex-direction: column;
  gap: var(--gap);
}

/* Main Content */
.main {
  display: flex;
  flex-direction: column;
  gap: var(--gap);
}

/* Sidebar Right */
.sidebar-right {
  display: flex;
  flex-direction: column;
  gap: var(--gap);
}

/* KPI Row */
.kpi-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--gap);
}
.kpi-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px 24px;
  position: relative;
  overflow: hidden;
}
.kpi-card::before {
  content: '';
  position: absolute; top: 0; left: 0; right: 0;
  height: 3px;
  border-radius: var(--radius) var(--radius) 0 0;
}
.kpi-card.blue::before { background: var(--accent-1); }
.kpi-card.purple::before { background: var(--accent-2); }
.kpi-card.cyan::before { background: var(--accent-3); }
.kpi-card.green::before { background: var(--green); }
.kpi-label { font-size: 12px; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }
.kpi-value { font-size: 30px; font-weight: 700; margin-bottom: 2px; }
.kpi-sub { font-size: 13px; color: var(--text-muted); }

/* Chart Cards */
.chart-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px 24px;
}
.chart-card h3 { font-size: 14px; font-weight: 600; color: var(--text-secondary); margin-bottom: 16px; }
.chart-card canvas { max-height: 260px; max-width: 100%; }

/* Providers Table */
.table-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px 24px;
}
.table-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-wrap: wrap; gap: 12px; }
.table-header h3 { font-size: 14px; font-weight: 600; color: var(--text-secondary); }
.table-filters { display: flex; gap: 8px; align-items: center; }
.table-filters select {
  background: var(--bg-primary); color: var(--text-primary);
  border: 1px solid var(--border); border-radius: 6px;
  padding: 6px 10px; font-size: 12px; cursor: pointer;
}
.prov-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.prov-table thead th {
  text-align: left; padding: 10px 12px;
  border-bottom: 1px solid var(--border);
  color: var(--text-muted); font-weight: 600; font-size: 11px;
  text-transform: uppercase; letter-spacing: 0.5px;
  cursor: pointer; user-select: none;
}
.prov-table thead th:hover { color: var(--text-secondary); }
.prov-table tbody td { padding: 10px 12px; border-bottom: 1px solid rgba(30,42,69,0.5); }
.prov-table tbody tr:hover { background: rgba(59,130,246,0.04); }
.score-bar { height: 4px; border-radius: 2px; margin-top: 4px; }
.status-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; }

/* Provider List (Sidebar) */
.provider-list {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
}
.provider-list h3 { font-size: 14px; font-weight: 600; color: var(--text-secondary); margin-bottom: 12px; }
.provider-item {
  padding: 10px;
  border-radius: 8px;
  margin-bottom: 8px;
  background: var(--bg-primary);
  border: 1px solid transparent;
  transition: border-color 0.2s;
}
.provider-item:hover { border-color: var(--accent-1); }
.provider-item .name { font-size: 13px; font-weight: 600; }
.provider-item .meta { font-size: 11px; color: var(--text-muted); margin-top: 4px; display: flex; justify-content: space-between; }
.provider-item .mini-bar { height: 3px; border-radius: 2px; margin-top: 6px; background: var(--border); }
.provider-item .mini-bar-fill { height: 100%; border-radius: 2px; }

/* Topic Feed (Sidebar Right) */
.topic-feed {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
  max-height: 400px;
  overflow-y: auto;
}
.topic-feed h3 { font-size: 14px; font-weight: 600; color: var(--text-secondary); margin-bottom: 12px; }
.topic-item {
  padding: 8px 0;
  border-bottom: 1px solid rgba(30,42,69,0.5);
  font-size: 12px;
}
.topic-item:last-child { border-bottom: none; }
.topic-item .time { color: var(--text-muted); font-size: 10px; }
.topic-item .title { color: var(--text-primary); margin-top: 2px; }

/* Agent List (Sidebar Right) */
.agent-list {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
  max-height: 300px;
  overflow-y: auto;
}
.agent-list h3 { font-size: 14px; font-weight: 600; color: var(--text-secondary); margin-bottom: 12px; }
.agent-item {
  padding: 10px;
  border-radius: 8px;
  margin-bottom: 8px;
  background: var(--bg-primary);
  border: 1px solid transparent;
  transition: border-color 0.2s;
}
.agent-item:hover { border-color: var(--accent-2); }
.agent-item .name { font-size: 13px; font-weight: 600; }
.agent-item .name .dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; }
.agent-item .name .dot.online { background: var(--green); box-shadow: 0 0 6px var(--green); }
.agent-item .name .dot.offline { background: var(--red); }
.agent-item .name .dot.unknown { background: var(--yellow); }
.agent-item .meta { font-size: 11px; color: var(--text-muted); margin-top: 4px; }
.agent-item .tags { font-size: 10px; color: var(--accent-3); margin-top: 4px; }

.a2a-row { display:flex; justify-content:space-between; padding:6px 0; font-size:13px; border-bottom:1px solid rgba(30,42,69,0.3); }
.a2a-row:last-child { border-bottom:none; }
.a2a-label { color:var(--muted); }
.a2a-value { font-weight:600; }

/* Footer */
.footer { text-align: center; padding: 20px; color: var(--text-muted); font-size: 12px; }

/* Loading */
.loading { text-align: center; padding: 60px; color: var(--text-muted); }
.loading::after { content: ''; display: block; width: 32px; height: 32px; margin: 16px auto; border: 3px solid var(--border); border-top-color: var(--accent-1); border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
</head>
<body>
<div class="dashboard">
  <div class="header">
    <div>
      <h1>🏪 <span>HashA2A</span></h1>
      <div style="font-size:13px;color:var(--text-secondary);margin-top:2px;">Agent-to-Agent Intelligence Layer</div>
    </div>
    <div class="header-right">
      <span class="badge badge-live">Live</span>
      <span class="badge badge-version">v<span id="agent-version">—</span></span>
    </div>
  </div>

  <div id="dashboard-content">
    <div class="loading">Loading dashboard data…</div>
  </div>

  <div class="footer">
    HashA2A · Data refreshes every 10s · HCS audit trail · HIP-991 + x402 payments
  </div>
</div>

<script>
let charts = { initialized: false };

function initCharts() {
  if (typeof Chart === 'undefined') {
    setTimeout(initCharts, 1000);
    return;
  }
  Chart.defaults.color = '#7b8cae';
  Chart.defaults.borderColor = '#1e2a45';
  charts.initialized = true;
}

function renderDashboard(data) {
  const container = document.getElementById('dashboard-content');

  if (data.error) {
    container.innerHTML = `<div class="loading" style="color:var(--red)">⚠️ ${data.error}</div>`;
    return;
  }

  document.getElementById('agent-version').textContent = data.version || '—';

  const providers = data.providers || [];
  const totalStaked = providers.reduce((s, p) => s + (p.staked_hbar || 0), 0);
  const totalReqs = data.total_requests || 0;
  const avgTrust = providers.length ? providers.reduce((s, p) => s + (p.trust_score || 0), 0) / providers.length : 0;

  container.innerHTML = `
    <div class="layout">
      <div class="sidebar-left">
        <div class="kpi-card blue">
          <div class="kpi-label">Requests Served</div>
          <div class="kpi-value">${fmt(totalReqs)}</div>
          <div class="kpi-sub">${providers.length} active providers</div>
        </div>
        <div class="kpi-card purple">
          <div class="kpi-label">Avg Trust Score</div>
          <div class="kpi-value">${avgTrust.toFixed(0)}</div>
          <div class="kpi-sub">weighted reputation</div>
        </div>
        <div class="kpi-card cyan">
          <div class="kpi-label">HBAR Staked</div>
          <div class="kpi-value">${fmt(totalStaked)}</div>
          <div class="kpi-sub">ℏ across all providers</div>
        </div>
        <div class="kpi-card green">
          <div class="kpi-label">Payments</div>
          <div class="kpi-value" style="font-size:22px;">HIP-991 + x402</div>
          <div class="kpi-sub">HBAR · USDC (Base)</div>
        </div>
      </div>

      <div class="main">
        <div class="chart-row" style="display:grid;grid-template-columns:1fr 1fr;gap:var(--gap);">
          <div class="chart-card">
            <h3>Provider Trust Scores</h3>
            <canvas id="trust-chart"></canvas>
          </div>
          <div class="chart-card">
            <h3>Cost per Query (HBAR)</h3>
            <canvas id="cost-chart"></canvas>
          </div>
        </div>
        <div class="chart-card">
          <h3>Provider Performance Radar</h3>
          <canvas id="radar-chart" style="max-height:300px;"></canvas>
        </div>
        <div class="table-card">
          <div class="table-header">
            <h3>📦 Providers</h3>
            <div class="table-filters">
              <select id="filter-min-trust" onchange="applyTableFilter()">
                <option value="0">Min Trust: Any</option>
                <option value="70">Min Trust: ≥70</option>
                <option value="50">Min Trust: ≥50</option>
                <option value="30">Min Trust: ≥30</option>
              </select>
              <select id="filter-cost" onchange="applyTableFilter()">
                <option value="all">Any Price</option>
                <option value="low">≤ 0.3 HBAR</option>
                <option value="mid">≤ 0.5 HBAR</option>
                <option value="high">> 0.5 HBAR</option>
              </select>
            </div>
          </div>
          <div style="overflow-x:auto;">
            <table class="prov-table" id="prov-table">
              <thead>
                <tr>
                  <th onclick="sortTable('name')">Provider</th>
                  <th onclick="sortTable('trust_score')">Trust Score</th>
                  <th onclick="sortTable('cost_hbar')">Cost (HBAR)</th>
                  <th onclick="sortTable('staked_hbar')">Staked</th>
                  <th onclick="sortTable('success_rate')">Success</th>
                </tr>
              </thead>
              <tbody id="table-body"></tbody>
            </table>
          </div>
        </div>
      </div>

      <div class="sidebar-right">
        <div class="provider-list">
          <h3>🔌 Quick Access</h3>
          <div id="quick-providers"></div>
        </div>
        <div class="provider-list" id="a2a-stats" style="display:none;">
          <h3>🔄 A2A Protocol</h3>
          <div id="a2a-content"></div>
        </div>
        <div class="agent-list">
          <h3>🤖 Discovered Agents <span id="agent-count" style="color:var(--green);font-size:12px;"></span></h3>
          <div id="agent-items"><div style="color:var(--text-muted);font-size:12px;">Scanning HCS topics…</div></div>
        </div>
        <div class="topic-feed">
          <h3>📡 Live Topic Feed</h3>
          <div id="topic-items"><div style="color:var(--text-muted);font-size:12px;">Waiting for HCS messages…</div></div>
        </div>
      </div>
    </div>
  `;

  window._allProviders = providers;
  window._agents = data.agents || [];
  applyTableFilter();
  renderTrustChart(providers);
  renderCostChart(providers);
  renderRadarChart(providers);
  renderQuickProviders(providers);
  renderAgents(window._agents);
  renderA2AStats(data);
}

function renderTrustChart(providers) {
  const canvas = document.getElementById('trust-chart');
  if (!canvas) return;
  if (charts.trust) charts.trust.destroy();

  const labels = providers.map(p => p.name.split(' ')[0]);
  const scores = providers.map(p => p.trust_score || 0);
  const colors = scores.map(s => s >= 70 ? '#22c55e' : s >= 50 ? '#eab308' : '#ef4444');

  charts.trust = new Chart(canvas, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        data: scores,
        backgroundColor: colors.map(c => c + 'CC'),
        borderColor: colors,
        borderWidth: 1,
        borderRadius: 4,
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      indexAxis: 'y',
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: ctx => `Trust: ${ctx.parsed.x}/100` } }
      },
      scales: {
        x: { beginAtZero: true, max: 100, grid: { color: '#1e2a4544' } },
        y: { grid: { display: false } }
      }
    }
  });
}

function renderCostChart(providers) {
  const canvas = document.getElementById('cost-chart');
  if (!canvas) return;
  if (charts.cost) charts.cost.destroy();

  charts.cost = new Chart(canvas, {
    type: 'doughnut',
    data: {
      labels: providers.map(p => p.name),
      datasets: [{
        data: providers.map(p => p.cost_hbar),
        backgroundColor: ['#3b82f6CC', '#8b5cf6CC', '#06b6d4CC', '#22c55eCC', '#eab308CC'],
        borderColor: '#131b2e',
        borderWidth: 2,
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      cutout: '60%',
      plugins: {
        legend: { position: 'bottom', labels: { usePointStyle: true, padding: 8, color: '#7b8cae', font: { size: 10 } } },
        tooltip: { callbacks: { label: ctx => `${ctx.label}: ${ctx.parsed} HBAR` } }
      }
    }
  });
}

function renderRadarChart(providers) {
  const canvas = document.getElementById('radar-chart');
  if (!canvas) return;
  if (charts.radar) charts.radar.destroy();

  const labels = providers.map(p => p.name.split(' ')[0]);
  const trustScores = providers.map(p => (p.trust_score || 0) / 100);
  const successRates = providers.map(p => p.success_rate || 0);
  const stakedNorm = providers.map(p => Math.min((p.staked_hbar || 0) / 1000, 1));

  charts.radar = new Chart(canvas, {
    type: 'radar',
    data: {
      labels: ['Trust', 'Success Rate', 'Stake Ratio'],
      datasets: providers.slice(0, 4).map((p, i) => ({
        label: p.name.split(' ')[0],
        data: [
          (p.trust_score || 0) / 100,
          p.success_rate || 0,
          Math.min((p.staked_hbar || 0) / 1000, 1),
        ],
        borderColor: ['#3b82f6', '#8b5cf6', '#06b6d4', '#22c55e'][i],
        backgroundColor: ['#3b82f633', '#8b5cf633', '#06b6d433', '#22c55e33'][i],
        borderWidth: 2,
        pointRadius: 3,
      }))
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      scales: { r: { beginAtZero: true, max: 1, grid: { color: '#1e2a4544' } } },
      plugins: { legend: { position: 'bottom', labels: { usePointStyle: true, padding: 8, color: '#7b8cae', font: { size: 10 } } } }
    }
  });
}

function renderQuickProviders(providers) {
  const container = document.getElementById('quick-providers');
  if (!container) return;

  container.innerHTML = providers.map(p => {
    const ts = p.trust_score || 0;
    const color = ts >= 70 ? '#22c55e' : ts >= 50 ? '#eab308' : '#ef4444';
    return `<div class="provider-item">
      <div class="name">${p.name}</div>
      <div class="meta">
        <span>${p.cost_hbar} ℏ</span>
        <span style="color:${color}">${ts.toFixed(0)}</span>
      </div>
      <div class="mini-bar"><div class="mini-bar-fill" style="width:${ts}%;background:${color};"></div></div>
    </div>`;
  }).join('');
}

function renderA2AStats(data) {
  const el = document.getElementById('a2a-stats');
  const content = document.getElementById('a2a-content');
  if (!el || !content) return;
  const a2a = data.a2a;
  if (!a2a || !a2a.tasks_by_status || !Object.keys(a2a.tasks_by_status).length) {
    el.style.display = 'none';
    return;
  }
  el.style.display = 'block';
  const statusMap = a2a.tasks_by_status;
  const total = a2a.total_tasks || 0;
  const contexts = a2a.total_contexts || 0;
  const completed = statusMap.completed || 0;
  const failed = statusMap.failed || 0;
  const active = (statusMap.submitted || 0) + (statusMap.working || 0);
  const successRate = total > 0 ? ((completed / total) * 100).toFixed(0) : '—';
  content.innerHTML =
    '<div class="a2a-row"><span class="a2a-label">Tasks</span><span class="a2a-value">' + total + '</span></div>' +
    '<div class="a2a-row"><span class="a2a-label">Contexts</span><span class="a2a-value">' + contexts + '</span></div>' +
    '<div class="a2a-row"><span class="a2a-label">Active</span><span class="a2a-value" style="color:var(--yellow)">' + active + '</span></div>' +
    '<div class="a2a-row"><span class="a2a-label">Completed</span><span class="a2a-value" style="color:var(--green)">' + completed + '</span></div>' +
    '<div class="a2a-row"><span class="a2a-label">Success Rate</span><span class="a2a-value" style="color:var(--' + (successRate >= 80 ? 'green' : successRate >= 50 ? 'yellow' : 'red') + ')">' + successRate + '%</span></div>' +
    '<div style="margin-top:8px;font-size:11px;text-align:center"><a href="/dashboard/tasks" style="color:var(--blue)">Manage tasks →</a></div>';
}

let _sortCol = 'trust_score', _sortDir = 'desc';

function applyTableFilter() {
  const minTrust = parseInt(document.getElementById('filter-min-trust').value);
  const costFilter = document.getElementById('filter-cost').value;

  let filtered = window._allProviders.filter(p => {
    if (p.trust_score < minTrust) return false;
    if (costFilter === 'low' && p.cost_hbar > 0.3) return false;
    if (costFilter === 'mid' && p.cost_hbar > 0.5) return false;
    if (costFilter === 'high' && p.cost_hbar <= 0.5) return false;
    return true;
  });

  sortData(filtered);
}

function sortData(data) {
  const sorted = [...data].sort((a, b) => {
    let aVal = a[_sortCol] ?? 0, bVal = b[_sortCol] ?? 0;
    if (typeof aVal === 'string') aVal = aVal.toLowerCase();
    if (typeof bVal === 'string') bVal = bVal.toLowerCase();
    return aVal < bVal ? -1 : aVal > bVal ? 1 : 0;
  });
  if (_sortDir === 'desc') sorted.reverse();
  renderTable(sorted);
}

function sortTable(col) {
  if (_sortCol === col) _sortDir = _sortDir === 'asc' ? 'desc' : 'asc';
  else { _sortCol = col; _sortDir = 'desc'; }
  sortData(window._allProviders);
}

function renderTable(providers) {
  const tbody = document.getElementById('table-body');
  if (!tbody) return;

  tbody.innerHTML = providers.map(p => {
    const ts = p.trust_score || 0;
    const color = ts >= 70 ? 'var(--green)' : ts >= 50 ? 'var(--yellow)' : 'var(--red)';
    const barColor = ts >= 70 ? '#22c55e' : ts >= 50 ? '#eab308' : '#ef4444';
    return `<tr>
      <td><strong>${p.name}</strong><br><span style="font-size:11px;color:var(--text-muted);">${p.provider_id}</span></td>
      <td>
        <span style="color:${color};font-weight:600;">${ts.toFixed(0)}</span>
        <div class="score-bar" style="width:${ts}%;background:${barColor};"></div>
      </td>
      <td>${p.cost_hbar} ℏ</td>
      <td>${(p.staked_hbar || 0).toFixed(0)} ℏ</td>
      <td>${((p.success_rate || 0) * 100).toFixed(0)}%</td>
    </tr>`;
  }).join('');
}

function fmt(n) {
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
  if (n >= 1000) return (n / 1000).toFixed(1) + 'K';
  return n.toLocaleString();
}

async function fetchData() {
  try {
    const resp = await fetch('/dashboard/data');
    const data = await resp.json();
    initCharts();
    renderDashboard(data);
  } catch (e) {
    document.getElementById('dashboard-content').innerHTML =
      `<div class="loading" style="color:var(--red)">⚠️ Connection error (${e.message || 'unknown'})</div>`;
  }
}

function connectWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const ws = new WebSocket(`${protocol}//${window.location.host}/ws/dashboard`);

  ws.onopen = () => {
    console.log('WebSocket connected');
  };

  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data);
      if (msg.type === 'agent_heartbeat') {
        updateAgentPresence(msg.data.agent_id, 'online');
      } else if (msg.type === 'agent_discovered') {
        if (!window._agents) window._agents = [];
        const existing = window._agents.find(a => a.agent_id === msg.data.agent_id);
        if (!existing) {
          window._agents.push({
            agent_id: msg.data.agent_id,
            agent_name: msg.data.agent_name,
            description: msg.data.description,
            tags: msg.data.tags,
            presence: 'online',
            trust_score: 50,
            total_requests: 0,
            last_seen: new Date().toISOString(),
            heartbeat_count: 1,
          });
          renderAgents(window._agents);
        }
      } else if (msg.type === 'agent_directory_update') {
        console.log('Agent directory update:', msg.data);
      }
    } catch (e) {
      console.error('WebSocket message error:', e);
    }
  };

  ws.onclose = () => {
    console.log('WebSocket disconnected, reconnecting in 5s…');
    setTimeout(connectWebSocket, 5000);
  };

  ws.onerror = (e) => {
    console.error('WebSocket error:', e);
  };

  setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send('ping');
    }
  }, 30000);
}

fetchData();
setInterval(fetchData, 10000);
connectWebSocket();
</script>
</body>
</html>"""


def _collect_dashboard_data(request: Request) -> dict:
    settings = getattr(request.app.state, "settings", None)
    provider_registry = getattr(request.app.state, "provider_registry", None)
    agent_registry = getattr(request.app.state, "agent_registry", None)

    providers = []
    if provider_registry:
        for p in provider_registry.list_all():
            r = p.reputation
            providers.append({
                "provider_id": p.provider_id,
                "name": p.name,
                "cost_hbar": p.cost_hbar,
                "trust_score": round(r.trust_score, 1),
                "staked_hbar": r.staked_hbar,
                "success_rate": round(r.successful_requests / r.total_requests, 3) if r.total_requests > 0 else 1.0,
                "total_requests": r.total_requests,
            })

    agents = []
    if agent_registry:
        discovered = agent_registry.get_discovered_agents()
        for a in discovered:
            agents.append({
                "agent_id": a.agent_id,
                "agent_name": a.agent_name,
                "description": a.description,
                "tags": a.tags,
                "presence": a.presence,
                "trust_score": a.trust_score,
                "total_requests": a.total_requests,
                "last_seen": a.last_seen,
                "heartbeat_count": a.heartbeat_count,
            })

    return {
        "version": getattr(settings, "agent_version", "?"),
        "total_requests": getattr(agent_registry, "_total_requests_served", 0) if agent_registry else 0,
        "providers": providers,
        "agents": agents,
        "agent_stats": {
            "total_agents": len(agents),
            "online_agents": sum(1 for a in agents if a["presence"] == "online"),
            "offline_agents": sum(1 for a in agents if a["presence"] == "offline"),
        },
    }


@router.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def get_dashboard():
    return HTMLResponse(DASHBOARD_HTML)


@router.get("/dashboard/data", include_in_schema=False)
async def get_dashboard_data(request: Request):
    try:
        data = _collect_dashboard_data(request)
        # Add A2A task stats
        from api.routes.tasks import get_mgr, get_ctx
        try:
            mgr = get_mgr()
            ctx = get_ctx()
            all_tasks = mgr.list_tasks(limit=1000)
            data["a2a"] = {
                "tasks_by_status": mgr.count_by_status(),
                "total_tasks": len(all_tasks),
                "total_contexts": len(ctx.list_contexts()),
            }
        except Exception:
            data["a2a"] = {"tasks_by_status": {}, "total_tasks": 0, "total_contexts": 0}
        return JSONResponse(data)
    except Exception as e:
        return JSONResponse({"error": str(e)})


@router.get("/dashboard/tasks", response_class=HTMLResponse, include_in_schema=False)
async def get_tasks_dashboard():
    return HTMLResponse(TASKS_HTML)


@router.get("/dashboard/tasks/data", include_in_schema=False)
async def get_tasks_data():
    from api.routes.tasks import get_mgr, get_ctx
    mgr = get_mgr()
    ctx = get_ctx()
    try:
        tasks = mgr.list_tasks(limit=30)
        contexts = ctx.list_contexts(limit=20)
        return JSONResponse({
            "tasks": [t.model_dump(mode="json") for t in tasks],
            "counts": mgr.count_by_status(),
            "contexts": [c.model_dump(mode="json") for c in contexts],
            "task_count": len(tasks),
            "context_count": len(contexts),
        })
    except Exception as e:
        return JSONResponse({"error": str(e)})


ORACLE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>HashA2A — Oracle Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.5.1"></script>
<style>
:root { --bg:#0b1120;--card:#131b2e;--border:#1e2a45;--text:#e8edf5;--muted:#7b8cae;--blue:#3b82f6;--purple:#8b5cf6;--green:#22c55e;--yellow:#eab308;--red:#ef4444;--radius:12px;--gap:16px; }
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--bg);color:var(--text);font-family:'Inter',system-ui,sans-serif;padding:24px}
.header{display:flex;justify-content:space-between;align-items:center;margin-bottom:24px;flex-wrap:wrap;gap:12px}
.header h1{font-size:24px;font-weight:700}
.header h1 span{color:var(--blue)}
.badge{background:rgba(59,130,246,0.12);color:var(--blue);padding:4px 12px;border-radius:999px;font-size:13px}
.chart-row{display:grid;grid-template-columns:2fr 1fr;gap:var(--gap);margin-bottom:var(--gap)}
@media(max-width:900px){.chart-row{grid-template-columns:1fr}}
.chart-card{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:20px}
.chart-card h3{font-size:13px;font-weight:600;color:var(--muted);margin-bottom:12px}
.chart-card canvas{max-height:200px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(420px,1fr));gap:var(--gap)}
.card{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:20px}
.card .asset-title{font-size:18px;font-weight:700;margin-bottom:8px}
.oracle-row{display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid rgba(30,42,69,0.5);font-size:14px;align-items:center}
.oracle-row:last-child{border-bottom:none}
.oracle-name{color:var(--muted)}
.oracle-price{font-weight:600}
.confidence-dot{width:8px;height:8px;border-radius:50%;display:inline-block;margin-right:6px}
.spread{margin-top:12px;padding:8px 12px;border-radius:8px;font-size:13px;display:flex;justify-content:space-between}
.spread-high{background:rgba(34,197,94,0.1);color:var(--green);border:1px solid rgba(34,197,94,0.2)}
.spread-medium{background:rgba(234,179,8,0.1);color:var(--yellow);border:1px solid rgba(234,179,8,0.2)}
.spread-low{background:rgba(123,140,174,0.1);color:var(--muted);border:1px solid rgba(30,42,69,0.5)}
.footer{text-align:center;margin-top:24px;font-size:12px;color:var(--muted)}
.loading{text-align:center;padding:40px;color:var(--muted)}
</style>
</head>
<body>
<div class="header">
  <h1>🔮 <span>HashA2A</span> Oracle Dashboard</h1>
  <div style="display:flex;gap:12px;align-items:center">
    <span class="badge" id="status-badge">Loading...</span>
    <span class="badge" id="history-count" style="background:rgba(139,92,246,0.12);color:var(--purple)">0 snapshots</span>
  </div>
</div>

<div class="chart-row">
  <div class="chart-card">
    <h3>📈 Spread History (last 20 snapshots)</h3>
    <canvas id="spread-chart"></canvas>
  </div>
  <div class="chart-card">
    <h3>📊 Sources per Asset</h3>
    <canvas id="sources-chart"></canvas>
  </div>
</div>

<div class="grid" id="oracle-grid">
  <div class="loading" style="grid-column:1/-1;">Fetching live oracle data...</div>
</div>
<div class="footer">Auto-refreshes every 30s · Data from Pyth · CoinGecko · DeFiLlama · Spread history stored locally</div>

<script>
const SPREAD_KEY = 'hasha2a_spread_history';
const MAX_HISTORY = 20;
let spreadChart = null;
let sourcesChart = null;

function loadHistory() {
  try { return JSON.parse(localStorage.getItem(SPREAD_KEY) || '[]'); } catch(e) { return []; }
}

function saveHistory(history) {
  localStorage.setItem(SPREAD_KEY, JSON.stringify(history));
}

function updateCharts(assets) {
  const history = loadHistory();
  const now = new Date().toLocaleTimeString();
  const snapshot = { time: now };
  for (const [asset, info] of Object.entries(assets)) {
    snapshot[asset] = info.spread_pct;
  }
  history.push(snapshot);
  if (history.length > MAX_HISTORY) history.shift();
  saveHistory(history);
  document.getElementById('history-count').textContent = history.length + ' snapshots';

  const labels = history.map(h => h.time);
  const datasets = Object.keys(assets).map((asset, i) => ({
    label: asset,
    data: history.map(h => h[asset] || 0),
    borderColor: ['#3b82f6','#8b5cf6','#22c55e','#06b6d4','#eab308','#ef4444'][i],
    backgroundColor: ['#3b82f633','#8b5cf633','#22c55e33','#06b6d433','#eab30833','#ef444433'][i],
    borderWidth: 2,
    pointRadius: 2,
    tension: 0.3,
  }));

  if (spreadChart) { spreadChart.destroy(); }
  const ctx = document.getElementById('spread-chart').getContext('2d');
  spreadChart = new Chart(ctx, {
    type: 'line', data: { labels, datasets },
    options: {
      responsive: true, maintainAspectRatio: false,
      scales: {
        x: { ticks: { color: '#7b8cae', font: { size: 10 } } },
        y: { ticks: { color: '#7b8cae', font: { size: 10 }, callback: v => v + '%' } }
      },
      plugins: { legend: { position: 'bottom', labels: { color: '#7b8cae', usePointStyle: true, padding: 8, font: { size: 10 } } } }
    }
  });

  if (sourcesChart) { sourcesChart.destroy(); }
  const srcCtx = document.getElementById('sources-chart').getContext('2d');
  const srcLabels = Object.keys(assets);
  const srcData = Object.values(assets).map(a => a.prices.length);
  sourcesChart = new Chart(srcCtx, {
    type: 'bar', data: { labels: srcLabels, datasets: [{ label: 'Oracle Sources', data: srcData, backgroundColor: ['#3b82f6','#8b5cf6','#22c55e','#06b6d4','#eab308','#ef4444'] }] },
    options: {
      responsive: true, maintainAspectRatio: false,
      scales: { y: { ticks: { color: '#7b8cae', font: { size: 10 }, stepSize: 1 } } },
      plugins: { legend: { display: false } }
    }
  });
}

async function fetchData() {
  const badge = document.getElementById('status-badge');
  const grid = document.getElementById('oracle-grid');
  try {
    badge.textContent = '⏳ Fetching...';
    const resp = await fetch('/dashboard/oracles/data');
    const data = await resp.json();
    if (data.error) { badge.textContent = '⚠ Error'; return; }
    badge.textContent = data.count + ' assets · ' + new Date().toLocaleTimeString();
    updateCharts(data.assets);
    grid.innerHTML = Object.entries(data.assets).map(([asset, info]) => {
      const sc = info.opportunity === 'high' ? 'spread-high' : info.opportunity === 'medium' ? 'spread-medium' : 'spread-low';
      return '<div class="card"><div class="asset-title">' + asset + '</div>' +
        info.prices.map(p => '<div class="oracle-row"><span class="oracle-name"><span class="confidence-dot" style="background:' + (p.confidence > 0.5 ? 'var(--green)' : p.confidence > 0.2 ? 'var(--yellow)' : 'var(--red)') + '"></span>' + p.source_name + '</span><span class="oracle-price">$' + p.price.toFixed(2) + '</span></div>').join('') +
        '<div class="spread ' + sc + '"><span>Spread</span><span><strong>' + info.spread_pct + '%</strong> · ' + info.opportunity + '</span></div></div>';
    }).join('');
  } catch(e) {
    grid.innerHTML = '<div class="loading" style="grid-column:1/-1;">Connection error. Retrying...</div>';
    badge.textContent = '⚠ Offline';
  }
}
fetchData();
setInterval(fetchData, 30000);
</script>
</body>
</html>"""


TASKS_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>HashA2A — Task Dashboard</title>
<style>
:root{--bg:#0b1120;--card:#131b2e;--border:#1e2a45;--text:#e8edf5;--muted:#7b8cae;--blue:#3b82f6;--purple:#8b5cf6;--green:#22c55e;--yellow:#eab308;--red:#ef4444;--radius:12px;--gap:16px}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--bg);color:var(--text);font-family:'Inter',system-ui,sans-serif;padding:24px}
.header{display:flex;justify-content:space-between;align-items:center;margin-bottom:24px;flex-wrap:wrap;gap:16px}
.header h1{font-size:24px;font-weight:700}
.header h1 span{color:var(--blue)}
.badge{background:rgba(59,130,246,0.12);color:var(--blue);padding:4px 12px;border-radius:999px;font-size:13px}
.kpi-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:var(--gap);margin-bottom:var(--gap)}
.kpi{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:16px 20px;text-align:center}
.kpi .num{font-size:28px;font-weight:800}
.kpi .label{font-size:12px;color:var(--muted);margin-top:4px}
.kpi .sub{font-size:11px;color:var(--muted);margin-top:2px}
.grid{display:grid;grid-template-columns:2fr 1fr;gap:var(--gap)}
@media(max-width:900px){.grid{grid-template-columns:1fr}}
.card{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:20px}
.card h3{font-size:14px;font-weight:600;color:var(--muted);margin-bottom:12px}
.task-row{display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid rgba(30,42,69,0.5);font-size:13px;align-items:center;cursor:pointer;transition:background .1s}
.task-row:hover{background:rgba(59,130,246,0.04)}
.task-row:last-child{border-bottom:none}
.task-id{color:var(--muted);font-family:monospace;font-size:11px}
.task-status{padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600}
.status-submitted{background:rgba(59,130,246,0.1);color:var(--blue)}
.status-working{background:rgba(234,179,8,0.1);color:var(--yellow)}
.status-completed{background:rgba(34,197,94,0.1);color:var(--green)}
.status-failed{background:rgba(239,68,68,0.1);color:var(--red)}
.status-input-required{background:rgba(139,92,246,0.1);color:var(--purple)}
.ctx-row{padding:8px 0;border-bottom:1px solid rgba(30,42,69,0.5);font-size:12px}
.ctx-row:last-child{border-bottom:none}
.ctx-id{color:var(--muted);font-family:monospace;font-size:11px}
.ctx-count{color:var(--green);font-weight:600}
.detail-panel{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:20px;margin-top:var(--gap);display:none}
.detail-panel.open{display:block}
.detail-row{display:flex;padding:6px 0;font-size:13px;border-bottom:1px solid rgba(30,42,69,0.3)}
.detail-label{color:var(--muted);width:100px;flex-shrink:0}
.detail-value{color:var(--text)}
.footer{text-align:center;margin-top:24px;font-size:12px;color:var(--muted)}
</style>
</head>
<body>
<div class="header">
  <h1>📋 <span>HashA2A</span> Task Dashboard</h1>
  <span class="badge" id="status-badge">Loading...</span>
</div>
<div class="kpi-row" id="kpi-row"></div>
<div class="grid">
  <div>
    <div class="card">
      <h3>📌 Recent Tasks</h3>
      <div id="task-list">Loading...</div>
    </div>
    <div class="detail-panel" id="detail-panel">
      <h3 style="margin-bottom:12px">📄 Task Detail</h3>
      <div id="detail-content"></div>
    </div>
  </div>
  <div>
    <div class="card">
      <h3>🧠 Context Activity</h3>
      <div id="ctx-list">Loading...</div>
    </div>
  </div>
</div>
<div class="footer">Auto-refreshes every 15s · A2A Tasks API</div>
<script>
async function fetchData() {
  try {
    const resp = await fetch('/dashboard/tasks/data');
    const data = await resp.json();
    if (data.error) { document.getElementById('status-badge').textContent = 'Error'; return; }
    document.getElementById('status-badge').textContent = data.task_count + ' tasks · ' + data.context_count + ' contexts · ' + new Date().toLocaleTimeString();

    const kpi = document.getElementById('kpi-row');
    kpi.innerHTML = Object.entries(data.counts).map(([s, c]) =>
      `<div class="kpi"><div class="num" style="color:var(--${s === 'completed' ? 'green' : s === 'failed' ? 'red' : s === 'working' ? 'yellow' : s === 'input-required' ? 'purple' : 'blue'})">${c}</div><div class="label">${s}</div></div>`
    ).join('');

    const taskList = document.getElementById('task-list');
    taskList.innerHTML = data.tasks.map(t => {
      const sClass = 'status-' + t.status;
      return '<div class="task-row" onclick="showDetail(\'' + t.task_id + '\')"><span class="task-id">' + t.task_id.substring(0, 16) + '...</span><span class="task-status ' + sClass + '">' + t.status + '</span><span style="color:var(--muted);font-size:11px">' + t.parts.length + ' parts</span></div>';
    }).join('') || '<div style="color:var(--muted);font-size:13px;padding:12px 0">No tasks yet. Create one via API.</div>';

    const ctxList = document.getElementById('ctx-list');
    ctxList.innerHTML = data.contexts.map(c => {
      const desc = c.summary ? c.summary.substring(0, 60) + '...' : 'No activity';
      return '<div class="ctx-row"><span class="ctx-id">' + c.context_id.substring(0, 16) + '...</span><span class="ctx-count">' + c.interaction_count + ' interactions</span><div style="color:var(--muted);font-size:11px;margin-top:2px">' + desc + '</div></div>';
    }).join('') || '<div style="color:var(--muted);font-size:13px;padding:12px 0">No contexts yet.</div>';

    window._tasks = data.tasks;
    window._contexts = data.contexts;
  } catch(e) {
    document.getElementById('status-badge').textContent = 'Offline';
  }
}

function showDetail(taskId) {
  const panel = document.getElementById('detail-panel');
  const content = document.getElementById('detail-content');
  const task = window._tasks ? window._tasks.find(t => t.task_id === taskId) : null;
  if (!task) return;
  panel.classList.add('open');
  content.innerHTML = [
    '<div class="detail-row"><span class="detail-label">Task ID</span><span class="detail-value" style="font-family:monospace;font-size:11px">' + task.task_id + '</span></div>',
    '<div class="detail-row"><span class="detail-label">Status</span><span class="detail-value"><span class="task-status status-' + task.status + '">' + task.status + '</span></span></div>',
    '<div class="detail-row"><span class="detail-label">Context</span><span class="detail-value" style="font-family:monospace;font-size:11px">' + (task.context_id || 'none') + '</span></div>',
    '<div class="detail-row"><span class="detail-label">Parts</span><span class="detail-value">' + task.parts.length + ' parts</span></div>',
    '<div class="detail-row"><span class="detail-label">Artifacts</span><span class="detail-value">' + task.artifacts.length + ' files</span></div>',
    task.context_id ? '<div style="margin-top:12px"><a href="/api/v1/tasks/context/' + task.context_id + '/history" target="_blank" style="color:var(--blue);font-size:13px">View context history →</a></div>' : '',
  ].join('');
  if (task.parts.length) {
    content.innerHTML += '<div style="margin-top:12px;font-size:12px;color:var(--muted)">Last part: ' + task.parts[task.parts.length - 1].text?.substring(0, 120) + '</div>';
  }
}

fetchData();
setInterval(fetchData, 15000);
</script>
</body>
</html>"""


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def get_landing():
    return HTMLResponse(LANDING_HTML)


@router.get("/landing/data", include_in_schema=False)
async def get_landing_data():
    from core.oracle_hub import OracleHub
    hub = OracleHub()
    try:
        import asyncio
        prices = await hub.get_price("BTC/USD")
        await hub.close()
        if prices:
            return JSONResponse({
                "prices": [p.to_dict() for p in prices],
                "oracles": len(prices),
            })
        return JSONResponse({"prices": [], "oracles": 0})
    except Exception as e:
        await hub.close()
        return JSONResponse({"error": str(e)})


LANDING_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>HashA2A — Agent-to-Agent Intelligence Layer | Data Marketplace for AI Agents</title>
<meta name="description" content="A decentralized data marketplace where AI agents discover, purchase, and consume verified multi-oracle intelligence. Pay per query via HBAR (HIP-991) or USDC (x402).">
<meta name="robots" content="index, follow">
<link rel="canonical" href="https://github.com/ymiydev-prog/HashA2A">
<!-- Open Graph -->
<meta property="og:title" content="HashA2A — Agent-to-Agent Intelligence Layer">
<meta property="og:description" content="Buy verified multi-oracle intelligence with HBAR or USDC. AI agent data marketplace on Hedera.">
<meta property="og:type" content="website">
<meta property="og:url" content="https://github.com/ymiydev-prog/HashA2A">
<meta property="og:image" content="/og-image.png">
<!-- Twitter Card -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="HashA2A — A2A Intelligence Layer">
<meta name="twitter:description" content="Decentralized data marketplace for AI agents. OracleHub + Arbitrage + Deep Research.">
<!-- Structured Data -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "HashA2A",
  "applicationCategory": "Data Marketplace",
  "description": "Agent-to-Agent Intelligence Layer on Hedera. AI agents buy processed data via HBAR micropayments.",
  "url": "https://github.com/ymiydev-prog/HashA2A",
  "operatingSystem": "Linux, macOS, Docker",
  "offers": {
    "@type": "Offer",
    "price": "0.25",
    "priceCurrency": "USD"
  }
}
</script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
:root {
  --bg: #0b1120; --card: #131b2e; --border: #1e2a45;
  --text: #e8edf5; --muted: #7b8cae;
  --blue: #3b82f6; --purple: #8b5cf6; --green: #22c55e; --cyan: #06b6d4;
  --radius: 12px; --gap: 16px;
}
body { background: var(--bg); color: var(--text); font-family: 'Inter', system-ui, sans-serif; }
a { color: var(--blue); text-decoration: none; }
a:focus { outline: 2px solid var(--blue); outline-offset: 2px; }
button:focus, [tabindex]:focus { outline: 2px solid var(--purple); outline-offset: 2px; }
:focus:not(:focus-visible) { outline: none; }
:focus-visible { outline: 2px solid var(--blue); outline-offset: 2px; }
.skip-link { position: absolute; top: -40px; left: 0; background: var(--blue); color: white; padding: 8px 16px; z-index: 100; transition: top 0.2s; }
.skip-link:focus { top: 0; }
.visually-hidden { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0,0,0,0); white-space: nowrap; border: 0; }
.container { max-width: 1200px; margin: 0 auto; padding: 0 24px; }

/* Nav */
.nav { display: flex; justify-content: space-between; align-items: center; padding: 20px 0; border-bottom: 1px solid var(--border); }
.nav-logo { font-size: 22px; font-weight: 800; }
.nav-logo span:first-child { color: var(--blue); }
.nav-logo span:last-child { color: var(--purple); }
.nav-links { display: flex; gap: 24px; align-items: center; }
.nav-links a { font-size: 14px; color: var(--muted); transition: color 0.2s; }
.nav-links a:hover { color: var(--text); }
.nav-btn { background: linear-gradient(135deg, var(--blue), var(--purple)); color: white !important; padding: 8px 20px; border-radius: 8px; font-weight: 600; font-size: 13px !important; }

/* Hero */
.hero { padding: 80px 0 60px; text-align: center; position: relative; overflow: hidden; }
.hero-bg { position: absolute; inset: 0; background: radial-gradient(ellipse at 50% 0%, rgba(59,130,246,0.08) 0%, transparent 60%), radial-gradient(ellipse at 80% 50%, rgba(139,92,246,0.06) 0%, transparent 50%); pointer-events: none; }
.hero h1 { font-size: 56px; font-weight: 800; line-height: 1.15; letter-spacing: -0.02em; position: relative; }
.hero h1 .accent { background: linear-gradient(135deg, var(--blue), var(--purple)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.hero p { font-size: 20px; color: var(--muted); margin-top: 20px; max-width: 600px; margin-left: auto; margin-right: auto; line-height: 1.6; position: relative; }
.hero-btns { display: flex; gap: 16px; justify-content: center; margin-top: 32px; position: relative; }
.hero-btn { padding: 14px 32px; border-radius: 10px; font-size: 15px; font-weight: 600; transition: all 0.2s; }
.hero-btn-primary { background: linear-gradient(135deg, var(--blue), var(--purple)); color: white; }
.hero-btn-primary:hover { transform: translateY(-2px); box-shadow: 0 8px 30px rgba(59,130,246,0.3); }
.hero-btn-secondary { background: var(--card); color: var(--text); border: 1px solid var(--border); }
.hero-btn-secondary:hover { border-color: var(--blue); }

/* Video */
.video-section { padding: 0 0 60px; text-align: center; }
.video-container { max-width: 800px; margin: 0 auto; border-radius: var(--radius); overflow: hidden; border: 1px solid var(--border); background: var(--card); }
.video-container video { width: 100%; display: block; }

/* Section titles */
.section-title { font-size: 32px; font-weight: 700; text-align: center; margin-bottom: 8px; }
.section-sub { font-size: 16px; color: var(--muted); text-align: center; margin-bottom: 48px; }

/* Features */
.features { padding: 60px 0; }
.features-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: var(--gap); }
.feature-card { background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); padding: 32px 24px; transition: all 0.2s; }
.feature-card:hover { border-color: var(--blue); transform: translateY(-2px); }
.feature-icon { font-size: 32px; margin-bottom: 16px; }
.feature-card h3 { font-size: 18px; font-weight: 600; margin-bottom: 8px; }
.feature-card p { font-size: 14px; color: var(--muted); line-height: 1.6; }

/* Live Data */
.live-data { padding: 60px 0; }
.live-card { background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); padding: 32px; text-align: center; max-width: 500px; margin: 0 auto; }
.live-label { font-size: 13px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.1em; }
.live-price { font-size: 48px; font-weight: 800; margin: 8px 0; }
.live-price .currency { font-size: 24px; color: var(--muted); }
.live-sources { display: flex; justify-content: center; gap: 16px; margin-top: 12px; font-size: 12px; color: var(--muted); }
.live-source { display: flex; align-items: center; gap: 4px; }
.live-dot { width: 6px; height: 6px; border-radius: 50%; display: inline-block; }
.live-dot.online { background: var(--green); }
.live-refresh { font-size: 12px; color: var(--muted); margin-top: 12px; }

/* Pricing */
.pricing { padding: 60px 0; }
.pricing-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: var(--gap); }
.pricing-card { background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); padding: 24px; text-align: center; }
.pricing-card.featured { border-color: var(--blue); position: relative; }
.pricing-card.featured::before { content: 'Best Seller'; position: absolute; top: -10px; left: 50%; transform: translateX(-50%); background: linear-gradient(135deg, var(--blue), var(--purple)); padding: 4px 16px; border-radius: 999px; font-size: 11px; font-weight: 600; color: white; }
.pricing-name { font-size: 16px; font-weight: 600; margin-bottom: 4px; }
.pricing-desc { font-size: 12px; color: var(--muted); margin-bottom: 16px; }
.pricing-amount { font-size: 28px; font-weight: 800; }
.pricing-hbar { color: var(--blue); font-size: 16px; margin-top: 4px; }
.pricing-hbar { color: var(--blue); }
.pricing-usdc { color: var(--green); margin-top: 4px; font-size: 14px; }
.pricing-row { display: flex; justify-content: space-between; padding: 8px 0; font-size: 13px; border-bottom: 1px solid rgba(30,42,69,0.5); }
.pricing-row:last-child { border-bottom: none; }
.pricing-row .label { color: var(--muted); }
.pricing-row .value { color: var(--text); font-weight: 500; }

/* Integration */
.integrate { padding: 60px 0; }
.integrate-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: var(--gap); }
.integrate-card { background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; }
.integrate-header { padding: 16px 20px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; }
.integrate-header h3 { font-size: 14px; font-weight: 600; }
.integrate-badge { font-size: 11px; padding: 2px 8px; border-radius: 4px; background: rgba(59,130,246,0.1); color: var(--blue); }
.integrate-body { padding: 16px 20px; }
.integrate-body pre { font-size: 12px; color: var(--muted); line-height: 1.7; overflow-x: auto; font-family: 'JetBrains Mono', 'Fira Code', monospace; }
.integrate-body code { color: var(--cyan); }

/* Footer */
.footer { border-top: 1px solid var(--border); padding: 40px 0; margin-top: 60px; }
.footer-grid { display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 40px; }
.footer-brand h3 { font-size: 18px; font-weight: 700; }
.footer-brand h3 span:first-child { color: var(--blue); }
.footer-brand h3 span:last-child { color: var(--purple); }
.footer-brand p { font-size: 13px; color: var(--muted); margin-top: 8px; max-width: 300px; line-height: 1.6; }
.footer-col h4 { font-size: 13px; font-weight: 600; color: var(--text); margin-bottom: 16px; text-transform: uppercase; letter-spacing: 0.05em; }
.footer-col a { display: block; font-size: 13px; color: var(--muted); margin-bottom: 10px; transition: color 0.2s; }
.footer-col a:hover { color: var(--text); }
.footer-bottom { border-top: 1px solid var(--border); margin-top: 32px; padding-top: 24px; display: flex; justify-content: space-between; align-items: center; font-size: 13px; color: var(--muted); }
.footer-social { display: flex; gap: 16px; }
.footer-social a { display: flex; align-items: center; gap: 6px; font-size: 13px; color: var(--muted); transition: color 0.2s; }
.footer-social a:hover { color: var(--text); }

@media (max-width: 768px) {
  .hero h1 { font-size: 32px; }
  .hero p { font-size: 16px; }
  .footer-grid { grid-template-columns: 1fr; gap: 24px; }
  .footer-bottom { flex-direction: column; gap: 12px; text-align: center; }
  .integrate-grid { grid-template-columns: 1fr; }
}
</style>
</head>
<body>
<a href="#main-content" class="skip-link">Skip to main content</a>
<header role="banner">
<div class="nav" role="navigation" aria-label="Main navigation">
  <div class="container" style="display:flex;justify-content:space-between;align-items:center;width:100%;">
    <div class="nav-logo"><span>Hash</span><span>A2A</span></div>
    <div class="nav-links">
      <a href="#features">Features</a>
      <a href="#pricing">Pricing</a>
      <a href="#integrate">Integrate</a>
      <a href="https://github.com/ymiydev-prog/HashA2A" aria-label="View source on GitHub">GitHub</a>
      <a href="/dashboard" class="nav-btn">Dashboard</a>
    </div>
  </div>
</div>
</header>

<main id="main-content" role="main">

<section class="hero" aria-label="Hero banner">
  <div class="hero-bg" aria-hidden="true"></div>
  <div class="container">
    <h1>Buy Verified Intelligence<br/>with <span class="accent">HBAR or USDC</span></h1>
    <p>HashA2A is a decentralized data marketplace where AI agents discover, purchase, and consume verified multi-oracle intelligence — powered by Hedera HCS, the A2A protocol, and the x402 payment standard.</p>
    <div class="hero-btns">
      <a href="#integrate" class="hero-btn hero-btn-primary">Integrate Your Agent →</a>
      <a href="/dashboard" class="hero-btn hero-btn-secondary">Live Dashboard</a>
    </div>
  </div>
</section>

<section class="video-section" aria-label="Promotional video">
  <div class="container">
    <div class="video-container">
      <video controls poster="" preload="metadata" playsinline aria-label="HashA2A promotional video">
        <source src="/promo.mp4" type="video/mp4">
      </video>
    </div>
  </div>
</section>

<section class="features" id="features" aria-label="Features overview">
  <div class="container">
    <h2 class="section-title">Everything AI Agents Need</h2>
    <p class="section-sub">Real-time, cross-verified, cryptographically provable data</p>
    <div class="features-grid">
      <div class="feature-card">
        <div class="feature-icon">🔮</div>
        <h3>OracleHub</h3>
        <p>Multi-oracle price aggregation from Pyth, CoinGecko, and Chainlink (via DeFiLlama). 19 assets: crypto, gold, silver, forex. Median-price with IQR confidence scoring.</p>
      </div>
      <div class="feature-card">
        <div class="feature-icon">📊</div>
        <h3>Arbitrage Engine</h3>
        <p>Real-time cross-oracle spread detection across 6+ assets. Buy from the cheapest oracle, sell to the most expensive. Identifies profitable opportunities instantly.</p>
      </div>
      <div class="feature-card">
        <div class="feature-icon">🔄</div>
        <h3>A2A Protocol</h3>
        <p>Full Google A2A compliance: JSON-RPC 2.0, SSE streaming, task lifecycle (7 states), context passing, artifact storage, AP2 mandates, and JWT auth.</p>
      </div>
      <div class="feature-card">
        <div class="feature-icon">🧠</div>
        <h3>Deep Research</h3>
        <p>Web search + news + social signals + prediction market data combined with AI analysis (GPT-5-nano). Premium intelligence delivered via A2A tasks.</p>
      </div>
      <div class="feature-card">
        <div class="feature-icon">🔐</div>
        <h3>Auth + Payments</h3>
        <p>Ephemeral JWT tokens, AP2 cryptographic mandates with spending limits. Pay per query via USDC (x402), HBAR (HIP-991), or pre-authorized budgets.</p>
      </div>
      <div class="feature-card">
        <div class="feature-icon">🔌</div>
        <h3>MCP + A2A + REST</h3>
        <p>10 MCP tools, Google A2A JSON-RPC, SSE streaming, REST API, WebSocket. Works with Claude, Cursor, LangChain, and any A2A-compatible agent.</p>
      </div>
    </div>
  </div>
</section>

<section class="live-data" aria-label="Live oracle data">
  <div class="container" style="text-align:center;">
    <h2 class="section-title">Live Oracle Data</h2>
    <p class="section-sub">Real-time BTC/USD cross-verified across multiple oracles</p>
    <div class="live-card">
      <div class="live-label">BTC / USD</div>
      <div class="live-price"><span id="btc-price">—</span> <span class="currency">USD</span></div>
      <div class="live-sources" id="btc-sources"></div>
      <div class="live-refresh" id="btc-refresh">Fetching live data...</div>
    </div>
  </div>
</section>

 <section class="pricing" id="pricing" aria-label="Pricing plans">
   <div class="container">
     <h2 class="section-title">Pay Per Query</h2>
     <p class="section-sub">USDC prices are fixed. HBAR updates in real-time with the market.</p>
     <div class="pricing-grid">
       <div class="pricing-card" data-usdc="0.25" data-key="price_feed">
         <div class="pricing-name">Price Feed</div>
         <div class="pricing-desc">Single asset, multi-oracle</div>
         <div class="pricing-amount pricing-usdc">$0.25 USDC</div>
         <div class="pricing-hbar" id="hbar-price_feed">~ — HBAR</div>
       </div>
       <div class="pricing-card featured" data-usdc="0.50" data-key="arbitrage_scan">
         <div class="pricing-name">Arbitrage Scan</div>
         <div class="pricing-desc">All assets, ranked by spread</div>
         <div class="pricing-amount pricing-usdc">$0.50 USDC</div>
         <div class="pricing-hbar" id="hbar-arbitrage_scan">~ — HBAR</div>
       </div>
       <div class="pricing-card" data-usdc="0.50" data-key="deep_research">
         <div class="pricing-name">Deep Research</div>
         <div class="pricing-desc">Web + news + AI analysis</div>
         <div class="pricing-amount pricing-usdc">$0.50 USDC</div>
         <div class="pricing-hbar" id="hbar-deep_research">~ — HBAR</div>
       </div>
       <div class="pricing-card" data-usdc="0.15" data-key="prediction_market">
         <div class="pricing-name">Predictions</div>
         <div class="pricing-desc">Per provider query</div>
         <div class="pricing-amount pricing-usdc">$0.15 USDC</div>
         <div class="pricing-hbar" id="hbar-prediction_market">~ — HBAR</div>
       </div>
     </div>
     <p style="text-align:center;color:var(--muted);font-size:13px;margin-top:16px;" id="rate-info">Loading live HBAR rate...</p>
   </div>
 </section>

<section class="integrate" id="integrate" aria-label="Integration guide">
  <div class="container">
    <h2 class="section-title">Start in 30 Seconds</h2>
    <p class="section-sub">Three ways to integrate HashA2A into your agent</p>
    <div class="integrate-grid">
      <div class="integrate-card">
        <div class="integrate-header"><h3>MCP (Recommended)</h3><span class="integrate-badge">Agents</span></div>
        <div class="integrate-body">
<pre>{
  "mcpServers": {
    "hasha2a": {
      "url": "http://localhost:8080/mcp"
    }
  }
}

# 10 tools: get_price, scan_arbitrage,
# list_providers, deep_research, and more</pre>
        </div>
      </div>
      <div class="integrate-card">
        <div class="integrate-header"><h3>REST API</h3><span class="integrate-badge">Universal</span></div>
        <div class="integrate-body">
<pre><code>curl -X POST</code> http://localhost:8080/api/v1/feeds/prices \
  -H <code>"Content-Type: application/json"</code> \
  -d <code>'{"asset":"BTC/USD"}'</code>

<code>curl -X POST</code> http://localhost:8080/api/v1/requests \
  -H <code>"Content-Type: application/json"</code> \
  -d <code>'{"provider_id":"polymarket"}'</code></pre>
        </div>
      </div>
      <div class="integrate-card">
        <div class="integrate-header"><h3>A2A JSON-RPC 2.0</h3><span class="integrate-badge">Standard</span></div>
        <div class="integrate-body">
<pre><code>POST /api/v1/a2a/rpc</code>
<code>{"jsonrpc":"2.0","id":"1",
 "method":"message/send",
 "params":{"message":{
   "parts":[
     {"text":"BTC/USD price"}
]}}}</code>

# Or with SSE streaming:
<code>POST /api/v1/a2a/rpc/stream</code>
<code>{"jsonrpc":"2.0","id":"1",
 "method":"message/stream",
 "params":{"message":{
   "parts":[
     {"text":"BTC/USD price"}
]}}}</code>
→ SSE: task/submitted → task/working
→ SSE: task/progress →
  "Consulting oracles..."
→ SSE: task/completed → ✅</pre>
        </div>
      </div>
      <div class="integrate-card">
        <div class="integrate-header"><h3>A2A Discovery</h3><span class="integrate-badge">Autonomous</span></div>
        <div class="integrate-body">
<pre>GET /.well-known/agent.json
  → 6 interfaces (JSONRPC, SSE, MCP)
  → 5 skills with I/O schemas
  → JWT + AP2 + x402 payments
  → Context + artifact support

GET /llms.txt
  → Full API documentation
  → Pricing in both currencies</pre>
        </div>
      </div>
    </div>
  </div>
</section>

</main>

<footer class="footer" role="contentinfo">
  <div class="container">
    <div class="footer-grid">
      <div class="footer-brand">
        <h3><span>Hash</span><span>A2A</span></h3>
        <p>The Agent-to-Agent Intelligence Layer. A decentralized data marketplace where AI agents buy verified multi-oracle intelligence via HBAR (HIP-991) or USDC (x402).</p>
      </div>
      <div class="footer-col">
        <h4>Product</h4>
        <a href="#features">Features</a>
        <a href="#pricing">Pricing</a>
        <a href="#integrate">Integration</a>
        <a href="/dashboard/oracles">Oracle Dashboard</a>
      </div>
      <div class="footer-col">
        <h4>Protocols</h4>
        <a href="/mcp/">MCP Server</a>
        <a href="/.well-known/agent.json">A2A Card</a>
        <a href="/.well-known/x402.json">x402 Payments</a>
        <a href="/api/v1/feeds/pricing">Live Pricing</a>
        <a href="/llms.txt">llms.txt</a>
      </div>
      <div class="footer-col">
        <h4>Dashboards</h4>
        <a href="/dashboard">Main Dashboard</a>
        <a href="/dashboard/oracles">Oracle Dashboard</a>
        <a href="/dashboard/tasks">Task Dashboard</a>
      </div>
      <div class="footer-col">
        <h4>Community</h4>
        <a href="https://github.com/ymiydev-prog/HashA2A">GitHub</a>
        <a href="https://github.com/ymiydev-prog/HashA2A/pull/1">Pull Request</a>
        <a href="https://x.com" target="_blank" rel="noopener">X (Twitter)</a>
      </div>
    </div>
    <div class="footer-bottom">
      <span>HashA2A v0.2.0 — MIT License</span>
      <div class="footer-social">
        <a href="https://github.com/ymiydev-prog/HashA2A">🐙 GitHub</a>
        <a href="https://x.com" target="_blank" rel="noopener">𝕏 X</a>
      </div>
    </div>
  </div>
</footer>

<script>
async function loadBtcPrice() {
  const priceEl = document.getElementById('btc-price');
  const sourcesEl = document.getElementById('btc-sources');
  const refreshEl = document.getElementById('btc-refresh');
  try {
    const resp = await fetch('/landing/data');
    const data = await resp.json();
    if (data.prices && data.prices.length) {
      const pyth = data.prices.find(p => p.source === 'pyth');
      if (pyth) {
        priceEl.textContent = '$' + pyth.price.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
      }
      sourcesEl.innerHTML = data.prices.map(p => `<span class="live-source"><span class="live-dot online"></span>${p.source_name}</span>`).join('');
      refreshEl.textContent = data.oracles + ' oracles · updated ' + new Date().toLocaleTimeString();
    } else {
      priceEl.textContent = '\u2014';
      refreshEl.textContent = 'No data available';
    }
  } catch(e) {
    priceEl.textContent = '\u26A0\uFE0F';
    refreshEl.textContent = 'Connection error';
  }
}

async function loadPricing() {
  const rateInfo = document.getElementById('rate-info');
  if (!rateInfo) return;
  try {
    const resp = await fetch('/api/v1/feeds/pricing');
    const data = await resp.json();
    const p = data.products;
    const r = data.rates;
    document.getElementById('hbar-price_feed').textContent = '\u2248 ' + p.price_feed.hbar + ' HBAR';
    document.getElementById('hbar-arbitrage_scan').textContent = '\u2248 ' + p.arbitrage_scan.hbar + ' HBAR';
    document.getElementById('hbar-deep_research').textContent = '\u2248 ' + p.deep_research.hbar + ' HBAR';
    document.getElementById('hbar-prediction_market').textContent = '\u2248 ' + p.prediction_market.hbar + ' HBAR';
    rateInfo.textContent = '1 HBAR = $' + r.usd_per_hbar + ' · Updated ' + new Date(r.updated_at * 1000).toLocaleTimeString();
  } catch(e) {
    rateInfo.textContent = 'Live pricing unavailable — using default rates';
  }
}

loadBtcPrice();
loadPricing();
setInterval(loadBtcPrice, 30000);
setInterval(loadPricing, 60000);
</script>
</body>
</html>"""
