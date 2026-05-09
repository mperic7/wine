#!/usr/bin/env python3
"""
Wine E-Label Generator
======================
Generates HTML e-label pages and print-ready QR codes from wines.json.
 
Usage:
    python generate.py                          # uses default domain from wines.json
    python generate.py --domain opg-peric.hr    # override domain
    python generate.py --test                   # use localhost URLs for testing
"""
 
import json
import os
import sys
import argparse
from pathlib import Path
 
# --- Configuration ---
SCRIPT_DIR = Path(__file__).parent
DATA_FILE = SCRIPT_DIR / "data" / "wines.json"
TEMPLATE_FILE = SCRIPT_DIR / "templates" / "elabel.html"
OUTPUT_DIR = SCRIPT_DIR / "site"
QR_DIR = OUTPUT_DIR / "qrcodes"
ELABEL_DIR = OUTPUT_DIR / "elabel"
 
# --- Translations ---
LABELS = {
    "hr": {
        "page_title": "E-oznaka",
        "ingredients": "Sastojci",
        "allergens": "Alergeni",
        "contains": "Sadrži",
        "nutrition": "Nutritivna deklaracija",
        "energy": "Energija",
        "fat": "Masti",
        "saturated_fat": "od kojih zasićene masne kiseline",
        "carbs": "Ugljikohidrati",
        "sugars": "od kojih šećeri",
        "protein": "Bjelančevine",
        "salt": "Sol",
    },
    "en": {
        "page_title": "E-label",
        "ingredients": "Ingredients",
        "allergens": "Allergens",
        "contains": "Contains",
        "nutrition": "Nutrition declaration",
        "energy": "Energy",
        "fat": "Fat",
        "saturated_fat": "of which saturates",
        "carbs": "Carbohydrate",
        "sugars": "of which sugars",
        "protein": "Protein",
        "salt": "Salt",
    }
}
 
 
def load_data():
    """Load wine data from JSON file."""
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
 
 
def load_template():
    """Load HTML template."""
    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        return f.read()
 
 
def format_number(value):
    """Format nutritional values: show '<0.5' for zero, otherwise 1 decimal."""
    if value == 0:
        return "< 0,5"
    return f"{value:.1f}".replace(".", ",")
 
 
def build_ingredients_html(ingredients, allergens):
    """Build ingredients list with allergens highlighted."""
    parts = []
    for ing in ingredients:
        is_allergen = any(a.lower() in ing.lower() for a in allergens)
        if is_allergen:
            parts.append(f'<span class="allergen">{ing}</span>')
        else:
            parts.append(ing)
    return ", ".join(parts)
 
 
def generate_elabel_html(template, wine, lang, labels):
    """Generate a single e-label HTML page."""
    n = wine["nutrition_per_100ml"]
    ingredients = wine["ingredients"].get(lang, wine["ingredients"]["hr"])
    allergens = wine["allergens"].get(lang, wine["allergens"]["hr"])
    responsible = wine["responsible_consumption_note"].get(
        lang, wine["responsible_consumption_note"]["hr"]
    )
 
    replacements = {
        "{{lang}}": lang,
        "{{page_title}}": f'{labels["page_title"]} — {wine["name"]} {wine["vintage"]}',
        "{{wine_id}}": wine["id"],
        "{{wine_name}}": wine["name"],
        "{{vintage}}": str(wine["vintage"]),
        "{{category}}": wine["category"],
        "{{origin}}": wine["origin"],
        "{{alcohol}}": f'{wine["alcohol_pct"]:.1f}'.replace(".", ","),
        "{{volume}}": f'{wine["volume_ml"] / 1000:.2f} L'.replace(".", ","),
        "{{active_hr}}": "active" if lang == "hr" else "",
        "{{active_en}}": "active" if lang == "en" else "",
        "{{label_ingredients}}": labels["ingredients"],
        "{{label_allergens}}": labels["allergens"],
        "{{label_contains}}": labels["contains"],
        "{{label_nutrition}}": labels["nutrition"],
        "{{label_energy}}": labels["energy"],
        "{{label_fat}}": labels["fat"],
        "{{label_saturated_fat}}": labels["saturated_fat"],
        "{{label_carbs}}": labels["carbs"],
        "{{label_sugars}}": labels["sugars"],
        "{{label_protein}}": labels["protein"],
        "{{label_salt}}": labels["salt"],
        "{{ingredients_html}}": build_ingredients_html(ingredients, allergens),
        "{{allergens_text}}": ", ".join(allergens),
        "{{energy_kj}}": str(n["energy_kj"]),
        "{{energy_kcal}}": str(n["energy_kcal"]),
        "{{fat}}": format_number(n["fat_g"]),
        "{{saturated_fat}}": format_number(n["saturated_fat_g"]),
        "{{carbs}}": format_number(n["carbohydrates_g"]),
        "{{sugars}}": format_number(n["sugars_g"]),
        "{{protein}}": format_number(n["protein_g"]),
        "{{salt}}": format_number(n["salt_g"]),
        "{{responsible_note}}": responsible,
    }
 
    html = template
    for key, value in replacements.items():
        html = html.replace(key, value)
    return html
 
 
def generate_qr_code(url, output_path, size_cm=2.0):
    """Generate a high-resolution QR code for print."""
    try:
        import qrcode
        from qrcode.image.styledpil import StyledPilImage
    except ImportError:
        print("GREŠKA: Instaliraj qrcode biblioteku:")
        print("  pip install qrcode[pil]")
        sys.exit(1)
 
    qr = qrcode.QRCode(
        version=None,  # auto-detect
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=20,      # pixels per module — high for print
        border=4,         # quiet zone (standard)
    )
    qr.add_data(url)
    qr.make(fit=True)
 
    img = qr.make_image(fill_color="black", back_color="white")
 
    # Save as PNG
    img.save(str(output_path))
 
    # Also save as SVG for vector print
    svg_path = output_path.with_suffix(".svg")
    generate_qr_svg(qr, svg_path)
 
    return output_path, svg_path
 
 
def generate_qr_svg(qr, output_path):
    """Generate SVG version of QR code for scalable print."""
    matrix = qr.get_matrix()
    size = len(matrix)
    module_size = 10  # SVG units per module
 
    svg_size = size * module_size
    rects = []
    for y, row in enumerate(matrix):
        for x, cell in enumerate(row):
            if cell:
                rects.append(
                    f'<rect x="{x * module_size}" y="{y * module_size}" '
                    f'width="{module_size}" height="{module_size}" fill="black"/>'
                )
 
    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_size} {svg_size}" width="{svg_size}" height="{svg_size}">
  <rect width="{svg_size}" height="{svg_size}" fill="white"/>
  {"".join(rects)}
</svg>'''
 
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg)
 
 
def calculate_nutrition(analysis):
    """
    Calculate nutritional values from lab analysis data.
    Returns dict with per-100ml values.
 
    Based on EU Reg. 1169/2011 Annex XIV conversion factors:
    - Alcohol: 7 kcal/g (29 kJ/g)
    - Carbohydrates: 4 kcal/g (17 kJ/g)
    - Organic acids: 3 kcal/g (13 kJ/g)
    """
    # Alcohol in g per 100ml
    alcohol_g = analysis["actual_alcohol_pct"] * 0.789
 
    # Sugars in g per 100ml
    sugars_g = analysis["reducing_sugars_g_per_l"] / 10
 
    # Organic acids (non-volatile) in g per 100ml
    acids_g = analysis.get("non_volatile_acidity_g_per_l", 0) / 10
 
    # Energy calculation
    energy_kcal = round(alcohol_g * 7 + sugars_g * 4 + acids_g * 3)
    energy_kj = round(alcohol_g * 29 + sugars_g * 17 + acids_g * 13)
 
    return {
        "energy_kj": energy_kj,
        "energy_kcal": energy_kcal,
        "fat_g": 0,
        "saturated_fat_g": 0,
        "carbohydrates_g": round(sugars_g, 1),
        "sugars_g": round(sugars_g, 1),
        "protein_g": 0,
        "salt_g": 0,
    }
 
 
def main():
    parser = argparse.ArgumentParser(description="Wine E-Label Generator")
    parser.add_argument("--domain", help="Override domain (e.g., opg-peric.hr)")
    parser.add_argument("--test", action="store_true", help="Use localhost URLs")
    parser.add_argument("--recalc", action="store_true",
                        help="Recalculate nutrition from analysis data")
    parser.add_argument("--wines", nargs="+", metavar="ID",
                        help="Generiraj samo za navedene ID-jeve (npr. --wines grasevina-2024 frankovka-2024)")
    parser.add_argument("--list", action="store_true",
                        help="Samo ispiši sva vina iz wines.json")
    args = parser.parse_args()
 
    # Load data
    data = load_data()
    template = load_template()
 
    # List mode — just show available wines and exit
    if args.list:
        print("Vina u wines.json:")
        for w in data["wines"]:
            print(f"   {w['id']:30s}  {w['name']} {w['vintage']}")
        return
 
    # Filter wines if --wines specified
    if args.wines:
        selected = [w for w in data["wines"] if w["id"] in args.wines]
        unknown = set(args.wines) - {w["id"] for w in selected}
        if unknown:
            print(f"⚠ Nepoznati ID-jevi: {', '.join(unknown)}")
            print(f"  Koristi --list za popis svih vina")
        wines_to_generate = selected
    else:
        wines_to_generate = data["wines"]
 
    # Determine base URL
    if args.test:
        base_url = "http://localhost:8000"
    elif args.domain:
        base_url = f"https://{args.domain}"
    else:
        base_url = data["winery"]["url"]
 
    # Ensure output directories exist
    ELABEL_DIR.mkdir(parents=True, exist_ok=True)
    QR_DIR.mkdir(parents=True, exist_ok=True)
 
    print(f"🍷 Wine E-Label Generator")
    print(f"   Base URL: {base_url}")
    print(f"   Vina: {len(wines_to_generate)}/{len(data['wines'])}")
    print()
 
    for wine in wines_to_generate:
        # Optionally recalculate nutrition from analysis
        if args.recalc and "analysis" in wine:
            wine["nutrition_per_100ml"] = calculate_nutrition(wine["analysis"])
            print(f"   ↻ Recalculated nutrition for {wine['name']} {wine['vintage']}")
 
        # Generate HTML for each language
        wine_dir = ELABEL_DIR / wine["id"]
        wine_dir.mkdir(parents=True, exist_ok=True)
 
        for lang in LABELS:
            labels = LABELS[lang]
 
            # HR = index.html, other langs = {lang}.html
            filename = "index.html" if lang == "hr" else f"{lang}.html"
            filepath = wine_dir / filename
 
            html = generate_elabel_html(template, wine, lang, labels)
 
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html)
 
            print(f"   ✓ {filepath.relative_to(SCRIPT_DIR)}")
 
        # Generate QR code (points to clean URL without .html)
        elabel_url = f'{base_url}/elabel/{wine["id"]}/'
        qr_png = QR_DIR / f'{wine["id"]}.png'
        png_path, svg_path = generate_qr_code(elabel_url, qr_png)
 
        print(f"   ✓ {png_path.relative_to(SCRIPT_DIR)} (PNG)")
        print(f"   ✓ {svg_path.relative_to(SCRIPT_DIR)} (SVG)")
        print(f"   → URL: {elabel_url}")
        print()
 
    # Save updated data if recalculated
    if args.recalc:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("   💾 Ažurirani nutritivni podatci spremljeni u wines.json")
 
    print("✅ Gotovo! Generirane stranice su u site/ direktoriju.")
    print()
    print("Za lokalni pregled:")
    print("   cd site && python -m http.server 8000")
    print(f"   Otvori: http://localhost:8000/elabel/{data['wines'][0]['id']}/")
 
 
if __name__ == "__main__":
    main()
 