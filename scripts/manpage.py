#!/usr/bin/env python3
"""Render the built page as a man page, yunan(1), for reading in a terminal.

    curl -sO https://yunan.dev/yunan.1 && man ./yunan.1

The page stays the only source of the words: this reads dist/index.html after
the build has written its numbers, and maps its parts to man(7) macros.
Sections become .SH, routes .SS, paragraphs .PP, lists and datasheet rows .TP,
margin notes indented blocks. Figures keep their captions and the photographs'
alt text, so nothing on the page is lost to a terminal. Links print their
address after the text. Standard library only; called by build.py.
"""
import html.parser
import pathlib
import re

SITE = "https://yunan.dev"
VOID = {"br", "img", "polygon", "line", "path", "circle", "rect", "meta", "link", "input"}


def esc(text: str) -> str:
    """Escape page text for roff: backslashes, and a leading dot or quote that would read as a request."""
    text = text.replace("\\", "\\e")
    return re.sub(r"^([.'])", r"\\&\1", text, flags=re.M)


BR = "\x00"  # a line break inside a block, written out as .br


class Man(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []   # finished roff lines
        self.buf = ""              # inline text of the current block
        self.stack: list[str] = []  # open tags, for context
        self.href: list[str | None] = []
        self.skip = 0              # inside something a terminal can't show
        self.cells: list[str] = []  # the datasheet row being read
        self.in_main = False

    # -- helpers ----------------------------------------------------------
    def flush(self, macro: str | None = None) -> None:
        text = re.sub(r"[ \t]*\n[ \t]*", "\n", re.sub(r"[ \t]+", " ", self.buf)).strip()
        self.buf = ""
        if text:
            if macro:
                self.out.append(macro)
            for line in text.split("\n"):
                line = line.strip()
                if line == BR:
                    self.out.append(".br")
                elif line:
                    self.out.append(re.sub(r"^([.'])", r"\\&\1", line))

    def font(self, f: str) -> None:
        self.buf += f"\\f{f}"

    def inside(self, tag: str, cls: str | None = None) -> bool:
        return any(t.split(".")[0] == tag if cls is None else t == f"{tag}.{cls}" for t in self.stack)

    # -- parser -----------------------------------------------------------
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = (a.get("class") or "").split()
        key = f"{tag}.{cls[0]}" if cls else tag
        if tag not in VOID:
            self.stack.append(key)
        if tag == "main":
            self.in_main = True
        if tag in ("style", "script", "thead") or (tag == "div" and "front" in cls) or (tag == "span" and "tag" in cls):
            self.skip += 1
        if self.skip:
            return
        if tag == "h1":
            self.buf = ""
        elif tag == "h2" and self.in_main:
            self.flush()
        elif tag == "h3" or tag == "header":
            self.flush()
        elif tag == "p":
            self.flush()
        elif tag == "li" and self.inside("ol", "parts"):
            self.flush()
        elif tag == "tr" and self.inside("tbody"):
            self.flush(); self.cells = []
        elif tag == "figure":
            self.flush()
        elif tag == "figcaption":
            self.flush()
        elif tag == "img":
            self.flush(".PP")
            self.buf = "\\fIPhotograph:\\fR " + a.get("alt", "")
            self.flush(".RS\n.PP")
            self.out.append(".RE")
        elif tag == "title" and self.inside("svg"):
            self.flush()
        elif tag == "br":
            self.buf += f"\n{BR}\n"
        elif tag in ("i", "em"):
            self.font("I")
        elif tag in ("b", "strong"):
            self.font("B")
        elif tag == "a":
            self.href.append(a.get("href"))
        elif tag == "sup":
            self.buf += "["

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        key = self.stack.pop() if self.stack else ""
        if tag in ("style", "script", "thead") or key in ("div.front", "span.tag"):
            self.skip -= 1
            return
        if self.skip:
            return
        if tag == "h1":
            pass
        elif tag == "h2" and self.in_main:
            title = re.sub(r"^\s*\d+\s*", "", self.buf).strip()
            self.buf = ""
            self.out.append(f'.SH "{title.upper()}"')
        elif tag == "header":
            self.flush(".PP")
        elif tag == "h3":
            self.out.append(f'.SS "{self.buf.strip()}"'); self.buf = ""
        elif tag == "p":
            if key == "p.note":
                self.buf = self.buf.replace("\\fR", "\\fR ", 1)  # space after the note's letter
                self.out.append(".RS 4")
                self.flush(".PP")
                self.out.append(".RE")
            else:
                self.flush(".PP")
        elif tag == "li" and self.inside("ol", "parts"):
            m = re.match(r"\s*(\d+\.\d+)\s*(.*)", self.buf, re.S)
            self.buf = m.group(2) if m else self.buf
            self.out.append(".TP 5")
            self.out.append(m.group(1) if m else "")
            self.flush()
        elif tag in ("th", "td") and self.inside("tbody"):
            self.cells.append(re.sub(r"\s+", " ", self.buf).strip()); self.buf = ""
        elif tag == "tr" and self.inside("tbody") and len(self.cells) == 4:
            name, value, unit, conditions = self.cells
            self.out += [".TP", f"\\fB{name}\\fR"]
            self.out.append(f"{value} {unit}; {conditions}" if unit != "—" else f"{value}; {conditions}")
        elif tag == "figcaption":
            self.flush(".PP")
        elif tag == "title" and self.inside("svg"):
            self.buf = "\\fIDrawing:\\fR " + self.buf.strip()
            self.out.append(".RS")
            self.flush(".PP")
            self.out.append(".RE")
        elif tag in ("i", "em", "b", "strong"):
            self.font("R")
        elif tag == "a":
            href = self.href.pop() if self.href else None
            if href and href.startswith("http"):
                self.buf += f" <{href}>"
        elif tag == "sup":
            self.buf += "]"
        elif tag == "main":
            self.flush()
            self.in_main = False

    def handle_data(self, data):
        if self.skip:
            return
        if self.inside("svg") and not self.inside("title"):
            return
        self.buf += data.replace("\\", "\\e").replace("\u2011", "-")  # line-start dots are escaped at flush; non-breaking hyphens read as plain ones in a terminal


def render(page: str, date: str) -> str:
    cover = re.search(r'<p class="what">(.*?)</p>', page, re.S).group(1)
    tagline = re.sub(r"<[^>]+>", "", cover).replace("\n", " ")
    tagline = re.sub(r"\s+", " ", tagline).strip()
    fig1 = re.sub(r"<[^>]+>", "", re.search(r'<header class="cover".*?<figcaption>(.*?)</figcaption>', page, re.S).group(1)).strip()
    man = Man()
    man.feed(page[page.index("<main"):page.index("</main>") + 7])
    head = [
        f'.TH YUNAN 1 {date} "yunan.dev" "Field manual"',
        ".SH NAME",
        "yunan \\- Yunan Wang (王煜楠), field manual, edition 1",
        ".SH DESCRIPTION",
        esc(tagline),
        ".PP",
        esc(fig1),
    ]
    tail = [".SH SEE ALSO", f"The illustrated edition: <{SITE}/>"]
    return "\n".join(head + man.out + tail) + "\n"


def write(dist: pathlib.Path, date: str) -> int:
    text = render((dist / "index.html").read_text(), date)
    (dist / "yunan.1").write_text(text)
    return len(text.encode())


if __name__ == "__main__":
    import datetime
    root = pathlib.Path(__file__).resolve().parent.parent
    print(write(root / "dist", datetime.date.today().isoformat()), "B")
