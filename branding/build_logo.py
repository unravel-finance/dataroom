"""Rasterise the Unravel brand mark (SVG → PNG) for embedding in factsheets.

The page-1 renderer pairs the mark with a separately-drawn "Unravel" wordmark
in the display font, so this script outputs the *mark only* — no wordmark
composited in.

    python branding/build_logo.py
"""

from __future__ import annotations

import io
from pathlib import Path

import cairosvg
from PIL import Image

HERE = Path(__file__).resolve().parent
SVG = HERE / "unravel-logo.svg"
PNG_OUT = HERE / "unravel-logo.png"


def build_logo(target_height_px: int = 320) -> Path:
    mark_png = cairosvg.svg2png(url=str(SVG), output_height=target_height_px)
    mark = Image.open(io.BytesIO(mark_png)).convert("RGBA")
    bbox = mark.getbbox()
    if bbox:
        mark = mark.crop(bbox)
    mark.save(PNG_OUT, optimize=True)
    return PNG_OUT


if __name__ == "__main__":
    out = build_logo()
    print(f"wrote {out}  ({out.stat().st_size} bytes)  size={Image.open(out).size}")
