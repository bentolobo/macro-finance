"""Living "In the News" feed.

At every build this module pulls the public RSS feeds of the financial press and the
official institutions, keeps items that match a chapter's keywords, and renders a dated
headline box. Policy (see Instructor Guide):

* Headlines, dates and links only for the commercial press (WSJ, Economist, FT).
  No article text is copied; a link sends the reader to the publisher.
* Official bodies (Fed, ECB, BIS, IMF) also get a short teaser (their releases are
  published for redistribution).
* If every feed fails, the last good snapshot (cache/news.json) is shown with its date.
"""
from __future__ import annotations

import html
import json
import re
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "cache" / "news.json"
TIMEOUT = 15
UA = {"User-Agent": "MacroFinanceLivingTextbook/1.0 (+https://bentolobo.github.io/macro-finance/)"}

# (publisher, feed url, kind)  kind: "press" = headline+link only; "official" = + teaser
FEEDS = [
    ("Wall Street Journal", "https://feeds.content.dowjones.io/public/rss/RSSWorldNews", "press"),
    ("Wall Street Journal", "https://feeds.content.dowjones.io/public/rss/RSSMarketsMain", "press"),
    ("Wall Street Journal", "https://feeds.content.dowjones.io/public/rss/socialeconomyfeed", "press"),
    ("The Economist", "https://www.economist.com/finance-and-economics/rss.xml", "press"),
    ("The Economist", "https://www.economist.com/international/rss.xml", "press"),
    ("Financial Times", "https://www.ft.com/global-economy?format=rss", "press"),
    ("Financial Times", "https://www.ft.com/markets?format=rss", "press"),
    ("Federal Reserve Board", "https://www.federalreserve.gov/feeds/press_all.xml", "official"),
    ("European Central Bank", "https://www.ecb.europa.eu/rss/press.html", "official"),
    ("Bank for International Settlements", "https://www.bis.org/doclist/all_pressrels.rss", "official"),
    ("Bank for International Settlements", "https://www.bis.org/doclist/cbspeeches.rss", "official"),
]

# Chapter keyword filters (case-insensitive, word-start match). Extend per chapter.
KEYWORDS = {
    "ch01": ["dollar", "currenc", "exchange rate", "forex", "foreign exchange", "tariff", "trade war",
             "trade deal", "globali", "deglobali", "capital flow", "foreign direct investment",
             "reserve currenc", "reserves", "emerging market", "multinational", "yuan", "renminbi",
             "euro ", "yen", "sanction", "supply chain", "fragment", "cross-border", "IMF", "BIS",
             "swap line", "stablecoin", "de-dollar"],
    "ch02": ["gold standard", "gold price", "gold reserve", "reserve currenc", "de-dollar", "dollar dominance",
             "Bretton Woods", "SDR", "exchange rate regime", "currency peg", "peg ", "currency board",
             "dollarization", "dollarisation", "renminbi", "yuan", "euro adoption", "swap line", "CBDC",
             "BRICS", "IMF", "monetary system", "central bank gold"],
    "ch03": ["currency crisis", "currency crash", "devaluat", "depreciat", "peso", "lira", "rupee", "rupiah",
             "naira", "rand ", "won ", "ringgit", "yen ", "capital flight", "capital control", "speculative attack",
             "contagion", "bailout", "IMF", "debt crisis", "default", "emerging-market currenc",
             "emerging market currenc", "currency slump", "currency plunge"],
    "ch04": ["sanction", "expropriat", "nationaliz", "nationalis", "geopolit", "coup", "election", "unrest",
             "war ", "conflict", "tariff", "export control", "investment screening", "seiz", "political risk",
             "regime", "embargo", "blacklist", "entity list", "CFIUS", "USMCA"],
}
CASE_SENSITIVE = {"IMF", "BIS", "FX", "FDI", "SDR", "CBDC", "BRICS", "CFIUS", "USMCA"}
WINDOW_DAYS = 45
MAX_ITEMS = 10
MAX_PER_PUBLISHER = 3

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rss1": "http://purl.org/rss/1.0/",
    "dc": "http://purl.org/dc/elements/1.1/",
}


# ------------------------------------------------------------------ parsing
def _text(el, *paths):
    for p in paths:
        x = el.find(p, NS)
        if x is not None:
            if x.text and x.text.strip():
                return x.text.strip()
            if x.get("href"):
                return x.get("href").strip()
    return ""


def _date(s: str):
    if not s:
        return None
    s = s.strip()
    try:
        d = parsedate_to_datetime(s)
    except (TypeError, ValueError, IndexError):
        try:
            d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        except ValueError:
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc)


def _clean(s: str, words: int = 30) -> str:
    s = html.unescape(re.sub(r"<[^>]+>", " ", s or ""))
    s = re.sub(r"\s+", " ", s).strip()
    w = s.split()
    return " ".join(w[:words]) + ("…" if len(w) > words else "")


def parse_feed(xml_bytes: bytes):
    """Return [{title, link, date(datetime), summary}] from RSS 2.0, RSS 1.0/RDF or Atom."""
    root = ET.fromstring(xml_bytes)
    out = []
    items = (root.findall("./channel/item") or root.findall(".//item")
             or root.findall("rss1:item", NS) or root.findall(".//rss1:item", NS))
    if items:
        for it in items:
            out.append({
                "title": _clean(_text(it, "title", "rss1:title"), 40),
                "link": _text(it, "link", "rss1:link", "guid"),
                "date": _date(_text(it, "pubDate", "dc:date", "rss1:date")),
                "summary": _text(it, "description", "rss1:description"),
            })
        return out
    for e in root.findall("atom:entry", NS):
        out.append({
            "title": _clean(_text(e, "atom:title"), 40),
            "link": _text(e, "atom:link"),
            "date": _date(_text(e, "atom:updated", "atom:published")),
            "summary": _text(e, "atom:summary", "atom:content"),
        })
    return out


# Automated market-data blurbs ("WSJ Dollar Index Rises 0.44% to 97.97") add nothing.
NOISE = re.compile(r"\bIndex (Rises|Falls|Edges|Slips|Gains)\b.*\d|\bAppointments?\b|\bvacanc|newsletter", re.I)


# ---------------------------------------------------------------- matching
def _matches(title: str, summary: str, chapter: str, kind: str = "press", publisher: str = "") -> bool:
    """Press items must match in the headline itself; official releases may match in the
    teaser, but not merely by naming the issuing institution."""
    if NOISE.search(title):
        return False
    hay = title if kind == "press" else f"{title} {summary}"
    own = {"Bank for International Settlements": "BIS"}.get(publisher)
    for k in KEYWORDS.get(chapter, []):
        if k == own:
            continue
        if k in CASE_SENSITIVE:
            if re.search(rf"\b{re.escape(k)}\b", hay):
                return True
        elif re.search(rf"\b{re.escape(k.lower())}", hay.lower()):
            return True
    return False


# ------------------------------------------------------------------ fetch
def fetch_all(verbose: bool = True):
    import requests
    pulled, status = [], []
    for pub, url, kind in FEEDS:
        try:
            r = requests.get(url, headers=UA, timeout=TIMEOUT)
            r.raise_for_status()
            items = parse_feed(r.content)
            for it in items:
                it.update(publisher=pub, kind=kind, feed=url)
            pulled += items
            status.append((pub, url, "ok", len(items)))
        except Exception as e:  # noqa: BLE001 — a dead feed must never break the build
            status.append((pub, url, f"failed: {type(e).__name__}", 0))
    if verbose:
        for pub, url, st, n in status:
            print(f"  NEWS {st:28s} {n:3d}  {pub} · {url}")
    return pulled, status


def refresh(verbose: bool = True) -> dict:
    """Fetch every feed and store the snapshot. Keeps the old snapshot if nothing arrived."""
    pulled, status = fetch_all(verbose)
    ok = [s for s in status if s[2] == "ok"]
    if not ok:
        return load()
    snap = {
        "retrieved": datetime.now(timezone.utc).isoformat(timespec="minutes"),
        "feeds_ok": len(ok), "feeds_total": len(status),
        "items": [{**it, "date": it["date"].isoformat() if it["date"] else None} for it in pulled],
    }
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(snap, ensure_ascii=False, indent=1))
    return snap


def load() -> dict:
    if CACHE.exists():
        return json.loads(CACHE.read_text())
    return {"retrieved": None, "feeds_ok": 0, "feeds_total": len(FEEDS), "items": []}


# ------------------------------------------------------------------ select
def select(chapter: str, snap: dict | None = None, now: datetime | None = None):
    snap = snap or load()
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(days=WINDOW_DAYS)
    seen, per_pub, chosen = set(), {}, []
    items = []
    for it in snap["items"]:
        d = _date(it["date"]) if it.get("date") else None
        if d is None or d < cutoff or not it.get("title") or not it.get("link"):
            continue
        if not _matches(it["title"], _clean(it.get("summary", ""), 80), chapter,
                        it.get("kind", "press"), it.get("publisher", "")):
            continue
        items.append({**it, "date": d})
    items.sort(key=lambda x: x["date"], reverse=True)
    for it in items:
        # "Boris Vujčić: Integrated, open…" and "Integrated, open…" are the same speech
        key = re.sub(r"\W+", " ", re.sub(r"^[^:]{2,40}:\s*", "", it["title"]).lower()).strip()
        if key in seen or per_pub.get(it["publisher"], 0) >= MAX_PER_PUBLISHER:
            continue
        seen.add(key)
        per_pub[it["publisher"]] = per_pub.get(it["publisher"], 0) + 1
        chosen.append(it)
        if len(chosen) >= MAX_ITEMS:
            break
    return chosen


# ------------------------------------------------------------------ render
def _md_escape(s: str) -> str:
    return s.replace("[", "\\[").replace("]", "\\]").replace("*", "\\*").replace("_", "\\_")


def render_box(chapter: str, refresh_first: bool = False) -> str:
    """Markdown for a callout box. Works in HTML and Word output."""
    snap = refresh(verbose=False) if refresh_first else load()
    chosen = select(chapter, snap)
    when = snap.get("retrieved")
    when_txt = (datetime.fromisoformat(when).astimezone().strftime("%-d %B %Y") if when else "not yet retrieved")
    lines = ["::: {.callout-note .mf-box .mf-news icon=false}",
             "## Latest headlines", ""]
    if not chosen:
        lines.append("*No matching headlines in the last "
                     f"{WINDOW_DAYS} days at the time of this build.*")
    for it in chosen:
        d = it["date"].astimezone().strftime("%-d %b %Y")
        lines.append(f"- **[{_md_escape(it['title'])}]({it['link']})**  \n"
                     f"  <span class='news-meta'>{it['publisher']} · {d}</span>  ")
        if it["kind"] == "official":
            teaser = _clean(it.get("summary", ""), 30)
            if teaser and teaser.lower() != it["title"].lower():
                lines.append(f"  <span class='news-teaser'>{_md_escape(teaser)}</span>")
    src = (f"Headlines retrieved {when_txt} from" if when else
           "Headlines appear after the first online build. They are drawn from")
    lines += ["", f"<span class='news-meta'>{src} the public feeds of "
              "the WSJ, The Economist, the FT, the Federal Reserve, the ECB and the BIS, filtered for "
              "this chapter's topics. Links open the publisher's site; some articles require a "
              "subscription. Your library's databases give full-text access.</span>", ":::"]
    return "\n".join(lines)


if __name__ == "__main__":
    s = refresh()
    print(f"{s['feeds_ok']}/{s['feeds_total']} feeds ok; {len(select('ch01', s))} items for ch01")
