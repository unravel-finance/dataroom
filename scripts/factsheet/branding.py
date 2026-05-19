"""Shared factsheet brand assets.

Things every page shares, kept here so the copies can't drift:
  * the top-left brand lockup (logo mark + "Unravel" wordmark);
  * the brand colour-palette helpers (accent ramps derived from
    ``theme.ACCENT``) used by the charts.
"""

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
    """Draw the logo mark + 'Unravel' wordmark at the top-left.

    Falls back to a text-only wordmark if the rasterised mark isn't present
    (matplotlib can't read the SVG source, so the committed PNG is what we
    embed — see scripts/factsheet/assets/build_logo.py)."""
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
    """`n` shades of the brand accent, darkest first. Used for grouped series
    (the 1D/5D/10D quantile bars) so they read on-brand instead of grey while
    staying distinguishable by lightness."""
    ramp = sns.light_palette(theme.ACCENT, n_colors=n + 1)[1:][::-1]
    return [_to_hex(rgb) for rgb in ramp]


def quantile_palette(n: int) -> list[str]:
    """Single-hue sequential ramp (light → brand accent) for the n quantile
    lines. One colour scheme instead of five distinct hues — quantiles stay
    distinguishable by lightness while the chart stays on-brand."""
    # Light accent-tinted grey for Q1 up to the brand accent for the top.
    ramp = sns.blend_palette(["#D9D9D9", theme.ACCENT_SOFT, theme.ACCENT], n)
    return [_to_hex(rgb) for rgb in ramp]


def accent_by_magnitude(values, *, floor: float = 0.32) -> list[str]:
    """One brand-accent shade per value, intensity scaled by |value|.

    The largest-magnitude bar gets the full accent; smaller bars fade toward
    a light tint but never below ``floor`` so they stay visible on white."""
    cmap = sns.light_palette(theme.ACCENT, as_cmap=True)
    mags = [abs(float(v)) for v in values]
    vmax = max(mags, default=0.0) or 1.0
    return [_to_hex(cmap(floor + (1.0 - floor) * (m / vmax))) for m in mags]
