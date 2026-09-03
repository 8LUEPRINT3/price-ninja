// Cloudflare Worker — price-ninja proxy
// Handles:
//   /search  -> Flipp flyer search (CORS)
//   /recalls -> Health Canada / CFIA food recalls (filtered + cached, CORS)
// Deploy at: https://dash.cloudflare.com → Workers & Pages → Create Worker
// Paste this code → Deploy → note your worker URL (e.g. price-ninja.username.workers.dev)
// Then update PROXY_BASE in index.html to match

const UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36";

function cors() {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET",
    "Access-Control-Allow-Headers": "*",
  };
}

export default {
  async fetch(request) {
    const url = new URL(request.url);

    // CORS preflight
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: cors() });
    }

    if (url.pathname.startsWith("/search")) {
      return handleSearch(url);
    }
    if (url.pathname.startsWith("/recalls")) {
      return handleRecalls();
    }

    return new Response("Not found", { status: 404, headers: cors() });
  },
};

// ── Flipp flyer search ──────────────────────────────────
async function handleSearch(url) {
  const flippUrl = `https://backflipp.wishabi.com/flipp/items/search?${url.searchParams.toString()}`;
  const resp = await fetch(flippUrl, {
    headers: { "User-Agent": UA, "Accept": "application/json" },
  });
  const data = await resp.text();
  return new Response(data, {
    status: resp.status,
    headers: {
      "Content-Type": "application/json",
      "Access-Control-Allow-Origin": "*",
      "Cache-Control": "public, max-age=300",
    },
  });
}

// ── CFIA food recalls (Canada) ──────────────────────────
async function handleRecalls() {
  // Cache the filtered result for 1 hour (CFIA updates ~daily)
  const cache = caches.default;
  const cacheKey = new Request("https://price-ninja-cfia-recalls/v1");
  const cached = await cache.match(cacheKey);
  if (cached) return cached;

  const cfiaUrl = "https://recalls-rappels.canada.ca/sites/default/files/opendata-donneesouvertes/HCRSAMOpenData.json";
  const resp = await fetch(cfiaUrl, { headers: { "User-Agent": UA, "Accept": "application/json" } });
  if (!resp.ok) {
    return new Response(JSON.stringify({ error: "CFIA fetch failed" }), {
      status: 502,
      headers: { "Content-Type": "application/json", ...cors() },
    });
  }

  const data = await resp.json();
  const list = (Array.isArray(data) ? data : [])
    .filter((r) => r.Organization === "CFIA" && r.Archived !== "Yes")
    .sort((a, b) => (b["Last updated"] || "").localeCompare(a["Last updated"] || ""))
    .slice(0, 80)
    .map((r) => ({
      title: r.Title,
      product: r.Product,
      issue: r.Issue,
      recallClass: r["Recall class"],
      url: r.URL,
      updated: r["Last updated"],
      what: r["What you should do"],
    }));

  const out = new Response(JSON.stringify(list), {
    headers: {
      "Content-Type": "application/json",
      "Access-Control-Allow-Origin": "*",
      "Cache-Control": "public, max-age=3600",
    },
  });
  await cache.put(cacheKey, out.clone());
  return out;
}
