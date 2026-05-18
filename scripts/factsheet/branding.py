"""Shared factsheet brand header (logo mark + 'Unravel' wordmark).

Page 1 and page 2 render an identical top-left lockup; keeping it here
stops the two copies from drifting.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.image as mpimg
import matplotlib.pyplot as plt

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
