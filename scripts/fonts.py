#!/usr/bin/env python3
"""Subset the two webfonts to the characters the page uses (run when the text gains a new character).

The Google Fonts CSS2 API subsets on the server when given `text=`; this script
asks it once, at author time, and self-hosts the result. Visitors never contact
Google. The character set is recorded in fonts/subset.txt so the build can fail
if the page later uses a character the font doesn't have.

- Barlow Condensed 600 (labels): printable ASCII plus every other non-CJK
  character found in the page, so any English label works.
- Noto Serif SC 700 (the name): exactly the CJK characters in the page.
Run: python3 scripts/fonts.py
"""
import html
import pathlib
import re
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE = ROOT / "site/index.html"
FONTS = ROOT / "site/fonts"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
ASCII = "".join(chr(c) for c in range(0x20, 0x7F))


def is_cjk(ch: str) -> bool:
    return "㐀" <= ch <= "鿿"


def page_chars() -> set[str]:
    text = html.unescape(re.sub(r"<style>.*?</style>|<[^>]+>", " ", PAGE.read_text(), flags=re.S))
    return {ch for ch in text if ch.isprintable() and not ch.isspace()}


def fetch(family: str, chars: str, out: str) -> int:
    css_url = f"https://fonts.googleapis.com/css2?family={family}&text={urllib.parse.quote(chars)}"
    css = urllib.request.urlopen(urllib.request.Request(css_url, headers={"User-Agent": UA}), timeout=30).read().decode()
    font_url = re.search(r"url\((https://[^)]+)\)", css).group(1)
    data = urllib.request.urlopen(urllib.request.Request(font_url, headers={"User-Agent": UA}), timeout=30).read()
    assert data[:4] == b"wOF2", "expected a WOFF2 file"
    (FONTS / out).write_bytes(data)
    return len(data)


def main() -> None:
    chars = page_chars()
    latin = ASCII + "".join(sorted(ch for ch in chars if ch not in ASCII and not is_cjk(ch)))
    cjk = "".join(sorted(ch for ch in chars if is_cjk(ch)))
    print("barlow-condensed-600.woff2", fetch("Barlow+Condensed:wght@600", latin, "barlow-condensed-600.woff2"), "B")
    print("noto-serif-sc-700-name.woff2", fetch("Noto+Serif+SC:wght@700", cjk, "noto-serif-sc-700-name.woff2"), "B")
    (FONTS / "subset.txt").write_text(f"barlow-condensed-600\t{latin}\nnoto-serif-sc-700-name\t{cjk}\n")


if __name__ == "__main__":
    main()
