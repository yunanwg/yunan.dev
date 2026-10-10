#!/usr/bin/env python3
"""Weigh the page and write the numbers into it.

Elements marked data-m="..." get their real values. Writing the numbers
changes the page size slightly, so we iterate until it is stable.
Used by build.py on dist/; run directly to refresh site/index.html while editing.

Units: B for bytes, kB = 1000 B. Compression is gzip level 9.
Exits 1 if the page breaks the R5 budget (DESIGN-RULES.md).
"""
import gzip
import pathlib
import re
import sys

PAGE = pathlib.Path(__file__).resolve().parent.parent / "site/index.html"
FIRST_ROUND_TRIP_KB = 14.6  # 10 TCP segments x 1460 B
BUDGET_HTML_GZ = 14_000      # R5: HTML, compressed
BUDGET_TOTAL = 100_000       # R5: page + fonts + images, compressed

NUMBER_WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine"}


def weigh(text: str, base: pathlib.Path | None = None) -> dict:
    raw = text.encode()
    fonts = img = 0
    plates = len(set(re.findall(r'<img[^>]*\ssrc="([^"]+)"', text)))
    marks = len(set(re.findall(r'url\("?([^")]+\.png)"?\)', text)))
    if base is not None:
        for url in sorted(set(re.findall(r'url\("?([^")]+\.woff2)"?\)', text))):
            fonts += (base / url).stat().st_size
        srcs = set(re.findall(r'<img[^>]*\ssrc="([^"]+)"', text)) | set(re.findall(r'url\("?([^")]+\.png)"?\)', text))
        srcs |= {m.lstrip("/") for m in re.findall(r'<link rel="icon" href="([^"]+)" sizes="32x32"', text)}  # the tab icon
        for src in sorted(srcs):
            img += (base / src).stat().st_size
    css = sum(len(m.encode()) for m in re.findall(r"<style>(.*?)</style>", text, re.S))
    svg = sum(len(m.encode()) for m in re.findall(r"<svg.*?</svg>", text, re.S))
    scripts = re.findall(r"<script\b(?![^>]*type=\"application/ld\+json\")[^>]*>.*?</script>", text, re.S | re.I)
    js = sum(len(m.encode()) for m in scripts)  # JSON-LD is data the browser never runs
    js += sum(len(m.encode()) for m in re.findall(r'\son[a-z]+="[^"]*"', text))
    gz = len(gzip.compress(raw, 9, mtime=0))
    markup = len(raw) - css - svg - js
    return {"raw": len(raw), "css": css, "svg": svg, "js": js, "html": len(raw) - css, "text": markup,
            "markup": markup, "gz": gz, "fonts": fonts, "img": img, "plates": plates, "marks": marks, "total": gz + fonts + img}


def size_plates(text: str, w: dict) -> str:
    """Fig. 6: each plate's area in proportion to its bytes; an empty part keeps a dashed full outline."""
    biggest = max(w[k] for k in ("markup", "css", "svg", "fonts", "img"))
    def plate(m):
        b = w[m.group(2)]
        s = (b / biggest) ** 0.5 if b else 1
        hw, hh = 110 * s, 18 * s
        pts = f"{140 - hw:.1f},18 140,{18 - hh:.1f} {140 + hw:.1f},18 140,{18 + hh:.1f}"
        return f'{m.group(1)}points="{pts}"{m.group(3)}x1="{140 + hw:.1f}"'
    return re.sub(r'(data-plate="(\w+)" style="[^"]*" )points="[^"]*"(/>\s*<line class="lead" data-lead )x1="[^"]*"', plate, text)


def fill(text: str, w: dict) -> str:
    gz_kb = w["gz"] / 1000
    values = {
        "html": f"{w['html']:,}",
        "css": f"{w['css']:,}",
        "svg": f"{w['svg']:,}",
        "js": f"{w['js']:,}",
        "text": f"{w['text']:,}",
        "markup": f"{w['markup']:,}",
        "gz": f"{gz_kb:.1f}",
        "fonts": f"{w['fonts']:,}",
        "img": f"{w['img']:,}",
        "plates": NUMBER_WORDS.get(w["plates"], str(w["plates"])),
        "marks": NUMBER_WORDS.get(w["marks"], str(w["marks"])),
        "total": f"{w['total'] / 1000:.1f}",
        "f2title": (f"Exploded view of this page, parts unpacked: markup {w['markup']:,} bytes, "
                    f"styles {w['css']:,}, figures {w['svg']:,}, fonts {w['fonts']:,}, images {w['img']:,}, scripts {w['js']:,}."),
    }
    text = size_plates(text, w)
    for key, val in values.items():
        text = re.sub(rf'(data-m="{key}"[^>]*>)[^<]*(<)', rf"\g<1>{val}\g<2>", text)
    pct = min(100, gz_kb / FIRST_ROUND_TRIP_KB * 100)
    text = re.sub(r'style="width:[\d.]+%" data-m="gzpct"', f'style="width:{pct:.0f}%" data-m="gzpct"', text)
    return text


def process(path: pathlib.Path) -> dict:
    text = path.read_text()
    for _ in range(5):
        new = fill(text, weigh(text, path.parent))
        if new == text:
            break
        text = new
    path.write_text(text)
    return weigh(text, path.parent)


def check(w: dict) -> list[str]:
    failures = []
    if w["gz"] > BUDGET_HTML_GZ:
        failures.append(f"HTML {w['gz']:,} B compressed > {BUDGET_HTML_GZ:,} B")
    if w["total"] > BUDGET_TOTAL:
        failures.append(f"page, fonts and images {w['total']:,} B > {BUDGET_TOTAL:,} B")
    if w["js"] > 0:
        failures.append(f"scripts {w['js']:,} B > 0 B")
    return failures


def report(w: dict) -> None:
    failures = check(w)
    if failures:
        print("BUDGET FAILED (R5): " + "; ".join(failures), file=sys.stderr)
        sys.exit(1)
    print(f"budget ok: HTML {w['gz']:,} B / {BUDGET_HTML_GZ:,}, total {w['total']:,} B / {BUDGET_TOTAL:,}, scripts {w['js']} B")


if __name__ == "__main__":
    report(process(PAGE))
