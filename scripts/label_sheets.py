"""Foi de interpretare vizuală pentru validarea irigării (80 de parcele de primăvară: 40 irigat + 40 neirigat):
câte 20 de parcele pe imagine (4 foi: sheet_01.png .. sheet_04.png), în iulie și în august 2024 (iul NIR / aug NIR / aug).

Fiecare parcelă e conturată cu galben, cu 500 m de vecinătate în jur, în ordine amestecată și fără clasa atribuită de regulă.
Rezultat:
- data/interim/label_sheets/sheet_01.png .. sheet_04.png
- data/out/labels.csv și data/interim/label_sheets/labels.csv (coloane: id, irigat = 1/0/gol, în ordinea #1..#80 de pe foi)
- data/interim/label_sheets/index.csv (numar, id, parcel_id, foaie)
Rulare, din rădăcina proiectului: .venv/Scripts/python.exe -X utf8 scripts/label_sheets.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'render')]

import geopandas as gpd  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import rasterio  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402
from rasterio.windows import from_bounds  # noqa: E402

from common import F  # noqa: E402
from gisday_config import INTERIM, OUT  # noqa: E402

HALF_M, CHIP, PER_SHEET, COLS = 500, 120, 20, 4
NATURAL, FALSE_COLOR = (1, 2, 3), (4, 1, 2)      # R-G-B; infraroșu apropiat-R-G (vegetația viguroasă apare roșie)
OUT_DIR = INTERIM / 'label_sheets'


def chip(src, geom, bands):
    """Decupaj în jurul parcelei, cu parcela conturată."""
    c = geom.centroid
    win = from_bounds(c.x - HALF_M, c.y - HALF_M, c.x + HALF_M, c.y + HALF_M, src.transform).round_offsets().round_lengths()
    rgb = src.read(list(bands), window=win, out_shape=(3, CHIP * 2, CHIP * 2), boundless=True, fill_value=0).astype(np.float32)
    gain = np.array([1.9, 3.4, 3.4], np.float32) if bands == FALSE_COLOR else 3.4
    tone = np.clip(np.clip((np.moveaxis(rgb, 0, -1) - 1000) / 10000, 0, 1) * gain, 0, 1) ** 0.85
    img = Image.fromarray((tone * 255).astype(np.uint8), 'RGB')
    draw = ImageDraw.Draw(img)
    scale = CHIP * 2 / (2 * HALF_M)
    rings = list(geom.geoms) if geom.geom_type == 'MultiPolygon' else [geom]
    for ring in rings:
        pts = [((x - (c.x - HALF_M)) * scale, ((c.y + HALF_M) - y) * scale) for x, y in ring.exterior.coords]
        draw.line(pts + [pts[0]], fill=(255, 240, 0), width=3)
    return img.resize((CHIP, CHIP), Image.LANCZOS)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for old_png in OUT_DIR.glob('sheet_*.png'):
        old_png.unlink()

    labels = gpd.read_file(OUT / 'irrigation_labels.gpkg', layer='etichete')
    order = labels.sample(frac=1.0, random_state=7).reset_index(drop=True)
    with rasterio.open(INTERIM / 's2_iulie_2024.tif') as july, rasterio.open(INTERIM / 's2_august_2024.tif') as august:
        geoms = order.to_crs(july.crs).geometry
        rows = (PER_SHEET + COLS - 1) // COLS
        for sheet in range(0, len(order), PER_SHEET):
            canvas = Image.new('RGB', (COLS * (3 * CHIP + 28), rows * (CHIP + 34)), (20, 24, 30))
            draw = ImageDraw.Draw(canvas)
            for i in range(sheet, min(sheet + PER_SHEET, len(order))):
                col, row = (i - sheet) % COLS, (i - sheet) // COLS
                x, y = 8 + col * (3 * CHIP + 28), 26 + row * (CHIP + 34)
                pid = int(order.parcel_id.iloc[i])
                canvas.paste(chip(july, geoms.iloc[i], FALSE_COLOR), (x, y))
                canvas.paste(chip(august, geoms.iloc[i], FALSE_COLOR), (x + CHIP + 4, y))
                canvas.paste(chip(august, geoms.iloc[i], NATURAL), (x + 2 * CHIP + 8, y))
                draw.text((x, y - 21), f'#{i + 1:02d} (id {pid}) · iul NIR / aug NIR / aug', font=F(14, 'SemiBold'), fill=(235, 238, 242))
            canvas.save(OUT_DIR / f'sheet_{sheet // PER_SHEET + 1:02d}.png')

    index_df = pd.DataFrame({
        'numar': range(1, len(order) + 1),
        'id': order['parcel_id'].astype(int),
        'parcel_id': order['parcel_id'].astype(int),
        'foaie': [f'sheet_{(k // PER_SHEET) + 1:02d}.png' for k in range(len(order))],
    })
    index_df.to_csv(OUT_DIR / 'index.csv', index=False)

    labels_csv = pd.DataFrame({
        'id': order['parcel_id'].astype(int),
        'irigat': [''] * len(order),
    })
    labels_csv.to_csv(OUT / 'labels.csv', index=False)
    labels_csv.to_csv(OUT_DIR / 'labels.csv', index=False)
    print('foi:', (len(order) + PER_SHEET - 1) // PER_SHEET, '| parcele:', len(order), '| labels.csv scris în:', OUT / 'labels.csv', 'și', OUT_DIR / 'labels.csv')


if __name__ == '__main__':
    main()
