"""
pylib/datafeeds.py — data layer for *Macro Finance: A Living Textbook on
International Finance* (Bento J. Lobo, UTC).               engine v2, Nov 2026

Three-tier fallback on every accessor:
    1. live API   2. cached parquet in cache/   3. curated published value
A render never fails because an endpoint is down. When all three fail for a
time series, an *illustrative* shape is drawn and the exhibit is watermarked.

Changes from v1 (366-line engine shipped in macro-finance.zip):
  * Value now prints as its number in inline `{python}` expressions. v1 was a
    dataclass whose auto-generated __repr__ leaked into the prose.
  * Value carries no unit text in the prose. Units belong to the sentence
    ("$`{python} val('fx_turnover')` trillion"); v1 doubled them.
  * Every curated value carries its own source and reference date.
  * series(name) dispatches the named live series used by the chapters.
  * archive_vintage(chapter) records every value the chapter used.
  * The FDI fallback no longer draws the trade-openness shape.
"""
from __future__ import annotations

import io, json, os, warnings
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "cache"
VINTAGES = ROOT / "data" / "vintages"
CACHE.mkdir(exist_ok=True)
VINTAGES.mkdir(parents=True, exist_ok=True)

TIMEOUT = 20
HEADERS = {"User-Agent": "macro-finance-textbook/2.0 (academic use)"}
FRED_BASE = "https://api.stlouisfed.org/fred"
WB_BASE = "https://api.worldbank.org/v2"
ECB_BASE = "https://data-api.ecb.europa.eu/service/data"
FRED_KEY = os.getenv("FRED_API_KEY", "")


# ---------------------------------------------------------------- provenance
@dataclass
class Provenance:
    source: str
    series: str
    retrieved: date
    tier: str            # live | cache | curated | illustrative
    note: str = ""

    def __str__(self) -> str:
        if self.tier == "curated":
            return f"{self.source} ({self.note})" if self.note else self.source
        if self.tier == "illustrative":
            return "ILLUSTRATIVE SHAPE — a connected render replaces this"
        return f"{self.source}, retrieved {self.retrieved:%d %b %Y}"


@dataclass
class Value:
    """A number that knows where it came from. Prints as the number only."""
    number: float
    fmt: str = "{:,.1f}"
    prov: Provenance | None = None
    unit: str = ""                 # metadata for exhibits; never printed inline

    def __str__(self) -> str:
        return self.fmt.format(self.number)

    __repr__ = __str__

    def __float__(self) -> float:
        return float(self.number)

    def __format__(self, spec: str) -> str:
        return format(self.number, spec) if spec else str(self)


TIER_REPORT: list[dict] = []
_USED: dict[str, float] = {}


def _record(p: Provenance) -> Provenance:
    TIER_REPORT.append({"series": p.series, "source": p.source, "tier": p.tier,
                        "retrieved": p.retrieved.isoformat()})
    return p


def refresh_date() -> str:
    return date.today().strftime("%d %B %Y")


def tier_summary() -> pd.DataFrame:
    return pd.DataFrame(TIER_REPORT).drop_duplicates()


# -------------------------------------------------------------- cache layer
def _cache_path(key: str) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in key)
    return CACHE / f"{safe}.parquet"


def _write_cache(key: str, df: pd.DataFrame) -> None:
    try:
        df.to_parquet(_cache_path(key))
        meta = CACHE / "_manifest.json"
        m = json.loads(meta.read_text()) if meta.exists() else {}
        m[key] = {"retrieved": date.today().isoformat(), "rows": len(df)}
        meta.write_text(json.dumps(m, indent=2, sort_keys=True))
    except Exception as e:                                  # pragma: no cover
        warnings.warn(f"cache write failed for {key}: {e}")


def _read_cache(key: str):
    p = _cache_path(key)
    if not p.exists():
        return None, None
    try:
        df = pd.read_parquet(p)
        meta = CACHE / "_manifest.json"
        when = None
        if meta.exists():
            e = json.loads(meta.read_text()).get(key, {})
            when = date.fromisoformat(e["retrieved"]) if "retrieved" in e else None
        return df, when or date.fromtimestamp(p.stat().st_mtime)
    except Exception:
        return None, None


def _fetch(key, puller, source, series):
    try:
        df = puller()
        if df is None or len(df) == 0:
            raise ValueError("empty response")
        _write_cache(key, df)
        return df, _record(Provenance(source, series, date.today(), "live"))
    except Exception as e:
        cached, when = _read_cache(key)
        if cached is not None:
            return cached, _record(Provenance(source, series, when or date.today(),
                                              "cache", note="cached snapshot"))
        raise RuntimeError(f"[{key}] live fetch failed and no cache: {e}") from e


# ----------------------------------------------------------------- providers
def fred(series_id: str, start: str = "1990-01-01"):
    def _pull():
        if not FRED_KEY:
            # Keyless fallback: FRED's public graph CSV (same series, same values).
            r = requests.get("https://fred.stlouisfed.org/graph/fredgraph.csv",
                             params={"id": series_id, "cosd": start},
                             headers=HEADERS, timeout=TIMEOUT)
            r.raise_for_status()
            from io import StringIO
            df = pd.read_csv(StringIO(r.text))
            df.columns = ["date", "value"]
            df["date"] = pd.to_datetime(df["date"])
            df["value"] = pd.to_numeric(df["value"], errors="coerce")
            return df.dropna().set_index("date")
        r = requests.get(f"{FRED_BASE}/series/observations",
                         params={"series_id": series_id, "api_key": FRED_KEY,
                                 "file_type": "json", "observation_start": start},
                         headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        df = pd.DataFrame(r.json()["observations"])[["date", "value"]]
        df["date"] = pd.to_datetime(df["date"])
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        return df.dropna().set_index("date")
    df, prov = _fetch(f"fred_{series_id}", _pull,
                      "Federal Reserve Bank of St. Louis (FRED)", series_id)
    return df["value"].rename(series_id), prov


def worldbank(indicator: str, countries="WLD", start: int = 1970):
    end = datetime.now().year
    cc = countries if isinstance(countries, str) else ";".join(countries)

    def _pull():
        out, page = [], 1
        while True:
            r = requests.get(f"{WB_BASE}/country/{cc}/indicator/{indicator}",
                             params={"format": "json", "per_page": 20000,
                                     "date": f"{start}:{end}", "page": page},
                             headers=HEADERS, timeout=TIMEOUT)
            r.raise_for_status()
            js = r.json()
            if len(js) < 2 or js[1] is None:
                break
            out.extend(js[1])
            if page >= js[0]["pages"]:
                break
            page += 1
        df = pd.DataFrame([{"iso3": d["countryiso3code"], "year": int(d["date"]),
                            "value": d["value"]} for d in out])
        return df.dropna(subset=["value"]).sort_values("year")
    df, prov = _fetch(f"wb_{indicator}_{cc}", _pull,
                      "World Bank, World Development Indicators", indicator)
    return _guard_latest(df, indicator), prov


def _guard_latest(df, indicator, tol=0.15):
    """World aggregates for the newest year are often computed on partial country
    coverage and can jump implausibly (e.g. WLD trade/GDP 56.7 -> 68.5 in the first
    2025 release). Drop the newest year when it moves more than `tol` (relative)
    against both the prior year and the 5-year mean; log it so the author sees it."""
    if df is None or len(df) < 7 or not {"year", "value"} <= set(df.columns):
        return df
    d = df.sort_values("year")
    last, prev = d["value"].iloc[-1], d["value"].iloc[-2]
    mean5 = d["value"].iloc[-6:-1].mean()
    if prev and abs(last / prev - 1) > tol and abs(last / mean5 - 1) > tol:
        y = int(d["year"].iloc[-1])
        warnings.warn(f"{indicator}: {y} value {last:.2f} held back as provisional "
                      f"(prior {prev:.2f}); revisit when coverage completes")
        HELD_BACK[indicator] = (y, float(last))
        return d.iloc[:-1]
    return d


HELD_BACK: dict = {}


# ------------------------------------------------ curated values (low cadence)
# Each entry: value, format, source, reference note. Verified 11 Nov 2026.
_BIS = "BIS Triennial Central Bank Survey"
_C = {
    # BIS Triennial, April 2025 round (statistical release, 30 Sep 2025)
    "fx_turnover":            (9.6,   "{:.1f}", _BIS, "April 2025, USD trillion/day, net-net"),
    "fx_turnover_2022":       (7.5,   "{:.1f}", _BIS, "April 2022, USD trillion/day"),
    "fx_turnover_chg":        (28,    "{:.0f}", _BIS, "% change, April 2022 to April 2025"),
    "irt_turnover":           (7.9,   "{:.1f}", _BIS, "OTC IRD, April 2025, USD trillion/day"),
    "irt_turnover_chg":       (59,    "{:.0f}", _BIS, "% change, April 2022 to April 2025"),
    "triennial_jurisdictions":(52,    "{:.0f}", _BIS, "2025 round"),
    "triennial_dealers":      (1100,  "{:,.0f}", _BIS, "2025 round: 'more than 1,100'"),
    "usd_fx_share":           (89.2,  "{:.0f}", _BIS, "share of trades with USD on one side, April 2025"),
    "fx_share_dealers":       (46,    "{:.0f}", _BIS, "reporting dealers, % of turnover, April 2025"),
    "fx_share_otherfin":      (50,    "{:.0f}", _BIS, "other financial institutions, %, April 2025"),
    "fx_share_nonfin":        (5,     "{:.0f}", _BIS, "non-financial customers, %, April 2025"),
    # IMF COFER data brief, 1 July 2026
    "cofer_usd":              (57.13, "{:.2f}", "IMF COFER", "2026Q1"),
    "cofer_usd_prev":         (56.42, "{:.2f}", "IMF COFER", "2025Q4"),
    "cofer_total":            (13.10, "{:.2f}", "IMF COFER", "total FX reserves, USD trillion, 2026Q1"),
    # WTO Global Trade Outlook and Statistics, 19 March 2026
    "wto_merch_exports":      (26.26, "{:.1f}", "WTO Global Trade Outlook and Statistics", "2025, USD trillion"),
    # Federal Reserve FEDS Note, 'The International Role of the U.S. Dollar – 2025 Edition'
    "usd_debt_share":         (60,    "{:.0f}", "Federal Reserve, FEDS Note (July 2025)", "foreign-currency debt issuance, ~%"),
    "usd_loan_share":         (55,    "{:.0f}", "Federal Reserve, FEDS Note (July 2025)", "cross-border loans, ~%"),
    # World Bank WDI, 2024 (fallback only; live via NY.GDP.MKTP.CD)
    "world_gdp":              (111.0, "{:.0f}", "World Bank WDI", "2024, USD trillion (approx.)"),
    "us_gdp":                 (29.2,  "{:.1f}", "World Bank WDI", "2024, USD trillion (approx.)"),
}
CURATED: dict[str, Value] = {
    k: Value(v, f, Provenance(src, k, date(2026, 11, 11), "curated", note))
    for k, (v, f, src, note) in _C.items()
}

# Derived values: computed, never typed.
def _derive() -> None:
    fx, trade = CURATED["fx_turnover"].number, CURATED["wto_merch_exports"].number
    CURATED["fx_annual"] = Value(fx * 252, "{:,.0f}")
    CURATED["days_to_clear_trade"] = Value(trade / fx, "{:.1f}")
    CURATED["usd_gdp_share"] = Value(100 * CURATED["us_gdp"].number /
                                     CURATED["world_gdp"].number, "{:.0f}")
_derive()

# Time series published at low cadence (curated, sourced).
FX_TURNOVER_ROUNDS = pd.Series(
    {1998: 1.527, 2001: 1.239, 2004: 1.934, 2007: 3.324, 2010: 3.973,
     2013: 5.357, 2016: 5.066, 2019: 6.581, 2022: 7.506, 2025: 9.6},
    name="USD trillion per day")          # BIS Triennial, net-net, as published
IRD_TURNOVER_ROUNDS = pd.Series(
    {2016: 2.7, 2019: 6.5, 2022: 5.0, 2025: 7.9},
    name="USD trillion per day")          # 2019 and 2022 as compared in the 2025 release
COFER_2026Q1 = {"USD": 57.13, "EUR": 20.03, "JPY": 5.44, "CNY": 1.99}  # IMF brief, 1 Jul 2026
COFER_2025Q4 = {"USD": 56.42, "EUR": 20.38, "JPY": 5.84, "CNY": 1.95}


def val(name: str) -> Value:
    v = CURATED[name]
    _USED[name] = float(v)
    if v.prov:
        _record(v.prov)
    return v


# ------------------------------------------------------ illustrative fallback
def _illustrative(kind: str):
    """Last resort: a representative shape, flagged so the exhibit watermarks."""
    import numpy as np
    prov = _record(Provenance("illustrative", kind, date.today(), "illustrative"))
    if kind == "usd":
        idx = pd.date_range("2006-01-01", date.today(), freq="MS")
        rng = np.random.default_rng(7)
        return pd.Series(100 + np.cumsum(rng.normal(0, 1.4, len(idx))), index=idx), prov
    yrs = np.arange(1970 if kind == "openness" else 1990, date.today().year - 1)
    if kind == "openness":
        v = 25 + 35 / (1 + np.exp(-(yrs - 1995) / 7))
    else:   # fdi: volatile, mid-2000s and mid-2010s humps
        v = 1.2 + 1.6 * np.exp(-((yrs - 2007) / 3) ** 2) + 1.4 * np.exp(-((yrs - 2015.5) / 2) ** 2)
    return pd.DataFrame({"year": yrs, "value": v}), prov


# ------------------------------------------------------- named live series
def series(name: str):
    """Return (data, provenance) for a named series, falling back gracefully."""
    try:
        if name == "broad_dollar":
            s, p = fred("DTWEXBGS", start="2006-01-01")
            return s.resample("MS").mean(), p
        if name == "trade_openness":
            return worldbank("NE.TRD.GNFS.ZS", "WLD", 1970)
        if name == "fdi_inflows_gdp":
            return worldbank("BX.KLT.DINV.WD.GD.ZS", "WLD", 1990)
    except Exception as e:
        warnings.warn(f"{name}: {e}; illustrative shape used")
        return _illustrative({"broad_dollar": "usd", "trade_openness": "openness",
                              "fdi_inflows_gdp": "fdi"}[name])
    raise KeyError(name)


# ------------------------------------------------------- vintage archive
def archive_vintage(chapter: str, stats: dict | None = None) -> None:
    """Append this build's headline numbers for the 'Then and Now' feature.
    Call at the END of a chapter so every val() used is recorded."""
    rec = {"built": date.today().isoformat(), **_USED, **(stats or {})}
    with (VINTAGES / f"{chapter}.jsonl").open("a") as fh:
        fh.write(json.dumps(rec) + "\n")


def history(chapter: str, stat: str):
    f = VINTAGES / f"{chapter}.jsonl"
    if not f.exists():
        return []
    rows = [json.loads(l) for l in f.read_text().splitlines() if l.strip()]
    return [(r["built"], r[stat]) for r in rows if stat in r]


def refresh_all() -> None:
    """Warm every cache the book uses. Called by `make doctor` and the Action."""
    for name in ["broad_dollar", "trade_openness", "fdi_inflows_gdp"]:
        _, p = series(name)
        print(f"  {p.tier.upper():13s} {name}")
    try:
        from pylib import newsfeed
        snap = newsfeed.refresh()
        print(f"  NEWS          {snap.get('feeds_ok', 0)}/{snap.get('feeds_total', 0)} feeds ok")
    except Exception as e:  # noqa: BLE001
        print(f"  NEWS          refresh failed: {e}")


def fx_round(year: int) -> Value:
    """Global FX turnover in a Triennial round (USD trillion/day)."""
    _USED[f"fx_round_{year}"] = float(FX_TURNOVER_ROUNDS[year])
    return Value(float(FX_TURNOVER_ROUNDS[year]), "{:.1f}")
