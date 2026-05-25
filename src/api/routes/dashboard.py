from fastapi import APIRouter, Cookie, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.exceptions import HTTPException
import json
import hashlib
import os

router = APIRouter(tags=["dashboard-admin"])

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>HashA2A — Dashboard</title>
<link rel="icon" type="image/png" href="/favicon.png">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.5.1"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
*, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }
:root {
  --bg: #06080f;
  --surface: rgba(255,255,255,0.03);
  --surface-hover: rgba(255,255,255,0.06);
  --border: rgba(255,255,255,0.06);
  --border-hover: rgba(255,255,255,0.12);
  --text: #f0f2f7;
  --text-secondary: #8b92a8;
  --text-muted: #555b70;
  --blue: #3b82f6;
  --purple: #8b5cf6;
  --cyan: #06b6d4;
  --green: #10b981;
  --amber: #f59e0b;
  --red: #ef4444;
  --radius: 14px;
  --radius-sm: 10px;
}
html { scroll-behavior: smooth; }
body {
  background: var(--bg); color: var(--text);
  font-family: 'Inter', system-ui, sans-serif;
  -webkit-font-smoothing: antialiased;
  min-height: 100vh;
}
.bg-grid {
  position: fixed; inset: 0; z-index: 0; pointer-events: none;
  background-image: radial-gradient(circle at 1px 1px, rgba(255,255,255,0.025) 1px, transparent 0);
  background-size: 36px 36px;
}
.bg-gradient {
  position: fixed; inset: 0; z-index: 0; pointer-events: none;
  background: radial-gradient(ellipse 70% 50% at 30% 0%, rgba(59,130,246,0.06) 0%, transparent 60%),
              radial-gradient(ellipse 50% 40% at 80% 10%, rgba(139,92,246,0.04) 0%, transparent 50%);
}

/* Layout */
.app { position: relative; z-index: 1; max-width: 1440px; margin: 0 auto; padding: 16px; }

/* Top Bar */
.topbar {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 24px; margin-bottom: 16px;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); backdrop-filter: blur(12px);
}
.topbar-logo { font-size: 18px; font-weight: 800; letter-spacing: -0.02em; }
.topbar-logo .hash { color: var(--blue); }
.topbar-logo .a2a { color: var(--purple); }
.topbar-right { display: flex; align-items: center; gap: 12px; }
.badge {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 5px 12px; border-radius: 999px; font-size: 12px; font-weight: 600;
}
.badge-live { background: rgba(16,185,129,0.1); color: var(--green); border: 1px solid rgba(16,185,129,0.2); }
.badge-live::before { content:''; width:7px; height:7px; border-radius:50%; background:var(--green); animation:pulse 2s infinite; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.3} }
.badge-ver { background: rgba(59,130,246,0.08); color: var(--blue); border: 1px solid rgba(59,130,246,0.15); }
.topbar-nav { display: flex; gap: 4px; }
.topbar-nav a {
  padding: 6px 14px; border-radius: 8px; font-size: 13px; font-weight: 500;
  color: var(--text-secondary); transition: all 0.2s;
}
.topbar-nav a:hover, .topbar-nav a.active { color: var(--text); background: var(--surface-hover); }

/* 3-Column Layout */
.layout { display: grid; grid-template-columns: 260px 1fr 280px; gap: 16px; }
@media (max-width: 1200px) { .layout { grid-template-columns: 1fr; } }

/* Cards */
.card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 20px 24px;
  backdrop-filter: blur(12px); transition: all 0.3s;
}
.card:hover { border-color: var(--border-hover); }

/* KPIs */
.kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 16px; }
@media (max-width: 900px) { .kpi-grid { grid-template-columns: repeat(2, 1fr); } }
.kpi {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 20px 24px; position: relative; overflow: hidden;
}
.kpi::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
}
.kpi.blue::before { background: linear-gradient(90deg, var(--blue), var(--cyan)); }
.kpi.purple::before { background: linear-gradient(90deg, var(--purple), var(--blue)); }
.kpi.cyan::before { background: linear-gradient(90deg, var(--cyan), var(--green)); }
.kpi.green::before { background: linear-gradient(90deg, var(--green), var(--cyan)); }
.kpi-label { font-size: 12px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 8px; font-weight: 600; }
.kpi-value { font-size: 28px; font-weight: 800; letter-spacing: -0.02em; }
.kpi-sub { font-size: 13px; color: var(--text-secondary); margin-top: 4px; }

/* Charts */
.chart-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
@media (max-width: 700px) { .chart-grid { grid-template-columns: 1fr; } }
.chart-card { }
.chart-card h3 { font-size: 13px; font-weight: 600; color: var(--text-secondary); margin-bottom: 16px; }
.chart-card canvas { max-height: 240px; }

/* Table */
.table-card { }
.table-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-wrap: wrap; gap: 12px; }
.table-header h3 { font-size: 13px; font-weight: 600; color: var(--text-secondary); }
.table-filters { display: flex; gap: 8px; }
.table-filters select {
  background: var(--bg); color: var(--text); border: 1px solid var(--border);
  border-radius: 8px; padding: 6px 12px; font-size: 12px; font-family: inherit; cursor: pointer;
}
.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table thead th {
  text-align: left; padding: 10px 12px; border-bottom: 1px solid var(--border);
  color: var(--text-muted); font-weight: 600; font-size: 11px;
  text-transform: uppercase; letter-spacing: 0.06em; cursor: pointer;
}
.data-table thead th:hover { color: var(--text-secondary); }
.data-table tbody td { padding: 12px; border-bottom: 1px solid var(--border); }
.data-table tbody tr { transition: background 0.15s; }
.data-table tbody tr:hover { background: var(--surface-hover); }
.score-bar { height: 4px; border-radius: 2px; margin-top: 6px; }
.mono { font-family: 'JetBrains Mono', monospace; font-size: 11px; }

/* Sidebar */
.sidebar-left, .sidebar-right { display: flex; flex-direction: column; gap: 16px; }
.provider-list h3, .agent-list h3, .topic-feed h3, .a2a-card h3 {
  font-size: 13px; font-weight: 600; color: var(--text-secondary); margin-bottom: 12px;
}
.provider-item {
  padding: 12px; border-radius: var(--radius-sm); margin-bottom: 8px;
  background: var(--bg); border: 1px solid transparent; transition: all 0.2s;
}
.provider-item:hover { border-color: var(--border-hover); }
.provider-item .name { font-size: 13px; font-weight: 600; }
.provider-item .meta { font-size: 11px; color: var(--text-muted); margin-top: 4px; display: flex; justify-content: space-between; }
.mini-bar { height: 3px; border-radius: 2px; margin-top: 8px; background: var(--border); }
.mini-bar-fill { height: 100%; border-radius: 2px; }

.agent-item {
  padding: 12px; border-radius: var(--radius-sm); margin-bottom: 8px;
  background: var(--bg); border: 1px solid transparent; transition: all 0.2s;
}
.agent-item:hover { border-color: var(--border-hover); }
.agent-item .name { font-size: 13px; font-weight: 600; }
.agent-item .dot { display: inline-block; width: 7px; height: 7px; border-radius: 50%; margin-right: 6px; }
.agent-item .dot.online { background: var(--green); box-shadow: 0 0 6px var(--green); }
.agent-item .dot.offline { background: var(--red); }
.agent-item .dot.unknown { background: var(--amber); }
.agent-item .meta { font-size: 11px; color: var(--text-muted); margin-top: 4px; }
.agent-item .tags { font-size: 10px; color: var(--cyan); margin-top: 4px; }

.topic-item { padding: 8px 0; border-bottom: 1px solid var(--border); font-size: 12px; }
.topic-item:last-child { border-bottom: none; }
.topic-item .time { color: var(--text-muted); font-size: 10px; }
.topic-item .title { color: var(--text); margin-top: 2px; }

.a2a-row { display: flex; justify-content: space-between; padding: 8px 0; font-size: 13px; border-bottom: 1px solid var(--border); }
.a2a-row:last-child { border-bottom: none; }
.a2a-label { color: var(--text-muted); }
.a2a-value { font-weight: 600; }

/* Loading */
.loading { text-align: center; padding: 60px; color: var(--text-muted); }
.loading::after { content: ''; display: block; width: 28px; height: 28px; margin: 16px auto; border: 3px solid var(--border); border-top-color: var(--blue); border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* Footer */
.footer { text-align: center; padding: 24px; color: var(--text-muted); font-size: 12px; margin-top: 16px; }
</style>
</head>
<body>
<div class="bg-grid"></div>
<div class="bg-gradient"></div>

<div class="app">
  <div class="topbar">
    <div style="display:flex;align-items:center;gap:16px;">
      <div class="topbar-logo" style="display:flex;align-items:center;gap:10px;">
        <svg width="24" height="24" viewBox="0 0 60 60" fill="none" xmlns="http://www.w3.org/2000/svg" style="flex-shrink:0;">
          <polygon points="30,4 52,16 52,40 30,52 8,40 8,16" fill="none" stroke="url(#lg-d1)" stroke-width="3" stroke-linejoin="round"/>
          <polygon points="30,14 44,22 44,36 30,44 16,36 16,22" fill="url(#lg-d1)" opacity="0.12"/>
          <circle cx="30" cy="4" r="3.5" fill="#3b82f6"/>
          <circle cx="52" cy="16" r="3.5" fill="#6366f1"/>
          <circle cx="52" cy="40" r="3.5" fill="#8b5cf6"/>
          <circle cx="30" cy="52" r="3.5" fill="#06b6d4"/>
          <circle cx="8" cy="40" r="3.5" fill="#3b82f6"/>
          <circle cx="8" cy="16" r="3.5" fill="#6366f1"/>
          <circle cx="30" cy="28" r="4.5" fill="white" opacity="0.9"/>
          <defs><linearGradient id="lg-d1" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#3b82f6"/><stop offset="100%" stop-color="#8b5cf6"/></linearGradient></defs>
        </svg>
        <span class="hash">Hash</span><span class="a2a">A2A</span></div>
      <nav class="topbar-nav">
        <a href="/dashboard" class="active">Dashboard</a>
        <a href="/dashboard/oracles">Oracles</a>
        <a href="/dashboard/tasks">Tasks</a>
        <a href="/mcp/">MCP</a>
      </nav>
    </div>
    <div class="topbar-right">
      <span class="badge badge-live">Live</span>
      <span class="badge badge-ver">v<span id="agent-version">—</span></span>
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
  if (typeof Chart === 'undefined') { setTimeout(initCharts, 1000); return; }
  Chart.defaults.color = '#8b92a8';
  Chart.defaults.borderColor = 'rgba(255,255,255,0.06)';
  charts.initialized = true;
}

function renderDashboard(data) {
  const container = document.getElementById('dashboard-content');
  if (data.error) { container.innerHTML = '<div class="loading" style="color:var(--red)">' + data.error + '</div>'; return; }
  document.getElementById('agent-version').textContent = data.version || '—';

  const providers = data.providers || [];
  const totalStaked = providers.reduce((s, p) => s + (p.staked_hbar || 0), 0);
  const totalReqs = data.total_requests || 0;
  const avgTrust = providers.length ? providers.reduce((s, p) => s + (p.trust_score || 0), 0) / providers.length : 0;

  container.innerHTML = `
    <div class="kpi-grid">
      <div class="kpi blue"><div class="kpi-label">Requests Served</div><div class="kpi-value">${fmt(totalReqs)}</div><div class="kpi-sub">${providers.length} active providers</div></div>
      <div class="kpi purple"><div class="kpi-label">Avg Trust Score</div><div class="kpi-value">${avgTrust.toFixed(0)}</div><div class="kpi-sub">weighted reputation</div></div>
      <div class="kpi cyan"><div class="kpi-label">HBAR Staked</div><div class="kpi-value">${fmt(totalStaked)}</div><div class="kpi-sub">across all providers</div></div>
      <div class="kpi green"><div class="kpi-label">Payments</div><div class="kpi-value" style="font-size:20px;">HIP-991 + x402</div><div class="kpi-sub">HBAR · USDC (Base)</div></div>
    </div>

    <div class="layout">
      <div class="sidebar-left">
        <div class="card provider-list">
          <h3>Providers</h3>
          <div id="quick-providers"></div>
        </div>
        <div class="card a2a-card" id="a2a-stats" style="display:none;">
          <h3>A2A Protocol</h3>
          <div id="a2a-content"></div>
        </div>
      </div>

      <div class="main">
        <div class="chart-grid">
          <div class="card chart-card"><h3>Trust Scores</h3><canvas id="trust-chart"></canvas></div>
          <div class="card chart-card"><h3>Cost Distribution</h3><canvas id="cost-chart"></canvas></div>
        </div>
        <div class="card chart-card" style="margin-bottom:16px;"><h3>Performance Radar</h3><canvas id="radar-chart" style="max-height:280px;"></canvas></div>
        <div class="card table-card">
          <div class="table-header">
            <h3>All Providers</h3>
            <div class="table-filters">
              <select id="filter-min-trust" onchange="applyTableFilter()">
                <option value="0">Any Trust</option><option value="70">≥70</option><option value="50">≥50</option><option value="30">≥30</option>
              </select>
              <select id="filter-cost" onchange="applyTableFilter()">
                <option value="all">Any Price</option><option value="low">≤0.3 HBAR</option><option value="mid">≤0.5 HBAR</option><option value="high">&gt;0.5 HBAR</option>
              </select>
            </div>
          </div>
          <div style="overflow-x:auto;">
            <table class="data-table" id="prov-table">
              <thead><tr>
                <th onclick="sortTable('name')">Provider</th>
                <th onclick="sortTable('trust_score')">Trust</th>
                <th onclick="sortTable('cost_hbar')">Cost</th>
                <th onclick="sortTable('staked_hbar')">Staked</th>
                <th onclick="sortTable('success_rate')">Success</th>
              </tr></thead>
              <tbody id="table-body"></tbody>
            </table>
          </div>
        </div>
      </div>

      <div class="sidebar-right">
        <div class="card agent-list">
          <h3>Agents <span id="agent-count" style="color:var(--green);font-size:11px;"></span></h3>
          <div id="agent-items"><div style="color:var(--text-muted);font-size:12px;">Scanning…</div></div>
        </div>
        <div class="card topic-feed">
          <h3>Topic Feed</h3>
          <div id="topic-items"><div style="color:var(--text-muted);font-size:12px;">Waiting for messages…</div></div>
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
  const colors = scores.map(s => s >= 70 ? '#10b981' : s >= 50 ? '#f59e0b' : '#ef4444');
  charts.trust = new Chart(canvas, {
    type: 'bar',
    data: { labels, datasets: [{ data: scores, backgroundColor: colors.map(c => c + '99'), borderColor: colors, borderWidth: 1, borderRadius: 6 }] },
    options: { responsive: true, maintainAspectRatio: false, indexAxis: 'y', plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => 'Trust: ' + ctx.parsed.x + '/100' } } }, scales: { x: { beginAtZero: true, max: 100, grid: { color: 'rgba(255,255,255,0.04)' } }, y: { grid: { display: false } } } }
  });
}

function renderCostChart(providers) {
  const canvas = document.getElementById('cost-chart');
  if (!canvas) return;
  if (charts.cost) charts.cost.destroy();
  charts.cost = new Chart(canvas, {
    type: 'doughnut',
    data: { labels: providers.map(p => p.name), datasets: [{ data: providers.map(p => p.cost_hbar), backgroundColor: ['#3b82f699','#8b5cf699','#06b6d499','#10b98199','#f59e0b99'], borderColor: '#06080f', borderWidth: 2 }] },
    options: { responsive: true, maintainAspectRatio: false, cutout: '65%', plugins: { legend: { position: 'bottom', labels: { usePointStyle: true, padding: 8, color: '#8b92a8', font: { size: 10 } } }, tooltip: { callbacks: { label: ctx => ctx.label + ': ' + ctx.parsed + ' HBAR' } } } }
  });
}

function renderRadarChart(providers) {
  const canvas = document.getElementById('radar-chart');
  if (!canvas) return;
  if (charts.radar) charts.radar.destroy();
  charts.radar = new Chart(canvas, {
    type: 'radar',
    data: {
      labels: ['Trust', 'Success Rate', 'Stake Ratio'],
      datasets: providers.slice(0, 4).map((p, i) => ({
        label: p.name.split(' ')[0],
        data: [(p.trust_score||0)/100, p.success_rate||0, Math.min((p.staked_hbar||0)/1000, 1)],
        borderColor: ['#3b82f6','#8b5cf6','#06b6d4','#10b981'][i],
        backgroundColor: ['#3b82f622','#8b5cf622','#06b6d422','#10b98122'][i],
        borderWidth: 2, pointRadius: 3,
      }))
    },
    options: { responsive: true, maintainAspectRatio: false, scales: { r: { beginAtZero: true, max: 1, grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { display: false } } }, plugins: { legend: { position: 'bottom', labels: { usePointStyle: true, padding: 8, color: '#8b92a8', font: { size: 10 } } } } }
  });
}

function renderQuickProviders(providers) {
  const container = document.getElementById('quick-providers');
  if (!container) return;
  container.innerHTML = providers.map(p => {
    const ts = p.trust_score || 0;
    const color = ts >= 70 ? '#10b981' : ts >= 50 ? '#f59e0b' : '#ef4444';
    return '<div class="provider-item"><div class="name">' + p.name + '</div><div class="meta"><span>' + p.cost_hbar + ' HBAR</span><span style="color:' + color + '">' + ts.toFixed(0) + '</span></div><div class="mini-bar"><div class="mini-bar-fill" style="width:' + ts + '%;background:' + color + ';"></div></div></div>';
  }).join('');
}

function renderAgents(agents) {
  const container = document.getElementById('agent-items');
  const countEl = document.getElementById('agent-count');
  if (!container) return;
  if (countEl) { const online = agents.filter(a => a.presence === 'online').length; countEl.textContent = '(' + online + '/' + agents.length + ')'; }
  if (!agents.length) { container.innerHTML = '<div style="color:var(--text-muted);font-size:12px;">No agents discovered yet.</div>'; return; }
  container.innerHTML = agents.map(a => {
    const dotClass = a.presence === 'online' ? 'online' : a.presence === 'offline' ? 'offline' : 'unknown';
    const tags = (a.tags || []).slice(0, 3).map(t => '<span style="margin-right:4px;">#' + t + '</span>').join('');
    return '<div class="agent-item"><div class="name"><span class="dot ' + dotClass + '"></span>' + a.agent_name + '</div><div class="meta">' + (a.description||'').substring(0,50) + ' · ' + (a.total_requests||0) + ' reqs</div>' + (tags ? '<div class="tags">' + tags + '</div>' : '') + '</div>';
  }).join('');
}

function renderA2AStats(data) {
  const el = document.getElementById('a2a-stats');
  const content = document.getElementById('a2a-content');
  if (!el || !content) return;
  const a2a = data.a2a;
  if (!a2a || !a2a.tasks_by_status || !Object.keys(a2a.tasks_by_status).length) { el.style.display = 'none'; return; }
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
    '<div class="a2a-row"><span class="a2a-label">Active</span><span class="a2a-value" style="color:var(--amber)">' + active + '</span></div>' +
    '<div class="a2a-row"><span class="a2a-label">Completed</span><span class="a2a-value" style="color:var(--green)">' + completed + '</span></div>' +
    '<div class="a2a-row"><span class="a2a-label">Success</span><span class="a2a-value" style="color:var(--' + (successRate >= 80 ? 'green' : successRate >= 50 ? 'amber' : 'red') + ')">' + successRate + '%</span></div>' +
    '<div style="margin-top:10px;text-align:center"><a href="/dashboard/tasks" style="color:var(--blue);font-size:12px;">Manage tasks →</a></div>';
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
    const color = ts >= 70 ? 'var(--green)' : ts >= 50 ? 'var(--amber)' : 'var(--red)';
    const barColor = ts >= 70 ? '#10b981' : ts >= 50 ? '#f59e0b' : '#ef4444';
    return '<tr><td><strong>' + p.name + '</strong><br><span class="mono" style="color:var(--text-muted);">' + p.provider_id + '</span></td><td><span style="color:' + color + ';font-weight:600;">' + ts.toFixed(0) + '</span><div class="score-bar" style="width:' + ts + '%;background:' + barColor + ';"></div></td><td>' + p.cost_hbar + ' HBAR</td><td>' + (p.staked_hbar || 0).toFixed(0) + ' HBAR</td><td>' + ((p.success_rate || 0) * 100).toFixed(0) + '%</td></tr>';
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
    document.getElementById('dashboard-content').innerHTML = '<div class="loading" style="color:var(--red)">Connection error: ' + e.message + '</div>';
  }
}

function connectWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const ws = new WebSocket(protocol + '//' + window.location.host + '/ws/dashboard');
  ws.onopen = () => console.log('WebSocket connected');
  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data);
      if (msg.type === 'agent_heartbeat') updateAgentPresence(msg.data.agent_id, 'online');
      else if (msg.type === 'agent_discovered') {
        if (!window._agents) window._agents = [];
        const existing = window._agents.find(a => a.agent_id === msg.data.agent_id);
        if (!existing) {
          window._agents.push({ agent_id: msg.data.agent_id, agent_name: msg.data.agent_name, description: msg.data.description, tags: msg.data.tags, presence: 'online', trust_score: 50, total_requests: 0, last_seen: new Date().toISOString(), heartbeat_count: 1 });
          renderAgents(window._agents);
        }
      }
    } catch (e) { console.error('WebSocket message error:', e); }
  };
  ws.onclose = () => setTimeout(connectWebSocket, 5000);
  setInterval(() => { if (ws.readyState === WebSocket.OPEN) ws.send('ping'); }, 30000);
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


LOGIN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>HashA2A — Login</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
*, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }
body {
  background: #06080f; color: #f0f2f7;
  font-family: 'Inter', sans-serif; min-height: 100vh;
  display: flex; align-items: center; justify-content: center;
}
.container { max-width: 400px; width: 100%; padding: 24px; }
.card {
  background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06);
  border-radius: 16px; padding: 40px 32px; text-align: center;
}
.logo { font-size: 24px; font-weight: 800; letter-spacing: -0.02em; margin-bottom: 8px; }
.logo .hash { color: #3b82f6; }
.logo .a2a { background: linear-gradient(135deg, #8b5cf6, #06b6d4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
h1 { font-size: 20px; font-weight: 700; margin: 24px 0 8px; }
p { font-size: 14px; color: #8b92a8; margin-bottom: 24px; }
input {
  width: 100%; padding: 12px 16px; border-radius: 10px;
  border: 1px solid rgba(255,255,255,0.06); background: rgba(255,255,255,0.03);
  color: #f0f2f7; font-size: 15px; font-family: inherit;
  outline: none; transition: border-color 0.2s;
}
input:focus { border-color: #3b82f6; }
button {
  width: 100%; padding: 12px; border-radius: 10px; border: none;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6); color: white;
  font-size: 15px; font-weight: 600; cursor: pointer; margin-top: 16px;
  transition: opacity 0.2s;
}
button:hover { opacity: 0.9; }
.error { color: #ef4444; font-size: 13px; margin-top: 12px; display: none; }
</style>
</head>
<body>
<div class="container">
  <div class="card">
    <div class="logo"><span class="hash">Hash</span><span class="a2a">A2A</span></div>
    <h1>Dashboard Access</h1>
    <p>Enter the dashboard password to continue.</p>
    <form id="login-form">
      <input type="password" id="password" placeholder="Password" autofocus>
      <button type="submit">Unlock Dashboard</button>
      <div class="error" id="error-msg">Incorrect password</div>
    </form>
  </div>
</div>
<script>
document.getElementById('login-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const pw = document.getElementById('password').value;
  const resp = await fetch('/dashboard/auth', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({password: pw}),
  });
  if (resp.ok) {
    window.location.href = '/dashboard';
  } else {
    document.getElementById('error-msg').style.display = 'block';
  }
});
</script>
</body>
</html>"""


def _check_dash_auth(request: Request, dash_token: str | None = None):
    from core.config import Settings
    settings = Settings()
    if not settings.dashboard_password:
        return
    if dash_token and dash_token == settings.dashboard_password:
        return
    raise HTTPException(status_code=401, detail="Unauthorized")


@router.get("/dashboard/login", response_class=HTMLResponse, include_in_schema=False)
async def get_dashboard_login():
    return HTMLResponse(LOGIN_HTML)


@router.post("/dashboard/auth", include_in_schema=False)
async def post_dashboard_auth(data: dict):
    from core.config import Settings
    settings = Settings()
    if not settings.dashboard_password:
        return JSONResponse({"ok": True})
    pw = data.get("password", "")
    if pw == settings.dashboard_password:
        resp = JSONResponse({"ok": True})
        resp.set_cookie(key="dash_token", value=pw, httponly=True, max_age=86400, samesite="lax")
        return resp
    raise HTTPException(status_code=403, detail="Incorrect password")


@router.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def get_dashboard(request: Request, dash_token: str | None = Cookie(None)):
    _check_dash_auth(request, dash_token)
    return HTMLResponse(DASHBOARD_HTML)


@router.get("/dashboard/data", include_in_schema=False)
async def get_dashboard_data(request: Request, dash_token: str | None = Cookie(None)):
    _check_dash_auth(request, dash_token)
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
async def get_tasks_dashboard(request: Request, dash_token: str | None = Cookie(None)):
    _check_dash_auth(request, dash_token)
    return HTMLResponse(TASKS_HTML)


@router.get("/dashboard/tasks/data", include_in_schema=False)
async def get_tasks_data(request: Request, dash_token: str | None = Cookie(None)):
    _check_dash_auth(request, dash_token)
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


@router.get("/dashboard/oracles", response_class=HTMLResponse, include_in_schema=False)
async def get_oracles_dashboard(request: Request, dash_token: str | None = Cookie(None)):
    _check_dash_auth(request, dash_token)
    return HTMLResponse(ORACLE_HTML)


@router.get("/dashboard/oracles/data", include_in_schema=False)
async def get_oracles_data(request: Request, dash_token: str | None = Cookie(None)):
    _check_dash_auth(request, dash_token)
    from core.oracle_hub import OracleHub
    hub = OracleHub()
    try:
        all_prices = await hub.get_all_prices()
        assets = {}
        for asset, prices in all_prices.items():
            if not prices:
                continue
            price_vals = [p.price for p in prices]
            median = sorted(price_vals)[len(price_vals) // 2]
            spread_pct = round(abs(max(price_vals) - min(price_vals)) / median * 100, 3) if median else 0
            opp = "low"
            if spread_pct > 1.0:
                opp = "high"
            elif spread_pct > 0.3:
                opp = "medium"
            assets[asset] = {
                "prices": [p.to_dict() for p in prices],
                "spread_pct": spread_pct,
                "opportunity": opp,
                "median": round(median, 2),
            }
        return JSONResponse({"count": len(assets), "assets": assets})
    except Exception as e:
        return JSONResponse({"error": str(e)})
    finally:
        await hub.close()


ORACLE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>HashA2A — Oracle Dashboard</title>
<link rel="icon" type="image/png" href="/favicon.png">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.5.1"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
*, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }
:root {
  --bg: #06080f; --surface: rgba(255,255,255,0.03); --surface-hover: rgba(255,255,255,0.06);
  --border: rgba(255,255,255,0.06); --border-hover: rgba(255,255,255,0.12);
  --text: #f0f2f7; --text-secondary: #8b92a8; --text-muted: #555b70;
  --blue: #3b82f6; --purple: #8b5cf6; --cyan: #06b6d4; --green: #10b981; --amber: #f59e0b; --red: #ef4444;
  --radius: 14px; --radius-sm: 10px;
}
body { background: var(--bg); color: var(--text); font-family: 'Inter', system-ui, sans-serif; min-height: 100vh; }
.bg-grid { position:fixed;inset:0;z-index:0;pointer-events:none; background-image:radial-gradient(circle at 1px 1px,rgba(255,255,255,0.025) 1px,transparent 0); background-size:36px 36px; }
.bg-gradient { position:fixed;inset:0;z-index:0;pointer-events:none; background:radial-gradient(ellipse 70% 50% at 30% 0%,rgba(59,130,246,0.06) 0%,transparent 60%), radial-gradient(ellipse 50% 40% at 80% 10%,rgba(139,92,246,0.04) 0%,transparent 50%); }
.app { position:relative; z-index:1; max-width:1400px; margin:0 auto; padding:16px; }

/* Top Bar */
.topbar { display:flex;justify-content:space-between;align-items:center; padding:16px 24px; margin-bottom:16px; background:var(--surface); border:1px solid var(--border); border-radius:var(--radius); backdrop-filter:blur(12px); }
.topbar-logo { font-size:18px; font-weight:800; letter-spacing:-0.02em; }
.topbar-logo .hash { color:var(--blue); }
.topbar-logo .a2a { color:var(--purple); }
.topbar-nav { display:flex; gap:4px; }
.topbar-nav a { padding:6px 14px; border-radius:8px; font-size:13px; font-weight:500; color:var(--text-secondary); transition:all 0.2s; }
.topbar-nav a:hover, .topbar-nav a.active { color:var(--text); background:var(--surface-hover); }
.badge { display:inline-flex;align-items:center;gap:6px; padding:5px 12px; border-radius:999px; font-size:12px; font-weight:600; }
.badge-live { background:rgba(16,185,129,0.1); color:var(--green); border:1px solid rgba(16,185,129,0.2); }
.badge-live::before { content:''; width:7px; height:7px; border-radius:50%; background:var(--green); animation:pulse 2s infinite; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.3} }

/* Charts */
.chart-row { display:grid; grid-template-columns:2fr 1fr; gap:16px; margin-bottom:16px; }
@media(max-width:900px) { .chart-row { grid-template-columns:1fr; } }
.card { background:var(--surface); border:1px solid var(--border); border-radius:var(--radius); padding:20px 24px; backdrop-filter:blur(12px); }
.card h3 { font-size:13px; font-weight:600; color:var(--text-secondary); margin-bottom:16px; }
.card canvas { max-height:200px; }

/* Grid */
.grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(380px,1fr)); gap:16px; }
@media(max-width:500px) { .grid { grid-template-columns:1fr; } }
.asset-card { overflow:hidden; }
.asset-title { font-size:18px; font-weight:800; letter-spacing:-0.01em; margin-bottom:12px; display:flex; align-items:center; gap:8px; }
.asset-title .icon { width:32px; height:32px; border-radius:8px; background:var(--surface); border:1px solid var(--border); display:flex; align-items:center; justify-content:center; font-size:14px; }
.oracle-row { display:flex; justify-content:space-between; padding:10px 0; border-bottom:1px solid var(--border); font-size:14px; align-items:center; }
.oracle-row:last-child { border-bottom:none; }
.oracle-name { color:var(--text-secondary); font-size:13px; }
.oracle-price { font-weight:600; font-family:'JetBrains Mono',monospace; font-size:13px; }
.confidence-dot { width:7px; height:7px; border-radius:50%; display:inline-block; margin-right:6px; }
.spread-bar { margin-top:12px; padding:10px 14px; border-radius:var(--radius-sm); font-size:13px; display:flex; justify-content:space-between; align-items:center; }
.spread-high { background:rgba(16,185,129,0.08); color:var(--green); border:1px solid rgba(16,185,129,0.15); }
.spread-medium { background:rgba(245,158,11,0.08); color:var(--amber); border:1px solid rgba(245,158,11,0.15); }
.spread-low { background:rgba(255,255,255,0.02); color:var(--text-muted); border:1px solid var(--border); }

.footer { text-align:center; padding:24px; color:var(--text-muted); font-size:12px; margin-top:16px; }
.loading { text-align:center; padding:60px; color:var(--text-muted); }
.loading::after { content:''; display:block; width:28px; height:28px; margin:16px auto; border:3px solid var(--border); border-top-color:var(--blue); border-radius:50%; animation:spin 0.8s linear infinite; }
@keyframes spin { to { transform:rotate(360deg); } }
</style>
</head>
<body>
<div class="bg-grid"></div>
<div class="bg-gradient"></div>

<div class="app">
  <div class="topbar">
    <div style="display:flex;align-items:center;gap:16px;">
      <div class="topbar-logo" style="display:flex;align-items:center;gap:10px;">
        <svg width="24" height="24" viewBox="0 0 60 60" fill="none" xmlns="http://www.w3.org/2000/svg" style="flex-shrink:0;">
          <polygon points="30,4 52,16 52,40 30,52 8,40 8,16" fill="none" stroke="url(#lg-d2)" stroke-width="3" stroke-linejoin="round"/>
          <polygon points="30,14 44,22 44,36 30,44 16,36 16,22" fill="url(#lg-d2)" opacity="0.12"/>
          <circle cx="30" cy="4" r="3.5" fill="#3b82f6"/>
          <circle cx="52" cy="16" r="3.5" fill="#6366f1"/>
          <circle cx="52" cy="40" r="3.5" fill="#8b5cf6"/>
          <circle cx="30" cy="52" r="3.5" fill="#06b6d4"/>
          <circle cx="8" cy="40" r="3.5" fill="#3b82f6"/>
          <circle cx="8" cy="16" r="3.5" fill="#6366f1"/>
          <circle cx="30" cy="28" r="4.5" fill="white" opacity="0.9"/>
          <defs><linearGradient id="lg-d2" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#3b82f6"/><stop offset="100%" stop-color="#8b5cf6"/></linearGradient></defs>
        </svg>
        <span class="hash">Hash</span><span class="a2a">A2A</span></div>
      <nav class="topbar-nav">
        <a href="/dashboard">Dashboard</a>
        <a href="/dashboard/oracles" class="active">Oracles</a>
        <a href="/dashboard/tasks">Tasks</a>
        <a href="/mcp/">MCP</a>
      </nav>
    </div>
    <div style="display:flex;gap:12px;align-items:center;">
      <span class="badge badge-live" id="status-badge">Loading...</span>
      <span class="badge" id="history-count" style="background:rgba(139,92,246,0.08);color:var(--purple);border:1px solid rgba(139,92,246,0.15);">0 snapshots</span>
    </div>
  </div>

  <div class="chart-row">
    <div class="card"><h3>Spread History (last 20 snapshots)</h3><canvas id="spread-chart"></canvas></div>
    <div class="card"><h3>Sources per Asset</h3><canvas id="sources-chart"></canvas></div>
  </div>

  <div class="grid" id="oracle-grid">
    <div class="loading" style="grid-column:1/-1;">Fetching live oracle data...</div>
  </div>

  <div class="footer">Auto-refreshes every 30s · Data from Pyth · CoinGecko · DeFiLlama · Spread history stored locally</div>
</div>

<script>
const SPREAD_KEY = 'hasha2a_spread_history';
const MAX_HISTORY = 20;
let spreadChart = null, sourcesChart = null;

function loadHistory() { try { return JSON.parse(localStorage.getItem(SPREAD_KEY) || '[]'); } catch(e) { return []; } }
function saveHistory(history) { localStorage.setItem(SPREAD_KEY, JSON.stringify(history)); }

function updateCharts(assets) {
  const history = loadHistory();
  const now = new Date().toLocaleTimeString();
  const snapshot = { time: now };
  for (const [asset, info] of Object.entries(assets)) { snapshot[asset] = info.spread_pct; }
  history.push(snapshot);
  if (history.length > MAX_HISTORY) history.shift();
  saveHistory(history);
  document.getElementById('history-count').textContent = history.length + ' snapshots';

  const labels = history.map(h => h.time);
  const colors = ['#3b82f6','#8b5cf6','#10b981','#06b6d4','#f59e0b','#ef4444'];
  const datasets = Object.keys(assets).map((asset, i) => ({
    label: asset, data: history.map(h => h[asset] || 0),
    borderColor: colors[i % colors.length], backgroundColor: colors[i % colors.length] + '22',
    borderWidth: 2, pointRadius: 2, tension: 0.3,
  }));

  if (spreadChart) spreadChart.destroy();
  spreadChart = new Chart(document.getElementById('spread-chart').getContext('2d'), {
    type: 'line', data: { labels, datasets },
    options: { responsive: true, maintainAspectRatio: false, scales: { x: { ticks: { color:'#8b92a8', font:{size:10} } }, y: { ticks: { color:'#8b92a8', font:{size:10}, callback:v=>v+'%' } } }, plugins: { legend: { position:'bottom', labels:{ color:'#8b92a8', usePointStyle:true, padding:8, font:{size:10} } } } }
  });

  if (sourcesChart) sourcesChart.destroy();
  sourcesChart = new Chart(document.getElementById('sources-chart').getContext('2d'), {
    type: 'bar', data: { labels: Object.keys(assets), datasets: [{ label:'Oracle Sources', data: Object.values(assets).map(a=>a.prices.length), backgroundColor: colors, borderRadius: 6 }] },
    options: { responsive: true, maintainAspectRatio: false, scales: { y: { ticks:{ color:'#8b92a8', font:{size:10}, stepSize:1 } } }, plugins: { legend:{ display:false } } }
  });
}

async function fetchData() {
  const badge = document.getElementById('status-badge');
  const grid = document.getElementById('oracle-grid');
  try {
    badge.textContent = 'Fetching...';
    const resp = await fetch('/dashboard/oracles/data');
    const data = await resp.json();
    if (data.error) { badge.textContent = 'Error'; return; }
    badge.textContent = data.count + ' assets';
    updateCharts(data.assets);
    const icons = { 'BTC':'₿', 'ETH':'Ξ', 'SOL':'◎', 'XAU':'🥇', 'XAG':'🥈', 'USD/JPY':'¥' };
    grid.innerHTML = Object.entries(data.assets).map(([asset, info]) => {
      const sc = info.opportunity === 'high' ? 'spread-high' : info.opportunity === 'medium' ? 'spread-medium' : 'spread-low';
      const icon = icons[asset] || '◆';
      return '<div class="card asset-card"><div class="asset-title"><span class="icon">' + icon + '</span>' + asset + '</div>' +
        info.prices.map(p => '<div class="oracle-row"><span class="oracle-name"><span class="confidence-dot" style="background:' + (p.confidence>0.5?'var(--green)':p.confidence>0.2?'var(--amber)':'var(--red)') + '"></span>' + p.source_name + '</span><span class="oracle-price">$' + p.price.toFixed(2) + '</span></div>').join('') +
        '<div class="spread-bar ' + sc + '"><span>Spread</span><span><strong>' + info.spread_pct + '%</strong> · ' + info.opportunity + '</span></div></div>';
    }).join('');
  } catch(e) {
    grid.innerHTML = '<div class="loading" style="grid-column:1/-1;">Connection error. Retrying...</div>';
    badge.textContent = 'Offline';
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
<link rel="icon" type="image/png" href="/favicon.png">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
*, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }
:root {
  --bg: #06080f; --surface: rgba(255,255,255,0.03); --surface-hover: rgba(255,255,255,0.06);
  --border: rgba(255,255,255,0.06); --border-hover: rgba(255,255,255,0.12);
  --text: #f0f2f7; --text-secondary: #8b92a8; --text-muted: #555b70;
  --blue: #3b82f6; --purple: #8b5cf6; --cyan: #06b6d4; --green: #10b981; --amber: #f59e0b; --red: #ef4444;
  --radius: 14px; --radius-sm: 10px;
}
body { background: var(--bg); color: var(--text); font-family: 'Inter', system-ui, sans-serif; min-height: 100vh; }
.bg-grid { position:fixed;inset:0;z-index:0;pointer-events:none; background-image:radial-gradient(circle at 1px 1px,rgba(255,255,255,0.025) 1px,transparent 0); background-size:36px 36px; }
.bg-gradient { position:fixed;inset:0;z-index:0;pointer-events:none; background:radial-gradient(ellipse 70% 50% at 30% 0%,rgba(59,130,246,0.06) 0%,transparent 60%), radial-gradient(ellipse 50% 40% at 80% 10%,rgba(139,92,246,0.04) 0%,transparent 50%); }
.app { position:relative; z-index:1; max-width:1400px; margin:0 auto; padding:16px; }

/* Top Bar */
.topbar { display:flex;justify-content:space-between;align-items:center; padding:16px 24px; margin-bottom:16px; background:var(--surface); border:1px solid var(--border); border-radius:var(--radius); backdrop-filter:blur(12px); }
.topbar-logo { font-size:18px; font-weight:800; letter-spacing:-0.02em; }
.topbar-logo .hash { color:var(--blue); }
.topbar-logo .a2a { color:var(--purple); }
.topbar-nav { display:flex; gap:4px; }
.topbar-nav a { padding:6px 14px; border-radius:8px; font-size:13px; font-weight:500; color:var(--text-secondary); transition:all 0.2s; }
.topbar-nav a:hover, .topbar-nav a.active { color:var(--text); background:var(--surface-hover); }
.badge { display:inline-flex;align-items:center;gap:6px; padding:5px 12px; border-radius:999px; font-size:12px; font-weight:600; background:rgba(59,130,246,0.08); color:var(--blue); border:1px solid rgba(59,130,246,0.15); }

/* KPIs */
.kpi-row { display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:12px; margin-bottom:16px; }
.kpi { background:var(--surface); border:1px solid var(--border); border-radius:var(--radius); padding:16px 20px; text-align:center; }
.kpi .num { font-size:28px; font-weight:800; letter-spacing:-0.02em; }
.kpi .label { font-size:11px; color:var(--text-muted); margin-top:4px; text-transform:uppercase; letter-spacing:0.06em; font-weight:600; }

/* Grid */
.grid { display:grid; grid-template-columns:2fr 1fr; gap:16px; }
@media(max-width:900px) { .grid { grid-template-columns:1fr; } }
.card { background:var(--surface); border:1px solid var(--border); border-radius:var(--radius); padding:20px 24px; backdrop-filter:blur(12px); }
.card h3 { font-size:13px; font-weight:600; color:var(--text-secondary); margin-bottom:16px; }

/* Task Rows */
.task-row { display:flex; justify-content:space-between; padding:12px 0; border-bottom:1px solid var(--border); font-size:13px; align-items:center; cursor:pointer; transition:background 0.15s; }
.task-row:hover { background:var(--surface-hover); margin:0 -24px; padding:12px 24px; border-radius:8px; }
.task-row:last-child { border-bottom:none; }
.task-id { color:var(--text-muted); font-family:'JetBrains Mono',monospace; font-size:11px; }
.task-status { padding:3px 10px; border-radius:6px; font-size:11px; font-weight:600; text-transform:capitalize; }
.status-submitted { background:rgba(59,130,246,0.1); color:var(--blue); }
.status-working { background:rgba(245,158,11,0.1); color:var(--amber); }
.status-completed { background:rgba(16,185,129,0.1); color:var(--green); }
.status-failed { background:rgba(239,68,68,0.1); color:var(--red); }
.status-input-required { background:rgba(139,92,246,0.1); color:var(--purple); }

/* Context Rows */
.ctx-row { padding:10px 0; border-bottom:1px solid var(--border); font-size:12px; }
.ctx-row:last-child { border-bottom:none; }
.ctx-id { color:var(--text-muted); font-family:'JetBrains Mono',monospace; font-size:11px; }
.ctx-count { color:var(--green); font-weight:600; }

/* Detail Panel */
.detail-panel { background:var(--surface); border:1px solid var(--border); border-radius:var(--radius); padding:20px 24px; margin-top:16px; display:none; }
.detail-panel.open { display:block; }
.detail-row { display:flex; padding:8px 0; font-size:13px; border-bottom:1px solid var(--border); }
.detail-row:last-child { border-bottom:none; }
.detail-label { color:var(--text-muted); width:100px; flex-shrink:0; font-size:12px; }
.detail-value { color:var(--text); }

.footer { text-align:center; padding:24px; color:var(--text-muted); font-size:12px; margin-top:16px; }
</style>
</head>
<body>
<div class="bg-grid"></div>
<div class="bg-gradient"></div>

<div class="app">
  <div class="topbar">
    <div style="display:flex;align-items:center;gap:16px;">
      <div class="topbar-logo" style="display:flex;align-items:center;gap:10px;">
        <svg width="24" height="24" viewBox="0 0 60 60" fill="none" xmlns="http://www.w3.org/2000/svg" style="flex-shrink:0;">
          <polygon points="30,4 52,16 52,40 30,52 8,40 8,16" fill="none" stroke="url(#lg-d3)" stroke-width="3" stroke-linejoin="round"/>
          <polygon points="30,14 44,22 44,36 30,44 16,36 16,22" fill="url(#lg-d3)" opacity="0.12"/>
          <circle cx="30" cy="4" r="3.5" fill="#3b82f6"/>
          <circle cx="52" cy="16" r="3.5" fill="#6366f1"/>
          <circle cx="52" cy="40" r="3.5" fill="#8b5cf6"/>
          <circle cx="30" cy="52" r="3.5" fill="#06b6d4"/>
          <circle cx="8" cy="40" r="3.5" fill="#3b82f6"/>
          <circle cx="8" cy="16" r="3.5" fill="#6366f1"/>
          <circle cx="30" cy="28" r="4.5" fill="white" opacity="0.9"/>
          <defs><linearGradient id="lg-d3" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#3b82f6"/><stop offset="100%" stop-color="#8b5cf6"/></linearGradient></defs>
        </svg>
        <span class="hash">Hash</span><span class="a2a">A2A</span></div>
      <nav class="topbar-nav">
        <a href="/dashboard">Dashboard</a>
        <a href="/dashboard/oracles">Oracles</a>
        <a href="/dashboard/tasks" class="active">Tasks</a>
        <a href="/mcp/">MCP</a>
      </nav>
    </div>
    <span class="badge" id="status-badge">Loading...</span>
  </div>

  <div class="kpi-row" id="kpi-row"></div>

  <div class="grid">
    <div>
      <div class="card">
        <h3>Recent Tasks</h3>
        <div id="task-list">Loading...</div>
      </div>
      <div class="detail-panel" id="detail-panel">
        <h3 style="margin-bottom:12px">Task Detail</h3>
        <div id="detail-content"></div>
      </div>
    </div>
    <div>
      <div class="card">
        <h3>Context Activity</h3>
        <div id="ctx-list">Loading...</div>
      </div>
    </div>
  </div>

  <div class="footer">Auto-refreshes every 15s · A2A Tasks API</div>
</div>

<script>
async function fetchData() {
  try {
    const resp = await fetch('/dashboard/tasks/data');
    const data = await resp.json();
    if (data.error) { document.getElementById('status-badge').textContent = 'Error'; return; }
    document.getElementById('status-badge').textContent = data.task_count + ' tasks · ' + data.context_count + ' contexts';

    const kpi = document.getElementById('kpi-row');
    kpi.innerHTML = Object.entries(data.counts).map(([s, c]) =>
      '<div class="kpi"><div class="num" style="color:var(--' + (s==='completed'?'green':s==='failed'?'red':s==='working'?'amber':s==='input-required'?'purple':'blue') + ')">' + c + '</div><div class="label">' + s + '</div></div>'
    ).join('');

    const taskList = document.getElementById('task-list');
    taskList.innerHTML = data.tasks.map(t => {
      const sClass = 'status-' + t.status;
      return '<div class="task-row" onclick="showDetail(\\'' + t.task_id + '\\')"><span class="task-id">' + t.task_id.substring(0, 16) + '...</span><span class="task-status ' + sClass + '">' + t.status + '</span><span style="color:var(--text-muted);font-size:11px">' + t.parts.length + ' parts</span></div>';
    }).join('') || '<div style="color:var(--text-muted);font-size:13px;padding:12px 0">No tasks yet. Create one via API.</div>';

    const ctxList = document.getElementById('ctx-list');
    ctxList.innerHTML = data.contexts.map(c => {
      const desc = c.summary ? c.summary.substring(0, 60) + '...' : 'No activity';
      return '<div class="ctx-row"><span class="ctx-id">' + c.context_id.substring(0, 16) + '...</span><span class="ctx-count">' + c.interaction_count + ' interactions</span><div style="color:var(--text-muted);font-size:11px;margin-top:4px">' + desc + '</div></div>';
    }).join('') || '<div style="color:var(--text-muted);font-size:13px;padding:12px 0">No contexts yet.</div>';

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
    '<div class="detail-row"><span class="detail-label">Task ID</span><span class="detail-value" style="font-family:JetBrains Mono,monospace;font-size:11px">' + task.task_id + '</span></div>',
    '<div class="detail-row"><span class="detail-label">Status</span><span class="detail-value"><span class="task-status status-' + task.status + '">' + task.status + '</span></span></div>',
    '<div class="detail-row"><span class="detail-label">Context</span><span class="detail-value" style="font-family:JetBrains Mono,monospace;font-size:11px">' + (task.context_id || 'none') + '</span></div>',
    '<div class="detail-row"><span class="detail-label">Parts</span><span class="detail-value">' + task.parts.length + ' parts</span></div>',
    '<div class="detail-row"><span class="detail-label">Artifacts</span><span class="detail-value">' + task.artifacts.length + ' files</span></div>',
    task.context_id ? '<div style="margin-top:12px"><a href="/api/v1/tasks/context/' + task.context_id + '/history" target="_blank" style="color:var(--blue);font-size:13px">View context history →</a></div>' : '',
  ].join('');
  if (task.parts.length) {
    content.innerHTML += '<div style="margin-top:12px;font-size:12px;color:var(--text-muted)">Last part: ' + task.parts[task.parts.length - 1].text?.substring(0, 120) + '</div>';
  }
}

fetchData();
setInterval(fetchData, 15000);
</script>
</body>
</html>"""



