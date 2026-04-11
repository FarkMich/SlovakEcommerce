#!/usr/bin/env python3
"""Odstráni GTM+GA4 zo všetkých HTML, pridá Plausible a link na /css/style.css."""
from __future__ import annotations
import re
from pathlib import Path

HTML_FILES = [
    "index.html", "trh.html", "platformy.html", "eshopari.html",
    "doprava.html", "sk-vs-eu.html", "onas/index.html", "mediakit/index.html",
    "privacy.html",
]

PLAUSIBLE_SCRIPT = (
    '<script defer data-domain="slovakecommerce.sk" '
    'src="https://plausible.io/js/script.outbound-links.tagged-events.js"></script>'
)

GTM_BOOTSTRAP = re.compile(
    r"<script>\(function\(w,d,s,l,i\)\{[^<]*?GTM-596C6QQZ'\);\s*</script>",
    re.DOTALL,
)
GTM_NOSCRIPT = re.compile(
    r"<noscript>\s*<iframe[^>]*GTM-596C6QQZ[^>]*>\s*</iframe>\s*</noscript>",
    re.IGNORECASE | re.DOTALL,
)
GA4_LOADER = re.compile(
    r'<script\s+async\s+src="https://www\.googletagmanager\.com/gtag/js\?id=G-SB4FTZYVRH"></script>',
    re.IGNORECASE,
)
GA4_INLINE = re.compile(
    r"<script>\s*window\.dataLayer\s*=\s*window\.dataLayer\s*\|\|\s*\[\]\s*;\s*function gtag\(\)\s*\{\s*dataLayer\.push\(arguments\);\s*\}\s*gtag\('js',\s*new Date\(\)\);\s*gtag\('config',\s*'G-SB4FTZYVRH'\);\s*</script>",
    re.IGNORECASE,
)
GA4_REF = re.compile(r"G-SB4FTZYVRH", re.IGNORECASE)
GTM_REF = re.compile(r"GTM-596C6QQZ", re.IGNORECASE)

STYLESHEET_LINK = '<link rel="stylesheet" href="/css/style.css">'


def process(path: Path) -> dict:
    if not path.exists():
        return {"path": str(path), "skipped": "missing"}
    original = path.read_text(encoding="utf-8")
    html = original
    changes = []

    for name, pat in (
        ("GTM bootstrap", GTM_BOOTSTRAP),
        ("GTM noscript", GTM_NOSCRIPT),
        ("GA4 loader", GA4_LOADER),
        ("GA4 inline", GA4_INLINE),
    ):
        html, n = pat.subn("", html)
        if n:
            changes.append(f"- {name} ({n}x)")

    stray_ga = len(GA4_REF.findall(html))
    stray_gtm = len(GTM_REF.findall(html))
    if stray_ga:
        changes.append(f"! stray GA4 refs: {stray_ga}")
    if stray_gtm:
        changes.append(f"! stray GTM refs: {stray_gtm}")

    if "plausible.io/js/script" not in html and "</head>" in html:
        html = html.replace("</head>", f"    {PLAUSIBLE_SCRIPT}\n</head>", 1)
        changes.append("+ Plausible script")

    if '/css/style.css' not in html and "</head>" in html:
        html = html.replace("</head>", f'    {STYLESHEET_LINK}\n</head>', 1)
        changes.append("+ link /css/style.css")

    if html != original:
        path.write_text(html, encoding="utf-8")
        return {"path": str(path), "changes": changes}
    return {"path": str(path), "changes": ["(no change)"]}


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    for rel in HTML_FILES:
        r = process(root / rel)
        print(f"[{r['path']}]")
        if "skipped" in r:
            print(f"  -> {r['skipped']}")
        else:
            for c in r["changes"]:
                print(f"  {c}")


if __name__ == "__main__":
    main()
