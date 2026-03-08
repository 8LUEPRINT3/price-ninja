#!/usr/bin/env python3
# utils/embed_formatter.py — Telegram alert formatter

import requests
from utils.logger import log


def build_message(result: dict) -> str:
    emoji    = result.get("emoji", "💰")
    source   = result.get("source", "Unknown")
    title    = result.get("title", "Deal")
    store    = result.get("store", "")
    price    = result.get("price")
    original = result.get("original")
    savings  = result.get("savings", "")
    expires  = result.get("expires", "")
    url      = result.get("url", "")
    summary  = result.get("summary", "")
    category = result.get("category", "")

    if category == "fallback":
        links = result.get("links", {})
        lines = [f"🛋️ <b>{title}</b>"]
        for store_name, link in links.items():
            lines.append(f"• <a href='{link}'>{store_name}</a>")
        return "\n".join(lines)

    lines = [f"{emoji} <b>{title}</b>"]

    if store:
        lines.append(f"🏪 {store}")

    if price:
        price_line = f"💲 <b>${price}</b>"
        if original:
            price_line += f"  <s>${original}</s>"
        if savings:
            price_line += f"  ✂️ {savings}"
        lines.append(price_line)

    if expires:
        lines.append(f"📅 Valid to: {expires}")

    if summary:
        lines.append(f"📝 {summary[:150]}...")

    lines.append(f"🔗 <a href='{url}'>View Deal</a>")
    lines.append(f"📡 Source: {source}")

    return "\n".join(lines)


def send_telegram_alert(result: dict, token: str, chat_id: str):
    if not token or not chat_id:
        log("⚠️ Telegram not configured — skipping alert", "warn")
        return

    message = build_message(result)

    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={
                "chat_id":    chat_id,
                "text":       message,
                "parse_mode": "HTML",
                "disable_web_page_preview": False,
            },
            timeout=10,
        )
        if resp.status_code == 200:
            log(f"✅ Telegram alert sent: {result.get('title', '')[:50]}", "info")
        else:
            log(f"⚠️ Telegram error {resp.status_code}: {resp.text[:100]}", "warn")
    except Exception as e:
        log(f"❌ Telegram send failed: {e}", "error")
