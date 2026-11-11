"""Chapter 1 conceptual exhibits (infographics). Data charts live in the
chapter source itself, where 'Show the code' reveals the query."""
from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

from pylib.plotting import (NAVY, TEAL, AMBER, RUST, PLUM, SLATE, INK, MUTED, RULE,
                            PAPER, canvas, top, card, pill, arrow, text_block,
                            finish, _measure)
from pylib.datafeeds import val, CURATED


# ------------------------------------------------------------- at a glance
def glance():
    fig, ax = canvas(10.6, 2.9)
    H = top(ax)
    ax.add_patch(FancyBboxPatch((0.5, 0.5), 99, H - 1, boxstyle="round,pad=0,rounding_size=1.5",
                                fc=NAVY, ec="none"))
    ax.text(3, H - 4, "CHAPTER 1 AT A GLANCE", color="#f2c14e", fontsize=10.5, fontweight="bold", va="top")
    items = [
        (f"${val('fx_turnover')}tn", "daily global FX turnover, April 2025"),
        (f"+{val('fx_turnover_chg')}%", "versus the 2022 survey round"),
        (f"${val('irt_turnover')}tn", "daily OTC interest rate derivatives"),
        (f"{float(val('cofer_usd')):.1f}%", "dollar share of FX reserves, 2026 Q1"),
        (f"{val('fx_share_nonfin')}%", "of FX turnover is non-financial clients"),
    ]
    w = 94 / 5
    for i, (big, small) in enumerate(items):
        x = 3 + i * w
        ax.text(x, H - 10, big, color="white", fontsize=19, fontweight="bold", va="top")
        text_block(ax, x, H - 17.5, small, w - 3, 9.2, color="#d6e2ee")
        if i:
            ax.plot([x - 1.5, x - 1.5], [6.5, H - 9], color="#3d6a94", lw=1)
    ax.text(3, 3, "Sources: BIS Triennial Central Bank Survey, April 2025; IMF COFER, 2026 Q1. "
            "Every figure on this card is injected at build time.", color="#a9bfd4",
            fontsize=7.8, style="italic")
    return finish(fig, "glance")


# ------------------------------------------------------------ 1.1 study cycle
def ex0101():
    fig, ax = canvas(10.6, 4.4)
    H = top(ax)
    steps = [
        ("1 · BEFORE YOU READ", "Guess first", "Answer three questions before you know the answers.", NAVY),
        ("2 · WORKED → FADED", "Then solve", "Full solution, then the same problem with steps removed.", TEAL),
        ("3 · TRAP", "Meet the error", "Diagnose the plausible mistake before it becomes a habit.", RUST),
        ("4 · CONFIDENCE CHECK", "Rate yourself", "State your certainty before the answer. Calibration is a skill.", PLUM),
        ("5 · RECALL LEDGER", "Retrieve", "Short answers from memory, including older chapters.", AMBER),
    ]
    w, g = 17.6, 2.5
    bottoms = []
    for i, (k, t, b, c) in enumerate(steps):
        x = 1 + i * (w + g)
        bottoms.append(card(ax, x, H - 2, w, t, b, color=c, kicker=k, title_size=11, body_size=9.2))
        if i:
            arrow(ax, x - g + 0.3, H - 9, x - 0.3, H - 9)
    yb = min(bottoms) - 3
    ax.annotate("", (1 + w / 2, min(bottoms) - 0.5), (1 + 4 * (w + g) + w / 2, min(bottoms) - 0.5),
                arrowprops=dict(arrowstyle="-|>", color=SLATE, lw=1.4,
                                connectionstyle="arc3,rad=-0.12"))
    ax.text(50, yb - 4.2, "Next week: redo only the items you missed. Retrieve — don't reread.",
            ha="center", va="top", fontsize=10, color=SLATE, fontweight="bold")
    return finish(fig, "ex0101", "How each chapter is built to be studied")


# ------------------------------------------------------------ 1.2 frictions
def ex0102():
    fig, ax = canvas(10.6, 5.4)
    H = top(ax)
    F = [
        ("FRICTION 1", "Multiple currencies", "Cash flows are denominated in units that move against "
         "each other. A certain cash flow becomes an uncertain value.", "Parts II–IV · Chapters 5–13", NAVY),
        ("FRICTION 2", "Sovereign states", "Every transaction crosses a jurisdiction. States tax, block, "
         "expropriate and default — and there is no higher court.", "Chapters 4, 17, 18", RUST),
        ("FRICTION 3", "Institutional heterogeneity", "Accounting, tax, bankruptcy and creditor rights "
         "differ. The same transaction reports differently.", "Chapters 13, 19", TEAL),
        ("FRICTION 4", "Information and distance", "Investors know less about foreign firms: hence "
         "home bias, and a higher cost of capital away from home.", "Chapters 14, 15", PLUM),
    ]
    w = 48
    y1 = H - 2
    b0 = card(ax, 1, y1, w, F[0][1], F[0][2], F[0][4], F[0][3], F[0][0])
    b1 = card(ax, 51, y1, w, F[1][1], F[1][2], F[1][4], F[1][3], F[1][0])
    y2 = min(b0, b1) - 3
    card(ax, 1, y2, w, F[2][1], F[2][2], F[2][4], F[2][3], F[2][0])
    card(ax, 51, y2, w, F[3][1], F[3][2], F[3][4], F[3][3], F[3][0])
    return finish(fig, "ex0102", "The four frictions",
                  "Every later chapter is an elaboration of one of these boxes.")


# ------------------------------------------------------- 1.9 gross vs net
def ex0109():
    fig, ax = canvas(10.6, 3.0)
    H = top(ax)
    boxes = [("Corporate client buys €10m from Dealer A", "1 trade · $10m", AMBER),
             ("Dealer A lays off the risk with Dealer B", "2 trades · $20m", TEAL),
             ("Dealer B hedges with Dealer C", "3 trades · $30m", NAVY)]
    w, g, y = 22, 4.5, H - 3
    bots = []
    for i, (t, f, c) in enumerate(boxes):
        x = 1 + i * (w + g)
        bots.append(card(ax, x, y, w, t, "", c, f, band=False, title_size=10))
        if i:
            arrow(ax, x - g + 0.4, y - 7, x - 0.4, y - 7)
    x = 1 + 3 * (w + g)
    arrow(ax, x - g + 0.4, y - 7, x - 0.4, y - 7)
    card(ax, x, y, 100 - x - 1, "Reported gross turnover: $30m", "Underlying customer demand: $10m",
         RUST, band=False, title_size=10.5, min_h=y - min(bots))
    ax.text(1, min(bots) - 3, "Gross measures count intermediation. Net measures count demand.",
            fontsize=9.5, color=RUST, fontweight="bold", va="top")
    return finish(fig, "ex0109", "Why a gross turnover figure is not customer demand")


# ------------------------------------------------------- 1.10 participants
def ex0110():
    d, o, n = float(val("fx_share_dealers")), float(val("fx_share_otherfin")), float(val("fx_share_nonfin"))
    fig = plt.figure(figsize=(10.6, 4.6))
    axp = fig.add_axes([0.0, 0.04, 0.36, 0.86])
    axp.pie([d, o, n], colors=[NAVY, TEAL, AMBER], startangle=90, counterclock=False,
            wedgeprops=dict(width=0.38, edgecolor="white", linewidth=2))
    axp.text(0, 0.06, f"{n:.0f}%", ha="center", va="center", fontsize=22, fontweight="bold", color=AMBER)
    axp.text(0, -0.2, "non-financial\nclients", ha="center", va="center", fontsize=9, color=MUTED)
    ax = fig.add_axes([0.38, 0, 0.62, 1])
    ax.set_xlim(0, 62); ax.set_ylim(0, 62 * 4.6 / (10.6 * 0.62)); ax.axis("off")
    from pylib.plotting import _reg
    _reg(fig)
    H = ax.get_ylim()[1]
    rows = [(f"{d:.0f}%", "Reporting dealers", "The roughly 1,100 banks and dealers the survey covers, "
             "trading with each other: making prices and managing inventory.", NAVY),
            (f"{o:.0f}%", "Other financial institutions", "Smaller banks, hedge funds and principal trading "
             "firms, asset managers and pension funds, official institutions.", TEAL),
            (f"{n:.0f}%", "Non-financial customers", "Corporates and governments converting and hedging "
             "commercial flows — the client this book trains you to serve.", AMBER)]
    y = H - 2
    for big, t, b, c in rows:
        ax.add_patch(FancyBboxPatch((1, y - 9), 1.4, 9, boxstyle="round,pad=0,rounding_size=0.6", fc=c, ec="none"))
        ax.text(4, y, big, fontsize=16, fontweight="bold", color=c, va="top")
        yy, _ = text_block(ax, 15, y - 0.2, t, 46, 10.5, weight="bold")
        yy, _ = text_block(ax, 15, yy - 0.4, b, 46, 9, color=MUTED)
        y = min(yy, y - 9) - 2.6
    return finish(fig, "ex0110", "Who trades foreign exchange",
                  "Share of global turnover by counterparty, April 2025",
                  source="Source: BIS Triennial Central Bank Survey, April 2025. Shares are rounded and may not sum to 100.")


# ---------------------------------------------------- 1.11 three exposures
def ex0111():
    fig, ax = canvas(10.6, 5.0)
    H = top(ax)
    cols = [("TRANSACTION", "A contracted cash flow already on the books", NAVY,
             [("Horizon", "Days to about a year"), ("Hedged with", "Forward, option, money market"),
              ("What gets hit", "Cash"), ("Developed in", "Chapter 11")]),
            ("ECONOMIC / OPERATING", "The value of the future competitive position", RUST,
             [("Horizon", "Years; it never ends"), ("Hedged with", "Operations: sourcing, plant location, pricing"),
              ("What gets hit", "Firm value"), ("Developed in", "Chapter 12")]),
            ("TRANSLATION", "Restating foreign statements into one currency", TEAL,
             [("Horizon", "Each reporting date"), ("Hedged with", "Balance-sheet hedge, often value-destroying"),
              ("What gets hit", "Reported equity (CTA)"), ("Developed in", "Chapter 13")])]
    w = 31.5
    bots = []
    for i, (k, t, c, rows) in enumerate(cols):
        x = 1 + i * (w + 2)
        body = "\n".join(f"{a}: {b}" for a, b in rows)
        bots.append(card(ax, x, H - 2, w, t, body, c, kicker=k, title_size=11, body_size=9.4))
    ax.text(50, min(bots) - 2.5, "Real exposure outlives any single contract. The one firms measure best "
            "is usually the one that matters least.", ha="center", va="top", fontsize=9.5,
            color=RUST, fontweight="bold")
    return finish(fig, "ex0111", "Three kinds of currency exposure",
                  "The classification question: what, exactly, changes in value when the rate moves?")


# ---------------------------------------------------- 1.12 diagnostic tree
def ex0112():
    fig, ax = canvas(10.6, 6.2)
    H = top(ax)
    q = dict(color=SLATE, size=10)
    pill(ax, 28, H - 10, 44, 8, "Is there a signed contract, receivable or payable?", **q)
    pill(ax, 3, H - 25, 40, 8, "Is it settled in a currency other than your own?", **q)
    pill(ax, 57, H - 25, 40, 8, "Does the rate change your prices, volumes or costs?", **q)
    pill(ax, 1, H - 39, 22, 8, "TRANSACTION · Ch. 11", NAVY, 9.5)
    pill(ax, 25, H - 39, 20, 8, "No currency exposure on this item", "#e3e9ef", 9, tc=INK)
    pill(ax, 55, H - 39, 22, 8, "ECONOMIC · Ch. 12", RUST, 9.5)
    pill(ax, 79, H - 39, 20, 8, "Do you own a foreign subsidiary?", SLATE, 9)
    pill(ax, 76, H - 52, 23, 7, "TRANSLATION · Ch. 13", TEAL, 9.5)
    for (x0, y0, x1, y1, lab, lx) in [(40, H - 10, 23, H - 17, "YES", 25.5), (60, H - 10, 77, H - 17, "NO", 70),
                                      (15, H - 25, 12, H - 31, "YES", 9), (30, H - 25, 35, H - 31, "NO", 34.5),
                                      (70, H - 25, 66, H - 31, "YES", 63), (85, H - 25, 89, H - 31, "ALSO", 88.8),
                                      (89, H - 39, 87.5, H - 45, "YES", 89.5)]:
        arrow(ax, x0, y0, x1, y1)
        ax.text(lx, (y0 + y1) / 2, lab, fontsize=8.5, color=SLATE, fontweight="bold", va="center")
    ax.text(1, H - 49, "Trap: a firm with no foreign contracts and no foreign\nsubsidiary can still sit "
            "in the economic-exposure branch.", fontsize=9.5, color=RUST, fontweight="bold", va="top")
    return finish(fig, "ex0112", "Which exposure is it? A diagnostic")


# ------------------------------------------------------- 1.13 eighty years
def ex0113():
    from datetime import date
    now = date.today().year
    fig, ax = canvas(10.6, 3.8)
    H = top(ax)
    x = lambda yr: 2 + 96 * (yr - 1944) / (now - 1944)
    eras = [(1944, 1973, "Bretton Woods", "Pegs to the dollar, dollar to gold", NAVY, +1),
            (1973, 1990, "Floating and liberalization", "Capital controls dismantled", TEAL, -1),
            (1990, 2008, "Hyper-globalization", "Trade and gross flows surge", AMBER, +1),
            (2008, 2016, "Retrenchment", "Crisis; bank flows collapse", RUST, -1),
            (2016, now, "Fragmentation?", "Tariffs, sanctions, reshoring", PLUM, +1)]
    yb = H / 2 - 1.5
    for a, b, t, s, c, side in eras:
        ax.add_patch(plt.Rectangle((x(a), yb), x(b) - x(a), 3, fc=c, ec="white", lw=1.5))
        mid = (x(a) + x(b)) / 2
        ly = yb + 3 + 3 if side > 0 else yb - 3
        ax.plot([mid, mid], [yb + 3 if side > 0 else yb, ly - (0.6 if side > 0 else -0.6)], color=c, lw=1.2)
        ax.text(mid, ly, t, ha="center", va="bottom" if side > 0 else "top", fontsize=9.6, fontweight="bold", color=c)
        ax.text(mid, ly + 2.6 if side > 0 else ly - 2.6, s, ha="center",
                va="bottom" if side > 0 else "top", fontsize=8.4, color=MUTED)
    for yr in [1944, 1973, 1990, 2008, 2016]:
        ax.text(x(yr), yb + 3.4, str(yr), fontsize=7.6, color=MUTED, va="bottom", ha="left" if yr == 1944 else "center")
    ev = [(1971, "Nixon shock"), (1999, "Euro launched"), (2008.7, "Lehman"), (2020.2, "Covid"), (2025.3, "Tariff shock")]
    for i, (yr, lab) in enumerate(ev):
        ax.plot(x(yr), yb + 1.5, "o", ms=5, mfc="white", mec=INK, zorder=5)
    for i, (yr, lab) in enumerate(ev):
        depth = 15.5 if i % 2 == 0 else 19.5
        ax.plot([x(yr)] * 2, [yb, yb - depth + 1.4], color="#9aa7b3", lw=0.8, ls=":")
        ax.text(x(yr), yb - depth, f"{lab} ({int(yr)})", ha="right" if x(yr) > 92 else "center",
                va="top", fontsize=8, color=INK)
    return finish(fig, "ex0113", "Eighty years of the international monetary system",
                  "Five regimes; each felt permanent from the inside.")


# ------------------------------------------------- 1.17 twenty questions
TWENTY = [
    ("I · The global environment", NAVY, ["Why is this a separate field?", "Who decides what a currency is worth?",
                                           "What does the balance of payments measure?", "Who answers when a country runs out of dollars?"]),
    ("II · The FX market", TEAL, ["How does a market with no exchange work?", "Which parity relations must hold?",
                                  "Can anyone forecast a rate?"]),
    ("III · Derivatives", AMBER, ["How do I lock in a rate?", "How do I buy protection and keep the upside?",
                                  "How do I change the currency of my debt?"]),
    ("IV · Exposure", RUST, ["What do I do with a €4m receivable?", "What is my exposure with no FX contracts?",
                             "Why did equity move with no cash flow?"]),
    ("V · Financing and investing", PLUM, ["Where should a multinational raise money?", "How much foreign equity, and why so little?",
                                           "Build abroad, buy abroad, or stay home?", "How do I value a project in a foreign currency?"]),
    ("VI · Risk, policy, frontier", SLATE, ["What if the counterparty is a government?", "How do I move cash without giving it away?",
                                            "What is changing in the system, and what is not?"]),
]


def ex0117():
    fig, ax = canvas(10.6, 7.6)
    H = top(ax)
    n = 1
    y = H - 1.5
    for part, c, qs in TWENTY:
        body = "\n".join(f"{n + i}  {q}" for i, q in enumerate(qs))
        n += len(qs)
        x = 1 if TWENTY.index((part, c, qs)) % 2 == 0 else 51
        if x == 1:
            yb1 = card(ax, 1, y, 48, "", body, c, kicker=part.upper(), body_size=9.6)
        else:
            yb2 = card(ax, 51, y, 48, "", body, c, kicker=part.upper(), body_size=9.6)
            y = min(yb1, yb2) - 2
    return finish(fig, "ex0117", "The book in twenty questions",
                  "Each chapter answers one question a practitioner actually asks.")


# ------------------------------------------------------------ 1.18 top ten
TOP10 = [("An exchange rate is a price; most costly errors are quotation errors.", "Ch. 5"),
         ("Arbitrage ties the market together; covered interest parity is the knot.", "Ch. 6, 8, 10"),
         ("The forward rate is a price, not a prediction.", "Ch. 6, 7"),
         ("Nobody forecasts rates in the short run. The random walk usually wins.", "Ch. 7"),
         ("PPP is a long-run pull, not a trading rule.", "Ch. 6"),
         ("Fixed rate, free capital, independent policy: choose two.", "Ch. 2, 20"),
         ("The dollar is not merely one currency among many.", "Ch. 2, 3, 10, 20"),
         ("Economic exposure outlives every contract you hedge.", "Ch. 12"),
         ("Hedging adds value only by reducing frictions.", "Ch. 11"),
         ("Countries fail on currency mismatch and short maturity.", "Ch. 18, 20")]


def ex0118():
    fig, ax = canvas(10.6, 6.6)
    H = top(ax)
    cols = [PALETTE_TOP[i % 5] for i in range(10)]
    y = H - 1.5
    for r in range(5):
        bots = []
        for cidx in range(2):
            i = r * 2 + cidx
            x = 1 + cidx * 50
            t, ch = TOP10[i]
            bots.append(card(ax, x, y, 48, t, "", cols[i], ch, kicker=f"{i + 1}", title_size=10.2,
                             band=True))
        y = min(bots) - 1.6
    return finish(fig, "ex0118", "Ten things to still know in five years",
                  "Two are in tension with each other, and one is overstated. Chapter 1, Problem 1.15 asks which.")


PALETTE_TOP = [NAVY, TEAL, AMBER, RUST, PLUM]


# --------------------------------------------------------- 1.20 data tiers
def ex0120():
    fig, ax = canvas(10.6, 3.2)
    H = top(ax)
    T = [("TIER 1 · LIVE", "Called at build time", "The issuing agency's API: BIS, IMF, World Bank, FRED, ECB.", TEAL),
         ("TIER 2 · CACHE", "If the call fails", "The last successful snapshot, committed to the repository, so the book builds offline.", AMBER),
         ("TIER 3 · CURATED", "If there is no cache", "A published value with its source and reference date. Time series that cannot be drawn are watermarked as illustrative.", RUST)]
    w, g = 30, 4
    for i, (k, t, b, c) in enumerate(T):
        x = 1 + i * (w + g)
        card(ax, x, H - 2, w, t, b, c, kicker=k, title_size=10.5, body_size=9.2)
        if i:
            arrow(ax, x - g + 0.4, H - 9, x - 0.4, H - 9)
    return finish(fig, "ex0120", "How every number in this book gets here",
                  "Every exhibit carries its source and retrieval date. Quote the vintage when you cite a figure.")


# -------------------------------------------------------- 1.21 AI map
def ex0121():
    fig, ax = canvas(10.6, 5.6)
    H = top(ax)
    A = [("1 · THE INFORMATION FRICTION", "Models read foreign filings, local news and satellite data at a cost that used to be prohibitive.",
          "Evidence: strong on capability; unproven on home bias.  §1.1, Friction 4", NAVY),
         ("2 · MARKET STRUCTURE", "Execution algorithms and principal trading firms intermediate a rising share of FX turnover.",
          "Evidence: strong. The new risk is correlation, not speed.  §1.3, Ch. 5", TEAL),
         ("3 · THE TREASURY FUNCTION", "Cash-flow forecasting, exposure capture and execution are being automated; agents transact inside policy limits.",
          "Evidence: real pilot savings; governance binds.  §1.4, Ch. 11", AMBER),
         ("4 · THE DATA ITSELF", "Nowcasting from unstructured data shortens the lag between the world changing and the statistic reporting it.",
          "Evidence: promising. A model output has no vintage.  §1.8, Ch. 7", RUST)]
    y = H - 2
    b = [card(ax, 1, y, 48, "", A[0][1], A[0][3], A[0][2], A[0][0], body_size=9.6),
         card(ax, 51, y, 48, "", A[1][1], A[1][3], A[1][2], A[1][0], body_size=9.6)]
    y = min(b) - 2.5
    b = [card(ax, 1, y, 48, "", A[2][1], A[2][3], A[2][2], A[2][0], body_size=9.6),
         card(ax, 51, y, 48, "", A[3][1], A[3][3], A[3][2], A[3][0], body_size=9.6)]
    ax.text(50, min(b) - 2.2, "AI changes the cost of processing information. It does not change what is "
            "knowable about a future exchange rate.", ha="center", va="top", fontsize=9.5, color=PLUM, fontweight="bold")
    return finish(fig, "ex0121", "Where AI touches this chapter",
                  "Four contact points, ordered by strength of evidence.")


# ------------------------------------------------------ 1.22 ladder
def ex0122():
    fig, ax = canvas(10.6, 3.9)
    H = top(ax)
    R = [("RUNG 1 · HUMAN-LED", "Treasury decides; software reports", "Spreadsheets and a TMS. Exposure captured monthly; hedge ratios set by policy and reviewed by a committee.", "Where most firms are", NAVY),
         ("RUNG 2 · MACHINE-ADVISED", "Treasury decides; models recommend", "Forecasts, exposure netting and execution timing are model-generated; a human approves every trade.", "Where the gains are proven", TEAL),
         ("RUNG 3 · AGENT-EXECUTED", "Policy decides; agents act", "Agents route payments and execute hedges within written limits. Humans set the limits and review exceptions.", "Where governance is not", RUST)]
    w, g = 30, 4
    bots = []
    for i, (k, t, b, f, c) in enumerate(R):
        x = 1 + i * (w + g)
        bots.append(card(ax, x, H - 2, w, t, b, c, f, k, title_size=10.2, body_size=9.2))
        if i:
            arrow(ax, x - g + 0.4, H - 9, x - 0.4, H - 9)
    ax.text(50, min(bots) - 2.2, "A loss caused by an agent acting inside its limits is still the treasurer's "
            "loss, and still the CFO's disclosure.", ha="center", va="top", fontsize=9.3, color=PLUM, style="italic")
    return finish(fig, "ex0122", "The treasury automation ladder",
                  "Most treasuries sit on rung one or two. The question at rung three is not technical.")
