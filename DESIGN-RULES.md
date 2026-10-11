# Design rules

The site is a field manual for one person, on a single page. These rules are
the manual for the manual. The implementation is `site/index.html`.

Each rule is named so it can be cited in a review ("breaks R4"). When a rule
and a nice idea disagree, the rule wins or gets rewritten here first.

## Governing rules

**R1. Material, not effects.** Be bold with material: solid ink surfaces,
texture, type at scale, dense tables. Never with effects: glows, gradients,
shadows, blur, parallax, hover animations on everything. Material reads as care;
effects read as performance.

**R2. Real and working.** Every device must be something a real manual has,
and it must actually work. Contents that link, a thumb index you can use, a print stylesheet that prints, an
exploded view with measured numbers. If it only looks like a manual feature, it
goes.

**R3. One loud place per page.** The cover is loud: a solid ink field with the
name at full scale. Everything after it is quiet paper. Interior pages get one
loud element at most (a figure, a datasheet), never two.

**R4. Every number is measured.** Byte counts, star counts and page weights are
computed at build time and written into the page. Nothing is typed by hand.
Placeholder values are allowed during design but must carry a visible † and a
footnote saying so.

**R5. The budget is a rule, not a goal.**

| What | Limit |
|---|---|
| HTML, compressed | ≤ 14 kB (first round trip) |
| Page + fonts + images, compressed | ≤ 100 kB (images counted at their file size) |
| JavaScript | 0 B |
| Third-party requests at runtime | 0 |

Units: B for bytes, kB = 1000 B, gzip level 9 (a brotli host sends less).
`python3 scripts/build.py` weighs the built page and exits 1 when it breaks
the budget, so an over-budget page is never deployed. The check has been shown
to fail with a lowered budget, so it is real.

## Colour

Solid colours only, from the outdoor side of the palette. No red, no
gradients, no tints used as decoration.

| Token | Light | Dark | Role |
|---|---|---|---|
| `--spruce` | `#17302a` | `#2a5245` | Cover field, spine band, thumb tabs |
| `--lichen` | `#c6cf86` | `#c6cf86` | Ink on spruce; the dither on the cover |
| `--cover-ink` | `#e8ece3` | `#e8ece3` | Text on the cover |
| `--paper` | `#eceee8` | `#111714` | Page background |
| `--ink` | `#18241f` | `#dde3da` | Body text, rules, datasheet frame |
| `--moss` | `#4f5d22` | `#c6cf86` | Section numbers, note markers, margin notes |
| `--dim` | `#5a6660` | `#8f9a93` | Captions, table headers, metadata |
| `--rule` | `#b9c0b6` | `#2b3530` | Hairlines between rows |

Dark `--spruce` is `#2a5245`, lighter than the light-mode value, so the spine
and tabs keep their shape on dark paper (2.1:1 as a shape; was 1.5:1).

Contrast, measured (WCAG 2): ink on paper 13.7:1 (dark 13.9), moss on paper
6.2:1 (dark 11.0), dim on paper 5.1:1 (dark 6.2), cover ink on spruce 11.8:1
(dark 7.3), lichen on spruce 8.5:1 (dark 5.3). Every text pair passes AA; new
pairs must too. Focus rings must reach 3:1 against whatever they sit on: on
the thumb tabs the ring takes the tab's own text colour.

## Type

Three voices, each with one job.

| Voice | Family | Cost | Used for |
|---|---|---|---|
| Reading | System serif: Iowan Old Style, Charter, Palatino, Georgia | 0 B | All running text |
| Labelling | Barlow Condensed 600, ASCII subset | 10.7 KB | The Latin name, section numbers, captions' figure labels, table headers, cover metadata, thumb tabs, spine |
| Name | Noto Serif SC 700, cut to 王煜楠 | 1.6 KB | The Chinese name, nowhere else |
| Data | System monospace | 0 B | Datasheet rows only |

- **T1. Body is never a web font.** Reading text costs nothing and looks native.
- **T2. Display faces are subsets.** Only the characters a page uses ship, and a
  page only declares the fonts it renders (the project page doesn't load the
  name font). A web
  font that grows past 20 KB needs a reason written here.
- **T3. Scale has two ends.** Body at 18 px; the cover name at up to 13 rem;
  section numbers at 5 rem. Nothing in between competes with them.
- **T4. Numbers know where they are.** Old-style figures in running text,
  lining tabular figures in tables and data.
- **T5. Care you can't see.** Balanced headings, `text-wrap: pretty` in
  paragraphs, small caps for abbreviations (AI, LLM, CV, CI), hanging
  punctuation (Safari only; other engines ignore it), real typographic quotes
  and dashes, and a literal space between a section number and its title so
  copied text reads "1 Purpose".
- **T6. No uppercase labels.** Hierarchy comes from the condensed face and from
  size, never from tracked-out capitals.

Licences for both web fonts (SIL OFL 1.1) live next to the font files.

## Texture

**X1. One texture: ordered dither.** A 4 × 4 SVG pattern at 25 % coverage
(about 200 B). It fills the cover's elevation profile in lichen and the plates
of the exploded view in ink. It is not used for backgrounds, borders or
anything decorative. A pattern's colour resolves where the pattern is defined,
so each colour gets its own pattern.

**X2. Photographs are plates.** Photos are printed in five fixed inks by
ordered dither (8 × 8 Bayer): paper `#eceee8`, lichen `#c6cf86`, glacier
`#7d9cb4`, moss `#4f5d22`, spruce `#17302a`. Each dot takes the nearest ink by
colour, not by brightness, so blue stays blue and green stays green; a grey sky
prints as paper. Files are lossless WebPs in the five inks. Glacier is a plate ink only; no
text or UI uses it. Plates keep their inks in dark mode, a printed plate on a
dark page, never a negative.

- **One screen ruling.** Every file is half its display width and shown at
  exactly 2× with `image-rendering: pixelated`: one dot is 2 CSS px on every
  plate. Large plates are 576 px, tall ones 400 px, small ones 288 px. They
  are smoothed only on low-density phones, where shrinking causes moiré.
- **Frameless.** The plate's paper is the page's paper: no frame in light
  mode, a hairline where the page is darker.
- **Placement, not a gallery.** One large plate per route against one small or
  tall one in the margin, alternating sides down the page. At most one overlap
  on the page (Fig. 3 on Fig. 2's corner, ringed in page paper), only where the
  margin is wide enough (≥ 80 rem); phones and print get a plain stack.
- **Captions** state the day or time on the route, read from the photo's own
  date, and nothing that can't be checked. Companions are not named.

- **Marks.** Employer marks (the symbol only, never the wordmark) sit before
  the name in running text, at cap height. They are 32 px 1-bit WebPs with
  ordered-dithered edges (`scripts/marks.py`), used as CSS masks so they take
  the text's own colour in both themes. No brand colour.

Originals stay in the git-ignored `assets/`; published files carry
no metadata. Images (plates and marks) count towards R5; plates load lazily.

## Layout

- **L1. Cover, then paper.** Full-bleed spruce cover: the edition along the
  top, the Chinese name, the Latin name, one italic line, and
  the ride across the bottom edge with its figure caption on a lichen tag.
- **L2. Spine band.** On screens ≥ 62 rem, a 3 rem spruce band runs down the
  left edge, carrying the name and edition, set vertically.
- **L3. Text column plus margin.** Running text in a 36 rem column; notes in
  the margin to its right on wide screens, inline with a moss rule on narrow
  ones. Wide elements (datasheets) span both.
- **L4. Thumb index.** Solid spruce tabs fixed to the right edge on wide
  screens. Plain links everywhere; where the browser supports
  `:target-current`, the tab for the section being read turns lichen. Always
  write it as `:is(:target-current)` so browsers without it keep the hover.
  Each tab is its own legend: hover or keyboard focus widens it to show the
  section's name. The tabs belong to the paper, not the cover: they are a
  zero-height `position: sticky` strip placed after the cover, so they start
  at the top of the paper and can never sit on Fig. 1. No animation, so it
  works the same in every browser.
  Tabs are right-aligned to the viewport edge. Between 62 and 76 rem the main
  column reserves a 3.5 rem right gutter so the tabs never sit on content, and
  the cover caption keeps clear of them at every width.
- **L5. Phones are first-class.** 375 px wide with no horizontal scroll. Grid
  tracks are `minmax(0, 1fr)`; anything wider than the column (tables) scrolls
  inside its own box.
- **L6. (Parked: the site is a single page for now.) Interior pages get a band, not a cover.** A short spruce band with a
  breadcrumb back into the manual, the section number in lichen and the title
  in the condensed face at up to 6 rem, and one italic line. Then paper. The
  band is the page's one loud place (R3), so the rest stays quiet: figures in
  ink dither, no datasheet frame. (A prototype exists outside the repository.)

## Components

**C1. Front matter.** Contents, under a heading with a 2 px rule, only where
there are no thumb tabs: phones and print. On wide screens the tabs carry the
same list, so it would be said twice. (A record of
changes was tried and dropped: the changelog lives in the repository, not on
the page.)

**C2. Section heading.** A moss numeral in the condensed face at 5 rem,
followed by the title in the serif. Numbers are real references: subsections
are 2.1, 2.2, and notes and text may cite them.

**C3. Numbered parts.** Lists of things (principles, projects) carry their
section number (3.1, 3.2) in a hanging column.

**C4. Margin notes.** Lettered (a, b, c), linked from a superscript in the
text, highlighted when targeted. A note adds something; it never repeats the
text or another element on the page.

**C5. Figures.** Numbered (Fig. 1, Fig. 2), drawn in inline SVG, captioned
with what they show and where the data comes from. A figure with placeholder
data says so in its caption.

**C6. Datasheet.** Frame of 2 px ink, a solid ink header bar with the unit name
and revision, columns Parameter, Value, Unit, Conditions. Values right-aligned
in tabular monospace. Humour belongs here, stated as flatly as a real spec.

**C7. Exploded view.** The page split into its parts (markup, styles, figures,
fonts, scripts), each plate labelled with measured bytes, scripts included.
The figure's accessible name carries the same numbers. Filled plates for
parts the page carries, dashed for parts it doesn't. The caption gives the
assembled, compressed total.

**C8. (Parked with L6.) Record of changes, per page.** On a project page the record lists the
project's own releases, taken from its git tags and release commits, never
paraphrased from memory.

## Motion

**M1. Motion is rationed.** The site is a manual, and manuals mostly sit still.
Exactly these may move, all under `prefers-reduced-motion: no-preference`,
none in print:

1. **One load moment.** Fig. 1 is the real Tour du Mont Blanc (June 2025,
   149 km, 8 days), and one edge reveals it left to right at the pace it was
   walked: watch moving time, compressed to 12 s, so the edge slows on the
   climbs. Line and dithered ground are revealed together. Generated by
   `scripts/fig1.py` from `assets/tmb-profile.json` (git-ignored), which holds
   elevation and distance/time shares only, never coordinates. The name and
   caption do not move.
2. **One scroll-linked figure.** Fig. 6, the exploded view, explodes as it scrolls into view:
   plates start stacked and spread apart on a named `view-timeline` shared by
   the whole figure. Only the plates move; labels and leader lines stay put.
   Each plate's area is in proportion to the bytes it stands for (written by
   `scripts/measure.py`); an empty part keeps a dashed full-size outline.
3. **Answers to the reader.** Hover, focus and `:target` changes transition in
   150 ms or less (thumb tabs, link underlines, targeted notes).
4. **A position mark.** On wide screens a pair of short lichen ticks, one on
   each edge so the lettering stays clear, travels down the spine band with `scroll(root)`: where you are in the manual. Without scroll
   timelines there is no tick, rather than a wrong one.

Nothing else moves on its own.

**M2. The base state is the finished state.** Every animation only reveals
what is already there: without animation support, with reduced motion, in
print, in reader modes and in full-page screenshots, the reader sees the
complete figure. A scroll or load animation's start keyframe must still be
legible, because some contexts show nothing else.

**M3. Not in this manual:** fade-and-slide-in on sections, numbers that count
up (datasheet values are measurements, not a scoreboard), parallax, a
shrinking header, a reading-progress bar, hover effects that don't answer the
hover.

## Print

**P1. It prints like a manual.** Colours collapse to black on white, the spine
and thumb index disappear, notes go inline, figures and tables never break
across pages, and external links print their URL after the link text.
The cover's figure caption prints below the profile, not on it. Verified with
headless Chrome: 3 pages (cover to section 2, Fig. 2 to section 3,
specifications to colophon).

## Voice

**V1. Flat statements, dry jokes.** Write like a manual: present tense, short
sentences, no adjectives that sell. Humour is allowed where a manual would
deadpan: the datasheet, field notes, error states.

**V2. No packaging.** If a sentence sounds good but says nothing, cut it.

## Not in this manual

Gradients, drop shadows, glassmorphism, rounded cards, hero images, stock
icons, cursor effects, scroll-jacking, cookie banners, analytics, web fonts for
body text, tracked-out uppercase labels, the colour red.

## Open questions for phase 4

- Real data for the datasheet.
- Font subsetting in CI. See `README.md`.
