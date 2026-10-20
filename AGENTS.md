# AGENTS.md

Instructions for coding agents (and people) working on yunan.dev: a personal
site on a single page, built to be small, fast, script-free and long-lived.
Read `DESIGN-RULES.md` before changing anything visible; rules are cited by
name (R1–R5, T, X, L, C, M, P).

## Where the source lives

The site is edited in a private repository, beside the career facts it must
agree with, and published to github.com/yunanwg/yunan.dev as a pull request
that the private repository's workflow opens and squash-merges. Each publish
is one commit here, titled with the change's Conventional Commit subject.
Don't push or merge in the public repository by hand: the next publish
refuses to overwrite a state it never had. Paths below are relative to this
folder; run the commands from it.

## Layout

```
site/            what ships: index.html, 404.html, _headers, fonts/, img/
scripts/         build.py and the author-time generators
assets/          git-ignored author inputs, never published: original photos
                 (metadata stripped), mark sources, tmb-profile.json for Fig. 1
wrangler.jsonc   Cloudflare Workers static assets (no Worker code yet; one is allowed, see R5)
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

The build strips comments and CSS whitespace from the shipped page, so comment
the source freely; the budget and Fig. 6 measure what ships. It also writes `yunan.1`, the page as a man page (`scripts/manpage.py`; read it with
`curl -sO https://yunan.dev/yunan.1 && man ./yunan.1`), `sitemap.xml` and `.well-known/security.txt` (expiry renewed
on every build). `robots.txt` welcomes search and AI answers and opts out of
training (`Content-Signal: ai-train=no`, plus the training-only crawlers).
The JSON-LD block in the head is data, not script: the budget check ignores it.
HTML is at about 12 of 14 kB, so new head tags or copy still need weighing.

## Editing the page

- `site/index.html` is the only source of copy. Edit it directly.
- Elements with `data-m="..."` are written by the build (sizes, counts). Don't
  hand-edit their values.
- Inline everything except fonts and images. No JavaScript in the page, no
  third-party requests from the reader's browser, no trackers. Server-side work
  (a Worker, build-time fetches, CI dependencies) is fine within R5.
- Numbers must be measured or sourced (R4). Never invent one for a caption or
  a datasheet row. Datasheet rows from the watch (vertical gain, locomotion,
  sleep) are dated snapshots, not build-time reads: refresh them by hand from
  Garmin (the author asks Claude through the Garmin connector), and update the
  date in the row's conditions with the number.
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
| `scripts/plates.py` | `site/img/*.webp` photo plates (needs Pillow) | a photo or crop changes |
| `scripts/marks.py` | `site/img/mark-*.webp` employer marks (needs Pillow) | a mark changes |
| `scripts/icons.py` | `site/favicon.ico`, `favicon-96.png`, `apple-touch-icon.png` from the Fig. 2 ibex (needs Pillow) | the icon changes |
| `scripts/og.py` | `site/og.png`, the link preview: the cover's name beside Fig. 2 (needs Pillow and Chrome) | the cover or Fig. 2 changes |
| `scripts/strip.py` | strips a JPEG's metadata in place, losslessly | a new original lands in `assets/` |
| `scripts/fonts.py` | `site/fonts/*.woff2`, `site/fonts/subset.txt` (needs fontTools) | the build reports a missing character |

`fonts.py` asks the Google Fonts CSS2 API for a server-side subset (`text=`),
then keeps only the OpenType features the page uses (Barlow: kern, liga, tnum),
and self-hosts the result. Visitors never contact Google.

## Browser support

Chrome and Safari (26+) run the scroll-driven animations; Firefox (and Zen)
don't yet, so there Fig. 6 is shown already exploded. Only Chromium highlights
the current thumb tab (`:target-current`). Check forced colours (Windows
contrast themes) after touching the marks or the cover: they drop author
backgrounds, which is why the marks get `forced-color-adjust: none`. Print from Firefox too:
it drops any SVG filled with a pattern (and text after it on the page), prints
the screen's animation state, and ignores `break-after: avoid`; the print
stylesheet works around all three. Anything that
must work everywhere uses plain CSS, such as the thumb index, which is
`position: sticky`. Respect `prefers-reduced-motion` and keep the print
stylesheet working.

## Commits

[Conventional Commits](https://www.conventionalcommits.org/): `type: subject`
in plain English, imperative, lower case after the colon, no trailing period.
Release notes are grouped by type, so pick it by what the reader of the page
would notice:

| Type | For |
|---|---|
| `feat` | something new on the page (a figure, a section, a datasheet row) |
| `fix` | something on the page that was wrong or broken |
| `perf` | the same page, fewer bytes |
| `docs` | AGENTS.md, DESIGN-RULES.md, README |
| `build` | `build.py`, `measure.py` and the generators |
| `ci` | workflows, Dependabot, deploy configuration |
| `chore` | anything else |

Commits are signed. No AI attribution trailers.

## Deploying

Pushes to `main` build and deploy through GitHub Actions with
`cloudflare/wrangler-action`. Pull requests build and check without
deploying. Credentials live in the `production` environment, which only
`main` can deploy to: the secret `CLOUDFLARE_API_TOKEN` (Workers deploy only)
and the variable `CLOUDFLARE_ACCOUNT_ID`.

Every build on `main` attests `dist/` (GitHub artifact attestations): anyone can
check that a file served at yunan.dev was built from the commit named in the
colophon, with `gh attestation verify FILE -R yunanwg/yunan.dev`.

Releases: push an annotated tag `vEDITION.REV`, matching what the page
prints (cover "edition 1", datasheet "Rev. 1" is `v1.1`); raise the page's
numbers in the same commit as the tag. The tag builds and attests the site, then publishes a
release with the site as a tarball and `yunan.1`, and notes grouped by commit
type (`scripts/release_notes.py`). The tag's message opens the notes. Tags
don't deploy; `main` does.

IPFS: every build also addresses `dist/` on IPFS, offline, with kubo's
`unixfs-v1-2025` profile (IPIP-499) and `--hidden` (the profile would drop
`.well-known/`), and attests the resulting `site.car` beside `dist/**`. A deploy
from `main` then pins the CAR on Filebase (S3 import, so the pinned CID is the
build's, and the job checks it) and points the Filebase IPNS name `yunan-dev`
at it, keeping the last 10 pins. `yunan.eth`'s contenthash is `ipns://<that
name>`, set once from the owner's wallet, so https://yunan.eth.limo serves the
same bytes as yunan.dev with no signature per deploy. The `production`
environment holds `FILEBASE_KEY`, `FILEBASE_SECRET` and the variable
`FILEBASE_BUCKET`; without the variable the step is skipped. A release also
attaches the CAR. To check a served page against a release:
`ipfs init --profile unixfs-v1-2025 && ipfs add -r --hidden --only-hash -Q DIR`
on the unpacked tarball prints the same CID as that run's summary.

Actions are pinned to commit SHAs and the repository refuses unpinned ones;
Dependabot, configured in the private repository, opens a weekly PR there to move them. `links.yml` checks the page's links
every Monday; a failure only sends an email.

## Cloudflare zone notes

- **No injected scripts.** On the Free plan, turning Bot Fight Mode on once also
  turns on JavaScript Detections, which inject a `<script>` from
  `/cdn-cgi/challenge-platform/` into every HTML response; the dashboard can't
  turn it off again. It was turned off through the API on 2026-10-11:
  `PUT /zones/{zone_id}/bot_management` with `{"fight_mode":false,"enable_js":false}`,
  using a short-lived token with Zone > Bot Management > Edit. Don't re-enable
  Bot Fight Mode. Don't use `Cache-Control: no-transform` as a workaround: it
  also stops compression (about 42 kB instead of 13.5 kB).
  Check: `curl -s https://yunan.dev/ | grep -c challenge-platform` should print 0.
