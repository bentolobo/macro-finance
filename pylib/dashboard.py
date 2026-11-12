"""Today's Indicators: the data behind the site-wide sidebar.

Two layers, because the inputs move at different speeds:

* Markets (Dow, S&P 500, Nasdaq, 10-year Treasury, EUR, JPY) and policy-rate odds move
  by the second. The sidebar pulls them in the reader's browser: TradingView quote
  widgets for prices, the Polymarket public API for meeting-by-meeting odds.
* Macro releases (CPI, PCE, payrolls, unemployment, claims, policy rates) change on
  release days. This module pulls them from FRED and the ECB and writes
  cache/dashboard.json. A GitHub Action runs it hourly on weekdays and commits only when
  a value changes; the sidebar reads the committed file.

Nothing here is typed by hand: each figure is computed from the source series, and a
series that fails keeps its last good value with its own date.

Run:  python -m pylib.dashboard
"""
from __future__ import annotations

import json
import os
import re
from datetime import date, datetime, timezone
from io import StringIO
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "cache" / "dashboard.json"
TIMEOUT = 20
UA = {"User-Agent": "MacroFinanceLivingTextbook/1.0 (+https://bentolobo.github.io/macro-finance/)"}
FRED_KEY = os.getenv("FRED_API_KEY", "")

# ---------------------------------------------------------------- indicators
# (key, label, FRED id, transform, unit, decimals)
#   transform: "level" | "yoy" (12-month % change of an index) | "diff" (1-period change)
INDICATORS = {
    "Inflation": [
        ("cpi", "CPI, all items (y/y)", "CPIAUCSL", "yoy", "%", 1),
        ("core_cpi", "Core CPI (y/y)", "CPILFESL", "yoy", "%", 1),
        ("core_pce", "Core PCE, Fed's target gauge (y/y)", "PCEPILFE", "yoy", "%", 1),
        ("ea_hicp", "Euro area HICP (y/y)", "ESTAT:prc_hicp_minr", "level", "%", 1),
    ],
    "Growth": [
        ("gdp", "US real GDP (q/q, annualized)", "A191RL1Q225SBEA", "level", "%", 1),
        ("gdpnow", "GDPNow, current-quarter estimate", "GDPNOW", "level", "%", 1),
    ],
    "Jobs": [
        ("unrate", "Unemployment rate", "UNRATE", "level", "%", 1),
        ("payrolls", "Nonfarm payrolls (monthly change)", "PAYEMS", "diff", "k", 0),
        ("claims", "Initial jobless claims (weekly)", "ICSA", "level", "k", 0),
    ],
}

# Policy rates: last change is computed from the series itself.
POLICY = [
    ("fed", "Federal Reserve", "Fed funds target", ["DFEDTARL", "DFEDTARU"]),
    ("ecb", "European Central Bank", "Deposit facility rate", ["ECBDFR"]),
]

# Latest policy statements (official feeds; headline + link only).
STATEMENT_FEEDS = [
    ("Fed", "https://www.federalreserve.gov/feeds/press_monetary.xml",
     r"FOMC statement|minutes of the Federal Open Market Committee"),
    ("ECB", "https://www.ecb.europa.eu/rss/press.html", r"monetary policy decision"),
    ("BoJ", "https://www.boj.or.jp/en/rss/whatsnew.xml", r"statement on monetary policy|monetary policy meeting"),
]


# ------------------------------------------------------------------ fetchers
def _fred(series_id: str, start: str = "2018-01-01") -> tuple[pd.Series, str | None]:
    """Observations and FRED's last-updated stamp (None on the keyless path)."""
    if FRED_KEY:
        r = requests.get("https://api.stlouisfed.org/fred/series/observations",
                         params={"series_id": series_id, "api_key": FRED_KEY, "file_type": "json",
                                 "observation_start": start}, headers=UA, timeout=TIMEOUT)
        r.raise_for_status()
        df = pd.DataFrame(r.json()["observations"])
        s = pd.Series(pd.to_numeric(df["value"], errors="coerce").values,
                      index=pd.to_datetime(df["date"])).dropna()
        updated = None
        try:
            m = requests.get("https://api.stlouisfed.org/fred/series",
                             params={"series_id": series_id, "api_key": FRED_KEY, "file_type": "json"},
                             headers=UA, timeout=TIMEOUT)
            m.raise_for_status()
            updated = m.json()["seriess"][0]["last_updated"][:10]
        except Exception:  # noqa: BLE001
            pass
        return s, updated
    r = requests.get("https://fred.stlouisfed.org/graph/fredgraph.csv",
                     params={"id": series_id, "cosd": start}, headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    df = pd.read_csv(StringIO(r.text))
    s = pd.Series(pd.to_numeric(df.iloc[:, 1], errors="coerce").values,
                  index=pd.to_datetime(df.iloc[:, 0])).dropna()
    return s, None


def _ecb(key: str) -> tuple[pd.Series, str | None]:
    flow, rest = key.split("/", 1)
    r = requests.get(f"https://data-api.ecb.europa.eu/service/data/{flow}/{rest}",
                     params={"format": "csvdata", "startPeriod": "2018-01"}, headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    df = pd.read_csv(StringIO(r.text))
    s = pd.Series(pd.to_numeric(df["OBS_VALUE"], errors="coerce").values,
                  index=pd.to_datetime(df["TIME_PERIOD"])).dropna().sort_index()
    return s, None


def _eurostat(dataset: str) -> tuple[pd.Series, str | None]:
    """Euro area HICP, annual rate. ECOICOP ver. 2 (from 2026): the all-items code is
    coicop18=TOTAL; the old CP00 series in prc_hicp_manr stops at Dec 2025."""
    r = requests.get(f"https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/{dataset}",
                     params={"geo": "EA", "coicop18": "TOTAL", "unit": "RCH_A", "lastTimePeriod": 24},
                     headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    j = r.json()
    times = sorted(j["dimension"]["time"]["category"]["index"].items(), key=lambda kv: kv[1])
    vals = j.get("value", {})
    s = pd.Series({pd.Timestamp(t + "-01"): float(vals[str(i)]) for t, i in times if str(i) in vals})
    return s.sort_index(), (j.get("updated") or "")[:10] or None


def _series(sid: str):
    if sid.startswith("ESTAT:"):
        return _eurostat(sid[6:])
    return _ecb(sid[4:]) if sid.startswith("ECB:") else _fred(sid)


# --------------------------------------------------------------- transforms
def _transform(s: pd.Series, how: str) -> pd.Series:
    if how == "yoy":
        s = s.asfreq("MS") if s.index.inferred_freq in (None, "MS") else s
        return (s / s.shift(12) - 1).mul(100).dropna()
    if how == "diff":
        return s.diff().dropna()
    return s


UP_IS_GOOD = {"gdp", "gdpnow", "payrolls"}   # arrow colour: green when a rise is good news
QUARTERLY = {"A191RL1Q225SBEA", "GDPNOW"}


def _period(ts: pd.Timestamp, sid: str) -> str:
    if sid in QUARTERLY:
        return f"Q{ts.quarter} {ts.year}"
    return f"week of {ts:%-d %b %Y}" if sid in ("ICSA",) else f"{ts:%b %Y}"


def _scale(v: float, unit: str, sid: str) -> float:
    return v / 1000 if (unit == "k" and sid == "ICSA") else v   # claims are persons; PAYEMS already thousands


def _indicator(key, label, sid, how, unit, dp):
    s, updated = _series(sid)
    t = _transform(s, how)
    if len(t) < 2:
        raise ValueError("not enough observations")
    last, prev = t.index[-1], t.index[-2]
    return {
        "key": key, "label": label, "unit": unit, "dp": dp,
        "up_is_good": key in UP_IS_GOOD,
        "value": round(_scale(float(t.iloc[-1]), unit, sid), dp + 1),
        "prev": round(_scale(float(t.iloc[-2]), unit, sid), dp + 1),
        "period": _period(last, sid), "prev_period": _period(prev, sid),
        "updated": updated,
        "source": ("Eurostat" if sid.startswith("ESTAT:") else
                   "ECB Data Portal" if sid.startswith("ECB:") else "FRED"),
        "series": sid.split(":", 1)[-1],
        "url": (f"https://ec.europa.eu/eurostat/databrowser/view/{sid[6:]}/default/table" if sid.startswith("ESTAT:") else
                "https://data.ecb.europa.eu/data/datasets/" + sid[4:].split("/")[0] if sid.startswith("ECB:") else
                f"https://fred.stlouisfed.org/series/{sid}"),
        "status": "live",
    }


def _policy(key, bank, label, sids):
    parts = [_fred(sid)[0] for sid in sids]
    df = pd.concat(parts, axis=1).dropna()
    cur = df.iloc[-1]
    # walk back to the last date the (lower bound of the) rate changed
    lead = df.iloc[:, 0]
    changed = lead[lead.ne(lead.shift())]
    when = changed.index[-1]
    before = lead[lead.index < when]
    move = (float(lead.loc[when]) - float(before.iloc[-1])) * 100 if len(before) else 0.0
    rate = (f"{cur.iloc[0]:.2f}–{cur.iloc[1]:.2f}%" if len(sids) == 2 else f"{cur.iloc[0]:.2f}%")
    verb = "raised" if move > 0 else "cut" if move < 0 else "set"
    return {
        "key": key, "bank": bank, "label": label, "rate": rate,
        "last_move_bp": round(move), "last_move_date": f"{when:%Y-%m-%d}",
        "last_move_text": f"{verb} {abs(round(move))} bp on {when:%-d %b %Y}" if move else f"unchanged since {when:%-d %b %Y}",
        "as_of": f"{df.index[-1]:%Y-%m-%d}", "series": ",".join(sids),
        "url": f"https://fred.stlouisfed.org/series/{sids[-1]}", "status": "live",
    }


def _statements():
    from pylib.newsfeed import parse_feed
    out = []
    for bank, url, pat in STATEMENT_FEEDS:
        try:
            r = requests.get(url, headers=UA, timeout=TIMEOUT)
            r.raise_for_status()
            items = [i for i in parse_feed(r.content) if re.search(pat, i["title"], re.I) and i["date"]]
            items.sort(key=lambda i: i["date"], reverse=True)
            for i in items[:2]:
                out.append({"bank": bank, "title": i["title"], "link": i["link"],
                            "date": i["date"].isoformat()})
            print(f"  STATEMENTS {bank}: {len(items)} matching")
        except Exception as e:  # noqa: BLE001
            print(f"  STATEMENTS {bank} failed: {type(e).__name__}: {e}")
    out.sort(key=lambda i: i["date"], reverse=True)
    return out[:5]


# --------------------------------------------------------------------- build
def load() -> dict:
    return json.loads(OUT.read_text()) if OUT.exists() else {}


def build() -> dict:
    old = load()
    old_items = {i["key"]: i for g in old.get("groups", []) for i in g["items"]}
    old_policy = {p["key"]: p for p in old.get("policy", [])}

    groups = []
    for title, specs in INDICATORS.items():
        items = []
        for spec in specs:
            try:
                items.append(_indicator(*spec))
                print(f"  LIVE   {spec[2]}")
            except Exception as e:  # noqa: BLE001 — keep the last good value, say so
                print(f"  FAILED {spec[2]}: {type(e).__name__}: {e}")
                if spec[0] in old_items:
                    items.append({**old_items[spec[0]], "status": "cached"})
        groups.append({"title": title, "items": items})

    policy = []
    for spec in POLICY:
        try:
            policy.append(_policy(*spec))
            print(f"  LIVE   policy {spec[0]}")
        except Exception as e:  # noqa: BLE001
            print(f"  FAILED policy {spec[0]}: {type(e).__name__}: {e}")
            if spec[0] in old_policy:
                policy.append({**old_policy[spec[0]], "status": "cached"})

    statements = _statements() or old.get("statements", [])
    return {"groups": groups, "policy": policy, "statements": statements}


def refresh() -> bool:
    """Write cache/dashboard.json. Returns True if any value changed (the timestamp alone
    does not count, so the hourly job commits only on real news)."""
    new = build()
    old = load()
    strip = lambda d: {k: v for k, v in d.items() if k != "built"}  # noqa: E731
    changed = strip(old) != new
    if changed or not old:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps({"built": datetime.now(timezone.utc).isoformat(timespec="minutes"), **new},
                                  ensure_ascii=False, indent=1))
    print(f"  DASHBOARD {'updated' if changed else 'unchanged'}")
    return changed


if __name__ == "__main__":
    refresh()
