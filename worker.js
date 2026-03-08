// Cloudflare Worker — price-ninja Flipp proxy
// Deploy at: https://dash.cloudflare.com → Workers → Create Worker
// Paste this code → Deploy → note your worker URL (e.g. price-ninja.username.workers.dev)
// Then update PROXY_BASE in index.html to match

export default {
  async fetch(request) {
    const url = new URL(request.url);

    // CORS preflight
    if (request.method === "OPTIONS") {
      return new Response(null, {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "GET",
          "Access-Control-Allow-Headers": "*",
        },
      });
    }

    // Only allow /search path
    if (!url.pathname.startsWith("/search")) {
      return new Response("Not found", { status: 404 });
    }

    // Forward to Flipp
    const flippUrl = `https://backflipp.wishabi.com/flipp/items/search?${url.searchParams.toString()}`;
    const resp = await fetch(flippUrl, {
      headers: {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
      },
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
  },
};
