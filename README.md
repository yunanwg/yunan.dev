# yunan.dev

The personal site of Yunan Wang, a field manual for one person on a single
page.

It is one HTML file, two font subsets, a handful of dithered images and no
scripts, at about 51 kB. The build refuses to deploy a page over 14 kB of
compressed HTML or 100 kB in total.

- `site/`: the page and everything it loads
- `DESIGN-RULES.md`: the rules the page follows
- `AGENTS.md`: how to build, check and change it

```sh
python3 scripts/build.py
```
