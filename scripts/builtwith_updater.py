#!/usr/bin/env python3
"""
Slovak E-commerce -- BuiltWith Slovakia Platform Scraper
Zdroj: https://trends.builtwith.com/shop/country/Slovakia
Metoda: HTTP scraping verejnej stranky (bez API kluca, bez prihlasenia)
Vystup: data/builtwith_platforms.json
Aktualizacia: 1x mesacne (1. den v mesiaci)
"""

import json
import urllib.request
import re
import os
import sys
from datetime import datetime

URL = "https://trends.builtwith.com/shop/country/Slovakia"

# Farby pre jednotlive platformy
COLORS = {
    "Shoptet":     "#d4a55a",
    "WooCommerce": "#7ec8a0",
    "Shopify":     "#96bf48",
    "Wix":         "#8e77b5",
    "PrestaShop":  "#df0067",
    "OpenCart":    "#44ade5",
    "SmartWeb":    "#e07070",
    "UpGates":     "#6b8f71",
    "Magento":     "#f46f25",
    "BigCommerce": "#34495e",
}

# Fallback -- posledne zname SK data (januar 2025, zdroj: BuiltWith)
FALLBACK_DATA = [
    {"name": "Shoptet",     "count": 7431},
    {"name": "WooCommerce", "count": 5481},
    {"name": "Shopify",     "count": 2423},
    {"name": "Wix",         "count": 2038},
    {"name": "PrestaShop",  "count": 1970},
    {"name": "OpenCart",    "count": 1196},
    {"name": "SmartWeb",    "count": 869},
    {"name": "UpGates",     "count": 853},
]


def fetch_page():
    req = urllib.request.Request(
        URL,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; slovakecommerce.sk/1.0)",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        }
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_platforms(html):
    """
    Vytiahne platformy a pocty z HTML.
    BuiltWith Slovakia stranka ma tabulku s riadkami:
      <td>Shoptet</td><td>7,431</td>  alebo podobne
    Skusa viacero parserov pre robustnost.
    """
    results = []

    # Parser 1: hladaj riadky tabulky s nazvom a cislom
    # Vzor: <a href="/shop/shoptet">Shoptet</a> ... 7,431
    pattern1 = re.findall(
        r'href=["\'][^"\']*shop/([^"\'/?]+)["\'][^>]*>([^<]+)</a>.*?(\d[\d,]+)',
        html, re.IGNORECASE | re.DOTALL
    )
    if pattern1:
        for tech_slug, name, count_str in pattern1:
            count = int(count_str.replace(",", "").replace(" ", ""))
            if count > 0:
                results.append({"name": name.strip(), "count": count})

    # Parser 2: hladaj priamo cisla vedla nazvov platform
    if not results:
        pattern2 = re.findall(
            r'<(?:td|th)[^>]*>\s*<a[^>]*>([^<]+)</a>\s*</(?:td|th)>\s*<(?:td|th)[^>]*>\s*([\d,]+)\s*</(?:td|th)>',
            html, re.IGNORECASE
        )
        for name, count_str in pattern2:
            count = int(count_str.replace(",", ""))
            if count > 0:
                results.append({"name": name.strip(), "count": count})

    # Parser 3: JSON data v skripte (niektoré BuiltWith stranky embeduju data)
    if not results:
        json_match = re.search(r'var\s+chartData\s*=\s*(\[.*?\]);', html, re.DOTALL)
        if json_match:
            try:
                chart = json.loads(json_match.group(1))
                for item in chart:
                    if isinstance(item, dict) and "name" in item and "y" in item:
                        results.append({"name": item["name"], "count": int(item["y"])})
            except Exception:
                pass

    # Deduplikuj a zorad
    seen = set()
    unique = []
    for r in results:
        if r["name"] not in seen:
            seen.add(r["name"])
            unique.append(r)

    return sorted(unique, key=lambda x: x["count"], reverse=True)


def build_output(platforms, source_type="scraped"):
    total = sum(p["count"] for p in platforms)
    result = []
    for p in platforms:
        result.append({
            "name": p["name"],
            "count": p["count"],
            "color": COLORS.get(p["name"], "#888888"),
            "share_pct": round(p["count"] / total * 100, 1) if total > 0 else 0,
            "source": source_type
        })
    return {
        "meta": {
            "source": "BuiltWith.com / trends.builtwith.com/shop/country/Slovakia",
            "url": URL,
            "updated": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "updated_display": datetime.utcnow().strftime("%-d. %-m. %Y"),
            "source_type": source_type
        },
        "total_tracked": total,
        "platforms": result
    }


def main():
    print("=" * 55)
    print("Slovak E-commerce -- BuiltWith SK Scraper")
    print("=" * 55)

    use_static = "--static" in sys.argv

    if not use_static:
        print(f"\nStiahnutie: {URL}")
        try:
            html = fetch_page()
            print(f"  OK ({len(html)} znakov)")

            platforms = parse_platforms(html)

            if platforms:
                print(f"  Najdene platformy: {len(platforms)}")
                output = build_output(platforms, source_type="scraped")
            else:
                print("  Parsing neuspesny -- pouzivam fallback")
                output = build_output(FALLBACK_DATA, source_type="fallback")

        except Exception as e:
            print(f"  Chyba: {e} -- pouzivam fallback")
            output = build_output(FALLBACK_DATA, source_type="fallback")
    else:
        print("\nStaticky fallback mod (--static)")
        output = build_output(FALLBACK_DATA, source_type="fallback")

    # Uloz
    os.makedirs("data", exist_ok=True)
    path = "data/builtwith_platforms.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nUlozene: {path}")
    print(f"Zdroj: {output['meta']['source_type']}")
    print(f"Aktualizovane: {output['meta']['updated_display']}")
    print(f"\nPlatformy:")
    for p in output["platforms"][:10]:
        bar = "=" * int(p["count"] / 200)
        print(f"  {p['name']:<15} {str(p['count']):>6}  ({p['share_pct']}%)  {bar}")


if __name__ == "__main__":
    main()
