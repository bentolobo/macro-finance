"""House style and exhibit engine for Macro Finance.            engine v2, Nov 2026

Rules implemented here (see the project instructions):
  * Infographics draw on a fixed 0-100 canvas (y scaled so units are square).
  * Text is wrapped by MEASURING each line with the renderer, never by
    counting characters. Cards compute their own height from the result.
  * Titles use a deferred header band: placed after everything else is drawn,
    a fixed gap above the topmost real content.
  * Provenance is a small right-aligned tag above the frame, never rotated.
  * A two-gate audit runs on every exhibit: (a) text overlapping text,
    (b) text escaping its own card. Findings go to _audit/, not the page.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

NAVY, TEAL, AMBER, RUST, PLUM, SLATE = (
    "#1f4e79", "#2a9d8f", "#e9b949", "#e76f51", "#6a4c93", "#5a6b7b")
INK, MUTED, RULE, PAPER = "#14202b", "#5a6b7b", "#dfe6ec", "#f5f7f9"
TEXT_ON_PAPER = {"#e9b949": "#9a6f00"}   # amber fails contrast as text; darken it
PALETTE = [NAVY, TEAL, RUST, PLUM, AMBER, SLATE]
AUDIT_DIR = Path(__file__).resolve().parent.parent / "_audit"


def house_style() -> None:
    mpl.rcParams.update({
        "figure.dpi": 110, "savefig.dpi": 200,
        "font.family": "DejaVu Sans", "font.size": 10.5,
        "axes.prop_cycle": mpl.cycler(color=PALETTE),
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.edgecolor": "#9aa7b3", "axes.labelcolor": INK,
        "xtick.color": MUTED, "ytick.color": MUTED,
        "axes.grid": True, "grid.alpha": 0.3, "grid.linewidth": 0.6,
        "legend.frameon": False, "axes.titlesize": 11,
    })
    if "text.parse_math" in mpl.rcParams:        # '$9.6 ... $30m' is money, not TeX
        mpl.rcParams["text.parse_math"] = False


house_style()

# ----------------------------------------------------------------- registry
_FRAMES: dict = {}       # fig -> list of (frame_patch, [texts])
_ALLOW: dict = {}        # fig -> set of frozenset(id pairs) allowed to touch


def _reg(fig):
    _FRAMES.setdefault(fig, [])
    _ALLOW.setdefault(fig, set())


# ------------------------------------------------------------------- canvas
def canvas(w: float = 10.6, h: float = 5.6):
    """A 0-100 wide canvas; y runs 0..100*h/w so one unit is square."""
    fig = plt.figure(figsize=(w, h))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100 * h / w)
    ax.axis("off")
    _reg(fig)
    return fig, ax


def top(ax) -> float:
    return ax.get_ylim()[1]


def _px_per_unit(ax) -> float:
    a = ax.transData.transform((0, 0))
    b = ax.transData.transform((1, 0))
    return b[0] - a[0]


def _measure(ax, s: str, size: float, weight: str = "normal") -> tuple[float, float]:
    """Width and height of a string, in canvas units."""
    r = ax.figure.canvas.get_renderer()
    t = ax.text(0, 0, s, fontsize=size, fontweight=weight)
    bb = t.get_window_extent(r)
    t.remove()
    k = _px_per_unit(ax)
    return bb.width / k, bb.height / k


def wrap(ax, text: str, width: float, size: float, weight: str = "normal") -> list[str]:
    """Greedy wrap, measuring each candidate line with the renderer."""
    out = []
    for para in text.split("\n"):
        line = ""
        for word in para.split():
            cand = f"{line} {word}".strip()
            if line and _measure(ax, cand, size, weight)[0] > width:
                out.append(line)
                line = word
            else:
                line = cand
        out.append(line)
    return out


def text_block(ax, x, y_top, text, width, size=10, color=INK, weight="normal",
               lead=1.32, ha="left", style="normal"):
    """Draw wrapped text with its top edge at y_top; return (bottom_y, texts)."""
    lines = wrap(ax, text, width, size, weight)
    lh = _measure(ax, "Hg", size, weight)[1] * lead
    xs = {"left": x, "center": x + width / 2, "right": x + width}[ha]
    txt = ax.text(xs, y_top, "\n".join(lines), fontsize=size, color=color,
                  fontweight=weight, va="top", ha=ha, linespacing=lead, style=style)
    return y_top - lh * len(lines), [txt]


def card(ax, x, y_top, w, title, body="", color=NAVY, footer="", kicker="",
         title_size=11.5, body_size=9.6, pad=2.0, fill=PAPER, band=True,
         min_h: float = 0.0):
    """A card whose height is computed from the measured text it holds.
    Returns the bottom y. Text is registered with the frame for gate (b)."""
    texts = []
    y = y_top - pad * 0.8
    if band and kicker:
        bh = _measure(ax, kicker, 8.6, "bold")[1] + 1.4
        ax.add_patch(FancyBboxPatch((x, y_top - bh), w, bh, boxstyle="round,pad=0,rounding_size=1.2",
                                    fc=color, ec="none", zorder=3))
        texts.append(ax.text(x + pad, y_top - bh / 2, kicker, fontsize=8.6, fontweight="bold",
                             color=INK if color == AMBER else "white", va="center", zorder=4))
        y = y_top - bh - pad * 0.7
    if title:
        y, t = text_block(ax, x + pad, y, title, w - 2 * pad, title_size,
                          color=TEXT_ON_PAPER.get(color, color) if band else INK, weight="bold")
        texts += t
        y -= 0.9
    if body:
        y, t = text_block(ax, x + pad, y, body, w - 2 * pad, body_size, color=INK)
        texts += t
        y -= 0.8
    if footer:
        y, t = text_block(ax, x + pad, y - 0.4, footer, w - 2 * pad, 8.8,
                          color=TEXT_ON_PAPER.get(color, color), weight="bold")
        texts += t
    bottom = min(y - pad * 0.7, y_top - min_h)
    frame = FancyBboxPatch((x, bottom), w, y_top - bottom,
                           boxstyle="round,pad=0,rounding_size=1.4",
                           fc=fill, ec=RULE if band else color, lw=1.2, zorder=1)
    ax.add_patch(frame)
    _FRAMES[ax.figure].append((frame, texts))
    return bottom


def pill(ax, x, y, w, h, text, color, size=10, fc=None, tc="white", weight="bold"):
    """A filled rounded box with centred, measured-wrapped text."""
    p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.2",
                       fc=fc or color, ec="none", zorder=2)
    ax.add_patch(p)
    lines = wrap(ax, text, w - 2.4, size, weight)
    t = ax.text(x + w / 2, y + h / 2, "\n".join(lines), ha="center", va="center",
                fontsize=size, color=tc, fontweight=weight, zorder=3, linespacing=1.25)
    _FRAMES[ax.figure].append((p, [t]))
    return t


def arrow(ax, x0, y0, x1, y1, color=SLATE, lw=1.4):
    ax.annotate("", (x1, y1), (x0, y0),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=lw, shrinkA=0, shrinkB=0))


def allow(fig, a, b):
    """Declare two texts allowed to touch (e.g. a label and its leader line)."""
    _reg(fig)
    _ALLOW[fig].add(frozenset((id(a), id(b))))


# ----------------------------------------------------------- deferred header
def finish(fig, label: str, title: str = "", subtitle: str = "",
           source: str = "", tag: str = "", illustrative: bool = False):
    """Place the header band a fixed gap above the real top of content, the
    provenance tag above the frame and the source line below it; then audit."""
    _reg(fig)
    fig.canvas.draw()
    _crop_canvas(fig)
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    H = fig.bbox.height
    tops, bots = [], []
    for ax in fig.axes:
        if ax.axison:                      # a data chart: use its tight box
            bb = ax.get_tightbbox(r)
            tops.append(bb.y1)
            bots.append(bb.y0)
            continue
        skip = {id(ax.patch), id(ax.xaxis), id(ax.yaxis), *map(id, ax.spines.values())}
        for a in ax.get_children():
            if id(a) in skip or not a.get_visible():
                continue
            try:
                bb = a.get_window_extent(r)
            except Exception:
                continue
            if bb.height <= 0 or bb.width <= 0 or bb.height > 5 * H:
                continue
            tops.append(bb.y1)
            bots.append(bb.y0)
    ctop = max(tops) / H if tops else 1.0
    cbot = min(bots) / H if bots else 0.0
    gap = 14 / H
    left = fig.axes[0].get_position().x0 if fig.axes else 0.0
    y = ctop + gap
    if tag or illustrative:
        fig.text(0.99, y, (tag or "").upper() if not illustrative else
                 "ILLUSTRATIVE SHAPE · NO NETWORK AT BUILD · A CONNECTED RENDER REPLACES THIS",
                 ha="right", va="bottom", fontsize=7.4,
                 color=RUST if illustrative else MUTED, fontweight="bold")
        y += 20 / H
    if subtitle:
        fig.text(left, y, subtitle, ha="left", va="bottom", fontsize=10, color=MUTED, style="italic")
        y += 22 / H
    if title:
        fig.text(left, y, title, ha="left", va="bottom", fontsize=14, color=NAVY, fontweight="bold")
    if source:
        fig.text(left, cbot - 16 / H, source, ha="left", va="top", fontsize=8,
                 color=MUTED, style="italic")
    findings = audit(fig)
    AUDIT_DIR.mkdir(exist_ok=True)
    (AUDIT_DIR / f"{label}.txt").write_text("\n".join(findings) or "clean")
    return fig


def _crop_canvas(fig, margin: float = 1.2):
    """Trim a single 0-100 canvas to its content, keeping units square, so no
    exhibit carries a void below (or above) what it draws."""
    if len(fig.axes) != 1 or fig.axes[0].axison:
        return
    ax = fig.axes[0]
    r = fig.canvas.get_renderer()
    skip = {id(ax.patch), id(ax.xaxis), id(ax.yaxis), *map(id, ax.spines.values())}
    inv = ax.transData.inverted()
    ys = []
    for a in ax.get_children():
        if id(a) in skip or not a.get_visible():
            continue
        try:
            bb = a.get_window_extent(r)
        except Exception:
            continue
        if bb.width <= 0 or bb.height <= 0 or bb.height > 5 * fig.bbox.height:
            continue
        ys += [inv.transform((0, bb.y0))[1], inv.transform((0, bb.y1))[1]]
    if not ys:
        return
    y0, y1 = ax.get_ylim()
    lo, hi = min(ys) - margin, max(ys) + margin
    w, h = fig.get_size_inches()
    fig.set_size_inches(w, h * (hi - lo) / (y1 - y0))
    ax.set_ylim(lo, hi)


def audit(fig) -> list[str]:
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    texts = [t for t in fig.texts if t.get_text().strip()]
    for ax in fig.axes:
        texts += [t for t in ax.texts if t.get_text().strip() and t.get_visible()]
        texts += [t for t in [ax.xaxis.label, ax.yaxis.label] if t.get_text()]
    boxes = [(t, t.get_window_extent(r)) for t in texts]
    allowed = _ALLOW.get(fig, set())
    out = []
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            (ta, a), (tb, b) = boxes[i], boxes[j]
            if frozenset((id(ta), id(tb))) in allowed:
                continue
            ov_w = min(a.x1, b.x1) - max(a.x0, b.x0)
            ov_h = min(a.y1, b.y1) - max(a.y0, b.y0)
            if ov_w > 1.5 and ov_h > 1.5:
                out.append(f"TEXT/TEXT  {ta.get_text()[:30]!r} x {tb.get_text()[:30]!r}")
    for frame, ts in _FRAMES.get(fig, []):
        fb = frame.get_window_extent(r)
        for t in ts:
            tb = t.get_window_extent(r)
            if tb.x0 < fb.x0 - 1 or tb.x1 > fb.x1 + 1 or tb.y0 < fb.y0 - 1 or tb.y1 > fb.y1 + 1:
                out.append(f"TEXT/FRAME {t.get_text()[:30]!r} escapes its box")
    return out
