#!/usr/bin/env python3
# scrapers/rfd_monitor.py — RedFlagDeals RSS OSINT monitor

import os
import hashlib
import feedparser
from utils.logger import log

RFD_FEEDS = [
    "https://forums.redflagdeals.com/rss-feeds/forums/-/600",   # Hot Deals
    "https://forums.redflagdeals.com/rss-feeds/forums/-/9",     # Computers & Electronics
    "https://forums.redflagdeals.com/rss-feeds/forums/-/28",    # Grocery
]

SEEN_FILE = "data/seen_deals.txt"

TECH_KEYWORDS = [
    "laptop", "headset", "ram", "ssd", "gpu", "monitor",
    "deal", "clearance", "price error", "student", "tablet",
    "keyboard", "webcam", "usb", "charger", "phone",
]

GROCERY_KEYWORDS = [
    "grocery", "food", "chicken", "beef", "rice", "pasta",
    "milk", "eggs", "bread", "produce", "vegetable", "fruit",
    "pc express", "loblaws", "metro", "sobeys", "no frills",
    "walmart", "costco", "flyer", "sale",
]


def load_seen() -> set:
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(f.read().splitlines())
    return set()


def save_seen(seen: set):
    os.makedirs("data", exist_ok=True)
    with open(SEEN_FILE, "w") as f:
        f.write("\n".join(seen))


def check_rfd_deals() -> list:
    results = []
    seen = load_seen()

    for feed_url in RFD_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            log(f"📡 RFD feed: {len(feed.entries)} entries from {feed_url}", "debug")

            for entry in feed.entries[:20]:
                title_lower = entry.title.lower()
                eid = hashlib.md5(entry.link.encode()).hexdigest()

                if eid in seen:
                    continue

                is_tech    = any(k in title_lower for k in TECH_KEYWORDS)
                is_grocery = any(k in title_lower for k in GROCERY_KEYWORDS)

                if is_tech or is_grocery:
                    category = "tech" if is_tech else "grocery"
                    emoji    = "🔵" if is_tech else "🟢"

                    result = {
                        "title":    entry.title,
                        "url":      entry.link,
                        "summary":  getattr(entry, "summary", "")[:200],
                        "category": category,
                        "source":   "RedFlagDeals",
                        "emoji":    emoji,
                        "query":    "rfd_sweep",
                    }
                    results.append(result)
                    seen.add(eid)
                    log(f"✅ RFD deal: {entry.title[:60]}", "info")

        except Exception as e:
            log(f"❌ RFD feed failed {feed_url}: {e}", "error")

    save_seen(seen)
    return results
