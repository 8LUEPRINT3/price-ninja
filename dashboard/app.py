#!/usr/bin/env python3
# dashboard/app.py — price-ninja web dashboard (v3.0)

import sqlite3
import json
import os
from flask import Flask, render_template, request, redirect, jsonify
from datetime import datetime

app = Flask(__name__)
DB = os.path.join(os.path.dirname(__file__), "../database/deals.db")


def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS deals (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            title     TEXT,
            store     TEXT,
            price     REAL,
            original  REAL,
            savings   TEXT,
            url       TEXT,
            category  TEXT,
            source    TEXT,
            query     TEXT,
            expires   TEXT,
            timestamp TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS wishlist (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            item      TEXT UNIQUE,
            added     TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    conn.close()


@app.route("/")
def index():
    conn = get_db()
    deals = conn.execute(
        "SELECT * FROM deals ORDER BY timestamp DESC LIMIT 50"
    ).fetchall()
    stats = conn.execute(
        "SELECT COUNT(*) as total, MIN(price) as min_price, MAX(price) as max_price FROM deals"
    ).fetchone()
    conn.close()
    return render_template("index.html", deals=deals, stats=stats)


@app.route("/wishlist", methods=["GET", "POST"])
def wishlist():
    conn = get_db()
    if request.method == "POST":
        item = request.form.get("item", "").strip().lower()
        if item:
            try:
                conn.execute("INSERT INTO wishlist (item) VALUES (?)", (item,))
                conn.commit()
            except sqlite3.IntegrityError:
                pass
    items = conn.execute("SELECT * FROM wishlist ORDER BY added DESC").fetchall()
    conn.close()
    return render_template("wishlist.html", items=items)


@app.route("/wishlist/delete/<int:item_id>", methods=["POST"])
def delete_wishlist_item(item_id):
    conn = get_db()
    conn.execute("DELETE FROM wishlist WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return redirect("/wishlist")


@app.route("/api/deals")
def api_deals():
    conn = get_db()
    category = request.args.get("category")
    if category:
        deals = conn.execute(
            "SELECT * FROM deals WHERE category=? ORDER BY timestamp DESC LIMIT 100",
            (category,)
        ).fetchall()
    else:
        deals = conn.execute(
            "SELECT * FROM deals ORDER BY timestamp DESC LIMIT 100"
        ).fetchall()
    conn.close()
    return jsonify([dict(d) for d in deals])


@app.route("/api/stats")
def api_stats():
    conn = get_db()
    stats = {
        "total_deals": conn.execute("SELECT COUNT(*) FROM deals").fetchone()[0],
        "total_wishlist": conn.execute("SELECT COUNT(*) FROM wishlist").fetchone()[0],
        "categories": [dict(r) for r in conn.execute(
            "SELECT category, COUNT(*) as count FROM deals GROUP BY category"
        ).fetchall()],
    }
    conn.close()
    return jsonify(stats)


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
