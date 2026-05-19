"""Brand lockup (logo + wordmark) and accent-palette helpers."""

from __future__ import annotations

from pathlib import Path

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import seaborn as sns

from scripts.factsheet import theme

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
LOGO_PNG = ASSETS_DIR / "unravel-logo.png"

_LOGO_Y = 0.960
_LOGO_H = 0.022


def draw_brand(fig: plt.Figure, margin_x: float) -> None:
    """Logo mark + 'Unravel' wordmark, top-left. Text-only if the PNG is absent."""
    wordmark_x = margin_x
    if LOGO_PNG.exists():
        img = mpimg.imread(LOGO_PNG)
        aspect = img.shape[1] / img.shape[0]
        logo_w = _LOGO_H * (theme.PAGE_H_IN / theme.PAGE_W_IN) * aspect
        ax_logo = fig.add_axes((margin_x, _LOGO_Y - _LOGO_H / 2, logo_w, _LOGO_H))
        ax_logo.imshow(img, interpolation="bilinear")
        ax_logo.axis("off")
        wordmark_x = margin_x + logo_w + 0.010
    fig.text(
        wordmark_x,
        _LOGO_Y,
        "Unravel",
        fontsize=13,
        fontweight="bold",
        color=theme.INK,
        va="center",
        family=theme.display_font(),
    )


def _to_hex(rgb) -> str:
    return "#%02x%02x%02x" % tuple(int(round(c * 255)) for c in rgb[:3])


def accent_ramp(n: int) -> list[str]:
    """`n` accent shades, darkest first — for grouped series (1D/5D/10D bars)."""
    ramp = sns.light_palette(theme.ACCENT, n_colors=n + 1)[1:][::-1]
    return [_to_hex(rgb) for rgb in ramp]


def quantile_palette(n: int) -> list[str]:
    """Single-hue light→accent ramp for the n quantile lines."""
    ramp = sns.blend_palette(["#D9D9D9", theme.ACCENT_SOFT, theme.ACCENT], n)
    return [_to_hex(rgb) for rgb in ramp]


def accent_by_magnitude(values, *, floor: float = 0.32) -> list[str]:
    """One accent shade per value, intensity scaled by |value| (>= floor)."""
    cmap = sns.light_palette(theme.ACCENT, as_cmap=True)
    mags = [abs(float(v)) for v in values]
    vmax = max(mags, default=0.0) or 1.0
    return [_to_hex(cmap(floor + (1.0 - floor) * (m / vmax))) for m in mags]
