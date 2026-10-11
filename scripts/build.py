#!/usr/bin/env python3
"""Build the site: site/ -> dist/, then refuse to ship if a rule is broken.

1. Copy site/ to dist/ (the source is never modified).
2. Check every character on the page is in the font subsets (fonts/subset.txt),
   then drop comments and CSS whitespace (the source keeps them for people).
3. Read brilliant-CV's stars and contributors from the GitHub API.
4. Give fonts and images content-hashed names, so they can be cached forever.
5. Write sitemap.xml and .well-known/security.txt.
6. Weigh the page, write the numbers in, and gate on the R5 budget.

Standard library only. GITHUB_TOKEN, if set, raises the API rate limit.
Run: python3 scripts/build.py
"""
import datetime
import hashlib
import html
import json
import os
import pathlib
import re
import shutil
import subprocess
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
    text = html.unescape(re.sub(r"<style>.*?</style>|<script\b.*?</script>|<[^>]+>", " ", page, flags=re.S))
    missing = sorted({ch for ch in text if ch.isprintable() and not ch.isspace() and ch not in subset})
    if missing:
        fail(f"characters not in the font subsets: {''.join(missing)!r}. Run python3 scripts/fonts.py")


def minify(page: str) -> str:
    """Comments and CSS indentation are for people reading site/; visitors don't download them.
    Strings are left alone, and spaces around ":" are kept ("a :hover" is not "a:hover")."""
    def css(m):
        parts = re.split(r'("[^"]*"|\'[^\']*\')', re.sub(r"/\*.*?\*/", "", m.group(1), flags=re.S))
        for i in range(0, len(parts), 2):
            parts[i] = re.sub(r"\s*([{};,>])\s*", r"\1", re.sub(r"\s+", " ", parts[i])).replace(";}", "}")
        return "<style>" + "".join(parts).strip() + "</style>"
    page = re.sub(r"<!--.*?-->\s*", "", page, flags=re.S)
    return re.sub(r"<style>(.*?)</style>", css, page, flags=re.S)


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
    for path in sorted([*DIST.glob("fonts/*.woff2"), *DIST.glob("img/*.webp")]):
        rel = path.relative_to(DIST).as_posix()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()[:10]
        hashed = f"{path.parent.name}/{path.stem}.{digest}{path.suffix}"
        path.rename(DIST / hashed)
        page = page.replace(f'"{rel}"', f'"{hashed}"')
    return page


def last_modified() -> str:
    """When the page last changed: its last commit, or today outside a git checkout."""
    try:
        out = subprocess.run(["git", "log", "-1", "--format=%cs", "--", "site/"], cwd=ROOT,
                             capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        out = ""
    return out or datetime.date.today().isoformat()


def well_known() -> None:
    (DIST / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f'  <url><loc>https://yunan.dev/</loc><lastmod>{last_modified()}</lastmod></url>\n'
        '</urlset>\n')
    # RFC 9116 wants an expiry under a year away; the weekly rebuild keeps it fresh.
    expires = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=360)).strftime("%Y-%m-%dT00:00:00Z")
    (DIST / ".well-known").mkdir(exist_ok=True)
    (DIST / ".well-known/security.txt").write_text(
        "Contact: mailto:bonjour@yunan.dev\n"
        f"Expires: {expires}\n"
        "Preferred-Languages: en, fr, zh\n"
        "Canonical: https://yunan.dev/.well-known/security.txt\n")


def main() -> None:
    copy()
    index = DIST / "index.html"
    page = index.read_text()
    check_glyphs(page)
    page = minify(page)
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
    well_known()
    w = measure.process(index)
    print(f"dist/index.html: HTML {w['gz']:,} B gzip, fonts {w['fonts']:,} B, images {w['img']:,} B")
    measure.report(w)


if __name__ == "__main__":
    main()
