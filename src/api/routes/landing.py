from fastapi import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse

router = APIRouter(tags=["landing"])


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def get_landing():
    return HTMLResponse(LANDING_HTML)


def _read_well_known(subpath: str) -> str:
    import os
    path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "static", ".well-known", subpath)
    with open(path) as f:
        return f.read()

@router.get("/.well-known/agent.json", include_in_schema=False)
async def get_well_known_agent():
    import json
    try:
        data = json.loads(_read_well_known("agent.json"))
        return JSONResponse(data)
    except (FileNotFoundError, json.JSONDecodeError):
        return JSONResponse({"error": "agent.json not found"}, status_code=404)

@router.get("/.well-known/x402.json", include_in_schema=False)
async def get_well_known_x402():
    import json
    try:
        data = json.loads(_read_well_known("x402.json"))
        return JSONResponse(data)
    except (FileNotFoundError, json.JSONDecodeError):
        return JSONResponse({"error": "x402.json not found"}, status_code=404)

@router.get("/.well-known/circle/skill.md", include_in_schema=False)
async def get_circle_skill():
    from fastapi.responses import PlainTextResponse
    try:
        content = _read_well_known("circle/skill.md")
        return PlainTextResponse(content, media_type="text/markdown")
    except FileNotFoundError:
        return JSONResponse({"error": "Circle skill not found"}, status_code=404)

@router.get("/favicon.png", include_in_schema=False)
async def get_favicon():
    from fastapi.responses import FileResponse
    import os
    path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "static", "favicon.png")
    if os.path.isfile(path):
        return FileResponse(path, media_type="image/png")
    return JSONResponse({"error": "not found"}, status_code=404)

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
<link rel="icon" type="image/png" href="/favicon.png">
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
  --blue-glow: rgba(59,130,246,0.15);
  --purple: #8b5cf6;
  --purple-glow: rgba(139,92,246,0.15);
  --cyan: #06b6d4;
  --cyan-glow: rgba(6,182,212,0.15);
  --green: #10b981;
  --green-glow: rgba(16,185,129,0.15);
  --amber: #f59e0b;
  --red: #ef4444;
  --radius: 16px;
  --radius-sm: 10px;
  --radius-xs: 6px;
}
html { scroll-behavior: smooth; }
body {
  background: var(--bg);
  color: var(--text);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  overflow-x: hidden;
  line-height: 1.6;
}
a { color: var(--blue); text-decoration: none; transition: color 0.2s; }
a:hover { color: #60a5fa; }
.container { max-width: 1200px; margin: 0 auto; padding: 0 24px; }

/* Background Effects */
.bg-grid {
  position: fixed; inset: 0; z-index: 0; pointer-events: none;
  background-image:
    radial-gradient(circle at 1px 1px, rgba(255,255,255,0.03) 1px, transparent 0);
  background-size: 40px 40px;
}
.bg-gradient {
  position: fixed; inset: 0; z-index: 0; pointer-events: none;
  background:
    radial-gradient(ellipse 80% 60% at 50% 0%, rgba(59,130,246,0.08) 0%, transparent 60%),
    radial-gradient(ellipse 60% 50% at 80% 20%, rgba(139,92,246,0.06) 0%, transparent 50%),
    radial-gradient(ellipse 50% 40% at 20% 80%, rgba(6,182,212,0.05) 0%, transparent 50%);
}
.bg-gradient::after {
  content: ''; position: absolute; inset: 0;
  background: linear-gradient(180deg, transparent 0%, var(--bg) 100%);
}

/* Nav */
.nav {
  position: sticky; top: 0; z-index: 100;
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  background: rgba(6,8,15,0.8);
  border-bottom: 1px solid var(--border);
}
.nav-inner {
  max-width: 1200px; margin: 0 auto; padding: 0 24px;
  display: flex; justify-content: space-between; align-items: center; height: 64px;
}
.nav-logo {
  font-size: 20px; font-weight: 800; letter-spacing: -0.02em;
  display: flex; align-items: center; gap: 2px;
}
.nav-logo .hash { color: var(--blue); }
.nav-logo .a2a {
  background: linear-gradient(135deg, var(--purple), var(--cyan));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.nav-logo .dot { width: 6px; height: 6px; border-radius: 50%; background: var(--green); margin-left: 8px; box-shadow: 0 0 8px var(--green-glow); }
.nav-links { display: flex; gap: 8px; align-items: center; }
.nav-links a {
  font-size: 14px; font-weight: 500; color: var(--text-secondary);
  padding: 8px 14px; border-radius: var(--radius-xs); transition: all 0.2s;
}
.nav-links a:hover { color: var(--text); background: var(--surface-hover); }
.nav-cta {
  background: linear-gradient(135deg, var(--blue), var(--purple));
  color: white !important; font-weight: 600 !important;
  padding: 8px 18px !important; border-radius: var(--radius-sm) !important;
  box-shadow: 0 2px 12px rgba(59,130,246,0.25);
  transition: all 0.2s !important;
}
.nav-cta:hover { transform: translateY(-1px); box-shadow: 0 4px 20px rgba(59,130,246,0.35); }

/* Mobile Nav Toggle */
.nav-toggle {
  display: none; cursor: pointer;
  width: 32px; height: 32px; padding: 4px;
  background: none; border: none; color: var(--text);
}
.nav-toggle svg { width: 24px; height: 24px; }
.nav-toggle .bar {
  display: block; width: 100%; height: 2px;
  background: var(--text); border-radius: 2px;
  transition: all 0.3s ease;
}
.nav-toggle .bar:nth-child(2) { margin: 6px 0; }
.nav-toggle.active .bar:nth-child(1) { transform: rotate(45deg) translate(5px, 6px); }
.nav-toggle.active .bar:nth-child(2) { opacity: 0; }
.nav-toggle.active .bar:nth-child(3) { transform: rotate(-45deg) translate(5px, -6px); }

/* Mobile Nav */
@media (max-width: 768px) {
  .nav-toggle { display: block; }
  .nav-links {
    display: none; position: absolute; top: 64px; left: 0; right: 0;
    flex-direction: column; background: rgba(6,8,15,0.97);
    backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
    padding: 16px 24px; border-bottom: 1px solid var(--border);
    gap: 4px;
  }
  .nav-links.open { display: flex; }
  .nav-links a { padding: 12px 16px; border-radius: var(--radius-xs); }
  .nav-cta { text-align: center; margin-top: 8px; }
}

/* Hero Mobile */
@media (max-width: 768px) {
  .hero { padding: 80px 0 60px; }
  .hero h1 { font-size: clamp(28px, 8vw, 48px); }
  .hero p { font-size: 16px; }
  .hero-btns { flex-direction: column; gap: 12px; align-items: center; }
  .btn { width: 100%; max-width: 280px; justify-content: center; }
  .container { padding: 0 16px; }
  .section { padding: 60px 0; }
  .section-title { font-size: clamp(24px, 6vw, 32px); }
  .live-price { font-size: 40px; }
  .pricing-amount { font-size: 28px; }
}

/* Feature Icons */
.feature-icon svg { width: 28px; height: 28px; stroke-width: 1.5; }

/* Code block with copy button */
.code-block { position: relative; }
.copy-btn {
  position: absolute; top: 12px; right: 12px;
  width: 32px; height: 32px; padding: 0;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius-xs); cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  color: var(--text-muted); transition: all 0.2s;
  opacity: 0; z-index: 2;
}
.integrate-card:hover .copy-btn { opacity: 1; }
.copy-btn:hover { background: var(--surface-hover); border-color: var(--border-hover); color: var(--text); }
.copy-btn svg { width: 16px; height: 16px; }
.copy-btn .check-icon { display: none; color: var(--green); }
.copy-btn.copied .copy-icon { display: none; }
.copy-btn.copied .check-icon { display: block; }

/* Video autoplay indicator */
.video-wrapper .play-overlay {
  position: absolute; inset: 0; display: flex;
  align-items: center; justify-content: center;
  background: rgba(6,8,15,0.4); cursor: pointer;
  transition: opacity 0.3s;
}
.video-wrapper .play-overlay:hover { opacity: 0.8; }
.video-wrapper .play-overlay svg { width: 64px; height: 64px; }
.video-wrapper video[autoplay] + .play-overlay,
.video-wrapper video.playing + .play-overlay { display: none; }
.hero {
  position: relative; z-index: 1;
  padding: 120px 0 80px; text-align: center;
}
.hero-badge {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 6px 16px 6px 8px; border-radius: 999px;
  background: var(--surface); border: 1px solid var(--border);
  font-size: 13px; font-weight: 500; color: var(--text-secondary);
  margin-bottom: 32px;
  animation: fadeInUp 0.6s ease-out;
}
.hero-badge .pulse {
  width: 8px; height: 8px; border-radius: 50%; background: var(--green);
  box-shadow: 0 0 12px var(--green-glow);
  animation: pulse 2s ease-in-out infinite;
}
@keyframes pulse { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.5; transform: scale(1.2); } }
.hero h1 {
  font-size: clamp(40px, 7vw, 72px);
  font-weight: 900; line-height: 1.05; letter-spacing: -0.03em;
  max-width: 800px; margin: 0 auto;
  animation: fadeInUp 0.6s ease-out 0.1s both;
}
.hero h1 .gradient {
  background: linear-gradient(135deg, var(--blue) 0%, var(--purple) 50%, var(--cyan) 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-size: 200% 200%;
  animation: gradientShift 4s ease-in-out infinite;
}
@keyframes gradientShift { 0%, 100% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } }
.hero p {
  font-size: clamp(16px, 2.5vw, 20px);
  color: var(--text-secondary); margin-top: 24px;
  max-width: 600px; margin-left: auto; margin-right: auto;
  line-height: 1.7;
  animation: fadeInUp 0.6s ease-out 0.2s both;
}
.hero-btns {
  display: flex; gap: 12px; justify-content: center; margin-top: 40px;
  animation: fadeInUp 0.6s ease-out 0.3s both;
}
.btn {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 14px 28px; border-radius: var(--radius-sm);
  font-size: 15px; font-weight: 600; transition: all 0.2s;
  cursor: pointer; border: none; font-family: inherit;
}
.btn-primary {
  background: linear-gradient(135deg, var(--blue), var(--purple));
  color: white; box-shadow: 0 4px 20px rgba(59,130,246,0.3);
}
.btn-primary:hover { transform: translateY(-2px); box-shadow: 0 8px 30px rgba(59,130,246,0.4); }
.btn-secondary {
  background: var(--surface); color: var(--text);
  border: 1px solid var(--border);
}
.btn-secondary:hover { border-color: var(--border-hover); background: var(--surface-hover); transform: translateY(-2px); }

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Section */
.section { position: relative; z-index: 1; padding: 80px 0; }
.section-header { text-align: center; margin-bottom: 56px; }
.section-label {
  display: inline-block; font-size: 12px; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.1em;
  color: var(--blue); margin-bottom: 12px;
}
.section-title {
  font-size: clamp(28px, 4vw, 40px);
  font-weight: 800; letter-spacing: -0.02em; line-height: 1.2;
}
.section-desc {
  font-size: 17px; color: var(--text-secondary); margin-top: 16px;
  max-width: 560px; margin-left: auto; margin-right: auto; line-height: 1.6;
}

/* Glass Card */
.glass {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  transition: all 0.3s ease;
}
.glass:hover {
  border-color: var(--border-hover);
  background: var(--surface-hover);
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(0,0,0,0.3);
}

/* Features */
.features-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
@media (max-width: 900px) { .features-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 600px) { .features-grid { grid-template-columns: 1fr; } }
.feature-card { padding: 32px 28px; }
.feature-icon {
  width: 48px; height: 48px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  font-size: 22px; margin-bottom: 20px;
  background: var(--surface); border: 1px solid var(--border);
}
.feature-card h3 { font-size: 17px; font-weight: 700; margin-bottom: 10px; letter-spacing: -0.01em; }
.feature-card p { font-size: 14px; color: var(--text-secondary); line-height: 1.65; }

/* Live Data */
.live-section { text-align: center; }
.live-card {
  max-width: 480px; margin: 0 auto; padding: 40px 32px;
  position: relative; overflow: hidden;
}
.live-card::before {
  content: ''; position: absolute; top: 0; left: 50%; transform: translateX(-50%);
  width: 60%; height: 1px;
  background: linear-gradient(90deg, transparent, var(--blue), transparent);
}
.live-label {
  font-size: 13px; font-weight: 600; color: var(--text-muted);
  text-transform: uppercase; letter-spacing: 0.12em; margin-bottom: 8px;
}
.live-price {
  font-size: 56px; font-weight: 900; letter-spacing: -0.03em;
  font-family: 'JetBrains Mono', monospace;
  background: linear-gradient(135deg, var(--text), var(--text-secondary));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.live-price .currency { font-size: 24px; font-weight: 600; }
.live-sources { display: flex; justify-content: center; gap: 12px; margin-top: 16px; flex-wrap: wrap; }
.live-source {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 4px 12px; border-radius: 999px;
  background: var(--surface); border: 1px solid var(--border);
  font-size: 12px; font-weight: 500; color: var(--text-secondary);
}
.live-source .dot { width: 6px; height: 6px; border-radius: 50%; background: var(--green); }
.live-refresh { font-size: 12px; color: var(--text-muted); margin-top: 16px; }

/* Pricing */
.pricing-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
@media (max-width: 900px) { .pricing-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 600px) { .pricing-grid { grid-template-columns: 1fr; } }
.pricing-card { padding: 28px 24px; text-align: center; position: relative; }
.pricing-card.featured {
  border-color: var(--blue);
  background: linear-gradient(180deg, rgba(59,130,246,0.08) 0%, var(--surface) 100%);
}
.pricing-card.featured::before {
  content: 'Popular'; position: absolute; top: -1px; left: 50%; transform: translateX(-50%);
  background: linear-gradient(135deg, var(--blue), var(--purple));
  padding: 4px 14px; border-radius: 0 0 var(--radius-xs) var(--radius-xs);
  font-size: 11px; font-weight: 700; color: white; text-transform: uppercase; letter-spacing: 0.05em;
}
.pricing-name { font-size: 15px; font-weight: 700; margin-bottom: 4px; }
.pricing-desc { font-size: 13px; color: var(--text-muted); margin-bottom: 20px; }
.pricing-amount {
  font-size: 32px; font-weight: 900; letter-spacing: -0.02em;
  color: var(--green);
}
.pricing-hbar { font-size: 14px; color: var(--blue); margin-top: 6px; font-weight: 500; }

/* Integration */
.integrate-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }
@media (max-width: 700px) { .integrate-grid { grid-template-columns: 1fr; } }
.integrate-card { overflow: hidden; }
.integrate-card:hover { transform: translateY(-4px); }
.integrate-header {
  padding: 20px 24px; border-bottom: 1px solid var(--border);
  display: flex; justify-content: space-between; align-items: center;
}
.integrate-header h3 { font-size: 15px; font-weight: 700; }
.integrate-badge {
  font-size: 11px; font-weight: 600; padding: 3px 10px; border-radius: 999px;
  background: var(--blue-glow); color: var(--blue);
}
.integrate-body { padding: 20px 24px; }
.integrate-body pre {
  font-size: 13px; color: var(--text-secondary); line-height: 1.7;
  overflow-x: auto; font-family: 'JetBrains Mono', monospace;
  white-space: pre;
}
.integrate-body code { color: var(--cyan); }

/* Video */
.video-wrapper {
  max-width: 800px; margin: 0 auto; border-radius: var(--radius);
  overflow: hidden; border: 1px solid var(--border);
  background: var(--surface); position: relative;
}
.video-wrapper::before {
  content: ''; position: absolute; inset: -1px; border-radius: var(--radius);
  background: linear-gradient(135deg, var(--blue-glow), var(--purple-glow));
  z-index: -1;
}
.video-wrapper video { width: 100%; display: block; }

/* Footer */
.footer {
  position: relative; z-index: 1;
  border-top: 1px solid var(--border); padding: 64px 0 32px; margin-top: 40px;
}
.footer-grid { display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 40px; }
@media (max-width: 900px) { .footer-grid { grid-template-columns: 1fr 1fr; gap: 32px; } }
@media (max-width: 600px) { .footer-grid { grid-template-columns: 1fr; } }
.footer-brand h3 { font-size: 20px; font-weight: 800; letter-spacing: -0.02em; }
.footer-brand h3 .hash { color: var(--blue); }
.footer-brand h3 .a2a { color: var(--purple); }
.footer-brand p { font-size: 14px; color: var(--text-muted); margin-top: 12px; line-height: 1.6; max-width: 280px; }
.footer-col h4 {
  font-size: 12px; font-weight: 700; color: var(--text);
  text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 16px;
}
.footer-col a { display: block; font-size: 14px; color: var(--text-secondary); margin-bottom: 10px; }
.footer-col a:hover { color: var(--text); }
.footer-bottom {
  border-top: 1px solid var(--border); margin-top: 48px; padding-top: 24px;
  display: flex; justify-content: space-between; align-items: center;
  font-size: 13px; color: var(--text-muted);
}
.footer-social { display: flex; gap: 16px; }
.footer-social a { display: flex; align-items: center; gap: 6px; color: var(--text-muted); }
.footer-social a:hover { color: var(--text); }

/* Animations on scroll */
.fade-in { opacity: 0; transform: translateY(24px); transition: all 0.6s ease-out; }
.fade-in.visible { opacity: 1; transform: translateY(0); }
</style>
</head>
<body>
<div class="bg-grid"></div>
<div class="bg-gradient"></div>

<nav class="nav">
  <div class="nav-inner">
    <a href="/" class="nav-logo" style="display:flex;align-items:center;gap:10px;">
      <svg width="28" height="28" viewBox="0 0 60 60" fill="none" xmlns="http://www.w3.org/2000/svg" style="flex-shrink:0;">
        <polygon points="30,4 52,16 52,40 30,52 8,40 8,16" fill="none" stroke="url(#lg-hex)" stroke-width="3" stroke-linejoin="round"/>
        <polygon points="30,14 44,22 44,36 30,44 16,36 16,22" fill="url(#lg-hex)" opacity="0.12"/>
        <circle cx="30" cy="14" r="3.5" fill="#3b82f6"/>
        <circle cx="44" cy="22" r="3.5" fill="#6366f1"/>
        <circle cx="44" cy="36" r="3.5" fill="#8b5cf6"/>
        <circle cx="30" cy="44" r="3.5" fill="#06b6d4"/>
        <circle cx="16" cy="36" r="3.5" fill="#3b82f6"/>
        <circle cx="16" cy="22" r="3.5" fill="#6366f1"/>
        <circle cx="30" cy="28" r="4.5" fill="white" opacity="0.9"/>
        <line x1="30" y1="14" x2="30" y2="23.5" stroke="white" stroke-opacity="0.35" stroke-width="1.5"/>
        <line x1="44" y1="22" x2="34" y2="26" stroke="white" stroke-opacity="0.35" stroke-width="1.5"/>
        <line x1="44" y1="36" x2="34" y2="30" stroke="white" stroke-opacity="0.35" stroke-width="1.5"/>
        <line x1="30" y1="44" x2="30" y2="32.5" stroke="white" stroke-opacity="0.35" stroke-width="1.5"/>
        <line x1="16" y1="36" x2="26" y2="30" stroke="white" stroke-opacity="0.35" stroke-width="1.5"/>
        <line x1="16" y1="22" x2="26" y2="26" stroke="white" stroke-opacity="0.35" stroke-width="1.5"/>
        <defs><linearGradient id="lg-hex" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#3b82f6"/><stop offset="100%" stop-color="#8b5cf6"/></linearGradient></defs>
      </svg>
      <span class="hash">Hash</span><span class="a2a">A2A</span>
      <span class="dot"></span>
    </a>
    <button class="nav-toggle" id="nav-toggle" aria-label="Toggle menu">
      <span class="bar"></span><span class="bar"></span><span class="bar"></span>
    </button>
    <div class="nav-links" id="nav-links">
      <a href="#features">Features</a>
      <a href="#pricing">Pricing</a>
      <a href="#integrate">Integrate</a>
      <a href="/docs" target="_blank">API Docs</a>
      <a href="https://github.com/ymiydev-prog/HashA2A" class="nav-cta">GitHub</a>
    </div>
  </div>
</nav>

<main>

<section class="hero">
  <div class="container">
    <div class="hero-badge">
      <span class="pulse"></span>
      Live on Hedera Mainnet
    </div>
    <h1>Buy Verified Intelligence<br/>with <span class="gradient">HBAR or USDC</span></h1>
    <p>A decentralized data marketplace where AI agents discover, purchase, and consume verified multi-oracle intelligence — powered by Hedera HCS and the A2A protocol.</p>
    <div class="hero-btns">
      <a href="#integrate" class="btn btn-primary">Integrate Your Agent</a>
      <a href="/docs" target="_blank" class="btn btn-secondary">API Docs</a>
    </div>
  </div>
</section>

<section class="section video-section">
  <div class="container">
    <div class="video-wrapper">
      <video id="promo-video" autoplay muted loop playsinline preload="metadata">
        <source src="/promo.mp4" type="video/mp4">
      </video>
      <div class="play-overlay" id="play-overlay">
        <svg viewBox="0 0 24 24" fill="white" stroke="none"><polygon points="5 3 19 12 5 21 5 3"/></svg>
      </div>
    </div>
  </div>
</section>

<section class="section" id="features">
  <div class="container">
    <div class="section-header">
      <div class="section-label">Capabilities</div>
      <h2 class="section-title">Everything AI Agents Need</h2>
      <p class="section-desc">Real-time, cross-verified, cryptographically provable data — delivered via multiple protocols.</p>
    </div>
    <div class="features-grid">
      <div class="glass feature-card">
        <div class="feature-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg></div>
        <h3>OracleHub</h3>
        <p>Multi-oracle price aggregation from Pyth, CoinGecko, and DeFiLlama. 19 assets across crypto, commodities, and forex with median-price IQR confidence scoring.</p>
      </div>
      <div class="glass feature-card">
        <div class="feature-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg></div>
        <h3>Arbitrage Engine</h3>
        <p>Real-time cross-oracle spread detection. Identifies profitable opportunities across 6+ assets, ranking by confidence and spread percentage.</p>
      </div>
      <div class="glass feature-card">
        <div class="feature-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><polyline points="17 1 21 5 17 9"/><path d="M3 11V9a4 4 0 014-4h14"/><polyline points="7 23 3 19 7 15"/><path d="M21 13v2a4 4 0 01-4 4H3"/></svg></div>
        <h3>A2A Protocol</h3>
        <p>Full Google A2A compliance: JSON-RPC 2.0, SSE streaming, 7-state task lifecycle, context passing, artifact storage, AP2 mandates, and JWT auth.</p>
      </div>
      <div class="glass feature-card">
        <div class="feature-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 014 4v14a3 3 0 00-3-3H2z"/><path d="M22 3h-6a4 4 0 00-4 4v14a3 3 0 013-3h7z"/></svg></div>
        <h3>Deep Research</h3>
        <p>Web search + news + social signals + prediction market data combined with AI analysis. Premium intelligence delivered via A2A tasks.</p>
      </div>
      <div class="glass feature-card">
        <div class="feature-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg></div>
        <h3>Auth + Payments</h3>
        <p>Ephemeral JWT tokens, AP2 cryptographic mandates with spending limits. Pay per query via USDC (x402), HBAR (HIP-991), or pre-authorized budgets.</p>
      </div>
      <div class="glass feature-card">
        <div class="feature-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.55a11 11 0 0114.08 0"/><path d="M1.42 9a16 16 0 0121.16 0"/><path d="M8.53 16.11a6 6 0 016.95 0"/><circle cx="12" cy="20" r="1"/></svg></div>
        <h3>MCP + A2A + REST</h3>
        <p>18 MCP tools, Google A2A JSON-RPC, SSE streaming, REST API, WebSocket. Works with Claude, Cursor, LangChain, and any A2A agent.</p>
      </div>
    </div>
  </div>
</section>

<section class="section live-section">
  <div class="container">
    <div class="section-header">
      <div class="section-label">Real-Time Data</div>
      <h2 class="section-title">Live Oracle Feed</h2>
      <p class="section-desc">BTC/USD cross-verified across multiple oracles, updated every 30 seconds.</p>
    </div>
    <div class="glass live-card">
      <div class="live-label">BTC / USD</div>
      <div class="live-price"><span id="btc-price">—</span> <span class="currency">USD</span></div>
      <div class="live-sources" id="btc-sources"></div>
      <div class="live-refresh" id="btc-refresh">Fetching live data...</div>
    </div>
  </div>
</section>

<section class="section" id="pricing">
  <div class="container">
    <div class="section-header">
      <div class="section-label">Pricing</div>
      <h2 class="section-title">Pay Per Query</h2>
      <p class="section-desc">USDC prices are fixed. HBAR updates in real-time with the market.</p>
    </div>
    <div class="pricing-grid">
      <div class="glass pricing-card" data-usdc="0.25">
        <div class="pricing-name">Price Feed</div>
        <div class="pricing-desc">Single asset, multi-oracle</div>
        <div class="pricing-amount">$0.25</div>
        <div class="pricing-hbar" id="hbar-price_feed">~ — HBAR</div>
      </div>
      <div class="glass pricing-card featured" data-usdc="0.50">
        <div class="pricing-name">Arbitrage Scan</div>
        <div class="pricing-desc">All assets, ranked by spread</div>
        <div class="pricing-amount">$0.50</div>
        <div class="pricing-hbar" id="hbar-arbitrage_scan">~ — HBAR</div>
      </div>
      <div class="glass pricing-card" data-usdc="0.50">
        <div class="pricing-name">Deep Research</div>
        <div class="pricing-desc">Web + news + AI analysis</div>
        <div class="pricing-amount">$0.50</div>
        <div class="pricing-hbar" id="hbar-deep_research">~ — HBAR</div>
      </div>
      <div class="glass pricing-card" data-usdc="0.15">
        <div class="pricing-name">Predictions</div>
        <div class="pricing-desc">Per provider query</div>
        <div class="pricing-amount">$0.15</div>
        <div class="pricing-hbar" id="hbar-prediction_market">~ — HBAR</div>
      </div>
    </div>
    <p style="text-align:center;color:var(--text-muted);font-size:13px;margin-top:20px;" id="rate-info">Loading live HBAR rate...</p>
  </div>
</section>

<section class="section" id="integrate">
  <div class="container">
    <div class="section-header">
      <div class="section-label">Integration</div>
      <h2 class="section-title">Start in 30 Seconds</h2>
      <p class="section-desc">Four ways to connect your agent to HashA2A.</p>
    </div>
    <div class="integrate-grid">
      <div class="glass integrate-card">
        <div class="integrate-header"><h3>MCP Server</h3><span class="integrate-badge">Recommended</span></div>
        <div class="integrate-body">
          <div class="code-block">
            <button class="copy-btn" onclick="copyCode(this)" aria-label="Copy code">
              <svg class="copy-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
              <svg class="check-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
            </button>
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
      </div>
      <div class="glass integrate-card">
        <div class="integrate-header"><h3>REST API</h3><span class="integrate-badge">Universal</span></div>
        <div class="integrate-body">
          <div class="code-block">
            <button class="copy-btn" onclick="copyCode(this)" aria-label="Copy code">
              <svg class="copy-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
              <svg class="check-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
            </button>
<pre><code>curl -X POST</code> http://localhost:8080/api/v1/feeds/prices \\
  -H <code>"Content-Type: application/json"</code> \\
  -d <code>'{"asset":"BTC/USD"}'</code>

<code>curl -X POST</code> http://localhost:8080/api/v1/requests \\
  -H <code>"Content-Type: application/json"</code> \\
  -d <code>'{"provider_id":"polymarket"}'</code></pre>
          </div>
        </div>
      </div>
      <div class="glass integrate-card">
        <div class="integrate-header"><h3>A2A JSON-RPC 2.0</h3><span class="integrate-badge">Standard</span></div>
        <div class="integrate-body">
          <div class="code-block">
            <button class="copy-btn" onclick="copyCode(this)" aria-label="Copy code">
              <svg class="copy-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
              <svg class="check-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
            </button>
<pre><code>POST /api/v1/a2a/rpc</code>
<code>{"jsonrpc":"2.0","id":"1",
  "method":"message/send",
  "params":{"message":{
    "parts":[{"text":"BTC/USD price"}]
  }}}</code>

# SSE streaming:
<code>POST /api/v1/a2a/rpc/stream</code>
→ task/submitted → task/working
→ task/progress → "Consulting oracles..."
→ task/completed → ✅</pre>
          </div>
        </div>
      </div>
      <div class="glass integrate-card">
        <div class="integrate-header"><h3>Agent Discovery</h3><span class="integrate-badge">Autonomous</span></div>
        <div class="integrate-body">
          <div class="code-block">
            <button class="copy-btn" onclick="copyCode(this)" aria-label="Copy code">
              <svg class="copy-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
              <svg class="check-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
            </button>
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
  </div>
</section>

</main>

<footer class="footer">
  <div class="container">
    <div class="footer-grid">
      <div class="footer-brand">
        <h3><span class="hash">Hash</span><span class="a2a">A2A</span></h3>
        <p>The Agent-to-Agent Intelligence Layer on Hedera. AI agents buy verified multi-oracle intelligence via HBAR or USDC.</p>
      </div>
      <div class="footer-col">
        <h4>Product</h4>
        <a href="#features">Features</a>
        <a href="#pricing">Pricing</a>
        <a href="#integrate">Integration</a>
      </div>
      <div class="footer-col">
        <h4>API</h4>
        <a href="/docs">OpenAPI Docs</a>
        <a href="/redoc">ReDoc</a>
        <a href="/mcp/">MCP Server</a>
        <a href="/.well-known/agent.json">Agent Card</a>
        <a href="/api/v1/feeds/pricing">Live Pricing</a>
      </div>
      <div class="footer-col">
        <h4>Community</h4>
        <a href="https://github.com/ymiydev-prog/HashA2A">GitHub</a>
        <a href="https://x.com/hasha2a" target="_blank" rel="noopener">X / Twitter</a>
      </div>
    </div>
    <div class="footer-bottom">
      <span>HashA2A v0.2.0 — MIT License</span>
      <div class="footer-social">
        <a href="https://github.com/ymiydev-prog/HashA2A">GitHub</a>
        <a href="https://x.com/hasha2a" target="_blank" rel="noopener">X</a>
      </div>
    </div>
  </div>
</footer>

<script>
// Copy code button
function copyCode(btn) {
  const pre = btn.nextElementSibling;
  const text = pre.innerText;
  navigator.clipboard.writeText(text).then(() => {
    btn.classList.add('copied');
    setTimeout(() => btn.classList.remove('copied'), 2000);
  });
}

// Mobile nav toggle
const navToggle = document.getElementById('nav-toggle');
const navLinks = document.getElementById('nav-links');
if (navToggle && navLinks) {
  navToggle.addEventListener('click', () => {
    navToggle.classList.toggle('active');
    navLinks.classList.toggle('open');
  });
  navLinks.querySelectorAll('a').forEach(a => {
    a.addEventListener('click', () => {
      navToggle.classList.remove('active');
      navLinks.classList.remove('open');
    });
  });
}

// Video autoplay + play overlay
const video = document.getElementById('promo-video');
const overlay = document.getElementById('play-overlay');
if (video && overlay) {
  video.addEventListener('play', () => { video.classList.add('playing'); overlay.style.display = 'none'; });
  video.addEventListener('pause', () => { video.classList.remove('playing'); overlay.style.display = 'flex'; });
  overlay.addEventListener('click', () => { video.muted = false; video.play(); });
}

// Scroll animations
const observer = new IntersectionObserver((entries) => {
  entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('visible'); });
}, { threshold: 0.1 });
document.querySelectorAll('.section, .feature-card, .pricing-card, .integrate-card').forEach(el => {
  el.classList.add('fade-in');
  observer.observe(el);
});

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
      sourcesEl.innerHTML = data.prices.map(p => `<span class="live-source"><span class="dot"></span>${p.source_name}</span>`).join('');
      refreshEl.textContent = data.oracles + ' oracles · updated ' + new Date().toLocaleTimeString();
    } else {
      priceEl.textContent = '—';
      refreshEl.textContent = 'No data available';
    }
  } catch(e) {
    priceEl.textContent = '—';
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
    document.getElementById('hbar-price_feed').textContent = '~ ' + p.price_feed.hbar + ' HBAR';
    document.getElementById('hbar-arbitrage_scan').textContent = '~ ' + p.arbitrage_scan.hbar + ' HBAR';
    document.getElementById('hbar-deep_research').textContent = '~ ' + p.deep_research.hbar + ' HBAR';
    document.getElementById('hbar-prediction_market').textContent = '~ ' + p.prediction_market.hbar + ' HBAR';
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
