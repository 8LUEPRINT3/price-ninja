#!/usr/bin/env python3
# scrapers/freshco_scraper.py — FreshCo flyer scraper (Canada)
# FreshCo is a Sobeys discount banner — flyers via Flipp + Reebee

import requests
import time
from typing import List, Dict

FLIPP_URL = "https://backflipp.wishabi.com/flipp/items/search"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
}

FRESHCO_STORE_NAMES = {"freshco", "fresh co", "freshco.com"}


def search_freshco(query: str, postal_code: str, keyword_map: dict = None) -> List[Dict]:
    """
    Search FreshCo flyer deals via Flipp, filtered to FreshCo only.
    FreshCo operates in Ontario — best results with ON postal codes.
    """
    results = []
    seen = set()

    terms = [query]
    if keyword_map and query.lower() in keyword_map:
        terms = keyword_map[query.lower()].get("synonyms", [query])

    for term in terms[:3]:
        try:
            resp = requests.get(FLIPP_URL, headers=HEADERS, params={
                "q": term,
                "postal_code": postal_code.replace(" ", ""),
                "locale": "en-ca",
            }, timeout=12)

            if resp.status_code != 200:
                continue

            data = resp.json()
            items = data.get("items") or data.get("flyer_items") or data.get("ecom_items") or []

            for item in items:
                store = str(item.get("merchant_name") or item.get("retailer") or "").lower()
                if not any(f in store for f in FRESHCO_STORE_NAMES):
                    continue

                uid = item.get("flyer_item_id") or item.get("id") or id(item)
                if uid in seen:
                    continue
                seen.add(uid)

                current  = item.get("current_price") or item.get("price") or item.get("sale_price")
                original = item.get("original_price") or item.get("regular_price")
                name     = item.get("name") or item.get("description") or "Unknown"
                flyer_id = item.get("flyer_id", "")
                url      = f"https://flipp.com/en-ca/flyer/{flyer_id}" if flyer_id else "https://www.freshco.com/flyer/"

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

                results.append({
                    "name":        name,
                    "store":       item.get("merchant_name") or "FreshCo",
                    "price":       f"{float(current):.2f}" if current else None,
                    "original":    f"{float(original):.2f}" if original else None,
                    "savings":     savings_str,
                    "savings_pct": savings_pct,
                    "url":         url,
                    "expires":     item.get("valid_to") or "",
                    "image":       item.get("clean_image_url") or item.get("clipping_image_url") or "",
                    "category":    item.get("category") or "",
                    "source":      "FreshCo",
                    "term_matched": term,
                })

        except Exception as e:
            print(f"[FreshCo] Error for '{term}': {e}")

        time.sleep(0.4)

    results.sort(key=lambda x: (-x["savings_pct"], float(x["price"]) if x["price"] else 999))
    return results
