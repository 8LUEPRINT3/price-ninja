#!/usr/bin/env python3
# utils/price_link_generator.py — Fallback shelf price links

from urllib.parse import quote_plus


def generate_store_links(item: str) -> dict:
    q = quote_plus(item)
    return {
        "Walmart Canada":    f"https://www.walmart.ca/search?q={q}",
        "Loblaws":           f"https://www.loblaws.ca/search?search-bar={q}",
        "No Frills":         f"https://www.nofrills.ca/search?search-bar={q}",
        "Metro":             f"https://www.metro.ca/en/online-grocery/search?filter={q}",
        "Sobeys":            f"https://www.sobeys.com/en/search/?query={q}",
        "Costco Canada":     f"https://www.costco.ca/CatalogSearch?keyword={q}",
        "FreshCo":           f"https://www.freshco.com/search/?q={q}",
        "Food Basics":       f"https://www.foodbasics.ca/search?filter={q}",
        "T&T Supermarket":   f"https://www.tntsupermarket.com/search.html?q={q}",
        "Amazon Canada":     f"https://www.amazon.ca/s?k={q}",
    }
