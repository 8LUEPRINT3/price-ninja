#!/usr/bin/env python3
# scrapers/circular_scraper.py — Circular/Flipp US store scraper
# Covers: Walmart, Kroger, Albertsons, Publix, Aldi, Target, Safeway US,
#         Walgreens, CVS, Dollar General, Food Lion, H-E-B, Meijer, Hy-Vee

import requests
import time
from typing import List, Dict

# Flipp works for US too — it aggregates circular flyers
FLIPP_URL = "https://backflipp.wishabi.com/flipp/items/search"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
}

# Major US grocery/retail chains to surface clearly
US_PRIORITY_STORES = {
    "walmart", "kroger", "albertsons", "publix", "aldi", "target",
    "safeway", "meijer", "heb", "h-e-b", "hy-vee", "food lion",
    "stop & shop", "giant", "shoprite", "wegmans", "harris teeter",
    "cvs", "walgreens", "dollar general", "dollar tree", "family dollar",
    "costco", "sam's club", "whole foods", "trader joe's",
}


def search_circular_us(query: str, zip_code: str, keyword_map: dict = None) -> List[Dict]:
    """
    Search US circular/flyer deals via Flipp.
    zip_code: US ZIP code string
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
                "postal_code": zip_code.strip(),
                "locale": "en-us",
            }, timeout=12)

            if resp.status_code != 200:
                continue

            data = resp.json()
            items = data.get("items") or data.get("flyer_items") or data.get("ecom_items") or []

            for item in items[:25]:
                uid = item.get("flyer_item_id") or item.get("id") or id(item)
                if uid in seen:
                    continue
                seen.add(uid)

                current  = item.get("current_price") or item.get("price") or item.get("sale_price")
                original = item.get("original_price") or item.get("regular_price")
                name     = item.get("name") or item.get("description") or "Unknown"
                store    = item.get("merchant_name") or item.get("retailer") or "Unknown"
                flyer_id = item.get("flyer_id", "")
                url      = f"https://flipp.com/en-us/flyer/{flyer_id}" if flyer_id else "https://flipp.com"

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

                # Flag priority stores
                is_priority = any(s in store.lower() for s in US_PRIORITY_STORES)

                results.append({
                    "name":        name,
                    "store":       store,
                    "price":       f"{float(current):.2f}" if current else None,
                    "original":    f"{float(original):.2f}" if original else None,
                    "savings":     savings_str,
                    "savings_pct": savings_pct,
                    "url":         url,
                    "expires":     item.get("valid_to") or "",
                    "image":       item.get("clean_image_url") or item.get("clipping_image_url") or "",
                    "category":    item.get("category") or "",
                    "source":      "Circular",
                    "priority":    is_priority,
                    "term_matched": term,
                })

        except Exception as e:
            print(f"[Circular] Error for '{term}': {e}")

        time.sleep(0.4)

    # Sort: priority stores + biggest savings first
    results.sort(key=lambda x: (
        not x.get("priority", False),
        -x["savings_pct"],
        float(x["price"]) if x["price"] else 999
    ))
    return results
