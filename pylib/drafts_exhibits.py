"""Exhibits for the working-draft chapters: the international monetary system,
currency crises, and political risk. Data charts follow the house rule: live
fetch -> cached snapshot -> illustrative watermark, with provenance on the chart."""
from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon

from pylib.plotting import (NAVY, TEAL, AMBER, RUST, PLUM, SLATE, INK, MUTED, RULE,
                            PAPER, canvas, top, card, pill, arrow, text_block, finish)
from pylib.datafeeds import fred, _fetch, _record, Provenance, HEADERS, TIMEOUT


# ======================================================================
# Chapter 2 · The International Monetary System
# ======================================================================
def ims_timeline():
    """Two centuries of monetary regimes, 1792 to today."""
    now = date.today().year
    fig, ax = canvas(10.6, 4.2)
    H = top(ax)
    x = lambda yr: 2 + 96 * (yr - 1792) / (now - 1792)
    eras = [(1792, 1873, "Bimetallism", "Gold and silver both money; Britain on gold de facto", SLATE, +1),
            (1873, 1914, "Classical gold standard", "Fixed parities; free capital; no lender of last resort", AMBER, -1),
            (1914, 1944, "Interwar disorder", "Suspension, return, collapse, controls", RUST, +1),
            (1944, 1973, "Bretton Woods", "Pegs to the dollar; dollar to gold", NAVY, -1),
            (1973, now, "Floating-dollar era", "Floats, pegs, the euro; the dollar still central", TEAL, +1)]
    yb = H / 2 - 1.5
    for a, b, t, s, c, side in eras:
        ax.add_patch(plt.Rectangle((x(a), yb), x(b) - x(a), 3, fc=c, ec="white", lw=1.5))
        mid = (x(a) + x(b)) / 2
        ly = yb + 6 if side > 0 else yb - 3
        ax.plot([mid, mid], [yb + 3 if side > 0 else yb, ly - (0.6 if side > 0 else -0.6)], color=c, lw=1.2)
        ax.text(mid, ly, t, ha="center", va="bottom" if side > 0 else "top", fontsize=9.6,
                fontweight="bold", color="#9a6f00" if c == AMBER else c)
        sub_y = ly + 2.6 if side > 0 else ly - 2.6
        ha = "right" if mid > 85 else ("left" if mid < 15 else "center")
        ax.text(min(mid, 99) if ha != "right" else 99, sub_y, s, ha=ha, va="bottom" if side > 0 else "top",
                fontsize=7.9, color=MUTED)
    for yr in [1792, 1873, 1914, 1944, 1973]:
        ax.text(x(yr), yb + 3.4, str(yr), fontsize=7.6, color=MUTED, va="bottom",
                ha="left" if yr == 1792 else "center")
    ev = [(1815, "Waterloo: Rothschild gold", 15.5), (1821, "Britain resumes gold convertibility", 20.5),
          (1931, "Sterling leaves gold", 15.5), (1971, "Nixon closes the gold window", 20.5),
          (1999, "Euro launched", 15.5), (2016, "Renminbi joins the SDR", 25.5)]
    for i, (yr, lab, depth) in enumerate(ev):
        ax.plot(x(yr), yb + 1.5, "o", ms=5, mfc="white", mec=INK, zorder=5)
        ax.plot([x(yr)] * 2, [yb, yb - depth + 1.4], color="#9aa7b3", lw=0.8, ls=":")
        ax.text(x(yr), yb - depth, f"{lab} ({yr})", ha="right" if x(yr) > 88 else ("left" if x(yr) < 12 else "center"),
                va="top", fontsize=8, color=INK)
    return finish(fig, "d02_timeline", "Two centuries of the international monetary system",
                  "Five regimes in 230 years; each felt permanent from the inside.")


# Official dollar parities of sterling. Gaps are periods of floating or wartime control.
GBP_PARITIES = [  # (start, end, $ per £, label)
    (1879, 1914, 4.8665, "Gold-standard parity $4.87"),
    (1925, 1931, 4.8665, "Return to gold at the prewar parity"),
    (1940, 1949, 4.03, "Wartime peg $4.03"),
    (1949, 1967, 2.80, "1949 devaluation: $2.80"),
    (1967, 1971, 2.40, "1967 devaluation: $2.40"),
]


def gbp_dollar():
    """The pound in dollars: official parities 1879-1971, market rate since 1971."""
    fig, ax = plt.subplots(figsize=(10.6, 4.4))
    try:
        s, prov = fred("DEXUSUK", "1971-01-01")
        m = s.resample("MS").mean()
        ill = False
    except Exception:
        idx = pd.date_range("1971-01-01", date.today(), freq="MS")
        m = pd.Series(np.linspace(2.4, 1.3, len(idx)), index=idx)
        prov = _record(Provenance("illustrative", "gbp", date.today(), "illustrative"))
        ill = True
    for a, b, v, lab in GBP_PARITIES:
        ax.plot([a, b], [v, v], color=NAVY, lw=3, solid_capstyle="butt")
    ax.annotate("Gold-standard parity\n$4.87 (1879–1914)", (1896, 4.8665), xytext=(0, 10),
                textcoords="offset points", ha="center", va="bottom", fontsize=8.6, color=NAVY)
    ax.annotate("Back on gold\n1925–31", (1928, 4.8665), xytext=(0, 10), textcoords="offset points",
                ha="center", va="bottom", fontsize=8.6, color=NAVY)
    ax.annotate("$4.03\n1940–49", (1944.5, 4.03), xytext=(0, -26), textcoords="offset points",
                ha="center", fontsize=8.6, color=NAVY)
    ax.annotate("$2.80 after the\n1949 devaluation", (1958, 2.80), xytext=(0, 8), textcoords="offset points",
                ha="center", va="bottom", fontsize=8.6, color=NAVY)
    ax.annotate("$2.40\n1967", (1969, 2.40), xytext=(0, -26), textcoords="offset points",
                ha="center", fontsize=8.6, color=NAVY)
    yrs = m.index.year + (m.index.month - 1) / 12
    ax.plot(yrs, m.values, color=RUST, lw=1.6)
    for a, b, lab in [(1914, 1925, "War and\nfloating"), (1931, 1940, "Floating;\ncontrols")]:
        ax.axvspan(a, b, color="#eeeae2", lw=0)
        ax.text((a + b) / 2, 1.2, lab, ha="center", fontsize=8, color=MUTED)
    if not ill:
        last_y, last_v = yrs[-1], m.iloc[-1]
        ax.annotate(f"${last_v:.2f}", (last_y, last_v), xytext=(6, 0), textcoords="offset points",
                    va="center", color=RUST, fontweight="bold")
        lo = m.idxmin()
        ax.annotate(f"Low ${m.min():.2f} ({lo:%b %Y})", (lo.year + (lo.month - 1) / 12, m.min()),
                    xytext=(4, -8), textcoords="offset points", ha="left", va="top", fontsize=8.6, color=RUST)
    ax.text(1990, 2.75, "Market rate since 1971", color=RUST, fontsize=9, fontweight="bold")
    ax.set_xlim(1875, date.today().year + 4)
    ax.set_ylim(0.8, 5.6)
    ax.set_ylabel("U.S. dollars per pound")
    return finish(fig, "d02_gbp", "The pound in dollars, 1879 to today",
                  "Official parities under gold and Bretton Woods (navy); the market rate after 1971 (rust)",
                  source=f"Sources: official parities (Bank of England; IMF); market rate {prov}, series DEXUSUK, monthly average.",
                  illustrative=ill)


def trilemma():
    """The impossible trinity as a budget constraint: pick any two."""
    fig, ax = canvas(10.6, 5.6)
    H = top(ax)
    A, B, C = (50, H - 6), (14, 9), (86, 9)
    ax.add_patch(Polygon([A, B, C], closed=True, fc="#f3f6f9", ec=NAVY, lw=2))
    for (px, py), lab, va in [(A, "Fixed exchange rate", "bottom"), (B, "Free capital mobility", "top"),
                              (C, "Independent monetary policy", "top")]:
        ax.plot(px, py, "o", ms=11, color=NAVY, zorder=4)
        ax.text(px, py + (2.4 if va == "bottom" else -2.6), lab, ha="center", va=va,
                fontsize=11, fontweight="bold", color=NAVY)
    sides = [((A[0] + B[0]) / 2 - 3, (A[1] + B[1]) / 2, "right",
              "Gold standard\ncurrency boards\neuro members", "give up: monetary policy", AMBER),
             ((A[0] + C[0]) / 2 + 3, (A[1] + C[1]) / 2, "left",
              "Bretton Woods\nChina for decades", "give up: open capital account", RUST),
             (50, B[1] + 6.5, "center",
              "Floating: the U.S., euro area, U.K., Japan", "give up: a fixed rate", TEAL)]
    for sx, sy, ha, what, cost, c in sides:
        ax.text(sx, sy + 1.6, what, ha=ha, va="bottom", fontsize=9.4, color=INK, fontweight="bold",
                linespacing=1.25)
        ax.text(sx, sy - 0.2, cost, ha=ha, va="top", fontsize=8.8, color="#9a6f00" if c == AMBER else c)
    ax.text(50, (A[1] + B[1] + C[1]) / 3 + 4, "Pick\nany two", ha="center", va="center",
            fontsize=15, fontweight="bold", color=SLATE)
    return finish(fig, "d02_trilemma", "The impossible trinity",
                  "Every monetary regime in the timeline is a choice of two corners")


# ======================================================================
# Chapter 3 · Global Currency Crises
# ======================================================================
CRISES = [  # (year, label, side +1 above / -1 below, level 1-4)
    (1720, "John Law's Mississippi scheme collapses", +1, 1),
    (1825, "Panic of 1825: Latin American loans default", -1, 1),
    (1890, "Baring crisis: Argentina", +1, 2),
    (1931, "Sterling forced off gold", -1, 2),
    (1992, "ERM: Black Wednesday", +1, 1),
    (1994, "Mexico: Tequila crisis", -1, 1),
    (1997, "Asia: baht, rupiah, won", +1, 2),
    (1998, "Russia defaults; LTCM", -1, 2),
    (1999, "Brazil floats the real", +1, 3),
    (2002, "Argentina ends convertibility", -1, 3),
    (2018, "Turkey and Argentina", +1, 1),
    (2022, "U.K. gilt crisis; sterling slides", -1, 1)]


def crisis_timeline():
    """Three centuries of currency crises on a broken axis."""
    now = date.today().year
    fig, ax = canvas(10.6, 4.6)
    H = top(ax)

    def x(yr):  # 1700-1940 compressed into the left 40%, 1985-now on the right
        if yr <= 1940:
            return 3 + 37 * (yr - 1700) / 240
        return 46 + 51 * (yr - 1985) / (now - 1985)
    yb = H / 2 - 1
    ax.plot([x(1700), x(1940)], [yb, yb], color=SLATE, lw=2.2)
    ax.plot([x(1985), x(now)], [yb, yb], color=SLATE, lw=2.2)
    ax.text((x(1940) + x(1985)) / 2, yb, "//", ha="center", va="center", fontsize=13, color=MUTED)
    for yr in [1700, 1800, 1900, 1990, 2000, 2010, 2020]:
        ax.text(x(yr), yb - 1.2, str(yr), ha="center", va="top", fontsize=7.6, color=MUTED)
    for i, (yr, lab, side, lvl) in enumerate(CRISES):
        up = side > 0
        d = 3 + 5.2 * (lvl - 1) + 2
        y = yb + d if up else yb - d - 2.5
        c = RUST if yr >= 1985 else PLUM
        ax.plot(x(yr), yb, "o", ms=6, color=c, zorder=4)
        ax.plot([x(yr)] * 2, [yb, y], color=c, lw=0.8, ls=":")
        ha = "left" if x(yr) < 10 else ("right" if x(yr) > 88 else "center")
        ax.text(x(yr), y, f"{yr} · {lab}", ha=ha, va="bottom" if up else "top", fontsize=7.8, color=INK,
                bbox=dict(fc=PAPER, ec="none", pad=0.6))
    return finish(fig, "d03_timeline", "Three centuries of currency crises",
                  "The cast changes; the plot — a promise of convertibility that markets stop believing — does not")


EVENTS = [("Mexican peso", "DEXMXUS", "1994-12-20", RUST),
          ("Thai baht", "DEXTHUS", "1997-07-02", AMBER),
          ("Korean won", "DEXKOUS", "1997-11-17", PLUM),
          ("Brazilian real", "DEXBZUS", "1999-01-13", TEAL)]


def crisis_event_study():
    """Each currency's dollar value, indexed to 100 on the day the peg broke."""
    fig, ax = plt.subplots(figsize=(10.6, 4.4))
    provs, drawn = [], 0
    for name, sid, t0, c in EVENTS:
        try:
            s, prov = fred(sid, "1993-01-01")
        except Exception:
            continue
        s = s.dropna()
        t0 = pd.Timestamp(t0)
        pos = s.index.searchsorted(t0)
        if pos < 60 or pos + 250 > len(s):
            continue
        w = s.iloc[pos - 60: pos + 251]
        v = 100 * w.iloc[60] / w            # dollars per unit of local currency, indexed
        trough = v.min()
        ax.plot(range(-60, -60 + len(v)), v.values, color=c, lw=1.8,
                label=f"{name} ({pd.Timestamp(t0):%b %Y}): {trough - 100:+.0f}% at worst")
        provs.append(prov)
        drawn += 1
    ill = drawn == 0
    if ill:
        t = np.arange(-60, 251)
        ax.plot(t, np.where(t < 0, 100, 100 - 45 * (1 - np.exp(-t / 40))), color=SLATE)
    if drawn:
        ax.legend(loc="upper right", fontsize=8.8, frameon=True, framealpha=0.95)
    ax.axvline(0, color=INK, lw=1)
    ax.text(2, 103, "Day the peg broke", fontsize=8.6, color=INK)
    ax.axhline(100, color=MUTED, lw=0.8, ls="--")
    ax.set_xlabel("Trading days from the break")
    ax.set_ylabel("Dollar value of currency (break day = 100)")
    src = provs[0] if provs else "illustrative"
    return finish(fig, "d03_events", "When the peg breaks",
                  "Dollar value of four currencies around their crisis dates",
                  source=f"Source: {src}; series DEXMXUS, DEXTHUS, DEXKOUS, DEXBZUS (noon buying rates). "
                         "Break dates: Mexico 20 Dec 1994; Thailand 2 Jul 1997; Korea 17 Nov 1997; Brazil 13 Jan 1999.",
                  illustrative=ill)


# ======================================================================
# Chapter 4 · Political Risk in International Finance
# ======================================================================
GPR_URL = "https://www.matteoiacoviello.com/gpr_files/data_gpr_export.xls"


def gpr():
    """Caldara-Iacoviello geopolitical risk, monthly. Historical index (since 1900)."""
    def _pull():
        import requests
        from io import BytesIO
        r = requests.get(GPR_URL, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        raw = pd.read_excel(BytesIO(r.content))
        dcol = next(c for c in raw.columns if "month" in str(c).lower() or "date" in str(c).lower())
        vcol = "GPRH" if "GPRH" in raw.columns else "GPR"
        df = pd.DataFrame({"date": pd.to_datetime(raw[dcol]), "value": pd.to_numeric(raw[vcol], errors="coerce")})
        return df.dropna().set_index("date")
    return _fetch("gpr_historical", _pull, "Caldara & Iacoviello, Geopolitical Risk Index (matteoiacoviello.com/gpr.htm)",
                  "GPRH")


def gpr_chart():
    fig, ax = plt.subplots(figsize=(10.6, 4.2))
    try:
        df, prov = gpr()
        s = df["value"]
        ill = False
    except Exception:
        idx = pd.date_range("1900-01-01", date.today(), freq="MS")
        s = pd.Series(100 + 40 * np.sin(np.arange(len(idx)) / 40) ** 2, index=idx)
        prov = _record(Provenance("illustrative", "gpr", date.today(), "illustrative"))
        ill = True
    sm = s.rolling(3, min_periods=1).mean()
    ax.plot(sm.index, sm.values, color=PLUM, lw=1.3)
    ax.axhline(100, color=MUTED, lw=0.8, ls="--")
    if not ill:
        for a, b, lab in [("1914-07", "1918-11", "World War I"), ("1939-09", "1945-08", "World War II"),
                          ("2001-09", "2001-12", "9/11"), ("2003-01", "2003-06", "Iraq"),
                          ("2022-02", "2022-06", "Ukraine")]:
            seg = sm.loc[a:b]
            if len(seg):
                d = seg.idxmax()
                ax.annotate(lab, (d, seg.max()), xytext=(0, 6), textcoords="offset points",
                            ha="center", fontsize=8.6, color=PLUM, fontweight="bold")
        ax.annotate(f"Latest: {s.iloc[-1]:.0f} ({s.index[-1]:%b %Y})", (s.index[-1], sm.iloc[-1]),
                    xytext=(-6, 18), textcoords="offset points", ha="right", fontsize=8.6, color=INK)
    ax.set_ylabel("Index (1900–2019 average = 100)")
    return finish(fig, "d04_gpr", "Geopolitical risk since 1900",
                  "Share of newspaper articles about wars, threats and terrorism; three-month average",
                  source=f"Source: {prov}. Historical index (GPRH).", illustrative=ill)


def epu_chart():
    fig, ax = plt.subplots(figsize=(10.6, 3.8))
    try:
        s, prov = fred("GEPUCURRENT", "1997-01-01")
        ill = False
    except Exception:
        idx = pd.date_range("1997-01-01", date.today(), freq="MS")
        s = pd.Series(np.linspace(70, 300, len(idx)), index=idx)
        prov = _record(Provenance("illustrative", "epu", date.today(), "illustrative"))
        ill = True
    ax.fill_between(s.index, s.values, color=TEAL, alpha=0.18, lw=0)
    ax.plot(s.index, s.values, color=TEAL, lw=1.4)
    if not ill:
        pk = s.idxmax()
        ax.annotate(f"Peak {s.max():.0f} ({pk:%b %Y})", (pk, s.max()), xytext=(-8, 0), textcoords="offset points",
                    ha="right", va="center", fontsize=8.6, color=TEAL, fontweight="bold")
        ax.annotate(f"{s.iloc[-1]:.0f} ({s.index[-1]:%b %Y})", (s.index[-1], s.iloc[-1]), xytext=(6, 0),
                    textcoords="offset points", va="center", fontsize=8.6, color=INK)
    ax.set_ylabel("Index (1997–2015 = 100)")
    return finish(fig, "d04_epu", "Global economic policy uncertainty",
                  "GDP-weighted news-based index across 20 economies",
                  source=f"Source: Baker, Bloom & Davis via {prov}, series GEPUCURRENT.", illustrative=ill)


RISKS = [("Transfer and convertibility", "You earn pesos and cannot turn them into dollars or send them home.",
          "Argentina's controls (2001, 2011–15, 2019–24)", NAVY),
         ("Expropriation", "The host state takes the asset outright or by a thousand regulatory cuts.",
          "Russia's 'temporary management' decrees (2023)", RUST),
         ("War and civil disturbance", "Physical loss or forced shutdown from conflict, terrorism or unrest.",
          "Western plants idled in Ukraine (2022–)", PLUM),
         ("Breach of contract", "The government or a state firm walks away from what it signed.",
          "Renegotiated energy and mining contracts", AMBER),
         ("Sovereign non-payment", "The state does not pay what it owes — to bondholders or to you.",
          "Defaults: Argentina, Russia, Sri Lanka, Zambia", SLATE),
         ("Home-government risk", "Your own government's sanctions, tariffs or export controls.",
          "Sanctions on Russia; U.S.–China export controls", TEAL)]


def polrisk_types():
    fig, ax = canvas(10.6, 6.2)
    H = top(ax)
    w, gap = 31, 2.5
    bottoms = []
    for i, (t, body, ex, c) in enumerate(RISKS):
        col, row = i % 3, i // 3
        xx = 1.5 + col * (w + gap)
        yt = H - 2 if row == 0 else min(bottoms[:3]) - 3
        b = card(ax, xx, yt, w, t, body, color=c, footer=ex, kicker=f"RISK {i + 1}", min_h=0)
        bottoms.append(b)
    return finish(fig, "d04_types", "Six ways a government can cost you money",
                  "The first five are the risks political-risk insurers such as MIGA cover; the sixth comes from home")
