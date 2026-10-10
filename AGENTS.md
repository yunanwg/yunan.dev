# AGENTS.md

Instructions for coding agents (and people) working on yunan.dev: a personal
site on a single page, built to be small, fast, script-free and long-lived.
Read `DESIGN-RULES.md` before changing anything visible; rules are cited by
name (R1–R5, T, X, L, C, M, P).

## Layout

```
site/            what ships: index.html, 404.html, _headers, fonts/, img/
scripts/         build.py and the author-time generators
assets/          git-ignored author inputs, never published: original photos
                 (metadata stripped), mark sources, tmb-profile.json for Fig. 1
wrangler.jsonc   Cloudflare Workers static assets, no Worker code
.github/workflows/deploy.yml   build on every push and PR, deploy from main, weekly rebuild
```

## Commands

```sh
python3 scripts/build.py      # site/ -> dist/, then gate; exits 1 on any failure
python3 scripts/measure.py    # refresh the data-m numbers in site/index.html while editing
python3 -m http.server 4173 --directory site   # preview the source
npx wrangler@4 dev            # preview dist/ as Cloudflare serves it, with _headers
```

`build.py` uses the standard library only. It fails, and nothing deploys, when:

- the compressed HTML is over 14,000 B, or page + fonts + images over 100,000 B (R5);
- the page contains any script (R5);
- a character on the page is missing from the font subsets;
- the GitHub API can't be read (a stale count must not ship; the last deploy stays up).

## Editing the page

- `site/index.html` is the only source of copy. Edit it directly.
- Elements with `data-m="..."` are written by the build (sizes, counts). Don't
  hand-edit their values.
- Inline everything except fonts and images. No JavaScript, no third-party
  requests, no trackers.
- Numbers must be measured or sourced (R4). Never invent one for a caption or
  a datasheet row.
- Privacy: no coordinates, no EXIF, no companions' names, no employer
  internals (architectures, internal tool names, colleagues). Originals in
  `assets/` keep only their orientation tag: run `python3 scripts/strip.py` on
  every new photo before it goes anywhere.

## Generators (author time, not in CI)

Their inputs are git-ignored originals, so they run on the author's machine
and their outputs are committed.

| Script | Writes | Run when |
|---|---|---|
| `scripts/fig1.py` | Fig. 1 SVG, keyframes and caption in `site/index.html` | `assets/tmb-profile.json` changes |
| `scripts/plates.py` | `site/img/*.png` photo plates (needs Pillow) | a photo or crop changes |
| `scripts/marks.py` | `site/img/mark-*.png` employer marks (needs Pillow) | a mark changes |
| `scripts/strip.py` | strips a JPEG's metadata in place, losslessly | a new original lands in `assets/` |
| `scripts/fonts.py` | `site/fonts/*.woff2`, `site/fonts/subset.txt` | the build reports a missing character |

`fonts.py` asks the Google Fonts CSS2 API for a server-side subset (`text=`)
and self-hosts the result. Visitors never contact Google.

## Browser support

Chrome and Safari get the scroll-linked extras. Firefox (and Zen) don't yet
support scroll-driven animations or `:target-current`, so there Fig. 6 is shown
already exploded and the current thumb tab isn't highlighted. Anything that
must work everywhere uses plain CSS, such as the thumb index, which is
`position: sticky`. Respect `prefers-reduced-motion` and keep the print
stylesheet working.

## Deploying

Pushes to `main` build and deploy through GitHub Actions with
`cloudflare/wrangler-action`. Pull requests build and check without
deploying. Credentials live in the `production` environment, which only
`main` can deploy to: the secret `CLOUDFLARE_API_TOKEN` (Workers deploy only)
and the variable `CLOUDFLARE_ACCOUNT_ID`.
