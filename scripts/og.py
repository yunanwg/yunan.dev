#!/usr/bin/env python3
"""Make the link preview image (Open Graph) from the page's own cover.

Lifts the cover's name and line out of site/index.html into a 1200 x 630
frame with Fig. 2 on the right, screenshots it with headless Chrome, and
reduces it to the site's inks. Writes site/og.png. It is fetched by link previews only, never by the
page. Needs Pillow and Google Chrome. Run: python3 scripts/og.py
"""
import pathlib
import re
import subprocess
import tempfile

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
W, H = 1200, 630
FRAME = f"""
html, body {{ width: {W}px; height: {H}px; overflow: hidden; background: var(--spruce); margin: 0; }}
.cover {{ height: {H}px; position: relative; }}
.cover-in {{ padding: 44px 0 0 64px; max-width: 580px; margin: 0; box-sizing: border-box; }}
.cover h1 {{ margin-top: 92px; }}
.cover .zh {{ font-size: 124px; }}
.cover .en {{ font-size: 78px; }}
.cover .what {{ font-size: 21px; max-width: none; }}
.cover figure {{ display: none; }}
.og-plate {{ position: absolute; right: 39px; top: 39px; width: 576px; height: 552px; image-rendering: pixelated; }}
* {{ animation: none !important; }}
"""


def main() -> None:
    page = (SITE / "index.html").read_text()
    head = page[:page.index("</head>")]
    defs = re.search(r'<svg width="0" height="0".*?</svg>', page, re.S).group(0)
    cover = re.search(r'<header class="cover">.*?</header>', page, re.S).group(0)
    # Fig. 2 at the plates' own ruling (2x), on the right; the ride stays on the page.
    plate = re.search(r'<img src="(img/day7-camp-ibex[^"]*)"', page).group(1)
    cover = cover.replace("</header>", f'<img class="og-plate" src="{plate}" alt=""></header>')
    card = f'{head}<style>{FRAME}</style></head><body>{defs}{cover}</body></html>'
    with tempfile.TemporaryDirectory() as tmp:
        # Written next to index.html so the fonts resolve; removed straight after.
        html = SITE / "_og-card.html"
        html.write_text(card)
        shot = pathlib.Path(tmp) / "og.png"
        try:
            subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                            f"--window-size={W},{H}", "--virtual-time-budget=3000", f"--screenshot={shot}", html.as_uri()],
                           check=True, capture_output=True)
        finally:
            html.unlink()
        im = Image.open(shot).convert("RGB").crop((0, 0, W, H))
    im.quantize(colors=12, dither=Image.Dither.NONE).save(SITE / "og.png", optimize=True)
    print("og.png", (SITE / "og.png").stat().st_size, "B")


if __name__ == "__main__":
    main()
