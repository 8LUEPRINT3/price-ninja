# 🥷 price-ninja v2.0

**Stealth economic OSINT platform for student survival**

Hunts grocery and tech deals from Flipp flyers and RedFlagDeals — sends Telegram alerts when prices drop on your wishlist.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. First-time setup
python setup_wizard.py

# 3. Hunt deals
python main.py

# 4. Web dashboard (v3.0)
cd dashboard && python app.py
```

## Structure

```
price-ninja/
├── main.py                     # Mission control
├── setup_wizard.py             # First-time setup
├── requirements.txt
├── .env.example                # Copy to .env
├── scrapers/
│   ├── flipp_scraper.py        # Flipp flyer deals
│   └── rfd_monitor.py          # RedFlagDeals RSS
├── utils/
│   ├── logger.py               # Coloured logging
│   ├── embed_formatter.py      # Telegram alerts
│   └── price_link_generator.py # Fallback store links
├── config/
│   ├── keywords_map.json       # Synonym expansion (ndengu → mung beans)
│   ├── postal_codes.json       # Your location
│   └── merchant_blocklist.json # Filtered stores
├── data/
│   ├── user_wishlist.txt       # What you track
│   └── seen_deals.txt          # Deduplication cache
├── database/
│   └── deals.db                # SQLite (auto-created)
└── dashboard/
    ├── app.py                  # Flask web UI
    └── templates/
        ├── index.html
        └── wishlist.html
```

## Cron (run every 6 hours)

```bash
0 */6 * * * cd ~/price-ninja && python3 main.py >> data/log.txt 2>&1
```

## Features

- 🔍 **Flipp scraper** — searches flyer deals with synonym expansion
- 📡 **RFD monitor** — RSS sweep for tech and grocery hot deals
- 🤖 **Telegram alerts** — rich HTML messages with prices and links
- 🛋️ **Fallback links** — shelf price links when no deal found
- 🧠 **Synonym map** — search `ndengu` → finds `mung beans` deals
- 🚫 **Merchant blocklist** — filters irrelevant stores
- 🌐 **Web dashboard** — Flask UI with deal history and wishlist manager
