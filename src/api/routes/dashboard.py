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
}
.header h1 { font-size: 22px; font-weight: 700; }
.header h1 span { background: linear-gradient(135deg, var(--accent-1), var(--accent-2)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.header-right { display: flex; align-items: center; gap: 16px; }
.badge {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 4px 12px; border-radius: 9999px; font-size: 12px; font-weight: 600;
}
.badge-live { background: rgba(34,197,94,0.12); color: var(--green); border: 1px solid rgba(34,197,94,0.25); }
.badge-version { background: rgba(59,130,246,0.1); color: var(--accent-1); border: 1px solid rgba(59,130,246,0.2); }

/* KPI Row */
.kpi-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--gap);
  margin-bottom: var(--gap);
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

/* Chart Row */
.chart-row {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: var(--gap);
  margin-bottom: var(--gap);
}
@media (max-width: 900px) { .chart-row { grid-template-columns: 1fr; } }
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
  margin-bottom: var(--gap);
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
      <span class="badge badge-live">● Live</span>
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
    <div class="kpi-row">
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

    <div class="chart-row">
      <div class="chart-card">
        <h3>Provider Trust Scores</h3>
        <canvas id="trust-chart"></canvas>
      </div>
      <div class="chart-card">
        <h3>Cost per Query (HBAR)</h3>
        <canvas id="cost-chart"></canvas>
      </div>
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
  `;

  window._allProviders = providers;
  applyTableFilter();
  renderTrustChart(providers);
  renderCostChart(providers);
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
        legend: { position: 'bottom', labels: { usePointStyle: true, padding: 12, color: '#7b8cae' } },
        tooltip: { callbacks: { label: ctx => `${ctx.label}: ${ctx.parsed} HBAR` } }
      }
    }
  });
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

fetchData();
setInterval(fetchData, 10000);
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

    return {
        "version": getattr(settings, "agent_version", "?"),
        "total_requests": getattr(agent_registry, "_total_requests_served", 0) if agent_registry else 0,
        "providers": providers,
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
