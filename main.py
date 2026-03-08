#!/usr/bin/env python3
# main.py — price-ninja v2.0
# Stealth economic OSINT platform for student survival

import os
import time
import json
from dotenv import load_dotenv
from scrapers.flipp_scraper import search_flyer_deals
from scrapers.rfd_monitor import check_rfd_deals
from utils.embed_formatter import send_telegram_alert
from utils.logger import log

load_dotenv()

TELEGRAM_TOKEN   = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if __name__ == "__main__":
    log("🚨 price-ninja v2.0: Booting reconnaissance engine...", "info")

    # Load user wishlist
    try:
        with open("data/user_wishlist.txt", "r") as f:
            wishlist = [line.strip().lower() for line in f
                        if line.strip() and not line.startswith("#")]
        log(f"📋 Loaded {len(wishlist)} items from wishlist", "info")
    except FileNotFoundError:
        log("⚠️ No user_wishlist.txt found. Run: python setup_wizard.py", "error")
        exit(1)

    # Step 1: Flipp Flyer Hunt
    log("🔍 Hunting grocery deals via Flipp...", "info")
    flyer_results = search_flyer_deals(wishlist)
    for result in flyer_results:
        send_telegram_alert(result, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)

    # Step 2: RFD OSINT Sweep
    log("📡 Scanning RedFlagDeals for tech & drops...", "info")
    rfd_results = check_rfd_deals()
    for result in rfd_results:
        send_telegram_alert(result, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)

    log("✅ Recon cycle complete. Sleeping until next cron.", "success")
