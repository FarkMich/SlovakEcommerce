#!/usr/bin/env python3
"""Vygeneruje Open Graph cover obrázok 1200x630 px do /og-cover.png.

Pokúša sa použiť self-hosted Sora (woff2 -> TTF cez fontTools+brotli),
fallback na systémové Poppins / DejaVu Sans Mono ak brotli nie je dostupné.
"""
from __future__ import annotations
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent.parent
FONTS_DIR = ROOT / "fonts"
OUT_PATH = ROOT / "og-cover.png"

SYSTEM_FALLBACK = {
    "sora-300": "/usr/share/fonts/truetype/google-fonts/Poppins-Light.ttf",
    "sora-400": "/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf",
    "sora-600": "/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf",
    "sora-700": "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf",
    "sora-800": "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf",
    "dmmono-300": "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "dmmono-400": "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "dmmono-500": "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
}

W, H = 1200, 630
PAD = 72

# Paleta z /css/style.css
BG = (18, 14, 8)            # --bg espresso
BG2 = (28, 22, 14)           # panel
GOLD = (212, 165, 90)        # --gold
LIME = (126, 200, 160)       # --lime
WHITE = (240, 232, 216)
WHITE70 = (170, 165, 155)
WHITE40 = (120, 115, 105)
BORDER = (60, 50, 38)


def _try_woff2(src: Path, dst: Path) -> bool:
    try:
        from fontTools.ttLib import TTFont  # requires brotli
        f = TTFont(str(src))
        f.flavor = None
        f.save(str(dst))
        return True
    except Exception:
        return False


def load_font(weight: int, size: int, tmpdir: Path) -> ImageFont.FreeTypeFont:
    key = f"sora-{weight}"
    src = FONTS_DIR / f"sora-{weight}-latin.woff2"
    dst = tmpdir / f"{key}.ttf"
    if src.exists() and _try_woff2(src, dst):
        return ImageFont.truetype(str(dst), size)
    # fallback
    return ImageFont.truetype(SYSTEM_FALLBACK[key], size)


def load_mono(weight: int, size: int, tmpdir: Path) -> ImageFont.FreeTypeFont:
    key = f"dmmono-{weight}"
    src = FONTS_DIR / f"dm-mono-{weight}-latin.woff2"
    dst = tmpdir / f"{key}.ttf"
    if src.exists() and _try_woff2(src, dst):
        return ImageFont.truetype(str(dst), size)
    return ImageFont.truetype(SYSTEM_FALLBACK[key], size)


def hex_polygon(cx: float, cy: float, r: float):
    """Hexagon (flat-top) body pre logo."""
    import math
    pts = []
    for i in range(6):
        a = math.radians(60 * i - 90)  # pointy-top
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def draw_logo(draw: ImageDraw.ImageDraw, cx: float, cy: float, r: float) -> None:
    poly = hex_polygon(cx, cy, r)
    draw.polygon(poly, fill=(int(GOLD[0] * 0.10 + BG[0] * 0.9),
                             int(GOLD[1] * 0.10 + BG[1] * 0.9),
                             int(GOLD[2] * 0.10 + BG[2] * 0.9)),
                 outline=GOLD, width=3)
    # mini line chart vo vnútri loga
    pts = [
        (cx - r * 0.55, cy + r * 0.35),
        (cx - r * 0.22, cy - r * 0.10),
        (cx + r * 0.10, cy + r * 0.15),
        (cx + r * 0.38, cy - r * 0.25),
        (cx + r * 0.62, cy - r * 0.05),
    ]
    draw.line(pts, fill=LIME, width=5, joint="curve")
    draw.ellipse((pts[1][0] - 5, pts[1][1] - 5, pts[1][0] + 5, pts[1][1] + 5), fill=LIME)
    draw.ellipse((pts[3][0] - 5, pts[3][1] - 5, pts[3][0] + 5, pts[3][1] + 5), fill=GOLD)


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        tmpdir = Path(td)
        f_title = load_font(800, 68, tmpdir)
        f_tag = load_font(400, 24, tmpdir)
        f_label = load_mono(500, 16, tmpdir)
        f_brand = load_font(700, 26, tmpdir)

        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)

        # dekoratívne horizontálne linky v pozadí
        for y in range(120, H - 140, 60):
            draw.line([(PAD, y), (W - PAD, y)], fill=BORDER, width=1)

        # horný "chip" label
        chip_text = "DÁTA · TRENDY · ŠTATISTIKY · 2026"
        tw = draw.textlength(chip_text, font=f_label)
        chip_x, chip_y = PAD, PAD
        chip_w, chip_h = tw + 32, 36
        draw.rounded_rectangle(
            (chip_x, chip_y, chip_x + chip_w, chip_y + chip_h),
            radius=18, outline=GOLD, width=2,
        )
        draw.text((chip_x + 16, chip_y + 9), chip_text, font=f_label, fill=GOLD)

        # nadpis — zalomený do ľavého stĺpca (max ~640 px šírka)
        title_max_w = 640
        title1 = "Slovenský"
        title2 = "e-commerce"
        y = 170
        draw.text((PAD, y), title1, font=f_title, fill=WHITE)
        y += 78
        draw.text((PAD, y), title2, font=f_title, fill=GOLD)
        y += 100

        # tagline — zalomiť na dva riadky aby nekolidoval s KPI panelom
        tagline1 = "Komplexný prehľad slovenského"
        tagline2 = "e-commerce trhu · Dáta pre biznis"
        draw.text((PAD, y), tagline1, font=f_tag, fill=WHITE70)
        draw.text((PAD, y + 32), tagline2, font=f_tag, fill=WHITE70)

        # pravá strana — KPI blok (menší, aby sedel)
        kpi_w = 320
        kpi_h = 290
        kpi_x = W - PAD - kpi_w
        kpi_y = 160
        draw.rounded_rectangle(
            (kpi_x, kpi_y, kpi_x + kpi_w, kpi_y + kpi_h),
            radius=18, fill=BG2, outline=BORDER, width=1,
        )
        # KPI rows
        kpis = [
            ("€580 M", "Obrat Shoptet 2025"),
            ("15 000+", "Aktívnych e-shopov"),
            ("6,5 M", "Objednávok / rok"),
            ("85 %",  "Online nákupcov SK"),
        ]
        row_y = kpi_y + 22
        f_kpi = load_font(800, 30, tmpdir)
        f_kpi_sub = load_mono(400, 11, tmpdir)
        for val, lbl in kpis:
            draw.text((kpi_x + 22, row_y), val, font=f_kpi, fill=LIME)
            draw.text((kpi_x + 22, row_y + 36), lbl.upper(), font=f_kpi_sub, fill=WHITE40)
            row_y += 62

        # spodná lišta — logo + domain
        bar_y = H - 100
        draw.line([(PAD, bar_y), (W - PAD, bar_y)], fill=BORDER, width=1)

        # logo hexagon
        logo_r = 28
        draw_logo(draw, PAD + logo_r, bar_y + 46, logo_r)

        # brand text vedľa loga
        brand_x = PAD + logo_r * 2 + 18
        draw.text((brand_x, bar_y + 26), "Slovak", font=f_brand, fill=WHITE)
        sw = draw.textlength("Slovak", font=f_brand)
        draw.text((brand_x + sw + 6, bar_y + 26), "e-commerce", font=f_brand, fill=GOLD)

        # pravá strana — doména
        domain = "slovakecommerce.sk"
        dw = draw.textlength(domain, font=f_label)
        draw.text((W - PAD - dw, bar_y + 36), domain, font=f_label, fill=WHITE40)

        img.save(OUT_PATH, "PNG", optimize=True)
        print(f"✓ {OUT_PATH} ({OUT_PATH.stat().st_size} B, {W}x{H})")


if __name__ == "__main__":
    main()
