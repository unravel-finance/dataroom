"""Visual theme for the Unravel factsheet PDFs.

Anchors on the unravel.finance brand: a near-black primary on white, with a
restrained accent palette for charts. Typography defaults to the system sans —
DejaVu Sans is pre-installed in matplotlib and reads cleanly in print.
"""

from __future__ import annotations

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import font_manager

# Brand palette — mirrors apps/web/styles/shadcn-ui.css (light theme).
INK = "#0A0A0A"  # neutral-950 — primary text & lines
SUB_INK = "#404040"  # neutral-700 — secondary body
MUTED = "#737373"  # neutral-500 — captions, axis labels
HAIR = "#E5E5E5"  # neutral-200 — hairline rules
BG = "#FFFFFF"
PANEL = "#FAFAFA"  # neutral-50 — stat cards
ACCENT = "#0F766E"  # teal-700 — equity curve / positive
ACCENT_SOFT = "#14B8A6"  # teal-500
NEG = "#B91C1C"  # red-700 — drawdown / negative
BENCH = "#A3A3A3"  # neutral-400 — benchmark / passive series

PAGE_W_IN = 8.27  # A4 portrait
PAGE_H_IN = 11.69
MARGIN_IN = 0.55


def _pick_sans() -> str:
    """Prefer Inter/Mona Sans-like fonts if present, else fall back."""
    preferred = [
        "Inter",
        "Mona Sans",
        "Helvetica Neue",
        "Helvetica",
        "Arial",
        "DejaVu Sans",
    ]
    available = {f.name for f in font_manager.fontManager.ttflist}
    for name in preferred:
        if name in available:
            return name
    return "DejaVu Sans"


def apply_theme() -> None:
    """Apply matplotlib rcParams that match the brand."""
    sans = _pick_sans()
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": [sans, "DejaVu Sans"],
            "font.size": 9,
            "axes.titlesize": 10,
            "axes.titleweight": "semibold",
            "axes.labelsize": 8,
            "axes.labelcolor": SUB_INK,
            "axes.edgecolor": HAIR,
            "axes.linewidth": 0.6,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "xtick.color": MUTED,
            "ytick.color": MUTED,
            "xtick.labelsize": 7.5,
            "ytick.labelsize": 7.5,
            "xtick.direction": "out",
            "ytick.direction": "out",
            "grid.color": HAIR,
            "grid.linewidth": 0.5,
            "grid.linestyle": "-",
            "legend.frameon": False,
            "legend.fontsize": 8,
            "figure.facecolor": BG,
            "axes.facecolor": BG,
            "savefig.facecolor": BG,
            "pdf.fonttype": 42,  # embed TrueType — text remains selectable
            "ps.fonttype": 42,
        }
    )


def new_page() -> "plt.Figure":
    """Return a blank A4 portrait figure with the theme applied."""
    apply_theme()
    fig = plt.figure(figsize=(PAGE_W_IN, PAGE_H_IN), dpi=150)
    return fig
