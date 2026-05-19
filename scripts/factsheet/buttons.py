"""Website-style link buttons — the whole rectangle is one PDF hyperlink."""

from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.artist import Artist
from matplotlib.patches import Rectangle

from scripts.factsheet import theme

BTN_H = 0.030


class RectLink(Artist):
    """PDF Link annotation over a figure-fraction rectangle.

    matplotlib's PDF backend only emits link annotations for text, not
    patches, so we add the whole-button link via the backend's
    _get_link_annotation. No-op on non-PDF backends / API changes.
    """

    def __init__(self, fig: plt.Figure, rect: tuple, url: str) -> None:
        super().__init__()
        self._fig = fig
        self._rect = rect  # (x, y, w, h) figure fractions
        self._url = url
        self.set_zorder(7)

    def draw(self, renderer) -> None:  # noqa: ANN001
        try:
            from matplotlib.backends.backend_pdf import (
                RendererPdf,
                _get_link_annotation,
            )

            # Unwrap the MixedModeRenderer chain to the real RendererPdf.
            pdf = renderer
            seen = set()
            while pdf is not None and id(pdf) not in seen:
                seen.add(id(pdf))
                if isinstance(pdf, RendererPdf):
                    break
                pdf = getattr(pdf, "_renderer", None)
            if not isinstance(pdf, RendererPdf):
                return
            x, y, w, h = self._rect
            (x0, y0) = self._fig.transFigure.transform((x, y))
            (x1, y1) = self._fig.transFigure.transform((x + w, y + h))
            gc = pdf.new_gc()
            gc.set_url(self._url)
            pdf.file._annotations[-1][1].append(
                _get_link_annotation(gc, x0, y0, x1 - x0, y1 - y0)
            )
        except Exception:  # noqa: BLE001 — never break factsheet generation
            return


def draw_link_button(
    fig: plt.Figure,
    x: float,
    y: float,
    w: float,
    label: str,
    url: str,
    *,
    primary: bool,
    height: float = BTN_H,
    fontsize: float = 8,
) -> None:
    """Square-cornered button; whole rect links. Primary = filled ink."""
    face = theme.INK if primary else "#FFFFFF"
    edge = theme.INK if primary else "#D4D4D4"
    fg = "#FFFFFF" if primary else theme.INK
    box = Rectangle(
        (x, y),
        w,
        height,
        transform=fig.transFigure,
        facecolor=face,
        edgecolor=edge,
        linewidth=0.9,
        clip_on=False,
        zorder=5,
    )
    fig.add_artist(box)
    fig.add_artist(RectLink(fig, (x, y, w, height), url))
    mid = y + height / 2
    fig.text(
        x + 0.014,
        mid,
        label,
        fontsize=fontsize,
        weight="semibold",
        color=fg,
        va="center",
        ha="left",
        zorder=6,
    )
    fig.text(
        x + w - 0.012,
        mid,
        "→",
        fontsize=fontsize + 1.5,
        weight="bold",
        color=fg,
        va="center",
        ha="right",
        zorder=6,
    )
