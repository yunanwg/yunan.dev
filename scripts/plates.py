#!/usr/bin/env python3
"""Print the photographic plates (DESIGN-RULES X2) from the git-ignored originals.

Each dot takes the nearest of five inks by colour (ordered 8x8 Bayer dither),
so hue survives. One screen ruling: every file is half its display width and
is shown at exactly 2x. Run: python3 scripts/plates.py
"""
import io
import pathlib
from PIL import Image, ImageOps, ImageEnhance

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "assets"  # git-ignored
OUT = ROOT / "site/img"
INKS = ["eceee8", "c6cf86", "7d9cb4", "4f5d22", "17302a"]  # paper, lichen, glacier, moss, spruce
SPREAD, SAT = 70, 1.6
# (original, published file, display width in CSS px, crop as left,top,right,bottom shares)
PLATES = [
    ("tmb-day7-ibex.jpg", "day7-camp-ibex.png", 576, (0, .2, 1, .92)),
    ("tmb-day5-snow.jpg", "day5-grand-col-ferret.png", 288, (0, .15, 1, 1)),
    ("laugavegur-day3.jpg", "laugavegur-day3.png", 400, (0, .03, 1, .86)),
    ("gravel-200-tree.jpg", "gravel-200-tree.png", 288, (0, .38, 1, 1)),
]
M = [[0,32,8,40,2,34,10,42],[48,16,56,24,50,18,58,26],[12,44,4,36,14,46,6,38],[60,28,52,20,62,30,54,22],
     [3,35,11,43,1,33,9,41],[51,19,59,27,49,17,57,25],[15,47,7,39,13,45,5,37],[63,31,55,23,61,29,53,21]]


def require(*paths) -> None:
    """Generators need the git-ignored originals, which exist only on the author's machine."""
    missing = [str(p.relative_to(ROOT)) for p in paths if not p.exists()]
    if missing:
        raise SystemExit(f"missing {', '.join(missing)}: this generator runs where the originals live "
                         "(assets/ is git-ignored). The committed outputs in site/ are enough to build.")


def d2(a, b):  # redmean-weighted RGB distance
    r = (a[0] + b[0]) / 2
    return (2 + r/256)*(a[0]-b[0])**2 + 4*(a[1]-b[1])**2 + (2 + (255-r)/256)*(a[2]-b[2])**2


def plate(src: pathlib.Path, display_w: int, crop) -> Image.Image:
    inks = [tuple(int(h[i:i+2], 16) for i in (0, 2, 4)) for h in INKS]
    rgb = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    w, h = rgb.size
    rgb = rgb.crop((int(crop[0]*w), int(crop[1]*h), int(crop[2]*w), int(crop[3]*h)))
    tw = display_w // 2
    rgb = rgb.resize((tw, round(rgb.height * tw / rgb.width)), Image.LANCZOS)
    rgb = ImageOps.autocontrast(rgb, cutoff=1)
    rgb = ImageEnhance.Color(rgb).enhance(SAT)
    rgb = ImageEnhance.Contrast(rgb).enhance(1.1)
    px = rgb.load(); q = Image.new("P", rgb.size); qp = q.load()
    for y in range(rgb.height):
        for x in range(rgb.width):
            t = SPREAD * ((M[y % 8][x % 8] + .5) / 64 - .5)
            p = px[x, y]; p = (p[0]+t, p[1]+t, p[2]+t)
            qp[x, y] = min(range(len(inks)), key=lambda i: d2(p, inks[i]))
    flat = [c for ink in inks for c in ink]
    q.putpalette(flat + [0, 0, 0] * (256 - len(inks)))
    return q


def main() -> None:
    require(*(SRC / src for src, *_ in PLATES))
    for src, out, display_w, crop in PLATES:
        q = plate(SRC / src, display_w, crop)
        buf = io.BytesIO(); q.save(buf, "PNG", optimize=True, bits=4)  # no metadata is written
        (OUT / out).write_bytes(buf.getvalue())
        print(f"{out}: {q.width}x{q.height} file, shown {display_w}x{q.height * 2}, {len(buf.getvalue()):,} B")


if __name__ == "__main__":
    main()
