"""Justified text layout for the factsheet pages.

matplotlib has no native text justification, so we measure each word's
rendered width and distribute the slack evenly between words. Shared by
page 1 (overview body) and page 2 (notice & disclaimer).
"""

from __future__ import annotations

import textwrap

import matplotlib.pyplot as plt

from scripts.factsheet import theme


def _measure_text_width_frac(
    fig: plt.Figure, text: str, fontsize: float
) -> float:
    """Width of `text` rendered at `fontsize`, in figure-fraction units."""
    renderer = fig.canvas.get_renderer()
    t = fig.text(0, 0, text, fontsize=fontsize)
    px = t.get_window_extent(renderer=renderer).width
    t.remove()
    return px / (fig.dpi * theme.PAGE_W_IN)


def _render_justified_line(
    fig: plt.Figure,
    x_frac: float,
    y_frac: float,
    line: str,
    fontsize: float,
    color: str,
    column_width_frac: float,
) -> None:
    """Render `line` filling exactly `column_width_frac`, distributing extra
    space evenly between words. Single-word lines fall back to left-align."""
    words = line.split()
    if len(words) <= 1:
        fig.text(x_frac, y_frac, line, fontsize=fontsize, color=color, va="top")
        return
    word_widths = [_measure_text_width_frac(fig, w, fontsize) for w in words]
    total_word_w = sum(word_widths)
    gap = (column_width_frac - total_word_w) / (len(words) - 1)
    # Safety: if the line is already wider than the column, don't try to
    # compress (gap would go negative) — just render left-aligned.
    if gap < 0:
        fig.text(x_frac, y_frac, line, fontsize=fontsize, color=color, va="top")
        return
    cur = x_frac
    for word, w in zip(words, word_widths):
        fig.text(cur, y_frac, word, fontsize=fontsize, color=color, va="top")
        cur += w + gap


def _render_justified_block(
    fig: plt.Figure,
    x_frac: float,
    y_top: float,
    column_width_frac: float,
    text: str,
    *,
    fontsize: float,
    color: str,
    linespacing: float,
    wrap_chars: int,
    paragraph_gap: float = 0.6,
) -> None:
    """Render `text` as a justified column. Last line of each paragraph stays
    ragged-right (typographic convention)."""
    line_height_frac = (fontsize * linespacing / 72.0) / theme.PAGE_H_IN
    paragraph_gap_frac = line_height_frac * paragraph_gap

    paragraphs = [
        p.strip().replace("\n", " ") for p in text.split("\n\n") if p.strip()
    ]
    y = y_top
    for p_idx, paragraph in enumerate(paragraphs):
        lines = textwrap.wrap(paragraph, width=wrap_chars, break_long_words=False)
        for i, line in enumerate(lines):
            is_last = i == len(lines) - 1
            if is_last:
                fig.text(x_frac, y, line, fontsize=fontsize, color=color, va="top")
            else:
                _render_justified_line(
                    fig, x_frac, y, line, fontsize, color, column_width_frac
                )
            y -= line_height_frac
        if p_idx < len(paragraphs) - 1:
            y -= paragraph_gap_frac
