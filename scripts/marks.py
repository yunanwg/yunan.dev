#!/usr/bin/env python3
"""Print the employer marks as 1-bit PNG masks (DESIGN-RULES X2, marks).

The page paints them with the text colour through `mask-image`, so one file
serves light and dark. Edge pixels are ordered-dithered, like the plates.
Sources are the marks only (no wordmarks), light on a dark field.
Run: python3 scripts/marks.py
"""
import io
import pathlib
from PIL import Image, ImageOps

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "site/img"
SRC = ROOT / "assets"  # git-ignored
SIZE = 32  # shown at about 15 CSS px: one dot per device pixel on a 2x screen
LO, HI = 110, 210  # levels: darker than LO is field, lighter than HI is mark
M = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def require(*paths) -> None:
    """Generators need the git-ignored originals, which exist only on the author's machine."""
    missing = [str(p.relative_to(ROOT)) for p in paths if not p.exists()]
    if missing:
        raise SystemExit(f"missing {', '.join(missing)}: this generator runs where the originals live "
                         "(assets/ is git-ignored). The committed outputs in site/ are enough to build.")


def mark(src: pathlib.Path, out: str) -> None:
    im = ImageOps.exif_transpose(Image.open(src)).convert("L")
    bbox = im.point(lambda v: 255 if v > 128 else 0).getbbox()
    im = im.crop(bbox)
    side = max(im.size)
    sq = Image.new("L", (side, side), 0); sq.paste(im, ((side - im.width) // 2, (side - im.height) // 2))
    sq = sq.resize((SIZE, SIZE), Image.LANCZOS)
    px = sq.load(); q = Image.new("P", sq.size); qp = q.load()
    for y in range(SIZE):
        for x in range(SIZE):
            v = min(1, max(0, (px[x, y] - LO) / (HI - LO)))  # the field prints as nothing
            qp[x, y] = 1 if v > (M[y % 4][x % 4] + .5) / 16 else 0
    q.putpalette([0, 0, 0, 0, 0, 0] + [0, 0, 0] * 254)
    buf = io.BytesIO(); q.save(buf, "PNG", optimize=True, bits=1, transparency=0)
    (OUT / out).write_bytes(buf.getvalue())
    print(out, len(buf.getvalue()), "B")


if __name__ == "__main__":
    require(SRC / "mark-qonto.png", SRC / "mark-3ds.jpg")
    mark(SRC / "mark-qonto.png", "mark-qonto.png")
    mark(SRC / "mark-3ds.jpg", "mark-3ds.png")
