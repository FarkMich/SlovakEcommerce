#!/usr/bin/env python3
"""Synchronizuje Open Graph + Twitter Card meta tagy naprieč všetkými HTML.

- Všetky stránky používajú /og-cover.png (absolútna URL).
- Zachováva rôzne og:title / og:description pre jednotlivé stránky.
- Idempotentné: opakovane spustené prepíše existujúce og:/twitter: bloky.
"""
from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://slovakecommerce.sk"
IMAGE = f"{SITE}/og-cover.png"

# rel_path -> (og:title, og:description, og:url path, og:type)
PAGES = {
    "index.html": (
        "Slovenský e-commerce 2026 | Dáta, trendy a štatistiky",
        "Komplexný prehľad slovenského e-commerce trhu. €580M obrat, 15 000+ e-shopov, 6,5M objednávok. Dáta pre e-shopárov, médiá a investorov.",
        "/",
        "website",
    ),
    "trh.html": (
        "Trh | Slovenský e-commerce 2026",
        "Veľkosť slovenského e-commerce trhu, obrat, AOV, medziročný rast. Oficiálne dáta Shoptet, Heureka a ŠÚ SR.",
        "/trh.html",
        "article",
    ),
    "platformy.html": (
        "Platformy | Slovenský e-commerce 2026",
        "Shoptet, WooCommerce, Shopify a ďalšie e-commerce platformy na Slovensku. Dáta BuiltWith a prehľad hosting infraštruktúry.",
        "/platformy.html",
        "article",
    ),
    "eshopari.html": (
        "E-shopári | Slovenský e-commerce 2026",
        "Kto sú slovenskí e-shopári, čo ich trápi, ako rastú. Segmentácia trhu, výzvy a príležitosti.",
        "/eshopari.html",
        "article",
    ),
    "doprava.html": (
        "Doprava a platby | Slovenský e-commerce 2026",
        "Najpoužívanejší dopravcovia a platobné metódy v slovenskom e-commerce. Packeta, Slovenská pošta, GLS, karty vs COD.",
        "/doprava.html",
        "article",
    ),
    "sk-vs-eu.html": (
        "SK vs EÚ | Slovenský e-commerce 2026",
        "Ako si Slovensko stojí v online nákupoch v porovnaní s EÚ. Live dáta z Eurostat isoc_ec_ib20.",
        "/sk-vs-eu.html",
        "article",
    ),
    "privacy.html": (
        "Ochrana súkromia | Slovak e-commerce",
        "Ako nakladáme s dátami návštevníkov slovakecommerce.sk. Plausible Analytics, žiadne cookies, GDPR.",
        "/privacy.html",
        "article",
    ),
    "onas/index.html": (
        "O nás | Slovak e-commerce",
        "Nezávislý dátový projekt o slovenskom e-commerce trhu. Kto je za tým a prečo.",
        "/onas/",
        "article",
    ),
    "mediakit/index.html": (
        "Media kit | Slovak e-commerce",
        "Dáta, grafy a loga na stiahnutie pre médiá. Slovak e-commerce media kit 2026.",
        "/mediakit/",
        "article",
    ),
}


def build_block(title: str, description: str, url_path: str, og_type: str) -> str:
    url = SITE + url_path
    return "\n".join([
        f'<meta property="og:type" content="{og_type}">',
        f'<meta property="og:site_name" content="Slovak e-commerce">',
        f'<meta property="og:locale" content="sk_SK">',
        f'<meta property="og:title" content="{title}">',
        f'<meta property="og:description" content="{description}">',
        f'<meta property="og:url" content="{url}">',
        f'<meta property="og:image" content="{IMAGE}">',
        f'<meta property="og:image:width" content="1200">',
        f'<meta property="og:image:height" content="630">',
        f'<meta property="og:image:alt" content="Slovenský e-commerce 2026 – cover s kľúčovými štatistikami">',
        f'<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{title}">',
        f'<meta name="twitter:description" content="{description}">',
        f'<meta name="twitter:image" content="{IMAGE}">',
        f'<meta name="description" content="{description}">',
    ])


# Match existing og:*, twitter:*, meta name="description" blocks (contiguous)
META_LINE_RE = re.compile(
    r'\s*<meta\s+(?:property="og:[^"]+"|name="twitter:[^"]+"|name="description")[^>]*>\s*',
    re.IGNORECASE,
)


def replace_meta_block(html: str, new_block: str) -> str:
    """Odstráni všetky existujúce og:/twitter:/description meta tagy a vloží nový
    blok za <title>...</title>."""
    html = META_LINE_RE.sub("\n", html)
    # Collapse multiple blank lines
    html = re.sub(r"\n{3,}", "\n\n", html)
    title_end = re.search(r"</title>\s*", html, re.IGNORECASE)
    if not title_end:
        return html
    insert_at = title_end.end()
    return html[:insert_at] + "\n" + new_block + "\n" + html[insert_at:]


def main() -> None:
    for rel, (title, description, url_path, og_type) in PAGES.items():
        p = ROOT / rel
        if not p.exists():
            print(f"skip: {rel} (missing)")
            continue
        html = p.read_text(encoding="utf-8")
        block = build_block(title, description, url_path, og_type)
        new_html = replace_meta_block(html, block)
        if new_html != html:
            p.write_text(new_html, encoding="utf-8")
            print(f"updated: {rel}")
        else:
            print(f"no change: {rel}")


if __name__ == "__main__":
    main()
