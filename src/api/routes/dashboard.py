from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["dashboard"])

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>HashA2A — Dashboard</title>
<script src="https://unpkg.com/htmx.org@2.0.4"></script>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #e2e8f0; min-height: 100vh; }
.header { background: linear-gradient(135deg, #1e293b, #0f172a); border-bottom: 1px solid #334155; padding: 1.5rem 2rem; display: flex; justify-content: space-between; align-items: center; }
.header h1 { font-size: 1.5rem; font-weight: 700; background: linear-gradient(135deg, #3b82f6, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.header span { font-size: 0.875rem; color: #94a3b8; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1rem; padding: 1.5rem 2rem; }
.card { background: #1e293b; border: 1px solid #334155; border-radius: 0.75rem; padding: 1.25rem; }
.card h3 { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; color: #64748b; margin-bottom: 0.75rem; }
.card .big { font-size: 2rem; font-weight: 700; }
.provider { display: flex; justify-content: space-between; align-items: center; padding: 0.75rem 0; border-bottom: 1px solid #1e293b; }
.provider:last-child { border-bottom: none; }
.provider .name { font-weight: 600; }
.provider .price { font-family: monospace; color: #22c55e; }
.provider .trust { font-family: monospace; }
.badge { display: inline-block; padding: 0.125rem 0.5rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; }
.badge-green { background: #22c55e22; color: #22c55e; border: 1px solid #22c55e44; }
.badge-blue { background: #3b82f622; color: #3b82f6; border: 1px solid #3b82f644; }
.badge-yellow { background: #eab30822; color: #eab308; border: 1px solid #eab30844; }
.badge-red { background: #ef444422; color: #ef4444; border: 1px solid #ef444444; }
.badge-gray { background: #64748b22; color: #94a3b8; border: 1px solid #64748b44; }
.topic { background: #0f172a; border-radius: 0.5rem; padding: 0.5rem 0.75rem; font-family: monospace; font-size: 0.75rem; color: #94a3b8; margin-top: 0.5rem; }
.progress-bar { height: 0.5rem; background: #334155; border-radius: 9999px; margin-top: 0.5rem; overflow: hidden; }
.progress-fill { height: 100%; border-radius: 9999px; transition: width 0.5s ease; }
@media (max-width: 640px) { .grid { grid-template-columns: 1fr; } }
</style>
</head>
<body>
<div class="header">
  <div>
    <h1>🏪 HashA2A</h1>
    <span>Agent-to-Agent Intelligence Layer</span>
  </div>
  <div id="status-badge"><span class="badge badge-green">● Live</span></div>
</div>

<div class="grid" hx-get="/dashboard/data" hx-trigger="load, every 5s" hx-swap="innerHTML">
  <div class="card" style="grid-column: 1 / -1; text-align: center; padding: 3rem; color: #64748b;">
    Loading dashboard data...
  </div>
</div>

<script>
setInterval(() => {
  document.querySelectorAll('[hx-trigger*="every"]').forEach(el => {
    htmx.trigger(el, 'every');
  });
}, 5000);
</script>
</body>
</html>"""


@router.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def get_dashboard():
    return HTMLResponse(DASHBOARD_HTML)


@router.get("/dashboard/data", include_in_schema=False)
async def get_dashboard_data(request: Request):
    from fastapi.responses import JSONResponse

    settings = getattr(request.app.state, "settings", None)
    hedera = getattr(request.app.state, "hedera", None)
    provider_registry = getattr(request.app.state, "provider_registry", None)
    agent_registry = getattr(request.app.state, "agent_registry", None)

    providers_html = ""
    total_staked = 0
    if provider_registry:
        for p in provider_registry.list_all():
            r = p.reputation
            trust = r.trust_score
            total_staked += r.staked_hbar
            trust_badge = "badge-green" if trust >= 70 else "badge-yellow" if trust >= 40 else "badge-red"
            providers_html += f"""<div class="provider">
  <div>
    <div class="name">{p.name}</div>
    <div style="font-size:0.75rem;color:#64748b;">{p.provider_id} · {r.total_requests} req</div>
  </div>
  <div style="text-align:right;">
    <div class="price">{p.cost_hbar} HBAR</div>
    <div class="trust"><span class="badge {trust_badge}">{trust:.0f}</span></div>
  </div>
</div>"""

    topics_html = ""
    if hedera:
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            topics_html = f"""<div class="topic">📥 Inbound: {loop.run_until_complete(hedera.get_or_create_inbound_topic())}</div>
<div class="topic">📤 Outbound: {loop.run_until_complete(hedera.get_or_create_outbound_topic())}</div>
<div class="topic">📜 Audit: {loop.run_until_complete(hedera.get_or_create_audit_topic())}</div>"""
        except Exception:
            topics_html = '<div class="topic" style="color:#ef4444;">⚠️ Hedera not configured</div>'

    html = f"""
<div class="card">
  <h3>🏪 Agent Status</h3>
  <div class="big">{agent_registry._total_requests_served if agent_registry else 0}</div>
  <div style="color:#64748b;font-size:0.875rem;">Total Requests Served</div>
  <div style="margin-top: 0.75rem; display: flex; gap: 1rem;">
    <div><span style="color:#22c55e;">●</span> Live</div>
    <div><span style="color:#94a3b8;">v{getattr(settings, 'agent_version', '?')}</span></div>
  </div>
</div>

<div class="card">
  <h3>💰 Treasury</h3>
  <div class="big">{total_staked:.0f}</div>
  <div style="color:#64748b;font-size:0.875rem;">Total HBAR Staked</div>
  {topics_html}
</div>

<div class="card" style="grid-column: span 2;">
  <h3>📦 Providers</h3>
  <div class="progress-bar"><div class="progress-fill" style="width:{min(len(providers_html.split('</div>')) * 10, 100)}%;background:linear-gradient(90deg,#3b82f6,#8b5cf6);"></div></div>
  {providers_html}
</div>

<div class="card" style="grid-column: span 2;">
  <h3>📡 Endpoints</h3>
  <div class="topic">GET /api/v1/providers — List providers</div>
  <div class="topic">POST /api/v1/requests — New data request</div>
  <div class="topic">GET /api/v1/agent/profile — Agent info</div>
  <div class="topic">GET /api/v1/agent/topics — HCS topics</div>
  <div class="topic">📡 MCP: /mcp — MCP Server endpoint</div>
</div>

<div class="card">
  <h3>🧠 Payments</h3>
  <div style="display:flex;gap:1rem;flex-wrap:wrap;">
    <span class="badge badge-blue">HIP-991 HBAR</span>
    <span class="badge badge-yellow">x402 USDC</span>
  </div>
  <div style="margin-top:0.75rem;color:#64748b;font-size:0.75rem;">
    HIP-991 auto-collects fee on HCS submit<br>
    x402 accepts USDC on Base/Polygon
  </div>
</div>
"""
    return HTMLResponse(html)
