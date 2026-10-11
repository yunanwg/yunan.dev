#!/usr/bin/env python3
"""Release notes for a tag, grouped by conventional-commit type.

Lists the commits since the previous tag (all of them for the first release),
under headings a reader of the page would recognise. The tag's own annotation,
if it has one, comes first. Standard library only; run by the release job.
Run: python3 scripts/release_notes.py v1.1 > notes.md
"""
import re
import subprocess
import sys

GROUPS = [
    ("feat", "On the page"),
    ("fix", "Fixed"),
    ("perf", "Lighter"),
    ("docs", "Documentation"),
    ("build", "Build"),
    ("ci", "Deployment"),
    ("chore", "Other"),
]


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout.strip()


def main(tag: str) -> None:
    try:
        previous = git("describe", "--tags", "--abbrev=0", f"{tag}^")
        span = f"{previous}..{tag}"
    except subprocess.CalledProcessError:
        previous, span = None, tag
    title = git("tag", "-l", "--format=%(contents:subject)", tag)
    body = git("tag", "-l", "--format=%(contents:body)", tag)
    annotation = f"**{title}**\n\n{body}".strip() if body else (f"**{title}**" if title else "")
    subjects = git("log", "--reverse", "--format=%s", span).splitlines()

    groups: dict[str, list[str]] = {}
    for subject in subjects:
        m = re.match(r"(\w+)(?:\([^)]*\))?!?: (.+)", subject)
        kind, text = (m.group(1), m.group(2)) if m else ("chore", subject)
        groups.setdefault(kind if kind in dict(GROUPS) else "chore", []).append(text[0].upper() + text[1:])

    out = [annotation, ""] if annotation else []
    for kind, heading in GROUPS:
        if groups.get(kind):
            out += [f"## {heading}", *[f"- {line}" for line in groups[kind]], ""]
    out.append(f"Since {previous}." if previous else "The first release.")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv[1])
