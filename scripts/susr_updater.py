#!/usr/bin/env python3
"""
Slovak E-commerce — Štatistický úrad SR Retail Index Updater
Dataset: ob1801ms — Špecifické štruktúry maloobchodu (mesačne)
NACE: G47 — Maloobchod okrem motorových vozidiel
Jednotka: Bázický index, priemer 2021 = 100, stále ceny

API endpoint: https://data.statistics.sk/api/v2/dataset/ob1801ms/{rok}/{mesiac}/
              SPECU_B_AAM2021/NACE2_G47/UNIT_KP_INX/U_OD_0001?lang=sk

Výstup: data/susr_retail.json
Spúšťaj cez GitHub Actions každý pondelok (rovnaký workflow ako eurostat_updater.py)
"""

import json
import urllib.request
from datetime import datetime, date
import os

BASE_URL = "https://data.statistics.sk/api/v2/dataset/ob1801ms"
PARAMS   = "SPECU_B_AAM2021/NACE2_G47/UNIT_KP_INX/U_OD_0001?lang=sk"

MONTHS = ["1.", "2.", "3.", "4.", "5.", "6.",
          "7.", "8.", "9.", "10.", "11.", "12."]

MONTH_LABELS_SK = {
    "1.": "januári", "2.": "februári", "3.": "marci",
    "4.": "apríli",  "5.": "máji",     "6.": "júni",
    "7.": "júli",    "8.": "auguste",  "9.": "septembri",
    "10.": "októbri","11.": "novembri","12.": "decembri"
}
MONTH_SHORT = {
    "1.": "jan", "2.": "feb", "3.": "mar", "4.": "apr",
    "5.": "máj", "6.": "jún", "7.": "júl", "8.": "aug",
    "9.": "sep", "10.": "okt","11.": "nov", "12.": "dec"
}


def fetch_one(year, month):
    url = f"{BASE_URL}/{year}/{month}/{PARAMS}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "slovakecommerce.sk/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            d = json.loads(resp.read().decode())
        val = d.get("value", [None])
        return val[0] if isinstance(val, list) and val else None
    except Exception:
        return None


def fetch_all_data(years):
    data = {}
    total = len(years) * len(MONTHS)
    done = 0
    for year in years:
        data[str(year)] = {}
        for month in MONTHS:
            val = fetch_one(str(year), month)
            data[str(year)][month] = val
            done += 1
            if done % 12 == 0:
                print(f"  {done}/{total} ({year} hotovo)")
    return data


def compute_yoy(data, years):
    """Medziročná zmena v % pre každý mesiac."""
    yoy = {}
    for year in years[1:]:
        prev = str(year - 1)
        curr = str(year)
        yoy[curr] = {}
        for m in MONTHS:
            c = data[curr].get(m)
            p = data[prev].get(m)
            if c is not None and p is not None and p != 0:
                yoy[curr][m] = round((c / p - 1) * 100, 1)
            else:
                yoy[curr][m] = None
    return yoy


def annual_avg(data, year):
    vals = [v for v in data[str(year)].values() if v is not None]
    return round(sum(vals) / len(vals), 1) if vals else None


def find_latest(data, years):
    """Nájdi posledný mesiac s dostupnou hodnotou."""
    for year in reversed(years):
        for month in reversed(MONTHS):
            val = data[str(year)].get(month)
            if val is not None:
                return str(year), month, val
    return None, None, None


def build_output(data, yoy, years):
    latest_year, latest_month, latest_val = find_latest(data, years)
    latest_yoy = yoy.get(latest_year, {}).get(latest_month) if latest_year else None
    prev_year_val = data.get(str(int(latest_year) - 1), {}).get(latest_month) if latest_year else None

    # Ročné priemery
    annual = {str(y): annual_avg(data, y) for y in years}

    # Posledných 24 mesiacov ako časový rad pre graf
    chart_series = []
    for year in years:
        for month in MONTHS:
            val = data[str(year)].get(month)
            yoy_val = yoy.get(str(year), {}).get(month)
            if val is not None:
                chart_series.append({
                    "label": f"{MONTH_SHORT[month]} {year}",
                    "year": year,
                    "month": month,
                    "index": val,
                    "yoy": yoy_val
                })

    return {
        "meta": {
            "dataset": "ob1801ms",
            "indicator": "Maloobchod okrem motorových vozidiel (NACE G47)",
            "unit": "Bázický index, priemer 2021 = 100, stále ceny",
            "source": "Štatistický úrad SR (ob1801ms)",
            "updated": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "updated_display": datetime.utcnow().strftime("%-d. %-m. %Y"),
            "note": "Index 100 = priemer mesiacov roka 2021. Hodnota nad 100 znamená rast oproti základu."
        },
        "latest": {
            "year": latest_year,
            "month": latest_month,
            "month_label": MONTH_LABELS_SK.get(latest_month, latest_month),
            "month_short": MONTH_SHORT.get(latest_month, latest_month),
            "index": latest_val,
            "yoy_pct": latest_yoy,
            "prev_year_index": prev_year_val
        },
        "annual_avg": annual,
        "raw": data,
        "yoy": yoy,
        "chart_series": chart_series[-24:]  # posledných 24 mesiacov
    }


def static_fallback():
    """Aktuálne dáta (december 2025) ako fallback ak API nie je dostupné."""
    print("Používam statický fallback (overené dáta z ŠÚ SR, december 2025)")
    raw = {
        "2021": {"1.":76.8,"2.":79.2,"3.":95.7,"4.":95.4,"5.":101.6,"6.":107.5,
                 "7.":102.3,"8.":103.6,"9.":102.8,"10.":108.5,"11.":108.0,"12.":116.7},
        "2022": {"1.":91.4,"2.":91.9,"3.":111.8,"4.":103.9,"5.":109.3,"6.":108.7,
                 "7.":103.9,"8.":104.2,"9.":104.4,"10.":103.6,"11.":105.6,"12.":117.6},
        "2023": {"1.":90.2,"2.":89.0,"3.":101.9,"4.":92.5,"5.":98.7,"6.":101.7,
                 "7.":96.9,"8.":100.1,"9.":96.4,"10.":102.6,"11.":103.7,"12.":113.3},
        "2024": {"1.":91.9,"2.":93.7,"3.":102.4,"4.":101.4,"5.":103.8,"6.":102.8,
                 "7.":102.6,"8.":100.8,"9.":100.6,"10.":107.6,"11.":108.9,"12.":124.7},
        "2025": {"1.":92.7,"2.":91.3,"3.":99.8,"4.":101.0,"5.":102.0,"6.":102.5,
                 "7.":103.0,"8.":100.1,"9.":102.0,"10.":108.3,"11.":105.4,"12.":118.5}
    }
    years = [2021, 2022, 2023, 2024, 2025]
    yoy = compute_yoy(raw, years)
    return build_output(raw, yoy, years)


def main():
    import sys
    print("=" * 55)
    print("Slovak E-commerce — ŠÚ SR Retail Index Updater")
    print("=" * 55)

    use_static = "--static" in sys.argv

    if use_static:
        output = static_fallback()
    else:
        print("\nSťahujem dáta z ŠÚ SR API...")
        current_year = date.today().year
        years = list(range(2021, current_year + 1))
        data = fetch_all_data(years)

        has_data = any(
            v is not None
            for yr in data.values()
            for v in yr.values()
        )

        if not has_data:
            print("API nedostupné — používam statický fallback")
            output = static_fallback()
        else:
            yoy = compute_yoy(data, years)
            output = build_output(data, yoy, years)

    # Ulož
    os.makedirs("data", exist_ok=True)
    path = "data/susr_retail.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # Prehľad
    l = output["latest"]
    yoy_str = f"{l['yoy_pct']:+.1f} %" if l["yoy_pct"] is not None else "N/A"
    print(f"\n✓ Uložené: {path}")
    print(f"\n📊 Posledný dostupný mesiac: {l['month_short']} {l['year']}")
    print(f"   Index:           {l['index']} (základ 2021=100)")
    print(f"   Medziročná zmena: {yoy_str}")
    print(f"   Predch. rok:     {l['prev_year_index']}")
    print(f"\n📅 Ročné priemery:")
    for yr, avg in sorted(output["annual_avg"].items()):
        bar = "█" * int((avg or 0) / 5)
        print(f"   {yr}: {avg:6.1f}  {bar}")


if __name__ == "__main__":
    main()
