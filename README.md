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

## Deploy Your Own

### 1. Fork this repo

### 2. Deploy the Cloudflare Worker (CORS proxy)

1. Go to [dash.cloudflare.com](https://dash.cloudflare.com) → **Workers & Pages** → **Create Worker**
2. Paste the contents of `worker.js`
3. Click **Deploy**
4. Note your worker URL: `https://price-ninja-proxy.YOUR_SUBDOMAIN.workers.dev`
5. Update `PROXY_BASE` in `index.html` line ~215 to match your worker URL

### 3. Enable GitHub Pages

Repo → Settings → Pages → Source: **Deploy from branch** → `main` → `/ (root)` → Save

Your app will be live at: `https://YOUR_USERNAME.github.io/price-ninja`

## Tech

- Pure HTML/CSS/JS (no build step, no frameworks)
- Flipp flyer API via Cloudflare Worker proxy
- Location data: 500+ cities baked in
- Cloudflare Workers (free tier: 100k req/day)
