#!/usr/bin/env python3
# scrapers/flipp_scraper.py — Flipp flyer deal hunter

import requests
import json
import time
from typing import List, Dict
from utils.logger import log
from utils.price_link_generator import generate_store_links

FLIPP_URL = "https://backflipp.wishabi.com/flipp/items/search"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
}


def search_flyer_deals(wishlist: List[str]) -> List[Dict]:
    results = []

    # Load configs
    try:
        with open("config/keywords_map.json", "r") as f:
            keyword_map = json.load(f)
    except FileNotFoundError:
        keyword_map = {}
        log("⚠️ keywords_map.json not found — using raw searches", "warn")

    try:
        with open("config/postal_codes.json", "r") as f:
            postal_code = json.load(f)["default"]
    except FileNotFoundError:
        postal_code = "L4M3X9"
        log("⚠️ postal_codes.json not found — using default L4M3X9", "warn")

    try:
        with open("config/merchant_blocklist.json", "r") as f:
            blocked = [s.lower() for s in json.load(f)]
    except FileNotFoundError:
        blocked = []

    for item in wishlist:
        log(f"🔎 Searching Flipp for: {item}", "debug")

        # Expand synonyms
        synonyms = [item]
        if item in keyword_map:
            synonyms = keyword_map[item].get("synonyms", [item])
        else:
            log(f"⚠️ No synonym map for '{item}', using raw search", "warn")

        found = False
        for term in synonyms:
            params = {
                "q": term,
                "postal_code": postal_code.replace(" ", ""),
                "locale": "en-ca",
            }
            try:
                resp = requests.get(FLIPP_URL, headers=HEADERS,
                                    params=params, timeout=12)
                if resp.status_code != 200:
                    log(f"⚠️ Flipp returned {resp.status_code} for '{term}'", "warn")
                    continue

                data = resp.json()
                # Response has: items, ecom_items, flyer_items
                items = (data.get("items") or
                         data.get("flyer_items") or
                         data.get("ecom_items") or [])

                for deal in items[:5]:
                    store_name = str(deal.get("merchant_name", deal.get("retailer", ""))).lower()
                    if any(b in store_name for b in blocked):
                        continue

                    current  = deal.get("current_price") or deal.get("price") or deal.get("sale_price")
                    original = deal.get("original_price") or deal.get("regular_price") or deal.get("pre_price")
                    name     = deal.get("name") or deal.get("description") or "Unknown item"

                    # Calculate savings
                    savings = ""
                    if current and original:
                        try:
                            saved = float(original) - float(current)
                            if saved > 0:
                                pct   = (saved / float(original)) * 100
                                savings = f"Save ${saved:.2f} ({pct:.0f}%)"
                        except Exception:
                            pass

                    flyer_id = deal.get("flyer_id", "")
                    url = f"https://flipp.com/en-ca/flyer/{flyer_id}" if flyer_id else "https://flipp.com"

                    result = {
                        "title":    name,
                        "price":    current,
                        "original": original,
                        "savings":  savings,
                        "store":    deal.get("merchant_name", deal.get("retailer", "Unknown")),
                        "url":      url,
                        "expires":  deal.get("valid_to", deal.get("sale_story", "Unknown")),
                        "category": keyword_map.get(item, {}).get("category", "general"),
                        "query":    item,
                        "source":   "Flipp",
                        "emoji":    "🛒",
                    }
                    results.append(result)
                    log(f"✅ Deal: {result['title']} @ {result['store']} — ${current}", "info")
                    found = True

                if found:
                    break

            except Exception as e:
                log(f"❌ Flipp search failed for '{term}': {e}", "error")

            time.sleep(1.2)  # polite delay

        # Fallback: shelf price links if no deal found
        if not found:
            log(f"⚠️ No active deal found for '{item}' — generating fallback links", "warn")
            fallback_links = generate_store_links(item)
            results.append({
                "title":       f"No active flyer deal for: {item}",
                "description": "Check these stores for shelf prices:",
                "links":       fallback_links,
                "category":    "fallback",
                "query":       item,
                "source":      "Fallback",
                "emoji":       "🛋️",
            })

    return results
