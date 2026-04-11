#!/usr/bin/env python3
"""Self-host Google Fonts lokálne.

Stiahne Sora (300/400/600/700/800) + DM Mono (300/400/500), uloží do /fonts/
a vygeneruje /css/fonts.css s @font-face rules (latin + latin-ext subset).

Spusti z rootu repa:
    python3 scripts/download_fonts.py

Potom upraví HTML súbory tak, aby vymenili:
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?..." rel="stylesheet">
za:
    <link rel="preload" href="/fonts/sora-800.woff2" as="font" type="font/woff2" crossorigin>
    <link rel="stylesheet" href="/css/fonts.css">
"""
from __future__ import annotations
import re
import sys
import urllib.request
from pathlib import Path

FONTS_CSS_URL = (
    "https://fonts.googleapis.com/css2?"
    "family=Sora:wght@300;400;600;700;800"
    "&family=DM+Mono:wght@300;400;500"
    "&display=swap"
)

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

HTML_FILES = [
    "index.html", "trh.html", "platformy.html", "eshopari.html",
    "doprava.html", "sk-vs-eu.html", "onas/index.html", "mediakit/index.html",
    "privacy.html",
]

FONT_NAME_MAP = {
    "Sora": "sora",
    "DM Mono": "dm-mono",
}


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def parse_css(css_text: str) -> list[dict]:
    """Parsuje @font-face bloky a vracia list záznamov."""
    blocks = re.findall(r"@font-face\s*\{([^}]+)\}", css_text, re.DOTALL)
    records = []
    current_subset = None
    # Google vracia /* comment */ hneď pred @font-face s subset name.
    # Rozbijeme text podľa komentárov.
    parts = re.split(r"/\*\s*([a-z0-9\-]+)\s*\*/", css_text)
    # parts: ['', 'latin', '@font-face{...}', 'latin-ext', '@font-face{...}', ...]
    for i in range(1, len(parts) - 1, 2):
        subset = parts[i]
        chunk = parts[i + 1]
        for m in re.finditer(r"@font-face\s*\{([^}]+)\}", chunk, re.DOTALL):
            body = m.group(1)
            family = re.search(r"font-family:\s*'([^']+)'", body)
            weight = re.search(r"font-weight:\s*(\d+)", body)
            style = re.search(r"font-style:\s*(\w+)", body)
            src = re.search(r"url\(([^)]+)\)\s*format\('woff2'\)", body)
            unicode_range = re.search(r"unicode-range:\s*([^;]+);", body)
            if not (family and weight and src):
                continue
            records.append({
                "family": family.group(1),
                "weight": int(weight.group(1)),
                "style": (style.group(1) if style else "normal"),
                "url": src.group(1).strip(),
                "unicode_range": (unicode_range.group(1).strip() if unicode_range else None),
                "subset": subset,
            })
    return records


def local_filename(rec: dict) -> str:
    slug = FONT_NAME_MAP.get(rec["family"], rec["family"].lower().replace(" ", "-"))
    return f"{slug}-{rec['weight']}-{rec['subset']}.woff2"


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    fonts_dir = root / "fonts"
    css_dir = root / "css"
    fonts_dir.mkdir(exist_ok=True)
    css_dir.mkdir(exist_ok=True)

    print(f"[1/4] Fetching {FONTS_CSS_URL}")
    css_text = fetch(FONTS_CSS_URL).decode("utf-8")
    records = parse_css(css_text)
    print(f"   -> parsed {len(records)} @font-face entries")

    print("[2/4] Downloading woff2 files")
    for rec in records:
        out = fonts_dir / local_filename(rec)
        if out.exists():
            print(f"   ✓ {out.name} (cached)")
            continue
        data = fetch(rec["url"])
        out.write_bytes(data)
        print(f"   ✓ {out.name} ({len(data)} B)")

    print("[3/4] Writing css/fonts.css")
    lines = [
        "/* Self-hosted fonts - generované scripts/download_fonts.py */",
        "",
    ]
    for rec in records:
        lines.append("@font-face {")
        lines.append(f"  font-family: '{rec['family']}';")
        lines.append(f"  font-style: {rec['style']};")
        lines.append(f"  font-weight: {rec['weight']};")
        lines.append("  font-display: swap;")
        lines.append(f"  src: url('/fonts/{local_filename(rec)}') format('woff2');")
        if rec["unicode_range"]:
            lines.append(f"  unicode-range: {rec['unicode_range']};")
        lines.append("}")
        lines.append("")
    (css_dir / "fonts.css").write_text("\n".join(lines), encoding="utf-8")
    print(f"   -> {css_dir / 'fonts.css'}")

    print("[4/4] Rewriting HTML files (Google Fonts -> local)")
    preconnect_re = re.compile(
        r'<link\s+rel="preconnect"\s+href="https://fonts\.(googleapis|gstatic)\.com"[^>]*>\s*',
        re.IGNORECASE,
    )
    gfont_link_re = re.compile(
        r'<link\s+href="https://fonts\.googleapis\.com/css2[^"]*"\s+rel="stylesheet">\s*',
        re.IGNORECASE,
    )
    # preload najťažší weight (800 latin) pre LCP h1
    preload_tag = (
        '<link rel="preload" href="/fonts/sora-800-latin.woff2" '
        'as="font" type="font/woff2" crossorigin>'
    )
    fonts_css_tag = '<link rel="stylesheet" href="/css/fonts.css">'

    for rel in HTML_FILES:
        p = root / rel
        if not p.exists():
            continue
        html = p.read_text(encoding="utf-8")
        original = html
        html = preconnect_re.sub("", html)
        html = gfont_link_re.sub("", html)
        if "/css/fonts.css" not in html and "</head>" in html:
            inject = f"    {preload_tag}\n    {fonts_css_tag}\n</head>"
            html = html.replace("</head>", inject, 1)
        if html != original:
            p.write_text(html, encoding="utf-8")
            print(f"   edited: {rel}")

    print("\n✅ Done. Nezabudni v scripts/migrate_tracking.py a vercel.json")
    print("   skontrolovať CSP — po self-hostingu už fonts.googleapis.com")
    print("   nemusí byť v style-src/font-src.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
