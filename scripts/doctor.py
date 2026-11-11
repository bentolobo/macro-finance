#!/usr/bin/env python3
"""`make doctor` — tells you, before you render, exactly what your build will
look like: which series came back live, which fell back to cache, and which
resolved to a curated value. Run this first."""
import os, sys, shutil, subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pylib.datafeeds import (refresh_all, tier_summary, FRED_KEY)   # noqa: E402

GREEN, RED, YELL, OFF = "\033[32m", "\033[31m", "\033[33m", "\033[0m"

def check(label, ok, hint=""):
    print(f"  {GREEN+'PASS'+OFF if ok else RED+'FAIL'+OFF}  {label}")
    if not ok and hint:
        print(f"        → {hint}")
    return ok

print("\nMacro Finance — build doctor\n" + "-" * 58)
ok = True
ok &= check("quarto on PATH", shutil.which("quarto") is not None,
            "install from quarto.org/docs/get-started")
ok &= check("python ≥ 3.10", sys.version_info >= (3, 10))
for mod in ("pandas", "matplotlib", "requests", "pyarrow", "jupyter"):
    ok &= check(f"import {mod}", __import__("importlib").util.find_spec(mod) is not None,
                "pip install -r requirements.txt")
check("FRED_API_KEY set", bool(FRED_KEY),
      "free key at fred.stlouisfed.org/docs/api/api_key.html, then put "
      "FRED_API_KEY=... in .env  (book still builds without it, from cache)")

print("\nFetching every series the book uses...\n" + "-" * 58)
refresh_all()

t = tier_summary()
live = (t.tier == "live").sum() if len(t) else 0
print("\n" + "-" * 58)
print(f"  live: {live}   cache: {(t.tier=='cache').sum()}   "
      f"illustrative: {(t.tier=='illustrative').sum()}")
if live:
    print(GREEN + "\n  You have live data. `make html` now renders the real book." + OFF)
else:
    print(YELL + "\n  No live series resolved — check network/key. The book will "
          "still render from cache, with vintage stamps showing their age." + OFF)
