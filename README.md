# 🥷 price-ninja

**Live flyer deal search — Canada & all 50 US States**

[**🔗 Open App**](https://8lueprint3.github.io/price-ninja)

## Features

- 🇨🇦 All Canadian provinces + 89 cities
- 🇺🇸 All 50 US states + DC + 411 cities
- Live Flipp flyer data (real-time prices)
- Sort by: Best savings / Lowest price / Store A–Z
- Filter by: On Sale / Under $5 / Under $10 / Under $20
- Mobile-friendly dark UI
- Synonym search (search "chicken" → finds "chicken breast", "chicken thighs" etc.)
- ⚠️ **Recalls** tab — live food recalls & advisories from official sources (🇺🇸 U.S. FDA via openFDA · 🇨🇦 Health Canada / CFIA), with risk classification (Class I / II / III)

## Deploy Your Own

### 1. Fork this repo

### 2. Deploy the Cloudflare Worker (CORS proxy)

1. Go to [dash.cloudflare.com](https://dash.cloudflare.com) → **Workers & Pages** → **Create Worker**
2. Paste the contents of `worker.js`
3. Click **Deploy**
4. Note your worker URL: `https://price-ninja-proxy.YOUR_SUBDOMAIN.workers.dev`
5. Update `PROXY_BASE` in `index.html` line ~215 to match your worker URL

> **Note:** the worker now handles two paths — `/search` (Flipp deals) and `/recalls` (CFIA food recalls). Redeploying the worker is required for the 🇨🇦 Canada recalls feed; the 🇺🇸 U.S. recalls feed calls openFDA directly and works without the worker.

### 3. Enable GitHub Pages

Repo → Settings → Pages → Source: **Deploy from branch** → `main` → `/ (root)` → Save

Your app will be live at: `https://YOUR_USERNAME.github.io/price-ninja`

## Tech

- Pure HTML/CSS/JS (no build step, no frameworks)
- Flipp flyer API via Cloudflare Worker proxy
- Location data: 500+ cities baked in
- Cloudflare Workers (free tier: 100k req/day)
