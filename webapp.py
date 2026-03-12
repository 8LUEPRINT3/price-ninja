#!/usr/bin/env python3
# webapp.py — price-ninja search webapp

import os
import sys
import json
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from utils.logger import log

# Add scrapers to path
sys.path.insert(0, os.path.dirname(__file__))

load_dotenv()

app = Flask(__name__, template_folder="templates")

FLIPP_URL = "https://backflipp.wishabi.com/flipp/items/search"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
}

# Load location data
with open("config/locations.json") as f:
    LOCATIONS = json.load(f)

# Load keyword map
try:
    with open("config/keywords_map.json") as f:
        KEYWORD_MAP = json.load(f)
except Exception:
    KEYWORD_MAP = {}

# Import additional scrapers
try:
    from scrapers.reebee_scraper import search_reebee
    REEBEE_ENABLED = True
except Exception as e:
    REEBEE_ENABLED = False
    log(f"Reebee scraper unavailable: {e}", "warn")

try:
    from scrapers.costco_scraper import search_costco
    COSTCO_ENABLED = True
except Exception as e:
    COSTCO_ENABLED = False
    log(f"Costco scraper unavailable: {e}", "warn")

try:
    from scrapers.freshco_scraper import search_freshco
    FRESHCO_ENABLED = True
except Exception as e:
    FRESHCO_ENABLED = False
    log(f"FreshCo scraper unavailable: {e}", "warn")

try:
    from scrapers.circular_scraper import search_circular_us
    CIRCULAR_ENABLED = True
except Exception as e:
    CIRCULAR_ENABLED = False
    log(f"Circular scraper unavailable: {e}", "warn")


def flipp_search(query: str, postal_code: str, country: str) -> list:
    locale = "en-ca" if country == "CA" else "en-us"
    terms = [query]
    if query.lower() in KEYWORD_MAP:
        terms = KEYWORD_MAP[query.lower()].get("synonyms", [query])

    all_results = []
    seen_ids = set()

    for term in terms[:3]:
        try:
            resp = requests.get(FLIPP_URL, headers=HEADERS, params={
                "q": term,
                "postal_code": postal_code.replace(" ", ""),
                "locale": locale,
            }, timeout=12)

            if resp.status_code != 200:
                continue

            data = resp.json()
            items = (data.get("items") or data.get("flyer_items") or data.get("ecom_items") or [])

            for deal in items[:20]:
                uid = deal.get("flyer_item_id") or deal.get("id") or id(deal)
                if uid in seen_ids:
                    continue
                seen_ids.add(uid)

                current  = deal.get("current_price") or deal.get("price") or deal.get("sale_price")
                original = deal.get("original_price") or deal.get("regular_price") or deal.get("pre_price")
                name     = deal.get("name") or deal.get("description") or "Unknown item"
                store    = deal.get("merchant_name") or deal.get("retailer") or "Unknown"
                flyer_id = deal.get("flyer_id", "")
                url      = f"https://flipp.com/en-ca/flyer/{flyer_id}" if flyer_id else "https://flipp.com"

                savings_str = ""
                savings_pct = 0
                if current and original:
                    try:
                        saved = float(original) - float(current)
                        if saved > 0:
                            savings_pct = round((saved / float(original)) * 100)
                            savings_str = f"Save ${saved:.2f} ({savings_pct}% off)"
                    except Exception:
                        pass

                all_results.append({
                    "name":        name,
                    "store":       store,
                    "price":       f"{float(current):.2f}" if current else None,
                    "original":    f"{float(original):.2f}" if original else None,
                    "savings":     savings_str,
                    "savings_pct": savings_pct,
                    "url":         url,
                    "expires":     deal.get("valid_to", ""),
                    "image":       deal.get("clean_image_url") or deal.get("clipping_image_url") or "",
                    "category":    deal.get("category", ""),
                    "source":      "Flipp",
                    "term_matched": term,
                })

        except Exception as e:
            log(f"[Flipp] Search error for '{term}': {e}", "error")
        time.sleep(0.4)

    all_results.sort(key=lambda x: (-x["savings_pct"], float(x["price"]) if x["price"] else 999))
    return all_results


def multi_source_search(query: str, postal_code: str, country: str) -> list:
    """
    Run all enabled scrapers in parallel and merge results.
    Deduplicates by (store, name, price).
    """
    tasks = {}

    with ThreadPoolExecutor(max_workers=5) as executor:
        # Always run Flipp
        tasks["flipp"] = executor.submit(flipp_search, query, postal_code, country)

        # Canada-only scrapers
        if country == "CA":
            if REEBEE_ENABLED:
                tasks["reebee"] = executor.submit(search_reebee, query, postal_code, KEYWORD_MAP)
            if COSTCO_ENABLED:
                tasks["costco"] = executor.submit(search_costco, query, postal_code, country, KEYWORD_MAP)
            if FRESHCO_ENABLED:
                tasks["freshco"] = executor.submit(search_freshco, query, postal_code, KEYWORD_MAP)

        # US-only scrapers
        if country == "US":
            if COSTCO_ENABLED:
                tasks["costco_us"] = executor.submit(search_costco, query, postal_code, country, KEYWORD_MAP)
            if CIRCULAR_ENABLED:
                tasks["circular"] = executor.submit(search_circular_us, query, postal_code, KEYWORD_MAP)

        all_results = []
        seen = set()

        for name, future in tasks.items():
            try:
                results = future.result(timeout=20)
                for r in results:
                    # Deduplicate by store + name + price
                    key = (
                        str(r.get("store", "")).lower()[:20],
                        str(r.get("name", "")).lower()[:30],
                        str(r.get("price", "")),
                    )
                    if key in seen:
                        continue
                    seen.add(key)
                    all_results.append(r)
            except Exception as e:
                log(f"[{name}] scraper timed out or failed: {e}", "warn")

    # Final sort: biggest savings first, then price
    all_results.sort(key=lambda x: (-x.get("savings_pct", 0), float(x["price"]) if x.get("price") else 999))
    return all_results


@app.route("/")
def index():
    return render_template("search.html", locations=LOCATIONS)


@app.route("/api/provinces")
def api_provinces():
    country = request.args.get("country", "CA")
    data = LOCATIONS.get(country, {}).get("provinces", {})
    return jsonify({k: v["name"] for k, v in data.items()})


@app.route("/api/cities")
def api_cities():
    country  = request.args.get("country", "CA")
    province = request.args.get("province", "ON")
    cities   = LOCATIONS.get(country, {}).get("provinces", {}).get(province, {}).get("cities", {})
    return jsonify(cities)  # {city_name: postal_code}


@app.route("/api/search")
def api_search():
    query       = request.args.get("q", "").strip()
    postal_code = request.args.get("postal", "M5V2T6")
    country     = request.args.get("country", "CA")
    city        = request.args.get("city", "")
    province    = request.args.get("province", "")

    if not query:
        return jsonify({"error": "No query provided", "results": []})

    log(f"🔍 Search: '{query}' @ {postal_code} ({city}, {province}, {country})", "info")
    results = multi_source_search(query, postal_code, country)

    return jsonify({
        "query":    query,
        "location": f"{city}, {province}, {country}",
        "postal":   postal_code,
        "count":    len(results),
        "results":  results,
    })


@app.route("/api/search-list")
def api_search_list():
    """Search multiple items at once. Returns results grouped by item."""
    items_raw   = request.args.get("items", "").strip()
    postal_code = request.args.get("postal", "M5V2T6")
    country     = request.args.get("country", "CA")
    city        = request.args.get("city", "")
    province    = request.args.get("province", "")

    items = [i.strip() for i in items_raw.split(",") if i.strip()]
    if not items:
        return jsonify({"error": "No items provided", "groups": []})

    log(f"🛒 List search: {items} @ {postal_code} ({city})", "info")

    groups = []
    total = 0
    for item in items[:20]:  # cap at 20 items
        results = multi_source_search(item, postal_code, country)
        total += len(results)
        groups.append({
            "item":    item,
            "count":   len(results),
            "results": results,
        })
        time.sleep(0.2)

    return jsonify({
        "items":    items,
        "location": f"{city}, {province}, {country}",
        "postal":   postal_code,
        "total":    total,
        "groups":   groups,
    })


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5050)
