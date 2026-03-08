#!/usr/bin/env python3
# setup_wizard.py — price-ninja first-time setup

import os
import json

BANNER = """
██████╗ ██████╗ ██╗ ██████╗███████╗    ███╗   ██╗██╗███╗   ██╗     ██╗ █████╗
██╔══██╗██╔══██╗██║██╔════╝██╔════╝    ████╗  ██║██║████╗  ██║     ██║██╔══██╗
██████╔╝██████╔╝██║██║     █████╗      ██╔██╗ ██║██║██╔██╗ ██║     ██║███████║
██╔═══╝ ██╔══██╗██║██║     ██╔══╝      ██║╚██╗██║██║██║╚██╗██║██   ██║██╔══██║
██║     ██║  ██║██║╚██████╗███████╗    ██║ ╚████║██║██║ ╚████║╚█████╔╝██║  ██║
╚═╝     ╚═╝  ╚═╝╚═╝ ╚═════╝╚══════╝    ╚═╝  ╚═══╝╚═╝╚═╝  ╚═══╝ ╚════╝ ╚═╝  ╚═╝

                    🥷  price-ninja v2.0  —  Setup Wizard
"""

DEFAULT_KEYWORD_MAP = {
    "ndengu":   {"synonyms": ["mung beans", "moong dal", "green lentils"], "category": "pulse"},
    "matoke":   {"synonyms": ["plantain", "green banana", "cooking banana"], "category": "produce"},
    "dhania":   {"synonyms": ["cilantro", "coriander leaves", "fresh coriander"], "category": "herb"},
    "ugali":    {"synonyms": ["cornmeal", "corn flour", "maize flour", "masa"], "category": "grain"},
    "sukuma":   {"synonyms": ["kale", "collard greens", "sukuma wiki"], "category": "produce"},
    "ramen":    {"synonyms": ["instant noodles", "ramen noodles"], "category": "dry goods"},
    "oat milk": {"synonyms": ["oat milk", "oatly", "oat beverage"], "category": "dairy-alt"},
    "eggs":     {"synonyms": ["large eggs", "dozen eggs", "free range eggs"], "category": "protein"},
    "rice":     {"synonyms": ["jasmine rice", "basmati rice", "long grain rice", "white rice"], "category": "grain"},
    "chicken":  {"synonyms": ["chicken breast", "chicken thigh", "whole chicken", "chicken legs"], "category": "protein"},
}

DEFAULT_BLOCKLIST = [
    "petsmart", "ren's pets", "veterinarian", "petland",
    "home depot", "canadian tire hardware",
]


def create_dirs():
    for d in ["data", "config", "database", "dashboard/templates"]:
        os.makedirs(d, exist_ok=True)


def setup_postal():
    if os.path.exists("config/postal_codes.json"):
        print("   ✅ postal_codes.json already exists — skipping")
        return
    code = input("📍 Enter your postal code (e.g., L4M 3X9): ").strip().upper()
    if not code:
        code = "L4M 3X9"
    with open("config/postal_codes.json", "w") as f:
        json.dump({"default": code}, f, indent=2)
    print(f"   ✅ Saved postal code: {code}\n")


def setup_blocklist():
    if os.path.exists("config/merchant_blocklist.json"):
        print("   ✅ merchant_blocklist.json already exists — skipping")
        return
    with open("config/merchant_blocklist.json", "w") as f:
        json.dump(DEFAULT_BLOCKLIST, f, indent=2)
    print("   ✅ Created merchant blocklist (pet stores, hardware filtered)\n")


def setup_keywords():
    if os.path.exists("config/keywords_map.json"):
        print("   ✅ keywords_map.json already exists — skipping")
        return
    with open("config/keywords_map.json", "w") as f:
        json.dump(DEFAULT_KEYWORD_MAP, f, indent=2)
    print("   ✅ Created synonym map (ndengu, matoke, ramen, rice, chicken...)\n")


def setup_wishlist():
    if os.path.exists("data/user_wishlist.txt"):
        print("   ✅ user_wishlist.txt already exists — skipping")
        return

    print("🛒 What do you want to track? Enter items one by one.")
    print("   (Examples: chicken, rice, oat milk, ramen, eggs)")
    print("   Press Enter with no input when done.\n")

    wishlist = []
    while True:
        item = input(f"   Item {len(wishlist)+1}: ").strip().lower()
        if not item:
            if len(wishlist) == 0:
                print("   ⚠️ Adding default items: chicken, rice, eggs, ramen")
                wishlist = ["chicken", "rice", "eggs", "ramen"]
            break
        wishlist.append(item)
        if len(wishlist) >= 10:
            print("   ℹ️ Max 10 items reached")
            break

    with open("data/user_wishlist.txt", "w") as f:
        f.write("# price-ninja wishlist — one item per line\n")
        f.write("# Lines starting with # are ignored\n\n")
        f.write("\n".join(wishlist))

    print(f"\n   ✅ Saved wishlist: {', '.join(wishlist)}\n")


def setup_env():
    if os.path.exists(".env"):
        print("   ✅ .env already exists — skipping")
        return

    print("📬 Telegram bot setup (for deal alerts)")
    print("   Create a bot via @BotFather on Telegram\n")

    token   = input("   Bot token (from BotFather): ").strip()
    chat_id = input("   Your Telegram chat ID (send /start to @userinfobot): ").strip()

    with open(".env", "w") as f:
        f.write(f"TELEGRAM_BOT_TOKEN={token}\n")
        f.write(f"TELEGRAM_CHAT_ID={chat_id}\n")
        f.write("LOG_LEVEL=INFO\n")

    print("\n   ✅ Saved .env\n")


def main():
    print(BANNER)
    create_dirs()

    print("📁 Step 1: Creating directory structure...")
    print("   ✅ data/ config/ database/ dashboard/\n")

    print("📍 Step 2: Postal code setup")
    setup_postal()

    print("🚫 Step 3: Merchant blocklist")
    setup_blocklist()

    print("🔤 Step 4: Keyword synonym map")
    setup_keywords()

    print("🛒 Step 5: Your wishlist")
    setup_wishlist()

    print("🤖 Step 6: Telegram bot")
    setup_env()

    print("=" * 60)
    print("🎉 Setup complete! You're ready to hunt deals.\n")
    print("  ▶  Run now:        python main.py")
    print("  ⏰  Schedule cron: 0 */6 * * * cd ~/price-ninja && python3 main.py >> data/log.txt 2>&1")
    print("  🌐  Web dashboard: coming in v3.0")
    print()


if __name__ == "__main__":
    main()
