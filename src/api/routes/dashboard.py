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
let charts = {};

function initCharts() {
  Chart.defaults.color = '#7b8cae';
  Chart.defaults.borderColor = '#1e2a45';
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

function renderAgents(agents) {
  const container = document.getElementById('agent-items');
  const countEl = document.getElementById('agent-count');
  if (!container) return;

  if (countEl) {
    const online = agents.filter(a => a.presence === 'online').length;
    countEl.textContent = `(${online}/${agents.length} online)`;
  }

  if (!agents.length) {
    container.innerHTML = '<div style="color:var(--text-muted);font-size:12px;">No agents discovered yet. Listening on HCS topics…</div>';
    return;
  }

  container.innerHTML = agents.map(a => {
    const dotClass = a.presence === 'online' ? 'online' : a.presence === 'offline' ? 'offline' : 'unknown';
    const tags = (a.tags || []).slice(0, 3).map(t => `<span style="margin-right:4px;">#${t}</span>`).join('');
    return `<div class="agent-item">
      <div class="name"><span class="dot ${dotClass}"></span>${a.agent_name}</div>
      <div class="meta">${a.description ? a.description.substring(0, 50) + '…' : 'No description'} · ${a.total_requests || 0} requests</div>
      ${tags ? `<div class="tags">${tags}</div>` : ''}
    </div>`;
  }).join('');
}

function updateAgentPresence(agentId, presence) {
  const idx = window._agents.findIndex(a => a.agent_id === agentId);
  if (idx >= 0) {
    window._agents[idx].presence = presence;
    renderAgents(window._agents);
  }
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
      `<div class="loading" style="color:var(--red)">⚠️ Connection error</div>`;
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
        return JSONResponse(data)
    except Exception as e:
        return JSONResponse({"error": str(e)})
