#!/usr/bin/env python3
"""Nahradí inline nav.js injection skripty statickým HTML nav + footer.

Spracuje všetky HTML stránky:
- odstráni inline (function(){ ... })(); bloky, ktoré injektovali nav/footer
- odstráni akýkoľvek <script src=".../nav.js"> tag
- vloží statický <nav> hneď za <body>
- vloží statický <footer> hneď pred </body>
- pridá <script defer src="/js/nav.js"></script> pred </body>
  (nový nav.js drží iba scroll animácie + .active marker)
- preskočí stránky s vlastným custom nav/footer (onas, mediakit)
  -> tie len dostanú <script defer src="/js/nav.js">
"""
from __future__ import annotations
import re
from pathlib import Path

FULL_NAV_PAGES = [
    "index.html", "trh.html", "platformy.html", "eshopari.html",
    "doprava.html", "sk-vs-eu.html", "privacy.html",
]
SIMPLE_NAV_PAGES = ["onas/index.html", "mediakit/index.html"]

LOGO_SVG = (
    '<svg width="32" height="32" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">'
    '<path d="M18 2L32 10V26L18 34L4 26V10L18 2Z" fill="rgba(212,165,90,0.10)" stroke="#d4a55a" stroke-width="1.2"/>'
    '<polyline points="8,25 12,18 17,21 22,13 28,17" fill="none" stroke="#7ec8a0" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>'
    '<circle cx="12" cy="18" r="1.6" fill="#7ec8a0"/>'
    '<circle cx="22" cy="13" r="1.6" fill="#d4a55a"/>'
    '</svg>'
)

NAV_LINKS = [
    ("/trh.html", "Trh"),
    ("/platformy.html", "Platformy"),
    ("/eshopari.html", "E-shopári"),
    ("/doprava.html", "Doprava & platby"),
    ("/sk-vs-eu.html", "SK vs EÚ"),
]


def render_nav() -> str:
    links = "".join(
        f'<li><a href="{href}">{label}</a></li>' for href, label in NAV_LINKS
    )
    return (
        '<nav>'
        f'<a href="/index.html" class="logo">{LOGO_SVG}'
        '<div class="logo-text">Slovak<span>e-commerce</span></div></a>'
        f'<ul class="nav-links">{links}</ul>'
        '<a href="mailto:pr@slovakecommerce.sk" class="nav-cta plausible-event-name=Email+Click">Spolupráca →</a>'
        '</nav>'
    )


def render_footer() -> str:
    links = "".join(
        f'<li><a href="{href}">{label}</a></li>' for href, label in NAV_LINKS
    )
    return (
        '<footer>'
        '<div class="footer-top">'
        '<div>'
        f'<a href="/index.html" class="logo" style="margin-bottom:14px;display:inline-flex;">{LOGO_SVG}'
        '<span class="logo-text" style="font-size:17px;margin-left:12px;">Slovak<span>e-commerce</span></span></a>'
        '<p class="footer-desc">Komplexný prehľad slovenského e-commerce trhu. Dáta pre e-shopárov, médiá a investorov.</p>'
        '<a href="mailto:pr@slovakecommerce.sk" class="footer-cta plausible-event-name=Email+Click">Spolupráca a médiá →</a>'
        '<a href="mailto:michal@slovakecommerce.sk" class="footer-cta outline plausible-event-name=Email+Click" style="margin-top:6px;">michal@slovakecommerce.sk</a>'
        '</div>'
        '<div class="footer-col">'
        '<h4>Sekcie</h4>'
        f'<ul class="footer-links">{links}'
        '<li><a href="/onas/">O nás</a></li>'
        '<li><a href="/mediakit/">Media kit</a></li>'
        '<li><a href="/privacy.html">Ochrana súkromia</a></li>'
        '</ul>'
        '</div>'
        '</div>'
        '<div class="footer-bottom">'
        '<div class="footer-copy">© 2026 Slovak e-commerce · slovakecommerce.sk</div>'
        '<div class="footer-copy">Dáta: Heureka Group, Shoptet, Levosphere, Packeta, Eurostat, ŠÚ SR</div>'
        '</div>'
        '</footer>'
    )


NAV_SCRIPT_TAG = '<script defer src="/js/nav.js"></script>'

# matches the huge inline IIFE that injects nav + footer + animations
INLINE_NAV_BLOCK = re.compile(
    r"<script>\s*/\*\s*nav\.js.*?\}\)\(\);\s*</script>",
    re.DOTALL,
)
# matches any external nav.js include (in case someone added one)
EXTERNAL_NAV_SCRIPT = re.compile(
    r'<script[^>]*src="[^"]*nav\.js[^"]*"[^>]*>\s*</script>',
    re.IGNORECASE,
)
BODY_OPEN = re.compile(r"<body[^>]*>", re.IGNORECASE)
BODY_CLOSE = re.compile(r"</body>", re.IGNORECASE)


def ensure_body_close(html: str) -> str:
    """Ak HTML nemá </body></html>, doplní ich na koniec (platformy.html, trh.html…)."""
    if "</body>" not in html:
        html = html.rstrip() + "\n\n</body>\n</html>\n"
    return html


def strip_existing_nav_footer(html: str) -> str:
    """Odstráni existujúce statické <nav>…</nav> a <footer>…</footer>, ak tam sú.
    Bezpečne to robíme len pre FULL_NAV_PAGES, kde vieme že máme štandardný layout."""
    html = re.sub(r"<nav>.*?</nav>", "", html, count=1, flags=re.DOTALL)
    html = re.sub(r"<footer>.*?</footer>", "", html, count=1, flags=re.DOTALL)
    return html


def process_full(path: Path) -> list[str]:
    if not path.exists():
        return [f"skipped: {path} (missing)"]
    html = path.read_text(encoding="utf-8")
    original = html
    log: list[str] = []

    html, n = INLINE_NAV_BLOCK.subn("", html)
    if n:
        log.append(f"- inline nav.js block ({n}x)")

    html, n = EXTERNAL_NAV_SCRIPT.subn("", html)
    if n:
        log.append(f"- external nav.js ({n}x)")

    html = strip_existing_nav_footer(html)
    html = ensure_body_close(html)

    nav_html = render_nav()
    html = BODY_OPEN.sub(lambda m: f"{m.group(0)}\n{nav_html}\n", html, count=1)
    log.append("+ static <nav>")

    footer_html = render_footer()
    html = BODY_CLOSE.sub(f"\n{footer_html}\n{NAV_SCRIPT_TAG}\n</body>", html, count=1)
    log.append("+ static <footer> + nav.js <script>")

    if html != original:
        path.write_text(html, encoding="utf-8")
    else:
        log.append("(no change)")
    return log


def process_simple(path: Path) -> list[str]:
    """Pre onas/mediakit: majú vlastný minimalistický nav - len pridaj nav.js link."""
    if not path.exists():
        return [f"skipped: {path} (missing)"]
    html = path.read_text(encoding="utf-8")
    original = html
    log: list[str] = []
    if "/js/nav.js" not in html:
        html = ensure_body_close(html)
        html = BODY_CLOSE.sub(f"{NAV_SCRIPT_TAG}\n</body>", html, count=1)
        log.append("+ nav.js <script>")
    if html != original:
        path.write_text(html, encoding="utf-8")
    else:
        log.append("(no change)")
    return log


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    for rel in FULL_NAV_PAGES:
        print(f"[{rel}]")
        for line in process_full(root / rel):
            print(f"  {line}")
    for rel in SIMPLE_NAV_PAGES:
        print(f"[{rel}]")
        for line in process_simple(root / rel):
            print(f"  {line}")


if __name__ == "__main__":
    main()
