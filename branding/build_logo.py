"""Generate the combined Unravel logo (mark + 'Unravel' wordmark) as a PNG.

The PNG is committed to `branding/` and used as-is by the factsheet renderer.
Re-run this script if the SVG mark changes — Inter Display Bold is bundled
with the `fonts-inter` Debian package on Ubuntu; install it before running.

    apt install fonts-inter
    python branding/build_logo.py
"""

from __future__ import annotations

import io
from pathlib import Path

import cairosvg
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
SVG = HERE / "unravel-logo.svg"
PNG_OUT = HERE / "unravel-logo.png"

# Locate Inter Display Bold (Display cut is intended for headlines).
FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf",
    "/usr/share/fonts/opentype/inter/Inter-Bold.otf",
]


def _font_path() -> str:
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            return path
    raise FileNotFoundError(
        "Inter font not found. Install `fonts-inter` (Debian/Ubuntu) and retry."
    )


def build_logo(target_height_px: int = 320) -> Path:
    # 1. Rasterise the brand mark on its own.
    mark_png = cairosvg.svg2png(url=str(SVG), output_height=target_height_px)
    mark = Image.open(io.BytesIO(mark_png)).convert("RGBA")
    bbox = mark.getbbox()
    if bbox:
        mark = mark.crop(bbox)

    # 2. Lay out a horizontal canvas: mark | gap | wordmark
    gap_px = int(target_height_px * 0.12)
    # Wordmark cap-height ≈ mark height. Inter Display has roughly 0.72
    # cap-height-to-em ratio, so set the em a touch larger than the mark.
    font_size = int(target_height_px * 1.05)
    font = ImageFont.truetype(_font_path(), font_size)
    word = "Unravel"

    # Use anchor="lt" for predictable placement (left/top).
    probe = Image.new("RGBA", (1, 1))
    draw_probe = ImageDraw.Draw(probe)
    word_bbox = draw_probe.textbbox((0, 0), word, font=font, anchor="lt")
    word_left, word_top, word_right, word_bottom = word_bbox
    word_w = word_right - word_left
    word_h = word_bottom - word_top
    # Generous trailing padding so the wordmark never gets clipped.
    pad_right = int(target_height_px * 0.04)

    canvas_w = mark.width + gap_px + word_w + pad_right
    canvas_h = max(mark.height, word_h)
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))

    mark_y = (canvas_h - mark.height) // 2
    canvas.paste(mark, (0, mark_y), mark)

    word_x = mark.width + gap_px - word_left
    word_y = (canvas_h - word_h) // 2 - word_top
    ImageDraw.Draw(canvas).text(
        (word_x, word_y),
        word,
        font=font,
        fill=(10, 10, 10, 255),
        anchor="lt",
    )

    # Final crop to the bounding box so the image carries no extra margin.
    canvas = canvas.crop(canvas.getbbox())
    canvas.save(PNG_OUT, optimize=True)
    return PNG_OUT


if __name__ == "__main__":
    out = build_logo()
    print(f"wrote {out}  ({out.stat().st_size} bytes)")
