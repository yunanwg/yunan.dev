#!/usr/bin/env python3
"""Make the site icons from the ibex of Fig. 2, in the plates' five inks.

- favicon.ico (16 and 32 px) and favicon-96.png: one pixel per ink, no dither,
  so the silhouette stays legible at tab size. 96 px is what search results
  ask for (a multiple of 48).
- apple-touch-icon.png (180 px): dithered like the plates.
Needs Pillow and the git-ignored original. Run: python3 scripts/icons.py
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import plates  # noqa: E402

ROOT = plates.ROOT
SITE = ROOT / "site"
SRC = ROOT / "assets/tmb-day7-ibex.jpg"
CROP = (0.575, 0.43, 0.835, 0.625)  # the ibex and the snow behind it, square


def icon(px: int, dither: bool):
    plates.SPREAD = 70 if dither else 0
    q = plates.plate(SRC, px * 2, CROP)  # plate() renders at half the display width
    return q.crop((0, 0, px, px)).convert("RGB")


def main() -> None:
    plates.require(SRC)
    small, tiny = icon(32, dither=False), icon(16, dither=False)
    small.save(SITE / "favicon.ico", sizes=[(16, 16), (32, 32)], append_images=[tiny])
    icon(96, dither=False).quantize(colors=5).save(SITE / "favicon-96.png", optimize=True)
    icon(180, dither=True).quantize(colors=5).save(SITE / "apple-touch-icon.png", optimize=True)
    (SITE / "favicon.svg").unlink(missing_ok=True)
    for name in ("favicon.ico", "favicon-96.png", "apple-touch-icon.png"):
        print(name, (SITE / name).stat().st_size, "B")


if __name__ == "__main__":
    main()
