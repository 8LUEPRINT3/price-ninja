#!/usr/bin/env python3
# utils/logger.py — Coloured console logger

import os
from datetime import datetime

LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

LEVELS = {"DEBUG": 0, "INFO": 1, "WARN": 2, "SUCCESS": 2, "ERROR": 3}

COLOURS = {
    "debug":   "\033[90m",   # dark grey
    "info":    "\033[36m",   # cyan
    "warn":    "\033[33m",   # yellow
    "success": "\033[32m",   # green
    "error":   "\033[31m",   # red
}
RESET = "\033[0m"


def log(message: str, level: str = "info"):
    level_key = level.upper()
    if LEVELS.get(level_key, 1) < LEVELS.get(LEVEL, 1):
        return
    ts    = datetime.now().strftime("%H:%M:%S")
    color = COLOURS.get(level.lower(), "")
    print(f"{color}[{ts}] [{level.upper():7s}] {message}{RESET}", flush=True)
