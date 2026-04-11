#!/usr/bin/env python3
"""Pridá Plausible custom-event classes na kľúčové CTA prvky."""
from __future__ import annotations
import re
from pathlib import Path

HTML_FILES = [
    "index.html", "trh.html", "platformy.html", "eshopari.html",
    "doprava.html", "sk-vs-eu.html", "onas/index.html", "mediakit/index.html",
    "privacy.html",
]

SUBPAGE_MAP = {
    "/trh.html": "trh",
    "/platformy.html": "platformy",
    "/eshopari.html": "eshopari",
    "/doprava.html": "doprava",
    "/sk-vs-eu.html": "sk-vs-eu",
}


def add_class(tag: str, extra: str) -> str:
    if 'class="' in tag:
        return re.sub(r'class="([^"]*)"', lambda m: f'class="{m.group(1)} {extra}"', tag, count=1)
    return tag.replace("<a ", f'<a class="{extra}" ', 1)


def process(path: Path) -> list[str]:
    if not path.exists():
        return [f"skipped: {path}"]
    html = path.read_text(encoding="utf-8")
    original = html
    log: list[str] = []

    for href, name in SUBPAGE_MAP.items():
        pattern = re.compile(
            rf'<a\s+href="{re.escape(href)}"[^>]*class="subpage-card[^"]*"[^>]*>',
            re.IGNORECASE,
        )
        def _rep(m: re.Match) -> str:
            if "plausible-event-name" in m.group(0):
                return m.group(0)
            return add_class(m.group(0), f"plausible-event-name=Subpage+Click plausible-event-page={name}")
        html, n = pattern.subn(_rep, html)
        if n:
            log.append(f"+ subpage '{name}' ({n}x)")

    def _mailto(m: re.Match) -> str:
        if "plausible-event-name" in m.group(0):
            return m.group(0)
        return add_class(m.group(0), "plausible-event-name=Email+Click")
    html, n = re.subn(r'<a\s+href="mailto:[^"]+"[^>]*>', _mailto, html)
    if n:
        log.append(f"+ mailto ({n}x)")

    if html != original:
        path.write_text(html, encoding="utf-8")
    else:
        log.append("(no change)")
    return log


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    for rel in HTML_FILES:
        print(f"[{rel}]")
        for line in process(root / rel):
            print(f"  {line}")


if __name__ == "__main__":
    main()
