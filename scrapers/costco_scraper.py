#!/usr/bin/env python3
# scrapers/costco_scraper.py — Costco flyer scraper (Canada + US)
# Scrapes Costco's current flyer/warehouse deals

import requests
import re
import time
from typing import List, Dict
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-CA,en;q=0.9",
}

COSTCO_SEARCH_CA = "https://www.costco.ca/CatalogSearch?storeId=10053&langId=-28&keyword={query}&currentPage=1&pageSize=24&sortBy=score+desc"
COSTCO_SEARCH_US = "https://www.costco.com/CatalogSearch?storeId=10301&langId=-1&keyword={query}&currentPage=1&pageSize=24&sortBy=score+desc"

# Costco also has a deals/savings page
COSTCO_DEALS_CA = "https://www.costco.ca/savings-events.html"
COSTCO_DEALS_US = "https://www.costco.com/savings-events.html"

# Use Flipp's Costco data as primary (Costco is on Flipp)
FLIPP_URL = "https://backflipp.wishabi.com/flipp/items/search"


def search_costco(query: str, postal_code: str, country: str = "CA", keyword_map: dict = None) -> List[Dict]:
    """
    Search Costco deals via Flipp (most reliable) with fallback to direct scrape.
    """
    results = []
    seen = set()

    terms = [query]
    if keyword_map and query.lower() in keyword_map:
        terms = keyword_map[query.lower()].get("synonyms", [query])

    locale = "en-ca" if country == "CA" else "en-us"

    for term in terms[:3]:
        try:
            # Primary: Flipp filtered to Costco only
            params = {
                "q": term,
                "postal_code": postal_code.replace(" ", ""),
                "locale": locale,
            }
            resp = requests.get(FLIPP_URL, headers={
                "User-Agent": HEADERS["User-Agent"],
                "Accept": "application/json",
            }, params=params, timeout=12)

            if resp.status_code == 200:
                data = resp.json()
                items = data.get("items") or data.get("flyer_items") or data.get("ecom_items") or []

                for item in items:
                    store = str(item.get("merchant_name") or item.get("retailer") or "").lower()
                    if "costco" not in store:
                        continue

                    uid = item.get("flyer_item_id") or item.get("id") or id(item)
                    if uid in seen:
                        continue
                    seen.add(uid)

                    current  = item.get("current_price") or item.get("price") or item.get("sale_price")
                    original = item.get("original_price") or item.get("regular_price")
                    name     = item.get("name") or item.get("description") or "Unknown"
                    flyer_id = item.get("flyer_id", "")
                    url      = f"https://flipp.com/en-ca/flyer/{flyer_id}" if flyer_id else (
                        "https://www.costco.ca" if country == "CA" else "https://www.costco.com"
                    )

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
                        "store":       item.get("merchant_name") or "Costco",
                        "price":       f"{float(current):.2f}" if current else None,
                        "original":    f"{float(original):.2f}" if original else None,
                        "savings":     savings_str,
                        "savings_pct": savings_pct,
                        "url":         url,
                        "expires":     item.get("valid_to") or "",
                        "image":       item.get("clean_image_url") or item.get("clipping_image_url") or "",
                        "category":    item.get("category") or "",
                        "source":      "Costco",
                        "term_matched": term,
                    })

        except Exception as e:
            print(f"[Costco] Flipp search error for '{term}': {e}")

        # Fallback: direct Costco search scrape
        if not results:
            try:
                base_url = COSTCO_SEARCH_CA if country == "CA" else COSTCO_SEARCH_US
                url = base_url.format(query=requests.utils.quote(term))
                resp = requests.get(url, headers=HEADERS, timeout=15)

                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    products = soup.select(".product-list-item, .thumbnail-container, [id*='product']")

                    for prod in products[:10]:
                        name_el  = prod.select_one(".description a, .product-title, h3")
                        price_el = prod.select_one(".price, .your-price, [class*='price']")
                        img_el   = prod.select_one("img")
                        link_el  = prod.select_one("a[href]")

                        if not name_el:
                            continue

                        name  = name_el.get_text(strip=True)
                        price_text = price_el.get_text(strip=True) if price_el else ""
                        price_match = re.search(r"[\d,]+\.?\d*", price_text.replace(",", ""))
                        price = price_match.group() if price_match else None

                        prod_url = link_el["href"] if link_el else url
                        if prod_url and not prod_url.startswith("http"):
                            base = "https://www.costco.ca" if country == "CA" else "https://www.costco.com"
                            prod_url = base + prod_url

                        results.append({
                            "name":        name,
                            "store":       "Costco",
                            "price":       price,
                            "original":    None,
                            "savings":     "",
                            "savings_pct": 0,
                            "url":         prod_url or url,
                            "expires":     "",
                            "image":       img_el.get("src") or img_el.get("data-src") or "" if img_el else "",
                            "category":    "",
                            "source":      "Costco",
                            "term_matched": term,
                        })

            except Exception as e:
                print(f"[Costco] Direct scrape error for '{term}': {e}")

        time.sleep(0.5)

    results.sort(key=lambda x: (-x["savings_pct"], float(x["price"]) if x["price"] else 999))
    return results
