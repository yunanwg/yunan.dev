#!/usr/bin/env python3
"""Build the site: site/ -> dist/, then refuse to ship if a rule is broken.

1. Copy site/ to dist/ (the source is never modified).
2. Check every character on the page is in the font subsets (fonts/subset.txt).
3. Read brilliant-CV's stars and contributors from the GitHub API.
4. Give fonts and images content-hashed names, so they can be cached forever.
5. Weigh the page, write the numbers in, and gate on the R5 budget.

Standard library only. GITHUB_TOKEN, if set, raises the API rate limit.
Run: python3 scripts/build.py
"""
import hashlib
import html
import json
import os
import pathlib
import re
import shutil
import sys
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import measure  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE, DIST = ROOT / "site", ROOT / "dist"
REPO = "yunanwg/brilliant-CV"
AUTHOR_ONLY = {"fonts/subset.txt"}  # kept in the repo, not published


def fail(msg: str) -> None:
    print(f"BUILD FAILED: {msg}", file=sys.stderr)
    sys.exit(1)


def copy() -> None:
    shutil.rmtree(DIST, ignore_errors=True)
    shutil.copytree(SITE, DIST, ignore=shutil.ignore_patterns(".DS_Store"))
    for rel in AUTHOR_ONLY:
        (DIST / rel).unlink(missing_ok=True)


def check_glyphs(page: str) -> None:
    subset = "".join(line.split("\t", 1)[1] for line in (SITE / "fonts/subset.txt").read_text().splitlines())
    text = html.unescape(re.sub(r"<style>.*?</style>|<[^>]+>", " ", page, flags=re.S))
    missing = sorted({ch for ch in text if ch.isprintable() and not ch.isspace() and ch not in subset})
    if missing:
        fail(f"characters not in the font subsets: {''.join(missing)!r}. Run python3 scripts/fonts.py")


def github(path: str):
    req = urllib.request.Request(f"https://api.github.com/{path}", headers={"Accept": "application/vnd.github+json", "User-Agent": "yunan.dev-build"})
    if os.environ.get("GITHUB_TOKEN"):
        req.add_header("Authorization", f"Bearer {os.environ['GITHUB_TOKEN']}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r), r.headers.get("Link", "")


def counts() -> dict:
    """Live counts, or fail: a stale number must not ship (R4). The previous deploy stays up."""
    try:
        repo, _ = github(f"repos/{REPO}")
        _, link = github(f"repos/{REPO}/contributors?per_page=1&anon=1")
    except Exception as e:  # network, rate limit, API change
        fail(f"GitHub API: {e}")
    last = re.search(r'[?&]page=(\d+)>; rel="last"', link)
    return {"stars": f"{repo['stargazers_count']:,}", "contributors": last.group(1) if last else "1"}


def hash_assets(page: str) -> str:
    for path in sorted([*DIST.glob("fonts/*.woff2"), *DIST.glob("img/*.png")]):
        rel = path.relative_to(DIST).as_posix()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()[:10]
        hashed = f"{path.parent.name}/{path.stem}.{digest}{path.suffix}"
        path.rename(DIST / hashed)
        page = page.replace(f'"{rel}"', f'"{hashed}"')
    return page


def main() -> None:
    copy()
    index = DIST / "index.html"
    page = index.read_text()
    check_glyphs(page)
    for key, val in counts().items():
        page, n = re.subn(rf'(data-m="{key}">)[^<]*(<)', rf"\g<1>{val}\g<2>", page)
        if n != 1:
            fail(f'expected one data-m="{key}" in the page, found {n}')
    page = hash_assets(page)
    unhashed = re.findall(r'"((?:fonts|img)/[^"]+)"', page)
    unhashed = [u for u in unhashed if not re.search(r"\.[0-9a-f]{10}\.\w+$", u)]
    if unhashed:
        fail(f"asset references not hashed: {unhashed}")
    index.write_text(page)
    w = measure.process(index)
    print(f"dist/index.html: HTML {w['gz']:,} B gzip, fonts {w['fonts']:,} B, images {w['img']:,} B")
    measure.report(w)


if __name__ == "__main__":
    main()
